"""取りこぼしニュースのフィードを作る（GitHub Actions が毎日実行する本体）。

    .venv/bin/python src/build_feed.py             # 収集して feed.xml / index.html / state/*.json を更新
    .venv/bin/python src/build_feed.py --dry-run   # 何も書かずに、選ばれる記事と各収集元の状態を表示

入力: profile/profile.json（好みのプロファイル）、config/sources.md（収集元）、state/items.json（前回までに選んだ記事）
出力: feed.xml（RSS 2.0）、index.html（確認用ページ）、state/items.json、state/discovered_sources.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import sys
import xml.etree.ElementTree as ET
from email.utils import format_datetime
from pathlib import Path

from collect import Item, collect_all, domain_of, fetch
from rank import Profile, load_profile, rank
from sources import load_sources

import feedparser

ROOT = Path(__file__).resolve().parent.parent
SITE_URL = os.environ.get("FEED_SITE_URL", "https://kidsnz.github.io/260929_feedly-recommender/")
FEED_TITLE = "取りこぼしニュース"
FEED_DESCRIPTION = "Feedly の既読記事から作った好みのプロファイルで、まだ読んでいない媒体の関連ニュースを毎日集めたフィード"

DAILY_LIMIT = 30         # 1回の実行で新しく載せる最大件数
MIN_SCORE = 0.1          # これ未満の点数の記事は載せない（ノイズ除け。主な絞り込みはトピックの枠で行う）
PER_SOURCE_CAP = 4       # 1回の実行で同じ媒体から載せる最大件数
KEEP_DAYS = 7            # フィードに残す日数
MIN_OK_RSS_RATIO = 0.5   # RSS の半分以上が取得できなければ、フィードを更新せず失敗にする
AGGREGATOR_RSS = {"Techmeme", "Hacker News", "はてなブックマーク IT 人気", "はてなブックマーク 学び 人気",
                  "はてなブックマーク アニメとゲーム 人気", "Qiita トレンド"}
JST = dt.timezone(dt.timedelta(hours=9))

STATE_DIR = ROOT / "state"
ITEMS_JSON = STATE_DIR / "items.json"
DISCOVERED_JSON = STATE_DIR / "discovered_sources.json"


# ---------- 状態 ----------

def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def item_to_record(it: Item, selected_at: dt.datetime) -> dict:
    return {
        "title": it.title, "link": it.link, "source": it.source, "via": it.via, "collector": it.collector,
        "feed_url": it.feed_url, "domain": it.domain, "lang": it.lang, "score": it.score,
        "published": it.published.isoformat() if it.published else None,
        "selected_at": selected_at.isoformat(),
        "topics": {k: v["keywords"] for k, v in it.topics.items()},
        "primary": it.primary,
        "related": sorted(set(it.related) - {it.source}),
    }


def known_source_titles(profile_data: dict, log) -> list[tuple[str, str]]:
    """既読ソース（Feedly で購読中の媒体）の最新記事。同じニュースを「取りこぼし」として出さないために使う。"""
    out = []
    for s in profile_data["sources"]:
        if not (s.get("known") and s.get("feed_url")):
            continue
        try:
            for e in feedparser.parse(fetch(s["feed_url"])).entries:
                out.append((e.get("link", ""), e.get("title", "")))
        except Exception as e:
            log(f"  （既読ソースの取得に失敗: {s['name']}: {type(e).__name__}）")
    return out


# ---------- 出力 ----------

def description(rec: dict) -> str:
    parts = [f"{name}（{', '.join(kws[:4])}）" for name, kws in rec["topics"].items()]
    via = "" if rec["via"] == "RSS" else f"・{rec['via']}経由"
    related = rec.get("related", [])
    rel = f"｜同じ話題: 他{len(related)}媒体（{'、'.join(related[:3])}{' ほか' if len(related) > 3 else ''}）" if related else ""
    return f"該当トピック: {' / '.join(parts)}｜出典: {rec['source']}{via}{rel}｜スコア {rec['score']:.2f}"


def write_feed(records: list[dict], path: Path, now: dt.datetime) -> None:
    ET.register_namespace("atom", "http://www.w3.org/2005/Atom")
    rss = ET.Element("rss", {"version": "2.0"})
    ch = ET.SubElement(rss, "channel")
    ET.SubElement(ch, "title").text = FEED_TITLE
    ET.SubElement(ch, "link").text = SITE_URL
    ET.SubElement(ch, "description").text = FEED_DESCRIPTION
    ET.SubElement(ch, "language").text = "ja"
    ET.SubElement(ch, "lastBuildDate").text = format_datetime(now)
    ET.SubElement(ch, "{http://www.w3.org/2005/Atom}link",
                  {"href": SITE_URL + "feed.xml", "rel": "self", "type": "application/rss+xml"})
    for r in records:
        it = ET.SubElement(ch, "item")
        ET.SubElement(it, "title").text = r["title"]
        ET.SubElement(it, "link").text = r["link"]
        ET.SubElement(it, "description").text = description(r)
        for name in r["topics"]:
            ET.SubElement(it, "category").text = name
        guid = hashlib.sha1(r["link"].encode()).hexdigest()
        ET.SubElement(it, "guid", {"isPermaLink": "false"}).text = guid
        when = dt.datetime.fromisoformat(r["published"] or r["selected_at"])
        ET.SubElement(it, "pubDate").text = format_datetime(when)
        ET.SubElement(it, "source", {"url": r["feed_url"]}).text = r["source"]
    ET.indent(rss)
    path.write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(rss, encoding="utf-8") + b"\n")


def update_discovered(disc: dict, new_records: list[dict], rss_domains: set[str]) -> dict:
    """検索・集約経由で選ばれたのに RSS の一覧に無い媒体を数える（数ヶ月ごとの見直しで、追加候補にする）。"""
    for r in new_records:
        if not (r["via"] != "RSS" or r["collector"] in AGGREGATOR_RSS):
            continue
        d = r["domain"]
        if not d or d in rss_domains or d.endswith("news.google.com"):
            continue
        e = disc.setdefault(d, {"publisher": r["source"] if r["via"] == "Googleニュース" else d,
                                "count": 0, "first_seen": r["selected_at"][:10], "examples": []})
        e["count"] += 1
        e["last_seen"] = r["selected_at"][:10]
        e["examples"] = ([r["title"]] + e["examples"])[:3]
    return dict(sorted(disc.items(), key=lambda kv: -kv[1]["count"]))


def write_index(records: list[dict], disc: dict, statuses, path: Path, now: dt.datetime) -> None:
    esc = html.escape
    by_day: dict[str, list[dict]] = {}
    for r in records:
        day = dt.datetime.fromisoformat(r["selected_at"]).astimezone(JST).strftime("%Y-%m-%d")
        by_day.setdefault(day, []).append(r)
    sections = []
    for day, recs in by_day.items():
        rows = []
        for r in recs:
            chips = "".join(f'<span class="chip">{esc(n)}</span>' for n in r["topics"])
            via = "" if r["via"] == "RSS" else f' <span class="via">{esc(r["via"])}経由</span>'
            lang = '<span class="lang">EN</span>' if r["lang"] == "en" else ""
            rows.append(
                f'<li><a href="{esc(r["link"])}" target="_blank" rel="noopener">{esc(r["title"])}</a>'
                f'<div class="meta">{lang}<span class="src">{esc(r["source"])}</span>{via}'
                f'<span class="score">{r["score"]:.2f}</span></div><div class="chips">{chips}</div></li>')
        sections.append(f'<section><h2>{day} <small>{len(recs)}件</small></h2><ol>{"".join(rows)}</ol></section>')
    disc_rows = "".join(
        f'<li><b>{esc(v["publisher"])}</b> <span class="src">{esc(k)}</span> — {v["count"]}回'
        f'<div class="ex">{esc(v["examples"][0]) if v["examples"] else ""}</div></li>'
        for k, v in list(disc.items())[:10]) or "<li>まだありません</li>"
    ok = sum(s.ok for s in statuses)
    failed = [s for s in statuses if not s.ok]
    fail_html = ("<p class='warn'>取得できなかった収集元: " + "、".join(esc(s.label) for s in failed) + "</p>") if failed else ""
    page = f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{FEED_TITLE}</title>
<link rel="alternate" type="application/rss+xml" title="{FEED_TITLE}" href="feed.xml">
<style>
:root{{--bg:#fbfaf7;--fg:#1d1d1f;--muted:#6e6e73;--line:#e6e3dc;--chip:#eeeae2;--accent:#b4442f}}
@media (prefers-color-scheme:dark){{:root{{--bg:#161615;--fg:#ecebe8;--muted:#9b9a96;--line:#2c2b29;--chip:#262523;--accent:#e2765f}}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.6 -apple-system,BlinkMacSystemFont,"Hiragino Sans","Noto Sans JP",sans-serif}}
main{{max-width:760px;margin:0 auto;padding:40px 16px 80px}}
h1{{font-size:26px;margin:0 0 4px;letter-spacing:.02em}}
.lead{{color:var(--muted);margin:0 0 20px}}
.feed{{display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:12px 14px;border:1px solid var(--line);border-radius:10px;margin-bottom:32px}}
.feed code{{flex:1;min-width:0;overflow-wrap:anywhere;font-size:13px}}
.feed button{{border:0;background:var(--accent);color:#fff;border-radius:6px;padding:6px 12px;font:inherit;font-size:13px;cursor:pointer}}
h2{{font-size:15px;margin:36px 0 8px;padding-bottom:6px;border-bottom:1px solid var(--line)}}
h2 small{{color:var(--muted);font-weight:normal;margin-left:6px}}
ol{{list-style:none;margin:0;padding:0}}
li{{padding:12px 0;border-bottom:1px solid var(--line)}}
li a{{color:var(--fg);text-decoration:none;font-weight:600}}
li a:hover{{color:var(--accent)}}
.meta{{display:flex;gap:10px;font-size:12px;color:var(--muted);margin-top:4px;flex-wrap:wrap}}
.lang{{border:1px solid var(--muted);border-radius:3px;padding:0 4px;font-size:10px;line-height:16px}}
.score{{margin-left:auto;font-variant-numeric:tabular-nums}}
.chips{{margin-top:6px;display:flex;gap:6px;flex-wrap:wrap}}
.chip{{background:var(--chip);border-radius:999px;padding:1px 9px;font-size:12px}}
.ex{{color:var(--muted);font-size:12px}}
.warn{{color:var(--accent);font-size:13px}}
footer{{color:var(--muted);font-size:12px;margin-top:40px}}
</style></head><body><main>
<h1>{FEED_TITLE}</h1>
<p class="lead">{FEED_DESCRIPTION}。</p>
<div class="feed"><code id="u">{SITE_URL}feed.xml</code><button onclick="navigator.clipboard.writeText(document.getElementById('u').textContent);this.textContent='コピーしました'">URLをコピー</button></div>
{"".join(sections) or "<p>まだ記事がありません。</p>"}
<h2>リスト外でよく選ばれた媒体 <small>収集元への追加候補</small></h2>
<ol>{disc_rows}</ol>
<footer>最終更新 {now.astimezone(JST):%Y-%m-%d %H:%M} JST ・ 収集元 {ok}/{len(statuses)} 件取得{fail_html}</footer>
</main></body></html>
"""
    path.write_text(page, encoding="utf-8")


# ---------- 本体 ----------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="ファイルを書かずに結果を表示する")
    ap.add_argument("--limit", type=int, default=DAILY_LIMIT)
    ap.add_argument("--min-score", type=float, default=MIN_SCORE)
    args = ap.parse_args()
    log = print
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)

    profile_data = json.loads((ROOT / "profile" / "profile.json").read_text(encoding="utf-8"))
    profile: Profile = load_profile(profile_data)
    sources = load_sources()

    log(f"収集: RSS {len(sources.rss)} / Googleニュース検索 {len(sources.google)} / はてブ検索 {len(sources.hatena)}")
    items, statuses = collect_all(sources)
    rss_status = [s for s in statuses if s.kind == "rss"]
    ok_ratio = sum(s.ok for s in rss_status) / max(len(rss_status), 1)
    for s in statuses:
        if not s.ok:
            log(f"  取得失敗: {s.label}: {s.error}")
    log(f"  取得できた収集元 {sum(s.ok for s in statuses)}/{len(statuses)}、記事 {len(items)} 件")
    if ok_ratio < MIN_OK_RSS_RATIO:
        log(f"RSS の取得成功率が {ok_ratio:.0%} しかないため、フィードを更新せずに終了します")
        return 1

    # 前回までに選んだ記事（残す期間内）と、既読ソースの最新記事を「既に見たもの」として登録
    old = [r for r in load_json(ITEMS_JSON, [])
           if now - dt.datetime.fromisoformat(r["selected_at"]) < dt.timedelta(days=KEEP_DAYS)]
    known_titles = known_source_titles(profile_data, log)
    seen_titles = [(r["link"], r["title"]) for r in old] + known_titles
    log(f"  既に見た記事として扱う: 前回までの選択 {len(old)} 件 + 既読ソースの最新記事 {len(known_titles)} 件")

    res = rank(items, profile, sources.blocked, now=now, limit=args.limit, min_score=args.min_score,
               per_source_cap=PER_SOURCE_CAP, seen_titles=seen_titles)
    log(f"採点: 72時間より古い {res.too_old} 件 / 除外 {res.excluded} / 点数不足 {res.below_threshold} 件 / "
        f"既に見た話題 {res.already_seen} 件 / 同じ話題の別記事 {res.same_story} 件 / 媒体ごとの上限 {res.capped} 件"
        f" → 採用 {len(res.selected)} 件")
    log("  枠: " + "、".join(f"{k[:10]}{v}" for k, v in res.quotas.items()))
    for it in res.selected:
        rel = f" ＋同じ話題{len(set(it.related))}媒体" if it.related else ""
        log(f"  {it.score:5.2f} [{it.lang}] 〈{it.primary[:8]}〉 {it.title[:60]} — {it.source}（{it.via}）{rel}")

    if args.dry_run:
        return 0
    new = [item_to_record(it, now) for it in res.selected]
    records = new + old
    rss_domains = {domain_of(s["url"]) for s in sources.rss}
    disc = update_discovered(load_json(DISCOVERED_JSON, {}), new, rss_domains)
    STATE_DIR.mkdir(exist_ok=True)
    ITEMS_JSON.write_text(json.dumps(records, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    DISCOVERED_JSON.write_text(json.dumps(disc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    write_feed(records, ROOT / "feed.xml", now)
    write_index(records, disc, statuses, ROOT / "index.html", now)
    log(f"出力: feed.xml（{len(records)} 件、うち今回 {len(new)} 件）, index.html, state/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
