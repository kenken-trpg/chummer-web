# Chummer Web

非公式の Shadowrun 5th Edition キャラクター作成 Web アプリです。Catalyst Game Labs / The Topps Company とは無関係です。

ゲームデータと基礎翻訳は [chummer5a/chummer5a](https://github.com/chummer5a/chummer5a)（GPL-3.0）の `Chummer/data` と `Chummer/lang` を使います。このプロジェクトも GPL-3.0 です。日本語用語オーバーレイ（`backend/data/ja_overrides/`）は SR5 用語集に照らした手訳を主とし、一部の固有名は chumJA（Chummer の SR4 期日本語訳）由来、用語の裏取りに [shadowrun5eja](https://github.com/MiyabiRouga/shadowrun5eja)（Foundry VTT SR5e 日本語化）を参照しています。出典の詳細は [`NOTICE.txt`](NOTICE.txt) を参照してください。

キャラクターデータは**ブラウザ内（IndexedDB）に保存**されます。サーバーは計算と `.chum5` 変換をするだけで、キャラを保存しません。バックアップは JSON / `.chum5` で書き出してください。

## 使い方（Docker）

必要なのは Docker（Docker Desktop など）だけです。

```bash
git clone https://github.com/kenken-trpg/chummer-web.git
cd chummer-web
cp .env.example .env      # 任意。ポートや制限を変えたいとき
make up                   # → http://localhost:8080
```

`make up` は公開イメージ（`ghcr.io/kenken-trpg/chummer-web`）があれば pull し、なければ手元でビルドします。`make` が無い環境では `docker compose up` でも動きます（初回はビルドに数分）。

| コマンド | 内容 |
|---|---|
| `make up` | 起動（`http://localhost:8080`） |
| `make down` | 停止 |
| `make logs` | ログ追尾 |
| `make update` | `git pull` ＋ イメージ更新 ＋ 再起動 |
| `make doctor` | 起動前チェック（Docker / ポート空き 等） |

Chummer のゲームデータはイメージのビルド時に取得して同梱されます（実行時のネットワーク不要、特定コミットに固定）。

## 使い方（Docker なし・開発向け）

Python 3.11+ と Node 20+ が必要です（Windows は Docker を推奨）。

```bash
make setup       # backend venv ＋ npm install
make data        # Chummer ゲームデータ取得（backend/vendor/、git 管理外）
make dev         # API(:8000) と Next dev サーバ(:3000) を同時起動。Ctrl-C で両方停止
```

ブラウザで http://localhost:3000 を開きます。`make` が無ければ各ターゲットは `Makefile` の1行コマンドです。

## `.chum5` の取り込み

Chummer5a の `.chum5` / `.chum5lz` セーブを取り込めます（best-effort。カタログで解決
できないアイテムはスキップし、読込時に一覧表示）。`.chum5lz` が展開できない場合は
Chummer で非圧縮 `.chum5` に保存し直してください。

## テスト / チェック

```bash
make check       # CI と同じ: ruff / pytest / mypy / tsc / eslint / prettier / build
```

## 構成 / 開発ドキュメント

```
backend/    FastAPI + ルールエンジン（app/engine/compute の compute() が中心）。ステートレス
frontend/   Next.js 15 App Router + React 19。キャラは IndexedDB
deploy/     Caddyfile + supervisord.conf（コンテナ内のプロセス構成）
docs/       アーキテクチャ・データパイプライン・デプロイ・ルール追加手順
```

- [`CONTRIBUTING.md`](CONTRIBUTING.md) — セットアップ、コーディング規約、PR の作法
- [`SECURITY.md`](SECURITY.md) — 脆弱性の報告方法（GitHub の private vulnerability reporting）
- [`docs/architecture.md`](docs/architecture.md) — データフロー、`<bonus>` ノードと `effects`、API 一覧
- [`docs/deploy.md`](docs/deploy.md) — Docker、Cloud Run / Fly / 自宅 + Cloudflare Tunnel
- [`docs/adding-rules.md`](docs/adding-rules.md) — 新しい modifier / アイテム項目 / タブ / 検証の追加レシピ
- [`docs/data-pipeline.md`](docs/data-pipeline.md) — fetch → vendor → 翻訳オーバーレイ
- [`docs/i18n.md`](docs/i18n.md) — UI 文言の 2 レイヤーと `ja`/`en` の増やし方
- [`docs/share-link.md`](docs/share-link.md) — 読み取り専用の共有リンク（`/share#c=…`）の形式と検証
- [`docs/plans/`](docs/plans/) — 実施済みリファクタリングの作業記録（現状の説明ではなく履歴）

コントリビュート歓迎です。ゲームルールの変更は SR5（またはサプリ）のページ番号を添え、
書籍が曖昧な箇所は Chummer5a の挙動に合わせてください。
