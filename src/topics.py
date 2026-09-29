"""profile/topics.md（人が編集するトピック定義）を読み、記事テキストとの照合を行う。

topics.md の書式（1トピック = 1つの「## 見出し」）:

    ## AI・生成AI
    - キーワード: AI, 生成AI, LLM, ChatGPT
    - 英語: artificial intelligence, generative AI
    - 除外: AIメイク
    - 倍率: 2
    - 優先言語: en
    - 扱い: 集めない

「キーワード」は既読記事のデータから拾った語、「英語」は英語記事を拾うために足した語。
照合ではどちらも同じに扱う。「除外」を含む記事はそのトピックに数えない。
「倍率」は採点の重みに掛ける数（省略時 1）。
「優先言語」（en / ja）はそのトピックで満点にする記事の言語。「扱い: 集めない」は収集から除外する話題。
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOPICS_MD = ROOT / "profile" / "topics.md"

FIELD_KEYS = {"キーワード": "keywords", "英語": "english", "除外": "exclude"}


def normalize(s: str) -> str:
    """全角英数→半角、大文字小文字の揺れを吸収する前処理（大文字小文字は照合側で扱う）。"""
    return unicodedata.normalize("NFKC", s)


@dataclass
class Topic:
    name: str
    keywords: list[str] = field(default_factory=list)
    english: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    multiplier: float = 1.0
    lang: str = ""          # 優先言語（"en" / "ja" / ""）
    collect: bool = True    # False = 「集めない」話題（当たった記事を除外する）

    def __post_init__(self) -> None:
        self._kw = [(k, _compile(k)) for k in self.keywords + self.english]
        self._ex = [_compile(k) for k in self.exclude]

    @property
    def all_terms(self) -> list[str]:
        return self.keywords + self.english

    def match(self, text: str) -> list[str]:
        """text に含まれるキーワードの一覧（無ければ空）。"""
        text = normalize(text)
        if any(p.search(text) for p in self._ex):
            return []
        return [k for k, p in self._kw if p.search(text)]


def _compile(term: str) -> re.Pattern:
    term = normalize(term).strip()
    if term.isascii():
        # 英数字の語は単語の境目で照合する（"AI" が "said" に、"SK" が "Skills" に当たらないように）。
        # 大文字を含む4文字以下の語（AI, SK, Meta）は大文字小文字を区別する（"Meta" が "meta-analysis" に
        # 当たらないように）。それより長い語は区別しない（英語の報道は "NVIDIA" を "Nvidia" と書く）。
        flags = 0 if (len(term) <= 4 and any(c.isupper() for c in term)) else re.I
        # 空白とハイフンは同じに扱う（"self-driving" と "self driving"）
        body = r"[\s\-]?".join(re.escape(part) for part in re.split(r"[\s\-]+", term))
        plural = "(?:s|es)?" if term[-1:].isalpha() and len(term) >= 4 else ""
        return re.compile(rf"(?<![A-Za-z0-9]){body}{plural}(?![A-Za-z0-9])", flags)
    return re.compile(re.escape(term), re.I)


def load_topics(path: Path = TOPICS_MD) -> list[Topic]:
    topics: list[Topic] = []
    current: dict | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("## "):
            if current:
                topics.append(Topic(**current))
            current = {"name": line[3:].strip()}
        elif current is not None and (m := re.match(r"-\s*([^:：]+?)\s*[:：]\s*(.*)", line)):
            key, value = m.groups()
            if key == "倍率":
                current["multiplier"] = float(value)
            elif key == "優先言語":
                current["lang"] = value.strip().lower()
            elif key == "扱い":
                current["collect"] = value.strip() != "集めない"
            elif key in FIELD_KEYS:
                terms = [t.strip() for t in re.split(r"[,、，]", value) if t.strip()]
                current.setdefault(FIELD_KEYS[key], []).extend(terms)
    if current:
        topics.append(Topic(**current))
    if not topics:
        raise SystemExit(f"{path}: トピックが1つも読めません（「## トピック名」の見出しが必要）")
    return topics


def topic_from_dict(d: dict) -> Topic:
    """profile.json のトピック項目から Topic を作る（GitHub Actions 側は topics.md を読まず profile.json だけを使う）。"""
    return Topic(name=d["name"], keywords=d.get("keywords", []), english=d.get("english", []),
                 exclude=d.get("exclude", []), multiplier=d.get("multiplier", 1.0),
                 lang=d.get("lang", ""), collect=d.get("collect", True))


def match_all(topics: list[Topic], text: str) -> dict[str, list[str]]:
    text = normalize(text)
    out = {}
    for t in topics:
        hits = t.match(text)
        if hits:
            out[t.name] = hits
    return out
