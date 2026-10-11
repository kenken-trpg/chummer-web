- **タブのテストが混雑時に落ちる問題を直しました。** `vitest.config.mts` は負荷時を見込んで
  `testTimeout` を 15 秒にしていましたが、`waitFor` 自身の締め切り（`asyncUtilTimeout`、
  既定 1 秒）はそのままでした。タブが動的 import になってからは、初回の `waitFor` が Vite の
  変換も待つため、ここが実際の締め切りになっていました。`frontend/tests/setup.ts` で
  5 秒に引き上げています。
