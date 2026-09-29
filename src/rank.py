"""集めた記事をプロファイルで採点し、除外・同じ話題のまとめをして、トピックの配分どおりに選ぶ。

1. 除外: 既読ソース（ドメイン・媒体名）、除外する媒体、「集めない」話題、72時間より古い記事。
2. 採点: 点数 = Σ（トピックの採点の重み × 当たりの強さ × 言語の係数）× 新しさ
   - 当たりの強さ: 当たったキーワードごとに「キーワードの重み × 位置の係数（タイトル 1.0 / 要約だけ 0.5）」
     を出し、1 - Π(1 - 値) でまとめる（1語でも強く当たれば高く、語が増えるほど 1 に近づく）。
   - 言語の係数: トピックに優先言語があり、記事の言語と一致すれば 1.0、違えば 0.5。
   - 新しさ: 0.5 ** (経過時間 / 72時間)。
   - 話題の大きさ: 同じ話題を報じた媒体が多いほど点を上げる（1媒体につき 8%、最大 1.8 倍）。
   - 専門媒体: config/sources.md の「主なトピック」の先頭がそのトピックの媒体（先頭が「〜全般」でないもの）は、
     見出しにキーワードが無くてもそのトピックに当たりの強さ 0.5 で当たったものとし、そのトピックの点を 1.5 倍にする。
   - タイトルがどのトピックにも当たらない記事は採らない（要約だけの当たりは加点にとどめる）。
   - 各記事の「主トピック」= タイトルでの当たりの強さが最大のトピック（同点なら重みの小さい＝より専門的なほう）。
3. 同じ話題のまとめ: 見出しの特徴語（珍しい語ほど重い）の重なりで同じニュースを1つにまとめ、
   点の高い記事（RSS の直接リンクを少し優先）を代表にする。前回までに選んだ記事・既読ソースの最新記事と
   同じ話題のものは落とす。
4. 選抜: 枠（例: 30件）をプロファイルの「配分」でトピックに割り振り、主トピックごとに点の高い順に埋める。
   候補が足りないトピックの余りは、全体の点の高い順で埋める。1つの媒体からは上限件数まで。
"""
from __future__ import annotations

import datetime as dt
import math
import re
import unicodedata
import urllib.parse
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from collect import Item
from topics import Topic, topic_from_dict

MAX_AGE_HOURS = 72
FRESH_HALF_LIFE_HOURS = 72
LANG_MISMATCH = 0.5
SUMMARY_FACTOR = 0.5
# 見出しの特徴語の重なり（IDF 重み付き Jaccard）。2026-09-29 の実測で、同じ話題の組は 0.18〜0.46、
# 別の話題の組は 0.03〜0.20 と重なったため、2段にしている。
SAME_STORY = 0.30        # これ以上は「同じ話題」としてまとめる（説明欄の「同じ話題: 他N媒体」）
DIVERSITY = 0.18         # 最終選抜で、既に選んだ記事とこれ以上似ていれば見送る
GOOGLE_FACTOR = 0.85     # Googleニュース経由（転送リンク・雑多な媒体が混ざる）の点に掛ける
SPECIALIST = 1.5         # 専門媒体がその専門トピックの記事を出したときの倍率
BUZZ_PER_SOURCE = 0.08   # 同じ話題を報じた他の媒体1つあたりの加点
BUZZ_MAX_SOURCES = 10
SPECIALIST_BASE = 0.5    # 専門媒体の記事が見出しにキーワードを含まないときの、専門トピックへの当たりの強さ
DEAL_TITLE = re.compile(r"^(Grab|Snag|Save|Get) |\$\d[\d,.]* off|\d+% off|\bdeals?\b|Prime Day|Black Friday|Cyber Monday", re.I)
RSS_REP_RATIO = 0.8      # 同じ話題の代表は、点がこの割合以上なら RSS（直接取得した媒体）の記事を優先する
AD_TITLE = re.compile(r"【PR】|［PR］|\[PR\]|（PR）|\(PR\)|\bSponsored\b|\bSPONSORED\b")


@dataclass
class Profile:
    topics: list[Topic]           # 採点に使うトピック
    vetoes: list[Topic]           # 「集めない」話題
    weights: dict[str, float]
    allocation: dict[str, float]  # 配分（合計 1）
    kw_weights: dict[str, dict[str, float]]
    known_domains: set[str]
    known_publishers: set[str]


def load_profile(data: dict) -> Profile:
    topics, vetoes = [], []
    for d in data["topics"]:
        (topics if d.get("collect", True) else vetoes).append(topic_from_dict(d))
    return Profile(
        topics=topics, vetoes=vetoes,
        weights={d["name"]: d["weight"] for d in data["topics"]},
        allocation={d["name"]: d.get("allocation", 0) for d in data["topics"] if d.get("collect", True)},
        kw_weights={d["name"]: d.get("keyword_weights", {}) for d in data["topics"]},
        known_domains=set(data["known_domains"]),
        known_publishers={norm_name(n) for n in data.get("known_publishers", [])},
    )


def norm_name(s: str) -> str:
    return re.sub(r"[\s・｜|]+", "", unicodedata.normalize("NFKC", s)).lower()


def domain_matches(domain: str, domains: set[str]) -> bool:
    return any(domain == d or domain.endswith("." + d) for d in domains)


# ---------- 除外 ----------

def exclusion_reason(item: Item, profile: Profile, blocked: list[str]) -> str:
    if item.domain and domain_matches(item.domain, profile.known_domains):
        return "既読ソース"
    if item.via != "RSS" and norm_name(item.source) in profile.known_publishers:
        return "既読ソース"
    if AD_TITLE.search(item.title):
        return "広告記事"
    if item.lang == "en" and DEAL_TITLE.search(item.title):
        return "セール情報"
    if item.via == "Googleニュース" and item.source.startswith("株式会社"):
        return "企業の自社発表"
    blocked_names = {norm_name(b) for b in blocked}
    blocked_domains = {b.lower() for b in blocked if "." in b and " " not in b}
    if norm_name(item.source) in blocked_names or (item.domain and domain_matches(item.domain, blocked_domains)):
        return "除外する媒体"
    for v in profile.vetoes:
        if v.match(item.title) or len(set(v.match(item.summary))) >= 2:
            return f"集めない話題（{v.name}）"
    return ""


# ---------- 採点 ----------

def is_specialist(source_topics: str, topic_name: str) -> bool:
    """収集元の「主なトピック」欄の先頭に、トピック名の一部（「半導体」「宇宙」など）が含まれるか。
    先頭が「〜全般」の総合媒体は専門媒体とみなさない。"""
    head = re.split(r"[、,]", source_topics, maxsplit=1)[0]
    if not head or "全般" in head:
        return False
    parts = [p for p in re.split(r"[・（）()、\s]+", topic_name) if len(p) >= 2 and p != "ほか"]
    return any(p in head for p in parts)


def score_item(item: Item, profile: Profile, now: dt.datetime) -> None:
    total = 0.0
    matched = {}
    best = (0.0, 0.0, 0.0, "")  # (タイトルでの当たり, 全体の当たり, -重み, 名前)。言語に関係なく「何の記事か」で決める
    for t in profile.topics:
        in_title = t.match(item.title)
        in_summary = [k for k in t.match(item.summary) if k not in in_title]
        specialist = bool(item.source_topics) and is_specialist(item.source_topics, t.name)
        if not in_title and not in_summary and not specialist:
            continue
        kw = profile.kw_weights.get(t.name, {})
        miss = 1.0 - (SPECIALIST_BASE if specialist and not in_title else 0.0)
        for k in in_title:
            miss *= 1 - kw.get(k, 0.4)
        title_relevance = 1 - miss
        for k in in_summary:
            miss *= 1 - kw.get(k, 0.4) * SUMMARY_FACTOR
        relevance = 1 - miss
        lang_factor = 1.0 if (not t.lang or t.lang == item.lang) else LANG_MISMATCH
        weight = profile.weights.get(t.name, 0.5)
        contrib = weight * relevance * lang_factor
        if specialist:
            contrib *= SPECIALIST
        total += contrib
        matched[t.name] = {"keywords": (in_title + in_summary) or [f"専門媒体: {item.source}"], "contrib": round(contrib, 3)}
        best = max(best, (round(title_relevance, 3), round(relevance, 3), -weight, t.name))
    age_h = max(0.0, (now - item.published).total_seconds() / 3600) if item.published else 0.0
    item.fresh = 0.5 ** (age_h / FRESH_HALF_LIFE_HOURS) * (GOOGLE_FACTOR if item.via == "Googleニュース" else 1.0)
    item.score = round(total * item.fresh, 4)
    item.topics = dict(sorted(matched.items(), key=lambda kv: -kv[1]["contrib"]))
    item.primary = best[3] if best[0] > 0 else ""  # タイトルが当たらなければ主トピック無し＝採らない


# ---------- 同じ話題の判定 ----------

TRACKING = re.compile(r"^(utm_|fbclid|gclid|ref$|ref_|cmpid|ncid|sr_share)")
EN_STOP = set("""a an the to of and or in on for with as at by is are was were be been its it from new says say said how
what why who when after over amid into this that these those your you we our their his her will would can could may
has have had about more up out not no vs via than just now here there first last year years day week report reports
""".split())


def normalize_url(url: str) -> str:
    u = urllib.parse.urlparse(url.strip())
    q = [(k, v) for k, v in urllib.parse.parse_qsl(u.query) if not TRACKING.match(k)]
    host = u.netloc.lower().removeprefix("www.")
    return urllib.parse.urlunparse(("https", host, u.path.rstrip("/"), "", urllib.parse.urlencode(q), ""))


def story_tokens(title: str) -> set[str]:
    """見出しの特徴語。英語は単語（所有格と複数形の s を落とす）、日本語はカタカナ語・漢字の2文字組・英数字。"""
    t = unicodedata.normalize("NFKC", title).lower().replace("’", "'")
    toks = set()
    for w in re.findall(r"[a-z0-9][a-z0-9\-\.]*[a-z0-9]|[a-z0-9]", t):
        w = re.sub(r"'s$", "", w)
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        if w not in EN_STOP and len(w) > 1:
            toks.add(w)
    toks.update(re.findall(r"[゠-ヿ]{2,}", t))           # カタカナ語
    for run in re.findall(r"[一-鿿]{2,}", t):             # 漢字は2文字ずつ
        toks.update(run[i:i + 2] for i in range(len(run) - 1))
    return toks


class StoryIndex:
    """記事を「同じ話題」ごとにまとめる。珍しい語が重なるほど同じ話題とみなす（IDF 重み付き Jaccard）。"""

    def __init__(self, idf: dict[str, float], default_idf: float):
        self.idf, self.default_idf = idf, default_idf
        self.groups: list[set[str]] = []     # 各グループの代表の特徴語
        self.index: dict[str, list[int]] = defaultdict(list)

    def w(self, tok: str) -> float:
        return self.idf.get(tok, self.default_idf)

    def similarity(self, a: set[str], b: set[str]) -> float:
        union = sum(self.w(t) for t in a | b)
        return sum(self.w(t) for t in a & b) / union if union else 0.0

    def find(self, toks: set[str]) -> int | None:
        cands = {g for t in toks for g in self.index.get(t, ())}
        best, best_sim = None, SAME_STORY
        for g in cands:
            s = self.similarity(toks, self.groups[g])
            if s >= best_sim:
                best, best_sim = g, s
        return best

    def add(self, toks: set[str]) -> int:
        self.groups.append(toks)
        gid = len(self.groups) - 1
        for t in toks:
            self.index[t].append(gid)
        return gid


def build_idf(titles: list[str]) -> tuple[dict[str, float], float]:
    df = Counter(t for title in titles for t in story_tokens(title))
    n = max(len(titles), 1)
    return {t: math.log((n + 1) / (c + 1)) + 1 for t, c in df.items()}, math.log(n + 1) + 1


# ---------- 選抜 ----------

@dataclass
class RankResult:
    selected: list[Item]
    candidates: int
    excluded: dict[str, int]
    too_old: int
    below_threshold: int
    already_seen: int
    same_story: int
    capped: int
    quotas: dict[str, int] = field(default_factory=dict)


def quotas_for(allocation: dict[str, float], limit: int) -> dict[str, int]:
    """配分を整数の枠にする（最大剰余法）。"""
    raw = {k: v * limit for k, v in allocation.items()}
    q = {k: int(v) for k, v in raw.items()}
    for k in sorted(raw, key=lambda k: -(raw[k] - q[k]))[: limit - sum(q.values())]:
        q[k] += 1
    return q


def rank(items: list[Item], profile: Profile, blocked: list[str], *, now: dt.datetime, limit: int,
         min_score: float, per_source_cap: int, seen_titles: list[tuple[str, str]]) -> RankResult:
    excluded: Counter = Counter()
    fresh: list[Item] = []
    too_old = below = 0
    for it in items:
        if it.published and (now - it.published).total_seconds() > MAX_AGE_HOURS * 3600:
            too_old += 1
            continue
        reason = exclusion_reason(it, profile, blocked)
        if reason:
            excluded[reason] += 1
            continue
        score_item(it, profile, now)
        if not it.primary or it.score < min_score:
            below += 1
            continue
        fresh.append(it)

    # 既に見たもの（前回までの選択・既読ソースの最新記事）を先に登録しておき、同じ話題なら落とす
    idf, default_idf = build_idf([it.title for it in fresh] + [t for _, t in seen_titles])
    stories = StoryIndex(idf, default_idf)
    seen_urls = {normalize_url(u) for u, _ in seen_titles if u}
    for _, title in seen_titles:
        toks = story_tokens(title)
        if toks and stories.find(toks) is None:
            stories.add(toks)
    n_seen_groups = len(stories.groups)

    fresh.sort(key=lambda it: -it.score)
    reps: list[Item] = []
    rep_of: dict[int, Item] = {}
    already = same = 0
    for it in fresh:
        toks = story_tokens(it.title)
        if normalize_url(it.link) in seen_urls:
            already += 1
            continue
        gid = stories.find(toks) if toks else None
        if gid is not None and gid < n_seen_groups:
            already += 1
            continue
        if gid is not None:
            same += 1
            rep = rep_of[gid]
            if rep.via != "RSS" and it.via == "RSS" and it.score >= RSS_REP_RATIO * rep.score:
                # 代表を RSS の記事に入れ替える（地方紙の転載などより、選んだ媒体の直接リンクを出す）
                it.related = rep.related + [rep.source]
                rep_of[gid] = it
                reps[reps.index(rep)] = it
            else:
                rep.related.append(it.source)
            continue
        gid = stories.add(toks)
        rep_of[gid] = it
        reps.append(it)

    # 同じ話題を多くの媒体が報じていれば、その分だけ点を上げる
    for it in reps:
        n = len(set(it.related) - {it.source})
        it.buzz = 1 + BUZZ_PER_SOURCE * min(n, BUZZ_MAX_SOURCES)
        it.score = round(it.score * it.buzz, 4)

    # 配分どおりの枠で主トピックごとに選ぶ。枠の中は「そのトピック自体の点 × 新しさ」の順（小数2桁で同点なら合計点）。
    # 合計点だけで並べると、1語だけ当たった他トピックの記事が、別トピックの点で押し上げられて枠を奪うため。
    # 候補の足りない枠の余りは全体の点数順
    quotas = quotas_for(profile.allocation, limit)
    by_topic: dict[str, list[Item]] = defaultdict(list)
    for it in reps:
        by_topic[it.primary].append(it)
    for name, lst in by_topic.items():
        lst.sort(key=lambda it: (-round(it.topics[name]["contrib"] * it.fresh * it.buzz, 2), -it.score))
    picked_tokens: list[set[str]] = []
    selected: list[Item] = []
    chosen: set[int] = set()
    per_source: Counter = Counter()
    capped = 0

    diverse_skip = 0

    def take(it: Item) -> bool:
        nonlocal capped, diverse_skip
        if id(it) in chosen:
            return False
        key = norm_name(it.source)
        if per_source[key] >= per_source_cap:
            capped += 1
            return False
        toks = story_tokens(it.title)
        if any(stories.similarity(toks, p) >= DIVERSITY for p in picked_tokens):
            diverse_skip += 1
            return False
        per_source[key] += 1
        chosen.add(id(it))
        picked_tokens.append(toks)
        selected.append(it)
        return True

    for name, q in sorted(quotas.items(), key=lambda kv: -kv[1]):
        got = 0
        for it in by_topic.get(name, []):
            if got >= q:
                break
            got += take(it)
    for it in sorted(reps, key=lambda it: -it.score):
        if len(selected) >= limit:
            break
        take(it)
    selected.sort(key=lambda it: -it.score)
    return RankResult(selected, len(items), dict(excluded), too_old, below, already, same + diverse_skip, capped, quotas)
