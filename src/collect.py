"""収集元（RSS・Googleニュース検索・はてブ検索）から記事を集め、共通の形（Item）に揃える。"""
from __future__ import annotations

import calendar
import concurrent.futures as cf
import datetime as dt
import html
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field

import feedparser

from sources import Sources

USER_AGENT = "feedly-recommender/1.0 (+https://github.com/kidsnz/260929_feedly-recommender)"
TIMEOUT = 25
GOOGLE_INTERVAL_SEC = 1.0
SUMMARY_CHARS = 300

GOOGLE_PARAMS = {
    "en": {"hl": "en-US", "gl": "US", "ceid": "US:en"},
    "ja": {"hl": "ja", "gl": "JP", "ceid": "JP:ja"},
}


@dataclass
class Item:
    title: str
    link: str
    source: str            # 表示する出典名（媒体名）
    via: str               # 収集経路: "RSS" / "Googleニュース" / "はてブ検索"
    collector: str         # どの収集元から来たか（RSS の名前や検索語）
    feed_url: str          # 収集元の RSS URL（RSS の <source> 要素に使う）
    domain: str            # 記事の配信元ドメイン（既読ソース・除外媒体の判定に使う）
    published: dt.datetime | None
    summary: str = ""
    lang: str = ""
    # 採点結果（rank.py が埋める）
    score: float = 0.0
    topics: dict = field(default_factory=dict)
    primary: str = ""                                   # 主トピック
    related: list = field(default_factory=list)         # 同じ話題を報じた他の媒体
    fresh: float = 1.0                                  # 新しさの係数（経路の係数を含む）
    buzz: float = 1.0                                   # 話題の大きさの係数
    ja_alt: "Item | None" = None                        # 同じニュースの日本語記事（あれば出力で差し替える）
    merged: bool = False
    source_topics: str = ""                             # 収集元の「主なトピック」欄（専門媒体の判定に使う）


def domain_of(url: str) -> str:
    return urllib.parse.urlparse(url).netloc.lower().split(":")[0].removeprefix("www.")


def detect_lang(text: str) -> str:
    return "ja" if re.search(r"[぀-ヿ一-鿿]", text) else "en"


def plain(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment or "")
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def entry_time(e) -> dt.datetime | None:
    t = e.get("published_parsed") or e.get("updated_parsed")
    return dt.datetime.fromtimestamp(calendar.timegm(t), dt.timezone.utc) if t else None


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml, */*"})
    last = None
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = e
            if isinstance(e, urllib.error.HTTPError) and e.code in (403, 404, 410):
                break
            time.sleep(2)
    raise last


def _techmeme_link(e) -> str:
    """Techmeme の <link> は自サイトの要約ページ。要約の中の最初の外部リンクが元記事。"""
    for href in re.findall(r'href="([^"]+)"', e.get("summary", "")):
        if "techmeme.com" not in href:
            return html.unescape(href)
    return e.link


def from_rss(src: dict) -> list[Item]:
    f = feedparser.parse(fetch(src["url"]))
    items = []
    for e in f.entries:
        link = e.get("link", "")
        if not link or not e.get("title"):
            continue
        if "techmeme.com" in src["url"]:
            link = _techmeme_link(e)
        title = plain(e.title)
        items.append(Item(
            title=title, link=link, source=src["name"], via="RSS", collector=src["name"], feed_url=src["url"],
            domain=domain_of(link), published=entry_time(e),
            summary=plain(e.get("summary", ""))[:SUMMARY_CHARS], lang=detect_lang(title),
            source_topics=src.get("topics", ""),
        ))
    return items


def google_url(query: str, lang: str) -> str:
    params = {"q": f"{query} when:1d", **GOOGLE_PARAMS[lang]}
    return "https://news.google.com/rss/search?" + urllib.parse.urlencode(params)


def from_google(q: dict) -> list[Item]:
    url = google_url(q["query"], q["lang"])
    f = feedparser.parse(fetch(url))
    items = []
    for e in f.entries:
        src = e.get("source") or {}
        publisher = src.get("title", "")
        title = plain(e.title)
        if publisher and title.endswith(f" - {publisher}"):
            title = title[: -len(publisher) - 3]
        # Yahoo!ニュースは他媒体の転載。見出し末尾の（媒体名）を本当の出典として扱う
        m = re.search(r"（([^（）]{2,30})）$", title)
        if "yahoo" in publisher.lower() and m:
            publisher = m.group(1)
            title = title[: m.start()].rstrip()
        items.append(Item(
            title=title, link=e.link, source=publisher or "Googleニュース", via="Googleニュース",
            collector=f"Google: {q['query']}", feed_url=url, domain=domain_of(src.get("href", "")),
            published=entry_time(e), summary="",  # Google の要約は関連記事リンクの羅列なので使わない
            lang=detect_lang(title),
        ))
    return items


def hatena_url(query: str, min_users: int) -> str:
    return (f"https://b.hatena.ne.jp/q/{urllib.parse.quote(query)}?"
            + urllib.parse.urlencode({"mode": "rss", "sort": "recent", "users": min_users}))


def from_hatena(q: dict) -> list[Item]:
    url = hatena_url(q["query"], q["min_users"])
    f = feedparser.parse(fetch(url))
    items = []
    for e in f.entries:
        title = plain(e.title)
        items.append(Item(
            title=title, link=e.link, source=domain_of(e.link), via="はてブ検索", collector=f"はてブ: {q['query']}",
            feed_url=url, domain=domain_of(e.link), published=entry_time(e),
            summary=plain(e.get("summary", ""))[:SUMMARY_CHARS], lang=detect_lang(title),
        ))
    return items


@dataclass
class Status:
    label: str
    kind: str
    ok: bool
    count: int = 0
    error: str = ""


def collect_all(sources: Sources, log=print) -> tuple[list[Item], list[Status]]:
    items: list[Item] = []
    statuses: list[Status] = []

    def run(kind, label, fn, arg):
        try:
            got = fn(arg)
            return Status(label, kind, True, len(got)), got
        except Exception as e:  # 1つの収集元の失敗で全体を止めない
            return Status(label, kind, False, 0, f"{type(e).__name__}: {e}"[:120]), []

    def google_sequential():
        out = []
        for q in sources.google:
            out.append(run("google", f"Google: {q['query']}", from_google, q))
            time.sleep(GOOGLE_INTERVAL_SEC)
        return out

    with cf.ThreadPoolExecutor(10) as ex:
        google_job = ex.submit(google_sequential)
        jobs = [ex.submit(run, "rss", s["name"], from_rss, s) for s in sources.rss]
        jobs += [ex.submit(run, "hatena", f"はてブ: {q['query']}", from_hatena, q) for q in sources.hatena]
        results = [j.result() for j in jobs] + google_job.result()
    for st, got in results:
        statuses.append(st)
        items.extend(got)
    return items, statuses
