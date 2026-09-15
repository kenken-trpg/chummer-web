# Changelog

Notable changes. Format follows [Keep a Changelog](https://keepachangelog.com/);
self-hosters can pin to a tag instead of tracking `main`.

## [Unreleased]

### Added

- **電子機器の改造（Electronic Modification）を扱えるようにした。** Data Trails
  p.66 の改造 — Increase Attack や Modify Matrix Attribute、Add Module など
  32 件 — をカタログに載せ、コムリンク・サイバーデッキ・RCC のそれぞれに
  付けられるようにした。無料で、付けた機器のマトリックス属性を 1 点動かす。
  デッキのように属性が配列になっている機器では、`<modattributearray>` の
  とおり枠ごとに増減する（1 枠目 +1、2 枠目 -1 など）。.chum5 の読み書きにも
  対応し、Chummer 自身のテスト用セーブで「取り込めない品目」だった 3 件が
  なくなった。マトリックスの負傷ボックスへの影響（`<matrixcmbonus>`）は、
  そもそもこのアプリがまだ負傷ボックスを持っていないので入れていない。
- **車両に積んだギアを読み書きできるようにした。** メディキットやカメラなど、
  車両の `<gears>` にあるものを車両の持ち物として読み込み、同じ場所へ書き出す。
  Chummer が車両のセンサー評価から作る Sensor Array は、こちらは評価値で
  持っているので読み飛ばす。車両は入れ物として扱い、ほかのホストに差す品目
  以外は積める。
- **キャリアのセーブの支出履歴を読み込むようにした。** `<expenses>` のマイナスの
  行（家賃・購入・資質の取得など）を履歴として持ち、サイドバーの内訳に出す。
  値段はキャラ本体から計算しているので二重には数えず、書き出しでは元の
  マイナスの行として戻す。「Chummer との差」の中身を追う手がかりになる。
- **防具に入れたセンサーに、機能を付け外しできるようにした。** ヘルメットの
  Single Sensor に付くセンサー機能（カメラなど）が、防具の画面に出て、追加も
  取り外しもできる。読み込みと計算は前からできていて、画面だけができなかった。
- **防具にセンサーと視覚・聴覚強化を入れられるようにした。** ヘルメットや
  マスクの Single Sensor・Vision Magnification・Audio Enhancement なども、
  `<armorcapacity>` の分だけ防具の容量を使う。.chum5 の防具の `<gears>` から
  読み込み（これまでは取り込めないと警告して捨てていた、16 件）、同じ場所へ
  書き出す。防具の画面の「ギアを入れる」でも選べる。
- **値段を自分で決める品目を扱えるようにした。** Chummer のデータで値段が
  `Variable(下限-上限)` の品目 — カスタム品目（Custom Item）、Clothing、
  コムリンクアプリ（Theme Music など）、Uniforms など — をカタログに載せ、範囲内
  で値段を入力できる。カスタム品目には名前も付けられる。.chum5 の `<cost>` と
  名前とも往復するので、Chummer で作った「Wine」「Golden Lotus Flower」のような
  品目が取り込めずに消えることがなくなった。
- **防具にギアを入れられるようにした（ホルスター・メディキット・トロードなど）。**
  `<armorcapacity>` を持つギアは防具の容量をその分（数量ぶん）使い、改造と
  合わせて容量を超えるとエラーになる（Chummer の `Armor.CapacityRemaining`）。
  容量 0 の防具（帽子など）は調べない。防具の画面から入れ外しでき、防具を
  削除すると中のギアも消える。.chum5 では防具の `<gears>` から読み込み、同じ
  場所へ書き出す。古いセーブが改造の欄に入れていた Personal Drone Rack も
  ギアとして読む。センサーや視覚・聴覚強化は防具に入れられないので、読み込み
  時に取り込めなかったと警告する（これまでは何も言わずに捨てていた）。
- **ライフスタイルの快適さ・地域・防犯を上げられるようにした（RF p.219）。**
  1 段ごとに LP 1 と基本額の 10%（段の値段があればそれも）がかかり、上げ
  られるのはライフスタイルごとの上限まで。.chum5 の `<comforts>` / `<area>` /
  `<security>` とも往復する。ライフスタイル品質の選択肢は、LP を使わない
  ライフスタイルの一覧（allowed）で絞り込まなくなった。
- **Priority / Sum-to-Ten の作成中に、技能の上の何レベルかをカルマで買える
  ようにした。** 能力値（前の変更）の技能版。技能タブの各技能に「うちカルマ」
  欄が増え、その分は技能点（知識技能点）を使わず、上げた後の値×2（知識技能は
  ×1）カルマかかる。Chummer の `<base>` / `<karma>` とも往復するので、作成中に
  技能をカルマで上げた Chummer のキャラクターを読み込んでも「技能点の超過」に
  ならない。
- **`<prioritytable>` に対応した。** `priorities.xml` は Standard /
  Prime Runner / Street Level の 3 表を持っているのに、この app は Standard
  固定で、しかも未対応としても報告していなかった。セッティングが指定した表で
  計算・表示する。プライムランナー卓なら優先度 A の資金は 450,000¥ ではなく
  500,000¥ になる。データにない表を指定された場合は Standard に落として
  作成を続ける。
- **`critters.xml` のような「この app が読まないデータ」を未適用と分けた。**
  コデックス系のパックはどれも `amend_critters.xml` を含むため、毎回
  「未適用 1 件」が出ていた。パックに問題はなく卓にできることもないので、
  別の行で静かに知らせる。
- **customdata が何を変えたのか内訳を出す。** これまでは「217 件適用」と
  件数だけだった。ファイル・操作・書き換えたフィールドでまとめ、項目名まで
  並べる。`qualities.xml ・ source, page を変更 ・ 21 件` なら既存項目の
  出典差し替え、`martialarts.xml ・ 追加 ・ 57 件` なら新しいゲーム内容 —
  配布物が何をするものなのか、卓の側で検算できる。
- **スタイル一式をフォルダごと読み込めるようになった。** 配布されている
  ルールセットは `settings/` と `customdata/` が横並びの 1 フォルダなので、
  そのフォルダを選ぶだけで中のセッティングが全部プルダウンに入り、選んだ
  ものに合わせてカスタムデータが結合される。セッティングを切り替えるたびに
  フォルダを選び直す必要はない（同じフォルダの中身はこのブラウザに残る）。
  `sheets/` など残りの中身はデータセットに含めない。
- **customdata に対応した。** セッティングが参照している `customdata/`
  フォルダを読み込むと、追加の格闘技・武器・資質や、シャドウラン・コデックス
  向けの出典付け替えがそのまま効く。マージはローダより上流の XML に対して
  行うので、追加された項目は最初から同梱されていたものと区別がつかない。
  ファイルはブラウザに残り、サーバーはマージ結果だけを内容ハッシュの下に
  一時的に持つ（再起動で消え、次のリクエストが自動で送り直す）。
  適用できなかったルールは件数と理由を出す。
- 手元の Chummer セッティングファイル（`settings/*.xml`）を読み込めるように
  なった。優先度タブの「セッティングを読み込む」から選ぶと、使用ルールブック・
  作成方式に加えて、カルマ価格表・作成時の各種上限・カルマ→新円レート・
  禁止ウェア等級までそのファイルの値で計算される。読み込んだファイルは
  このブラウザにだけ残り、どこにも送信・保存されない。
- **未対応のハウスルールを明示する。** Chummer のセッティングは約 160 項目
  あり、この app が実装しているのはその一部。Chummer 標準から値を変えていて、
  かつ未実装の項目だけを名指しで警告に出す。黙って無視はしない。
- セッティング（ルールセット）の選択。優先度タブの先頭にプルダウンが増え、
  Chummer 同梱のセッティングを選ぶと、使用ルールブックと作成方式がまとめて
  切り替わる。ルールブックは個別にチェックしても変えられる。
  無効にしたルールブックの項目は購入一覧から消えるが、**すでに所持している
  装備・資質は消えない** — カタログ本体は絞らず、購入一覧だけを絞っている。
  初期状態は「制限なし」なので、既存キャラの見え方は変わらない。
- `.chum5` はセッティング名を書き出し / 読み込みする。Chummer は使用書籍を
  セッティングファイル側に持つのでセーブには入っておらず、読み込み時は
  同梱プリセット名と照合して復元する。知らない名前は名前だけ復元し、
  ルールブックは無制限のままにする。

まだ入っていないのは式で書かれたハウスルール（コンタクト点・知識点など）と、
Chummer の amend エンジンのうち実データが使っていない部分。段取りは
`docs/plans/settings-plan.md`。

### Changed

- **公開イメージを arm64 でもビルドするようにした。** これまで CI が作っていたのは
  `linux/amd64` だけで、Apple Silicon や arm のサーバーで引くと QEMU による
  エミュレーションになり、手元でビルドするより遅かった。アーキテクチャごとに
  ジョブを分け、それぞれのネイティブランナーでビルドして施錠状態で起動を確認し、
  両方が通ってから digest をまとめて 1 つのタグ（マニフェストリスト）にする。
  QEMU を使わないのは、`npm ci` と `next build` がエミュレーション下では数十分
  かかるため。arm64 ランナーは公開リポジトリなら無料。
  副次的に、公開の順序が直った。以前はビルドしたイメージを push してから
  スモークテストしていたので、起動しないイメージが `:latest` になりえた。
  いまは起動を確認してからでないとタグが付かない。
  必須チェックの名前は `docker` のまま保っている。マトリクスのチェック名は
  パラメータ込みになるので、そのままだとマトリクスを触るたびにブランチ保護の
  ルールが誰にも一致しなくなり、全 PR がマージ不能になる。実ビルドは
  `docker-build` に改名し、それを束ねる `docker` ジョブが名前を固定している。
- **`engine/qualities.py`（635 行）を `engine/qualities/` パッケージに分割した。**
  docstring が既に5つの役割を並べていたので、その軸で割った: 何を持っているかを
  組み立てる `_gather`、まだプレイヤーの選択が要るかを見る `_picks`、その選択を
  効果の行に結びつける `_binders`、要件木を評価する土台の `_context`、資質側の
  `<selectside>` を扱う `_sides`、割引と上限の `_limits`、エラーを出す `_validate`。
  `__init__.py` が全ての名前を再エクスポートするので、ここから import している
  14 のモジュールは無変更。最大でも 160 行になった。出力は一切変えていない
  （981 テスト・`make reconcile` の警告2／エラー63 とも分割前と同じ）。
- **`chummer_export.py`（971 行）を `chummer_export/` パッケージに分割した。**
  インポート側と同じ軸（`identity` / `qualities` / `gear` / `lifestyles` /
  `magic` / `_common`）に割り、往復の両側が並ぶようにした。`<spells>`・
  `<powers>`・`<complexforms>` はクオリティの出力から `magic` に、トラディション
  とメンターは連絡先の出力から切り出している。出力は Chummer のテストセーブ
  34 件すべてでバイト単位で変わらない（uuid と日時を伏せて全文を突き合わせた）。
- **フロントの状態の型を `app/models.py` から生成するようにした。**
  キャラクターの状態は JSON で行き来するので、同じ形が Pydantic と
  `frontend/lib/types/` に二重に書かれていて、実際にずれていた——
  `SpellInstall` の `alchemical` と `source_quality_id`、5 種類の
  `discounted`、`chargen_attributes_at_max`、`career_baseline`、`options` の
  計 11 個がブラウザ側の型に存在しなかった。`backend/scripts/
  gen_frontend_types.py` が `generated.ts` を書き、`--check` で古くなって
  いれば CI と pytest が落ちる。`character.ts` はなくなり、中にあった
  460 行の無名の `derived: {...}` は `derived.ts` の `Derived` になった。
  エンジンの出力とカタログは Python 側もただの dict なので、これまで通り
  手書きのまま。
- **ギアのタブで一番大きかった二つの画面を分解した。** `VehicleDroneGear.tsx`
  （626 行）と `MiscDrugsGear.tsx`（583 行）が、それぞれ 150 行・65 行の
  組み立て役と、意味のある単位のコンポーネントになった。車両側では
  「選んで装着」の同じ 20 行が 4 か所に写っていたので `SlotPicker` に
  まとめている。画面の見た目と操作は変えていない（ただし車内に積める
  ものが一つもないときは、これまで空の選択肢だけが出ていた欄が消える）。
- **1,800 行あったロケールファイルを分野別に割った。** `locales/ja.ts` /
  `en.ts` は分野別の 8 枚（`app` / `engine` / `sheet` / `sidebar` / `rules` /
  `chargen` / `gear` / `magic`）をまとめるだけの入口になった。キーも文言も
  1 行も変えていない（1,550 キー、全行が元のまま）。スプレッドは同じキーが
  あっても黙って後勝ちになるので（TS1117 は 1 つのオブジェクトリテラルの
  中でしか出ない）、`lib/i18n/locales.test.ts` が「どのキーもちょうど 1
  ファイルにしかない」ことを見張る。

### Fixed

- **古いイメージが残っていると、コンテナが起動しなくなっていた。** `compose.yaml` は
  手元にイメージがあればそれを使う設定だったので、コンテナの権限を落とす変更
  （`--cap-drop ALL` など）だけが新しく、対応する Dockerfile 側の変更を含まない
  イメージ、という組み合わせが起こりえた。この状態では caddy を exec できず
  (`EPERM`)、supervisord が再試行を諦めてコンテナは永久に unhealthy になる。
  毎回チェックアウトからビルドするようにして、イメージと `compose.yaml` が
  ずれないようにした。キャッシュが効くので通常は数秒で、`make up` の挙動は変わらない。
  あわせて、GHCR のパッケージはリポジトリが公開でも初回作成時は private のため
  `docker compose pull` が `unauthorized` で落ちることを README と `docs/deploy.md`
  に明記した。
- **`.dockerignore` が `.env` を完全一致でしか除外していなかった。** Dockerfile は
  `COPY frontend/ ./` でフロントエンドを丸ごとイメージに入れ、Next はビルド時に
  `frontend/.env.production` を読んで `NEXT_PUBLIC_*` をクライアントのバンドルに
  焼き込む。つまり置いた覚えのないファイルが、公開イメージから読める状態で
  出ていきうる。しかもレイヤは消せないので、後から気づいても取り消せない。
  `**/.env*` ＋ `!**/.env.example` にした。実際にダミーを置いてビルドし、
  修正前は Next が `- Environments: .env.production` と読み込んでいたこと、
  修正後はイメージ内にファイルも値も残らないことを確認した。
- **`.gitignore` が `.env` を完全一致でしか除外していなかった。** `.env` を編集した
  ついでにできる `.env.bak` や、`.env.production` は素通りする。中身は同じ秘密なので
  `.env*` で除外し、`.env.example` だけ戻す形にした。
- **サイドバーの「支出の内訳」が合計と合っていなかった。** 何かに付けたものは、
  付けた先の行に値段が畳み込まれる（サイバースパーはインプラントの行に、弾薬は
  銃の行に、プレートはジャケットの行に）。内訳は公開された行を費目ごとに足し直して
  作っていたので、その金額を二度数えていた。Chummer のテストセーブ 34 件のうち
  **29 件で内訳の合計が総額を上回り**、最悪のもので 61,910¥ ずれていた。
  gear エンジンが数えながら持っている費目別の集計をそのまま出すようにしたので、
  各行は必ず総額に戻る（34/34 で一致）。自作ドラッグは内訳に行が無く、
  払っているのに出てこなかったのもこれで直った。
- **作成時の可用性の上限を、セーブが持っている値で見るようにした。** `<maxavail>` は
  `.chum5` が自分で運んでくる数少ないハウスルールで、ゲームプレイオプションが
  決める（Standard 12、Prime Runner 15）うえ、卓が任意に動かせる。これを読まずに
  プリセットの 12 を当てていたので、Chummer 自身のテストキャラ 4 人が、
  そのキャラの上限内に収まっている装備 7 点を「入手可能度超過」と言われていた。
  書き出しでも同じタグに戻す。

- **依存のインストールが一過性のレジストリ障害で落ちるのをやめた。** PyPI も npm も
  常時可用が保証されたサービスではなく、インデックスが一瞬空を返すと pip は
  それを「指定が満たせない」と同じ形で報告する（`(from versions: none)`）。
  実際 PR #179 がこれで赤くなったが、見えなかったはずの wheel は全インタプリタ
  ぶん存在していて、`requirements.txt` のバージョン指定をどう変えても防げない
  たぐいのものだった。`scripts/retry.sh` が 15 秒・60 秒あけて 3 回まで試す。
  CI・Dockerfile・`make setup` の各インストールに噛ませた。**バージョン指定は
  これまで通りゆるいまま**（`pydantic>=2.13.5` などを締めてはいない）。

- **`cf-connecting-ip` を無条件に信じるのをやめた（レート制限の回避）。** この
  ヘッダを上書きするのは Cloudflare だけで、その後ろでない配置では呼び出し側が
  好きな値を書ける。リクエストごとに別の値を送れば、レート制限を素通りできた。
  `TRUST_CLOUDFLARE_IP=1` を設定したときだけ読む（`TRUSTED_PROXY_HOPS` と同じ扱い）。
- **API の応答にもセキュリティヘッダを付けた。** 同梱の構成では Caddy と Next が
  付けているが、バックエンドを直接公開する構成では何も付いていなかった。
  `nosniff`・`X-Frame-Options: DENY`・`Referrer-Policy`・COOP/CORP と、
  文書ではないことを示す CSP を付ける。
- **コンテナを読み取り専用で動かすようにした。** 実行中に image へ書き込む
  ものは無い（状態を持たず、Caddy と supervisord の書き込みは /tmp、Python は
  pyc を書かない）ので、compose では `read_only` にし、Linux の権限を全部落とし、
  権限の獲得も禁じ、/tmp と Next のキャッシュだけ tmpfs にした。CI でも同じ形で
  起動して確かめる（これまで image は作るだけで動かしていなかった）。
- **依存のインストールでスクリプトを実行しないようにした。** `npm ci
  --ignore-scripts`（Dockerfile・CI・make setup）。乗っ取られた依存が
  インストール時に任意のコードを動かす経路を断つ。この構成では必要な
  インストール時スクリプトは無く、ビルドもテストも通る。
- **サイバーウェアとバイオウェアの行にも「闇市」のチェックを出した。** 品目ごとの
  割引（#172）で、ウェアだけ画面から選べないままだった。
- **闇市の割引を、品目ごとに選ぶようにした（Chummer の `<discountedcost>`）。**
  Black Market Pipeline は分類の全部が安くなる資質ではなく、その分類の品目を
  1 つずつ選んで 10% 引きにするもの。これまでは対象分類を丸ごと自動で
  引いていた。.chum5 とも往復する。
- **Made Man では値段が変わらないようにした。** Chummer の Made Man は
  コンタクトを 1 人足すだけで、制限品の値引きはしない（`ImprovementType.MadeMan`
  は値段に使われていない）。Dealer Connection は Chummer と同じく自動のまま。
- **キャリアのセーブのカルマと新円を、残高として読み書きするようにした。**
  Chummer の `<karma>` / `<nuyen>` は使える残りだが、稼いだ合計として読んで
  いたので、読み込むと残りが大きくずれていた。今は履歴（`<expenses>`）の稼ぎを
  報酬として読み（Street Cred もこれで数える）、構成と報酬から出る残りと
  セーブの残高との差（払った家賃や別の値段での購入など）を「Chummer との差」
  として持つので、残高が保存どおりになる。書き出しも残りを書く。差はサイド
  バーに出て、消すこともできる。
- **最初から付いている品目を、入手可能度の上限で調べないようにした。** デザイナー
  防具の Ruthenium Polymer Coating（16F）など、防具・武器・車両・ギア・ウェアに
  付属する品目は親の入手可能度に含まれるので、Chummer の `CheckRestrictedGear`
  と同じく単独では数えない。
- **コムリンクの数量を読み書きするようにした。** Meta Link を 2 台持つセーブが
  1 台分しか払っていなかった。画面でも数量を変えられる。
- **コムリンクに最初から入っているアプリを無料にした。** Nixdorf Sekretar の
  Agent（評価値 3）を、古いセーブの読み込みで別に 3,000¥ 払わせていた。
- **マウントを記録していない古い .chum5 の武器アクセサリーで「空きマウント
  なし」が出ていた。** Chummer の「None」マウントは枠を使わない。セーブが
  None と書いた付属品はそのまま付け、書き出しでもマウントの無い付属品は
  None と書く。旧名の「Silencer」は今の Silencer/Suppressor として読む。
- **武器に最初から付いている付属品が、アクセサリーマウントを埋めていた。**
  Chummer は付属品を武器の「Internal」マウントに置き（武器のデータがその付属品の
  マウントを指定しているときだけ、そのマウントを使う）、Ingram Smartgun X の
  内蔵ガスベントがバレルを塞いで Electronic Firing を付けられない、という
  ことは起きない。同じく扱う。
- **ライフスタイルの資質と費用を Chummer に合わせた。** .chum5 からライフ
  スタイルの資質を読み込み、書き出すようにした。費用は Chummer と同じ段階計算
  （倍率は足さずに掛け合わせる、娯楽の資産 → それ以外の資質 → 契約の順）にした。
  資質の「allowed」は取得できるライフスタイルの制限ではなく、そのライフスタイル
  では LP を使わないという意味なので、Low でも Grid Subscription を買え、Medium の
  Gym も LP を使わずにお金を払う。ライフスタイルに最初から付く Grid Subscription
  だけが無料。
- **セッティングの技能の上限が効いていなかった。** 作成時は 6 に固定されていて
  `maxskillratingcreate` / `maxknowledgeskillratingcreate` を無視し、キャリアの
  `maxknowledgeskillrating`（知識技能の上限）は技能グループの上限として読まれて
  いた。Chummer と同じく、行動技能と技能グループは技能の上限、知識技能は
  知識技能の上限に従う。
- **知識技能点を超えた分をエラーにしていた。** Chummer は Priority /
  Sum-to-Ten で、知識技能点で足りない分を行動技能の技能点から払う。同じく
  技能点から払い、その旨を注意として出す。技能点も尽きたときだけエラーになる。
- **Chummer が書いた .chum5 のバイオウェアが一切読み込まれていなかった。**
  Chummer はバイオウェアも `<cyberwares>` に `<cyberware>` として書き、
  `<improvementsource>Bioware</improvementsource>` でだけ区別する。サイバー
  ウェアとして読んだ結果、値段・エッセンス・効果ごと落ちていた。
- **.chum5 の弾薬などの数量を 10 倍で読んでいた。** Chummer の `<qty>` は個数
  （100 発）で、この app の数量は値段の単位（10 発入り 1 箱）で数える。
  取り込みでは `costfor` で割り、書き出しでは掛ける。弾薬を持つ実キャラの
  新円が数万単位で多く出ていた。
- **「作成時にレーティング 6 の技能は 1 つまで」のエラーを外した。** SR4 の作成
  ルール（6 を 1 つ、または 5 を 2 つ）が紛れ込んでいた。SR5 の上限は各技能 6
  （Aptitude で 7）だけで、個数の制限は無く、Chummer も咎めない。上限そのものは
  これまでどおり守られる。
- **書き出した .chum5 を Chummer で開くと、技能が一つも無かった。** 技能を
  `<skills><skills>` に名前で書いていたが、Chummer は `<newskills>` を読み、
  行動技能は skills.xml の id（`<suid>`）が無いと捨てる。Chummer と同じ形で
  書く。取り込みでは知識技能の専門化も読むようにした。
- **Chummer が書いた .chum5 の技能が一切読み込まれていなかった。** Chummer は
  技能を `<newskills>` に、行動技能は名前でなく skills.xml の id（`<suid>`）で
  書く。この app は自分の書き出し形式（`<skills>`・名前）しか読まず、行動技能・
  技能グループ・知識技能・専門化がすべて落ちていた。Chummer 5.212.72 より前の
  セーブにある、フラグの無い母語（点を振っていない言語）も Chummer と同じく
  母語として読む。
- **.chum5 のウェアの子品目を、すべて無料で読み込んでいた。** サイバーリムに
  入れた Customized Agility や Biomonitor のように、利用者が買って入れたものも
  「親に付属」扱いになり、値段 0 だった。Chummer と同じく `<parentid>` で
  見分け、親のデータが自分で付けたものだけを付属として読む。書き出しも
  `<guid>` / `<parentid>` を書く。
- **.chum5 の 3 段以上に入れ子になったウェアの親子関係が崩れていた。**
  モジュラーコネクタ → アーム → 強化部品のような入れ子で、孫以下がすべて
  最上位の子として読み込まれていた。強化部品の入手可能度や容量が最上位に
  積まれ、コネクタが入手可能度 22（正しくは 8）、アームが容量超過（18/15）と
  誤って出ていた。
- **最初から付いている付属品の入手可能度を、親に足していた。** Ares Predator V
  や Ares Alpha の内蔵スマートガン（`+2R`）のように品目に含まれているものは、
  その品目の入手可能度にすでに入っている。Chummer と同じく、武器の付属品・
  防具の改造・車両の改造・武器マウント・ギアの子品目では足さない（ウェアの
  子品目は Chummer でも足すのでそのまま）。Predator V は 7R ではなく 5R になり、
  入手可能度 12 を超えたと誤って出ていた Ares Alpha（13F）なども通る。
- **テクノマンサーのストリームが .chum5 から読めていなかった。** 今の
  Chummer はストリームを `<tradition>`（`<traditiontype>RES</traditiontype>`）
  に書くが、この app は旧形式の `<stream>` しか読まず、`Default` を知らない
  流派として捨てていた。
- **Chummer が綴りを直した品目を、古い保存ファイルの旧名でも読む。**
  `Biocompatability`→`Biocompatibility`、`Dishevelled`→`Disheveled`、
  `Rapelling Gloves`、`Ondanstron`、`Metagenetic Improvement`、
  `Spirit of Guidance` など。古い保存ファイルにはこれらの sourceid が無く、
  名前でしか照合できない。
- **Prototype Transhuman で選んだネガティブ資質を .chum5 で往復させる。**
  Chummer は選んだ資質を別の資質行（`<qualitysource>Improvement</qualitysource>`、
  `<sourcename>` に親の名前）として持ち、親の `<extra>` は空にする。この
  app はその行を読み飛ばして「選択が必要」と出し、書き出しでは親の
  `<extra>` にしか書かず Chummer 側で選択が消えていた。子の行と、親子を
  結ぶ SpecificQuality の改善を読み書きし、子の選択（Allergy の対象、
  Wanted の相手）も保つ。

## [0.2.1] — 2026-09-05

### Security

Dependency-only release. `0.2.0` ships a frontend build with five known
advisories in it; the image published for that tag is not rebuilt, so
self-hosters on `:0.2.0` should move to `:0.2.1` (or `:0.2`, which now points
here). Nothing else changed — no rules, no API, no UI.

- `sharp` 0.34.5 → 0.35.4, for four libvips CVEs (GHSA-f88m-g3jw-g9cj).
- `postcss` 8.4.31 → 8.5.28, for arbitrary `.map` file disclosure via an
  attacker-controlled `sourceMappingURL` (CVE-2026-45623, CVE-2026-73646) and
  two lesser issues (CVE-2026-41305, CVE-2026-69153). Pinned through an
  `overrides` entry so Next stays on 15.x: the automated fix wanted Next 16,
  which is a migration rather than a patch.
- `next` 15.5.23 → 15.5.25.

Neither package is reachable from a request — `postcss` reads this project's
own CSS at build time and `sharp` backs Next's image optimisation, which this
app does not use on user input — so the practical exposure was low. `npm audit`
now reports zero.

## [0.2.0] — 2026-09-05

### Added

- **Read-only share links.** A character is encoded into the URL fragment and
  opened at `/share#c=…`. The fragment never reaches the server, so nothing is
  uploaded and nothing is stored; the view is `noindex`. Long links and dropped
  portraits are reported as a notice on a link that worked, not as an error.
- **English UI.** Every string is in `lib/i18n` behind a language switch, and
  the SR5 vocabulary tables, the formatters, the text sheet and the error copy
  all follow the locale. A locale that is missing a key fails the build.
- **Build-check panel** — the chargen errors and warnings in one place.
- Accessibility pass: every control has a name, the tab bar is a named `<nav>`
  with `aria-current`, there is a skip link ahead of the toolbar, and focus is
  visible. `eslint-plugin-jsx-a11y` is enforced.
- Catalog pickers say why a list stops where it does — how many rows were cut
  off, and that an empty search box lists core-rulebook entries only.
- `X-Request-ID` on every response, and `LOG_FORMAT=json` for one structured
  log line per request (`LOG_LEVEL` to go with it).
- End-to-end tests (Playwright) and coverage reporting for both halves.

### Changed

- **Japanese Run & Gun entry names.** 31 names that had no Japanese at all are
  now translated, and four existing ones were corrected (`コーティング`, not
  `コーディング`). Three entries stay in Latin script because the book prints
  them that way. Bracket and colon conventions in the overlay are now linted.
- `GET /api/catalog` is served with an ETag, so a reload revalidates into a 304
  instead of re-transferring ~2.9 MB.
- Addon dropdowns (armor mods, commlink accessories, vehicle mods, lifestyle
  qualities) no longer widen when the unrelated catalog search box below them
  has text in it; the narrowing is unconditional.
- Docker base images are pinned by digest and the image ships a baseline CSP.
- Collections sent by a client are size-capped in the models.
- A `v*` tag now publishes a GitHub Release from this file, and the image gets
  a `{major}.{minor}` tag to pin against.

### Fixed

- The knowledge-skill picker cut its list to 40 rows **before** removing the
  skills you already had, so a character with many knowledge skills was shown
  an empty list.
- A truncated catalog list now says it is truncated instead of looking complete.
- The per-IP rate limiter no longer trusts a client-supplied
  `X-Forwarded-For`, which let one caller present as many.
- Two `specialArmorBits` implementations had drifted; the sheet now uses one.

### Internal

No behaviour change, but this is most of the diff: `store.py`, the catalog
projection, the `.chum5` reader and writer, the weapons engine and the magic
loader were each split along their own seams, and the seven copies of the
catalog picker became one component. Test coverage went from ~49% to ~76% on
the frontend and ~91% to ~92% on the backend, with the panels that patch a
character — gear, weapons, vehicles, skills, qualities, lifestyles — and the
editor hook that owns the only copy of it covered for the first time.

## [0.1.0] — 2026-09-02

First tagged release.

### Character builder

- Build methods: Priority / Sum-to-Ten / Life Modules.
- Metatype + metavariants, attributes, active / knowledge / exotic skills and
  skill groups, positive & negative qualities.
- Augmentations (cyber- and bioware, grades, nested), armor + mods, weapons +
  accessories + ranges + recoil, commlinks / cyberdecks / RCCs / programs,
  drones & vehicles + mods + weapon mounts, lifestyles, contacts, martial arts.
- Magic: spells, spirits, foci, adept powers, mentor spirits, traditions,
  initiation + metamagics. Resonance: complex forms, sprites, submersion + echoes.
- Career mode: karma / nuyen reward ledger, chargen baseline diff, street cred.
- Derived-stat engine (`compute()`), chargen validation with errors / warnings.

### Import / export

- Chummer5a `.chum5` / `.chum5lz` import (best-effort; unresolved items become
  warnings) and `.chum5` export.
- JSON save / load.
- Cocofolia コマ + BCDice chat-palette export; conjured spirits / sprites as
  separate コマ.
- Character sheet: standard / compact / text / print (A4) layouts.

### Platform

- Japanese-first UI; terminology overlay on top of the Chummer JA translations.
- **Stateless backend** — characters live in the browser (IndexedDB); the
  server only computes and transforms.
- Import path hardened: `defusedxml`, request-size cap, `.chum5lz`
  decompression-bomb cap, per-IP rate limiting.
- chummer5a game data pinned to a commit and fetched at build time.
- One-container Docker image (Caddy + uvicorn + Next standalone) published to
  GHCR; `make up` / `compose.yaml` for local self-hosting.

[Unreleased]: https://github.com/kenken-trpg/chummer-web/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/kenken-trpg/chummer-web/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/kenken-trpg/chummer-web/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/kenken-trpg/chummer-web/releases/tag/v0.1.0
