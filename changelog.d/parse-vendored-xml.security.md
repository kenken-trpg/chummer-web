- **同梱 XML の読み込みも defusedxml を通す。** `vendor/` の data / lang /
  settings.xml は `make data` が網越しに取ってくるものなので、素の
  `ET.parse` では DTD の実体参照が展開されてしまう。読み込み口を
  `parse_vendored` 一つにまとめ、7 箇所の `# noqa: S314` をなくした。
  取り込みファイルと違い要素数・深さの上限はかけない（同梱データはそれより大きい）。
