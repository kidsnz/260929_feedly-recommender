# トピック定義（編集用）

このファイルを直すと、次に `src/build_profile.py` を実行したときにプロファイル（`profile.json` / `profile.md`）へ反映されます。

- `## 見出し` = トピック名。トピックの追加・削除・並べ替えは自由です。
- **キーワード**: 既読記事のタイトルに実際に出てきた語から選んだもの。
- **英語**: 英語の記事を拾うために追加した語（既読記事のデータ由来ではなく、キーワードの英訳・英語表記として推測で足したもの）。
- **除外**: この語を含む記事はそのトピックに数えません。
- **倍率**: 採点の重みに掛ける数（省略時は 1）。「もっと読みたい」トピックは 2、「控えめに」は 0.5 など。掛けたあと全体を最大 1.0 に揃え直します。
- **優先言語**: `en` か `ja`。そのトピックでは、この言語の記事を満点、それ以外の言語の記事を半分の点で数えます（省略時は言語で差を付けない）。
- **扱い**: `集めない` と書くと、そのトピックに当たる記事は**収集から除外**します（タイトルに当たるか、要約に2語以上当たった場合）。
- 区切りは `,` か `、`。英数字の語は単語単位で照合します。大文字を含む4文字以下の英語（Meta、AI など）は大文字小文字を区別し、それ以外（NVIDIA と Nvidia など）は区別しません。

## Anthropic・Claude
- 優先言語: en
- キーワード: Anthropic, アンソロピック, Claude, Claude Code, Opus, Sonnet, Haiku, Fable, Mythos, ダリオ・アモデイ, アモデイ
- 英語: Dario Amodei

## OpenAI・ChatGPT
- 優先言語: en
- キーワード: OpenAI, ChatGPT, GPT, Codex, Sora, サム・アルトマン, アルトマン
- 英語: Sam Altman

## AI・生成AI全般
- 優先言語: en
- キーワード: AI, 生成AI, 人工知能, LLM, 大規模言語モデル, AIモデル, 言語モデル, Gemini, Grok, DeepSeek, Llama, Qwen, Mistral, xAI, AGI, 画像生成, 動画生成, 推論, ベンチマーク, チャットボット
- 英語: artificial intelligence, generative AI, large language model, chatbot, machine learning, deep learning, foundation model
- 除外: アートメイク

## AIエージェント・AIコーディング
- 倍率: 2
- 優先言語: en
- キーワード: エージェント, AIエージェント, コーディング, Claude Code, Codex, Cursor, GitHub Copilot, Copilot, プログラミング, ローカルLLM, MCP, バイブコーディング
- 英語: AI agent, agentic, coding agent, vibe coding, AI coding, developer tools

## テック大手（Google・Apple・Meta・Amazon・Microsoft ほか）
- 優先言語: en
- キーワード: Google, グーグル, Apple, アップル, Meta, メタ, Amazon, アマゾン, Microsoft, マイクロソフト, iPhone, iPad, Mac, MacBook, Siri, iOS, Android, Pixel, YouTube, Windows, Oracle, オラクル, Palantir, パランティア, ザッカーバーグ, ティム・クック
- 英語: Alphabet, Zuckerberg, Tim Cook, Sundar Pichai, Satya Nadella, Big Tech

## 半導体・データセンター
- 優先言語: en
- キーワード: 半導体, NVIDIA, エヌビディア, TSMC, SK hynix, SKハイニックス, ハイニックス, サムスン, Samsung, Intel, インテル, AMD, メモリ, メモリー, HBM, DRAM, GPU, CPU, チップ, データセンター, ラピダス, ジェンスン・フアン
- 英語: semiconductor, chipmaker, Jensen Huang, data center, foundry, Rapidus

## 経済・マーケット・企業
- キーワード: 株価, 株式, 株高, 株安, 米国株, 日本株, 市況, 相場, 金利, 国債, 投資, 投資家, IPO, 上場, 時価総額, 決算, 売上高, 買収, 資金調達, 評価額, ソフトバンク, 孫正義, 日銀, FRB, 利下げ, 利上げ, 円安, 円高, 原油, 景気, インフレ
- 英語: stock market, valuation, earnings, acquisition, funding round, Federal Reserve, inflation, SoftBank, Masayoshi Son

## ゲーム
- 優先言語: ja
- キーワード: ゲーム, 任天堂, Nintendo, Steam, Nintendo Switch, Switch 2, Switch2, PlayStation, PS5, Xbox, インディーゲーム, 新作ゲーム, カプコン, スクウェア・エニックス, セガ, バンダイナムコ, コナミ, ゲームボーイ, ファミコン, レトロゲーム, ポケモン, Pokémon
- 英語: video game, gaming, indie game, game developer
- 除外: ゲーム理論

## 映画・アニメ・映像
- キーワード: 映画, アニメ, 実写, 実写化, Netflix, ネットフリックス, ディズニー, ドラマ, 予告編, 劇場版, 興行収入, 監督, ジブリ, ピクサー, 特撮
- 英語: film, movie, anime, box office, Disney, Pixar, Studio Ghibli, Netflix

## 宇宙・科学研究
- キーワード: 宇宙, SpaceX, スペースX, ロケット, 衛星, NASA, JAXA, 火星, 月面, スターシップ, Starlink, 研究結果, 研究チーム, 研究者, 科学者, 科学, 論文, 地震, 量子, 量子コンピューター, 物理学, 考古学
- 英語: spaceflight, outer space, rocket, satellite, Starship, Mars, astronomy, physics, quantum computing, study finds, researchers

## クルマ・EV・ロボット・自動運転
- キーワード: 自動車, トヨタ, ホンダ, テスラ, Tesla, イーロン・マスク, マスク氏, ロボタクシー, 自動運転, Waymo, ロボット, 人型ロボット, ヒューマノイド, EV, 電気自動車, BYD
- 英語: Elon Musk, robotaxi, self-driving, autonomous vehicle, humanoid robot, robotics, electric vehicle

## サイバーセキュリティ・プライバシー
- 優先言語: en
- キーワード: セキュリティ, サイバー攻撃, ハッキング, ハッカー, 脆弱性, マルウェア, ランサムウェア, 情報漏えい, 情報漏洩, 不正アクセス, 詐欺, プライバシー, 暗号化
- 英語: cybersecurity, hacker, hacking, vulnerability, malware, ransomware, data breach, privacy, encryption

## 健康・医療・生物
- キーワード: 医療, 医薬, 医薬品, 新薬, 治療薬, 創薬, 治療, 健康, 病気, がん細胞, がん治療, 抗がん, 癌, 感染, ウイルス, 細菌, ワクチン, 肥満, 睡眠, 老化, 寿命, 遺伝子, CRISPR, 脳科学, 脳細胞, 認知症, 化石, 動物
- 英語: medicine, drug, cancer, vaccine, obesity, gene therapy, CRISPR, brain, biology
- 除外: 首脳

## ガジェット・PC・電子工作
- 優先言語: en
- キーワード: ガジェット, スマホ, スマートフォン, PC, パソコン, ノートPC, グラボ, グラフィックボード, キーボード, イヤホン, ヘッドホン, カメラ, ディスプレイ, モニター, Raspberry Pi, ラズパイ, LED, ドローン, DJI, スマートグラス, ウェアラブル, AirTag, 電子工作, 自作PC, レビュー
- 英語: gadget, smartphone, laptop, graphics card, mechanical keyboard, headphones, camera, Raspberry Pi, Arduino, drone, smart glasses, wearable

## 暗号資産
- 扱い: 集めない
- キーワード: ビットコイン, 暗号資産, 仮想通貨, イーサリアム, ステーブルコイン, BTC, ETH, ブロックチェーン, NFT, Web3, コインベース
- 英語: Bitcoin, crypto, cryptocurrency, Ethereum, stablecoin, blockchain, Coinbase
