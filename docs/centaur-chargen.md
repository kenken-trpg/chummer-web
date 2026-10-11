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

## 実装済み: 蹴りの素手攻撃修正・STR変更・他の自然武器との併用

- 固定版のWeapon.CalculatedDamage/TotalAP/TotalReachと同梱settings.xmlに合わせ、
  `unarmedimprovementsapplytoweapons`を設定XML・SettingsState・計算へ接続した。
  未指定/Falseでは蹴り等の武器へunarmeddv/unarmedap/unarmedreachを適用せず、
  Trueのときだけ適用する。従来のAP/Reachの無条件適用とDVの未適用を修正した。
  基本種族の同種武器にも同じ設定が適用される。
- 通常のUnarmed Attackは設定によらず修正を受ける。
  unarmeddvphysicalによるS→P変更はその基本攻撃だけに適用し、
  他の素手技能武器のダメージ種別を変えない。一般のReach修正・カテゴリDVは別経路を維持する。
- Bone Density Augmentation 2、Penetrating Strike 2、KarateのKick Attack、
  Unarmed Combatを選んだDeath Dealer (Adept)を使って検証した。
  STR3の蹴りは設定Falseで6P/AP +1/Reach 1、Trueで7P/AP -1/Reach 2。
  STR5へ変更するとTrueで9Pとなり、Physical参照のAccuracyも再計算する。
  購入したRazor Clawsと生得の蹴りを別の無料攻撃として保持し、種族変更で蹴りだけを除去する。
- 再計算・JSON再読込・設定Patchの切替で補正を累積しない。
  `.chum5`の蹴りは元のSTR式・AP +1・Reach 1を保存する。
  `.chum5`は別の設定ファイルを参照する形式であり、Webの個別設定上書きは埋め込まない。
  同じ設定を再適用したWeb内往復で、攻撃値と件数が変わらないことを確認した。

検証は`test_centaur_kick.py`による。照合先は固定コミットの
[Weapon.CalculatedDamage/TotalAP/TotalReach](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Equipment/Weapon.cs)と同梱settings.xml。
これは固定版コードへの一致確認であり、RF本文・エラッタ・GUI実保存の確認とは区別する。

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
  四脚の個別義肢管理とRedlinerの計算は下記の範囲を検証した。
- 固定コミットのLifestyle.GetTotalMonthlyCostと照合し、Centaurの+150%を対象部分へ適用する
  既存処理を検証した。基本2,000¥は5,000¥。扶養・その他補正は区分ごとに合成し、
  外出/契約の定額費用を種族補正で増やさない。複数生活様式・複数月の支出内訳も一致する。

検証は`test_centaur_body.py`、既存5キャラクターの派生値snapshot、シート表示テストによる。
照合先は固定コミットの[Character.CalculatedMovement/LimbCount](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Characters/Character.cs)と
[Lifestyle.GetTotalMonthlyCost](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Equipment/Lifestyle.cs)。
生活費のRF本文・装備適合条件、実機での一致確認は引き続き残件。
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
  個別の四脚指定は下記の範囲を実装した。
  部分義肢・モジュラーコネクタの集計は下記範囲を検証した。

検証は`test_centaur_redliner.py`と既存のRedlinerテストによる。
照合先は固定コミットの
[Character.RedlinerBonus/RefreshRedlinerImprovements](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Characters/Character.cs)と
[Cyberware.LimbSlotCount/GetCyberlimbCount/SelectSide](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Equipment/Cyberware.cs)。
CF本文・エラッタ、RFの装備適合条件、Chummer GUI fixtureの確認は未実施。

## 実装済み: 左右2本ずつの個別義脚管理

- 義肢ごとのinstall IDと既存のsideを使い、Centaurの左脚2本・右脚2本を別々に保持する。
  前後の位置や新しいside値は追加しない。2本脚では片側1本の制限を維持し、
  Centaurの腕も片側1本のまま。
- 種族・資質・装備の追加肢を読み取ってから左右の自動割当を行う。
  未指定の4脚はLeft/Right/Left/Rightとなる。子パーツが親より前に並んでいても
  親のsideを引き継ぎ、特注AGI/STRはそれぞれの脚へ適用する。
- 能力値平均とRedlinerは個別IDと片側枠数で集計する。
  同じ側の2本を1本へまとめず、片側3本目はエラーとして平均・Redlinerの集計から外す。
  部位を占有する資質の重複判定も追加肢の枠数を使う。
- `derived.body_limb_slots`を追加し、義肢追加画面の自動side選択へ渡す。
  この値がない旧キャッシュは従来の片側1本として扱う。
  5つの既存派生値snapshotの変更は、この枠数フィールドの追加だけ。
- 4脚それぞれの特注値、左右、子パーツの所有関係をJSON・Web内`.chum5`往復で検証する。
  XMLには個別GUIDの4脚とLeft/Right各2件を保存する。
  Humanへ変更した場合も装備を削除せず、過剰分をエラー表示して集計を片側1本へ戻す。
  Centaurへの変更、1脚の削除、空き枠への追加も検証した。

検証は`test_centaur_limb_sides.py`、既存の義肢/資質テスト、追加画面のテストによる。
左右の枠数の根拠は上記のCyberware.SelectSideの`Character.LimbCount(slot) / 2`。
GUI実保存との一致、モジュラーの着脱・適合条件、全脚置換と個別脚の併用時の装備適合は残件。

## 実装済み: 部分義肢の集計境界とモジュラーコネクタの能力値継承

- 英語名のhand/foot/lower等による除外を、XMLのlimbslotに基づく集計へ変更した。
  同梱のObvious Foot、Obvious Lower Leg、Partial Cyberskullはlimbslotを持たず、
  個別能力値は保持するが全身平均・Redlinerの1肢として数えない。
- Modular Connector, Hipはlimbslot=legを持ち、接続した子義脚の能力値を継承する。
  inheritattributesを読み、正の子能力値の平均を切り捨てる。
  子がない場合は0となり、コネクタ自身の基礎3や生身の値へ置換しない。
  親より先に子が並んだ場合、継承が多段の場合も子から解決する。
- Redlinerを子義脚へ適用した後で親へ再継承する。親自身への重複加算を避け、
  親が占有する脚スロットと子義脚を二重計上しない。
  スロットのないコンテナの子は探索する。
  除外スロットの配下は、能力値平均では探索せず、Redlinerでは探索する参照元の違いも保持する。
- Centaurの4コネクタ・4子義脚について、特注AGI/STR、左右、全身平均、
  地上の義脚AGI、水泳、Redliner上限を検証した。
  能力値平均の分母は8、脚の集計は4。部分義肢の検証と合わせて基本種族の集計にも適用する。
- `.chum5`には義肢のcategory、limbslot、limbslotcount、inheritattributes、
  hasmodularmount、plugsintomodularmountを保存する。
  JSONとWeb内`.chum5`往復で個別の親子関係・能力値・移動を再現する。
  個別設定を上書きした義脚移動設定は、別の設定ファイルとして再適用して比較する。

検証は`test_centaur_modular_limbs.py`による。照合先は固定コミットの
[Cyberware.IsLimb/GetCyberlimbCount/GetAttributeTotalValue/Save/Load](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Equipment/Cyberware.cs)、
[CharacterAttrib.CalculatedTotalValue](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Attributes/Attribute.Core.cs)、
[Character.CalculatedMovement](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Characters/Character.cs)。

この変更は既存のparent_idで接続を表した場合の算術と保存に限定する。
接続状態による改善効果の制御は下記範囲を実装した。
モジュラー義肢全体の対応完了とは扱わない。

## 実装済み: モジュラー接続状態による改善効果の有効・無効

- 固定版のIsModularCurrentlyEquippedに合わせ、mountstoを持つ部品は単独では無効、
  祖先のmodularmountで有効、祖先のmountstoで再び無効として親から最上位まで判定する。
  同じ祖先に両タグがある場合はmountstoを優先する。子が先に並んでも同じ結果となり、
  循環参照では探索を打ち切って効果を無効にする。
- 外したモジュラー義肢とその子パーツの通常・無線・ペア改善効果を計算から外す。
  技能選択による技能値・Accuracyも適用しない。購入記録、価格、子パーツ、
  無線設定と技能選択の保存値を保持し、再接続時に再導出する。
- 全身能力値平均は無効な枝を探索しない。
  GetCyberlimbCountには接続状態の判定がないため、RedlinerのXMLスロット集計へは
  この除外を加えない。個別義肢の能力値と地上義脚移動も既存の計算を維持する。
- derivedのモジュラー部品とその配下にmodular_equippedを出力する。
  通常の装備の派生値形式は変更しない。接続状態を独立した購入フィールドにはせず、
  parent_idとカタログから再導出する。
- Centaurの4脚中1脚の取外し・再接続で、身体ダメージ欄の+1消失・復帰、
  コネクタの子能力値の消失・復帰、価格と既存エッセンス合計の保持を検証した。
  JSONとWeb内.chum5往復で外した義脚の子パーツと所有関係も保持する。
  膝コネクタの下腿ペア、複数段の接続、無線ペア、技能選択の効果も検証する。

検証は`test_modular_equipment.py`による。照合先は固定コミットの
[Cyberware.IsModularCurrentlyEquipped/ChangeModularEquip/RefreshWirelessBonuses](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Equipment/Cyberware.cs)と
[CharacterAttrib.CalculatedTotalValue](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Attributes/Attribute.Core.cs)。
効果経路だけの合成fixtureは装備適合の証明に使わない。

マウント種別・接続数・グレードの直接接続検証は下記範囲を実装した。
blocksmountsの占有検証は下記範囲を実装した。
着脱UIと格納gear・内蔵武器の接続状態への対応は後述の範囲を実装した。
汎用のエッセンス課金規則、RF/CF本文・エラッタ、GUI実保存は残件。
今回の実データのモジュラー脚は元々ess=0であり、接続状態によるエッセンスの一括免除は導入しない。

## 実装済み: モジュラーの直接接続先・接続数・グレードの検証

- 固定版のPlugsIntoTargetCyberwareとConstructModularCyberlimbListの接続先条件から、
  子のmountstoと直接の親のmodularmountの一致、同じグレード、
  1コネクタにつき同種マウントへ接続できる部品1件の条件を検証する。
  子のmountstoが空の通常パーツ・特注パーツはマウントの占有件数に含めない。
- 接続数は親install IDごとに数える。Centaurの同名・同側の2コネクタをまとめず、
  4コネクタに1脚ずつを接続する構成を許容する。
  容量制限設定が無効でもモジュラー接続数の制約は検証する。
- 不一致・過剰接続はderived.errorsへ構造化したエラーを出し、作成チェックで日英表示する。
  購入記録・価格・親子指定を保持し、勝手な削除・取外し・グレード変更は行わない。
  エラー時に接続したままの部品の効果を自動で停止する処理は加えない。
- 親なしのモジュラー部品は取外し状態として保持し、接続先不足のエラーを出さない。
  多段の接続では直接の親で検証し、取外した義脚の配下でも不正な接続を報告する。
  左右は既存のensure_sidesが親から継承する。保存前の矛盾したside指定を別途検証する変更は含まない。
- Patch、再計算、JSON、Web内.chum5往復で、正常な四脚の接続と過剰接続の検出を検証した。
  取外しによる過剰接続の解消、異種マウント、通常義脚への誤接続、グレード変更も検証する。

検証は`test_modular_mount_validation.py`による。照合先は固定コミットの
[Cyberware.PlugsIntoTargetCyberware](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Equipment/Cyberware.cs)と
[Character.ConstructModularCyberlimbList](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Characters/Character.cs)。
これは保存済みの直接接続の検証であり、選択UIの候補絞込みや
コネクタ自体の装着条件・車両ホストへ直接接続した場合の適合を網羅するものではない。

## 実装済み: blocksmountsによる部位占有の検証

- カタログのblocksmountsを配列で読み、.chum5にも元のカンマ区切りで保存する。
  モジュラー脚に存在しないタグを名前から補完しない。
- wrist/elbow/shoulderを腕、ankle/knee/hipを脚の枠へ対応させ、
  コネクタとその位置を占有する装備の合計が枠数を超えたときにエラーを出す。
  Centaurは脚4枠・片側2枠、Humanは脚2枠・片側1枠として検証する。
  limbslotcount=allは当該部位の全枠数を占有する。
- 通常の子パーツは根の義肢と同じ部位として集約し、同じblockタグを二重に数えない。
  コネクタ自身のblockタグは自分の枠の予約として扱い、自分自身とは衝突させない。
  mountstoを持つモジュラー部品の枝をまたいでbodyの占有へ加算しない。
  取外したモジュラー脚とその配下はbodyの部位枠を占有しない。
- 個別義肢の内部では、兄弟部品とその通常の子を同じ部位の1枠で検証する。
  例として同じ義脚内の膝・足首コネクタのblock競合を検出する。
  複数肢シャーシ（limbslotcount>1、all相当のslot）の内部は1枠と推測せず、この局所検証を省く。
  その内部の位置・接続適合は別途残件とする。
- 不正な構成は作成チェックで日英表示し、装備・購入費・接続記録を保持する。
  容量制限設定とは独立して検証する。車両内の装備はキャラクターの部位枠から除外する。
- 片側枠の種族差、左右の分離、四脚コネクタの正常構成、全脚置換と追加コネクタの競合、
  多段の子パーツ、取外し、JSONとWeb内.chum5往復によるエラー・費用の保持を検証した。
  全脚置換fixtureは算術経路の検証であり、Centaurの装備適合を認める根拠にはしない。

検証は`test_modular_mount_blocks.py`による。対応部位と枠数の根拠は固定コミットの
[Cyberware.MountToLimbType/SelectSide/Save](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Equipment/Cyberware.cs)。
通常の子の集約とモジュラー枝の境界は
[CharacterCreateのCyberware選択処理](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Forms/Character%20Forms/CharacterCreate.cs)と
[SelectCyberware](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Forms/Selection%20Forms/SelectCyberware.cs)
のblocksmounts/modularmount集計・候補除外を参照した。
Webでは保存済みの構成を枠超過として検証する。Chummerの購入順序に依存する候補一覧や
強制side選択の完全再現は対象外。未知のマウント名、複数肢シャーシ内部の位置、
車両の部位占有、着脱UI、RF/CF本文・エラッタとGUI実保存は引き続き残件。

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

生得MAGの残る権限・burnout仕様、義肢の装備適合、正典実機での`.chum5`往復は未完了であり、
Centaurを作成画面の候補へ公開する段階には達していない。

## 実装済み: モジュラー義肢の着脱UI

- サイバーウェア画面で、購入済みモジュラー義肢の接続先を選択・変更し、切り離せる。
  種別・グレード・左右が合い、別の対応義肢が占有していないキャラクター所有のコネクタを候補にする。
  左右未指定の義肢は接続先の左右を引き継ぐ既存エンジンに委ねる。
  自分自身・子孫・循環・車両を根に持つ装備は候補から除外する。
- 同名コネクタは左右と一覧内の番号で区別する。番号は表示用で、保存と接続には既存IDを使う。
  現在の接続先は候補として維持し、条件不一致なら選択不能の現在値として表示する。
  条件不一致でも切り離せる。同梱・資質付与の義肢は編集しない。
- 操作は対象購入行のparent_idだけを更新する。ID・価格・グレード・無線設定・子装備・
  技能選択・保持gear・武器アクセサリの記録を削除しない。接続後の改善効果は既存エンジンが再計算する。
  派生した接続状態を画面に表示し、モジュラー義肢内の装備も再帰的に表示する。
  接続中の義肢にも内部装備を選んで追加でき、親IDにはコネクタではなく対象義肢のIDを使う。
  簡易表示では既存仕様どおり操作欄を隠す。
- 公開カタログへmodular_mount/mounts_toを渡し、実データのHip/Full Legで検証した。
  UIテストは同名複数・着脱・移動・切り離し状態・不正な既存接続・循環・子孫・左右未指定・同梱を扱う。
  親ID更新後のJSON/`.chum5`往復・改善効果の再計算は既存のバックエンド着脱テストと合わせて検証する。

接続条件は固定版Character.ConstructModularCyberlimbListの同期側を照合した。
現在の接続先を表示に残すことと循環防止はWeb側の操作上の対応。
候補選択は直接接続の適合判定であり、全身のblocksmounts・容量・種族要件等は既存エンジンの通知で検証する。
保持gear・内蔵武器の接続状態への対応は後述の範囲を実装済み。
車両への接続、多肢シャーシ内部の位置指定、RF/CF本文・エラッタ・正典GUIでの一致は引き続き未確認。Centaurの候補公開条件は変更しない。

## 実装済み: 切り離した義肢の保持gear・内蔵武器

- モジュラー義肢と子義肢の派生接続状態を、そのwareが保持するgearと任意深さの子gearへ伝播する。
  保存行の順番に依存せず、切り離し中は通常bonusを改善効果へ加えず、技能ソフトの供給元にも使わない。
  再接続すると既存の記録から再計算する。gearの所有行・親ID・価格・equipped設定は変更しない。
  通常の携帯gearには新しい派生フィールドを追加しない。
- 内蔵武器は所有一覧と派生weaponsに残し、接続状態を付ける。装備編集画面で切り離しを表示する。
  Webシート・ココフォリア・ユドナリウムの攻撃候補は、切り離し状態の武器を除く。
  Foundry向けJSONでは装備行を残し、該当gearと内蔵武器のequippedをFalseにする。
- 実カタログのモジュラー脚、Foot Blade、Custom Item内のRespirator・Activesoftを用い、
  着脱・再接続、子gearの順序、通常gearへの非干渉、費用保持、JSON/`.chum5`の二重往復を検証した。
  Custom Itemの内容物は階層伝播を検証するfixtureであり、Centaur固有の装備適合を確認したものではない。

gearの改善効果切り替えは固定版Cyberware.ChangeModularEquipがGearChildrenへ
ChangeEquippedStatusを呼び、子義肢へ再帰する処理を照合した。
Webでは保存設定を変更せず派生接続状態を適用する。内蔵武器の攻撃候補からの除外は
この接続状態をWebの出力へ反映する実装判断であり、Chummer GUIとの一致を確認したものではない。
使用済み薬物のactive効果は保管場所とは別の既存状態として扱い、この着脱では変更しない。
内蔵武器のアクセサリ・弾薬のWeb内保存経路は後述の範囲を実装済み。
車両接続、多肢シャーシ内の位置指定、正典GUIでの一致は引き続き別項目。Centaurの候補公開条件は変更しない。

## 実装済み: 内蔵武器のアクセサリ・弾薬の所有と保存

- cyberware/biowareのadd_weapon_idから、義肢のインストールIDに対応する武器定義を取得する。
  アクセサリの親検証と同梱アクセサリの生成に使い、通常購入武器でないことを理由に削除しない。
  内蔵スマートガン等の同梱品は無料で生成し、再計算や読込で重複させない。
  弾薬の適合判定には内蔵武器の定義を使い、ware自身のallowgearも引き続き認める。
  武器のammo_gearには適合する弾薬だけを載せる。
- 選択弾薬のIDは所有元のware行へ保存する。画面の装填・取り外しもその行を更新する。
  通常武器や他の義肢へ変更を広げず、切り離し中も所有・数量・選択を保持する。
  攻撃候補から除く既存の派生接続状態は維持し、再接続時に同じ付属品を使う。
- `.chum5`では内蔵武器を生成元parentid付きで書き、義肢のweaponguidと武器guidを対応させる。
  読込時はparentidまたはweaponguidで所有義肢の新IDへ付属品を結び直す。
  sourceidが義肢のadd_weapon_idに一致することも確認し、独立した購入武器として重複登録しない。
  弾薬は武器配下のgears、選択はloadedammoguidとして保存するWeb独自拡張。
  gearのguidから新しいIDへ選択を付け直す。通常購入武器も同じ保存経路を使う。
  弾薬以外のware保持gearは従来のware配下へ保存する。
- 実カタログのHeavy Pistol、同梱Smartgun System、Personalized Grip、Regular Ammo/APDSを使い、
  同名2挺の所有分離、反復着脱、費用・能力値・数量の保持、JSONと二重の`.chum5`往復、
  再接続、親の削除、不適合gearの拒否を検証した。画面操作はcyberware/biowareの両方を検証する。

固定版Cyberware.Saveのweaponguid、Weapon.Saveのguid/parentid/accessoriesを照合した。
弾薬のWeb独自拡張はChummer本体のclips/activeammoslotの保存を再現していない。
正典GUIでの弾薬管理・保存往復、車両への接続と所有移動、多肢シャーシ内部の位置指定は未確認。
Centaurの候補公開条件は変更しない。

## 実装済み: 車両内モジュラー義肢の保持gearと本人の効果の分離

- 車両改造を祖先に持つwareのIDを、既存の車両ホスト検証から取得する。
  そのwareが保持するgearと任意深さの子gearへvehicle_hostedを派生させる。
  通常bonusと技能ソフトを本人の効果へ加えない。保存行の順序には依存しない。
  この状態はmodular_equippedと別に扱い、車両のコネクタへ接続中の義肢を切り離し扱いにしない。
  gearの所有行・数量・価格・equipped設定、内蔵武器のアクセサリは維持する。
- 実カタログのDrone Arm、Modular Connector, Wrist、Obvious Hand, Modularを使用し、
  身体側コネクタから車両側への移動、切り離し、身体への再接続をバックエンドで検証した。
  車両内義肢のエッセンスは既存処理でゼロになり、身体へ戻したときの値も復元する。
  Custom Item内のRespirator・Activesoftの効果分離、通常gearへの非干渉、付属品と費用保持、
  JSONと二重の`.chum5`往復、車両内コネクタのグレード・占有数検証を確認した。

車両内義肢自体を本人の改善効果から除く既存処理と、保持gearの扱いを揃えるWeb側の修正。
固定版Character.ConstructModularCyberlimbListが車両改造内のコネクタも列挙することは照合したが、
正典GUIでの移動・保存一致を確認したものではない。
車両内の接続候補・再帰表示・操作と、内蔵武器の出力を所有先へ分ける処理は後述の範囲を実装済み。
車両内gearの効果を車両側へ計算する処理、使用済み薬物のactive状態は変更しない。
Centaurの候補公開条件は変更しない。

## 実装済み: 車両内コネクタへの接続UIと内蔵武器の所有先

- 身体側・車両側の接続操作で、既存のcyberware親IDだけを変更する。
  派生vehicles/drones内のsubsystemsを持つ改造を外部ルートとして認め、
  車両名・改造名と行番号でコネクタを区別する。未知のルート・循環・子孫は候補にしない。
  型・グレード・占有数の既存条件を保ち、車両側では左右を厳密に一致させる。
  左右未指定のplugを身体側へ接続できる従来条件は維持する。
- 車両改造内の義肢ツリーを任意深さまで表示し、モジュラー義肢の切り離し・
  身体への再接続・他車両への移動を同じ選択欄で扱う。保持gearも表示する。
  内部装備の追加先はコネクタではなく選択した子義肢とし、その義肢のグレードを引き継ぐ。
  vehicleCompactの簡易表示では既存どおり操作欄を隠す。
- 検証済み車両改造へ至るwareの祖先をたどり、内蔵武器にvehicle_idを派生させる。
  独立した武器マウントのmounted_onとは区別し、保存行へ新しい所有IDを追加しない。
  本人のシート・テキストシート・ココフォリア・ユドナリウムの攻撃一覧から車両内蔵武器を除き、
  シートとテキストシートの車両欄、ユドナリウムの車両コマへ装備名を残す。
  Foundryでは内蔵武器・アクセサリ・保持gearをその車両へ出力し、身体へ戻すと本人へ戻す。
  装備編集画面には所有車両を表示し、付属品の編集は継続できる。
- 義肢が所有する武器を独立した車両武器マウントへ二重に取り付けないよう、
  UI候補とバックエンド検証の双方で除外する。
  実カタログの義手・コネクタ・ドローンによる所有先変更と`.chum5`往復を検証し、
  画面では接続先ラベル・親IDのみの更新・車両内再帰表示・内部装備の追加・左右条件を確認した。

接続候補の車両側の左右条件は固定版Character.ConstructModularCyberlimbListの同期処理を照合した。
車両内蔵武器の本人攻撃一覧からの除外と所有先表示はWeb側の実装判断であり、GUI一致は未確認。
車両内の義肢武器には固定版Chummerの判定処理があるが、操作方法の選択と正典本文の照合が
未完了のため、自動でGunnery判定を追加しない。確認範囲は下記を参照する。
既存の独立した車両武器マウントの判定は維持する。武器マウント内の改造を接続先にする構造、
多肢シャーシ内部の位置指定、車両内gearの効果計算は引き続き別項目。
Centaurの候補公開条件は変更しない。

### 調査: 車両内の義肢武器の技能・判定

固定コミットの[Weapon.GetDicePool](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Equipment/Weapon.cs#L9443)と
[RelevantAutosoft](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Equipment/Weapon.cs#L4559)を照合した。
専用の新技能ではなく、既存技能・オートソフトに操作方法別の分岐が存在する。
以下はソフトの実装確認であり、正典の裁定を確定するものではない。

| Chummerの操作モード | 確認できた基本処理（追加修正を除く） |
| --- | --- |
| DogBrain | Pilot + 武器に対応するオートソフト。R5有効時の近接武器はMelee Autosoft、それ以外はTargeting Autosoft。 |
| RemoteOperated | GunneryをLOGで判定する。 |
| ManualOperation / GunneryCommandDevice | Gunneryの通常のプールを使う。 |
| Skill | 武器に対応する通常技能。車両内のcyberwareを親IDでたどり、対応する義肢能力値があれば置き換える。 |

DogBrainにはDrone Arm用の追加処理がある。武器技能の対応能力値がAGIで、
所属改造の`UseOwnAttributesForWeapon`がtrue、武器の親cyberwareが解決できる場合に、
親義肢からAGIが非ゼロの祖先を探し、Pilotの代わりに用いる。条件を満たさなければPilotのまま。
この処理のコメントはRigger 5.0 p.125、近接用オートソフトのコメントはp.127を参照する。
同梱vehicles.xmlのDrone Armにも`useownattributesforweapon=True`とR5 p.125、
gear.xmlの`[Weapon] Melee Autosoft`にもR5 p.127がある。
これらの参照ページの正典本文・エラッタと、ジャンプイン等の操作方法との対応は未照合。

「車内に保管しているだけの義肢」「腕として使用可能な接続」「独立した武器マウント」を
同一視しない。現在のWebの`vehicle_id`は所有先の導出であり、操作方法や使用可能性の確定ではない。
したがって、車両所有という条件だけで攻撃式を追加せず、専用技能を新設もしない。

## 次の実装と公開条件

1. 正典で生得MAGとTalent・購入・成長・MAG0時の扱いを確認する。
   四脚の個別義肢指定/保存とRedlinerは上記範囲を実装済み。
   生活費のRF本文と装備適合、実`.chum5`も照合する。
   未確定の数式を推測で導入しない。
2. 生得資質・パワー・蹴りの導出は上記の範囲を実装済み。
   `.chum5`の由来付き資質・パワー・自然武器の保存とWeb内往復も実装済み。
   正典実機で保存したファイルとの往復は引き続き確認する。
3. 蹴りの素手攻撃修正・STR変動・他の自然武器との組合せは上記範囲を実装・検証済み。
   RF本文・エラッタ・実機での一致を引き続き確認する。
4. 生得MAG1の保持、Patch・特殊点・カルマ・キャリアbaseline・既存エッセンス損失への接続は上記範囲を実装済み。
   RF本文・エラッタ・実機fixtureを確認し、イニシエーション、共鳴Talentとの共存、burnout、
   MAG0時の生得能力の利用条件を確定してから残る権限を実装する。
5. 地上/水泳/飛行の計算、追加脚の平均への接続、生活費と支出内訳は上記の範囲を検証済み。
   四脚の個別義肢指定/保存とRedlinerも上記範囲を実装済み。
   部分義肢の集計境界・モジュラーコネクタの能力値継承は上記範囲を検証済み。
   接続状態による通常・無線・ペア・技能選択の改善効果の制御も上記範囲を実装済み。
   直接接続のマウント種別・接続数・グレードの検証も上記範囲を実装済み。
   blocksmountsの部位占有・個別義肢内部の競合検証も上記範囲を実装済み。
   キャラクター所有コネクタへの着脱UIも上記範囲を実装済み。
   車両接続・装備適合、正典実機での一致を引き続き確認する。
6. JSON/Patch/共有/IndexedDB/undo/redo/`.chum5`、キャリア移行、シート出力で往復確認する。
   基本5種族・亜種・感染者・SURGEへの回帰を確認する。
7. 以上を満たしてからRF条件付きで候補を公開する。
   Priority/SumToTenはA/B/Cのみ、特殊点6/3/0、追加25 karma。
   Karma式は種族60 karmaで追加25を重ねない。
   RF無効時は新規候補から除外し、既存Centaurは保持して出典警告を示す。

Naga/Pixie/Sasquatch、シェイプシフター、AIの候補公開は別の実装・検証単位とする。
