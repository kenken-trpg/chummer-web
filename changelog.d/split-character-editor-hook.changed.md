- **`useCharacterEditor` を 4 つに割った。** 581 行の 1 フックに取り込み・書き出し・
  カタログ再取得が同居していたのを、`useCharacterImport` / `useCharacterExport` /
  `useCatalogReload` に切り出し、中核は 300 行に。返す形は同じなので画面側は無変更。
  3 箇所あった「blob をリンクにして click」の重複は `offer()` にまとめた。
