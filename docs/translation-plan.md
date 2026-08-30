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
| `chummer5th_シート日本語化_52160対応/xz.language.xslt` | 2021-11 | SR5 シート用語集 | `lang.X` 変数 379 件 (英語ラベル→日本語)。能力値・リミット・ダメージタイプ・呪文カテゴリ・スキルグループ・シート見出し | **最優先の用語典拠**。SR5・最新・公式5版表記準拠 |
| `chummer5th_シート日本語化/xz.language.xslt` | 2020-03 | 同上 (旧版) | 2021 版のうち半数近くが英語のまま。競合語は全て 2021 が勝つ | ほぼ不要 |
| `chumJA_20130129/lang/ja_data.xml` | 2013-01 | SR**4** データ訳 | 同型スキーマ。`<name>` 完全一致で約 379 エントリ＋カテゴリ約 13 件を即補完可能 (動物・クリッター名、一部呪文、サイバーウェア grade 派生)。武器/防具/ギアの固有名カナ表記コーパス | 中。固有名カナは安全。ルール依存語は SR5 で要検証 |
| `chumJA_20130129/lang/ja.xml` | 2013-01 | SR4 UI 訳 | `ja-jp.xml` と同型。共通キーの種テキスト | 低 (最古)。`ja-jp.xml` を配線する場合のみ |
| `chumJA_20130129/sheets/`, `*.txt` | 2013 | XSLT シート/手順書 | 本アプリはシート XSLT 未使用 | 参考外 |

### 競合解決ルール (ユーザー指示)

`~/Downloads/` 内で競合したら**新しい方が常に真**。→ 優先順位: **2021 xslt > 2020 xslt > chumJA (2013)**。
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

再生成: `cd backend && .venv/bin/python scripts/build_ja_glossary.py`

### フェーズ 2 — `ja-jp_data.xml` カバレッジ拡充 (ユーザー影響が最大)

オーバーレイに追記していく。優先順位はフロントでの露出度と作業効率で決定。

1. **機械補完 (低リスク)**: chumJA SR4 との `<name>` 完全一致 379 件＋カテゴリ 13 件をスクリプトで流し込み。
   `qualities` は SR5 で改称/再定義されたものがあるためカテゴリと明白な固有名のみ自動、本体は手動レビュー。
2. **カテゴリ名の全数日本語化** (`<category translate>`)。数十件で完了し、タブ見出し/フィルタが一気に和名化。
   ※ 現状 `load_translations()` は `<category translate>` を拾わない。カテゴリを効かせるならローダー拡張が必要。
3. **高頻度エンティティを手動で** (用語集準拠): metatypes → skills → spells → qualities → weapons → armor →
   cyberware/bioware → gear → powers/mentors。
4. **critters / critterpowers / vehicles** は分量が多く露出が限定的なので後回し。動物名は chumJA から大量流用可。

各バッチ: 「英語のまま `tr()` フォールバックしているキー一覧を出力 → 用語集参照で訳 → オーバーレイ追記 → スナップショットテスト更新」。

### フェーズ 3 — `ja-jp.xml` (UI 文字列) の配線と改善

`ja-jp.xml` を活かす価値があるか判断してから着手。やるなら:

1. `public_catalog()` に `ui_strings` を追加、フロントに `t(key)` ヘルパを導入。
2. `ja-jp.xml` の英語残置 (`text == en-us` が約 1,007 件、`ja-jp` に無いキー 174 件) を、2021用語集＋chumJA `ja.xml`＋公式5版で補完。
3. ハードコード日本語を段階的に `t(key)` へ移行 (大がかり。別タスク化可)。

**推奨**: フェーズ 2 完了後に要否を再検討。UI 文字列は後回しでよい。

### フェーズ 4 — 品質パスと CI

- 用語集に対する lint スクリプト: オーバーレイ＋vendored を走査し、確定用語と違う訳、英語残置、カナ揺れ (`・` 有無、長音) を検出。`pytest` に組込み。
- `docs/` に翻訳方針 (カナ表記ルール、固有名は原則カナ、ルール用語は公式5版準拠 等) を明文化。

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
