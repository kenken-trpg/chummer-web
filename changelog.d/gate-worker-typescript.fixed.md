`deploy/` の Cloudflare Worker 2 つを CI のゲートに載せた。`check-frontend` は
`frontend/` から走るので、全リクエストの前に立つコンテナクラスと、private な
Cloud Run に届くトークンを鋳造する proxy の TypeScript は、一度も tsc に
かかっていなかった。`make check-workers` と CI の `workers` ジョブを追加し、
`deploy/cloudflare` に不足していた typescript と `typecheck` を足した。

あわせて Dependabot の対象に両ディレクトリを追加した。セキュリティ勧告は届いて
いたが通常の更新は届いておらず、2 つが勝手にずれていた —— `cloudflare-proxy` の
wrangler は `npm audit` で high 1 件・moderate 2 件が出る版のままだったので、
もう片方に揃えて上げた（いずれも開発時のみ動くもので、出荷物ではない）。
