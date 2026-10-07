- **CONTRIBUTING.md に「Debugging」節を追けた。** `backend/.venv` と
  イメージが同じライブラリ版を持たないこと（`starlette` 1.6.0 / 1.7.0 で
  `CORSMiddleware` の挙動が逆になり、手元の原典で本番を説明しようとして 3 回誤った）と、
  Cloudflare → Worker → Cloud Run → Caddy → uvicorn を上から剥がして原因の層を
  絞るコマンドを置いている。
- **`docs/deploy.md` のキャッシュの規則を、ルートに依らない形に書き直した。**
  `Vary`・ヘッダ変換の評価順・`Authorization`・Cache API の 4 つを先に挙げ、
  `/api/catalog` を落とした経緯はその適用例にしている。
