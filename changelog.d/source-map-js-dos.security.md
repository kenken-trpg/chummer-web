- **`source-map-js` の event-loop DoS（GHSA-68fv-2mgg-jv7q、high）を解消。**
  `next` → `postcss` 経由で 1.2.1 が入っていた。`postcss` の要求は `^1.2.1` なので
  lockfile を 1.2.2 に上げるだけで済み、`package.json` は変えていない。
