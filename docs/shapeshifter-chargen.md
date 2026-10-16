# シェイプシフター作成対応の開発状況

開始日: 2026-10-16。対象は metatypes.xml の category が `Shapeshifter` の 11 種
（Bovine・Canine・Equine・Falconine・Leonine・Lupine・Pantherine・Phocine・Tigrine・Ursine・Vulpine）。
基準データは同梱NOTICEのchummer5a固定コミット
`d7e94f6a090f267362757675d05bbe4d7543c217`。
照合先は同コミットのChummerのソースと、Chummer.Tests/TestFilesの実セーブ`Mittens Chargen.chum5`
（Vulpine/Human、SumToTen）。
この文書は実装状況を記録し、ルール本文（RF）の照合結果とは区別する。RF本文は未照合。

## データの形

- メタタイプが**動物の姿**、メタバリアントが**人間形態**（Human・Elf・Dwarf・Ork・Troll ほか22種）。
- 人間形態の側に、Shift (Metahuman Form) パワー、生得資質（Uneducatedは`removable="True"`）、
  噛みつきの`<naturalweapon>`、`<enableattribute>MAG`、`<enabletab>critter`が付く。
  動物の姿の側にはパワー・資質がない。
- 人間形態の移動率は`<walk alt="2/1/0">1/1/0</walk>`のように`alt`属性にあり、本文は動物の値。
- Priority表ではHeritage A/B/Cに入る（Vulpineなら特殊点8/6/4、追加5カルマ）。
  形態ごとに値段が違う（BovineのHumanは5、Elfは10カルマ。Karma式ではHuman 100、Elf 105）。
- 出典はRF。PhocineだけSAG。

## 実装済み: 作成時の計算（PR #592）

固定版の[Character.Create](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Characters/Character.cs)に合わせた。

- Chummerは、能力値の範囲をメタタイプ（動物の姿）から、カルマ・資質・パワー・bonusを
  メタバリアント（人間形態）から取る。`find_metatype`は、Shapeshifterのメタバリアントに
  親の`attributes`を載せて返す。
- 人間形態が未選択なら、Chummerと同じくHumanとして解決する（`bootstrap`）。
- `.chum5`の書き出しで、`removable="True"`の付与を`MetatypeRemovable`として書く。
- 明示的に送られた`metavariant: null`でメタバリアントをクリアする。
  これまでは捨てられており、Vulpine/HumanからHumanに変えると「Human」が残っていた。
- `Mittens Chargen`の能力値ポイント超過・自然上限の誤エラーが消えた。
  残る−49カルマは、Chummer側も予算超過（超過を0と保存）で、reconcileは一致扱い。

## 実装済み: 作成画面の候補（PR #594）

- 作成候補（`catalog()["metatypes"]`）に11種を加えた。Heritage行の絞り込みもこの一覧から取る。
- メタタイプ画面では、シェイプシフターのときメタバリアント欄を「人間形態」と表示し、
  「なし」は出さない。形態ごとの値段を選択肢に添える。
- 出典の本が無効なら候補に出さない。作成済みのキャラクターは保持し、既存の出典警告を出す。
- e2e `shapeshifter-creation.spec.ts`で、Priority・SumToTen・Karmaの3方式について、
  候補の値段、選択、Humanの付与（MAG 1・Shift・資質5つ・噛みつき・AGI 2〜7）、
  Elfへの切り替えと値段、再読込で保たれることを確かめる。

## 実装済み: 姿ごとの表示（PR #596）

固定版の[AttributeSection](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Attributes/AttributeSection.cs)の
`CopyAttribute`と`RemakeAttribute`に合わせた。

- 2つの姿は振ったポイント（baseとkarma）を共有し、最小値・最大値だけが姿ごとに違う。
  人間形態の値は「動物の値 −（動物の最小値 − 人間形態の最小値）」で、人間形態の範囲に収める。
  上限ボーナス（Exceptional Attributeなど）は両方の姿に掛かる。
- `derived.metatype_info.metahuman_form`に、各能力値のrating・total・min・max・augと、
  `alt`の移動率から計算した移動を出す（`engine/compute/_shapeshifter.py`）。
  地上は素のAGI（＋強化）、水泳は合計値を使う。本体の移動と同じ扱い。
- シートのコア欄、テキスト出力、能力値タブで、動物の姿と人間形態を並べて出す。
- `.chum5`の`<critter>`は`enabled_tabs`に従ってTrueと書かれる（`Mittens Chargen`と一致）。

検証は`backend/tests/test_shapeshifter_chargen.py`、MetaTab・AttrsTab・シートの単体テスト、
上記e2eによる。

## 残る項目

1. **RF本文の照合**。上記はすべて固定版Chummerのソースと実セーブへの一致確認であり、
   RFの本文・エラッタとは照合していない。
2. **キャリアの扱い**。Chummerはキャリアに移るとき、標準の能力値を人間形態の範囲で
   作り直し、動物の姿を別の一覧として持つ（`AttributeSection`の`xmlCharNodeAnimalForm`）。
   このアプリはキャリアでも動物の姿を主にしている。キャリアの実セーブとの照合は未実施。
3. **形態の切り替え**。Shiftで姿を変えたときに、どちらの値でダイスプールやリミットを出すかは
   扱っていない。現在は動物の姿で計算し、人間形態は並べて表示するだけ。
4. **噛みつき**。動物の姿の自然武器（Bite (… Form)）を、人間形態でも常に武器一覧に出している。
   武器の由来（`natural_source`）にはメタバリアント名（Human）が入る。
5. **外せる生得資質**。Uneducatedは`MetatypeRemovable`として保存するが、
   画面から外す（買い戻す）操作はない。メタバリアント全般にかかわる。
6. **`.chum5`の`walkalt`/`runalt`/`sprintalt`**。書き出していない。`Mittens Chargen`は動物と同じ値
   （1/1/0）を書いており、`alt`属性の値ではない。fidelityの検査は通る。
