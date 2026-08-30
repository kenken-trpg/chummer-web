# chummer-web 日本語訳 改善計画

最終更新: 2026-08-30

## 1. プロジェクト概要

Shadowrun 5th Edition の非公式キャラクター作成 Web アプリ。

| 層 | 技術 | 役割 |
|---|---|---|
| backend | FastAPI (`backend/app/`) | Chummer5a の XML データを読み込み、キャラ計算エンジン (`engine.py`) と保存/読込 API を提供 |
| frontend | Next.js + React (`frontend/`) | タブ式キャラクタービルダー UI (`components/character/tabs/*`) とシート表示 |
| data | `backend/vendor/chummer/` | `scripts/fetch_chummer_data.py` が chummer5a リポジトリ (GPL-3.0) の `master` から取得。**Git 管理外 (`.gitignore`)** |

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

`~/Downloads/` 内で競合したら**新しい方が常に真**。→ chummer 系: **2021 xslt > 2020 xslt > chumJA (2013)**。
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
  参考資料 (`~/Downloads/`) はリポジトリ非同梱のため、スクリプトを typed 引数化し**生成物を commit** する。
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

再生成: `cd backend && .venv/bin/python scripts/build_ja_glossary.py`

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

再生成: `cd backend && .venv/bin/python scripts/import_ja_from_refs.py --write`

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

**2b. 残 (未着手)**

1. **qualities / weapons / armor / cyberware / bioware / gear / mentors 残** の手動訳。
2. **critters / critterpowers / vehicles** は分量大・露出少で後回し (critters は catalog 未ロード)。

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

**4b. 残 (未着手)**

- `docs/` に翻訳方針 (カナ表記ルール、固有名は原則カナ、ルール用語は公式5版準拠、
  呪文は `漢語/カタカナ` 二重表記 等) を明文化。
- カナ揺れ (`・` 有無、長音) の検出ルール追加。

## 5. 具体的な最初の 3 ステップ

1. **フェーズ 0**: `data_loader` にオーバーレイ機構を実装＋テスト。
2. **フェーズ 1**: 2021 xslt から用語集を生成し、既存 2 ファイルとの不一致レポートを出す (読み取りのみ)。
3. **フェーズ 2-1/2-2**: chummer SR4 完全一致の自動補完＋全カテゴリ日本語化をオーバーレイに投入し、フロントで和名化を確認。

## 6. リスク・留意点

- **SR4↔SR5 差異**: chumJA はページ番号・一部ルール用語・改称アイテムが古い。固有名カナは流用可、ルール用語は要個別確認。
- **`vendor/` 非管理**: フェーズ 0 を飛ばして直接編集すると全て失われる。順序厳守。
- **上流バージョン差**: リポジトリの `ja-jp*.xml` は取得時点の chummer5a `master`。`<version>` と en-us の突き合わせで、
  上流で未訳なのか取得が古いのか切り分ける。
- **GPL-3.0**: オーバーレイも派生物。ライセンス表記を `NOTICE.txt` / README に追記。
- **`ja-jp.xml` の投資対効果**: フロントが日本語ハードコードで動いている現状、UI 文字列の全面 i18n 化は大工数。
  フェーズ 3 は「やる/やらない」を明示的に判断してから。

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
