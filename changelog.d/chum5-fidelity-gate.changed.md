- **書き出した `.chum5` が Chummer の読む欄を落としていないか、CI で見張るようにしました。**
  Chummer 自身のテスト用キャラ 34 件と項目ごとに突き合わせ（`make reconcile` の `--fidelity`）、
  Chummer が読み戻す欄が欠けていれば落ちます。Chummer が書くだけで読まない欄（読み込み時に計算し直す
  `totalvalue` など）と 5.202 時代の綴りは、理由つきで一覧に分けました。あわせて、魔法があるのに
  伝統を持たないキャラ（アデプト）にも Chummer と同じ空の Custom `<tradition>` を書きます。
