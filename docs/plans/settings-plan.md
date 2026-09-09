# Chummer セッティングファイルの移植

Chummer の「セッティングファイル」（`settings/*.xml`）を chummer-web に移す計画。
本文書は **段階 2（セッティング XML の読み込み）を実施した時点**の記録で、段階 3 は未実施。

## 何が足りていなかったか

移植済みだったのは `build_method`（Priority / SumToTen / Karma）だけで、
Chummer が `<settings>` に持つものはほぼ全てハードコードか未実装だった。

| Chummer の要素 | 実装前 | 段階 1 後 |
| --- | --- | --- |
| `<books>` 使用書籍 | なし（全 63 書籍が常時出る） | `SettingsState.books` |
| `<buildmethod>` | あり | プリセットから適用 |
| `<customdatadirectorynames>` | なし | なし（段階 3） |
| `<sumtoten>` / `<priorityarray>` | 定数 | 定数のまま |
| `<karmacost>` 40 項目 | 定数 | 定数のまま |
| `<maxskillratingcreate>` ほか上限 | 定数 | 定数のまま |
| `<bannedwaregrades>` | なし | なし |
| ハウスルール約 150 フラグ | ほぼなし | ほぼなし |

## 段階 1 — 使用書籍で絞る（実施済み）

* `data_loader/loaders/books.py` — `books.xml` と `settings.xml` を読む。
  後者は「この app が実際に適用できる部分」（書籍・作成方式）だけに射影し、
  エンジンに無い作成方式（LifeModule）のプリセットは**黙って Priority に
  書き換えず、落とす**。
* `models.SettingsState` — `{name, books}`。`books` が**空 = 無制限**。
  設定機能が無かった頃に作られたキャラが、いきなり装備を失わないための規約。
* 絞り込みは**クライアント側**、`CatalogPicker` / `PickerList` の 2 箇所だけ。
  カタログ本体は絞らない — カタログは所持品の名前・数値・ページ参照の引き先
  でもあり、そこを削ると「GM が後から書籍を外した」瞬間に、売却のために
  見たいはずの手持ち装備が消える。
* `.chum5` は**セッティング名しか運べない**（Chummer は書籍をセッティング
  ファイル側に持ち、セーブに含めない）。読み込み時は同梱プリセット名と
  照合して書籍を復元し、知らない名前は「名前だけ・無制限」で戻す。

### 段階 1 で意図的にやらなかったこと

* **所持品の書籍違反チェック**。書籍を外したときに、既に持っている装備・資質・
  術式を警告する検証。install の種類ごとに触る必要があり、段階 3 と一緒に
  やるほうが安い。
* エンジン定数の設定値化（カルマ表・各種上限）。段階 2。

## 段階 2 — セッティング XML の読み込み（実施済み）

* `app/settings_file.py` — `settings/*.xml` を `SettingsState` に読む。
  パースはサーバ側。Chummer XML の知識が全部そこにあるのと、「このファイルは
  何を変えたか」の判定に同梱 `settings.xml` との比較が要るため。
  **保存はしない** — 読んで返すだけで、ルールセットはキャラクターの中を旅する。
* `app/rules.py` — `Rules`。エンジンの定数を「設定で変わりうる数値」と
  「変わらない数値」に割り、前者をここへ移した。エンジンからの参照は
  17 ファイル・約 100 箇所あり、その多くは `Ctx` を持たない自由関数なので、
  引数で回す代わりに **ContextVar** で `compute()` が 1 回だけ束ねる。
  `catalog()` が既にプロセス全体のシングルトンである前例に合わせた形。
* **未対応ノブの明示**。Chummer 標準（`Standard` プリセット）と比べて
  値が変わっていて、かつこの app が実装していないタグだけを列挙し、
  `engine.settings.unsupported` の警告として出す。全 160 タグを並べても
  ノイズにしかならないので、差分だけを見る。ユーザーの 5 ファイルでは
  `ignoreart` / `cyberlegmovement` / `mysaddppcareer` の 3 件に収まる。
* `<chargenkarmatonuyenexpression>` は `{Karma} * N + {PriorityNuyen}` の
  形のときだけ N を読む。この app の換算式がちょうどその形だから。
  それ以外は本物の式なので、近似せず未対応として報告する。
* 読み込んだファイルは `localStorage`（`lib/character/settings-store.ts`）。
  失っても再読み込み 1 回で済み、キャラクターは失われない。

**リポジトリに第三者のセッティングファイルを同梱しない**のが要点。
ローカル読み込みなら再配布に当たらない。

### 段階 2 で honour していないもの

`contactpointsexpression` / `knowledgepointsexpression` などの式、
エンカンブランス系、`limbcount`、イニシアチブ・ダイスの上下限。
いずれも未対応リストに出るので、黙って無視はしない。

## 段階 3 — customdata のマージ（未実施）

`<customdatadirectorynames>` が指す `customdata/*/` を適用する。これが無いと
書籍フィルタだけでは意味を持たないセッティングがある — たとえば日本語版
シャドウラン・コデックス向けのセッティングは、既存 SR5 / SG / HT 項目の
`<source>` を `JCD` / `JCDS` に**付け替える** amend が本体なので、customdata
なしで books を `[SR5, RG, JCD, JCDS]` に絞ると、実質 SR5 + RG に縮退する。

必要なマージ機能は実物を見る限り小さい:

* `custom_*.xml` — ノードの追加
* `amend_*.xml` — `<id>` 一致で子要素を上書き
* `amendoperation="remove"` / `="addnode"`

Chummer の amend エンジン全体（xpath フィルタほか）は要らない。

## 権利面

同梱には踏み込まない。詳細は `NOTICE.txt` の方針（ルール本文は再録せず
ページ番号で参照）に従い、

* 第三者が配布するセッティング / customdata は**同梱せずローカル読み込み**、
* 同梱する場合は作者の明示的な許諾と `NOTICE.txt` への出典追記が前提。

fan-made の追加データ（新しい格闘技スタイル・技法・武器など）は
ページ番号参照ではなく創作物そのものなので、特に上記が必要。
