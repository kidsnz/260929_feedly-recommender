"""英語の見出しと日本語の見出しが「同じニュース」かを判定する。

日本語の記事にも英字のまま残る製品名・固有名詞（dots, World Labs, GPT-6 Astra）を手がかりにする。
「OpenAI」「Meta」のようなよく出る名前だけが共通しても同じとはみなさない（別のニュースでも出るため）。

判定 = 共通する特徴語が2つ以上 かつ 次のどちらか
  (a) 固有語（下記）のうち、既読の見出しで RARE_DF 回以下のものが1つ以上
  (b) 同じく EXTRA_DF 回以下のものが2つ以上（「GPT-6」+「Astra」のような2語の名前）
固有語 = 日本語の見出しに英字のまま書かれ、かつ英語の見出しで大文字始まり（Dots, World Labs）の共通語。
既読の見出しはほぼ日本語なので、英語の一般語（developer, platform）も「0回」と数えられてしまう。
英語側で小文字の語（"developer conference"）を外すことで、一般語を固有語と取り違えないようにしている。
英語の一般語の一覧（GENERIC）は、見出しが全語大文字始まり（Title Case）の記事のための予備。

2026-09-29 に実記事から作った正解表（同じ11組・別13組）で測った結果: 正しく一致 7/11、誤って一致 0/13（同日の実運転で見つかった誤一致1組を追加した後）
（条件を決めるのに使ったのと同じ記事で測っているので、実際の成績はこれより低い可能性がある）。
取り逃しは多いが、間違って差し替える・間違って「既に見た」として消すことはしない方を選んでいる。
"""
from __future__ import annotations

import re
import unicodedata

RARE_DF = 5
EXTRA_DF = 10

# カタカナ・漢字の表記を英語に直して照合する（日本語の見出しでは英字でなくカタカナで書かれる名前）
KATAKANA_ALIASES = {
    "エヌビディア": "nvidia", "アンソロピック": "anthropic", "オープンAI": "openai", "オープンエーアイ": "openai",
    "グーグル": "google", "アップル": "apple", "マイクロソフト": "microsoft", "アマゾン": "amazon", "メタ": "meta",
    "テスラ": "tesla", "サムスン": "samsung", "インテル": "intel", "クアルコム": "qualcomm", "アーム": "arm",
    "ソニー": "sony", "ネットフリックス": "netflix", "ユーチューブ": "youtube", "ディープシーク": "deepseek",
    "ジェミニ": "gemini", "クロード": "claude", "チャットGPT": "chatgpt", "アルトマン": "altman",
    "ザッカーバーグ": "zuckerberg", "マスク": "musk", "アモデイ": "amodei", "フアン": "huang", "スペースX": "spacex",
    "エックスAI": "xai", "パランティア": "palantir", "オラクル": "oracle", "ブロードコム": "broadcom",
    "ハイニックス": "hynix", "マイクロン": "micron", "ミューズ": "muse", "ウェイモ": "waymo",
    "エージェント": "agent", "ロボタクシー": "robotaxi", "ヒューマノイド": "humanoid", "スターシップ": "starship",
    "目論見書": "ipo", "上場": "ipo", "買収": "acquire", "半導体": "chip", "脆弱性": "vulnerability",
}

STOP = set("""a an the to of and or in on for with as at by is are was were be been its it from new says say said how
what why who when after over amid into this that these those your you we our their his her will would can could may
has have had about more up out not no vs via than just now here there first last year years day week report reports
ai launch launche announce use company""".split())
GENERIC = set("""platform incident safety security update feature tool app service system model data network center
cloud device tech market plan deal risk test user work project hub agent chip acquire billion million""".split())
WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-\.]*[A-Za-z0-9]|[A-Za-z0-9]")


def _ascii_words(title: str) -> set[str]:
    out = set()
    for w in WORD.findall(unicodedata.normalize("NFKC", title)):
        w = re.sub(r"'s$", "", w.lower())
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        if w in ("buy", "buys", "acquisition"):
            w = "acquire"
        if w not in STOP and len(w) > 1:
            out.add(w)
    return out


def xl_tokens(title: str) -> set[str]:
    """英日共通の特徴語: 英字の語 ＋ カタカナ・漢字表記を英語に直した語。"""
    t = unicodedata.normalize("NFKC", title)
    return _ascii_words(t) | {en for ja, en in KATAKANA_ALIASES.items() if ja in t}


def _capitalized_words(title: str) -> set[str]:
    """英語の見出しで大文字始まり（または数字を含む）の語。"""
    caps = set()
    for w in WORD.findall(unicodedata.normalize("NFKC", title)):
        if w[0].isupper() or any(c.isdigit() for c in w):
            caps |= _ascii_words(w)
    return caps


def same_story(en_title: str, ja_title: str, df: dict[str, int]) -> bool:
    """英語の見出し en_title と日本語の見出し ja_title が同じニュースか。df は既読の見出しでの出現回数。"""
    common = xl_tokens(en_title) & xl_tokens(ja_title)
    if len(common) < 2:
        return False
    literal = [t for t in common & _ascii_words(ja_title) & _capitalized_words(en_title)
               if t not in GENERIC and not t.replace(".", "").isdigit()]
    rare = [t for t in literal if df.get(t, 0) <= RARE_DF]
    extra = [t for t in literal if df.get(t, 0) <= EXTRA_DF]
    return bool(rare) or len(extra) >= 2


def is_japanese(title: str) -> bool:
    return bool(re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", title))
