"""英語と日本語の見出しが同じニュースかの判定のテスト。

正解表は 2026-09-29 の実記事から作った（同じ11組・別13組）。条件を決めたのと同じ記事なので、
ここで測れるのは「決めた条件どおりに動いているか」まで。実際の成績はこれより低い可能性がある。
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from crosslang import same_story  # noqa: E402

DF = json.loads((ROOT / "profile" / "profile.json").read_text(encoding="utf-8"))["xl_df"]

SAME = [
    ("OpenAI just launched its answer to Meta: 'always-on' AI agents called Dots", "OpenAI「dots」発表 会話後も仕事を続ける“常時稼働AI”が登場"),
    ("UK AI Security Institute finds GPT-6 Astra's rogue attack rate jumped", "「GPT-6 Astraは旧世代モデルよりサイバー攻撃を実行しやすい傾向にある」というイギリス政府機関の分析結果が公開される"),
    ("AMD buys AI world model startup World Labs for $8.2 billion", "AMD、フェイフェイ・リー博士のWorld Labsを約82億ドルで買収へ ハードとモデルを一体化したオープンAIエコシステム加速へ"),
    ("AMD buys AI world model startup World Labs for $8.2 billion", "AMDが3D世界を構築するAI企業「World Labs」を買収、「AIのゴッドマザー」が率いる画像・動画・3D空間の生成が可能な世界モデル"),
    ("Google Tests Flipkart Checkout in Gemini and Replaces Gems With Skills", "グーグル、Geminiのカスタムアプリ「Gem」を11月で終了 Skillへ移行"),
    ("ChatGPT Space is a shared hub for work projects and personal AI agents", "OpenAI、ChatGPT Space発表。チームがAIと働く「オフィス」"),
    ("OpenAI expands Codex and its API at DevDay with security scans, a Decisions API", "OpenAIが「Jev」に追従、「Decisions API」 Lunaで“リアルタイムに意思決定”"),
]
# 同じニュースだが、今の条件では取り逃す組（よく出る名前しか共通しない）。取り逃しが直ったら SAME へ移す
MISSED = [
    ("Anthropic's IPO filing shows soaring revenue, mounting costs, and existential risk", "アンソロピックIPO書類「強力なAI、人類存亡のリスク」 ロイター報道"),
    ("OpenAI CEO announces new AI agent and avoids mention of security concerns", "OpenAI、電話もメールも代わりにこなすAIエージェント「dots」を発表"),
]
DIFF = [
    ("OpenAI debuts personal AI agent Dot to rival Meta's Muse", "決済や予約などアプリ操作代行する、メタのAIエージェント「ミューズ」 誤動作リスクも"),
    ("OpenAI launches Dots, always-on AI agents in ChatGPT", "OpenAIのAIエージェントが豪州政府サイトに侵入、政府が知ったのは数カ月後"),
    ("Meta is expanding its AI agent Muse to small businesses", "メタの新パーソナルAIエージェント「Muse」。普及の鍵はユーザーの信頼"),
    ("First Thing: Anthropic warns of AI 'existential risk' as concerns emerge over Meta Muse", "Meta、メタバースからの戦略転換 AIグラスと大ヒット「Muse」が狙うもの"),
    ("Claude Code's Next Era — Thariq Shihipar, Anthropic", "アンソロピック、生成AI「Claude」で一時障害"),
    ("Netlist seeks US import ban on Micron chips used in Google and Nvidia AI servers", "NVIDIAですら1社では半導体は作れない――それでもAI時代の“勝者”になれたワケ"),
    ("OpenAI and Anthropic are reportedly investigating tens of thousands of agent incidents", "過去の障害を再現して Incident Agent を評価する"),
    ("Meta's new AI agent gave a stranger a user's home address", "Metaの最新AIエージェント、裏で「人間」が電話をかける試験運用が判明"),
    ("ChatGPT now reaches 1.2 billion people every week, OpenAI says", "OpenAI、ChatGPT Space発表。チームがAIと働く「オフィス」"),
    ("Thales and Google Cloud secure AI agents on the Gemini platform", "制御する「Open Agent Safety Platform」"),
    ("Lower the Cost of Building and Running Visual AI Agents with NVIDIA VSS", "NVIDIA、AIエージェントの「暴走」防ぐオープンソース基盤"),
    ("Here's why OpenAI is absent from Nvidia's industry-wide effort to end rogue agents", "NVIDIA、AIエージェントの「暴走」防ぐオープンソース基盤"),
    # 実運転で見つかった誤一致（英語の一般語 "developer" が既読見出しで0回だったため固有語に見えた）
    ("OpenAI CEO announces new AI agent and avoids mention of security concerns at developer conference",
     "コーディングエージェントにGoogle Cloudの専門知識とツールを組み込む「Google Cloud Developer Plugin for AI Coding Agents」発表"),
]


class CrossLanguage(unittest.TestCase):
    def test_same_stories_match(self):
        for en, ja in SAME:
            with self.subTest(en=en):
                self.assertTrue(same_story(en, ja, DF))

    def test_different_stories_do_not_match(self):
        # 最も重要: 別のニュースを同じと判定すると、取りこぼし記事を「既に見た」として消してしまう
        for en, ja in DIFF:
            with self.subTest(en=en):
                self.assertFalse(same_story(en, ja, DF))

    def test_known_misses_are_still_missed(self):
        # 取り逃しを把握しておくためのテスト（条件を緩めてこれが通らなくなったら、DIFF が守られているか確認）
        for en, ja in MISSED:
            with self.subTest(en=en):
                self.assertFalse(same_story(en, ja, DF))


if __name__ == "__main__":
    unittest.main()
