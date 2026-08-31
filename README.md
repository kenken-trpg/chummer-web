# Chummer Web

非公式の Shadowrun 5th Edition キャラクター作成 Web アプリです。Catalyst Game Labs / The Topps Company とは無関係です。

ゲームデータと翻訳は [chummer5a/chummer5a](https://github.com/chummer5a/chummer5a)（GPL-3.0）の `Chummer/data` と `Chummer/lang` を使います。このプロジェクトも GPL-3.0 です。

第1段階: Priority、メタタイプ、属性、スキル、Quality、派生値、JSON 保存/読込。

Chummer5a の `.chum5` / `.chum5lz` セーブを取り込めます（best-effort。カタログで解決
できないアイテムはスキップし、読込時に一覧表示）。`.chum5lz` が展開できない場合は
Chummer で非圧縮 `.chum5` に保存し直してください。

## 起動

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/fetch_chummer_data.py
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

別ターミナル:

```bash
cd frontend
npm install
npm run dev
```

ブラウザで http://localhost:3000 を開きます。

## テスト / チェック

```bash
cd backend && source .venv/bin/activate && python -m pytest
```

`make` があれば一括で:

```bash
make setup     # venv + npm install
make data      # Chummer ゲームデータ取得（backend/vendor/、git 管理外）
make check     # CI と同じ: ruff / pytest / tsc / eslint / prettier / build
```

## 構成 / 開発ドキュメント

```
backend/    FastAPI + ルールエンジン（app/engine.py の compute() が中心）
frontend/   Next.js 15 App Router + React 19
docs/       アーキテクチャ・データパイプライン・ルール追加手順
```

- [`CONTRIBUTING.md`](CONTRIBUTING.md) — セットアップ、コーディング規約、PR の作法
- [`docs/architecture.md`](docs/architecture.md) — データフロー、`<bonus>` ノードと `effects` の仕組み、API 一覧
- [`docs/adding-rules.md`](docs/adding-rules.md) — 新しい modifier / アイテム項目 / タブ / 検証の追加レシピ
- [`docs/data-pipeline.md`](docs/data-pipeline.md) — fetch → vendor → 翻訳オーバーレイ

コントリビュート歓迎です。ゲームルールの変更は SR5（またはサプリ）のページ番号を添え、
書籍が曖昧な箇所は Chummer5a の挙動に合わせてください。
