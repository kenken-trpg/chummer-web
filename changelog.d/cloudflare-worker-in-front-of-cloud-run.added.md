Cloud Run を認証必須のまま置き、Cloudflare Worker だけが呼べる構成を `deploy/cloudflare-proxy/` に追加。`*.run.app` は 403 のままなので、ゾーンの WAF が唯一の入口の前に立ち、`TRUST_CLOUDFLARE_IP=1` も迂回されない。
