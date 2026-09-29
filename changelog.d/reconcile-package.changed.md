- **`scripts/chum5_reconcile.py` を章ごとのパッケージに割った。** 828 行 1 枚だったものを
  `scripts/reconcile/`（`_saves` / `prices` / `balance` / `roundtrip` / `fidelity` / `cli`）に。
  答えを返す側と印字する側が分かれ、比較そのものは stdout を捕まえずに呼べる。
  コマンドの使い方・各不一致の読み方は従来どおり `chum5_reconcile.py` の説明書きにある。
