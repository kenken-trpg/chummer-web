# 翻訳インポートレポート

**自動生成** — `backend/scripts/regen_ja.sh` (= `import_ja_from_refs.py --write`)。
画面の日本語名は 3 つの層から来る。上流 Chummer の `ja-jp_data.xml`、その上に重ねる
`data.json`、最後にまだ英語の名前にだけ当てるシャドウラン・コデックスの名前
（`app/data_loader/codex.py`）。ここに載るのは `data.json` の全エントリで、出どころの表ごとに分けてある。
訳の表は英語名だけで引くので、「品目」の列には、その名前を持つ品目の種類と本をすべて並べる。

- オーバーレイ合計: **330 件**
- 日本語版のある本: RG, SR5, SRCX（コデックスが再録した品目も日本語版ありと数える）

## 日本語版の無い品目にだけ当たる自前の訳 (3)

サプリの用語は英語のままにする方針（本に無い片仮名を作らない）と食い違う候補。
chumJA（SR4 の訳）は別に数える。

| English | 日本語 | 出どころ | 品目 |
|---|---|---|---|
| Acceleration | 加速値 | import_ja_from_refs.CURATED | category: R5 |
| Body | 強靱力 | import_ja_from_refs.CURATED | category: R5 |
| Services | 助力 | import_ja_from_refs.CURATED | category: RF |

## ja_curated_dt.DT (12)

| English | 日本語 | 品目 |
|---|---|---|
| Attack Dongle | アタック・ドングル | gear: DT |
| Cable Tap | ケーブル・タップ | gear: DT |
| Fight or Flight Filter | FFF | echoes: DT |
| Mathemagics | マスマジックス | echoes: DT |
| Quiet | クワイエット | echoes: DT |
| Receiver | レシーバー | gear: DT |
| Resonance Riding | 共振接続 | echoes: DT |
| Resonance Scream | 共振スクリーム | echoes: DT |
| Skinlink | スキンリンク | echoes: DT |
| Sleepwalker | スリープウォーカー | echoes: DT |
| Stealth Dongle | ステルス・ドングル | gear: DT |
| Stun Dongle | スタン・ドングル | gear: DT |

## ja_curated_rg.RG (31)

| English | 日本語 | 品目 |
|---|---|---|
| Auto-Injector | 自動注射器 | armor_mods: RG |
| Chainsaw | チェーンソー | weapons: RG |
| Collapsed Frame | 折り畳み式 | weapon_accessories: RG |
| Custom Fit | カスタムフィット | — |
| Custom Fit (Stack) | カスタムフィット(累積) | — |
| Fresnel Fabric | フレネル布 | armor_mods: RG |
| Gear Access | 装備アクセス | — |
| Gecko Grip (for Weapon with No Stock Slot) | ゲッコー・グリップ(ストック・スロットを持たない武器用) | weapon_accessories: RG |
| Gel Packs | ゲルパック | armor_mods: RG |
| High-Fashion Armor Clothing | 高級ファッション志向のアーマー・クロージング | category: RG, SAG |
| Illuminating | 発光 | — |
| Newest Model | 最新モデル | — |
| Nightshade IR | ナイトシェード IR | category: RG |
| Nightshade IR and Contacts | ナイトシェードIRとコンタクト | armor_mods: RG |
| Padded | 急所保護 | — |
| Pulse Weave | パルス・ウィーブ | armor_mods: RG |
| Radiation Shielding | 放射線遮蔽 | armor_mods: RG |
| Rapid Transit: Diamond | ラピッド・トランジット：ダイヤモンド | armor_mods: RG |
| Rapid Transit: Elite | ラピッド・トランジット：エリート | armor_mods: RG |
| Rapid Transit: Platinum | ラピッド・トランジット：プラチナ | armor_mods: RG |
| Responsive Interface Gear: Armor | レスポンシブ・インターフェース・ギア(RIG)：アーマー | armor_mods: RG |
| Responsive Interface Gear: Helmet | レスポンシブ・インターフェース・ギア(RIG)：ヘルメット | — |
| Restrictive | 動きにくい | — |
| Ruthenium Polymer Coating | ルテニウム・ポリマー・コーティング | armor_mods: RG |
| SA Retiarius Net Gun | SA レティアルス・ネットガン | weapons: RG |
| Shock Weave | ショック・ウィーブ | armor_mods: RG |
| Silencer (PSK-3 Collapsible Heavy Pistol) | 消音器(PSK-3 折り畳み式ヘビーピストル) | weapon_accessories: RG |
| Specialty Armor | 専用の防具 | category: BB, CA, HS, HT, RG, SL |
| Universal Mirror Material | 自在反射材 | armor_mods: RG |
| Vindicator 200-Round Belt | ヴィンディケーター 200(ベルト) | weapon_accessories: RG |
| YNT Softweave Armor | YNT ソフトウィーブ・アーマー | armor_mods: RG |

## ja_curated_sr5.SR5 (20)

| English | 日本語 | 品目 |
|---|---|---|
| Animal Control (Insect Type) | 動物制御(Insect Type) | — |
| Combat Skill | 戦闘系能動技能 | — |
| Enhanced Senses (Ultrasound) | 強化感覚(生体ソナー) | — |
| Heavy [SR5] | 大型武器マウント | weapon_mounts: SR5 |
| Homunculus (Armored Material) | ホムンクルス(装甲素材／強化建材) | spirits: SR5 |
| Homunculus (Average Material) | ホムンクルス(平均的な素材) | spirits: SR5 |
| Homunculus (Cheap Material) | ホムンクルス(安手の素材) | spirits: SR5 |
| Homunculus (Fragile) | ホムンクルス(壊れやすい素材) | spirits: SR5 |
| Homunculus (Hardened Material) | ホムンクルス(特殊硬化材) | spirits: SR5 |
| Homunculus (Heavy Material) | ホムンクルス(強固な素材) | spirits: SR5 |
| Homunculus (Heavy Structural Material) | ホムンクルス(強固な建材) | spirits: SR5 |
| Homunculus (Reinforced Material) | ホムンクルス(強化素材) | spirits: SR5 |
| Homunculus (Structural Material) | ホムンクルス(建材) | spirits: SR5 |
| Manifest | 顕現 | — |
| Physical Skill | 身体系能動技能 | — |
| Psychokinesis (Infected) | 念動(Infected) | — |
| Social Skill | 社交系能動技能 | — |
| Standard [SR5] | 武器マウント | weapon_mounts: SR5 |
| Technical Skill | 技術系能動技能 | — |
| Vehicle Skill | ヴィークル系能動技能 | — |

## ja_curated_entities.ENTITIES (41)

| English | 日本語 | 品目 |
|---|---|---|
| (Synth)Leather | （合成）レザー | armor_mods: SR5 |
| Belt-Feed, 100-round | ベルト給弾, 100発 | weapon_accessories: SR5 |
| Berserker Temper | 狂戦士の気質 | — |
| Chemical Protection | 化学防護 | armor_mods: SR5 |
| Cyber Microgrenade Launcher | サイバー・マイクログレネードランチャー | — |
| Drum Magazine, 24-round | ドラムマガジン, 24発 | weapon_accessories: SR5 |
| Drum Magazine, 32-round | ドラムマガジン, 32発 | weapon_accessories: SR5 |
| Electrochromic Clothing | エレクトロクロミック・クロージング | armor_mods: SR5 |
| Essence Antihole | エッセンス・アンチホール | cyberware: SR5 |
| External Power Source | 外部電源 | weapon_accessories: SR5 |
| Fire Resistance | 耐火 | armor_mods: SR5 |
| Full Body Armor: Chemical Seal | フルボディアーマー：化学遮断 | armor_mods: SR5 |
| Full Body Armor: Environment Adaptation | フルボディアーマー：環境適応 | armor_mods: SR5 |
| Full Body Armor: Helmet | フルボディアーマー：ヘルメット | armor_mods: SR5 |
| Improved Potential (Chaos Mentor) | 潜在力強化：(混沌メンター) | — |
| Insulation | 断熱 | armor_mods: SR5 / bioware: CF |
| Liner - Chemical Protection (1) | ライナー - 化学防護 (1) | — |
| Liner - Chemical Protection (2) | ライナー - 化学防護 (2) | — |
| Liner - Chemical Protection (3) | ライナー - 化学防護 (3) | — |
| Liner - Chemical Protection (4) | ライナー - 化学防護 (4) | — |
| Liner - Chemical Protection (5) | ライナー - 化学防護 (5) | — |
| Liner - Chemical Protection (6) | ライナー - 化学防護 (6) | — |
| Liner - Fire Resistance (1) | ライナー - 耐火 (1) | — |
| Liner - Fire Resistance (2) | ライナー - 耐火 (2) | — |
| Liner - Fire Resistance (3) | ライナー - 耐火 (3) | — |
| Liner - Fire Resistance (4) | ライナー - 耐火 (4) | — |
| Liner - Fire Resistance (5) | ライナー - 耐火 (5) | — |
| Liner - Fire Resistance (6) | ライナー - 耐火 (6) | — |
| Liner - Insulation (1) | ライナー - 断熱 (1) | — |
| Liner - Insulation (2) | ライナー - 断熱 (2) | — |
| Liner - Insulation (3) | ライナー - 断熱 (3) | — |
| Liner - Insulation (4) | ライナー - 断熱 (4) | — |
| Liner - Insulation (5) | ライナー - 断熱 (5) | — |
| Liner - Insulation (6) | ライナー - 断熱 (6) | — |
| Nonconductivity | 非導電 | armor_mods: SR5 |
| Riposte | リポスト | martial_art_techniques: RG / powers: SG |
| Shock Frills | ショックフリル | armor_mods: SR5 |
| Silencer (Ares Light Fire 70) | 消音器（アレス・ライトファイア70） | weapon_accessories: SR5 |
| Silencer (Ares Light Fire 75) | 消音器（アレス・ライトファイア75） | weapon_accessories: SR5 |
| Thermal Damping | 熱感知抑制 | armor_mods: SR5 |
| Urban Explorer Jumpsuit: Helmet | アーバンエクスプローラー・ジャンプスーツ：ヘルメット | armor_mods: SR5 |

## import_ja_from_refs.CURATED (46)

| English | 日本語 | 品目 |
|---|---|---|
| Academic | 学術 | — |
| Acceleration | 加速値 | category: R5 |
| Acting | 演技 | — |
| Athletics | 運動 | — |
| Attributes | 能力値 | — |
| BTLs | BTLチップ | category: CF, SR5 |
| Biotech | 医療 | category: 2050, BB, CF, NF, SR5 |
| Body | 強靱力 | category: R5 |
| Close Combat | 近接戦闘 | — |
| Combat | 戦闘 | category: FA, HT, SG, SR5, SSP |
| Combat Active | 戦闘系能動技能 | category: SR5 |
| Conjuring | 召喚 | — |
| Cracking | クラッキング | — |
| Detection | 探知 | category: BB, CA, SG, SR5, SSP |
| Dwarf | ドワーフ | metatypes: SR5 |
| Electronics | エレクトロニクス | — |
| Elf | エルフ | metatypes: SR5 |
| Enchanting | 付術 | — |
| Foci | 収束具 | category: SR5 |
| Health | 身体 | category: FA, SG, SR5, SSP |
| Human | ヒューマン | metatypes: SR5 |
| Illusion | 幻影 | category: CA, SG, SR5, SS, SSP |
| Interest | 趣味 | — |
| Language | 言語 | — |
| Magical Active | 魔法系能動技能 | category: SR5 |
| Manipulation | 操作 | category: BB, BTB, CA, FA, HT, SG, SR5, SS, SSP |
| Metahuman | メタヒューマン | category: RF, SR5 |
| Mundane | マンディン | category: SR5 |
| Ork | オーク | metatypes: SR5 |
| Outdoors | 野外 | — |
| Physical Active | 身体系能動技能 | category: SR5 |
| Power Point | パワー・ポイント | metamagics: SR5 |
| Professional | 職業 | — |
| Resonance Active | 共振力系能動技能 | category: SR5 |
| Rigger Interface | リガー・コマンド・インターフェース | vehicle_mods: SR5 |
| Run and Gun | ラン＆ガン | — |
| Services | 助力 | category: RF |
| Shadowrun 5th Edition | シャドウラン 第5版 | — |
| Social | 社交 | — |
| Social Active | 社交系能動技能 | category: SR5 |
| Sorcery | 魔術 | — |
| Street | 街 | lifestyles: SR5 |
| Tasking | タスキング | — |
| Technical Active | 技術系能動技能 | category: SR5 |
| Troll | トロール | metatypes: SR5 |
| Vehicle Active | ヴィークル系能動技能 | category: SR5 |

## chumJA(SR4) category (49)

| English | 日本語 | 品目 |
|---|---|---|
| All | すべて | category: R5, RF, SS |
| Ammunition | 弾薬 | category: 2050, HAMG, HT, KC, KK, NF, R5, RG, SAG, SL, SOTG, SR5, TSG |
| Animals | 動物 | category: PZG |
| Autosofts | オートソフト | category: R5, SR5 |
| Basic | 標準 | category: 2050, CF, DTR, HT, KC, NF, SR5 |
| Bikes | バイク | category: 2050, HAMG, HT, R5, SAG, SOTG, SR5, TCT |
| Bodyware | ボディウェア | category: 2050, CF, HT, SR5, TCT |
| Cars | 自動車 | category: 2050, KK, R5, SAG, SHB, SHB3, SOTG, SR5, SS, TCT |
| Chemicals | 化学薬品 | category: 2050, CA, HT, SR5 |
| Commlink Accessories | コムリンク・アクセサリ | category: DT, KC, SR5 |
| Cosmetic | 美容整形 | category: 2050, HT, R5, SR5, TCT |
| Crossbows | クロスボウ | category: RG, SL, SR5 |
| Cultured | 培養 | category: 2050, CF, HT, SR5 |
| Cyberdecks | サイバーデッキ | category: 2050, DT, HKS, KC, LCD, SAG, SPS, SR5 |
| Cyberlimb | サイバーリム | category: 2050, CF, SR5 |
| Cyberlimb Accessory | サイバーリム・アクセサリ | category: BB, HT, SR5 |
| Cyberlimb Enhancement | サイバーリム強化 | category: CF, HT, R5, SR5 |
| Cyberterminals | サイバーターミナル | category: HKS |
| Cyberweapon | サイバー武器 | — |
| Drugs | ドラッグ | category: 2050, BB, CF, DTR, LCD, SAG, SR5, SS, TVG |
| Earware | イアウェア | category: 2050, CF, SR5 |
| Exotic Melee Weapons | 特殊近接武器 | category: CA, HAMG, NF, RG, SL, SR5 |
| Exotic Ranged Weapons | 特殊射撃武器 | category: CA, HT, LCD, RG, SL, SLG2, SOTG, SR5 |
| Explosives | 爆発物 | category: 2050, RG, SR5 |
| Eyeware | アイウェア | category: 2050, CF, SR5 |
| Free Spirit | 自由精霊 | — |
| Headware | ヘッドウェア | category: 2050, CF, KC, NF, SR5 |
| Heavy Machine Guns | ヘビーマシンガン | category: KK, RG, SL, SOTG, SR5 |
| Hovercraft | ホバークラフト | category: SAG |
| ID/Credsticks | ID/クレッドスティック | category: 2050, SR5 |
| Laser Weapons | レーザー武器 | category: HT, LCD, RG |
| Magical Compounds | 魔法化合物 | category: FA, PBG, SG |
| Magical Supplies | 魔法用品 | category: 2050, CA, FA, HT, PGG, SG, SR5, SSP |
| Medium Machine Guns | ミディアムマシンガン | category: RG, SR5 |
| Nanocybernetics | ナノサイバーウェア | category: CF |
| Negative | 不利 | category: AP, BB, BTB, CA, CF, DT, HT, KC, NF, R5, RF, RG, SAG, SFB, SFCR, SG, SL, SR5, TCT, TSG |
| Paranormal | 超常生物 | category: SR5 |
| Positive | 有利 | category: AP, BB, BTB, CA, CF, DT, DTR, FA, HS, HT, KC, NF, R5, RF, RG, SASS, SFB, SG, SL, SR5, TCT |
| RFID Tags | RFIDタグ | category: SR5 |
| Rotorcraft | 回転翼機 | category: 2050, NF, R5, SAG, SFME, SHB3, SR5 |
| Security Devices | セキュリティ機器 | category: 2050, SR5 |
| Sensors | センサー | category: CA, NF, SR5 |
| Shapeshifter | シェイプシフター | category: RF, SAG |
| Skillsofts | スキルソフト | category: SR5 |
| Tools | 工具 | category: 2050, NF, RF, SR5 |
| Toxins | 毒物 | category: 2050, BB, BTB, HT, PZG, SR5, SRM0803, SRM0804, SS |
| Trucks | トラック | category: 2050, KK, NF, R5, SAG, SHB, SHB3, SLG7, SOTG, SR5, SS |
| Unarmed | 素手 | category: HT, SL, SR5 |
| Weakness | 弱点 | — |

## chumJA(SR4) name (131)

| English | 日本語 | 品目 |
|---|---|---|
| Aboriginal | アボリジニ | traditions: SSP |
| Alleviate Nausea | 悪心緩和 | spells: SSP |
| Alligator | アリゲーター | mentors: HT |
| Ally Conjuration | 同盟精霊召霊術 | spells: SG |
| Ally Spirit | 同盟精霊 | spirits: SG |
| Alter Memory | 記憶改変 | spells: SSP |
| Anaphylaxis | 過敏症 | — |
| Animal Empathy | 動物共感 | powers: SG / qualities: RF |
| Astral Armor | アストラルの鎧 | spells: SSP |
| Attention Coprocessor | 注意力コプロセッサ | cyberware: CF |
| Aura Masking | オーラ擬態 | — |
| Balance Tail | 安定尾 | cyberware: CF |
| Banishing Resistance | 放逐抵抗 | — |
| Bat | コウモリ | mentors: HT |
| Boar | イノシシ | mentors: HS |
| Cannibalize | 貪肉術 | metamagics: SG |
| Caretaker Spirit | 昆虫精霊(世話役) | spirits: SG |
| Chameleon Skin | カメレオン・スキン | bioware: CF |
| Chemical Seal | 化学遮断 | armor_mods: SR5 |
| Chicken | ニワトリ | gear: RF |
| Clean Metabolism | クリーン代謝系 | bioware: CF |
| Colt Manhunter | コルト マンハンター | weapons: SFM |
| Commanding Voice | 命令の声 | powers: SS |
| Control Emotions | 感情制御 | spells: SSP |
| Corruption | 堕落術 | metamagics: SG |
| Coyote | コヨーテ | mentors: SFCC |
| Cybergland | サイバー分泌腺 | cyberware: HT |
| Dark King | 冥王 | mentors: FA |
| Deathly Aura | 死のオーラ | — |
| Desire Reflection | 欲望投影 | — |
| Devouring | 貪食 | — |
| Dietware | ダイエットウェア | bioware: CF |
| Divining | 啓示 | — |
| Dolphin | イルカ | mentors: HS |
| Echolocation | 反響定位 | — |
| Egyptian | エジプト | traditions: SSP |
| Eidetic Sense Memory | 感覚記憶 | powers: SSP |
| Empathy | 共感 | — |
| Endowment | パワー付与 | — |
| Energy Drain | エネルギー吸収 | — |
| Enthralling Performance | 美技披露 | powers: SSP |
| Essence Hole | エッセンスの穴 | cyberware: SR5 |
| Evanescence | 消失 | — |
| External Clip Port | 外部装弾口 | cyberware: SR5 |
| Feedback Clothing | フィードバック・クロージング | armor_mods: SR5 |
| Foot Anchor | 脚底アンカー | cyberware: CF |
| Fox | キツネ | mentors: SAG |
| Geomancy | 地霊術 | magic_arts: SG |
| Gills | 鰓 | bioware: CF |
| Giraffe | キリン | mentors: HS |
| Gliding | 滑走 | — |
| Grapple Hand | グラップルハンド | cyberware: CF |
| Great Mother | 太母 | mentors: SASS |
| Guardian Spirit | 護りの精霊 | spirits: SG |
| Guidance Spirit | 導きの精霊 | spirits: SG |
| Healthy Glow | 健康美 | spells: SSP |
| Hidden Life | 隠された生命 | — |
| Hive Mind | 群体連結 | — |
| Horse | ウマ | mentors: HS |
| Incubus | インキュバス | spells: CA |
| Infirm | 虚弱 | qualities: RF |
| Inhabitation | 侵食 | — |
| Iron Gut | 鋼の胃袋 | powers: SSP |
| Iron Lungs | 鋼の肺 | powers: SSP |
| Iron Will | 鋼の意思 | powers: SSP |
| Leeching | 搾取術 | spells: SG |
| Light | 光 | spells: SR5 / weapon_mounts: R5 |
| Lion | ライオン | mentors: BOTL |
| Magemask | メイジマスク | gear: SG |
| Magic Sense | 魔力感知 | metatypes: RF / powers: SG / qualities: RF |
| Magical Guard | 魔法の守護 | — |
| Magical Theory | 魔法理論 | — |
| Master Shedim | マスター・シェディム | spirits: SG |
| Math SPU | 算術SPU | cyberware: CF |
| Metahuman Form | 人間形態 | — |
| Micro Flare Launcher | 照明弾ピストル | gear: SR5 |
| Mind Link | 精神連結 | — |
| Mob Mood | 集団感情制御 | spells: SSP |
| Music | 音楽 | — |
| Mutable Form | きまぐれな姿 | — |
| Mutagen | 変異原 | — |
| Naga | ナーガ | — |
| Nodachi | ノダチ | weapons: SL |
| Norse | 北欧 | traditions: SSP |
| Nunchaku | ヌンチャク | weapons: SL |
| Nymph Spirit | 昆虫精霊(幼虫) | spirits: SG |
| Oak | 樫 | mentors: FA |
| Paragon | パラゴン | qualities: KC |
| Personal Domain | 独自ドメイン | — |
| Pestilence | 疫病 | — |
| Piercing Senses | 透徹感覚 | powers: SSP |
| Pig | ブタ | mentors: SAG |
| Pixie | ピクシー | — |
| Poisoner | 汚染者 | qualities: HT |
| Possession | 憑依 | — |
| Power Bleed | パワー奪取 | metamagics: SG |
| Psionic | サイオニック | traditions: SSP |
| Quake | 地震 | — |
| Raccoon | アライグマ | mentors: HS |
| Radar Sensor | レーダー・センサー | cyberware: CF |
| Rappelling Gloves | ラペリング・グローブ | gear: SR5 |
| Realistic Form | リアルな外見 | — |
| Reinforcement | 強化 | — |
| Sacrifice | 供犠 | metamagics: SG |
| Sasquatch | サスカッチ | — |
| Satellite Link | 衛星リンク | gear: SR5 / vehicle_mods: R5 |
| Scout Spirit | 昆虫精霊(斥候役) | spirits: SG |
| Seal | アザラシ | mentors: SAG |
| Sense Link | 感覚連結 | — |
| Shadow Cloak | 影の衣 | — |
| Shedim | シェディム | spirits: SG |
| Silence | 静寂 | buyable_critter_powers: SG / spells: SR5 |
| Siren | サイレン | vehicle_mods: SS |
| Skill Enhancement | 技能強化 | — |
| Smuggling Compartment | 密輸用容器 | cyberware: SR5 / vehicle_mods: R5 |
| Soldier Spirit | 昆虫精霊(兵士役) | spirits: SG |
| Sonic Projection | 音響投射 | — |
| Sound Link | 音声リンク | cyberware: SR5 / optics: RF |
| Spider | クモ | mentors: HS |
| Spirit Pact | 精霊の契約 | spells: SG |
| Standard | スタンダード | bioware: SR5 / cyberware: SR5 / drug_component_grades: CF / weapon_mounts: R5 |
| Storm | 嵐 | — |
| Sun | 太陽 | mentors: FA |
| Taint | 汚染術 | metamagics: SG |
| Task Spirit | 労役の精霊 | spirits: SG |
| Tonfa | トンファー | weapons: SL |
| Touch Link | 触覚リンク | cyberware: CF |
| Wall Walking | 壁歩き | — |
| Wealth | 富 | — |
| Worker Spirit | 昆虫精霊(労働者役) | spirits: SG |
| [Sense] Link | [感覚]連結 | spells: SSP |

## 本ごとの訳の出どころ

名前の数。1 つの名前が複数の本に載っていれば、それぞれの本で数える。

| 本 | 書名 | 日本語版 | 上流 | data.json | コデックス | 英語のまま |
|---|---|---|---|---|---|---|
| SR5 | Shadowrun 5th Edition | あり | 931 | 105 | 0 | 53 |
| RF | Run Faster |  | 17 | 12 | 6 | 726 |
| CF | Chrome Flesh |  | 5 | 27 | 15 | 497 |
| RG | Run and Gun | あり | 427 | 34 | 0 | 14 |
| R5 | Rigger 5.0 |  | 7 | 17 | 0 | 362 |
| 2050 | Shadowrun 2050 (German-Only) |  | 14 | 23 | 0 | 341 |
| SG | Street Grimoire |  | 137 | 34 | 0 | 181 |
| FA | Forbidden Arcana |  | 4 | 9 | 0 | 262 |
| KC | Kill Code |  | 1 | 8 | 3 | 199 |
| HT | Hard Targets |  | 10 | 23 | 11 | 158 |
| DT | Data Trails |  | 2 | 16 | 2 | 180 |
| SL | Street Lethal |  | 16 | 12 | 0 | 137 |
| SAG | State of the Art ADL (German-Only) |  | 8 | 14 | 0 | 142 |
| CA | Cutting Aces |  | 7 | 12 | 0 | 111 |
| SS | Stolen Souls |  | 13 | 9 | 0 | 60 |
| SSP | Shadow Spells |  | 2 | 23 | 0 | 49 |
| KK | Krime Katalog |  | 10 | 4 | 0 | 57 |
| SOTG | Datapuls SOTA 2080 (German-Only) |  | 6 | 6 | 0 | 59 |
| DTR | Dark Terrors |  | 2 | 3 | 0 | 63 |
| NF | No Future |  | 2 | 11 | 0 | 53 |
| HS | Howling Shadows |  | 12 | 8 | 0 | 42 |
| PBG | Parabotany (German-Only) |  | 1 | 1 | 0 | 45 |
| BTB | Better Than Bad |  | 0 | 4 | 2 | 40 |
| GH3 | Gun Heaven 3 |  | 11 | 0 | 0 | 34 |
| BB | Bullets & Bandages |  | 0 | 9 | 0 | 35 |
| TCT | The Complete Trog |  | 3 | 6 | 0 | 30 |
| LCD | Lockdown |  | 0 | 4 | 0 | 27 |
| SHB | Schattenhandbuch (German-Only) |  | 3 | 2 | 0 | 23 |
| PGG | Parageology (German-Only) |  | 0 | 1 | 0 | 23 |
| HAMG | Datapuls Hamburg (German-Only) |  | 2 | 3 | 0 | 18 |
| HKS | Hong Kong Sourcebook |  | 0 | 2 | 0 | 17 |
| QSR | Shadowrun Quick-Start Rules |  | 0 | 0 | 0 | 17 |
| SFB | Shadows In Focus: Butte |  | 0 | 2 | 0 | 10 |
| TSG | The Seattle Gambit |  | 1 | 2 | 0 | 9 |
| SHB2 | Schattenhandbuch 2 (German-Only) |  | 3 | 0 | 0 | 8 |
| SHB3 | Schattenhandbuch 3 (German-Only) |  | 0 | 3 | 0 | 8 |
| SFCR | Shadows In Focus: Casablanca-Rabat |  | 0 | 1 | 0 | 9 |
| AP | Assassin's Primer |  | 1 | 2 | 0 | 6 |
| PZG | Parazoology (German-Only) |  | 0 | 2 | 0 | 7 |
| SASS | Sail Away, Sweet Sister |  | 4 | 2 | 0 | 3 |
| SFME | Shadows In Focus: Metropole |  | 0 | 1 | 0 | 7 |
| TCG |  |  | 0 | 0 | 0 | 7 |
| BOTL | Book of the Lost |  | 0 | 1 | 0 | 4 |
| SFMO | Shadows In Focus: Morocco |  | 0 | 0 | 0 | 5 |
| SLG3 | Schattenload 3 (German-Only) |  | 0 | 0 | 0 | 5 |
| SOXG | Datapuls SOX 2080 (German-Only) |  | 0 | 0 | 0 | 4 |
| TVG | The Vladivostok Gauntlet |  | 0 | 1 | 0 | 3 |
| DTD | Data Trails (Dissonant Echoes) |  | 0 | 0 | 0 | 3 |
| SGE | Street Grimoire Errata |  | 2 | 0 | 0 | 1 |
| SLG2 | Schattenload 2 (German-Only) |  | 0 | 1 | 0 | 2 |
| SLG7 | Schattenload 7 (German-Only) |  | 0 | 1 | 0 | 2 |
| DATG | Datapuls Österreich (German-Only) |  | 0 | 0 | 0 | 2 |
| GRST2019 | Der Almanach – Gratisrollenspieltag 2019 (German-Only) |  | 0 | 0 | 0 | 2 |
| NP | Nothing Personal |  | 0 | 0 | 0 | 2 |
| SFM | Shadows In Focus: San Francisco Metroplex |  | 1 | 1 | 0 | 0 |
| SHB4 | Schattenhandbuch 4 (German-Only) |  | 1 | 0 | 0 | 1 |
| SPS | Splintered State |  | 0 | 1 | 0 | 1 |
| SRM0803 | Shadowrun Missions 0803: 10 Block Tango |  | 0 | 1 | 0 | 1 |
| SRM0804 | Shadowrun Missions 0804: Dirty Laundry |  | 0 | 1 | 0 | 1 |
| BLB | Bloody Business |  | 0 | 0 | 0 | 1 |
| GE | Grimmes Erwachen (German-Only) |  | 0 | 0 | 0 | 1 |
| SFCC | Shadows In Focus: Sioux Nation: Counting Coup |  | 0 | 1 | 0 | 0 |

