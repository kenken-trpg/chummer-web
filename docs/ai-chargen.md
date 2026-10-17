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

## このアプリの現状（開始時）

- 作成候補（`data_loader/__init__.py`の`playable`）にA.I.が無い。
- `engine/constants.py`の`SKIP_TALENTS = {"A.I."}`で、Talentの選択肢から外している。
- `halveattributepoints`・DEP・`advanced programs`・`qualityrestriction`は読んでいない。
- Talentの`<forbidden>`・`<required>`を読んでいない（`data_loader/loaders/priorities.py`）。
  このため、現在はシェイプシフターやケンタウロスもTechnomancerを選べてしまう可能性がある。段階1で確かめる。
- 特殊ポイントの消費（`_econ_priority.py`）はEDG・MAG・RESだけを数える。
- `.chum5`の書き出しには`depenabled`の枠がある（`chummer_export/build.py`）。
- 黙らせているbonusタグ`selectinherentaiprogram`（Inherent Program）は、A.I.未対応を理由に保留中。

## 段階

### 段階1: 作成時の計算（backend）

- A.I.と3つのメタバリアントを解決する。メタバリアントは自分の能力値の範囲を使う。
- Priority・SumToTenで、Attributes優先度の値を半分（切り捨て）にする。
- DEPを特殊能力値にする。開始値はTalentの深度（Karma方式では1）、上限はdepmax。
  特殊ポイントとカルマで上げられるようにする。
- A.I.のEDG上限をDEPの合計値にする。
- Talentの`<forbidden>`・`<required>`を読み、選択肢を絞る。不正な組み合わせはエラーにする。
  `SKIP_TALENTS`は外す。
- `qualityrestriction`を読み、許可リストに無い資質はエラーにする。
- `.chum5`の書き出しで、`depenabled`・DEP・メタタイプ区分を正しく書く。読み込みとの往復も確かめる。
- テストは`backend/tests/test_ai_chargen.py`。実セーブが無いので、上記のChummerの処理を
  1つずつテストにする。

### 段階2: 作成画面の候補（frontend＋catalog）

- 作成候補とHeritage行の絞り込みに、A.I.と3つのメタバリアントを出す。
  出典の本（DT）が無効なら候補に出さない。
- Talentの選択肢を、選んだ種族で絞る（A.I.ならA.I.のTalentだけ、それ以外ならA.I.のTalentを出さない）。
- 能力値タブでDEPを出し、肉体能力値（範囲0）を出さない。
- 資質の選択肢を`qualityrestriction`で絞る。
- e2e `ai-creation.spec.ts`で、Priority・SumToTen・Karmaの3方式について、候補、選択、
  能力値ポイントの半減、DEPの開始値、生得資質、再読込で保たれることを確かめる。
- `docs/chargen.md`の「メタタイプと種族」の節に、A.I.の選び方を短く書く。
- 訳語：DEP（Depth）、A.I.、3つのメタバリアントはjaの訳が無い。
  補足ルールブックの内容は英語のまま、という方針（`docs/data-pipeline.md`）に従うかを決める。

### 段階3以降（今回の範囲外）

- **プログラム**：`programs.xml`の取得とローダー、高度なプログラムのタブ、前提プログラムの検査、
  作成カルマ（5・8）。保留中の`selectinherentaiprogram`はここで実装する。
- **ホームノード**：コムリンク・デッキ・車両を選び、マトリックスイニシアティブ・状態モニター・
  リミットを出す。分岐が多いので、着手前にChummerのソースを読んで分割する。
- **キャリア**：作成後の扱いは未検討。

## 決めていないこと

1. Xenosapient・Protosapientの`<positive>`側に書かれたReal World Naivetéを、
   Chummerが肯定・否定のどちらとして数えるか（カルマの上限計算に効く）。段階1で確かめる。
2. A.I.のESS（0〜6）と、サイバーウェアなどの購入を止めるか。Chummerの作成フォームは止めていない
   ように見えるが、未確認。
3. Protosapientの生得資質Inherent Programは、選択（`selectinherentaiprogram`）が段階3まで無い。
   それまでは選択なしで付与し、未実装bonusとして表示する。
