# 収集元の一覧

`src/build_feed.py` は毎日この4つの表を読みに行きます。**行を足す・消すだけで収集元を変えられます**（表の形は崩さないでください）。

1. **RSS** — 媒体が公式に配信している新着一覧
2. **Googleニュース検索** — キーワードで数千媒体を横断検索（リストに無い媒体を拾う）
3. **はてなブックマーク検索** — キーワードで、はてブ利用者がブックマークした記事を横断検索（個人・企業の技術ブログなど）
4. **除外する媒体** — 検索で混ざる質の低い媒体を弾く

選んだ基準:

1. **媒体が公式に配信しているRSS**であること（ページの読み取り＝スクレイピングはしない）。
2. 追加した日（2026-09-29 か 2026-10-25）に実際に取得でき、直近数日の記事が載っていること。
3. 既に Feedly で読んでいる媒体（GIGAZINE、Bloomberg、電ファミニコゲーマー、ギズモード、WIRED.jp など）と**重ならない**こと。
4. プロファイルのどれかのトピックを受け持つこと。暗号資産は集めない。政治とアートはトピックから外した（2026-09-29）。
5. **日本語の記事だけを載せる**（2026-10-25）。英語の媒体は外し、海外のニュースは日本語で報じる媒体から拾う。見出しに日本語が無い記事は、日本語の媒体のものでも載せない。

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
| Security NEXT | ja | https://www.security-next.com/feed | セキュリティ | 脆弱性・情報漏えい・サイバー攻撃の速報専門。英語の BleepingComputer の代わり |
| ScanNetSecurity | ja | https://scan.netsecurity.ne.jp/rss/index.rdf | セキュリティ | 国内のセキュリティ専門媒体。インシデントと脆弱性 |
| ITmedia エンタープライズ | ja | https://rss.itmedia.co.jp/rss/2.0/enterprise.xml | 企業IT全般、AI、セキュリティ | 企業のAI導入・クラウド・セキュリティ |
| @IT | ja | https://rss.itmedia.co.jp/rss/2.0/ait.xml | 開発全般、セキュリティ、AIコーディング | 開発者・インフラ技術者向け。海外の調査や発表の紹介も多い |
| Impress クラウドWatch | ja | https://cloud.watch.impress.co.jp/data/rss/1.0/clw/feed.rdf | データセンター、テック大手 | クラウド・データセンター。海外テックの解説も |
| MONOist | ja | https://rss.itmedia.co.jp/rss/2.0/monoist.xml | ロボット、半導体 | 製造業・ロボット・組み込み・半導体 |
| テクノエッジ | ja | https://www.techno-edge.net/rss20/index.rdf | テック全般、AI、ガジェット | 海外のAI・ガジェットの新着を日本語で速く拾う。英語の The Verge・Engadget の代わり |
| 気になる、記になる… | ja | https://taisy0.com/feed | テック大手（Apple） | Apple の噂・新製品の速報。英語の 9to5Mac・MacRumors の代わり |
| iPhone Mania | ja | https://iphone-mania.jp/feed/ | テック大手（Apple）、ガジェット | iPhone・Apple の海外報道を日本語で |
| ITmedia Mobile | ja | https://rss.itmedia.co.jp/rss/2.0/mobile.xml | ガジェット、テック大手 | スマホ・周辺機器 |
| Make: Japan | ja | https://makezine.jp/feed | 電子工作 | 電子工作・ものづくり。英語の Hackaday の代わり |
| レスポンス | ja | https://response.jp/rss/index.rdf | クルマ・EV | 自動車・EV の業界ニュース |
| アニメ！アニメ！ | ja | https://animeanime.jp/rss/index.rdf | アニメ・映像 | アニメ業界のニュース。英語の Cartoon Brew の代わり |
| QLifePro | ja | https://www.qlifepro.com/feed/ | 健康・医療 | 大学・研究機関の医学研究の発表。英語の STAT の代わり |
| 大学ジャーナル | ja | https://univ-journal.jp/feed/ | 科学・健康 | 国内大学の研究成果。英語の ScienceDaily・Phys.org の代わり |

## Googleニュース検索

Googleニュースの検索結果RSS（`news.google.com/rss/search`）。Google が公開APIとして文書化しているものではありませんが、個人利用のRSSとして広く使われています（2026-09-29 にユーザーが採用を判断）。直近1日の記事に限って検索し、1回の実行で下の行数だけアクセスします（間隔1秒）。リンクは Google 経由の転送URLになります。

| 検索語 | 言語 | ねらうトピック |
|---|---|---|
| Anthropic OR Claude OR アンソロピック | ja | Anthropic・Claude |
| OpenAI OR ChatGPT OR オープンAI OR アルトマン | ja | OpenAI・ChatGPT |
| AIエージェント OR "Claude Code" OR Codex OR バイブコーディング | ja | AIコーディング |
| 生成AI OR Gemini OR DeepSeek OR 大規模言語モデル | ja | AI全般 |
| エヌビディア OR 半導体 OR TSMC OR HBM | ja | 半導体 |
| アップル OR グーグル OR メタ OR マイクロソフト OR アマゾン | ja | テック大手 |
| サイバー攻撃 OR 脆弱性 OR ランサムウェア OR 情報漏えい | ja | セキュリティ |
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
