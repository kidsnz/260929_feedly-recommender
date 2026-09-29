"""Feedly「Recently read」ページの保存ファイル（.mhtml / .html）から既読記事を抽出して CSV に書く。

使い方:
    python3 src/extract_read.py "input/Recently read.mhtml"            # -> data/read_articles.csv
    python3 src/extract_read.py page.html -o data/read_articles.csv

標準ライブラリのみで動く。Feedly の難読化されたクラス名（例: aRpq1uFg...）には依存せず、
意味のあるクラス名（EntryTitleLink, EntryMetadataSource, InterestingMetadata）と
「Published: ... Received: ...」のツールチップだけを頼りにする。
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import email
import email.policy
import html
import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent

FIELDS = [
    "read_rank",       # ページ上の並び順（0 = 一番最近読んだ）。Feedly は既読順に並べる
    "title",
    "source",          # サイト名（Feedly の表示名）
    "url",
    "published",       # 記事の公開日時（UTC, ISO 8601）
    "received",        # Feedly が記事を取得した日時（UTC）
    "feed_url",        # 購読している RSS フィードの URL
    "feedly_meme",     # Feedly が付けた「Meme」ラベル（話題のまとまり）。無ければ空
    "summary",         # Feedly が表示していた冒頭の要約文
    "entry_id",
]

ARTICLE_SPLIT = re.compile(r"(?=<article )")
ENTRY_ID = re.compile(r'<article id="([^"]+)_main"')
SOURCE = re.compile(r'<a class="[^"]*\bEntryMetadataSource\b[^"]*" href="([^"]*)">(.*?)</a>', re.S)
TITLE = re.compile(r'<a class="[^"]*\bEntryTitleLink\b[^"]*" href="([^"]*)"[^>]*>(.*?)</a>', re.S)
MEME = re.compile(r'title="Meme"[^>]*InterestingMetadata__icon.*?<span>(.*?)</span>', re.S)
DATES = re.compile(r'<span title="Published: ([^"\n]+)\s+Received: ([^"\n]+)">')
DATES_RECV_ONLY = re.compile(r'<span title="Received: ([^"\n]+)">')
SUMMARY = re.compile(r'<div>([^<]*)</div></div></div><div class="[^"]*"><span title="')
TAG = re.compile(r"<[^>]+>")


def load_html(path: Path) -> str:
    """.mhtml なら本体の text/html パートを取り出す。.html はそのまま読む。"""
    raw = path.read_bytes()
    if path.suffix.lower() in (".mhtml", ".mht") or raw[:200].lstrip().startswith(b"From:"):
        msg = email.message_from_bytes(raw, policy=email.policy.default)
        parts = [p for p in msg.walk() if p.get_content_type() == "text/html"]
        if not parts:
            sys.exit(f"{path}: MHTML の中に text/html パートがありません")
        best = max(parts, key=lambda p: len(p.get_payload(decode=True) or b""))
        return best.get_payload(decode=True).decode(best.get_content_charset() or "utf-8", "replace")
    return raw.decode("utf-8", "replace")


def parse_feedly_date(s: str) -> str:
    """'Thu, 24 Sep 2026 22:15:16 GMT-4' -> '2026-09-25T02:15:16Z'"""
    m = re.match(r"\w+, (\d+ \w+ \d{4} [\d:]+) GMT([+-]\d+)(?::?(\d\d))?", s.strip())
    if not m:
        return ""
    day, hms = m.group(1).rsplit(" ", 1)
    h, mi, se = (int(x) for x in hms.split(":"))
    # Feedly は 0 時台を「24:41:00」と書く（その日の 0:41。翌日ではない）。
    # 記事 ID に埋め込まれた取得時刻と全件照合して確認済み。
    h %= 24
    local = dt.datetime.strptime(day, "%d %b %Y") + dt.timedelta(hours=h, minutes=mi, seconds=se)
    sign = -1 if m.group(2).startswith("-") else 1
    offset = dt.timedelta(hours=abs(int(m.group(2))), minutes=int(m.group(3) or 0)) * sign
    return (local - offset).strftime("%Y-%m-%dT%H:%M:%SZ")


def text(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG.sub("", fragment))).strip()


def extract(page: str) -> tuple[list[dict], list[str]]:
    rows, problems = [], []
    for rank, block in enumerate(ARTICLE_SPLIT.split(page)[1:]):
        block = block[: block.find("</article>") + 10] if "</article>" in block else block
        eid = ENTRY_ID.search(block)
        src = SOURCE.search(block)
        ttl = TITLE.search(block)
        dates = DATES.search(block)
        summ = SUMMARY.search(block)
        row = {
            "read_rank": rank,
            "entry_id": eid.group(1) if eid else "",
            "source": text(src.group(2)) if src else "",
            "feed_url": unquote(src.group(1).split("/subscription/content/feed%2F", 1)[-1])
            if src and "feed%2F" in src.group(1) else "",
            "title": text(ttl.group(2)) if ttl else "",
            "url": html.unescape(ttl.group(1)) if ttl else "",
            "feedly_meme": " / ".join(text(m) for m in MEME.findall(block)),
            "summary": text(summ.group(1)) if summ else "",
        }
        if dates:
            row["published"] = parse_feedly_date(dates.group(1))
            row["received"] = parse_feedly_date(dates.group(2))
        else:
            r = DATES_RECV_ONLY.search(block)
            row["published"] = ""
            row["received"] = parse_feedly_date(r.group(1)) if r else ""
        for key in ("title", "url", "source", "published"):
            if not row[key]:
                problems.append(f"rank {rank}: {key} が取れない ({row['entry_id']})")
        rows.append(row)
    return rows, problems


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path, help="Feedly の Recently read を保存した .mhtml / .html")
    ap.add_argument("-o", "--output", type=Path, default=ROOT / "data" / "read_articles.csv")
    args = ap.parse_args()

    rows, problems = extract(load_html(args.input))
    if not rows:
        sys.exit("記事が1件も見つかりません。Feedly の画面構造が変わった可能性があります。")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8-sig") as f:  # BOM 付き = Excel/Numbers で文字化けしない
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    pubs = sorted(r["published"] for r in rows if r["published"])
    print(f"抽出: {len(rows)} 件 -> {args.output}")
    if pubs:
        print(f"公開日の範囲: {pubs[0]} 〜 {pubs[-1]}")
    print(f"欠損のある項目: {len(problems)} 件")
    for p in problems[:20]:
        print("  ", p)


if __name__ == "__main__":
    main()
