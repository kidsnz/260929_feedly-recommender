# 収集元の一覧

`src/build_feed.py` は毎日この4つの表を読みに行きます。**行を足す・消すだけで収集元を変えられます**（表の形は崩さないでください）。

1. **RSS** — 媒体が公式に配信している新着一覧
2. **Googleニュース検索** — キーワードで数千媒体を横断検索（リストに無い媒体を拾う）
3. **はてなブックマーク検索** — キーワードで、はてブ利用者がブックマークした記事を横断検索（個人・企業の技術ブログなど）
4. **除外する媒体** — 検索で混ざる質の低い媒体を弾く

選んだ基準:

1. **媒体が公式に配信しているRSS**であること（ページの読み取り＝スクレイピングはしない）。
2. 2026-09-29 に実際に取得でき、直近数日の記事が載っていること。
3. 既に Feedly で読んでいる媒体（GIGAZINE、Bloomberg、電ファミニコゲーマー、ギズモード、WIRED.jp など）と**重ならない**こと。
4. プロファイルのどれかのトピックを受け持つこと。AI・テックは**海外媒体を優先**（英語記事は満点、日本語記事は半分の点）、ゲームは日本の媒体だけ。暗号資産は集めない。政治とアートはトピックから外した（2026-09-29）。

「主なトピック」の**先頭**が特定の分野（「半導体」「宇宙」など）の媒体は専門媒体として扱い、見出しにキーワードが無くてもその分野の記事とみなし、その分野の点を1.5倍にします。先頭が「〜全般」の媒体は総合媒体として扱い、この加点をしません。

取得は1日1回、媒体を名乗る User-Agent を付けて行います。フィードに載せるのはタイトル・リンク・該当トピックだけで、記事本文や要約は転載しません。

## RSS

| 名前 | 言語 | RSS | 主なトピック | 選んだ理由 |
|---|---|---|---|---|
| ITmedia NEWS | ja | https://rss.itmedia.co.jp/rss/2.0/news_bursts.xml | テック全般・AI | 国内IT速報の定番。GIGAZINE と違う切り口で同じ領域を広く押さえる |
| ITmedia AI+ | ja | https://rss.itmedia.co.jp/rss/2.0/aiplus.xml | AI・生成AI | 国内唯一級の生成AI専門媒体。最重要トピックの取りこぼし対策 |
| ITmedia PC USER | ja | https://rss.itmedia.co.jp/rss/2.0/pcuser.xml | ガジェット・PC、半導体 | PC・周辺機器・CPU/GPUの新製品 |
| EE Times Japan | ja | https://rss.itmedia.co.jp/rss/2.0/eetimes.xml | 半導体 | 半導体業界の専門ニュース。NVIDIA・TSMC・メモリの動向を深く拾う |
| PC Watch | ja | https://pc.watch.impress.co.jp/data/rss/1.0/pcw/feed.rdf | ガジェット・PC、半導体 | PCハードの老舗。ベンチマークや新製品 |
| INTERNET Watch | ja | https://internet.watch.impress.co.jp/data/rss/1.0/iw/feed.rdf | ネット全般、セキュリティ | ネットサービス・セキュリティ・プラットフォーム企業の動き |
| Impress Watch | ja | https://www.watch.impress.co.jp/data/rss/1.0/ipw/feed.rdf | テック大手、ガジェット | Apple・Google など大手の製品とサービス |
| ケータイ Watch | ja | https://k-tai.watch.impress.co.jp/data/rss/1.0/ktw/feed.rdf | ガジェット、テック大手 | スマホ・iPhone・Android |
| AV Watch | ja | https://av.watch.impress.co.jp/data/rss/1.0/avw/feed.rdf | 映画・映像、ガジェット | 映像配信・映画・カメラ・ディスプレイ |
| GAME Watch | ja | https://game.watch.impress.co.jp/data/rss/1.0/gmw/feed.rdf | ゲーム | 任天堂・PlayStation・PCゲームの業界ニュース |
| Car Watch | ja | https://car.watch.impress.co.jp/data/rss/1.0/car/feed.rdf | クルマ・EV・自動運転 | 自動車・EV・自動運転の専門 |
| CNET Japan | ja | https://feeds.japan.cnet.com/rss/cnet/all.rdf | テック全般、経済 | テック企業のビジネス面 |
| ZDNET Japan | ja | https://feeds.japan.zdnet.com/rss/zdnet/all.rdf | 企業IT全般、AI、セキュリティ | 企業IT・生成AI導入・セキュリティ |
| 日経クロステック | ja | https://xtech.nikkei.com/rss/index.rdf | テック全般、AI、半導体 | 技術系の深い報道。見出しのみ無料で読める記事も多い |
| ASCII.jp | ja | https://ascii.jp/rss.xml | ガジェット、AI | 製品レビューとAIサービスの紹介 |
| Business Insider Japan | ja | https://www.businessinsider.jp/feed/index.xml | 経済、テック大手 | テック企業・スタートアップのビジネスニュース |
| 東洋経済オンライン | ja | https://toyokeizai.net/list/feed/rss | ニュース全般、経済 | 国内の企業・経済。Bloomberg と違う国内目線 |
| Publickey | ja | https://www.publickey1.jp/atom.xml | 開発全般、AIコーディング | 開発者向けクラウド・開発ツールの定番ブログ |
| gihyo.jp | ja | https://gihyo.jp/feed/rss2 | 開発全般、AIコーディング | 技術評論社。開発ツール・プログラミングの記事 |
| Zenn: Claude Code | ja | https://zenn.dev/topics/claudecode/feed | AIコーディング、Anthropic | Claude Code の実践記事。倍率2のトピックの中心 |
| Zenn: AI | ja | https://zenn.dev/topics/ai/feed | AIコーディング、AI | 開発者によるAI活用記事 |
| Qiita トレンド | ja | https://qiita.com/popular-items/feed | プログラミング全般、AIコーディング | 国内エンジニアの人気記事 |
| はてなブックマーク IT 人気 | ja | https://b.hatena.ne.jp/hotentry/it.rss | テック全般、AI | 多くの媒体・個人ブログから「いま読まれているIT記事」を集めた公式RSS。取りこぼし対策の要 |
| はてなブックマーク 学び 人気 | ja | https://b.hatena.ne.jp/hotentry/knowledge.rss | 雑学全般、科学・健康 | 科学・雑学系の人気記事。GIGAZINE の雑学ネタに近い層 |
| はてなブックマーク アニメとゲーム 人気 | ja | https://b.hatena.ne.jp/hotentry/game.rss | ゲーム、アニメ | ゲーム・アニメの人気記事 |
| AUTOMATON | ja | https://automaton-media.com/feed/ | ゲーム | インディー・海外ゲームに強い |
| 4Gamer.net | ja | https://www.4gamer.net/rss/index.xml | ゲーム | 国内最大級のゲーム媒体 |
| Game*Spark | ja | https://www.gamespark.jp/rss/index.rdf | ゲーム | 海外ゲームニュース |
| sorae | ja | https://sorae.info/feed | 宇宙 | 宇宙専門。SpaceX・ロケット・天文 |
| ナゾロジー | ja | https://nazology.kusuguru.co.jp/feed | 科学・健康 | 研究結果の紹介。GIGAZINE の「〜という研究結果」系に近い |
| カラパイア | ja | https://karapaia.com/index.rdf | 科学・生物 | 動物・科学の不思議ネタ |
| CINRA | ja | https://www.cinra.net/feed | 映画 | 映画・カルチャー |
| The Verge | en | https://www.theverge.com/rss/index.xml | テック全般、テック大手、ガジェット | 米国テックの代表的媒体 |
| Ars Technica | en | https://feeds.arstechnica.com/arstechnica/index | テック全般、AI、科学 | 技術的に踏み込んだ報道 |
| TechCrunch | en | https://techcrunch.com/feed/ | テック全般、AI、経済 | スタートアップ・AI企業の資金調達と新製品 |
| MIT Technology Review | en | https://www.technologyreview.com/feed/ | テック全般、AI、科学 | 日本語版は既読。英語版は翻訳されない記事を含む |
| WIRED (US) | en | https://www.wired.com/feed/rss | テック全般、カルチャー | 日本語版は既読。米国版は翻訳されない記事を含む |
| Engadget | en | https://www.engadget.com/rss.xml | テック全般、ガジェット | 製品ニュース |
| Tom's Hardware | en | https://www.tomshardware.com/feeds/all | 半導体、PC | CPU/GPU/メモリの速報 |
| IEEE Spectrum | en | https://spectrum.ieee.org/feeds/feed.rss | 半導体、ロボット、科学 | 技術者団体の専門誌 |
| The Register | en | https://www.theregister.com/headlines.atom | テック全般、半導体、セキュリティ | 企業IT・半導体・セキュリティ |
| Simon Willison's Weblog | en | https://simonwillison.net/atom/everything/ | AIコーディング、AI | LLMとAIコーディングを毎日検証している開発者のブログ |
| Latent Space | en | https://www.latent.space/feed | AIコーディング、AI | AIエンジニア向けの有力ニュースレター |
| GitHub Blog | en | https://github.blog/feed/ | 開発全般、AIコーディング | Copilot・開発ツールの公式発表 |
| Hacker News | en | https://news.ycombinator.com/rss | テック全般、AIコーディング | 開発者コミュニティの公式トップページRSS |
| OpenAI News | en | https://openai.com/news/rss.xml | OpenAI | OpenAI 公式の発表 |
| Google Blog | en | https://blog.google/rss/ | テック大手、AI | Google 公式の発表（Gemini など） |
| Hugging Face Blog | en | https://huggingface.co/blog/feed.xml | AI | オープンモデルの公式発表 |
| NVIDIA Blog | en | https://blogs.nvidia.com/feed/ | 半導体 | NVIDIA 公式の発表 |
| Electrek | en | https://electrek.co/feed/ | EV・自動運転 | Tesla・EV専門 |
| Phys.org | en | https://phys.org/rss-feed/ | 科学 | 研究成果のニュース |
| ScienceDaily | en | https://www.sciencedaily.com/rss/all.xml | 科学・健康 | 大学・研究機関の発表 |
| NASA | en | https://www.nasa.gov/news-release/feed/ | 宇宙 | NASA 公式発表 |
| STAT | en | https://www.statnews.com/feed/ | 健康・医療 | 医療・製薬の専門報道 |
| BleepingComputer | en | https://www.bleepingcomputer.com/feed/ | セキュリティ | サイバー攻撃・脆弱性の速報 |
| Cartoon Brew | en | https://www.cartoonbrew.com/feed | アニメ・映像 | アニメーション業界の専門 |
| Hackaday | en | https://hackaday.com/blog/feed/ | 電子工作 | 電子工作・LED・ハードウェアハック（Adafruit を読んでいた履歴から） |
| Techmeme | en | https://www.techmeme.com/feed.xml | テック全般・AI | 米国テック業界の主要ニュースを人手で選んで最速で並べる定番。リンクは元記事を使う |
| The Decoder | en | https://the-decoder.com/feed/ | AI | AIニュース専門。モデル発表・研究を速く拾う |
| 404 Media | en | https://www.404media.co/rss/ | テック全般、AI | 独立系の調査報道。他が書かないテック・AIの裏側 |
| Platformer | en | https://www.platformer.news/rss/ | テック大手、AI | Casey Newton のニュースレター。大手プラットフォームとAIの分析 |
| Stratechery | en | https://stratechery.com/feed/ | テック大手、AI | Ben Thompson の戦略分析（無料記事のみ全文） |
| Interconnects | en | https://www.interconnects.ai/feed | AI | Nathan Lambert によるモデル訓練・オープンモデルの深い解説 |
| Import AI | en | https://importai.substack.com/feed | AI | Anthropic 共同創業者 Jack Clark の週刊AI研究まとめ |
| Understanding AI | en | https://www.understandingai.org/feed | AI | Timothy B. Lee によるAIの丁寧な解説 |
| One Useful Thing | en | https://www.oneusefulthing.org/feed | AI | Ethan Mollick によるAI活用の考察 |
| The Pragmatic Engineer | en | https://newsletter.pragmaticengineer.com/feed | AIコーディング | ソフトウェア開発現場とAIツールの実態 |
| Ben's Bites | en | https://www.bensbites.com/feed | AI、AIコーディング | AIプロダクトの新着まとめ |
| Google DeepMind Blog | en | https://deepmind.google/blog/rss.xml | AI | DeepMind 公式の研究発表 |
| 9to5Mac | en | https://9to5mac.com/feed/ | テック大手（Apple） | Apple のリーク・新製品を最速で |
| MacRumors | en | https://www.macrumors.com/macrumors.xml | テック大手（Apple） | Apple の噂と新製品 |
| 9to5Google | en | https://9to5google.com/feed/ | テック大手（Google） | Google・Pixel・Gemini の新機能 |
| TechPowerUp | en | https://www.techpowerup.com/rss/news | 半導体、PC | GPU/CPU/メモリの速報 |
| ServeTheHome | en | https://www.servethehome.com/feed/ | 半導体・データセンター | サーバー・データセンターハードウェア |
| Chips and Cheese | en | https://chipsandcheese.com/feed/ | 半導体 | CPU/GPUのアーキテクチャ詳細分析 |

## Googleニュース検索

Googleニュースの検索結果RSS（`news.google.com/rss/search`）。Google が公開APIとして文書化しているものではありませんが、個人利用のRSSとして広く使われています（2026-09-29 にユーザーが採用を判断）。「日本語版さがし」の行は、海外の記事と同じニュースの日本語記事を見つけるためのもの（見つかれば日本語記事に差し替える）。直近1日の記事に限って検索し、1回の実行で下の行数だけアクセスします（間隔1秒）。リンクは Google 経由の転送URLになります。

| 検索語 | 言語 | ねらうトピック |
|---|---|---|
| Anthropic OR "Claude AI" OR "Claude Code" | en | Anthropic・Claude |
| OpenAI OR ChatGPT OR "Sam Altman" | en | OpenAI・ChatGPT |
| "AI agent" OR "coding agent" OR "vibe coding" OR "Claude Code" OR Codex | en | AIコーディング |
| "large language model" OR "AI model" OR Gemini OR DeepSeek OR "generative AI" | en | AI全般 |
| Nvidia OR TSMC OR "SK Hynix" OR HBM OR semiconductor | en | 半導体 |
| Apple OR Google OR Meta OR Microsoft OR Amazon | en | テック大手 |
| cybersecurity OR ransomware OR "data breach" OR vulnerability | en | セキュリティ |
| 生成AI OR AIエージェント | ja | AI（日本語版さがし） |
| OpenAI OR ChatGPT OR Anthropic OR Claude OR Gemini | ja | AI（日本語版さがし） |
| エヌビディア OR 半導体 OR TSMC OR HBM | ja | 半導体（日本語版さがし） |
| アップル OR グーグル OR メタ OR マイクロソフト OR アマゾン | ja | テック大手（日本語版さがし） |
| サイバー攻撃 OR 脆弱性 OR ランサムウェア | ja | セキュリティ（日本語版さがし） |
| 任天堂 OR "Nintendo Switch 2" OR 新作ゲーム OR ゲーム 発売 | ja | ゲーム |
| 映画 OR アニメ OR 実写化 | ja | 映画・アニメ |
| 研究結果 OR 研究チーム OR 新発見 | ja | 科学 |
| 宇宙 OR ロケット OR JAXA OR スペースX | ja | 宇宙 |
| 自動運転 OR EV OR 人型ロボット | ja | クルマ・ロボット |
| 新薬 OR 治療法 OR 医療 研究 | ja | 健康・医療 |
| 株価 OR 決算 OR IPO OR 買収 | ja | 経済 |

## はてなブックマーク検索

はてなブックマークの検索結果RSS（公式機能）。新しい順で、ブックマーク数が「最低ブックマーク」以上の記事だけを見ます。

| 検索語 | 最低ブックマーク | ねらうトピック |
|---|---|---|
| Claude Code | 5 | AIコーディング |
| AIエージェント | 5 | AIコーディング |
| 生成AI | 10 | AI |
| LLM | 10 | AI |
| 半導体 | 10 | 半導体 |
| ゲーム | 20 | ゲーム |
| 宇宙 | 10 | 宇宙 |
| 研究結果 | 20 | 科学 |

## 除外する媒体

検索（Googleニュース・はてブ）で混ざる、株価の自動記事・プレスリリース配信・転載サイトなど。媒体名（Googleニュースの出典名）かドメインのどちらかで判定します。このほか、タイトルに【PR】などが付いた広告記事と、Googleニュースで出典名が「株式会社〜」の企業の自社発表は、表に無くても除外します。

| 媒体名またはドメイン | 理由 |
|---|---|
| BigGo ファイナンス | 株価ニュースの自動生成 |
| Moomoo | 証券会社の株価ニュース |
| moomoo | 同上 |
| Yahoo!ファイナンス | 株価ニュース |
| Yahoo Finance | 株価ニュース |
| kabushiki.jp | 株価ニュース |
| みんかぶ | 株価ニュース |
| 株探 | 株価ニュース |
| Investing.com | 株価ニュース |
| Benzinga | 株価ニュース |
| MarketBeat | 株価ニュースの自動生成 |
| Simply Wall St | 株価分析の自動生成 |
| simplywall.st | 同上（ドメイン表記） |
| googlecloudpresscorner.com | Google Cloud の報道発表ページ |
| AInvest | 株価ニュースの自動生成 |
| The Motley Fool | 投資推奨記事 |
| TipRanks | 株価分析 |
| Seeking Alpha | 有料の投資分析 |
| Zacks | 株価分析 |
| PR TIMES | プレスリリース配信 |
| prtimes.jp | 同上 |
| @Press | プレスリリース配信 |
| PR Newswire | プレスリリース配信 |
| Business Wire | プレスリリース配信 |
| GlobeNewswire | プレスリリース配信 |
| ValuePress | プレスリリース配信 |
| Межа. Новини України. | 他媒体記事の機械的な転載 |
| softbank.jp | 企業の自社サービス紹介 |
