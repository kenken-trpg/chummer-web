# 作業記録（履歴）

ここにあるのは**ほぼすべて実施済みの作業計画**です。書かれた時点のコードを前提にしているので、
現状の説明としては読まないでください。「なぜこの形になっているか」を辿るための記録です。

各ファイルの冒頭に**状態**を 1 行で書いてあります。1 本だけ開いた人にも
履歴なのかどうかが分かるようにするためで、ここに戻らなくても判断できます。

現役の計画・設計は次のとおりです。

- [`translation-plan.md`](translation-plan.md) — 日本語化。上流訳 430 件の突き合わせなどが未着手。
- [`life-module-skill-overflow-design.md`](life-module-skill-overflow-design.md) — ライフモジュールの技能上限・超過分移し替えの詳細設計。独立した計算基盤を実装中。

それ以外は原則として履歴です。
[`fvtt-export-plan.md`](fvtt-export-plan.md) は書き出しのフィールド対応表そのものなので、
実施済みでも仕様としては現役です。

現状を知りたい場合は `docs/` 直下を参照してください:

| 知りたいこと | 参照先 |
| --- | --- |
| 全体構造・データフロー・API 一覧 | [`../architecture.md`](../architecture.md) |
| ルール / アイテム / タブの追加手順 | [`../adding-rules.md`](../adding-rules.md) |
| Chummer5a データの取り込みと翻訳オーバーレイ | [`../data-pipeline.md`](../data-pipeline.md) |
| デプロイ | [`../deploy.md`](../deploy.md) |
| UI 文言の 2 レイヤーとロケール追加 | [`../i18n.md`](../i18n.md) |
| 書き出し（何が出るか・取り込み手順・制限） | [`../exports.md`](../exports.md) |
| 共有リンクの形式 | [`../share-link.md`](../share-link.md) |

## 一覧

### アーキテクチャ

- [`stateless-refactor.md`](stateless-refactor.md) — サーバー側のキャラ保管を廃してブラウザ（IndexedDB）へ
- [`refactor-page-split-plan.md`](refactor-page-split-plan.md) — 巨大な `page.tsx` の分割
- [`refactor-character-sheet-plan.md`](refactor-character-sheet-plan.md) — シート描画の分割
- [`refactor-sidebar-qualities-plan.md`](refactor-sidebar-qualities-plan.md) — サイドバーと資質タブ

### ルール / データ

- [`settings-plan.md`](settings-plan.md) — Chummer セッティングファイルの移植（段階 1: 使用書籍）

### エンジン / バックエンド

- [`refactor-compute-phases-plan.md`](refactor-compute-phases-plan.md) — `compute()` のフェーズ分割
- [`refactor-ctx-bundles-plan.md`](refactor-ctx-bundles-plan.md) — フェーズ間で渡す `Ctx` バンドル
- [`refactor-improvements-plan.md`](refactor-improvements-plan.md) — `improvements` パッケージの分割
- [`refactor-effects-typeddict-plan.md`](refactor-effects-typeddict-plan.md) — `effects` の型付け
- [`refactor-effect-rows-plan.md`](refactor-effect-rows-plan.md) — 効果行の型付け（上の続き）
- [`refactor-data-loader-plan.md`](refactor-data-loader-plan.md) — データローダの分割
- [`refactor-catalog-typeddict-plan.md`](refactor-catalog-typeddict-plan.md) — `catalog()` の型付け
- [`refactor-ware-qualities-plan.md`](refactor-ware-qualities-plan.md) — ware / 資質の切り出し
- [`refactor-gear-weapons-plan.md`](refactor-gear-weapons-plan.md) — ギア / 武器 / 車両の切り出し
- [`refactor-engine-e402-b023-plan.md`](refactor-engine-e402-b023-plan.md) — 遅延 import とループ変数束縛の解消
- [`refactor-mypy-plan.md`](refactor-mypy-plan.md) — バックエンド全体の mypy strict 化
- [`refactor-chum5-roundtrip-plan.md`](refactor-chum5-roundtrip-plan.md) — `.chum5` 入出力の往復一致
- [`chum5-export-for-chummer-plan.md`](chum5-export-for-chummer-plan.md) — 書き出した `.chum5` を Chummer.exe が読めるようにする

### テスト / フロントエンド

- [`frontend-test-setup-plan.md`](frontend-test-setup-plan.md) — vitest ハーネスの導入
- [`frontend-test-coverage-plan.md`](frontend-test-coverage-plan.md) — 上に載せるテストの優先順位
- [`refactor-tab-tests-plan.md`](refactor-tab-tests-plan.md) — タブ単位のテスト
- [`print-sheet-plan.md`](print-sheet-plan.md) — 印刷 / PDF 用レイアウト
- [`fvtt-export-plan.md`](fvtt-export-plan.md) — Foundry VTT（shadowrun5e 0.34.5）向け書き出しのフィールド対応表

### 書き出し

ここにあるのは設計の記録です。使う側の文書は `docs/` 直下にあります。

- [`udonarium-export-plan.md`](udonarium-export-plan.md) — ユドナリウムのキャラクターコマ（器とチャットパレット）
- [`udonarium-vehicles-plan.md`](udonarium-vehicles-plan.md) — 上に乗り物とドローンのコマを足す
- [`chum5-export-for-chummer-plan.md`](chum5-export-for-chummer-plan.md) も書き出しの記録です（エンジン／バックエンドの節に載せています）

### デプロイ

- [`cloud-run-plan.md`](cloud-run-plan.md) — Google Cloud Run で公開するまでの段取り

### 翻訳

- [`translation-plan.md`](translation-plan.md) — 日本語化のフェーズ計画（**現役・一部未着手**）。生成物の
  `../translation-glossary.md` / `../translation-glossary-mismatches.md` /
  `../translation-import-report.md` は `docs/` 直下にあります
