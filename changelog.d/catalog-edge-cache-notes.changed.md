- **`/api/catalog` をエッジにキャッシュしない理由を `docs/deploy.md` に書いた。**
  Cache Rule・Response Header Transform・Worker の `cf.cacheEverything` がそれぞれ
  別の理由で効かないこと（`Vary: Origin`、キャッシュ判定がヘッダ変換より前、
  `Authorization` 付きは対象外）と、Cache API なら動くが ETag の 304 を壊すので
  採らなかったことを、次に測り直す人が同じ道を辿らないよう残している。
