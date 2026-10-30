# 書き出しを Chummer 本体で確かめる

このアプリが書き出した `.chum5` を Chummer 本体で開き、残りのカルマ・新円・エッセンスが
このアプリの値と合うかを確かめる手順と、2026-10-29 までに分かったことをまとめます。
ここまでの確認は Mac の Wine（[chummer-on-mac.md](chummer-on-mac.md)）で行いました。
Windows 機では Chummer をそのまま使えます。

## 用意するもの

- Chummer 5.226.177 Nightly（[chummer-on-mac.md](chummer-on-mac.md) の表と同じ版）。
  このアプリが固定しているコミットから作られた版なので、ずれが出たらこのアプリの側を疑えます。
- Chummer のテスト用セーブ 34 件。`python scripts/chum5_reconcile.py` を一度動かすと
  `backend/vendor/chummer-tests/` に取ってきます（gitignore 済み）。
- 確認用ファイルを置くフォルダー。リポジトリの外に置きます（以下 `<rt>`）。

## 手順

1. 確認用ファイルを作る（`backend/` で）:

   ```
   uv run python scripts/chum5_check_files.py BLUE Soma Miko --out <rt> --prefix A
   ```

   セーブごとに `A-<名前>.chum5` を書き、このアプリの残りカルマ・新円・エッセンスを表示します。
   別名（alias）も `A-<名前>` になります。

2. Chummer で開き、画面下の Karma Remaining・Nuyen Remaining・Essence を読む。
   右側の Karma Summary タブに、カルマの内訳（Attributes・Positive Qualities など）が出ます。
3. **閉じるときは「保存しない」。** Chummer は 1 つのプロセスで動き、閉じるときにファイルを
   保存し直すことがあります。保存し直されたファイルを開き直すと、違う値を読むことになります。
   確かめ直すときは `--prefix` を変えて新しいファイルを作ります。
4. 合わないときは `--split` で品目の種類ごとのファイルを作り、どの種類で合わないかを見ます。

   ```
   uv run python scripts/chum5_check_files.py BLUE --out <rt> --prefix B --split
   uv run python scripts/chum5_reconcile.py --items BLUE   # このアプリの品目ごとの値段
   ```

   `-none`（品目なし）・`-cyberwares`・`-gears`・`-weapons`・`-armors`・`-vehicles` の 6 つです。
   どれも単独では合うのに全体が合わないときは、品目以外（資質・種族・ライフスタイル・効果の記録）を疑います。

5. 書き出しではなく Chummer の版の違いを疑うときは、テスト用セーブそのもの（Chummer 5.202 が保存したもの）を
   今の Chummer で開いて比べます。別名だけ変えたコピーを使い、元のファイルは開きません。

## 開くときに出る確認と答え方

| 確認                                                                     | 出るとき                                                                       | 答え方                                                                    |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------- |
| 本の設定が違う（`Message_CharacterOptions_DesyncBooksOrCustomData`）     | 保存した本の一覧が、指している設定の本に含まれないとき。テスト用セーブは全部。 | 「いいえ」。値段やエッセンスは変わらない。                                |
| Orphaned Improvements                                                    | `--split` のファイル（抜いた品目の効果の記録が残る）。                         | 「はい」。書き出したままのファイルで出たら不具合。                        |
| The character's settings file (default) could not be found               | 5.202 のテスト用セーブそのもの。                                               | 「はい」で、Sum-to-Ten なら Sum-to-Ten、Priority なら標準の組み込み設定。 |
| 設定の作成方法が違う（DesyncBuildMethod）・Qi Focus の「Select a Power」 | 2026-10-29 の修正の前の書き出し。                                              | 今の書き出しでは出ない。出たら不具合。                                    |

## Chummer の読み方について分かったこと

- **Chummer の `Load` は、多くの欄をセーブからしか読まない。** データファイルから補わないので、
  書き出しに欄が無いと 0 や既定値になります。値段・エッセンス・アーマー・ダメージ、
  最大レーティング（`<maxrating>`。無いとレーティングが 0 に切り詰められる）、
  ライフスタイルの値段と倍率、資質の払ったカルマ（`<bp>`）と種類（`<qualitytype>`）がそうでした。
  書き出しは `backend/app/chummer_export/data_fields.py` の表に従い、Chummer 自身のセーブと同じ欄を書きます。
- **`<appversion>` は版として読まれる。** 読めない文字列だと 0.0.0 とみなされ、古いセーブ向けの補正が全部動きます。
  いまは固定版の版（5.226.0）を書いています。そのため、補正に頼っていた欄（ライフスタイルの値段など）を自分で書く必要がありました。
- **`<bonus>` は開くときに実行されない。** 種族・資質・品目の効果は、作ったときに効果の記録（`<improvements>`）として残り、
  開くときはそれを使います。書き出しに記録が無い効果は、Chummer では無いことになります
  （種族の `<bonus>` が抜けていて、ドワーフのライフスタイル +20% が効いていなかった）。

## 2026-10-29 の結果

書き出しは、その日の修正（下の PR）をすべて入れたものです。

| セーブ        | 確かめたこと          | 結果                                                                                  |
| ------------- | --------------------- | ------------------------------------------------------------------------------------- |
| Gangerbean    | 全体と、種類ごと 6 つ | 新円 −1,960・エッセンス 4.0 で一致                                                    |
| BLUE          | 全体と、種類ごと 6 つ | 新円 −1,243.67 で一致（端数は `5000 div 12`）。カルマ一致                             |
| Soma          | 全体                  | カルマ・新円・エッセンス一致                                                          |
| Rez0luti0n2.0 | 全体                  | 種族の効果を直す前は新円が 317 ずれていた。直した後の確認はまだ                       |
| Miko          | 全体                  | 新円一致。カルマが Chummer 0・このアプリ 1                                            |
| SCSi          | 全体                  | 新円一致。カルマが Chummer 5・このアプリ 0（Attributes が Chummer 20・このアプリ 25） |

## 残っていること

- **Rez0luti0n2.0 を直した後の書き出しで確かめる。** このアプリの新円は 499。
- **SCSi のカルマ（Attributes 20 と 25）。** 書き出しの能力値の欄（base・karma）は元のセーブと同じでした。
  Karma Summary の Special が「−5 of 1」と出ます。元のセーブを今の Chummer で開き（手順 5）、
  同じ値なら Chummer の版の違い、違えば書き出しの違いです。
- **Miko のカルマ（1 の差）。** Karma Summary は Positive Qualities 35（上限に数えるのは 5）・Negative 24・
  Metagenic 18P/−19N。手順 5 で同じく切り分けます。
- **BLUE のエッセンス。** Chummer は 0.94（元のセーブの `<totaless>` も 0.94）、このアプリは 1.3。
  書き出しではなく、このアプリの計算の違いです。
- **資質の欄が無いと、なぜ新円まで 123,123 ずれたのか**（BLUE）。直した後は一致するので、仕組みだけ未確認です。
- **種族の効果で、まだ書けないもの。** Mittens Chargen の元のセーブには、種族から `InitiativeDice` と
  自然の武器（`Weapon`）の記録がありますが、書き出しにはありません。
- 他のテスト用セーブ（ヴィークル・魔法・テクノマンサーの多いもの）でも同じ確認を続ける。

## 2026-10-29 時点の PR

順に積み重なっています（下が上に乗る）。マージは `scripts/merge_chain.sh` でまとめて行います
（bash が要ります。Windows では Git Bash か WSL）。

| PR   | ブランチ                           | 内容                                      |
| ---- | ---------------------------------- | ----------------------------------------- |
| #818 | `fix/export-item-cost`             | 品目の値段などデータの欄を書く            |
| #819 | `fix/ware-weapon-data`             | ウェアの武器・種族の武器にもデータの欄    |
| #829 | `fix/bioware-in-cyberwares`        | バイオウェアを `<cyberwares>` に書く      |
| #830 | `fix/settings-preset-build-method` | 作成方法に合う組み込み設定を選ぶ          |
| #831 | `fix/export-maxrating`             | 最大レーティング・収束具の値段            |
| #832 | `fix/export-appversion`            | `<appversion>` に版を書く                 |
| #833 | `docs/books-prompt`                | 本の設定の確認を調べた記録                |
| #834 | `fix/export-lifestyle-data`        | ライフスタイルの値段と倍率                |
| #835 | `fix/export-quality-karma`         | 資質のカルマと種類                        |
| #836 | `fix/export-metatype-bonus`        | 種族の効果・Reach、確認用ファイルの作り方 |
