# Chummer でのクリッター・パワー往復確認

資質が付けるクリッター・パワー（Infected・Dracoform）を、このアプリから書き出して
Chummer 本体で開き、資質を外して保存し直した記録です。
`backend/tests/test_critter_powers_desktop.py` がこのフォルダーのファイルを読みます。

## 環境

- Chummer 5.226.177（Nightly、2026-10-24 に確認）。このアプリが固定している
  chummer5a のコミット `d7e94f6` から作られたビルドで、データとコードが同じ。
- Windows 版。キャラクター設定で Run Faster と Howling Shadows を有効にした。
- 2026-10-26 に同じ手順を Mac の Wine で繰り返し、同じ結果になった
  （[chummer-on-mac.md](../../chummer-on-mac.md)）。このフォルダーのファイルは Windows 版のまま。

## ファイル

| ファイル                          | 作り方                                                                                                    |
| --------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `RT-Banshee-resave.chum5`         | エルフの Infected: Banshee（任意パワー Immunity (Toxins)）を書き出し、Chummer で開いて何も変えずに保存    |
| `RT-Banshee-removed.chum5`        | 同じものを開き、資質 Infected: Banshee を外して保存                                                       |
| `RT-WesternDrake-resave.chum5`    | ヒューマンの Dracoform (Western Drake) を書き出し、Chummer で開いて何も変えずに保存                       |
| `RT-WesternDrake-removed.chum5`   | 同じものを開き、資質を外して保存                                                                          |
| `RT-WesternDrake-reapplied.chum5` | 書き出したままのファイルを開き、「特殊 → Improvements の再適用」を実行して保存                            |
| `chummer-western-drake.chum5`     | Chummer で新しくヒューマンを作り、資質 Dracoform (Western Drake) を付けて保存（Chummer 自身が書いた正解） |

書き出し元の 2 ファイルは残していません。テストがその場で書き出して比べます。

## 確認したこと

- 書き出したファイルは、どちらも警告なしで開け、クリッターパワーのタブに一覧が出た。
- 資質を外すとパワーも消えた。外したファイルには、パワーも資質との結び付き
  （CritterPower の改善効果）も残っていない。
- 再保存したファイルをこのアプリで読み直すと、資質・任意パワーの選択・アーマー 2 が戻る。

## 見つけたこと

- **改善効果が書かれていなかった。** Chummer は開くときに `<bonus>` を実行し直さず、
  保存された改善効果だけを使う。書き出しにパワーの改善効果が無かったので、
  Hardened Armor のアーマー +2 が Chummer では効いていなかった。
  資質が付けるパワーについては、Chummer と同じ改善効果を書くように直した
  （`chummer-western-drake.chum5` と同じになることをテストで確かめる）。
  直した書き出しで作った Drake を Chummer で開くと、再適用しなくてもアーマーは 2 で、
  エラーも出なかった（Banshee も同じく開けた）。
  資質そのものの効果（能力値の上昇・MAG・タブ・資質の追加・天然武器）は、まだ書いていない。
- **Chummer は、クリッター・パワーのレーティングを読み込まない。**
  `CritterPower.Load` が `<rating>` を読まないので、開いて保存し直すと 0 になる
  （`RT-WesternDrake-resave.chum5` の Hardened Armor）。最新の chummer5a でも同じ。
  このアプリはレーティングを資質のデータから決めるので、読み直しには影響しない。
- **「Improvements の再適用」は、パワーの効果を 2 重にする。**
  資質を付け直してパワーを作り直すときに効果が付き、そのあとパワーの効果がもう一度付く。
  `RT-WesternDrake-reapplied.chum5` ではアーマーの改善効果が 2 つあり、Chummer の表示は 4 だった。
