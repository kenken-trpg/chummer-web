- 開発の手順: 変更履歴は PR ごとに `changelog.d/<名前>.<種別>.md` へ書き、リリース時に `make changelog` で `CHANGELOG.md` にまとめるようにした。
  PR どうしが `[Unreleased]` の同じ行を書き換えなくなるので、毎回の競合がなくなります。コードを変える PR で書き忘れると CI が知らせます。
