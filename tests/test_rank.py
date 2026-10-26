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
        Topic("AI", keywords=["AI", "生成AI"], english=["artificial intelligence"]),
        Topic("ゲーム", keywords=["ゲーム", "任天堂"]),
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
    def test_english_title_is_excluded(self):
        res = run([item("AI agent released"), item("AIエージェントを公開")])
        self.assertEqual(titles(res), ["AIエージェントを公開"])
        self.assertEqual(res.excluded.get("英語記事"), 1)

    def test_english_title_from_known_source_still_counts_as_seen(self):
        # 既読ソースの記事は言語に関係なく「既読ソース」として数える（同じ話題を「既に見た」に入れるため）
        res = run([item("AI news from a site I already read", domain="gigazine.net")])
        self.assertEqual(res.excluded, {"既読ソース": 1})

    def test_known_domain_is_excluded(self):
        res = run([item("既に読んでいる媒体のAIニュース", domain="gigazine.net")])
        self.assertEqual(titles(res), [])
        self.assertEqual(res.excluded.get("既読ソース"), 1)

    def test_known_publisher_via_google_is_excluded(self):
        res = run([item("AIのニュース", domain="", source="GIGAZINE", via="Googleニュース")])
        self.assertEqual(titles(res), [])

    def test_veto_topic_is_excluded(self):
        res = run([item("ビットコインとAI取引ボットが急増")])
        self.assertEqual(titles(res), [])
        self.assertIn("集めない話題（暗号資産）", res.excluded)

    def test_blocked_publisher_and_ads(self):
        res = run([item("AI関連株の注目銘柄", source="PR TIMES", via="Googleニュース"),
                   item("【PR】AIで仕事がはかどる")],
                  blocked=["PR TIMES"])
        self.assertEqual(titles(res), [])

    def test_too_old_is_dropped(self):
        res = run([item("新しいAIモデルを公開", hours=100)])
        self.assertEqual(res.too_old, 1)

    def test_summary_only_match_is_not_selected(self):
        res = run([item("今週のふりかえり", summary="AIとAIの話題が多い")])
        self.assertEqual(titles(res), [])


class Stories(unittest.TestCase):
    def test_same_story_is_merged(self):
        res = run([item("OpenAI、常時稼働のAIエージェント「Dots」をChatGPTで公開", source="A"),
                   item("OpenAI、常時稼働のAIエージェント「Dots」を公開", source="B"),
                   item("ロケットが初めて軌道に到達", source="C")])
        self.assertEqual(len(res.selected), 2)
        merged = [it for it in res.selected if "Dots" in it.title][0]
        self.assertEqual(merged.related, ["B"])

    def test_story_already_seen_is_dropped(self):
        res = run([item("OpenAI、常時稼働のAIエージェント「Dots」をChatGPTで公開")],
                  seen=[("https://gigazine.net/x", "OpenAI、常時稼働のAIエージェント「Dots」を公開")])
        self.assertEqual(titles(res), [])
        self.assertEqual(res.already_seen, 1)

    def test_bigger_story_ranks_higher(self):
        # 話題の大きさが無ければ、新しい方（ベンチマーク, 0時間前）が上に来る条件にしてある
        big = [item("Meta、AIエージェント「Muse」を中小企業向けに拡大", source=f"S{i}", hours=10) for i in range(5)]
        res = run(big + [item("新しいAIベンチマークを本日公開", source="X", hours=0)])
        self.assertIn("Muse", res.selected[0].title)


class Selection(unittest.TestCase):
    def test_quota_gives_small_topic_a_slot(self):
        # 見出しが互いに似ていない AI 記事（同じ話題にまとめられないように）
        ai = [item(t, source=f"S{i}") for i, t in enumerate([
            "NVIDIAがAI半導体の計画を発表", "アップル、写真アプリにAI機能", "AI家庭教師の新興企業が資金調達",
            "病院でAIによる診療振り分けを試験", "裁判所がAIと著作権の訴訟を審理"])]
        space = [item("ロケット打ち上げ成功、宇宙へ", source="sorae", hours=40)]
        res = run(ai + space, limit=2, prof=profile({"AI": 0.5, "宇宙": 0.5, "ゲーム": 0.0}))
        self.assertEqual(len(res.selected), 2)
        self.assertTrue(any("宇宙" in t for t in titles(res)), titles(res))

    def test_specialist_source_counts_without_keyword(self):
        res = run([item("Crew-13が発射台に到着", source="sorae", source_topics="宇宙")])
        self.assertEqual(len(res.selected), 1)
        self.assertEqual(res.selected[0].primary, "宇宙")

    def test_general_source_needs_keyword(self):
        res = run([item("Crew-13が発射台に到着", source="General", source_topics="宇宙全般、科学")])
        self.assertEqual(titles(res), [])


class FeedOutput(unittest.TestCase):
    def test_feed_is_valid_rss_with_topics_in_description(self):
        res = run([item("AIエージェントを公開"), item("ロケット打ち上げ成功、宇宙へ", source="sorae")])
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
