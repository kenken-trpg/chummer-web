# 用語集 vs 既存訳 — 不一致レポート

**自動生成** — `backend/scripts/build_ja_glossary.py`。
採用形は sr5eja > 2021版 > 手動確定 override。文脈依存・固有名は個別判断。

## A. コア用語 (ja-jp.xml + ui.json vs 用語集)

不一致: **0 件**

| English | 用語集 | キー | 現在値 | 一致 |
|---|---|---|---|---|
| Body | 強靱力 | `String_AttributeBODLong` | 強靱力 | ✅ |
| BOD | 強靱 | `String_AttributeBODShort` | 強靱 | ✅ |
| Agility | 敏捷力 | `String_AttributeAGILong` | 敏捷力 | ✅ |
| AGI | 敏捷 | `String_AttributeAGIShort` | 敏捷 | ✅ |
| Reaction | 反応力 | `String_AttributeREALong` | 反応力 | ✅ |
| REA | 反応 | `String_AttributeREAShort` | 反応 | ✅ |
| Strength | 筋力 | `String_AttributeSTRLong` | 筋力 | ✅ |
| STR | 筋力 | `String_AttributeSTRShort` | 筋力 | ✅ |
| Willpower | 意志力 | `String_AttributeWILLong` | 意志力 | ✅ |
| WIL | 意志 | `String_AttributeWILShort` | 意志 | ✅ |
| Logic | 論理力 | `String_AttributeLOGLong` | 論理力 | ✅ |
| LOG | 論理 | `String_AttributeLOGShort` | 論理 | ✅ |
| Intuition | 直観力 | `String_AttributeINTLong` | 直観力 | ✅ |
| INT | 直観 | `String_AttributeINTShort` | 直観 | ✅ |
| Charisma | 魅力 | `String_AttributeCHALong` | 魅力 | ✅ |
| CHA | 魅力 | `String_AttributeCHAShort` | 魅力 | ✅ |
| Edge | エッジ | `String_AttributeEDGLong` | エッジ | ✅ |
| EDG | エッジ | `String_AttributeEDGShort` | エッジ | ✅ |
| Magic | 魔力 | `String_AttributeMAGLong` | 魔力 | ✅ |
| MAG | 魔力 | `String_AttributeMAGShort` | 魔力 | ✅ |
| Resonance | 共振力 | `String_AttributeRESLong` | 共振力 | ✅ |
| RES | 共振 | `String_AttributeRESShort` | 共振 | ✅ |
| Essence | エッセンス | `String_AttributeESSLong` | エッセンス | ✅ |
| Essence | エッセンス | `String_AttributeESSShort` | エッセンス | ✅ |

## B. ja-jp.xml — 英語原文が用語集見出しと一致し訳が違うもの

| English | 用語集 | ja-jp.xml キー | 現在値 |
|---|---|---|---|
| Add | 追加 | `Button_Add` | Add |
| Delete Mod | 改造・モジュールを削除 | `Button_DeleteMod` | Delete Mod |
| Active | 能動 | `Checkbox_Active` | 有効 |
| armor | 装甲 | `Checkbox_CreatePACKSKit_Armor` | 防具 |
| Martial Arts | 格闘技 | `Checkbox_CreatePACKSKit_MartialArts` | マーシャルアーツ（仮訳） |
| Active | 能動 | `Checkbox_DetectionSpell4` | 有効 |
| Equipped | 装備中 | `Checkbox_Equipped` | 装備済み |
| Mental | 精神 | `Checkbox_ManipulationSpell2` | 精神操作 |
| Physical | 物理 | `Checkbox_ManipulationSpell3` | 物理操作 |
| Action | アクション | `ColumnHeader_Action` | 行動 |
| Base | 基本 | `Label_Base` | 自然 |
| Physical | 物理 | `Label_CMPhysical` | 身体 |
| Help | ヘルプ | `Label_Help` | Help |
| complex form | 複合体 | `Label_Options_BPComplexForm` | 複合体のレーティング |
| Spells | 呪文 | `Label_SelectedSpells` | 習得した呪文 |
| Broken | 破壊 | `Label_SkillGroup_Broken` | Broken |
| Rituals | 儀式呪文 | `Label_SummaryRituals` | 儀式 |
| Delete Item | アイテムを削除 | `MessageTitle_Delete` | アイテムの削除 |
| Power Level | レベル | `MessageTitle_PowerLevel` | パワーレベル |
| Physical | 物理 | `Node_Physical` | 身体 |
| bioware | バイオウェア | `Node_SelectedBioware` | 埋め込んでいるバイオウェア |
| Combat Spells | 戦闘呪文 | `Node_SelectedCombatSpells` | 習得した戦闘呪文 |
| Cyberware | サイバーウェア | `Node_SelectedCyberware` | 埋め込んでいるサイバーウェア |
| Detection Spells | 探知呪文 | `Node_SelectedDetectionSpells` | 習得した探知呪文 |
| Rituals | 儀式呪文 | `Node_SelectedGeomancyRituals` | Selected Geomancy Rituals |
| Health Spells | 身体呪文 | `Node_SelectedHealthSpells` | 習得した身体呪文 |
| Illusion Spells | 幻影呪文 | `Node_SelectedIllusionSpells` | 習得した幻影呪文 |
| Manipulation Spells | 操作呪文 | `Node_SelectedManipulationSpells` | 習得した操作呪文 |
| Martial Arts | 格闘技 | `Node_SelectedMartialArts` | 習得した格闘技 |
| Action | アクション | `Power_SortAction` | Action |
| Amount | 数量 | `String_Amount` | 金額 |
| Blitz | 速攻 | `String_Blitz` | Blitz |
| Bullet | ラウンド | `String_Bullet` | Bullet |
| Bullets | ラウンド | `String_Bullets` | Bullets |
| Capacity | 容量 | `String_Capacity` | Capacity |
| Career Karma | 通算カルマ | `String_CareerKarma` | 累計カルマ |
| Contacts | コンタクト | `String_Contacts` | Contacts |
| Essence | エッセンス | `String_DescEssence` | Essence |
| Mental | 精神 | `String_DescMental` | 精神操作 |
| Device Rating | 機器RTG | `String_DeviceRating` | 機器レーティング |
| Roll | ロール | `String_DiceRoller_Roll` | 振る |
| Grade | 等級 | `String_Grade` | 階梯 |
| Import Character | キャラクターをインポートする | `String_ImportCharacter` | Import Character |
| lifestyle | ライフスタイル | `String_Lifestyle` | (未訳) |
| Physical | 物理 | `String_LimitPhysicalShort` | 身体 |
| Metamagics | メタマジック | `String_Metamagics` | Metamagics |
| Barrel | バレル | `String_MountBarrel` | 銃身 |
| Internal | 内蔵 | `String_MountInternal` | Internal |
| None | 無し | `String_MountNone` | None |
| Side | サイド | `String_MountSide` | Side |
| Top | トップ | `String_MountTop` | 銃身上部 |
| program | プログラム | `String_Program` | Program |
| Push The Limit | 限界突破 | `String_PushTheLimit` | Push the Limit |
| quality | 資質 | `String_Quality` | Quality |
| RC | 反動補正RC | `String_RC` | RC |
| ritual | 儀式 | `String_Ritual` | 儀式＠ |
| Second Chance | 振り直し | `String_SecondChance` | Second Chance |
| armor | 装甲 | `String_SelectPACKSKit_Armor` | 装甲値 |
| Source | 資料 | `String_Source` | Source |
| Extended | 継続 | `String_SpellExtended` | 拡張 |
| Tradition | 様式 | `String_Tradition` | Tradition |
| General | 一般 | `String_VehicleModCategory_General` | (未訳) |
| Wireless | ワイヤレス | `String_Wireless` | Wireless |
| Initiation | 階梯 | `Tab_Initiation` | イニシエーション |
| Notes | 備考 | `Tab_Notes` | ノート |
| Description | 解説 | `Tab_Roster_Description` | Description |
| armor | 装甲 | `Tip_Armor` | 装甲値 |
| Notes | 備考 | `Title_Notes` | ノート |

## C. ja-jp_data.xml — エンティティ名・カテゴリが用語集見出しと一致するもの

| English | 用語集 | 種別 | 現在値 |
|---|---|---|---|
| Acceleration | 加速値 | name | Acceleration |
| adept power | アデプト・パワー | name | アデプトパワー |
| Control Rig | コントロール・リグ | name | 制御リグ |
| Defender | 防御側 | name | Defender |
| Dodge | 回避 | name | Dodge |
| Immunity | 完全耐性 | name | 耐性 |
| Internal | 内蔵 | name | Internal |
| Judge Intentions | 意図を測る | name | 意図をはかるテスト |
| Manual | 手動 | name | Manual |
| Memory | 記憶 | name | 記憶テスト |
| Mental Limit | 精神リミット | name | Mental Limit |
| Mundane | マンディン | name | Mundane |
| Name | 名前 | name | Name |
| None | 無し | name | None |
| Physical Limit | 身体リミット | name | Physical Limit |
| Public Grid | 公共グリッド | name | 公共っグリッド |
| Resist | 抵抗 | name | Resist |
| skill | 技能 | name | Skill |
| Social Limit | 社交リミット | name | Social Limit |
| armor | 装甲 | category | 防具 |
| Attributes | 能力値 | category | Attributes |
| Block | ブロック | category | Block |
| Body | 強靱力 | category | 強靭力 |
| Mundane | マンディン | category | マンデイン |
| Resonance | 共振力 | category | Resonance |
| ritual | 儀式 | category | Ritual |
| Rituals | 儀式呪文 | category | 儀式 |
| Services | 助力 | category | Services |

## D. shadowrun5eja が訳出済みで ui.json 未収録の用語 (seed 候補)

Foundry SR5e 日本語化 (github.com/MiyabiRouga/shadowrun5eja) が訳している UI・ルール語のうち、当方の `ui.json` に無いもの。訳語は shadowrun5eja を直接参照。

| English | 2021版 |
|---|---|
| Accessory |  |
| Action |  |
| Action Type |  |
| Action Type None |  |
| Action Type Varies |  |
| Active Defense |  |
| Add Ammo |  |
| Add Five To Overwatch |  |
| Add One To Overwatch |  |
| Add Skill |  |
| adept power |  |
| Agent |  |
| Ammo Full |  |
| Ammo Gel Rounds |  |
| Aoe |  |
| Apply Wounds |  |
| Armor Hardened |  |
| Armor Hardened Full |  |
| Attack | アタック |
| Attacker |  |
| Attacker Hits |  |
| Attacker Net Hits |  |
| Attr Intuition |  |
| Availability |  |
| Awakened |  |
| Awakened Emerged |  |
| Barrel |  |
| Base |  |
| Base Value |  |
| Biofeedback Damage |  |
| Biography |  |
| Blast Radius |  |
| Blitz |  |
| Block |  |
| Bonus |  |
| Bonuses |  |
| Broken |  |
| Bullet |  |
| Bullet Count |  |
| Bullets |  |
| Buy Hits |  |
| call in action |  |
| Can Default |  |
| Capacity |  |
| Career Karma |  |
| character |  |
| Clear Marks |  |
| Collapse |  |
| Collapse All |  |
| Common Program |  |
| Conceal |  |
| Connect To Network |  |
| Connection | コネ値 |
| contact | コンタクト |
| Contact Type |  |
| Continue |  |
| Control Rig |  |
| Cover |  |
| Create |  |
| critter power |  |
| Cyberware Grade |  |
| Cyberware Grade Alpha |  |
| Cyberware Grade Beta |  |
| Cyberware Grade Delta |  |
| Cyberware Grade Gamma |  |
| Cyberware Grade Grey |  |
| Cyberware Grade Standard |  |
| Cyberware Grade Used |  |
| Damage | ダメージ(DV) |
| Damage Replace |  |
| Damage Type | ダメージタイプ |
| Default Category Visibility |  |
| Defender |  |
| Defender Net Hits |  |
| Defense | 回避 |
| Defense Test |  |
| Delete Ammo |  |
| Delete Item |  |
| Delete License |  |
| Delete Mod |  |
| Delete Skill |  |
| Description |  |
| Descriptors |  |
| Details |  |
| Detection Spell Extended |  |
| device | 機器 |
| Device Cat Cyberdeck |  |
| Device Type |  |
| Direct Connection |  |
| Dmg Type Matrix |  |
| Dodge |  |
| Dont Apply Wounds |  |
| Drain | ドレイン |
| Drain Attribute |  |
| Drain Value |  |
| Dropoff |  |
| Duck Or Cover |  |
| Duration | 効果時間 |
| Duration Instant |  |
| Edit Ammo |  |
| Edit Item |  |
| Edit Skill |  |
| Effect |  |
| Effects |  |
| Emerged |  |
| Environment High |  |
| Environment Low |  |
| Environment Medium |  |
| Environment Modifier |  |
| Environment None |  |
| Environment Very High |  |
| Expand |  |
| Expand All |  |
| Extend |  |
| Extended |  |
| Extended Hits |  |
| Extended Test |  |
| Fade |  |
| Fade Attribute |  |
| Fade Value |  |
| Filter |  |
| Fire Mode |  |
| Full Defense |  |
| Full Defense Attribute |  |
| Full Matrix Defense |  |
| Glitch |  |
| Glitch Critical |  |
| Glitches |  |
| Good Cover |  |
| grid |  |
| Grids |  |
| Hacking Program |  |
| Hardened Armor |  |
| Help |  |
| Hits |  |
| Hot Sim |  |
| Immunity |  |
| Immunity To Normal Weapons |  |
| Import Character |  |
| Incoming Damage |  |
| Incoming Drain |  |
| Incoming Fade |  |
| Information |  |
| Init Cat Matrix |  |
| Internal |  |
| Is Critter |  |
| Is Grunt |  |
| Item Mod |  |
| Item Name |  |
| Knocked Down |  |
| Knowledge Skill Academic |  |
| Knowledge Skill Interests |  |
| Knowledge Skill Professional |  |
| Knowledge Skill Street |  |
| Languages |  |
| Last Roll |  |
| License |  |
| Licenses |  |
| Lifestyle Comforts |  |
| Lifestyle Guests |  |
| Lifestyle High |  |
| Lifestyle Low |  |
| Lifestyle Luxory |  |
| Lifestyle Middle |  |
| Lifestyle Neighborhood |  |
| Lifestyle Security |  |
| Lifestyle Squatter |  |
| Lifestyle Street |  |
| Lifestyle Type |  |
| Limit Mental |  |
| Limit Physical |  |
| Limit Social |  |
| Load |  |
| Loaded | 装填 |
| Loyalty | 忠実値 |
| Magic | 魔力 |
| Manual |  |
| Manual Override |  |
| Marks |  |
| Matrix Defense |  |
| Matrix Full Defense Attribute |  |
| Matrix Target |  |
| Melee Weapon Attack |  |
| Mental Limit | 精神リミット |
| Migration Complete |  |
| Mod Points |  |
| modification |  |
| Modification Categories |  |
| Modification Category |  |
| Modification Slots |  |
| Modified |  |
| Modified Armor |  |
| Modified Damage |  |
| Modified Drain |  |
| Modified Fade |  |
| Modify Roll |  |
| Mount Point |  |
| Move Item Inventory |  |
| Movement | 移動 |
| Mundane |  |
| Net Hits |  |
| New |  |
| No Cover |  |
| Normal |  |
| Normal Skill Button |  |
| Normal Spell Button |  |
| Not Extended |  |
| Notoriety | 悪名 |
| Open Network Manager |  |
| Open Origin |  |
| Opposed Type |  |
| Opposing Hits |  |
| Opposing Net Hits |  |
| Original Dice Pool |  |
| Out Of Range |  |
| Overflow |  |
| Override |  |
| Overwatch Score |  |
| Owner |  |
| Parry |  |
| Partial Cover |  |
| Physical Limit | 身体リミット |
| Physical Track | 身体ダメージトラック |
| Place Template |  |
| Plus Fifteen Minutes |  |
| Power Type |  |
| Program Type |  |
| Public Awareness | 公的認知度 |
| Public Grid |  |
| Push The Limit |  |
| Qty | 数量 |
| Quality Type |  |
| Quality Type Life Module |  |
| Quality Type Negative |  |
| Quality Type Positive |  |
| Quantity |  |
| Range Weapon Attack |  |
| Reagent |  |
| Reckless Spell Button |  |
| Recoil |  |
| Recoil Compensation |  |
| Refresh |  |
| Remove Bonus |  |
| Remove Specialization |  |
| Resist |  |
| Restore Default Skills |  |
| Result Override |  |
| Result Override Glitches |  |
| Result Override Hits |  |
| Right Click To Clear |  |
| Roll |  |
| Roll Composure |  |
| Roll Custom |  |
| Roll Defense |  |
| Roll Drain |  |
| Roll Fade |  |
| Roll Judge Intentions |  |
| Roll Lift Carry |  |
| Roll Memory |  |
| Roll Mode |  |
| Roll Soak |  |
| Rounds Remaining |  |
| Run |  |
| Running Silent |  |
| Running Speed |  |
| Same Grid |  |
| Second Attribute |  |
| Second Chance |  |
| Selected Targets |  |
| Sheet Actor |  |
| Sheet Item |  |
| Side |  |
| Situational Modifier |  |
| Soak |  |
| Soak Test |  |
| Social Limit | 社交リミット |
| Source |  |
| Spare Clips |  |
| sprite power |  |
| Stun Track | 精神ダメージトラック |
| Suppressing |  |
| Target | 対象 |
| Target Device |  |
| Temporary |  |
| Temporary Modifiers |  |
| Test |  |
| Threshold |  |
| Toggle Active |  |
| Toggle Breakdown |  |
| Toggle Equip |  |
| Toggle Wireless |  |
| Top |  |
| Total | 合計 |
| Under Barrel |  |
| Value |  |
| vehicle | ヴィークル |
| Walk |  |
| Walking Speed |  |
| Wireless |  |
| Wireless Offline |  |
| Wireless Online |  |
| Wireless Unavailable |  |

