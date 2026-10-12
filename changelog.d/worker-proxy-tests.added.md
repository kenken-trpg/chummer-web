- **本番の入口の Worker にテストを入れました。**
  `deploy/cloudflare-proxy`（Cloud Run の前に立ち、OIDC トークンを発行する
  Worker）はこれまで `tsc --noEmit` だけでした。署名した JWT の中身と検証、
  audience の取り違え、トークンの使い回しと期限前の再発行、交換失敗時の扱い、
  ヘッダの差し替え（authorization／cf-connecting-ip／x-forwarded-host／host）、
  keepalive cron の 11 件を vitest で押さえます。CI の `workers` ジョブで走ります。
