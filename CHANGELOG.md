# Changelog

このプロジェクトの変更履歴。形式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/)、バージョンは [Semantic Versioning](https://semver.org/lang/ja/) に従う。

## [1.1.0] - 2026-09-29

### Added

- AI・テック（優先言語が英語のトピック）で選んだ英語記事に、同じニュースの日本語記事があれば日本語記事に差し替える。説明欄と確認用ページに英語の原典を残す
- 英語と日本語の見出しが同じニュースかを判定する `src/crosslang.py`（日本語の見出しに英字で残る固有名詞で照合）と、その正解表のテスト
- `profile/profile.json` に既読見出しでの特徴語の出現回数（`xl_df`）
- 日本語版さがし用の Googleニュース検索語（AI・半導体・テック大手・セキュリティ）

### Changed

- 既読ソースと同じニュースの判定を、英語と日本語をまたいで行う
- 既読ソースとして除外した記事の見出しも「既に見た話題」に加える
- Yahoo!ニュースの記事は、見出し末尾の（媒体名）を出典として扱う（既読ソースの転載を除外するため）
- 出典名が「合同会社」「有限会社」で始まる Googleニュースの記事も、企業の自社発表として除外する
- 画像ギャラリーの分割ページ（【画像】… 2/4 など）を除外する

## [1.0.0] - 2026-09-29

### Added

- Feedly「Recently read」の保存ページ（.mhtml / .html）から既読記事を CSV に抜き出す `src/extract_read.py`
- 既読記事のタイトルから好みのプロファイル（`profile/profile.md` / `profile/profile.json`）を作る `src/build_profile.py`
  - トピック定義は人が編集する `profile/topics.md`（キーワード・英語・除外・倍率・優先言語・集めない話題）
  - 新しさの重みは半減期 180 日。倍率を掛けたあと最大 1.0 に揃え直し、配分（合計 100%）を出す
- RSS 約75本・Googleニュース検索・はてなブックマーク検索から集める `src/collect.py`（収集元は `config/sources.md`）
- 採点・除外・同じ話題のまとめ・トピック配分どおりの選抜を行う `src/rank.py`
- `feed.xml`（RSS 2.0）と確認用ページ `index.html` を作る `src/build_feed.py`
- 毎日 06:00 JST に実行して GitHub Pages に公開する GitHub Actions（`.github/workflows/update.yml`）
- 照合ルールと選抜のテスト（`tests/`）

[1.1.0]: https://github.com/kidsnz/260929_feedly-recommender/releases/tag/v1.1.0
[1.0.0]: https://github.com/kidsnz/260929_feedly-recommender/releases/tag/v1.0.0
