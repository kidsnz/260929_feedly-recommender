"""既読記事の CSV とトピック定義から、好みのプロファイルを作る。

    .venv/bin/python src/build_profile.py            # data/read_articles.csv + profile/topics.md
                                                      # -> profile/profile.json, profile/profile.md

重みの考え方:
  - Feedly の保存ページには「いつ読んだか」が無い。並び順は既読順なので、
    「その記事より前に読んだ記事の取得日時の最大値」を既読日の下限として使う（est_read）。
  - 新しさの重み = 0.5 ** (経過日数 / 半減期)。経過日数は保存日（最も新しい est_read）から数える。
    今日から数えないのは、同じ HTML で後日再実行しても結果が変わらないようにするため。
"""
from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import json
import math
import re
from pathlib import Path
from urllib.parse import urlparse

from topics import TOPICS_MD, load_topics, normalize

ROOT = Path(__file__).resolve().parent.parent
HALF_LIFE_DAYS = 180
RECENT_DAYS = 90  # 「最近」と「それ以前」を比べて伸びている話題を見る区切り
KNOWN_SOURCE_MIN = 5  # これ以上読んだソースを「既に読んでいるソース」とみなす（1〜2件の迷い込みで除外しない）
# 多数の媒体をまとめる集約サイト。ドメインで丸ごと除外すると他媒体まで消えるので、媒体名で判定する
AGGREGATOR_DOMAINS = {"news.google.com", "news.yahoo.co.jp", "news.yahoo.com", "msn.com", "flipboard.com"}
OLD_AGE_DAYS = 500  # 推定既読日がこれより古い記事を「古い記事」として別扱いで報告する

# 単独では話題を表さない語（キーワード集計から外す）
STOPWORDS = set("""
こと もの ため よう これ それ あれ ここ そこ 方法 理由 発表 開始 公開 可能 登場 話題 記事 最新 必要 場合
問題 以上 以下 結果 対応 決定 判明 明らか 新た 予定 報道 利用 使用 提供 実現 実施 追加 変更 確認 指摘
存在 期待 影響 関係 関連 検討 計画 強化 拡大 向上 導入 活用 支援 展開 開発 機能 情報 世界 日本 最大
最高 規模 完全 大幅 自分 時間 時代 過去 今後 現在 全体 一部 大手 独自 正式 公式 史上 最新作 本日 同社
""".split())


def load_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    rows.sort(key=lambda r: int(r["read_rank"]))
    running = ""
    for r in reversed(rows):  # 一番昔に読んだ記事から順に
        running = max(running, r["received"] or r["published"])
        r["est_read"] = running
    return rows


def parse_day(iso: str) -> dt.date:
    return dt.date.fromisoformat(iso[:10])


def is_japanese(s: str) -> bool:
    return bool(re.search(r"[぀-ヿ一-鿿]", s))


def extract_terms(tokenizer, title: str) -> set[str]:
    """タイトルから名詞（連続する名詞は複合語としても）を取り出す。"""
    chunks, buf = [], []
    for tok in tokenizer.tokenize(normalize(title)):
        pos = tok.part_of_speech.split(",")
        if pos[0] == "名詞" and pos[1] not in ("代名詞", "非自立", "数", "接尾") \
                and not re.fullmatch(r"[\d\W_]+", tok.surface):
            buf.append(tok.surface)
        else:
            if buf:
                chunks.append(buf)
            buf = []
    if buf:
        chunks.append(buf)
    terms = set()
    for chunk in chunks:
        terms.update(s for s in chunk if len(s) > 1 and s not in STOPWORDS)
        if 1 < len(chunk) <= 3:
            joined = "".join(chunk) if not all(s.isascii() for s in chunk) else " ".join(chunk)
            if joined not in STOPWORDS:
                terms.add(joined)
    return terms


def build(rows: list[dict], topics, half_life: int) -> dict:
    from janome.tokenizer import Tokenizer

    ref = max(parse_day(r["est_read"]) for r in rows)
    recent_from = ref - dt.timedelta(days=RECENT_DAYS)
    tokenizer = Tokenizer()
    for r in rows:
        r["age"] = (ref - parse_day(r["est_read"])).days
        r["w"] = 0.5 ** (r["age"] / half_life)
        r["recent"] = parse_day(r["est_read"]) >= recent_from
        text = normalize(r["title"])
        r["topics"] = {t.name: t.match(text) for t in topics}
        r["topics"] = {k: v for k, v in r["topics"].items() if v}
        r["terms"] = extract_terms(tokenizer, r["title"])

    total_w = sum(r["w"] for r in rows)
    n_recent = sum(r["recent"] for r in rows) or 1
    n_older = (len(rows) - n_recent) or 1

    # --- トピック ---
    topic_out = []
    for t in topics:
        hits = [r for r in rows if t.name in r["topics"]]
        share = sum(r["w"] for r in hits) / total_w
        recent_rate = sum(r["recent"] for r in hits) / n_recent
        older_rate = sum(not r["recent"] for r in hits) / n_older
        kw_w = collections.Counter()
        kw_n = collections.Counter()
        for r in hits:
            for k in r["topics"][t.name]:
                kw_w[k] += r["w"]
                kw_n[k] += 1
        topic_out.append({
            "name": t.name,
            "share": round(share, 4),
            "count": len(hits),
            "recent_rate": round(recent_rate, 4),
            "older_rate": round(older_rate, 4),
            "trend": trend_label(recent_rate, older_rate),
            "keywords_observed": [
                {"term": k, "weighted": round(kw_w[k], 2), "count": kw_n[k]} for k, _ in kw_w.most_common()
            ],
            "keywords_unused": [k for k in t.all_terms if k not in kw_n],
            "samples": [r["title"] for r in hits[:5]],
            "_def": t,
            "_kw_w": kw_w,
        })
    collecting = [t for t in topic_out if t["_def"].collect]
    max_share = max(t["share"] for t in collecting) or 1
    for t in topic_out:
        t["collect"] = t["_def"].collect
        t["lang"] = t["_def"].lang
        t["keywords"] = t["_def"].keywords
        t["english"] = t["_def"].english
        # 平方根で圧縮（「AI」が他のすべてを押し流さないように）してから、topics.md の倍率を掛ける
        t["multiplier"] = t["_def"].multiplier
        t["base_weight"] = round(math.sqrt(t["share"] / max_share), 3) if t["share"] and t["collect"] else 0.0
    # 倍率を掛けたあと、最大を 1.0 に揃え直す（rebalance）。「集めない」話題は重み 0
    max_raw = max(t["base_weight"] * t["multiplier"] for t in collecting) or 1
    total_raw = sum(t["base_weight"] * t["multiplier"] for t in collecting) or 1
    for t in topic_out:
        raw = t["base_weight"] * t["multiplier"]
        t["weight"] = round(raw / max_raw, 3)
        t["allocation"] = round(raw / total_raw, 4)  # 採点の重みの構成比（合計 100%）
        top = max(t["_kw_w"].values(), default=1)
        kw_weights = {}
        english = set(t["_def"].english)
        for k in t["_def"].all_terms:
            observed = t["_kw_w"].get(k, 0)
            # 実データに出た語は出現量の対数で 0.4〜1.0。出ていない語は、英語欄の語（主要語の英訳）なら 0.7、
            # キーワード欄の語なら 0.4（既読データは日本語が大半なので、英語の語はデータでは測れない）
            if observed:
                kw_weights[k] = round(0.4 + 0.6 * math.log1p(observed) / math.log1p(top), 3)
            else:
                kw_weights[k] = 0.7 if k in english else 0.4
        t["keyword_weights"] = kw_weights
        t["exclude"] = t["_def"].exclude
    topic_out.sort(key=lambda t: -t["share"])

    # --- ソース ---
    src = collections.defaultdict(lambda: {"count": 0, "w": 0.0, "domains": collections.Counter(), "feed_url": ""})
    for r in rows:
        s = src[r["source"]]
        s["count"] += 1
        s["w"] += r["w"]
        s["domains"][urlparse(r["url"]).netloc.lower().removeprefix("www.")] += 1
        s["feed_url"] = s["feed_url"] or r["feed_url"]
    sources = sorted(
        ({"name": k, "count": v["count"], "share": round(v["w"] / total_w, 4),
          "domain": v["domains"].most_common(1)[0][0], "feed_url": v["feed_url"]} for k, v in src.items()),
        key=lambda s: -s["share"])
    # 既読ソース = KNOWN_SOURCE_MIN 件以上読んだソース。その記事 URL に KNOWN_SOURCE_MIN 回以上出たドメイン
    # （集約サイトを除く）を「既に読んでいるドメイン」とする。フィード URL のホストは配信元ではないので使わない。
    known_domains = sorted({d for v in src.values() if v["count"] >= KNOWN_SOURCE_MIN
                            for d, n in v["domains"].items() if n >= KNOWN_SOURCE_MIN and d not in AGGREGATOR_DOMAINS})
    known_publishers = sorted(k for k, v in src.items() if v["count"] >= KNOWN_SOURCE_MIN)
    for s_ in sources:
        s_["known"] = s_["count"] >= KNOWN_SOURCE_MIN

    # --- 語の集計（トピック定義の見直し用）---
    term_w, term_n, term_recent, term_older = (collections.Counter() for _ in range(4))
    for r in rows:
        for k in r["terms"]:
            term_w[k] += r["w"]
            term_n[k] += 1
            (term_recent if r["recent"] else term_older)[k] += 1
    covered = {normalize(k).lower() for t in topics for k in t.all_terms}
    rising = []
    for k, n in term_n.items():
        if n < 8 or normalize(k).lower() in covered:
            continue
        rr, orr = term_recent[k] / n_recent, term_older[k] / n_older
        if rr > 2 * orr and term_recent[k] >= 5:
            rising.append({"term": k, "recent": term_recent[k], "older": term_older[k], "ratio": round(rr / max(orr, 1e-9), 1)})
    rising.sort(key=lambda x: -x["recent"])
    uncovered_top = [{"term": k, "weighted": round(v, 1), "count": term_n[k]}
                     for k, v in term_w.most_common() if normalize(k).lower() not in covered][:40]

    collect_names = {t.name for t in topics if t.collect}
    unmatched = [r for r in rows if not (set(r["topics"]) & collect_names)]
    ja = sum(is_japanese(r["title"]) for r in rows)
    old = [r for r in rows if r["age"] > OLD_AGE_DAYS]

    for t in topic_out:
        del t["_def"], t["_kw_w"]
    return {
        "version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "params": {"half_life_days": half_life, "reference_date": ref.isoformat(), "recent_days": RECENT_DAYS},
        "stats": {
            "articles": len(rows),
            "published_min": min(r["published"] for r in rows if r["published"]),
            "published_max": max(r["published"] for r in rows if r["published"]),
            "est_read_min_main": min(r["est_read"] for r in rows if r["age"] <= OLD_AGE_DAYS),
            "old_items_published_years": sorted({r["published"][:4] for r in old if r["published"]}),
            "japanese_titles": ja,
            "other_titles": len(rows) - ja,
            "matched_any_topic": len(rows) - len(unmatched),
            "old_items": len(old),
            "old_items_sources": collections.Counter(r["source"] for r in old).most_common(),
        },
        "topics": topic_out,
        "sources": sources,
        "known_domains": known_domains,
        "known_publishers": known_publishers,
        "known_urls_count": len({r["url"] for r in rows}),
        "top_terms": [{"term": k, "weighted": round(v, 1), "count": term_n[k]} for k, v in term_w.most_common(60)],
        "uncovered_top_terms": uncovered_top,
        "rising_uncovered_terms": rising[:30],
        "unmatched_samples": [f'{r["source"]}｜{r["title"]}' for r in unmatched[:15]],
    }


def trend_label(recent: float, older: float) -> str:
    if older == 0:
        return "新規" if recent else "—"
    ratio = recent / older
    if ratio >= 1.3:
        return "↑ 増加"
    if ratio <= 0.77:
        return "↓ 減少"
    return "→ 横ばい"


def bar(x: float, width: int = 20) -> str:
    n = round(x * width)
    return "█" * n + "░" * (width - n)


def render_md(p: dict) -> str:
    s, prm = p["stats"], p["params"]
    L = []
    a = L.append
    a("# 好みのプロファイル（確認用）")
    a("")
    a(f"> 自動生成: `src/build_profile.py`（{p['generated_at'][:10]}）。このファイルは再実行で上書きされます。")
    a("> **トピックを直したいときは `profile/topics.md` を編集**してから再実行してください（またはClaudeに日本語で頼む）。")
    a("")
    a("## 1. もとになったデータ")
    a("")
    a(f"- 既読記事: **{s['articles']:,} 件**（日本語タイトル {s['japanese_titles']:,} 件 / それ以外 {s['other_titles']:,} 件）")
    a(f"- 記事の公開日: {s['published_min'][:10]} 〜 {s['published_max'][:10]}"
      f"（ただし {s['old_items']} 件の古い記事を除くと {s['est_read_min_main'][:10]} 以降）")
    a(f"- トピックのどれかに当たった記事: {s['matched_any_topic']:,} 件"
      f"（{100 * s['matched_any_topic'] / s['articles']:.1f}%）")
    a(f"- 新しさの重み: 半減期 **{prm['half_life_days']}日**（基準日 {prm['reference_date']}。"
      f"{prm['half_life_days']}日前に読んだ記事は重み 0.5、{2 * prm['half_life_days']}日前は 0.25）")
    a("")
    a("## 2. よく読んでいるトピック（重みの大きい順）")
    a("")
    a("「割合」は新しさで重み付けした既読記事のうち、そのトピックに当たった割合（1記事が複数トピックに当たるので合計は100%を超えます）。"
      f"「傾向」は直近{prm['recent_days']}日とそれ以前の比較。")
    a("「採点の重み」は収集時の点数に使う値（割合の平方根 × `topics.md` の倍率を、最大 1.0 に揃えたもの）。"
      "「配分」はその構成比で、合計 100%。表は配分の大きい順。")
    a("")
    a("「優先言語」のあるトピックでは、その言語の記事を満点、他の言語の記事を半分の点で数えます。")
    a("")
    a("| # | トピック | 割合 | 件数 | 傾向 | 倍率 | 優先言語 | 採点の重み | 配分 | |")
    a("|---|---|---:|---:|---|---:|:---:|---:|---:|---|")
    shown = [t for t in p["topics"] if t["collect"]]
    max_alloc = max(t["allocation"] for t in shown) or 1
    for i, t in enumerate(sorted(shown, key=lambda t: -t["allocation"]), 1):
        mult = f"×{t['multiplier']:g}" if t["multiplier"] != 1 else ""
        lang = {"en": "英語", "ja": "日本語"}.get(t["lang"], "")
        a(f"| {i} | {t['name']} | {100 * t['share']:.1f}% | {t['count']} | {t['trend']} | {mult} | {lang} | {t['weight']:.2f} "
          f"| {100 * t['allocation']:.1f}% | `{bar(t['allocation'] / max_alloc, 12)}` |")
    a("")
    skipped = [t for t in p["topics"] if not t["collect"]]
    if skipped:
        a("**集めない話題**（当たった記事は収集から除外）: "
          + "、".join(f"{t['name']}（既読 {t['count']} 件、割合 {100 * t['share']:.1f}%）" for t in skipped))
        a("")
    a("## 3. トピックごとの中身")
    a("")
    for t in sorted((t for t in p["topics"] if t["collect"]), key=lambda t: -t["allocation"]):
        a(f"### {t['name']}")
        a("")
        kws = "、".join(f"{k['term']}（{k['count']}）" for k in t["keywords_observed"][:12]) or "（なし）"
        a(f"- **よく当たった語**（件数）: {kws}")
        if t["keywords_unused"]:
            a(f"- 既読記事には出てこなかった語（英語記事用など）: {'、'.join(t['keywords_unused'])}")
        if t["exclude"]:
            a(f"- 除外: {'、'.join(t['exclude'])}")
        a("- 最近読んだ例:")
        for title in t["samples"][:3]:
            a(f"  - {title}")
        a("")
    a("## 4. よく読んでいるソース")
    a("")
    a("| ソース | 件数 | 割合（重み付き） | ドメイン | 既読ソース扱い |")
    a("|---|---:|---:|---|:---:|")
    for src in p["sources"]:
        a(f"| {src['name']} | {src['count']} | {100 * src['share']:.1f}% | {src['domain']} | {'✓' if src['known'] else ''} |")
    a("")
    a(f"✓ の付いたソース（{KNOWN_SOURCE_MIN}件以上読んだもの）のドメインは、取りこぼし収集（ステップ3）で**既に読んでいるソース**として除外します。")
    a("")
    a("## 5. トピック定義の見直し候補")
    a("")
    a("### どのトピックにも入っていない、よく出る語")
    a("")
    a("、".join(f"{x['term']}（{x['count']}）" for x in p["uncovered_top_terms"][:30]))
    a("")
    a("多くは「発売」「アメリカ」のような一般語です。話題を表す語があれば `topics.md` に足してください。")
    a("")
    a(f"### 最近（直近{prm['recent_days']}日）増えている、未分類の語")
    a("")
    if p["rising_uncovered_terms"]:
        a("、".join(f"{x['term']}（直近{x['recent']}/以前{x['older']}）" for x in p["rising_uncovered_terms"][:20]))
    else:
        a("（該当なし）")
    a("")
    a("### どのトピックにも当たらなかった記事の例（最近の順）")
    a("")
    for x in p["unmatched_samples"][:10]:
        a(f"- {x}")
    a("")
    a("## 6. このプロファイルで確認できないこと")
    a("")
    a("- **いつ読んだか**: 保存ページには既読日時が無いため、並び順と取得日時から「この日以降に読んだ」という下限を推定しています。")
    a("- **どれだけ熱心に読んだか**: タイトルを開いただけか、最後まで読んだかは区別できません（Feedlyの「既読」は一覧で流しただけでも付く場合があります）。")
    a("- **読まなかった記事**: 購読していても読まなかった記事は保存ページに無いため、「興味が無い話題」は分かりません。")
    if s["old_items"]:
        srcs = "、".join(f"{k}（{v}）" for k, v in s["old_items_sources"])
        yrs = s["old_items_published_years"]
        a(f"- **古い記事 {s['old_items']} 件**: 公開が{yrs[0]}〜{yrs[-1]}年の記事が既読リストの末尾にまとまっています（{srcs}）。"
          "読んだ時期を推定できないため重みはほぼ0ですが、件数としてはソース表に含めています。")
    a("- **英語の関心**: 既読の大半が日本語のため、英語記事への関心の強さはデータからは測れません。"
      "`topics.md` の「英語」欄は英語記事を拾うために推測で足した語です。")
    a("")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", type=Path, default=ROOT / "data" / "read_articles.csv")
    ap.add_argument("--topics", type=Path, default=TOPICS_MD)
    ap.add_argument("--half-life", type=int, default=HALF_LIFE_DAYS, help="新しさの重みの半減期（日）")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "profile")
    args = ap.parse_args()

    profile = build(load_rows(args.input), load_topics(args.topics), args.half_life)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "profile.json").write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.out_dir / "profile.md").write_text(render_md(profile), encoding="utf-8")
    s = profile["stats"]
    print(f"プロファイル: {len(profile['topics'])} トピック / {s['articles']} 件"
          f"（トピックに当たった {s['matched_any_topic']} 件）-> {args.out_dir}/profile.json, profile.md")


if __name__ == "__main__":
    main()
