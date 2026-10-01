# Plan: Google Cloud Run で公開する

Working doc. 公開先を Cloud Run に置くまでの段取り。`docs/deploy.md` の
Cloud Run 節は「こう書ける」までで、公開運用に必要な詰め（イメージの届け方・
起動プローブ・サイジングの根拠）が入っていない。ここを埋めて、最後に
`deploy.md` へ実測値ごと差し戻すまでが範囲。

## Where we are

- `Dockerfile` は 1 コンテナ（Caddy → `127.0.0.1:8000` uvicorn / `:3000` next、
  supervisord）。`PORT` を尊重し、`USER app` で走り、書き込みは `/tmp` と
  `.next/cache` だけ。Cloud Run の要求とそのまま噛み合う。
- CI は main / `v*` タグで GHCR に amd64 + arm64 を publish 済み
  （`.github/workflows/ci.yml` の `docker-push` / `docker-manifest`）。
- `docs/deploy.md` › Google Cloud Run に `--source .` の例と、Cloudflare を
  前段に置いてはいけない理由が既にある。後者はそのまま有効。
- 手元で 37 分稼働した `ghcr.io/kenken-trpg/chummer-web:latest`（arm64、
  圧縮 159 MB / 展開 662 MB）の実測、温まった状態:

  | | 値 |
  | --- | --- |
  | メモリ | 152 MiB |
  | CPU（無負荷） | 0.3% |
  | `GET /api/health` | 25 ms |
  | `GET /api/catalog` | 初回 252 ms → 以降 23〜43 ms（2.99 MB） |

  冷えた状態は未測定。段階 1 の目的がこれ（`dev-server-cold-start-skews-timing`
  と同じ轍を踏まない）。

## 段階 1（実施済み）: 手動ミラーで run.app に出し、実測した

`chummer-web-81738` / `asia-northeast1`。GHCR のマルチアーチ index から amd64
digest を選び、`crane copy` で Artifact Registry へ複写して digest 指定で deploy。
`--source .` は採らなかった（毎回 4 ステージを組み直し、CI が smoke test した
ものとは別のイメージが出る）。予算アラートは ¥700 —— **請求先アカウントの通貨で
しか作れない**（JPY のアカウントに USD を出すと素の `INVALID_ARGUMENT`）。

### 分かったこと

**1. `--cpu-boost` は端から端まででは効かない。** アイドル後の 1 本目（起動
プローブが `/api/health` のとき、17 分アイドル）:

| | 最初の 200 | 1 本目の `/api/catalog` | 合計 |
| --- | --- | --- | --- |
| `--cpu-boost` あり | 5.9 s | 5.1 s（サーバ側 4754 ms） | 約 11 s |
| `--no-cpu-boost` | 10.4 s | 0.7 s（サーバ側 215 ms） | 約 11 s |

boost は起動から 4.5 秒を削り、その 4.5 秒を catalog 側に渡すだけだった。

**2. その差の正体は readiness だった。** `/api/health` は uvicorn が bind した
瞬間に 200 を返すので、Cloud Run はウォームアップ中のインスタンスにトラフィックを
流す。届いたリクエストは catalog をもう一度組み（`lru_cache` は同時呼び出しを
束ねない）、2 本が 1 vCPU を奪い合う。ログにオーバーレイ適用が各 2 回出ているのが
それ。boost なしだと起動が遅い分ウォームアップが先に完走し、衝突しない。

→ **`/api/ready` を足した**（`backend/app/main.py`）。ウォームアップ完了まで 503。
起動プローブはこちらを見る。失敗したウォームアップも ready を返す（さもないと
ready にならないコンテナを再起動し続けるプラットフォームで無限ループになる）。

**3. その効果を測った**（リビジョン `chummer-web-00004-84z`、21 分アイドル、
boost なし、起動プローブ `/api/ready`）:

| | 最初の 200 | 1 本目の `/api/catalog` | 合計 |
| --- | --- | --- | --- |
| 起動プローブ `/api/ready` | 13.3 s | 0.77 s（サーバ側 **90 ms**） | 約 13 s |

**これは単純な改善ではなく取引だった。** 二重構築は消えた（サーバ側
4754 ms → 90 ms、1 本目の `/api/health` も 0.099 s で既に温かい）が、最初の
利用者の待ちは 10.4 → 13.3 秒に伸びた。伸びた 2.9 秒は、以前 Cloud Run が
温まりきる前にトラフィックを入れて利用者に付け替えていた分そのもの。

割に合うのは **cron keepalive（10 分ごと）を前提にするから**で、その場合この
13.3 秒は「keepalive が落ちたときの最悪値」であり、常時の体感は温まった状態の
値になる。keepalive を入れないなら `/api/health` + boost なしのほうが速い。

**4. catalog の構築コスト** —— 手元の M 系 Mac で 0.51 秒、Cloud Run の 1 vCPU で
約 3.3 秒。`docs/deploy.md` の「first request after idle pays the one-off
`catalog()` XML parse」は正しい記述だった（一度これを否定したが、誤りだった）。

**5. ピークメモリ 約 300 MiB**（Cloud Monitoring、`1Gi` の 0.29）。`512Mi` でも
6 割で収まる。書き込み先の tmpfs もここに乗る。

**6. 温まった状態**（東京、国内から）: `/api/health` ttfb 74〜130 ms、
`/api/catalog` ttfb 70〜90 ms・total 0.48〜0.77 s（非圧縮 2.99 MB。gzip なら
425,599 バイト・0.12 s）、ページ `/` total 0.46 s。サーバ側の処理は 1〜5 ms
なので、ほぼ往復と転送。

**7. 匿名公開は組織ポリシーに阻まれた。** `--allow-unauthenticated` は `allUsers`
バインディングを要求し、*Domain restricted sharing*
(`constraints/iam.allowedPolicyMemberDomains`) がそれを拒む。deploy 自体は成功して
`Setting IAM policy failed` と言い、サービスは private のまま残る。ポリシーを緩める
代わりに、**Cloud Run を private のまま Cloudflare Worker だけが呼べる構成**を採った
（`deploy/cloudflare-proxy/`、`docs/deploy.md` › Cloud Run behind a Cloudflare Worker）。
`*.run.app` が 403 なので、ゾーンの WAF が唯一の入口の前に立ち、
`TRUST_CLOUDFLARE_IP=1` も迂回されない。

### 測れていないもの

- **429 に出るクライアント IP**。匿名公開しない判断をしたため、公開状態でしか
  確かめられないこの一点は残課題。Worker 構成に切り替えたあと、
  `cf-connecting-ip` が正しく効いているかを同じ方法で確かめる。

## 段階 2: CI 化とドメイン（段階 1 の数字を見てから）

0. ~~**Workload Identity 連携の下ごしらえ**~~ —— 手順は `docs/deploy.md` ›
   Deploying from CI に書いた（プール・プロバイダ・`gh-deploy` サービス
   アカウント・3 つの最小権限・リポジトリ変数 2 つ・連携だけを先に確かめる
   方法）。**GCP 側の実行は未了**。
1. ~~**`.github/workflows/deploy-cloudrun.yml`**~~ —— 済（#439）。`v*` タグで
   `docker-attest` の後に走る再利用ワークフロー。署名済みの manifest list から
   amd64 digest を選んで AR に複写し、digest を AR から読み直してから deploy
   する（複写が別の場所に落ちていても、誰も検めていない名前で本番に出ない）。
   `vars.GCP_PROJECT` が空なら skip するので、fork のタグは赤くならない。
2. ~~**`deploy/cloudrun/service.yaml`** — probe と env を宣言で持つ。~~ —— 済（#437）。
3. **ドメイン** — `gcloud beta run domain-mappings create`。asia-northeast1 で
   提供されているか要確認（全リージョンにはない）。Cloudflare DNS なら
   **DNS only**（grey cloud）: 証明書は Google が出すので自分のエンドポイントを
   見る必要がある。**プロキシを有効にして `TRUST_CLOUDFLARE_IP=1` は不可** ——
   `*.run.app` が開いたままで、そこへ直接叩けば `cf-connecting-ip` を詐称できる。
   WAF が欲しいなら Cloudflare Containers（`deploy/cloudflare/`）を選ぶ話になる。
4. ~~**リビジョン移行**~~ —— 済（#439）。`deploy/cloudrun/render.py` が現行
   リビジョンにトラフィックを固定したまま新リビジョンを `candidate` 0% で
   足すので、`services replace` が Ready（= `/api/ready` の起動プローブ）を
   待つ間、現行が全リクエストを受ける。応答できないリビジョンは訪問者では
   なくデプロイを落とす。移行は後続の `update-traffic` だけ。

残っているのは **3（ドメイン）** と、段階 2 の 0 に書いた **GCP 側の実行**の
2 つだけ。

## 付随して直すもの

- ~~**ログの重大度**~~ —— 済（#436）。`LOG_FORMAT=json` の出力に `severity` を
  併記した。Cloud Logging が知らない水準（独自レベル、ライブラリの `TRACE`）は
  推測せず省く。
- ~~`docs/deploy.md` › Google Cloud Run を実測値に差し替える~~ —— 済。
- ~~`changelog.d/` の断片~~ —— 済。#436・#437・#438・#439 それぞれに入れた。

## 別件で見つけたもの（この計画の範囲外）

- ~~**CSP 違反レポートがどのデプロイでも届いていない。**~~ —— 済（#467）。
  `frontend/lib/csp.ts` の `publicOrigin` が `X-Forwarded-Host` から公開
  オリジンを組むようにした。Caddy と Worker の両方がそのヘッダを（通過させる
  のではなく）**上書きで**付ける。どちらも置けない構成向けに `PUBLIC_ORIGIN`
  も読む。
- **`lru_cache` が同時呼び出しを束ねない**（`data_loader/__init__.py`）。
  `/api/ready` を入れたことで実害は塞がったが、複数リクエストが同時に冷えた
  overlay key を引けば同じ二重構築は起こりうる。

## 未検証

- Artifact Registry の保管料と Cloud Build 無料枠 —— 段階 2 で `--source .` を
  使わないなら Cloud Build は関係しない。
- asia-northeast1 のドメインマッピング可否 —— Worker 構成を採ったのでマッピング
  自体が不要になった。
