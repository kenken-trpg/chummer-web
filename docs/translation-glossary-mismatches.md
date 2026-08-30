# 用語集 vs 既存訳 — 不一致レポート

**自動生成** — `backend/scripts/build_ja_glossary.py`。
Phase 2 で採用形を決める際の作業リスト。用語集 (2021) を正とするが、
固有名・文脈依存の差は個別判断すること。

## A. コア用語 (ja-jp.xml キー明示マッピング)

不一致: **9 件**


| English | 用語集 (2021) | ja-jp.xml キー | 現在値 | 一致 |
|---|---|---|---|---|
| Body | 強靱力 | `String_AttributeBODLong` | 強靭力 | ❌ |
| BOD | 強靱 | `String_AttributeBODShort` | 強靭力 | ❌ |
| Agility | 敏捷力 | `String_AttributeAGILong` | 敏捷力 | ✅ |
| AGI | 敏捷 | `String_AttributeAGIShort` | 敏捷力 | ❌ |
| Reaction | 反応力 | `String_AttributeREALong` | 反応力 | ✅ |
| REA | 反応 | `String_AttributeREAShort` | 反応力 | ❌ |
| Strength | 筋力 | `String_AttributeSTRLong` | 筋力 | ✅ |
| STR | 筋力 | `String_AttributeSTRShort` | 筋力 | ✅ |
| Willpower | 意志力 | `String_AttributeWILLong` | 意志力 | ✅ |
| WIL | 意志 | `String_AttributeWILShort` | 意志力 | ❌ |
| Logic | 論理力 | `String_AttributeLOGLong` | 論理力 | ✅ |
| LOG | 論理 | `String_AttributeLOGShort` | 論理力 | ❌ |
| Intuition | 直観力 | `String_AttributeINTLong` | 直観力 | ✅ |
| INT | 直観 | `String_AttributeINTShort` | 直観力 | ❌ |
| Charisma | 魅力 | `String_AttributeCHALong` | 魅力 | ✅ |
| CHA | 魅力 | `String_AttributeCHAShort` | 魅力 | ✅ |
| Edge | エッジ | `String_AttributeEDGLong` | エッジ | ✅ |
| EDG | エッジ | `String_AttributeEDGShort` | エッジ | ✅ |
| Magic | 魔力 | `String_AttributeMAGLong` | 魔力 | ✅ |
| MAG | 魔力 | `String_AttributeMAGShort` | 魔力 | ✅ |
| Resonance | 共振力 | `String_AttributeRESLong` | 共振力 | ✅ |
| RES | 共振 | `String_AttributeRESShort` | 共振力 | ❌ |
| Essence | エッセンス | `String_AttributeESSLong` | エッセンス | ✅ |
| Essence | エッセンス | `String_AttributeESSShort` | ESS | ❌ |

## B. ja-jp.xml — 英語原文が用語集の見出しと一致するもの

en-us.xml の `<text>` が用語集の English と一致するキーについて、現在の日本語訳が用語集と違うものだけを挙げる。

| English | 用語集 | ja-jp.xml キー | 現在値 |
|---|---|---|---|
| Armor | 装甲 | `Checkbox_CreatePACKSKit_Armor` | 防具 |
| Martial Arts | 格闘技 | `Checkbox_CreatePACKSKit_MartialArts` | マーシャルアーツ（仮訳） |
| Equipped | 装備中 | `Checkbox_Equipped` | 装備済み |
| Mental | 精神 | `Checkbox_ManipulationSpell2` | 精神操作 |
| Physical | 物理 | `Checkbox_ManipulationSpell3` | 物理操作 |
| Notes | 備考 | `ColumnHeader_Notes` | Notes |
| Physical | 物理 | `Label_CMPhysical` | 身体 |
| Combat | 戦闘 | `Label_CharacterOptions_Combat` | Combat |
| Complex Form | 複合体 | `Label_Options_BPComplexForm` | 複合体のレーティング |
| Spells | 呪文 | `Label_SelectedSpells` | 習得した呪文 |
| Detection Spells | 探知呪文 | `Label_SpellDefenseDetection` | Detection Spells |
| Rituals | 儀式呪文 | `Label_SummaryRituals` | 儀式 |
| Physical | 物理 | `Node_Physical` | 身体 |
| Bioware | バイオウェア | `Node_SelectedBioware` | 埋め込んでいるバイオウェア |
| Combat Spells | 戦闘呪文 | `Node_SelectedCombatSpells` | 習得した戦闘呪文 |
| Cyberware | サイバーウェア | `Node_SelectedCyberware` | 埋め込んでいるサイバーウェア |
| Detection Spells | 探知呪文 | `Node_SelectedDetectionSpells` | 習得した探知呪文 |
| Rituals | 儀式呪文 | `Node_SelectedGeomancyRituals` | Selected Geomancy Rituals |
| Health Spells | 身体呪文 | `Node_SelectedHealthSpells` | 習得した身体呪文 |
| Illusion Spells | 幻影呪文 | `Node_SelectedIllusionSpells` | 習得した幻影呪文 |
| Manipulation Spells | 操作呪文 | `Node_SelectedManipulationSpells` | 習得した操作呪文 |
| Martial Arts | 格闘技 | `Node_SelectedMartialArts` | 習得した格闘技 |
| Category | カテゴリー | `Skill_SortCategory` | Category |
| Accuracy | 精度 | `String_Accuracy` | Accuracy |
| Ammo | 弾薬 | `String_Ammo` | Ammo |
| Amount | 数量 | `String_Amount` | 金額 |
| Armor | 装甲 | `String_Armor` | Armor |
| AGI | 敏捷 | `String_AttributeAGIShort` | 敏捷力 |
| Body | 強靱力 | `String_AttributeBODLong` | 強靭力 |
| BOD | 強靱 | `String_AttributeBODShort` | 強靭力 |
| INT | 直観 | `String_AttributeINTShort` | 直観力 |
| LOG | 論理 | `String_AttributeLOGShort` | 論理力 |
| REA | 反応 | `String_AttributeREAShort` | 反応力 |
| RES | 共振 | `String_AttributeRESShort` | 共振力 |
| WIL | 意志 | `String_AttributeWILShort` | 意志力 |
| Device | 機器 | `String_ComplexFormTargetDevice` | Device |
| Cost | コスト | `String_Cost` | Cost |
| Damage | ダメージ(DV) | `String_Damage` | Damage |
| Essence | エッセンス | `String_DescEssence` | Essence |
| Mental | 精神 | `String_DescMental` | 精神操作 |
| Device Rating | 機器RTG | `String_DeviceRating` | 機器レーティング |
| Grade | 等級 | `String_Grade` | 階梯 |
| Handling | 操縦値 | `String_Handling` | Handling |
| Level | レベル | `String_Level` | Level |
| Lifestyle | ライフスタイル | `String_Lifestyle` | (未訳) |
| Physical | 物理 | `String_LimitPhysicalShort` | 身体 |
| Martial Art | 格闘技 | `String_MartialArt` | Martial Art |
| Martial Arts | 格闘技 | `String_MartialArtsCount` | Martial Arts |
| Mode | モード | `String_Mode` | Mode |
| Name | 名前 | `String_Name` | Name |
| Points | ポイント | `String_Points` | Points |
| Power | パワー | `String_Power` | Power |
| Quality | 資質 | `String_Quality` | Quality |
| RC | 反動補正RC | `String_RC` | RC |
| Reach | リーチ | `String_Reach` | Reach |
| Armor | 装甲 | `String_SelectPACKSKit_Armor` | 装甲値 |
| Sensor | センサ | `String_Sensor` | Sensor |
| Special Attributes | 特殊能力値 | `String_SpecialAttributes` | Special Attributes |
| Total | 合計 | `String_Total` | Total |
| Tradition | 様式 | `String_Tradition` | Tradition |
| Vehicle | ヴィークル | `String_Vehicle` | Vehicle |
| Body | 強靱力 | `String_VehicleBody` | Body |
| Weapon | 武器 | `String_Weapon` | Weapon |
| Notes | 備考 | `Tab_Notes` | ノート |
| Armor | 装甲 | `Tip_Armor` | 装甲値 |
| Notes | 備考 | `Title_Notes` | ノート |

## C. ja-jp_data.xml — エンティティ名・カテゴリが用語集見出しと一致するもの

| English | 用語集 | 種別 | 現在値 |
|---|---|---|---|
| Acceleration | 加速値 | name | Acceleration |
| Judge Intentions | 意図を測る | name | 意図をはかるテスト |
| Memory | 記憶 | name | 記憶テスト |
| Mental Limit | 精神リミット | name | Mental Limit |
| Name | 名前 | name | Name |
| Physical Limit | 身体リミット | name | Physical Limit |
| Skill | 技能 | name | Skill |
| Social Limit | 社交リミット | name | Social Limit |
| Armor | 装甲 | category | 防具 |
| Attributes | 能力値 | category | Attributes |
| Body | 強靱力 | category | 強靭力 |
| Resonance | 共振力 | category | Resonance |
| Rituals | 儀式呪文 | category | 儀式 |
| Services | 助力 | category | Services |

