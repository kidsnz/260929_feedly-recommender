"""config/sources.md（収集元の一覧）を読む。

表は「## RSS」「## Googleニュース検索」「## はてなブックマーク検索」「## 除外する媒体」の4つ。
見出しの下の Markdown 表を、1行 = 1つの dict（キーは表の見出し）として読む。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES_MD = ROOT / "config" / "sources.md"

SECTIONS = {"RSS": "rss", "Googleニュース検索": "google", "はてなブックマーク検索": "hatena", "除外する媒体": "blocked"}


@dataclass
class Sources:
    rss: list[dict] = field(default_factory=list)
    google: list[dict] = field(default_factory=list)
    hatena: list[dict] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)


def parse_tables(text: str) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    section, header = None, None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("## "):
            section, header = SECTIONS.get(line[3:].strip()), None
            continue
        if section is None or not line.startswith("|"):
            if not line.startswith("|"):
                header = None
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if header is None:
            header = cells
        elif set(line) <= set("|-: "):
            continue  # 区切り行
        else:
            out.setdefault(section, []).append(dict(zip(header, cells)))
    return out


def load_sources(path: Path = SOURCES_MD) -> Sources:
    t = parse_tables(path.read_text(encoding="utf-8"))
    src = Sources(
        rss=[{"name": r["名前"], "lang": r["言語"], "url": r["RSS"], "topics": r.get("主なトピック", "")}
             for r in t.get("rss", [])],
        google=[{"query": r["検索語"], "lang": r["言語"]} for r in t.get("google", [])],
        hatena=[{"query": r["検索語"], "min_users": int(r["最低ブックマーク"])} for r in t.get("hatena", [])],
        blocked=[r["媒体名またはドメイン"] for r in t.get("blocked", [])],
    )
    if not src.rss:
        raise SystemExit(f"{path}: 「## RSS」の表が読めません")
    return src
