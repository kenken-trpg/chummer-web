# 資質のLv対応とChummer5aでの確認結果

基準: Chummer5a `d7e94f6a090f267362757675d05bbe4d7543c217`（本プロジェクトの固定データ）。

- [資質定義](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/data/qualities.xml)
- [取得画面のLv判定](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Forms/Selection%20Forms/SelectQuality.cs#L136)
- [内部のLv計算](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Uniques/Quality.cs#L1567)
- [シート出力の集約](https://github.com/chummer5a/chummer5a/blob/d7e94f6a090f267362757675d05bbe4d7543c217/Chummer/Backend/Characters/Character.cs#L12656)

取得画面は数値の `<limit>` があり、`<nolevels />` がない資質をLv付きとして扱う。
この条件に該当する資質は全34件。名前に段階が含まれる別資質（Allergy、Addiction、
Changelingなど）は、この数値Lvとは別の選択肢として扱う。

| 上流の資質名 | 出典 | 最大Lv | 1Lvのカルマ（正は消費、負は獲得） |
| --- | --- | ---: | ---: |
| Focused Concentration | SR5 | 6 | 4 |
| High Pain Tolerance | SR5 | 3 | 7 |
| Indomitable (Mental) | SR5 | 3 | 8 |
| Indomitable (Physical) | SR5 | 3 | 8 |
| Indomitable (Social) | SR5 | 3 | 8 |
| Magic Resistance | SR5 | 4 | 6 |
| Will to Live | SR5 | 3 | 3 |
| Gremlins | SR5 | 4 | -4 |
| Aged | BB | 3 | -7 |
| Illness | BB | 3 | -5 |
| Perceptive | RF | 2 | 5 |
| Spike Resistance | RF | 3 | 10 |
| Tough as Nails (Physical) | RF | 3 | 5 |
| Tough as Nails (Stun) | RF | 3 | 5 |
| Dimmer Bulb | RF | 3 | -5 |
| In Debt | RF | 15 | -1 |
| Infirm | RF | 5 | -5 |
| Arcane Arrester | RF | 2 | 10 |
| Shiva Arms (Pair) | RF | 2 | 8 |
| Hello World! | DT | 3 | 8 |
| Pilot Origins | DT | 3 | 8 |
| Social Appearance Anxiety | CA | 3 | -3 |
| Death Dealer | FA | 3 | 15 |
| Flesh Sculpter | FA | 3 | 10 |
| Illusionist | FA | 3 | 10 |
| Puppet Master | FA | 3 | 10 |
| Reckless Spell Master | FA | 6 | 10 |
| Skinwalker | FA | 3 | 5 |
| Busted Cyberware | TSG | 11 | -4 |
| Battle Hardened | SL | 3 | 2 |
| Thousand-Yard Stare | SL | 3 | -3 |
| Down the Rabbit Hole | KC | 4 | -2 |
| Special Modifications | BTB | 2 | 5 |
| Stolen Gear | NF | 20 | -1 |

`Restricted Gear`（上限3）、`Records on File`（10）、`Dealer Connection`（4）、
`Close Combat Mage`（3）は `<nolevels />` を持つためLv付きにはしない。
`<limit>False</limit>` の反復取得可能な資質にもLv入力は付けない。

## 実装方針

- ローダーからカタログAPIと計算結果に `has_levels` を渡し、個別の資質名では判定しない。
- `quality_ids` は従来どおり1Lvごとに同じIDを保持する。効果・カルマ計算と `.chum5` の入出力に使う。
- 所持欄と全シート形式の表示時だけLv付き資質を集約してLvを表示し、カルマを掲載する欄では合計額を表示する。
- 追加選択、左右、無料付帯、無効化状態が違う行は別項目として扱う。
- Lv選択は個別上限と `includeinlimit` / `limitwithinclusions` の共有上限を守る。
- 所持欄の削除はその資質の全Lvを外す。Lvを下げる操作は所持Lv欄で行う。
- キャリアの取得費用は追加したLv分を合算する。Lvを下げる場合は後から取得した分から外す。

`Restricted Gear` の作成時だけの上限 (`chargenlimit=1`) など、Lvではない資質の
取得制約全般は今回の変更対象には含めない。
