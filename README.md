# 取りこぼしニュース（feedly-recommender）

Feedly で読んだ記事の傾向から好みのプロファイルを作り、**まだ読んでいない媒体**から関連ニュースを毎日集めて RSS フィードにする個人用ツール。

- **フィード URL（Feedly に追加する）**: https://kidsnz.github.io/260929_feedly-recommender/feed.xml
- **確認用ページ（ブラウザで見る）**: https://kidsnz.github.io/260929_feedly-recommender/

## 仕組み

1. **好みを知る** — Feedly の「Recently read」ページを保存した `.mhtml` から既読記事を抜き出し（`data/read_articles.csv`、非公開）、タイトルの語をトピックに分けて、最近読んだ記事ほど重く数える → `profile/profile.md`（人が読む）と `profile/profile.json`（プログラムが読む）
2. **集める** — 毎朝 6:00 ごろ（日本時間）、`config/sources.md` に載せた RSS 約75本・Googleニュース検索・はてなブックマーク検索から直近の記事を集める
3. **選ぶ** — 既に読んでいる媒体の記事、既読ソースの最新記事と同じ話題、暗号資産、広告・セール情報を除き、プロファイルで採点。同じ話題は1件にまとめ、トピックごとの配分どおりに 30 件を選ぶ。AI・テックは海外（英語）の記事を優先して選ぶ
4. **日本語版があれば差し替える** — AI・テックで選んだ英語記事と同じニュースの日本語記事が集めた中にあれば、日本語記事を載せる（説明欄に英語の原典を残す）。無ければ英語の原典のまま。既読ソースの日本語記事と同じニュースなら「既に見た」として載せない
5. **届ける** — `feed.xml`（RSS 2.0）と確認用ページ `index.html` を更新し、GitHub Pages で公開。フィードには直近 7 日分が残る

各記事の説明欄には「該当トピック（当たった語）｜出典｜同じ話題を報じた他の媒体｜スコア」が入ります。

## フォルダ構成

| 場所 | 中身 |
|---|---|
| `profile/topics.md` | **トピック定義（編集用）**。トピック・キーワード・倍率・優先言語・集めない話題 |
| `profile/profile.md` | 好みのプロファイル（確認用・自動生成） |
| `profile/profile.json` | 好みのプロファイル（プログラム用・自動生成） |
| `config/sources.md` | **収集元の一覧（編集用）**。RSS・検索語・除外する媒体と、選んだ理由 |
| `src/` | プログラム（抽出 `extract_read.py` → プロファイル `build_profile.py` → フィード `build_feed.py`） |
| `tests/` | テスト |
| `feed.xml` `index.html` `state/` | 毎日の自動更新で書き換わる生成物 |
| `data/`、`*.mhtml` | 閲覧履歴。**公開しない**（`.gitignore` で除外） |

## 毎日の自動更新

何もしなくても、GitHub Actions が毎日 21:00 UTC（日本時間 6:00）に実行します。GitHub の混雑で数十分遅れることがあります。

### GitHub の画面で様子を見る

1. https://github.com/kidsnz/260929_feedly-recommender を開く
2. 上のタブの **「Actions」** を押す
3. 左の一覧の **「Update feed」** を押すと、実行の履歴が並ぶ。緑のチェック＝成功、赤の × ＝失敗

### いますぐ手動で更新する

1. 「Actions」タブ → 左の **「Update feed」**
2. 右側の **「Run workflow」** ボタンを押す → 出てきた小窓の緑の **「Run workflow」** を押す
3. 1〜2分で完了。確認用ページの下に「最終更新」の時刻が出る

### 失敗したとき

- 赤の × の行を押す → 「update-feed」を押すと、どの段階で止まったかが見える
- 「Build feed」で止まり、`RSS の取得成功率が…` と出ていれば、収集元の半分以上が一時的に取れなかった（前日のフィードはそのまま残る）。翌日の実行で直ることが多い
- 「Test」で止まっていれば、`topics.md` などの変更でテストが通らなくなっている

### 自動更新を止める

「Actions」タブ → 左の「Update feed」 → 右上の **「…」** → **「Disable workflow」**。再開は同じ場所の「Enable workflow」。

### GitHub Pages の設定（済み。確認したいとき）

リポジトリの **「Settings」** タブ → 左の **「Pages」** → 「Build and deployment」の Source が **「Deploy from a branch」**、Branch が **「main」「/ (root)」** になっていれば正しい。

## 数ヶ月ごとのプロファイル更新

好みが変わったら、新しい既読データでプロファイルを作り直します。

### 1. Feedly の既読ページを保存する

1. ブラウザ（Chrome）で Feedly を開き、左メニューの **「Recently read」** を開く
2. **一番下までスクロール**して、古い記事まで読み込ませる（Feedly は画面外の記事を読み込まないため。件数が多いと時間がかかる）
3. メニューの「ファイル」→「ページを別名で保存」→ 形式を **「ウェブページ、1 つのファイル」**（`.mhtml`）にして、このフォルダに保存

### 2. プロファイルを作り直す

初めてのときだけ、環境を用意します（[uv](https://docs.astral.sh/uv/) を使用）:

```sh
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

毎回:

```sh
.venv/bin/python src/extract_read.py "Recently read.mhtml"   # 既読記事の抽出（件数と日付の範囲が表示される）
.venv/bin/python src/build_profile.py                         # プロファイルの作成
.venv/bin/python -m unittest discover -s tests                # テスト
```

- 抽出の件数や日付の範囲が前回より極端に少ないときは、手順1のスクロールが足りていない可能性があります。
- Claude Code に「README の手順でプロファイルを更新して」と頼んでも同じことができます。

### 3. 確認して直す

1. `profile/profile.md` を読む。特に「5. トピック定義の見直し候補」（どのトピックにも入らない語、最近増えている語）
2. 直したいことがあれば `profile/topics.md` を編集して、`build_profile.py` を再実行
3. 収集元を増やしたいときは、確認用ページの下の **「リスト外でよく選ばれた媒体」**（`state/discovered_sources.json`）を見て、`config/sources.md` に追加

### 4. 公開する

```sh
git add profile config
git commit -m "プロファイルを更新"
git push
```

次の自動更新（または手動実行）から、新しいプロファイルで集め始めます。

## 好みの調整

| 変えたいこと | 場所 |
|---|---|
| トピックの追加・削除、キーワード | `profile/topics.md`（変えたら `build_profile.py` を再実行） |
| 特定のトピックを多めに／少なめに | `profile/topics.md` の `- 倍率: 2`（0.5 で控えめ） |
| 英語／日本語の記事を優先 | `profile/topics.md` の `- 優先言語: en` |
| 集めない話題 | `profile/topics.md` の `- 扱い: 集めない` |
| 収集元・検索語・除外する媒体 | `config/sources.md` |
| 1日の件数（30）、残す日数（7）、同じ媒体の上限（4） | `src/build_feed.py` の `DAILY_LIMIT` `KEEP_DAYS` `PER_SOURCE_CAP` |
| 新しさの重みの半減期（180日） | `src/build_profile.py` の `HALF_LIFE_DAYS` |

## このツールで分からないこと・限界

- **読んだ日時**: Feedly の保存ページに既読日時は無いため、並び順と取得日時から推定している。
- **熱心に読んだか**: 開いただけか最後まで読んだかは区別できない。読まなかった記事（＝興味が無い話題）も分からない。
- **見えるのは収集元に載った記事だけ**: RSS・検索に出てこない記事は拾えない。Googleニュース検索はこれを補うが、Google が公開APIとして文書化しているものではない。
- **同じ話題の判定は見出しだけで行う**: 2026-09-29 の実測で、同じ話題の見出しの組と別の話題の組の類似度が一部重なった（同じ 0.18〜0.46、別 0.03〜0.20）。まれに同じ話題が2件並んだり、関連の強い別の話題が1件に絞られたりする。日本語と英語の間ではまとめられない。
- **英語と日本語の「同じニュース」の判定**（`src/crosslang.py`）は、日本語の見出しに英字で残る製品名・固有名詞（dots、World Labs、GPT-6 Astra など）で行う。「OpenAI」「Anthropic」のようなよく出る名前だけが共通する組は同じとみなさない。2026-09-29 の実記事で作った正解表では、同じ9組のうち7組を一致、別13組のうち0組を誤一致（条件を決めるのに使った記事なので、実際はこれより低い可能性がある）。同日の実運転では、英語のまま残った記事の中に日本語版があるもの（例: Anthropic の IPO）を取り逃している。**間違って差し替える・間違って「既に見た」として消すことを避ける方を優先している。**
- **Googleニュース経由のリンク**は Google の転送 URL になる。

## 開発

```sh
.venv/bin/python -m unittest discover -s tests -v   # テスト
.venv/bin/python src/build_feed.py --dry-run        # 書き込まずに、選ばれる記事と収集元の状態を表示
```

変更履歴は [CHANGELOG.md](CHANGELOG.md)。
