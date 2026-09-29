"""照合ルールのテスト。当たるべきものと、当たってはいけないもの（誤爆）の両方を確かめる。

    .venv/bin/python -m unittest discover -s tests -v
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from topics import Topic, load_topics, match_all  # noqa: E402


def hits(term, text):
    return Topic("t", keywords=[term]).match(text)


class MatchRules(unittest.TestCase):
    def test_ascii_word_boundary(self):
        self.assertTrue(hits("AI", "生成AIが話題"))
        self.assertTrue(hits("AI", "AI agents are here"))
        self.assertFalse(hits("AI", "he said"))
        self.assertFalse(hits("SK", "Skills API で構築する"))
        self.assertTrue(hits("SK", "SK hynixが増産"))

    def test_case_sensitive_proper_nouns(self):
        self.assertTrue(hits("Meta", "Meta unveils glasses"))
        self.assertFalse(hits("Meta", "a meta-analysis of sleep"))
        self.assertFalse(hits("AI", "ai"))
        self.assertTrue(hits("NVIDIA", "Nvidia unveils new chips"))  # 5文字以上は区別しない

    def test_lowercase_terms_ignore_case(self):
        self.assertTrue(hits("crypto", "Crypto Markets Slide"))
        self.assertTrue(hits("semiconductor", "Semiconductors rally"))  # 複数形

    def test_multiword_and_hyphen(self):
        self.assertTrue(hits("self-driving", "self driving cars"))
        self.assertTrue(hits("Claude Code", "Claude Codeの新機能"))

    def test_fullwidth_normalized(self):
        self.assertTrue(hits("スペースX", "スペースＸのAI部門"))
        self.assertTrue(hits("AI", "ＡＩ新時代"))

    def test_exclude(self):
        t = Topic("health", keywords=["脳"], exclude=["首脳"])
        self.assertTrue(t.match("脳細胞の移植"))
        self.assertFalse(t.match("米中首脳会談"))


class ShippedTopics(unittest.TestCase):
    """profile/topics.md の実際の定義で、既知の誤爆が起きないこと。"""

    @classmethod
    def setUpClass(cls):
        cls.topics = load_topics()

    def test_known_false_positives(self):
        cases = {
            "Switch to a better bank account": "ゲーム",
            "A meta-analysis of coffee studies": "テック大手（Google・Apple・Meta・Amazon・Microsoft ほか）",
            "米中首脳が会談": "健康・医療・生物",
            "Make room: small space living tips": "宇宙・科学研究",
            "SEKIROの最高難度でプレイ、フロム脳の超本音トーク": "健康・医療・生物",
            "最後までがんばる選手たち": "健康・医療・生物",
        }
        for text, topic in cases.items():
            with self.subTest(text=text):
                self.assertNotIn(topic, match_all(self.topics, text))

    def test_known_true_positives(self):
        cases = {
            "Nvidia unveils new Blackwell chips": "半導体・データセンター",
            "Anthropic releases Claude Fable 5.1": "Anthropic・Claude",
            "Nintendo Switch 2 sales top 20 million": "ゲーム",
            "Nvidia and TSMC expand chip output": "半導体・データセンター",
        }
        for text, topic in cases.items():
            with self.subTest(text=text):
                self.assertIn(topic, match_all(self.topics, text))


if __name__ == "__main__":
    unittest.main()
