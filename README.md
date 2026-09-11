_[English version / 英語版はこちら](README.en.md)_

# Chummer Web

非公式の シャドウラン 5th Edition キャラクター作成 Web アプリです。Catalyst Game Labs / The Topps Company とは無関係です。

ゲームデータと基礎翻訳は [chummer5a/chummer5a](https://github.com/chummer5a/chummer5a)（GPL-3.0）の `Chummer/data` と `Chummer/lang` を使います。このプロジェクトも GPL-3.0 です。日本語用語オーバーレイ（`backend/data/ja_overrides/`）は SR5 用語集に照らした手訳を主とし、一部の固有名は chumJA（Chummer の SR4 期日本語訳）由来、用語の裏取りに [shadowrun5eja](https://github.com/MiyabiRouga/shadowrun5eja)（Foundry VTT SR5e 日本語化）を参照しています。出典の詳細は [`NOTICE.txt`](NOTICE.txt) を参照してください。

キャラクターデータは**ブラウザ内（IndexedDB）に保存**されます。サーバーは計算と `.chum5` 変換をするだけで、キャラを保存しません。バックアップは JSON / `.chum5` で書き出してください。

## 言語について

UI は日本語と英語を切り替えられます（上部のセレクタ）。**基準ロケールは日本語**で、
完全なのはこちらです。

英語ではアプリ側の文言（タブ、ボタン、パネル、シート・印刷レイアウト、作成チェックの
指摘文）が英語になり、カタログ項目は Chummer のデータファイル本来の英語名で出ます。
ルールエンジンの指摘文はキーとパラメータで返ってくるので、文言はフロントの辞書にあり、
言語切替に追従します。

ココフォリア書き出しも言語切替に追従します。ただし**既定は日本語**です
（日本語の VTT で、コマは日本語卓の部屋に貼られるため）。ダイスコマンド自体は
BCDice の記法なので、どちらの言語でもそのままです。

詳細は [`docs/i18n.md`](docs/i18n.md) を参照してください。

## 使い方（Docker）

必要なのは Docker（Docker Desktop など）だけです。

```bash
git clone https://github.com/kenken-trpg/chummer-web.git
cd chummer-web
cp .env.example .env      # 任意。ポートや制限を変えたいとき
make up                   # → http://localhost:8080
```

`make up` は公開イメージ（`ghcr.io/kenken-trpg/chummer-web`）があれば pull し、なければ手元でビルドします。`make` が無い環境では `docker compose up` でも動きます（初回はビルドに数分）。

| コマンド      | 内容                                     |
| ------------- | ---------------------------------------- |
| `make up`     | 起動（`http://localhost:8080`）          |
| `make down`   | 停止                                     |
| `make logs`   | ログ追尾                                 |
| `make update` | `git pull` ＋ イメージ更新 ＋ 再起動     |
| `make doctor` | 起動前チェック（Docker / ポート空き 等） |

Chummer のゲームデータはイメージのビルド時に取得して同梱されます（実行時のネットワーク不要、特定コミットに固定）。

## Web に公開する（localhost ＋ Cloudflare Tunnel）

自宅の PC やサーバーで動かしたまま、ポートを開けずにインターネットへ公開する手順です。
`cloudflared` が外向きの 443 だけでつなぐので、ルーターの設定は要りません。

### 1. localhost で起動する

上の「使い方（Docker）」のとおり起動し、http://localhost:8080 で開けることを確かめます。
`compose.yaml` はポートを `127.0.0.1` だけに公開しているので、LAN からは直接届きません（トンネル経由だけ）。

公開するときは、ローカル向けに緩めてある制限を元に戻しておきます。`.env` に：

```bash
RATE_LIMIT=120/minute
IMPORT_RATE_LIMIT=20/minute
# TRUSTED_PROXY_HOPS は 0 のまま（Cloudflare の cf-connecting-ip を使う）
```

書き換えたら `make up` をもう一度実行すると反映されます。

### 2. cloudflared を入れる

```bash
brew install cloudflared            # macOS
# Linux / Windows: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
cloudflared --version
```

### 3a. お試し：一時 URL で公開（アカウント不要）

```bash
cloudflared tunnel --url http://localhost:8080
```

表示される `https://<ランダム>.trycloudflare.com` がそのまま公開 URL です。Ctrl-C で止まり、
起動のたびに URL が変わります。卓の当日だけ共有する、といった用途向けです。

### 3b. 常設：自分のドメインで公開（Cloudflare アカウント＋ドメインが必要）

ドメインを Cloudflare の DNS で管理している前提です。以下 `chummer.example.com` を自分のホスト名に置き換えます。

```bash
cloudflared tunnel login                                   # ブラウザで認証 → ~/.cloudflared/cert.pem
cloudflared tunnel create chummer                          # トンネル ID と ~/.cloudflared/<ID>.json ができる
cloudflared tunnel route dns chummer chummer.example.com   # DNS に CNAME を作る
```

`~/.cloudflared/config.yml` を作ります（`<ID>` と `<ユーザー名>` は置き換え）：

```yaml
tunnel: <ID>
credentials-file: /Users/<ユーザー名>/.cloudflared/<ID>.json   # Linux なら /home/<ユーザー名>/...
ingress:
  - hostname: chummer.example.com
    service: http://localhost:8080
  - service: http_status:404
```

```bash
cloudflared tunnel run chummer      # 前面で起動 → https://chummer.example.com
```

動いたら、OS 起動時に自動で立ち上がるようにします：

```bash
sudo cloudflared service install    # config.yml を読んでサービス登録（macOS: launchd / Linux: systemd）
```

Linux の systemd 版は `/etc/cloudflared/config.yml` を読むので、`config.yml` と `<ID>.json` をそこへコピーし、
`credentials-file` のパスも合わせてください。アプリ側は `restart: unless-stopped` なので、Docker が起動すれば一緒に上がります。

### 4. 確認と後片付け

- `https://chummer.example.com/api/health` が `{"ok":true}` を返せば疎通しています。
- 身内だけで使うなら、Cloudflare ダッシュボードの **Zero Trust → Access** でそのホスト名にログイン（メール認証など）を掛けるのがおすすめです。匿名アクセスがなくなります。
- 止めるとき：`cloudflared` を Ctrl-C（サービス化したなら `sudo cloudflared service uninstall`）、アプリは `make down`。
  トンネル自体を消すなら `cloudflared tunnel delete chummer` と、DNS の CNAME を削除します。

キャラクターはブラウザ側に保存されるので、公開してもサーバーにキャラは残りません。
環境変数や他のデプロイ先は [`docs/deploy.md`](docs/deploy.md) を参照してください。

## 使い方（Docker なし・開発向け）

Python 3.11+ と Node 22.12+ が必要です（CI と Docker は 24 系。Windows は Docker を推奨）。

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

コントリビュート歓迎です。ゲームルールの変更は SR5（またはサプリメント）のページ番号を添え、
ルールブック・サプリメントでは曖昧な箇所は Chummer5a の挙動に合わせてください。
