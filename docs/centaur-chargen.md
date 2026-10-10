# ケンタウロス作成対応の開発状況

開始日: 2026-10-10。対象はCentaur単独。
基準データは同梱NOTICEのchummer5a固定コミット
`d7e94f6a090f267362757675d05bbe4d7543c217`。
要件は開発環境の `/private/tmp/chummer-web-nonhuman-chargen-research.md` §17に基づく。
この文書は実装状況を記録し、ルール本文の照合結果とは区別する。

## 実装済み: 生得付与のデータ読込

- 種族XMLの正負資質と固定パワーを読み、各付与のselect、rating、removableを保持する。
  同名の繰り返し指定を集合にまとめない。
- 生得付与の参照解決に使えるよう、資質ローダーで非表示定義の読込を明示的に指定できる。
  通常の購入候補は従来どおり非表示定義を除外する。
- クリッターパワーのbonusとrequired/forbiddenツリーを明示指定で読み込める。
  一般パワーには未対応のbonusタグがあるため、計算へ接続するまで通常カタログは説明用のままとする。
- パワー参照はIDを優先し、名称指定ではXMLの最初の定義を使う。
  標準Search / Natural WeaponのIDを同梱データのテストで固定した。
  カスタムデータで特定の同名定義を参照するときはIDを使う。

## 実装済み: 生得資質・固定パワー・蹴りの導出

- Centaurの資質4件を種族から導出し、Metatype由来、無料、資質上限・SURGE枠の対象外として扱う。
  購入リストへ自動挿入せず、購入済みの同種資質の記録を残して効果を一度だけ適用する。
  種族変更時には生得由来だけがなくなり、購入記録は残る。
- 蹴りを資質のaddweaponから1件生成する。
  STR3で5P、AP +1、Reach 1、Accuracy Physical、Unarmed Combat、0¥となる。
  Natural Weaponパワーのselectから第2の武器を生成しない。
- SearchとNatural Weaponを標準IDで導出し、出典・行動・固定selectを保持する。
  パワーのbonusを効果収集へ通し、要件判定にパワー名を渡す。
  カスタムデータによる標準IDへの変更と、未解決の付与定義の警告を検証する。
- 資質欄に生得由来・追加カルマなし・削除不可を表示する。
  メタタイプ欄、通常/印刷シート、テキスト出力で固定パワー・select・出典を表示する。
- 再計算・JSON再読込・種族往復で付与を増殖させない。
  生得付与をキャリアの購入・買い戻しに数えず、重なる購入資質の過去の支出を保持する。
- 亜種は親種族の配下だけで解決する。Centaurへの変更で他種族の亜種指定が残った場合、
  警告付きで解除し、Centaurの生得付与と能力値を維持する。

`test_centaur_data.py`はデータ境界、`test_centaur_grants.py`は実データを使ったcomputeと
JSON往復・カスタムデータの検証。作成画面の候補公開を証明するものではない。

## 実装済み: `.chum5`への生得付与保存とWeb内往復

- 生得資質4件をqualitysource=Metatype、contributetobp/contributetolimit=Falseで保存する。
  購入済みの同種資質のSelectedレコードも独立に保存し、再importで購入記録を失わない。
- 蹴りを資質のweaponguidと武器のparentidで結び付ける。
  武器にはSTR式、Physical参照、AP +1、Reach 1、費用0、アクセサリ不可を保存する。
  importでは既存のparentid判定により購入装備に混入せず、種族から1件だけ再導出する。
- Search/Natural Weaponを標準ID、固定extra、grade=0、counttowardslimit=Falseで保存する。
  種族変更時のパワー除去に必要なMetatype/CritterPower improvementもパワーGUIDに結び付ける。
- `test_centaur_chum5.py`で生成XMLの各フィールド・所有リンク、3回のWeb内往復、
  購入済み資質・武器との分離を検証する。

保存フィールドの照合先は固定コミットの
[Quality.Save](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Uniques/Quality.cs)、
[CritterPower.Save](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Uniques/CritterPower.cs)、
[Weapon.Save/Load](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Equipment/Weapon.cs)、
[Character.Create](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Characters/Character.cs)、
[ImprovementManager.Create/Remove](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Static/Managers/ImprovementManager.cs)。
テスト用XMLは生成fixtureであり、Chummer GUIが保存した実ファイルではない。
実機で開いた後の再保存や、種族変更時のChummer側動作の検証は未実施。

## 実装済み: 地上・水泳・飛行の移動と生活費の計算検証

- `movement.modes`にGround/Swim/Flyそれぞれの率・利用可否・距離・ヒット当たり加算を保持する。
  従来のmovement直下のwalk/run/sprintは地上の値として維持する。
- 固定コミットのCharacter.CalculatedMovementに合わせ、水泳は義肢を含む全身AGI/STRの平均、
  地上/飛行は生身AGIを使う。設定による義脚AGIの置換は地上だけへ適用する。
  カテゴリ別の固定/割合補正を混ぜず、小数の移動率も保持する。
- CentaurのAGI3/STR3は地上3m/12m・疾走4m毎ヒット、水泳3m・追加1m毎ヒット。
  飛行率は全て0であり、通常/印刷/テキストシートの飛行欄を表示しない。
  旧キャッシュにmodesがなくても地上欄は従来どおり表示する。
- `addlimb`が腕2/脚4/胴1/頭1と、義肢平均の分母8へ届くことを検証した。
  `limbslotcount=all`は脚4として平均する。公式CalculatedMovementの義脚条件は
  四脚でも2スロット以上であり、既存条件を維持する。
  四脚全てを個別に指定するUI/保存は未完了。Redlinerの計算は下記の範囲を検証した。
- 固定コミットのLifestyle.GetTotalMonthlyCostと照合し、Centaurの+150%を対象部分へ適用する
  既存処理を検証した。基本2,000¥は5,000¥。扶養・その他補正は区分ごとに合成し、
  外出/契約の定額費用を種族補正で増やさない。複数生活様式・複数月の支出内訳も一致する。

検証は`test_centaur_body.py`、既存5キャラクターの派生値snapshot、シート表示テストによる。
照合先は固定コミットの[Character.CalculatedMovement/LimbCount](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Characters/Character.cs)と
[Lifestyle.GetTotalMonthlyCost](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Equipment/Lifestyle.cs)。
生活費のRF本文・装備適合条件、四脚の個別義肢管理、実機での一致確認は引き続き残件。
シェイプシフターのalt移動率・形態同期はこの変更の対象外。

## 実装済み: Redlinerの追加肢・全脚置換・ボーナス上限

- `effects.extra_limbs`をRedliner/Cyber-Singularity Seekerの集計へ渡す。
  Centaurでは脚の集計枠が4となり、`limbslotcount=all`も4肢として数える。
  集計対象を空に指定した場合は、標準の腕/脚へ戻さず0肢とする。
- 集計した肢数と効果の上限を分離する。参照元の`min(count / 2, 2)`に合わせ、
  6肢を数えてもSTR/AGIまたはWILへのボーナスは最大2。
  既存の義肢強化上限も引き続き適用する。
- Redlinerの身体ダメージ欄へのペナルティをボーナス1点につき3枠へ修正する。
  2肢なら-3、4肢以上なら最大-6。同梱qualities.xmlのBOXの注記と
  `RefreshRedlinerImprovements`の`intCount * -3`を照合した。
  この修正は基本種族にも適用される。
- 実データの全脚置換装備と両腕で6肢になるケースについて、再計算、JSON、
  Web内`.chum5`往復、Human↔Centaurで集計枠が4↔2へ戻ることを検証する。
  装備名はLiminal Body, Tank (Full)であり、テストは計算経路の検証に限定する。
  Centaurがその装備を正典上装着できることの根拠にはしない。
- 左右の保存値は参照元でも`Left`/`Right`で、追加肢は片側の枠数を増やす構造。
  Web側には同じ側を1肢として扱う判定が残るため、個別の四脚指定は未完了。
  前後の位置を推測で追加しない。部分義肢・モジュラー義肢の集計範囲の一致も残件。

検証は`test_centaur_redliner.py`と既存のRedlinerテストによる。
照合先は固定コミットの
[Character.RedlinerBonus/RefreshRedlinerImprovements](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Characters/Character.cs)と
[Cyberware.LimbSlotCount/GetCyberlimbCount/SelectSide](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Equipment/Cyberware.cs)。
CF本文・エラッタ、RFの装備適合条件、Chummer GUI fixtureの確認は未実施。

## 実装済み: 生得MAGの開始値と既存購入・成長経路への接続

- 種族の`enableattribute`とTalentから、有効なMAG/RESと無料開始値を共通に解決する。
  XMLに能力値範囲があるだけ、または`enabletab`だけでは有効化しない。
  MundaneのCentaurはMAG1、RES0となり、種族変更・Talent変更・作成方式変更でもMAGを0に戻さない。
- Priority/SumToTenのMagician/AdeptはTalentの開始値で置換し、生得MAG1を加算しない。
  Karma式では開始値1。無料開始値を特殊点や能力値カルマへ請求しない。
  MAG1→3は特殊点2、上の1レベルをカルマで買う場合は特殊点1と15 karma、
  Karma式で全て買う場合は25 karmaとなる。
- 能力値範囲・要件判定・購入済み値・費用の無料開始値を揃え、既存の能力値画面で編集できる。
  生得MAGだけでは術式・精霊・アデプト・収束具のタブを有効化しない。
- 既存エッセンス損失設定を生得MAGにも適用する。DatajackでESS5.9、通常設定ではMAG0、
  上限だけ下げる設定ではMAG1。購入済みMAG1と生得付与の所有記録は保存する。
  `.chum5`のmagenabled、MAGのmetatypemin/base/karma、Web内往復も検証した。
- Priority式キャリア移行ではMAG1をbaselineへ保存し、MAG1→2を既存の10 karmaで計上する。
  基本5種族MundaneのMAGは引き続き0であり、既存snapshotの変更は不要。

開始値置換は固定コミットの
[SelectMetatypePriority](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Forms/Character%20Creation%20Forms/SelectMetatypePriority.cs)
のAssignLimits、価格は
[CharacterAttrib.TotalKarmaCost/UpgradeKarmaCost](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Attributes/Attribute.Core.cs)
を照合した。`test_centaur_magic.py`と能力値/タブ表示のテストで上記を検証する。
これはChummer固定版コードと既存エンジンへの接続であり、RF本文・エラッタやGUI fixtureの確認完了を意味しない。
生得MAGだけでのイニシエーション、共鳴Talentとの共存可否、キャリアのburnout、
MAG0時の生得能力の利用可否は未確定。これらの新しい権限や自動削除処理は導入していない。

生得MAGの残る権限・burnout仕様、四脚の個別義肢管理、正典実機での`.chum5`往復は未完了であり、
Centaurを作成画面の候補へ公開する段階には達していない。

## 次の実装と公開条件

1. 正典で生得MAGとTalent・購入・成長・MAG0時の扱いを確認する。
   四脚の個別義肢指定/保存とRedliner、生活費のRF本文と装備適合、実`.chum5`も照合する。
   未確定の数式を推測で導入しない。
2. 生得資質・パワー・蹴りの導出は上記の範囲を実装済み。
   `.chum5`の由来付き資質・パワー・自然武器の保存とWeb内往復も実装済み。
   正典実機で保存したファイルとの往復は引き続き確認する。
3. 蹴りの素手攻撃修正・STR変動・他の自然武器との組合せを引き続き検証する。
4. 生得MAG1の保持、Patch・特殊点・カルマ・キャリアbaseline・既存エッセンス損失への接続は上記範囲を実装済み。
   RF本文・エラッタ・実機fixtureを確認し、イニシエーション、共鳴Talentとの共存、burnout、
   MAG0時の生得能力の利用条件を確定してから残る権限を実装する。
5. 地上/水泳/飛行の計算、追加脚の平均への接続、生活費と支出内訳は上記の範囲を検証済み。
   四脚の個別義肢指定/保存とRedliner、装備適合、正典実機での一致を引き続き確認する。
6. JSON/Patch/共有/IndexedDB/undo/redo/`.chum5`、キャリア移行、シート出力で往復確認する。
   基本5種族・亜種・感染者・SURGEへの回帰を確認する。
7. 以上を満たしてからRF条件付きで候補を公開する。
   Priority/SumToTenはA/B/Cのみ、特殊点6/3/0、追加25 karma。
   Karma式は種族60 karmaで追加25を重ねない。
   RF無効時は新規候補から除外し、既存Centaurは保持して出典警告を示す。

Naga/Pixie/Sasquatch、シェイプシフター、AIの候補公開は別の実装・検証単位とする。
