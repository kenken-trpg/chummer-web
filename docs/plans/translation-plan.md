# chummer-web 日本語訳 改善計画

最終更新: 2026-09-05

## 1. プロジェクト概要

Shadowrun 5th Edition の非公式キャラクター作成 Web アプリ。

| 層 | 技術 | 役割 |
|---|---|---|
| backend | FastAPI (`backend/app/`) | Chummer5a の XML データを読み込み、キャラ計算エンジン (`engine.py`) と保存/読込 API を提供 |
| frontend | Next.js + React (`frontend/`) | タブ式キャラクタービルダー UI (`components/character/tabs/*`) とシート表示 |
| data | `backend/vendor/chummer/` | `scripts/fetch_chummer_data.py` が chummer5a リポジトリ (GPL-3.0) の**固定コミット** (`CHUMMER_REF`) から取得。**Git 管理外 (`.gitignore`)** |

翻訳ファイルは 2 つ (どちらも chummer5a 上流のコミュニティ翻訳):

- **`lang/ja-jp.xml`** — UI 文字列。`<string><key>…</key><text>…</text></string>` 形式。約 2,597 件。
- **`lang/ja-jp_data.xml`** — ゲームデータ名 (武器・ギア・クオリティ・呪文・クリッター等)。
  `<name>英語</name><translate>日本語</translate>` 形式、および `<category translate="日本語">英語</category>`。翻訳エントリ約 8,373 件。

## 2. 現状の実装と構造的な課題

### 2-1. データフロー

```
fetch_chummer_data.py ──> backend/vendor/chummer/lang/ja-jp*.xml
                                    │
data_loader.py:
  load_translations()  ja-jp_data.xml ─> { 英語name : 日本語 }
  load_ui_strings()    ja-jp.xml      ─> { key : 日本語 }
                                    │
catalog() ── "translations" + "ui_strings" を保持
                                    │
store.public_catalog() ── "translations" だけを返す   ← ui_strings は返していない
                                    │
frontend/app/page.tsx:  tr(name) = catalog.translations[name] || name
frontend 各タブ:  データ名は tr() 経由、UI ラベルは日本語ハードコード
```

### 2-2. 課題

1. **`ja-jp.xml` (UI 文字列) は現状ほぼ未使用。** `load_ui_strings()` は呼ばれるが `public_catalog()` が返しておらず、
   フロントも参照していない。フロントの UI ラベルは日本語ハードコード。→ 配線しない限りユーザーに影響しない。
2. **`ja-jp_data.xml` (データ名) が実際に効く場所。** 日本語化済み **約 27%** (2,320 / 8,373)。
   残り約 4,900 エントリが英語のまま `tr()` フォールバックで英語表示。
   欠落が大きいファイル: gear (~1,004)、mentors (~785)、qualities (~692)、critters (~580)、
   vehicles (~532)、weapons (~467)、cyberware (~300)、metatypes (~280)。
3. **`backend/vendor/` は Git 管理外。** `fetch_chummer_data.py` 再実行で翻訳ファイルは上流版で上書きされる。
   → 翻訳改善を直接ファイル編集でやると消える。**永続化の仕組み (オーバーレイ) が前提条件。**
4. **用語の不統一。** 例: `ja-jp.xml` の Body = `強靭力` (`靭`)、シート用語集(2021) = `強靱力` (`靱`、公式5版表記)。

## 3. 参考資料の評価

| 資料 | 日付 | 種別 | 内容 | 価値 |
|---|---|---|---|---|
| `chummer5th_シート日本語化_52160対応/xz.language.xslt` | 2021-11 | SR5 シート用語集 | `lang.X` 変数 377 件 (英語ラベル→日本語)。能力値・リミット・ダメージタイプ・呪文カテゴリ・スキルグループ・シート見出し | **用語の正典**。Chummer 系の作法。SR5・公式5版表記準拠 |
| `shadowrun5eja_ja.json` (github.com/MiyabiRouga/shadowrun5eja) | 2025 (保守中) | Foundry VTT SR5e i18n | UI・ルール用語 2,279 文字列。抽出できる term は約 414。descriptor / ルール語 / 等級 / カテゴリ | 中〜高。**用語の裏取り・空欄補完**。ただし LICENSE 記載なし → 文字列の verbatim 取り込みは要確認、参照利用に留める。アイテム名データは無し |
| `chummer5th_シート日本語化/xz.language.xslt` | 2020-03 | 同上 (旧版) | 2021 版のうち半数近くが英語のまま。競合語は全て 2021 が勝つ | ほぼ不要 |
| `chummer5th_シート日本語化/xz.language.xslt` | 2020-03 | 同上 (旧版) | 2021 版のうち半数近くが英語のまま。競合語は全て 2021 が勝つ | ほぼ不要 |
| `chumJA_20130129/lang/ja_data.xml` | 2013-01 | SR**4** データ訳 | 同型スキーマ。`<name>` 完全一致で約 379 エントリ＋カテゴリ約 13 件を即補完可能 (動物・クリッター名、一部呪文、サイバーウェア grade 派生)。武器/防具/ギアの固有名カナ表記コーパス | 中。固有名カナは安全。ルール依存語は SR5 で要検証 |
| `chumJA_20130129/lang/ja.xml` | 2013-01 | SR4 UI 訳 | `ja-jp.xml` と同型。共通キーの種テキスト | 低 (最古)。`ja-jp.xml` を配線する場合のみ |
| `chumJA_20130129/sheets/`, `*.txt` | 2013 | XSLT シート/手順書 | 本アプリはシート XSLT 未使用 | 参考外 |

### 競合解決ルール (ユーザー指示)

`$JA_REF_DIR/` (既定 `~/Downloads/`) 内で競合したら**新しい方が常に真**。→ chummer 系: **2021 xslt > 2020 xslt > chumJA (2013)**。
ただし `shadowrun5eja` は別プロジェクト (Foundry) で作法が異なるため**空欄補完のみ**、2021 xslt を上書きしない。
2 資料が食い違う語は `translation-glossary-mismatches.md` に `差異` として上げ、人が判断。
既存リポジトリ訳 (公式5版参照) は上記典拠と矛盾せず既に日本語なら維持。参考資料は「空欄の補完」と「明白な誤り/不統一の修正」に使う。

## 4. 改善計画 (フェーズ制)

### フェーズ 0 — 永続化の基盤 (前提・最優先) ✅ 完了 (2026-08-30)

直接編集が `fetch` で消える問題を解決する。

- **オーバーレイファイルを新設** (Git 管理下): `backend/data/ja_overrides/data.json` (`name→translate`) ＋ `ui.json` (`key→text`)。
  フォーマットは `backend/data/ja_overrides/README.md` に記載。
- `data_loader.py` を改修:
  - `OVERRIDE_DIR` 定数を追加。
  - `_load_ja_overrides(filename)` — JSON を読み、欠損/不正/非オブジェクト/空値は無視して `{}` を返す。
  - `load_translations()` / `load_ui_strings()` が vendored XML を読んだ後にオーバーレイで `update()` (オーバーレイ優先)。
    vendored 未取得でもオーバーレイ単体で動くよう early-return を廃止。
- `fetch_chummer_data.py` は無改修 (オーバーレイは別ディレクトリ `backend/data/`、`.gitignore` 対象外)。
- テスト `backend/tests/test_translation_overrides.py` (8 件): 空 JSON 同梱確認、欠損/不正 JSON フォールバック、
  非文字列・空値スキップ、vendored への上書きマージ、`catalog()["translations"]` への反映。全 408 件 green。

成果物: 「翻訳を足すと消えない」状態。以降のフェーズはこのオーバーレイに書く。

### フェーズ 1 — 用語集 (グロッサリ) の確定 ✅ 完了 (2026-08-30)

- `backend/scripts/build_ja_glossary.py` を新設。2021 `xz.language.xslt` から 377 変数を抽出し、
  2020 版との差分・vendored 2 ファイルとの不一致を突き合わせて 2 つの doc を再生成する。
  参考資料 (`$JA_REF_DIR/`、既定 `~/Downloads/`) はリポジトリ非同梱のため、スクリプトを typed 引数化し**生成物を commit** する。
- 成果物:
  - `docs/translation-glossary.md` — 確定用語表。和訳あり 200 件 / コード・略号 177 件。
    2020 版で英語のままだった 75 件が 2021 版で和訳済み → 2020 版は参照不要。
  - `docs/translation-glossary-mismatches.md` — Phase 2 の作業リスト。
    - A: コア能力値 12×(長/短)＋エッセンスの明示比較 → **不一致 9 件**。
      最重要は `強靭力`↔`強靱力` (公式5版は `靱`)、および能力値 Short キーが Long 形の和訳を使っている点
      (例 `String_AttributeAGIShort` = `敏捷力` → 用語集は `敏捷`)。
    - B: `ja-jp.xml` の英語原文が用語集見出しと一致するキーのうち訳が違うもの (英語残置・文脈依存差を含む)。
    - C: `ja-jp_data.xml` の name/category が用語集見出しと一致するもの (`防具`↔`装甲` 等)。
- **採用方針**: 用語集 (2021) を正とする。ただし文脈依存 (`Grade` = 階梯/等級、`Amount` = 数量/金額、
  操作呪文サブラベルの `精神`/`物理` 等) と固有名は Phase 2 で個別判断。

**フェーズ 1 拡張 ✅ (2026-08-30, フェーズ4 調査で追加)**

- 参考資料 **`shadowrun5eja_ja.json` (Foundry VTT SR5e 日本語化, 保守中)** を `build_ja_glossary.py` に統合。
  用語 term を約 414 抽出し、2021 xslt と統合 (2021 版を上書きせず空欄補完)。
- `docs/translation-glossary.md` — **統合語数 559** (2021 版 200 ＋ sr5eja 由来 359)。2 資料が食い違う語 18 件は `差異` 表示。
- `docs/translation-glossary-mismatches.md` — A のコア能力値は **不一致 0 件** (ui.json 反映後)。
  新設 **D**: sr5eja にあり `ui.json` 未収録の用語 **303 件** (descriptor・ルール語の seed 候補)。
- sr5eja は LICENSE 記載なし → 用語の**参照**に留める。verbatim 大量取り込みは避ける。

再生成: `backend/scripts/regen_ja.sh` (全成果物をまとめて再生成)

### フェーズ 2 — `ja-jp_data.xml` カバレッジ拡充 (ユーザー影響が最大) 🚧 進行中

オーバーレイ (`backend/data/ja_overrides/data.json`) に追記していく。

**2a. 機械補完 ✅ 完了 (2026-08-30)**

- `backend/scripts/import_ja_from_refs.py` を新設。curated (SR5・用語集照合済) ＋ chumJA SR4 の
  `<name>` / `<category>` 完全一致のみを、**`catalog()` が実際に使う名前・カテゴリに限定**して
  `data.json` に流し込む。`--write` なしは dry-run。再実行可。
- SR4 で語義がずれるものは除外: `Metahuman`→`ヒト` は `メタヒューマン` に curated 上書き、
  `Sioux`→`スー語` (言語) は除外、`Foci` カテゴリ (`集束具`) は SR5 公式 `フォーカス` 待ちで除外、
  `Armor` カテゴリは vendored `防具` 維持。知識カテゴリ 5 種はフロント `KNOW_CAT_JA` に合わせる。
- 結果: **200 件追加** (chumJA name 114 / chumJA category 53 / curated 33)。内訳は
  `docs/translation-import-report.md`。カテゴリは frontend が `tr(item.category)` を呼ぶ箇所で有効
  (ローダー拡張は不要だった)。
- テスト追加 (`test_translation_overrides.py`): 全値が日本語、全キーが `catalog()` に存在 (orphan 検出)、
  代表値アンカー。全 411 件 green。

再生成: `backend/scripts/regen_ja.sh`

**2b. 手動訳バッチ 🚧 進行中 (2026-08-30 一次分)**

- `import_ja_from_refs.py` の CURATED に「Phase 2b: hand translations」節を追加 (glossary 照合済)。
  一次分 **16 件**:
  - スキルグループ 10 種 (`Acting`→演技, `Close Combat`→近接戦闘, `Conjuring`→召喚, `Sorcery`→魔術,
    `Enchanting`→付術, `Tasking`→タスキング 等)。`Biotech` はギアカテゴリと名前衝突するため
    スキルグループの語義 (`医療`) を優先。
  - 残りのプレイアブル・メタバリアント 3 種 (`Hobgoblin`/`Ogre`/`Fomorian`)。
  - `Acceleration`→加速値、カテゴリ `Services`→助力 (Phase 1 Section C)。
- Phase 1 mismatch レポートの **A / B は Phase 3 送り**。理由: `String_Attribute*` は frontend が
  `ATTR_JA` 定数 (constants.ts) を使っており lang XML を見ていない。`ui.json` を今埋めても無効。
- overlay 合計 **215 件**。全 411 テスト green (orphan 検出テストにスキルグループも追加)。

**2b. 手動訳バッチ 2 ✅ (2026-08-30)**

- 高視認・高確度のシート表示エンティティのみ **48 件** を CURATED に追加 (overlay 合計 **263 件**):
  - スプライト 2、エレメンタル精霊 4 (`大気のエレメンタル` 等)、魔法アート 7 (`死霊術`/`占術`/`祓魔術`/
    `上級呪文行使` 等)、伝統の宗教名 6 (`仏教`/`ヒンドゥー教`/`ゾロアスター教` 等)、
    メンター精霊 29 (`猿`/`鯨`/`鳩`/`死`/`戦争`/`ジャーマン・シェパード`/`赤ずきん`/`観音` 等)。
  - **spells (残 170) は見送り**: 既存訳が `漢字/カタカナ` の二重表記 (`酸噴射/アシッド・ストリーム`)
    で、公式ルールブックなしに確度高く再現できない。
  - `(Alt)` / `[...]` 付きの派生名は既存訳が英語のまま放置しており、それに倣って除外。

**2b. 呪文バッチ 3 ✅ (2026-08-30)**

- `backend/scripts/ja_curated_spells.py` (`SPELLS` dict) に分離し `import_ja_from_refs.py` が取り込む。
- 既存 193 件の作法に合わせる:
  - 呪文 = `漢語訳/カタカナ音写` (`氷槍/アイス・スピア`)
  - 儀式 = 漢語のみ (`浄化円`, `擬態結界`)
  - `[...]` プレースホルダは両表記で保持、`Extended` は `広域〜/エクステンデッド・〜`
- **確度の高い 100 件のみ採用**。一般英単語＋既訳の合成パターン (Ward/Circle 系, `Increase [X]`,
  `Extended`) に限定。ブラッドマジック/ネクロ/風水/感染者系の造語 70 件は**英語フォールバックに差し戻し**
  (公式訳を検証できないため)。
- spells 訳出率: 293/363 (upstream 193 + 採用 100)。overlay 合計 **363 件**、全 411 テスト green。

**2b. 小バケツ一括 ✅ (2026-08-30)**

- `backend/scripts/ja_curated_entities.py` (`ENTITIES` dict) に分離。mentors / lifestyles /
  martial_arts / powers / echoes / complex_forms の未訳を **102 件**訳出。
  - lifestyles・martial_arts・powers は **英語ゼロに**。
  - mentors の `(Alt)`/`(SHB)` 派生 6、`MMRI`/`FAQ`/`LOTO` 略号は upstream 慣習で英語のまま。
- overlay 合計 **465 件**。全 419 テスト green (アンカー＋用語 lint に ENTITIES を追加)。

**2b. ギア (コアルールのみ) ✅ (2026-08-30)**

- weapons/armor/cyberware/gear 等の未訳 **2,228 件のうち `source == "SR5"` は 42 件だけ** と判明
  (コアのギアは vendored + overlay でほぼ訳済み。残りは全部サプリ由来)。
- SR5 コアの **38 件**を `ja_curated_entities.py` に追加 (`消音器（アレス・ライトファイア70）`、
  `ライナー - 耐火 (6)`、`フルボディアーマー：ヘルメット` 等)。純粋な型番 (AK-97, FN HAR 等) は
  兄弟エントリに倣い passthrough。
- **サプリ由来ギア ~2,200 件は方針として英語フォールバックのまま**。
- overlay 合計 **503 件**。全 419 テスト green。

**2b. qualities (コアルールのみ) ✅ (2026-08-30)**

- 未訳 681 件を `source` で分類 → **SR5 コアは 90/92 が訳済み (97%)**、RG も 16/16。
  未訳の SR5 コア 2 件 (`Infected Advanced Optional Power: Mimicry` / `Psychokinesis`) は、
  兄弟の `Infected Optional Power:` 系 40 件が upstream で全て英語 passthrough のため**同様に英語のまま**。
- 残り 679 件は全てサプリ由来 (RF 284, FA 97, KC 58, CF 46, DT 71 …)。
  **方針として英語フォールバック維持** → 本フェーズでの作業なし。

**2b. 残 (方針上ペンディング)**

- **Run Faster (RF, 291 資質)** — SURGE/Changeling・Fame・Made Man・College Education 等、卓で頻出。
  唯一「サプリだが訳す価値あり」の候補。着手は利用者判断。
- その他サプリ資質・ギア ~2,900 — 英語フォールバック維持。
- **critters / critterpowers** は catalog 未ロードで無意味、後回し。

### フェーズ 3 — `ja-jp.xml` (UI 文字列) の配線と改善 🚧 進行中

**3a. 配線 ✅ (2026-08-30)**

- `store.public_catalog()` が `ui_strings` (ja-jp.xml + `ja_overrides/ui.json` マージ済、2,596 件) を返す。
- frontend: `Catalog.ui_strings` 型を追加、`page.tsx` に `t(key, fallback?)` ヘルパ
  (`catalog.ui_strings[key] || fallback || key`) を導入し `TabPanelProps` 経由で配布。
- `ja_overrides/ui.json` を Phase 1 不一致レポートの高確度分で seed (**34 件**):
  - 能力値 Short 形 9 (`敏捷`/`反応`/`論理` 等) ＋ `String_AttributeBODLong` の `強靭力→強靱力`。
  - 文脈非依存の英語残置 24 (`String_Armor`→装甲, `String_Cost`→コスト, `ColumnHeader_Notes`→備考 等)。
  - `Grade`(階梯/等級)・`Amount`(数量/金額)・`Tradition`(様式/伝統) 等の文脈依存語は除外。
- テスト 3 件追加 (公開・キー実在・値が日本語)。全 414 テスト green。

**3b. 能力値ラベルの `t()` 移行 ✅ (2026-08-30)**

- `frontend/lib/ui-strings.ts` を新設: `makeT(catalog)` ＋
  `attrShort(key,t)` (`強靱`, `String_Attribute<KEY>Short`) ＋
  `attrName(key,t)` (`強靱力`, `String_Attribute<KEY>Long`) ＋
  `attrLabel(key,t)` = `` `${key} ${attrName(key,t)}` `` (`BOD 強靱力`)。
- 移行:
  - `CharacterSheet` の能力値欄: 英語コードのみ (`BOD`) → `attrShort` で日本語化 (`強靱`)。
  - `CharacterSidebar` / `AttrsTab` / `QualitiesTab` / `AdeptTab` / `ExtraSelect`: `ATTR_JA[key]`
    (`BOD 体`) → `attrLabel` (`BOD 強靱力` — 長形。`RES 共振力` の不揃いも解消)。
  - `constants.ts` の `ATTR_JA` 定数は削除。
  - 注: `attrLabel` のラベル列は幅が狭く `強靱力` が 2 行に折り返す。気になる場合は CSS で列幅調整。
- 全 414 backend テスト green、frontend `tsc` 既存エラーのみ (本変更起因なし)。

**3b. 残 (未着手)**

1. 他のハードコード日本語 (`KNOW_CAT_JA`、セクション見出し、各種 `<span>` ラベル) の `t()` 移行。
   多くは clean な lang キーが無く、現状の日本語で十分なため優先度低。
2. `ja-jp.xml` の英語残置 (`text == en-us` 約 1,007 件) の本格補完。

### フェーズ 4 — 品質パスと CI

**4a. 用語一貫性 lint ✅ (2026-08-30)**

- `backend/tests/test_terminology.py` (5 件)。統一した UI 用語が逆戻りしていないか機械チェック:
  - 禁止語 `属性`/`クオリティ`/`コネクト`/`メタタイプ`/`強靭`/`レゾナンス`、および `スキル`
    (`スキルソフト`/`スキルワイヤ`/`スキルジャック` は許可) を
    **frontend 全ソース (47 ファイル) ＋ `backend/app/*.py` ＋ `ja_overrides/*.json` ＋
    `ja_curated_spells.py`** から検出したら fail。
  - `data.json` の値が 2021 用語集と矛盾しないこと (例外: `Armor`→`防具`)。
- 全 419 テスト green。

**4b. 表記の統一 ✅ (2026-09-05)**

`test_terminology.py` は**語**を見ているが、**語のまわりの記号**を見ていなかった。
RG 第 1 バッチをすり抜けた 2 件はどちらも記号の問題で (全角開き括弧を半角で閉じる、
コロンの全半角)、500 行の差分の中では人間の目に留まらない。

- 新設 `backend/tests/test_ja_notation.py` (6 件)。`data.json` ＋ `ui.json` の値を走査:

  | 規約 | 根拠 (RG バッチ以前の実測) |
  |---|---|
  | 括弧は**半角** `()` | 括弧を含む 38 件中 33 件がそう |
  | コロンは**全角** `：` (前後スペースなし) | 5 件中 5 件がそう |
  | 括弧の全半角混在は禁止 | — |
  | 全角スペース禁止 | 0 件 |
  | 括弧前のスペースは**数値の等級接尾辞のみ** | `ライナー - 耐火 (6)` 18 件。英語名の ` (6)` を写している |

  **規約は好みで決めていない。RG バッチが触る前のコーパスが既にやっていたことを
  数えただけ**なので、適用は判断ではなく計数の問題になる。

- 適用した訂正は **RG バッチが持ち込んだ半角コロン 5 件のみ** (`ラピッド・トランジット：…`、
  `…ギア(RIG)：…`)。台帳経由で入れ直した。
- 全角括弧の残り 5 件 (`（合成）レザー`、`消音器（アレス・ライトファイア70/75）`、
  `高速水泳（エルフ／トロール）`、`統一マナの道（ハプスムドー）`) は
  **`FULLWIDTH_BRACKETS_KEPT` に固定して書き換えない**。コアルールブック日本語版で
  確認済みの訳であり、確認済みの語を体裁のために黙って書き換えるのは、
  未確認の語を推測で埋めるのと同じ種類の操作。人が判断したときに減らす。
  リストが実態と合わなくなったら (エントリが消えた・既に半角になった) fail する
  テストを併設してあるので、古い例外が残り続けることはない。

**4b. 残 (未着手)**

- カナ揺れ (`・` 有無、長音) の検出ルール。実測では**記号だけが違う表記ゆれ 0 件・
  同じ訳語が複数の英語名に付く衝突 0 件**だったので、現時点で守るべき実害がない。
  規模が増えてから。
- 翻訳方針の散文 (固有名は原則カナ、ルール用語は公式5版準拠、呪文は `漢語/カタカナ`
  二重表記 等) の明文化。記号の規約は上表で機械化済み。

### フェーズ 5 — 『ラン＆ガン』日本語版による検証と補完 📋 計画 (2026-09-05)

利用者が **SR5『ラン＆ガン』日本語版の物理書籍**を入手した。フェーズ 2b で
「サプリメント由来は英語フォールバック維持」としていた方針の、**RG に限った例外**。

#### 5-0. 事前調査の結果 (2026-09-05 実測)

`source == "RG"` のカタログ項目を数えたところ、**想定と実態がずれていた**。

| バケット | RG 件数 | 未訳 | 既訳の出所 |
|---|---:|---:|---|
| armor | 108 | 9 | upstream 93 / 当リポジトリ 6 |
| weapons | 98 | 7 | upstream 91 |
| gear | 77 | 4 | upstream 73 |
| martial_art_techniques | 77 | 0 | upstream 76 / 当リポジトリ 1 |
| martial_arts | 43 | 0 | upstream 43 |
| weapon_accessories | 37 | 4 | upstream 33 |
| armor_mods | 24 | 22 | upstream 2 |
| qualities | 16 | 0 | upstream 16 |
| commlinks | 3 | 0 | upstream 3 |
| **合計** | **483** | **46 (実名 36)** | **upstream 430 / 当リポジトリ 7** |

加えて RG が使うカテゴリ 37 種のうち **12 種が未訳** (`Specialty Armor`,
`High-Fashion Armor Clothing`, `Vision Enhancements`, `PI-Tac` 等)。
これらはピッカーの見出しとして出るので視認性が高い。

**したがって本フェーズの主作業は「翻訳」ではなく「検証」である。**
483 件中 430 件 (89%) は既に日本語で表示されているが、その出所は上流
`ja-jp_data.xml` のコミュニティ訳で、**公式日本語版と突き合わせた者はいない**。
例: `Too Pretty To Hit`→「可愛すぎて撃てない」、`One Trick Pony`→「一つ覚え」、
`Bartitsu`→「バリツ」。妥当に見えるが、公式訳である保証はない。

穴埋め 36 件より、この 430 件の検証のほうが価値が高い。

**進捗**: 仕組みは実装済み (5-1〜5-2、5-4〜5-5、2026-09-05)。5-3 は**穴埋めが完了**
(未訳 48 → 13、うち 9 件はカテゴリ名)。**上流訳 430 件の突き合わせは未着手。**

#### 5-1. 前提 — 先に決める 2 点 ✅

1. **ライセンス (§7 に追記が必要)。** これまでの第三者資料 (chumJA・XSLT・
   shadowrun5eja) はいずれも**ファン制作物**だった。公式日本語版は**商業出版物**で
   あり、§7 の既存の論拠 (「短い用語・固有名は創作的表現の余地が薄い」) は
   延長できるとしても、資料の性質が変わる。§7 に行を足し、明示的に立場を書く。
   - **取り込むのは項目名の対訳のみ。** ルール文・説明文・数値表・見出し文の
     転記はしない (現在のオーバーレイは `name → 訳` しか持てないので、構造上も
     そうなる)。この線は計画に書いて守る。
2. **方針の例外を文書化。** `docs/data-pipeline.md` の
   「core rulebook は訳す / supplement は英語のまま」を
   「ただし公式日本語版を持つサプリは項目名を訳す」に更新。

→ §7 に「公式日本語版 (書籍)」の行と判断を追記、`data-pipeline.md` の方針を更新済み。
**`NOTICE.txt` への出典追記は最初のバッチが入った時点で行う** (現在 `RG` が空なので、
今書くと使っていない資料をクレジットすることになる)。

#### 5-2. 作業台帳を機械生成する ✅

書籍を横に置いて 483 件を潰すので、**書籍のページ順に並んだ台帳**を出す。
カタログの各項目は `page` を持っている (例: `Aikido` = `martial_arts` p.128) ので、
これで並べれば紙をめくる順に一致する。

- `backend/scripts/make_rg_worksheet.py`
  → TSV を吐く: `status / bucket / page / english / current / from / official / note`。
  `--bucket` でバッチ単位、`--pending-only` で未決分のみ。既定の出力先はリポジトリ外
  (`$JA_REF_DIR/rg-worksheet.tsv`)。**未記入の台帳は commit しない。**
  `official` 欄の記入規則: 空 = 未着手 / `=` = `current` が書籍と一致 (そのまま採用) /
  訳語 = 日本語版の表記 (`current` と異なる場合) / `-` = 英語のまま。
  **`=` は突き合わせパスの前提**: 458 件の大半は「上流訳で合っている」はずで、同じ語を
  数百回打ち直すのは、見つける誤りより持ち込む誤りのほうが多い。`=` でも `RG` に
  収録されるので、検証済みという記録としては打ち込んだ場合と等価。
- `backend/scripts/import_rg_worksheet.py`
  → 記入済み TSV を読み `ja_curated_rg.py` を生成。既定は追記 (バッチをまたいで累積)、
  `--replace` で置換。`--write` なしは dry-run。日本語を含まない訳語・カタログに無い名前・
  「訳語と `-` の両方」は問題として報告して書き込まない。
  **形には寛容・意味には厳格** (2026-09-05 に強化)。表計算を経由すると内容と無関係に
  形が変わる (第 1 バッチの実物は `;` 区切りの `.csv`、BOM 付き、先頭にシート名の行、
  ファイル名も別) ため、区切り文字の判定・BOM 除去・ヘッダ行の探索・
  `$JA_REF_DIR` 内の最新台帳の自動選択を行う。一方、`official` 以外の列
  (`current` / `note`) に入った回答は**報告するだけで取り込まない**。
  `--accept-column current,note` を明示した時のみ取り込む。`current` を既定で
  拾うと、**未検証の上流訳を「人が書籍で確認した」記録として収録してしまう** —
  このパスが区別しようとしている当のものなので、既定では絶対に拾わない。
  なお `current` は生成時の値 (`make_rg_worksheet.current_terms()`) と比較して
  「人が上書きしたか」を判定するので、未記入行が誤検出されることはない。
- 実測: 台帳は **493 行** (名前 456 ＋ カテゴリ 37)。名前がバケットをまたぐもの
  (`Custom Fit` = armor + armor_mods 等) は 1 行に統合。
- **前提の検証 ✅ (2026-09-05)**: 日本語版のページ番号は英語版と一致する (書籍所持者の
  確認)。よって `page` 順の台帳はそのまま紙をめくる順序で使える。`--sort name` は不要。

#### 5-3. バッチ順 (視認性が高い順)

**先に穴埋めが 1 パスで済んだ** (2026-09-05)。書籍を持つ側が台帳の空欄行 48 件を
横断して埋めたため、バッチ 3・4 の未訳分と category 3 件が一度に片付き、`RG` 32 件 ＋
`RG_UNVERIFIED` 3 件 (`AK-98` / `FN MAG-5` / `HK XM30` — 書籍もラテン文字表記) が入った。
残り 13 件は判断保留 (下表の「保留」)。以降のバッチは**上流訳の突き合わせ**が主目的になる。

| # | 対象 | 件数 | 理由 |

| # | 対象 | 件数 | 理由 |
|---|---|---:|---|
| 1 | martial_arts + techniques | 120 | RG が定義するタブ 1 枚まるごと。全件が未検証の upstream 訳 |
| 2 | qualities | 16 | シート表示・サイドバーに常時出る |
| 3 | armor + armor_mods | 132 | 未訳 36 件のうち 23 件がここ。カテゴリ 12 種もここで潰す |
| 4 | weapons + weapon_accessories | 135 | |
| 5 | gear + commlinks | 80 | |

**保留 (英語表示のまま、`RG` にも `RG_UNVERIFIED` にも入れていない)**

- 実項目 4 件: `Grenade: Paint (Radioactive Tracking Dye)` (＋ `, Aerodynamic`)、
  `Ammo: Slingshot Capsule Round`、`Atomizer`。
- category 9 件: `Armor Enhancements` / `Customized Ballistic Mask` / `Gear` /
  `General` / `Improvised Weapons` / `PI-Tac` / `Rapid Transit Detailing` /
  `Tools of the Trade` / `Vision Enhancements`。category は Chummer 側の分類語で、
  書籍に対応する見出しがないものが多い。
- ~~`Silencer (PSK-3 Collapsible Heavy Pistol)`~~ 解決 (2026-09-05)。括弧内は書籍から、
  `Silencer` = `消音器` は既存オーバーレイ (`Silencer (Ares Light Fire 70)` →
  `消音器（アレス・ライトファイア70）`) に合わせ、書籍所持者の承認を得て
  `消音器(PSK-3 折り畳み式ヘビーピストル)` を収録。**訳語の一部が書籍以外を出所と
  する唯一の `RG` エントリ**なので、ここに記録しておく。

#### 5-4. 取り込みの仕組み ✅

既存の curated モジュール方式にそのまま乗る。**オーバーレイは vendored に優先し、
`import_ja_from_refs.py` の CURATED は「既に日本語でも値が違えば上書き」する**ので
(`main()` の `or existing.get(key) != val`)、上流訳の *訂正* も同じ経路で通る。

- `backend/scripts/ja_curated_rg.py`:
  ```python
  RG: dict[str, str] = {...}              # 公式日本語版で確認した訳
  RG_UNVERIFIED: tuple[str, ...] = (...)  # 書籍に該当なし / 判断保留 → 英語のまま
  ```
- `import_ja_from_refs.py` で `CURATED.update(_RG)` を **SPELLS / ENTITIES の後**に適用。
  公式版由来なので、同じ名前に上流のコミュニティ訳がある場合はこちらが勝つ。
- **確認できた訳は、上流と一致していても `RG` に載せる。** 差分だけ記録すると
  「検証した」記録が残らず、次の `CHUMMER_REF` 更新で静かに変わりうる。
  `data.json` は生成物なので件数が増える不利益はない。
- `regen_ja.sh` は無改修で通る (`import_ja_from_refs.py` 経由で入るため)。
- 経路は実証済み: 上流訳のある `Bartitsu` (`バリツ`) を台帳で別表記にすると
  `data.json` に `[curated]` として反映され、上流と一致する `Aikido` (`合気道`) も
  同時に固定される。

#### 5-5. テストとガード ✅

- `test_terminology.py::test_curated_module_values_use_unified_terminology` が
  `RG` も走査する (ENTITIES / SPELLS と同列)。
- 新設 `backend/tests/test_rg_coverage.py` (4 件) — RG 台帳の健全性:
  - 同じ名前が `RG` と `RG_UNVERIFIED` の両方に無いこと。
  - 両表のキーが全てカタログに実在すること (誤字・幽霊エントリ検出)。
  - `RG` の値が全て日本語であること (英語のままにしたいなら `RG_UNVERIFIED` へ)。
  - **`DECIDED_FLOOR` バーンダウン** — 決着済みの件数が floor を下回ったら fail、
    上回っても「floor を上げろ」と fail する。`eslint-suppressions.json` と同じ作法で、
    数字が実態から乖離できない。バッチを入れたら floor を書き換えて同じコミットに含める。
- `test_translation_overrides.py` の orphan 検出 (全キーが `catalog()` に実在) は既存のまま効く。

#### 5-6. リスク

- **上流訳の訂正は表示を変える。** 既存キャラのシートに出ている語が変わる。
  データ移行の問題はない (訳は表示時解決) が、差分は翻訳コミットとして単独に切る。
- **公式訳が存在しない項目がある。** 日本語版は英語版より収録が狭い可能性がある。
  該当なしは推測で埋めず `RG_UNVERIFIED` に入れて英語フォールバックのまま残す。
- **`(Alt)` / `[...]` 付きの派生名**はフェーズ 2b で英語のまま残す慣習にした。RG でも踏襲する。
- **作業量。** 483 件は 1 セッションでは終わらない。5-3 のバッチ単位でコミットし、
  各バッチで `regen_ja.sh` → テスト green を通す。

## 5. 具体的な最初の 3 ステップ

1. **フェーズ 0**: `data_loader` にオーバーレイ機構を実装＋テスト。
2. **フェーズ 1**: 2021 xslt から用語集を生成し、既存 2 ファイルとの不一致レポートを出す (読み取りのみ)。
3. **フェーズ 2-1/2-2**: chummer SR4 完全一致の自動補完＋全カテゴリ日本語化をオーバーレイに投入し、フロントで和名化を確認。

## 6. リスク・留意点

- **SR4↔SR5 差異**: chumJA はページ番号・一部ルール用語・改称アイテムが古い。固有名カナは流用可、ルール用語は要個別確認。
- **`vendor/` 非管理**: フェーズ 0 を飛ばして直接編集すると全て失われる。順序厳守。
- **上流バージョン差**: リポジトリの `ja-jp*.xml` は固定コミット (`CHUMMER_REF`) 時点の chummer5a。`<version>` と en-us の突き合わせで、
  上流で未訳なのか取得が古いのか切り分ける。
- **GPL-3.0**: オーバーレイも派生物。→ `NOTICE.txt` (2026-09-02) と README に出典表記を追加済み。
  第三者資料 (chumJA / 2021 XSLT / shadowrun5eja) の扱いは §7 を参照。
- **`ja-jp.xml` の投資対効果**: フロントが日本語ハードコードで動いている現状、UI 文字列の全面 i18n 化は大工数。
  フェーズ 3 は「やる/やらない」を明示的に判断してから。

## 7. ライセンス判断 (2026-09-02)

§3・フェーズ 1 拡張で留保していた第三者資料の扱いについて、公開 (Public 化) に
あたっての本プロジェクトの立場を明記する。**法的助言ではなく、権利者からの
申し出があれば見直す。** §3 の元の留保記述 (「LICENSE 記載なし → 参照のみ、
verbatim 取り込みは避ける」) は経緯として残す。

### 現状の取り込み内容

| 資料 | ライセンス | 本リポジトリでの扱い |
|---|---|---|
| chummer5a `Chummer/data` `Chummer/lang` | GPL-3.0 | ビルド時取得。`backend/vendor/` は git 非管理。本プロジェクトは派生物として GPL-3.0 |
| curated 手訳 (`ja_curated_*.py`, `import_ja_from_refs.CURATED`) | 本プロジェクト著作 | `data.json` の約 337 / 503 件 |
| chumJA (`chumJA_20130129`) の `<name>` / `<category>` 完全一致 | 表記なし | `data.json` の約 166 / 503 件。大半が固有名カナ・カテゴリ語。エントリ別の出典は `translation-import-report.md` |
| 2021 シート XSLT / shadowrun5eja | LICENSE なし | **shadowrun5eja の訳語は非収録**。`data.json` に一切入っていない。`translation-glossary.md` の `sr5eja` 列は `＝`／`≠` マーカーのみ、`translation-glossary-mismatches.md` セクション D は英語見出しのみ (2026-09-02 に verbatim 再現を除去) |
| 『シャドウラン5th ラン＆ガン』日本語版 (書籍) | 商業出版物 (全著作権留保) | **項目名の対訳のみ**を `scripts/ja_curated_rg.py` 経由で `data.json` に収録 (フェーズ 5、2026-09-05〜) |

### 判断

- **短い用語・固有名の対訳** (「アリゲーター」「弾薬」等) は個々には創作的表現の
  余地がほぼなく著作物性が薄い。chumJA 由来分はこの範囲に収まる。
- **shadowrun5eja は無ライセンス**。出荷物 (`data.json`) には元々含まれておらず、
  docs 側の verbatim 再現 (旧 `sr5eja` 列 約414・旧セクション D 約302) も
  マーカー化／英語のみに置換して除去した。glossary の `採用` 列には、2021 版に無い
  UI ラベル約 359 語が sr5eja 由来の空欄補完として残るが、いずれも短い語句で
  本プロジェクトが採用した用語として記録するもの (アプリには非搭載)。
- **公式日本語版 (書籍) について (2026-09-05 追記)。** これまでの第三者資料はいずれも
  ファン制作物だったが、フェーズ 5 で参照するのは**商業出版物**である。資料の性質が
  変わるので、線を明示的に引く:
  - **収録するのは項目名の対訳のみ** (「Aikido → 合気道」)。ルール文・説明文・
    数値表・見出し・イラストは一切転記しない。オーバーレイは構造上 `name → 訳` しか
    持てないため、機械的にもこの範囲を超えられない。
  - 個々の対訳は短い名詞句で、それ自体に創作的表現の余地はほぼない (chumJA 由来分に
    ついて上で述べた論拠がそのまま当てはまる)。**書籍の代替にはならない** — 本アプリは
    ルールを収録しておらず、遊ぶには書籍が必要である。
  - `NOTICE.txt` に出典としてクレジットする。
  - 申し出があれば `ja_curated_rg.py` を空にして `regen_ja.sh` を回すだけで
    完全に除去できる (下記の切り分けと同じ仕組み)。
- いずれの第三者資料も `NOTICE.txt` でクレジットし、ライセンス状況を明記した。
- 以上より、現状の内容で公開して差し支えない、というのが本プロジェクトの立場。

### 申し出があった場合の対応

権利者から異議があれば、`data.json` を curated 由来のみ (約 337 件) に再生成し、
`translation-glossary.md` の `採用` 列の sr5eja 空欄補完も除去する。`import_ja_from_refs.py`
の出典タグと `regen_ja.sh` でこの切り分けは機械的に可能。

## 進捗ログ

- 2026-08-30: 計画策定。
- 2026-08-30: フェーズ 0 完了。オーバーレイ機構 (`backend/data/ja_overrides/`, `data_loader.py`) ＋テスト 8 件。
- 2026-08-30: フェーズ 1 完了。`build_ja_glossary.py` ＋ `translation-glossary.md` / `translation-glossary-mismatches.md`。
- 2026-08-30: フェーズ 2a 完了。`import_ja_from_refs.py` で curated＋chumJA SR4 を 200 件 `data.json` へ。
- 2026-08-30: フェーズ 2b 一次分。スキルグループ 10・メタバリアント 3・その他 3 を追加 (計 215 件)。
- 2026-08-30: フェーズ 2b バッチ 2。メンター/精霊/伝統/魔法アート/スプライト 48 件を追加 (計 263 件)。
- 2026-08-30: フェーズ 2b バッチ 3。未訳呪文のうち確度の高い 100 件を訳出 (計 363 件)。
  サプリメント造語 70 件は英語フォールバックへ差し戻し。
- 2026-08-30: フェーズ 3a。`ui_strings` を public_catalog／frontend に配線、`ui.json` を 34 件 seed。
- 2026-08-30: フェーズ 3b。能力値ラベルを `ui-strings.ts` の `attrShort`/`attrLabel` 経由に移行、`ATTR_JA` 定数を削除。
- 2026-08-30: UI 用語統一。属性→能力値 / クオリティ→資質 / スキル→技能 / メタタイプ→メタ / コネクト→コンタクト / 魔法・レゾナンス→魔力・共振力 / 有利・不利→有利な資質・不利な資質。
- 2026-08-30: フェーズ 4a。`test_terminology.py` で用語逆戻りを機械検出 (5 件、計 419 テスト)。
- 2026-08-30: 参考資料調査。Foundry `shadowrun5eja` を用語集に統合 (統合 559 語、seed 候補 303 語)。
- 2026-08-30: フェーズ 2b 小バケツ。mentors/lifestyles/martial_arts/powers/echoes/CF を 102 件訳出 (overlay 465)。
- 2026-08-30: 呪文 descriptor/type/range/duration の日本語表示 (`frontend/lib/spell-terms.ts`)。
- 2026-08-30: SR5 コアギア 38 件訳出 (overlay 503)。サプリ由来 ~2,200 は英語フォールバック維持の方針。
- 2026-08-30: qualities 調査。SR5 コアは既に 97% 訳済み。未訳 679 は全てサプリ由来 → 方針上作業なし。
- 2026-08-30: 既存 frontend tsc エラー 10 件を修正。複合体 target / 残存カテゴリを日本語化。
- 2026-08-30: `regen_ja.sh` 新設。`data.json` ＋ glossary ＋ import-report をまとめて決定的に再生成。
  import-report を「全エントリを出典別」に変更 (`--no-reset` でも同一出力)。
- 2026-09-02: `NOTICE.txt` 追加 (データ・翻訳の出典表記) ＋ README 追記。§7 にライセンス判断を明記。
- 2026-09-02: shadowrun5eja の verbatim 再現を除去 (無ライセンス確認済み)。`build_ja_glossary.py`
  を改修し `translation-glossary.md` の `sr5eja` 列を `＝`／`≠` マーカーに、`translation-glossary-mismatches.md`
  セクション D を英語見出しのみに。`data.json` は元々 sr5eja 非収録。
  §3 の第三者資料の留保記述は経緯として保持。
- 2026-09-05: フェーズ 5 計画 (『ラン＆ガン』日本語版)。実測の結果、RG 483 件のうち未訳は
  46 件 (実名 36) にすぎず、430 件は**上流コミュニティ訳が未検証のまま表示されている**と判明。
  主作業を「穴埋め」から「公式版との突き合わせ」に置き直した。
- 2026-09-05: フェーズ 5 の仕組みを実装。`make_rg_worksheet.py` (493 行のページ順台帳) ＋
  `import_rg_worksheet.py` ＋ `ja_curated_rg.py` ＋ `test_rg_coverage.py` (`DECIDED_FLOOR`
  バーンダウン)。§7 に商業出版物を参照する場合の線引き (項目名のみ) を追記。
  **書籍を読むバッチ作業は未着手。**
- 2026-09-05: フェーズ 5 の第 1 バッチ。書籍所持者が台帳の**空欄行 48 件**を横断して
  記入。`RG` 31 件 ＋ `RG_UNVERIFIED` 3 件を収録し `DECIDED_FLOOR` を 34 に。未訳は
  48 → 14 (実項目 4・category 9・保留 1)。NOTICE.txt に日本語版書籍の出典を追記 (2-d)。
  **残る 459 件 = 上流コミュニティ訳の突き合わせで、これが本来の主作業。**
- 2026-09-05: 第 1 バッチの訂正。`コーディング`→`コーティング`、括弧を既存多数派の
  半角・スペースなしに統一 (旧来の全角 6 件は別書籍で確認済みのため据え置き)。
  日本語版のページ番号が英語版と一致することを確認し、台帳の前提注記を削除。
  保留していた `Silencer (PSK-3 …)` を承認のうえ収録し `DECIDED_FLOOR` 35、
  未訳 13 件 (実項目 4・category 9)。
