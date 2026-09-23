# Foundry VTT（shadowrun5e 0.34.5）向け書き出し — フィールド対応表

## 対象

- Foundry VTT v13 ＋ shadowrun5e システム **0.34.5**（タグ `0.34.5` = `b61d553`, 2026-05-30）
- 日本語化 Mod shadowrun5eja **3.1**（2026-05-31）。中身は `lang/ja.json` だけで、データ形式には関与しない。
- 0.37.x は参考扱い（通れば良い）。

## 方針

アクター JSON を直接作らず、システム内蔵の **Chummer/Data Import**（`src/module/apps/itemImport/apps/ActorImporter.ts`）に食わせる。
入力は Chummer の「File > Export → JSON」＝印刷用 XML を JSON 化したもの（`ActorFile` 型、`src/module/apps/actorImport/ActorSchema.ts`）。
chum5（保存形式）は通らない。完成値（`total` など）が必要なため。

型の正は `ActorSchema.ts`、見本は `src/unittests/actorImport/Examples/TestActor.ts`（いずれも 0.34.5 タグから取る）。

### 形の注意（落ちる／黙って 0 になる箇所）

- ルート: `{"?xml": {...}, "characters": {"character": {...}}}`。先頭の 1 人だけ読む。
- `attributes` は **2 要素の配列** `[null, {attribute: [...]}]`。`attributes[1].attribute` を読む。
- `nuyen` は文字列必須。`.replace()` を呼ぶので欠けると例外。
- 真偽値は `"True"` / `"False"` の文字列。
- 単数／複数は `OneOrMany`（1 件ならオブジェクト、複数なら配列）。常に配列で出してよい。
- 数値もほぼ文字列（`parseInt` / `Number` される）。

### 品目の照合（`itemImporter/Parser.ts:62-69`）

`suid` または `sourceid`（GUID）→ `name` → `name_english` の順でワールドのコンペンディウムを引き、無ければ空の品目を作ってフィールドから埋める。
こちらのデータは Chummer と同じ GUID を持つので、`name` は日本語名、`name_english` は英語名、`sourceid` は GUID で出す。

## キャラクター本体（`CharacterImporter.ts`）

| 取り込み側が読むフィールド | 用途 | こちらの出どころ | 備考 |
|---|---|---|---|
| `alias` / `name` | アクター名 | state `name` | alias は無し → `name` を出す |
| `metatype`, `metatype_english` | `system.metatype`（英語を小文字化） | state `metatype` | 英語名必須 |
| `calculatedstreetcred` | 裏社会の信用 | state `street_cred` 等から計算 | 要確認: Chummer の計算式（karma/10 ＋ 補正 − burnt） |
| `calculatednotoriety` | 悪名 | derived（資質由来）＋ state `notoriety_bonus` | 要確認 |
| `calculatedpublicawareness` | 知名度 | state `public_awareness` | |
| `karma`, `totalkarma` | カルマ現在値／総計 | derived `karma.remaining` / 総獲得 | |
| `nuyen` | 所持金（文字列） | derived `nuyen` | 必須 |
| `technomancer`, `magician`, `adept` | `system.special` | state の資質・覚醒種別 | "True"/"False" |
| `tradition.drainattributes` | 呪文抵抗の能力値（WIL 以外） | state `tradition_id` → 伝統データ | 例 `"WIL + LOG"` |
| `initiationgrade.initiationgrade[]` `{grade, technomancer}` | イニシエート／サブマージョン | state `initiate_grade` / `submersion_grade` | 最大値だけ使われる |
| `description`, `background`, `concept`, `notes` | 経歴 HTML | state 同名 | |
| `attributes[1].attribute[]` `{name_english, base, total}` | 能力値 | base = state `attributes`＋メタタイプ最低値、total = derived `totals` | total と差があると ActiveEffect で補正される |
| `initbonus`, `initdice` | 肉体イニシアティブ | derived `initiative.value` / `.dice` | |
| `astralinitdice`, `matrixarinitdice` | アストラル／AR | derived `astral_initiative` / `matrix_initiative` | |
| `critter` | クリッター判定 | 常に `"False"` | |
| `mainmugshotbase64`, `othermugshots.mugshot[].stringbase64` | 顔写真 | state `portrait` / `extra_portraits`（data URI の本体だけ） | |

## 技能（`ActorSkillImport.ts`）

`skills.skill[]` と `skills.skillgroup[]`。

| フィールド | こちら |
|---|---|
| `name`, `name_english` | 技能データの日本語名／英語名 |
| `rating` | derived の技能レベル（`skill_karma.levels` 等） |
| `knowledge`, `islanguage`, `isnativelanguage` | 知識技能・言語の区別（state `knowledge_skills`） |
| `skillcategory_english` | 知識の種類（Academic/Street/…） |
| `skillgroup_english`, `attribute`, `default` | 技能データ |
| `skillspecializations.skillspecialization[]` | 専門化 |

## 品目（`itemImporter/`）

全品目共通（`Parser.ts`）: `name`, `name_english`, `sourceid`（or `suid`）, `category_english`, `notes`/`description`, `source`, `page`, `rating`, `avail`, `qty`, `owncost`, `equipped`, `conditionmonitor`, `rawconceal`/`conceal`。

| 区分（キャラ側のキー） | 個別に読むフィールド | こちらの出どころ |
|---|---|---|
| 資質 `qualities.quality` | `qualitytype_english`, `bp`, `extra` | state 資質 |
| コンタクト `contacts.contact` | `connection`, `loyalty`, `role`, `family`, `blackmail` | state `contacts` |
| 生活様式 `lifestyles.lifestyle` | `baselifestyle`, `totalmonthlycost`, `purchased` | derived `lifestyles` |
| 防具 `armors.armor` / `otherarmors.otherarmor` | `armor`（`+` 付きは追加分）, `improvesource` | derived `armor_items` / `armor_mods` |
| ウェア `cyberwares.cyberware` | `ess`, `grade`, `capacity` | state `cyberware`/`bioware` ＋ derived 精神力 |
| 武器 `weapons.weapon` | `category_english`, `type`, `skill`, `rawaccuracy`, `rawap`, `rawrc`, `rawreach`, `damage_noammo_english`, `mode_english_noammo`, `ammo_english`, `ranges`, `clips.clip`, `currentammo`, `accessories.accessory`（`mount`, `rc`, `accuracy`, `conceal`） | derived `weapons` / `weapon_accessories` |
| 装備 `gears.gear` | `iscommlink`, `issin`, `isammo`, `category_english`; 機器は `devicerating`, `attack`, `sleaze`, `dataprocessing`, `firewall`; 弾は `weaponbonus*_english` | derived `gear` / `commlinks` / `cyberdecks` / `rccs` / `programs` |
| 呪文 `spells.spell` | `category_english`, `type_english`, `range_english`, `duration_english`, `damage_english`, `dv_english`, `descriptors_english` | state `spells` ＋ 呪文データ |
| 儀式 | `type_english`, `descriptors` | 同上（呪文のうち Ritual） |
| アデプトパワー `powers.power` | `rating`, `totalpoints` | derived `adept_powers` |
| 複合フォーム `complexforms.complexform` | `target_english`, `duration_english`, `fv_english` | state `complex_forms` |
| メタマジック／エコー `metamagics.metamagic` | 共通のみ | derived `initiation.metamagics` / `submersion.echoes` |
| クリッターパワー `critterpowers.critterpower` | `type_english`, `range_english`, `duration_english`, `extra_english` | メタタイプ由来のパワー |
| 車両 `vehicles.vehicle` | `handling`, `accel`, `speed`, `pilot`, `body`, `armor`, `sensor`, `seats`, `isdrone`, `mods.mod`（`weapons.weapon`）, `gears.gear` | derived `vehicles` / `drones` / `vehicle_mods` / `weapon_mounts` |

`_english` 付きのフィールドはシステム側がキーワードを解析するので、**必ず英語の原文**（Chummer データの値）を入れる。日本語は `name` など表示用だけに使う。

## 既存コードの再利用

- `backend/app/chummer_export/` の chum5 書き出しは、品目ごとの `sourceid` や `name` の組み立てが印刷用 XML とほぼ共通。区分ごとの変換を流用できる。
- 完成値（`total`, 限界, イニシアティブ, 武器の `raw*` と射程）は derived から取る。

## 未確定

- `calculatedstreetcred` / `calculatednotoriety` の算出式（Chummer の `CalculatedStreetCred` と合わせる）。
- 武器の `ranges` と `raw*` の書式（見本 `TestActor.ts` で確かめる）。
- 実機（FVTT v13 ＋ 0.34.5）での取り込み確認はユーザー側でしかできない。

## 進め方（案）

1. 本体（名前・メタタイプ・能力値・イニシアティブ・カルマ・ヌーヤン・経歴）＋技能＋資質。`TestActor.ts` の形でテストを固定。
2. コンタクト・生活様式・呪文・パワー・複合フォーム。
3. 防具・ウェア・装備・武器。
4. 車両・顔写真。
