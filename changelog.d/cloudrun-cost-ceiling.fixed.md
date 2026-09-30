Cloud Run + Cloudflare Worker 構成の「公開前」手順を `docs/deploy.md` に追加した。
WAF のレート制限ルールは、この構成では二重の備えではなく、課金される前にトラフィックを
止める唯一の蛇口になる（`maxScale: 1` は CPU とメモリの上限であって、下り転送は
その外にある）。GCP の予算アラートが通知であって停止ではないことも明記した。
あわせて `deploy/cloudrun/service.yaml` に `RATE_LIMIT` と `IMPORT_RATE_LIMIT` を
明示し、Containers 側の Worker と同じ値が同じ形で読めるようにした。
