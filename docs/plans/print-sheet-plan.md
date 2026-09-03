# Plan: 卓用 印刷 / PDF シートレイアウト

Working doc. First user-facing feature after the refactor series.
`components/CharacterSheet.tsx` の 4 つめのレイアウト `"print"` を足す。

## Where we are

`CharacterSheet` は `layout` prop で `standard` / `compact` / `text` を出し分ける。
`text` は `textSheet()` の `<pre>` 早期 return、他は `buildSheetData()` バンドルを
`<SheetHeader>` + 18 個の `<*Section {...s}/>` に流す（1 セクション 1 ファイル、
`components/character/sheet/sections/`）。

印刷は `globals.css` の `@media print`：`@page { margin }`、画面用シートを 2 カラムに
リフロー、ライトテーマ強制、`break-inside: avoid`。**卓向けの情報設計はされておらず**、
改ページが成り行き・コンディションモニターが数値表示・武器や防御の要点が拾いにくい。

## Approach（方針 A：CSS 主導、新規ランタイム依存なし）

`window.print()` →「PDF として保存」でそのまま PDF になる前提。`@react-pdf` や
サーバ生成は将来（方針 B）。用紙は **A4 固定**。

1. **`SheetLayout` に `"print"`**（`lib/character/sheet-data.ts`）。`useSheetLayout` が
   受理、Toolbar のレイアウト `<select>` に「印刷用」。
2. **`usePrintSheet(sheetLayout, setSheetLayout)`**（`lib/character/usePrintSheet.ts`）。
   `印刷 / PDF` ボタン → `print` レイアウトへ切替 → 2 フレーム待って `window.print()`
   → `afterprint` で元レイアウトに復帰（Safari 用に `setTimeout` フォールバック）。
3. **印刷専用ブロック**（`components/character/sheet/sections/print/`）
   - `PrintStatBlock` — `CoreSection` の代替。属性（基本/増強）、リミット 3、
     イニシアチブ、移動、防御プール（REA+INT+dodge）、ダメージ抵抗
     （BOD+armor+damage_resistance）、沈着 / 意図看破 / 記憶、エッセンス、
     非武装・特殊装甲・条件リミット・ライフスタイル。プール値は既存 `totals` / `d`
     の合成のみで新規ルールなし。
   - `PrintConditionMonitor` — 物理 / スタンを実ボックス升目で描画（3 個ごとに −1
     マーカー、`⌈BOD/2⌉` のオーバーフロー枠（破線）、`cm_recovery` 併記）。静的表示。
4. **`CharacterSheet.tsx` の印刷用セクション順**
   - 1 ページ目：ヘッダ → `PrintStatBlock` → `PrintConditionMonitor` → 技能 →
     知識 → キャリア → アクションDP → 資質。
   - `<div className="print-page-2">` に残り（戦闘 / ウェア / マトリクス / 魔法 /
     共鳴 / 武道 / コンタクト / 車両 / ドラッグ / SIN / その他ギア / 記述）。
     CSS で `break-before: page`。戦闘以降のセクションは既存コンポーネントを再利用。
5. **CSS**（`globals.css`）
   - `@page { size: A4; margin: 10mm; }`。2 カラムの旧印刷挙動は
     `.character-sheet:not(.character-sheet--print)` に隔離（standard/compact は不変）。
   - `.character-sheet--print`：モノクロ・単カラム・高密度。画面では A4 幅の紙
     プレビュー（影付き）、`@media print` で chrome を外し ~8.5pt。
   - `--print-scale` カスタムプロパティを用意（将来のページフィット微調整用、未使用）。

## 意匠

公式シートの**項目セットと配置の考え方**のみ参照。ロゴ・トレードドレスは
非公式プロジェクトのため非模倣。フッターの帰属表示は印刷でも残す。

## Commits

1. `feat(sheet): add "print" as a fourth sheet layout` — 型・`useSheetLayout`・
   `--print` class・Toolbar の option。
2. `feat(sheet): print stat-block + condition-monitor blocks` — `print/` の 2 コンポーネント、
   印刷用セクション順。
3. `feat(sheet): A4 print CSS + one-click layout switch` — `globals.css`、`usePrintSheet`、
   印刷ボタン結線。
4. `test(sheet): print blocks + usePrintSheet`。
5. `docs: plan for the print / PDF sheet layout`（本ファイル）。

各コミットで `cd frontend && npm run check` + `npm run build`。

## 検証

- `cd frontend && npm run check && npm run build`。
- ユニット：`print-sections.test.tsx`（`PrintStatBlock` / `PrintConditionMonitor` の
  升目数・プール値）、`usePrintSheet.test.tsx`（切替→print→復帰）。
- 手動：`npm run dev` で `.chum5` を取り込み → シートタブ → レイアウト「印刷用」。
  ストリートレベルが A4 2 ページ、覚醒 / 重装が 3〜4 ページで崩れず改ページ
  （Chrome 印刷プレビュー）。`印刷 / PDF` ボタン一発で切替→プレビュー→キャンセルで
  元レイアウトに戻る。標準 / コンパクト / テキストの印刷結果が退行しない。

## Not now（方針 B / 将来）

- Letter 切替 UI、ページ番号ヘッダ / フッタ。
- `@react-pdf/renderer` / サーバサイド PDF（ワンクリック DL）。方針 A の
  ページ制御で不足と判明してから。
- `--print-scale` を使ったレンダ後の自動ページフィット。
- コンディションモニターの画面上クリック操作（本件スコープ外・実装しない方針）。
