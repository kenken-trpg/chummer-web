# A.I. 作成対応の計画と開発状況

開始日: 2026-10-17。対象は metatypes.xml の category が `Metasapient` の A.I. と、
そのメタバリアント E-Ghost・Xenosapient・Protosapient（出典 DT p.135、E-Ghost は p.161）。
基準データは同梱NOTICEのchummer5a固定コミット
`d7e94f6a090f267362757675d05bbe4d7543c217`。
照合先は同コミットのChummerのソース。Chummer.Tests/TestFilesの実セーブ34件にA.I.のPCは無い
（BLUEとYetiにあるのはコンタクトの記述だけ）ので、シェイプシフターのような実セーブとの
一致確認はできない。この文書は計画と実装状況を記録し、ルール本文（DT）の照合結果とは区別する。
DT本文は未照合。

## データの形

- A.I.と3つのメタバリアントは、どれも`<karma>180</karma>`と`<halveattributepoints />`を持つ。
  肉体能力値（BOD・AGI・REA・STR）は最小・最大とも0。DEPは1〜6。ESSは0〜6。
  メンタル能力値の範囲は種類ごとに違う（A.I.はLOG 2〜7・INT 1〜5、XenosapientはLOG 3〜8 ほか）。
  シェイプシフターと違い、メタバリアントは自分の能力値の範囲を持つ。
- `<bonus>`は4つとも同じで、`enableattribute DEP`と`enabletab advanced programs`。
- 生得資質は種類ごとに違う。
  - A.I.：Codeslinger・Photographic Memory・Speed Reading／Real World Naiveté
  - E-Ghost：Hello World!×3・Lucky・Photographic Memory・Speed Reading／Social Stress
  - Xenosapient：Designer・Multiprocessing・Photographic Memory・Speed Reading・Real World Naiveté／Uncouth・Driven
  - Protosapient：Home Ground・Inherent Program・Munge・Redundancy・Real World Naiveté／Uncouth・Uneducated・Driven

  Xenosapient・ProtosapientのReal World Naivetéは`<positive>`側に書かれている（否定的資質なのに）。
- `<qualityrestriction>`（4つとも同じ。肯定的63件・否定的43件）は**取れる資質の許可リスト**。
  Chummerの`SelectQuality`は、この一覧に無い資質を候補から外す。metatypes.xmlでこれを持つのはA.I.系だけ。
- Priority表ではHeritage A（特殊点4）・B（特殊点2）・C（特殊点0）に入る。追加カルマは0。
- Talent表の各段に「A.I. - n Depth」（A 6／B 4／C 3／D 2／E 1）がある。`<required>`は`metatype A.I.`。
  ほかのTalentはすべて`<forbidden>metatype A.I.`（MundaneとTechnomancerを含む。Technomancerは
  `<required>metatypecategory Metahuman`）。A.I.はPriorityでは必ずA.I.のTalentを取ることになる。
  A〜CのA.I. Talentには技能（skilltype `matrix`）の無料割り当てが付く（A 5×2、B 4×2、C 2×1）。
- A.I.のプログラムは`programs.xml`にある（Advanced Programs 16件ほか、計87件）。このファイルはまだ取得していない。
  作成カルマは`settings.xml`の`karmanewaiprogram` 5・`karmanewaiadvancedprogram` 8。

## Chummerの処理（固定版ソースで確認したもの）

- **能力値ポイントの半減**：[SelectMetatypePriority](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Forms/Character%20Creation%20Forms/SelectMetatypePriority.cs)
  が、`halveattributepoints`を持つ種族ならAttributes優先度の値を`/= 2`（切り捨て）する。
  PriorityとSumToTenはこのフォームを通る。Karma方式には能力値ポイントが無いので関係しない。
- **DEPの開始値**：同フォームでTalentの`<depth>`を開始値にする（Talentに無ければ1）。
  上限は`<maxdepth>`、なければ`depmax`と開始値の大きい方。
- **肉体能力値**：DEPが有効なら、BOD・AGI・REA・STR・MAGの範囲を0にする（同フォーム、Spriteと同じ扱い）。
- **A.I.の判定**：`Character.IsAI`は「DEPが有効、かつBODのメタタイプ上限が0」。
- **EDGの上限**：A.I.なら、EDGのメタタイプ上限はDEPの合計値になる（`Attribute.Core.cs`）。
- **DEPは特殊能力値**：`AttributeSection`は、有効ならDEPを特殊能力値の一覧に加える。
  最小値の処理ではMAG・RESと同じ扱いで、0まで下がれる。
- **ホームノード**（`Character.HomeNode`）：A.I.のマトリックスイニシアティブ（常に4D6、
  ホームノードのData Processingを加える）、状態モニター、リミットを分岐させる。`IsAI`は`Character.cs`だけで181箇所。

## 開始時のこのアプリ

- 作成候補（`data_loader/__init__.py`の`playable`）にA.I.が無かった。
- `engine/constants.py`の`SKIP_TALENTS = {"A.I."}`で、Talentの選択肢から外していた。
- `halveattributepoints`・DEP・`advanced programs`・`qualityrestriction`を読んでいなかった。
- Talentの`<forbidden>`・`<required>`を読んでおらず、ケンタウロスやシェイプシフターも
  Technomancerを選べた。

## 実装済み: 作成時の計算（段階1、PR #602）

- 全メタタイプの`dep*`を読む（範囲0〜0は「持たない」）。`enableattribute DEP`で有効になり、
  開始値はTalentの深度（Karma方式では1）。特殊ポイントとカルマで上げる。
- Priority・SumToTenで、Attributes優先度の値を半分（切り捨て）にする。
- A.I.のEDG上限はDEPの合計値。Luckyなどの上限ボーナスはその上に乗る。
- Talentの`<forbidden>`・`<required>`を読む。取れないTalentはエラー
  （`engine.priority.talentNotAllowed`）。メタタイプを変えると取れるTalentに切り替える。
  Karma方式にはTalentの優先度が無いので、A.I.がMundaneでもエラーにしない。
- `qualityrestriction`に無い資質は`engine.qualities.forbidden`。
- 生得資質の肯定・否定は、Chummerと同じく qualities.xml の category から取る。
  `<positive>`側に書かれたReal World Naivetéも否定的資質として数える。
- 同じ生得資質が複数行あればその数だけ付ける（E-GhostのHello World!×3。
  GnomeのArcane Arresterも2つになり、呪文抵抗が4になった）。
- `.chum5`では、DEPのTalent由来の開始値をChummerの最小値として書く（MAG・RESと同じ）。
- 検証：`backend/tests/test_ai_chargen.py`。`make reconcile`（34件）の出力はmainと同一。

## 実装済み: 作成画面（段階2）

- 作成候補とHeritage A〜Cに、A.I.と3つのメタバリアントを出す。DTが無効なら出さない。
- Talentの選択肢を、選んだメタタイプが取れるものに絞る（`lib/character/metatype-limits.ts`）。
  Priority表でTalentの段を変えたときの既定値も同じ規則で選ぶ（A.I.ならEでもA.I.）。
- 能力値タブ・サイドバー・シート・テキスト出力でDEPを出す。能力値タブでは、範囲0〜0の
  肉体能力値の行を出さない（シートにはChummerと同じく0として出る）。
- 資質の選択肢を`qualityrestriction`で絞る。
- 訳語：Depth・A.I.・3つのメタバリアントは、用語集の表2と補足ルールブックの方針に従い英語のまま。
  Talentの表記は「A.I. - Depth 6」。
- 検証：e2e `ai-creation.spec.ts`（Priority・SumToTen・Karma）、各タブの単体テスト。

## 実装済み: プログラム（段階3）

固定版の[CharacterCreate](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Forms/Character%20Forms/CharacterCreate.cs)
（`CalculateBP`のプログラムの部分）、[SelectAIProgram](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Forms/Selection%20Forms/SelectAIProgram.cs)、
`AddImprovementCollection.selectinherentaiprogram`、`AIProgram.Save`に合わせた。

- `programs.xml`を取得対象に加え、`catalog()["ai_programs"]`として読む（71件、うちAdvanced Programs 16件）。
  デッキで動かすギアの同名プログラム（`gear.xml`）とは別物。
- 値段：1つにつき`<karmanewaiprogram>`（5）、Advanced Programsは`<karmanewaiadvancedprogram>`（8）。
  Talentに`<ainormalprogramlimit>`・`<aiadvancedprogramlimit>`を持つものが無いので、無料枠は無い。
  キャリアでも同じ値段（CharacterCareerの追加時の支払い）なので、作成時もキャリアも合計を足す。
  設定ファイルの2つの値を読む。カルマの内訳は「A.I. のプログラム」の1行。
- 前提：`<required><oneof><program>`のどれかを、すでに持っていること（SelectionSharedの`program`）。
  Chummerは追加するときだけ確かめるので、作成中だけエラーにする（資質と同じ）。
- オートソフトなど`selecttext`・`selectskill`を持つものは、対象を文字で入れる。空なら警告。
- Inherent Program：Common ProgramsかHacking Programsから1つ選ぶ（資質のExtra）。
  そのプログラムは無料で、削除できない。Protosapientの生得資質も同じ。
  `selectsprite`と同じく、選択肢はcatalogで付ける（付与用の資質のコピーにも付ける）。
- メタタイプが`advanced programs`のタブを有効にしない（A.I.でない）キャラクターは、プログラムを持たない。
- `.chum5`：`<aiprograms>`を`AIProgram.Save`と同じ項目で書く。Inherent Programの分は
  `candelete` Falseで書き、読み込みでは資質のExtraから作り直す（二重に請求しないため）。
  資質とプログラムは`AIProgram`のimprovement（`improvedname`がプログラムの`guid`、
  `sourcename`が資質の`guid`）で結ぶので、Chummerで資質を外すとプログラムも消える。
  あわせて、メタタイプが付ける資質のExtra（Inherent Programの選択、Codeslingerのアクション）を
  書き出し・読み込みするようにした。これまでは書かずに捨てていた。
- 画面：「プログラム」タブ（A.I.のみ）。カテゴリーで絞り、前提の無いものは追加できない。
  シートのマトリックスの節とテキスト出力に一覧を出す。
- 検証：`backend/tests/test_ai_programs.py`、`AIProgramsTab`の単体テスト、e2e `ai-programs.spec.ts`。
  `make reconcile`（34件）の出力はmainと同一。

## 実装済み: エッセンスとDepth

- Chummerは、A.I.がサイバーウェアなどを買うのを止めていない（CharacterCreate・SelectCyberwareに
  `IsAI`の制限は無く、`IsAI`はホームノードの表示にだけ使われる）。このアプリも止めない。
- その代わり、DEPはMAG・RESと同じくエッセンスで下がる（`Character`の`intDepMaxReduction`）。
  DEPの分のエッセンスは`GetAllAttributeSpecificEssence`の第3の値で、全体のエッセンスに
  DEP専用の補正（データに無い）を足したもの。MAGだけを免除する補正は掛からない。
  `<esslossreducesmaximumonly>`のときは上限だけが下がる。
- EDGの上限は、下がった後のDEPになる。
- 検証：`backend/tests/test_ai_chargen.py`の「essence」の節。

## これからの段階

- **ホームノード**：コムリンク・デッキ・車両を選び、マトリックスイニシアティブ・状態モニター・
  リミットを出す。分岐が多いので、着手前にChummerのソースを読んで分割する。
- **キャリア**：作成後の扱いは未検討。

## 残る項目

1. **DT本文の照合**。上記はすべて固定版Chummerのソースとの照合で、DTの本文・エラッタとは照合していない。
2. **実セーブとの照合**。Chummer.TestsにA.I.のPCが無い。Chummerで作ったセーブが手に入れば
   `make reconcile`と同じ形で確かめる。
3. **xlsx・FVTT・Udonariumの書き出し**。プログラムを書いていない。書き出し前の確認では
   「A.I. のプログラム」が失われると表示される。
