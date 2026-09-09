# Chummer セッティングファイルの移植

Chummer の「セッティングファイル」（`settings/*.xml`）を chummer-web に移す計画。
本文書は **段階 3（customdata マージ）まで実施した時点**の記録。

## 何が足りていなかったか

移植済みだったのは `build_method`（Priority / SumToTen / Karma）だけで、
Chummer が `<settings>` に持つものはほぼ全てハードコードか未実装だった。

| Chummer の要素 | 実装前 | 段階 1 後 |
| --- | --- | --- |
| `<books>` 使用書籍 | なし（全 63 書籍が常時出る） | `SettingsState.books` |
| `<buildmethod>` | あり | プリセットから適用 |
| `<customdatadirectorynames>` | なし | `SettingsState` + マージ実装 |
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

## 段階 3 — customdata のマージ（実施済み）

`<customdatadirectorynames>` が指す `customdata/*/` を、**ローダより上流の
XML ツリー**に適用する。追加された格闘技は、最初から同梱されていたものと
区別がつかない。

### amend の方言

Chummer の amend エンジンは大きい（xpath フィルタ、`replace`、`recurse`、
`regexreplace`）。実データが使うのは 4 つだけだった:

* `<id>`（無ければ `<name>`）一致で、同じタグの子要素を差し替える
* `amendoperation="addnode"` — 差し替えでなく追加
* `amendoperation="remove"` — その子要素を削除
* `pathfilter="field='value'"` — id でなくフィールドで対象を選ぶ

公開されている 5 セッティング分の customdata 全 23 XML で使われている属性は
`addnode` 63 回・`remove` 1 回・`pathfilter` 1 回で、他は全部 id 一致。
実装したのはこの範囲だけで、それ以外は**半端に適用せず報告する**。

### 一致判定で 2 回踏んだ罠

* **GUID の大小文字**。manifest は `5682BC90-…`、それを参照する
  セッティングは `5682bc90-…` と書く。
* **Unicode 正規化**。日本語のディレクトリ名は macOS のファイルシステムから
  NFD で、それを名指す XML からは NFC で来る。同じディレクトリで、バイト列が
  違う。

どちらも `_fold()`（casefold + NFC）で吸収する。

### どこに置くか

`catalog()` はプロセス全体のシングルトンで、エンジンから 36 ファイル・
102 箇所で直接呼ばれている。引数で回すのは大工事なので、`app/rules.py` と
同じく **ContextVar** にした:

* `_xml.parse_data(name)` / `data_root(name)` — 全ローダの唯一の読み口。
  オーバーレイがあればそれを、無ければ vendor を返す（31 箇所を置換）
* `catalog()` はオーバーレイのキーで LRU（4 件）。素で遊ぶ卓と customdata の
  卓が同じプロセスに来るので、1 件キャッシュでは足りない

### content-hash + サーバ側 LRU

ブラウザが `customdata/` のファイルを持ち、サーバは**マージ結果だけ**を
内容ハッシュの下に持つ。

1. リクエストはハッシュ（32 バイト）だけを運ぶ
2. サーバがそのハッシュを知らなければ **409** と「どのセットが要るか」を返す
3. クライアントが IndexedDB からファイルを送り、同じリクエストを 1 回だけ再送

サーバ側は永続化しない。再起動で消えて、次のリクエストが再アップロードする。
キャラクターはブラウザにあるので、消えて困るものは無い。

**`dataset` が空のときは 409 にしない。** セッティングが customdata を
参照していて、ユーザーがまだ読み込んでいない状態は「拒否する状態」ではなく
「素のデータで計算しつつ、UI が不足を告げる状態」。ここを拒否にすると、
キャラクターが計算不能になる（実装中に実際に踏んだ）。

### 段階 3 で対応していないもの

* `critters.xml` — この app がそもそも読んでいないので、amend も適用できない。
  スキップとして報告される
* Chummer の amend エンジンの残り（xpath フィルタ、`regexreplace` ほか）

## 権利面

同梱には踏み込まない。詳細は `NOTICE.txt` の方針（ルール本文は再録せず
ページ番号で参照）に従い、

* 第三者が配布するセッティング / customdata は**同梱せずローカル読み込み**、
* 同梱する場合は作者の明示的な許諾と `NOTICE.txt` への出典追記が前提。

fan-made の追加データ（新しい格闘技スタイル・技法・武器など）は
ページ番号参照ではなく創作物そのものなので、特に上記が必要。
