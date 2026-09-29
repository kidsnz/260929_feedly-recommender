"""採点・除外・同じ話題のまとめ・トピック枠・フィード出力のテスト。

    .venv/bin/python -m unittest discover -s tests -v
"""
import datetime as dt
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import feedparser  # noqa: E402

from build_feed import item_to_record, write_feed  # noqa: E402
from collect import Item  # noqa: E402
from rank import Profile, rank  # noqa: E402
from topics import Topic  # noqa: E402

NOW = dt.datetime(2026, 9, 29, 12, 0, tzinfo=dt.timezone.utc)


def profile(allocation=None):
    topics = [
        Topic("AI", keywords=["AI", "生成AI"], english=["artificial intelligence"], lang="en"),
        Topic("ゲーム", keywords=["ゲーム", "任天堂"], lang="ja"),
        Topic("宇宙", keywords=["宇宙", "ロケット"], english=["rocket"]),
    ]
    vetoes = [Topic("暗号資産", keywords=["ビットコイン"], english=["Bitcoin", "crypto"], collect=False)]
    return Profile(
        topics=topics, vetoes=vetoes,
        weights={"AI": 1.0, "ゲーム": 0.5, "宇宙": 0.5},
        allocation=allocation or {"AI": 0.5, "ゲーム": 0.25, "宇宙": 0.25},
        kw_weights={"AI": {"AI": 1.0}, "ゲーム": {"ゲーム": 1.0}, "宇宙": {"宇宙": 1.0, "rocket": 0.7}},
        known_domains={"gigazine.net"}, known_publishers={"gigazine"},
    )


def item(title, *, domain="example.com", source="Example", via="RSS", hours=1, summary="", source_topics=""):
    return Item(title=title, link=f"https://{domain}/{abs(hash(title))}", source=source, via=via,
                collector=source, feed_url=f"https://{domain}/feed", domain=domain,
                published=NOW - dt.timedelta(hours=hours), summary=summary,
                lang="ja" if any("぀" <= c <= "鿿" for c in title) else "en", source_topics=source_topics)


def run(items, *, limit=10, prof=None, seen=(), blocked=()):
    return rank(items, prof or profile(), list(blocked), now=NOW, limit=limit, min_score=0.05,
                per_source_cap=10, seen_titles=list(seen))


def titles(res):
    return [it.title for it in res.selected]


class Exclusion(unittest.TestCase):
    def test_known_domain_is_excluded(self):
        res = run([item("AI news from a site I already read", domain="gigazine.net")])
        self.assertEqual(titles(res), [])
        self.assertEqual(res.excluded.get("既読ソース"), 1)

    def test_known_publisher_via_google_is_excluded(self):
        res = run([item("AI news", domain="", source="GIGAZINE", via="Googleニュース")])
        self.assertEqual(titles(res), [])

    def test_veto_topic_is_excluded(self):
        res = run([item("Bitcoin and AI trading bots surge")])
        self.assertEqual(titles(res), [])
        self.assertIn("集めない話題（暗号資産）", res.excluded)

    def test_blocked_publisher_ads_and_deals(self):
        res = run([item("AI stock picks", source="PR TIMES", via="Googleニュース"),
                   item("【PR】AIで仕事がはかどる"),
                   item("Grab this AI laptop for $499")],
                  blocked=["PR TIMES"])
        self.assertEqual(titles(res), [])

    def test_too_old_is_dropped(self):
        res = run([item("AI model released", hours=100)])
        self.assertEqual(res.too_old, 1)

    def test_summary_only_match_is_not_selected(self):
        res = run([item("A quiet week in review", summary="lots of AI and AI")])
        self.assertEqual(titles(res), [])


class Stories(unittest.TestCase):
    def test_same_story_is_merged(self):
        res = run([item("OpenAI launches Dots, always-on AI agents in ChatGPT", source="A"),
                   item("OpenAI launches Dots, always-on AI agents", source="B"),
                   item("Rocket reaches orbit for the first time", source="C")])
        self.assertEqual(len(res.selected), 2)
        merged = [it for it in res.selected if "Dots" in it.title][0]
        self.assertEqual(merged.related, ["B"])

    def test_story_already_seen_is_dropped(self):
        res = run([item("OpenAI launches Dots, always-on AI agents in ChatGPT")],
                  seen=[("https://gigazine.net/x", "OpenAI launches Dots, always-on AI agents")])
        self.assertEqual(titles(res), [])
        self.assertEqual(res.already_seen, 1)

    def test_bigger_story_ranks_higher(self):
        # 話題の大きさが無ければ、新しい方（benchmark, 0時間前）が上に来る条件にしてある
        big = [item("Meta expands Muse AI agent to small businesses", source=f"S{i}", hours=10) for i in range(5)]
        res = run(big + [item("New AI benchmark released today", source="X", hours=0)])
        self.assertIn("Muse", res.selected[0].title)


class Selection(unittest.TestCase):
    def test_quota_gives_small_topic_a_slot(self):
        # 見出しが互いに似ていない AI 記事（同じ話題にまとめられないように）
        ai = [item(t, source=f"S{i}") for i, t in enumerate([
            "Nvidia unveils AI chip roadmap", "Apple adds AI features to Photos", "Startup raises funds for AI tutors",
            "Hospitals test AI triage tools", "Courts weigh AI copyright cases"])]
        space = [item("ロケット打ち上げ成功、宇宙へ", source="sorae", hours=40)]
        res = run(ai + space, limit=2, prof=profile({"AI": 0.5, "宇宙": 0.5, "ゲーム": 0.0}))
        self.assertEqual(len(res.selected), 2)
        self.assertTrue(any("宇宙" in t for t in titles(res)), titles(res))

    def test_preferred_language_scores_higher(self):
        res = run([item("AI agent released"), item("AIエージェントを公開")], limit=5)
        by_lang = {it.lang: it.score for it in res.selected}
        self.assertGreater(by_lang["en"], by_lang["ja"])

    def test_specialist_source_counts_without_keyword(self):
        res = run([item("Crew-13 at the launch pad", source="NASA", source_topics="宇宙")])
        self.assertEqual(len(res.selected), 1)
        self.assertEqual(res.selected[0].primary, "宇宙")

    def test_general_source_needs_keyword(self):
        res = run([item("Crew-13 at the launch pad", source="General", source_topics="宇宙全般、科学")])
        self.assertEqual(titles(res), [])


class JapaneseVersion(unittest.TestCase):
    def prof(self):
        p = profile()
        p.xl_df = {"openai": 300, "dot": 1}
        p.lang_of = {"AI": "en", "ゲーム": "ja", "宇宙": ""}
        return p

    def test_english_story_is_replaced_by_japanese_version(self):
        en = item("OpenAI launches Dots, always-on AI agents", source="TechCrunch")
        ja = item("OpenAI、常時稼働のAIエージェント「dots」を発表", source="ITmedia NEWS")
        res = run([en, ja], prof=self.prof())
        self.assertEqual(len(res.selected), 1)
        self.assertIs(res.selected[0].ja_alt, ja)
        rec = item_to_record(res.selected[0], NOW)
        self.assertEqual(rec["title"], ja.title)
        self.assertEqual(rec["source"], "ITmedia NEWS")
        self.assertEqual(rec["original"]["source"], "TechCrunch")

    def test_english_story_stays_when_no_japanese_version(self):
        en = item("OpenAI launches Dots, always-on AI agents", source="TechCrunch")
        other = item("OpenAIのAIエージェントが豪州政府サイトに侵入", source="ITmedia NEWS")
        res = run([en, other], prof=self.prof())
        dots = [it for it in res.selected if "Dots" in it.title]
        self.assertEqual(len(dots), 1)
        self.assertIsNone(dots[0].ja_alt)

    def test_story_seen_in_japanese_known_source_is_dropped(self):
        en = item("OpenAI launches Dots, always-on AI agents", source="TechCrunch")
        res = run([en], prof=self.prof(), seen=[("https://gigazine.net/x", "OpenAIが常時稼働AIエージェント「dots」を発表")])
        self.assertEqual(titles(res), [])


class FeedOutput(unittest.TestCase):
    def test_feed_is_valid_rss_with_topics_in_description(self):
        res = run([item("AI agent released"), item("ロケット打ち上げ成功、宇宙へ", source="sorae")])
        records = [item_to_record(it, NOW) for it in res.selected]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "feed.xml"
            write_feed(records, path, NOW)
            f = feedparser.parse(path.read_bytes())
        self.assertFalse(f.bozo, f.get("bozo_exception"))
        self.assertEqual(f.version, "rss20")
        self.assertEqual(len(f.entries), 2)
        for e in f.entries:
            self.assertIn("該当トピック", e.summary)
            self.assertTrue(e.get("tags"))


if __name__ == "__main__":
    unittest.main()
