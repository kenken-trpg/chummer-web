- **Cloudflare Worker の設定に実際のホスト名と Cloud Run の URL を入れた。**
  `cr.millionskenken.org` で先に立てて、トークンの発行・ホストヘッダの差し替え・
  `/api/ready`・cron を確かめてから本番名に移している。`RUN_URL` は Cloud Run が
  報告する `status.url` そのもので、minted token の audience にもなるため一字も違えられない。
