# ユドナリウム：乗り物・ドローンのコマ（計画）

ユドナリウム書き出し（[`udonarium-export-plan.md`](udonarium-export-plan.md)）に、乗り物と
ドローンのコマを足す。器もパレットの書き方も精霊・スプライトのコマ
（`buildSpiritPieces` / `buildSpritePieces`）と同じで、違うのは**プールの出どころ**。
精霊はフォース 1 つで全部決まったが、乗り物は「誰が操るか」で振る人が変わる。

実装はまだしない。決めることと、実データで分かった制約を並べたもの。

## 入力に何があるか

`derived.vehicles` / `derived.drones`（どちらも `InstalledDrone[]`、
`frontend/lib/types/rows/vehicles.ts`）。テスト用セーブ 34 件のうち 19 件が乗り物を
持ち、Serpent が 8 台で最多。実際に入っている値：

| 欄                 | 実データ                                                                        |
| ------------------ | ------------------------------------------------------------------------------- |
| `handling`         | ドローンは `"3"`、乗り物は **`"2/1"`**（オンロード/オフロード）。文字列         |
| `speed` / `accel`  | `"2"` / `"1"`                                                                   |
| `body`             | `"15"`〜**`"0"`**（マイクロドローンは 0）                                       |
| `armor`            | `"14"`〜`"0"`                                                                   |
| `pilot` / `sensor` | `"3"` / `"3"`                                                                   |
| `mods`             | `Rigger Interface` が入っていればリガーが乗り込める                             |
| `weapon_mounts`    | 枠はあるが **`weapon_name` は空・`weapon_install_id` は `null`**（19 件すべて） |
| `sensors`          | `Sensor Array` のみ                                                             |
| `gear`             | **空**                                                                          |

## 実データで分かった制約（ここが計画の軸）

セーブの生 XML まで降りて確かめた結果、**穴は書き出し側ではなくインポート側**だった。
最初に「マウントに武器が載っていない」と書いたのは `derived` を見ての誤りで、
セーブには載っている。

### 1. マウントされた武器が黙って捨てられている（バックエンドの不具合）

Serpent のセーブには、ドローン 7 台のマウントに**武器が計 9 本**入っている。

| ドローン                               | マウント内の武器                                  |
| -------------------------------------- | ------------------------------------------------- |
| F-B Bumblebee                          | Stoner-Ares M202 / Ares Desert Strike             |
| Steel Lynx                             | Stoner-Ares M202 / ArmTech MGL-12 / Narcoject One |
| MCT-Nissan Roto-drone                  | Krupp Arms Kriegfaust / Terracotta X-6 MGL        |
| MCT Fly-Spy ×2・Kanmushi・Ares Cheetah | Narcoject One                                     |

`derived` では全部 `weapon_name: ""` / `weapon_install_id: null`。原因は
`backend/app/chummer_import/vehicles.py:80` が **`<mountedweaponname>` を読んでいる**こと。
このタグはセーブに 1 つも無い（Chummer は `<weaponmount><weapons><weapon>` と
**入れ子で**持つ）。しかも同 93 行の `vehicleLoadSkipped` 警告は
`./weapons/weapon`（乗り物直下）しか見ていないので、**警告も出ない**。
Serpent のインポート警告 9 件にマウント武器の話は 1 つも無い。

直すときの注意：**1 つのマウントに武器が 2 本入り得る**（Bumblebee）。
`InstalledWeaponMount` は `weapon_install_id` を 1 個しか持たないので、
リストにするか 1 本 1 行にするかの形の変更が入る。

### 2. オートソフトの所属は、直せるものと直せないものがある

- **直せる**：マウント武器にぶら下がった `[Weapon] Targeting Autosoft`
  （Bumblebee の Stoner-Ares M202 用、`extra` に武器名が入っている）。
  武器ごと捨てられているので、1 と同じ修正で戻る。
- **直せない**：キャラの持ち物に浮いている 12 本。`<extra />` も `<parentid />` も
  **セーブの中で空**で、Chummer 自身どのドローン用か記録していない。
  インポートの取りこぼしではなく、元データに無い。

→ B-3（先にインポートを直す）で戻るのは `[Weapon]` 側だけ。`[Model]` 側は
変数にして卓で入れてもらう形にせざるを得ない。

### 3. リガー技能はある（当初の記述は誤り）

最初に「Serpent にも Gunnery も Pilot 技能もない」と書いたのは誤り。存在しない
キー（`derived.skills`）を見ていた。技能は `derived.skill_totals` にあり、Serpent は
**Gunnery 6・Pilot Ground Craft 5・Pilot Aircraft 3・Pilot Watercraft 1** を持つ。
遠隔操作もジャンプインも実データで振れる。

## コマに何を載せるか

乗り物・ドローンの判定は SR5 で 3 通りに分かれ、ダイスプールの顔が違う。

- **手動**：反応力 ＋ 操縦技能 ［ハンドリング］
- **遠隔操作 / ジャンプイン**：論理力 ＋ 操縦技能 ［ハンドリング］（VCR のボーナス付き）
- **自律**：パイロット ＋ オートソフト ［センサー または ハンドリング］

マウント武器は、手で撃つなら 砲術＋敏捷力 ［精度］、ジャンプイン/遠隔なら 砲術＋論理力、
自律なら パイロット＋ターゲティング・オートソフト ［センサー］。

変数にするのは `{パイロット}`・`{センサー}`・`{ハンドリング}`・`{装甲値}`、それに
操る人の `{論理力}`・`{反応力}`・`{砲術}`・`{操縦技能}`。精霊のフォースと同じ理屈で、
卓で動くのはこのあたりだけ。

`detail` パネルは精霊と同じ形で、**乗り物 CM = 12 + ceil(ボディ/2)**（SR5 p.199）と
マトリックス CM = 8 + ceil(装置評価/2)、それに移動力・イニシアティブ。

## 決めたこと

- **A-1：3 通り全部**を出す。手動（反応力＋操縦技能［ハンドリング］）・遠隔/ジャンプイン
  （論理力＋操縦技能、VCR 込み）・自律（パイロット＋オートソフト［センサー］）を
  セクションに分ける。卓で誰が操るかは場面で変わるので、出し分けない。
- **B-3：先にインポート側を直す。** `[Model]` オートソフトの機種を拾ってドローンに
  紐付ける。書き出しはその後。推定でごまかさない。
- **C-2：先にマウントへの武器搭載を確かめる。** 載らないなら実装側を直してから。
- **D-2：zip は分ける。** 召喚物／乗り物／ドローンで別の zip。
- **E-2：ボタンは 1 つ。** 精霊コマのボタンに合流させ、1 回押すと該当する zip が
  それぞれ落ちる（D-2 と合わせて、1 クリック・複数ダウンロード）。

## 作業の順番

B-3 と C-2 が先行条件なので、書き出しは 3 番目になる。

1. ~~**マウント武器のインポートを直す**~~ → 済み（#521）。詳細は下記
2. ~~**ドローンに付いてくる積載物を engine に作らせる**~~ → 済み。詳細は下記
3. **書き出しを足す**（下記）← 次はここ

### 1 で直したこと（済み）

バグは 2 つ重なっていた。

- 読み手が `<mountedweaponname>` という**存在しないタグ**を見ていた。Chummer は
  `<weaponmount><weapons><weapon>` と入れ子で持つ。
- 仮に読めていても、`<weaponmountcategories>`（マウントが受ける**カテゴリ**の一覧）を
  `allowedweapons`（カタログが持つ、組み込みマウント専用の**武器名**の一覧）に
  取り込んでいたため、engine 側の照合が武器名 vs カテゴリ名になり全部はじかれていた
  （`engine.gear.weaponNotOnMount` が 10 件）。

直した結果、Serpent のドローン 7 台に武器 8 挺が戻り、nuyen の食い違いも
|adj| 30,720 → 10,715 に縮んだ。残る 10,715 のうち 7,000 は Steel Lynx の
M202 がセーブ上 `<cost>0</cost>` で保存されているぶん。保存された値段を
優先する話は別件（他のキャラを悪化させる類）なので手を付けていない。

### 2 で直したこと（済み）

engine は `included_weaponmounts` から組み込みマウントを作っていたが、組み込みの
**武器**と**オートソフト**は作っていなかった。足したもの：

- カタログに `included_weapons`（項目の `<weapons><weapon>`）
- `WeaponInstall.included`。無料で、プレイヤーが外せない（UI も削除・個数・値引きを出さない）
- 組み込み武器をマウントに留める。どのマウントかはデータが知っている
  （そのマウントの `allowedweapons` が銃の名前を挙げている）
- 組み込みオートソフトを `programs` に作り、`parent_id` でドローンに付ける。
  無料で、評価と対象は項目の属性から
- 項目の短い書き方（`<gear rating="3" select="...">名前</gear>`）の評価と対象を読む。
  ゲームデータ中 69 件が評価を、32 件が対象をこの形で持っていて、
  これまでは評価 1・対象なしに潰れていた
- `_ensure_drone_equipment` を gear の計算の**先頭**に移した。付いてくるものは
  下流の各パスがふつうに解決すればよく、以前は programs と weapons の後ろに
  いたので作ったオートソフトが誰にも解決されなかった

F-B Bumblebee は、重マウントに Stoner-Ares M202・その照準用オートソフト評価 3・
Rigger Interface・Sensor Array を持った状態で出る（いずれも無料、ドローン代 24,000¥ のまま）。
書き出しでは組み込み武器に `<parentid>` を立てる（Chummer と同じ形）ので、
往復しても無料のままで、二重に買われない。

マウントに別の銃を載せてあるときは、項目の銃は置き場所が無いので作られない。
セーブ由来のマウントは `allowedweapons` を持たないので engine が補うが、
**空のときだけ**。そうしないと、プレイヤーが載せ替えた銃を項目の一覧が
はじいてしまう（Serpent の Bumblebee が実際にその形）。

### まだ残っていること

キャラの持ち物に浮いている `[Model]` オートソフト 12 本は所属不明のまま
（セーブの中で `<extra />` も `<parentid />` も空で、Chummer 自身どのドローン用か
記録していない）。書き出しでは変数にして卓で入れてもらう。

## 3 で作ったもの（済み）

- `frontend/lib/vtt-pools.ts` に `vehicleHandling`（`"2/1"` の分解）・
  `vehicleConditionMonitor`（12＋強靱力÷2）・`vehicleSkills`（カタログの
  `Vehicle Active` から拾う。本で増える `Pilot Aerospace` も入る）
- `frontend/lib/udonarium.ts` に `buildVehiclePieces` / `buildUdonariumVehicles`
- ボタンは 1 つに合流。押すと該当する zip が種類ごとに落ちる
  （`udonarium-conjured` / `udonarium-vehicles` / `udonarium-drones`）

パレットは操り方ごとに 3 セクション。搭載武器があれば各セクションに攻撃も出る。
変数は 操縦値・（あれば）操縦値オフロード・パイロット・センサ・強靱力・装甲値・
操縦技能・Gunnery・オートソフト と、反応力・論理力・（武器があれば）敏捷力。

**操縦技能は 1 つの変数にまとめた。** どのドローンがどの操縦技能を要るかは
データに無い（Chummer はドローンをサイズで分類していて、地上/空中/水上を
持っていない。乗り物側も `Corpsec/Police/Military` のような混成カテゴリがある）。
修得している中で最高のものを初期値にし、ほかも定義して注記で名前を出す。

**Gunnery の変数名は英語のまま。** 用語集に訳語が無く、勝手に作らない方針。
カタログ名をそのまま使う既存のやり方（`varName(tr(skill.name))`）と同じ。

### 実機確認（udonarium.app 1.17.4）

Serpent のドローン 7 台の zip を「ZIP読込」から入れ、7 コマとも卓に出た。
F-B Bumblebee のパレットでダイスボットが自動で シャドウラン 5th Edition になり、

- `({反応力}+{操縦技能}+0)B6@{操縦値}` → `(8B6[6]Limit[3]>=5) > 1,3,3,5,6,6,6,6 > 成功数3(リミット超過2)`
- `({パイロット}+{パイロット}+0)B6` → `(6B6>=5) > 1,3,4,4,4,6 > 成功数1`

変数もリミットも解決している。

## 見込みの作業

- `frontend/lib/udonarium.ts` に `buildVehiclePieces`（`buildSpiritPieces` と同じ形）
- `frontend/lib/vtt-pools.ts` に `vehicleLimit(handling)`（`"2/1"` の分解）と乗り物 CM
- `useCharacterExport.ts` に `downloadUdonariumVehicles`、`Toolbar.tsx` にボタン
- `udo.*` の訳語を `locales/{ja,en}/sheet.ts` に（`ハンドリング`・`パイロット`・`センサー`は
  [`docs/translation-glossary.md`](../translation-glossary.md) を引く）
- テストは `udonarium.test.ts` に。既存の `undefinedRefs(palette)` 不変条件が効く
- `changelog.d/udonarium-vehicles.added.md`

ココフォリア側に乗り物コマは無いので、**ユドナリウムだけが先に持つ機能になる**。
プールの計算を `vtt-pools.ts` に置けば、後からココフォリアにも回せる。
