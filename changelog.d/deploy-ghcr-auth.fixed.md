- **Cloud Run へのデプロイが GHCR を匿名で読んでいた。** イメージを Artifact
  Registry に写す段で `MANIFEST_UNKNOWN` になり、ダイジェストの誤りに見えて実は
  資格情報がなかった。GHCR パッケージは作成時 private なので、公開設定に依存しない
  よう `packages: read` と GHCR へのログインを追加した（他の GHCR ジョブ 3 つと同じ形）。
