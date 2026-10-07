- **`sharp` の librsvg 由来の脆弱性（GHSA-wq5f-xc86-pv6w / CVE-2026-96889、high）を解消。**
  `next` → `sharp` 経由で 0.35.4 が入っていた。`next` の要求は `^0.35.4` なので
  lockfile を 0.35.5 に上げるだけで済み、`package.json` は変えていない。
