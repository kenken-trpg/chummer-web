# SR5 用語集 (確定版)

**自動生成** — `backend/scripts/build_ja_glossary.py` が再生成する。手で編集しない。

## 出典と優先順位

- 典拠: `~/Downloads/chummer5th_シート日本語化_52160対応/xz.language.xslt` (2021-11, Chummer build 5.216.0 対応)。
- `~/Downloads/` 内で競合したら新しい方が真 → **2021 版 > 2020 版 > chumJA (2013)**。
- 2020 版 (`chummer5th_シート日本語化/xz.language.xslt`) は本表で完全に上位互換のため参照不要。
  - 2020 版では英語のままだったが 2021 版で和訳された語: **75 件**。
- 2021 版でも英語/略号のままの語 (下表2) は原文維持が正 (AP・DV・ESS 等のゲーム用語コード)。

- 和訳あり: **200 件** / コード・略号 (latin のまま): **177 件**。

## 表1: 和訳あり (確定用語)

| English | 日本語 | xslt var | 備考 |
|---|---|---|---|
| Accel | 加速値 | `lang.Accel` |  |
| Acceleration | 加速値 | `lang.Acceleration` | 2020版: `Acceleration` |
| Accuracy | 精度 | `lang.Accuracy` |  |
| Acid | 強酸 | `lang.Acid` |  |
| Active Skills | 能動技能 | `lang.ActiveSkills` |  |
| Addiction | 依存症 | `lang.Addiction` |  |
| Adept Powers | アデプトパワー | `lang.AdeptPowers` | 2020版: `Adept Powers` |
| Age | 年齢 | `lang.Age` |  |
| AGI | 敏捷 | `lang.AGI` | 2020版: `AGI` |
| Agility | 敏捷力 | `lang.Agility` |  |
| Alias | ストリートネーム | `lang.Alias` |  |
| Already Addicted | 既に中毒 | `lang.AlreadyAddicted` | 2020版: `Already Addicted` |
| Ammo | 弾薬 | `lang.Ammo` |  |
| Amount | 数量 | `lang.Amount` | 2020版: `Amount` |
| Archetype | アーキタイプ | `lang.Archetype` | 2020版: `Archetype` |
| Armor | 装甲 | `lang.Armor` | 2020版: `Armor` |
| Armor Value | 装甲値 | `lang.ArmorValue` | 2020版: `Value` |
| Astral | アストラル | `lang.Astral` |  |
| Astral Initiative | アストラルイニシアティブ | `lang.AstralInitiative` | 2020版: `アストラル イニシアティブ` |
| Astral Limit | アストラルリミット | `lang.AstralLimit` |  |
| Attack | アタック | `lang.Attack` |  |
| Attribute | 能力値 | `lang.Attribute` | 2020版: `Attribute` |
| Attributes | 能力値 | `lang.Attributes` |  |
| Bioware | バイオウェア | `lang.Bioware` | 2020版: `Bioware` |
| BOD | 強靱 | `lang.BOD` | 2020版: `BOD` |
| Body | 強靱力 | `lang.Body` |  |
| Calendar | カレンダー | `lang.Calendar` | 2020版: `Calendar` |
| Career | 累計 | `lang.Career` |  |
| Category | カテゴリー | `lang.Category` | 2020版: `Category` |
| CHA | 魅力 | `lang.CHA` | 2020版: `CHA` |
| Charisma | 魅力 | `lang.Charisma` |  |
| Cold | 冷気 | `lang.Cold` |  |
| Combat | 戦闘 | `lang.Combat` |  |
| Combat Spells | 戦闘呪文 | `lang.CombatSpells` |  |
| Commlink | コムリンク | `lang.Commlink` |  |
| Complex Form | 複合体 | `lang.ComplexForm` | 2020版: `Complex Form` |
| Complex Forms | 複合体 | `lang.ComplexForms` | 2020版: `Complex Forms` |
| Composure | 冷静テスト | `lang.Composure` |  |
| Connection | コネ値 | `lang.Connection` | 2020版: `Connection` |
| Contact | コンタクト | `lang.Contact` | 2020版: `Contact` |
| Contact Drug | 接触 | `lang.ContactDrug` | 2020版: `Contact` |
| Cost | コスト | `lang.Cost` | 2020版: `Cost` |
| Current Edge | エッジの現在値 | `lang.CurrentEdge` |  |
| Cyberware | サイバーウェア | `lang.Cyberware` | 2020版: `Cyberware` |
| Damage | ダメージ(DV) | `lang.Damage` |  |
| Damage Type | ダメージタイプ | `lang.DamageType` | 2020版: `Damage Type` |
| Data Proc | データ処理 | `lang.DataProc` |  |
| Data Processing | データ処理 | `lang.DataProcessing` | 2020版: `Data Processing` |
| Date | 日付 | `lang.Date` | 2020版: `Date` |
| Date (data label) | 日付 | `lang.Data` | 2020版: `Data` |
| Day | 日 | `lang.Day` | 2020版: `天` |
| Days | 日 | `lang.Days` | 2020版: `天` |
| Decrease Attribute | 能力値減少 | `lang.DecreaseAttribute` |  |
| Defense | 回避 | `lang.Defense` |  |
| Detection | 探知 | `lang.Detection` |  |
| Detection Spells | 探知呪文 | `lang.DetectionSpells` |  |
| Device | 機器 | `lang.Device` | 2020版: `Device` |
| Device Rating | 機器RTG | `lang.DeviceRating` | 2020版: `Rating` |
| Devices | デバイス | `lang.Devices` | 2020版: `Devices` |
| Direct | 直接 | `lang.Direct` |  |
| Drain | ドレイン | `lang.Drain` |  |
| Duration | 効果時間 | `lang.Duration` | 2020版: `Duration` |
| E | 超遠距離-6 | `lang.E` | 2020版: `超遠距離-4` |
| EDG | エッジ | `lang.EDG` | 2020版: `EDG` |
| Edge | エッジ | `lang.Edge` |  |
| Electricity | 電撃 | `lang.Electricity` |  |
| Equipped | 装備中 | `lang.Equipped` | 2020版: `Equipped` |
| Essence | エッセンス | `lang.Essence` |  |
| Eyes | 瞳の色 | `lang.Eyes` |  |
| Falling | 落下 | `lang.Falling` |  |
| Fatigue | 疲労 | `lang.Fatigue` |  |
| Fire | 火炎 | `lang.Fire` |  |
| Firewall | ファイアウォール | `lang.Firewall` |  |
| Fly | 飛行 | `lang.Fly` | 2020版: `Fly` |
| FV | フェイディング | `lang.FV` | 2020版: `FV` |
| Gender | 性別 | `lang.Gender` |  |
| Grade | 等級 | `lang.Grade` | 2020版: `Grade` |
| Hair | 髪の色 | `lang.Hair` |  |
| Handling | 操縦値 | `lang.Handling` |  |
| Health | 身体 | `lang.Health` |  |
| Health Spells | 身体呪文 | `lang.HealthSpells` |  |
| Height | 身長 | `lang.Height` |  |
| I Dcredsticks | ID/クレッドスティック | `lang.IDcredsticks` |  |
| Illusion | 幻影 | `lang.Illusion` |  |
| Illusion Spells | 幻影呪文 | `lang.IllusionSpells` |  |
| Implant | インプラント | `lang.Implant` | 2020版: `Implant` |
| Indirect | 間接 | `lang.Indirect` |  |
| Ingestion | 経口 | `lang.Ingestion` | 2020版: `Ingestion` |
| Inhalation | 吸入 | `lang.Inhalation` | 2020版: `Inhalation` |
| Initiative | イニシアティブ | `lang.Initiative` |  |
| Injection | 注入 | `lang.Injection` | 2020版: `Injection` |
| INT | 直観 | `lang.INT` | 2020版: `INT` |
| Intuition | 直観力 | `lang.Intuition` |  |
| Judge Intentions | 意図を測る | `lang.JudgeIntentions` |  |
| Karma | カルマ | `lang.Karma` |  |
| Knowledge Skills | 知識技能 | `lang.KnowledgeSkills` |  |
| L | 遠距離-3 | `lang.L` |  |
| Level | レベル | `lang.Level` | 2020版: `Level` |
| Lifestyle | ライフスタイル | `lang.Lifestyle` | 2020版: `Lifestyle` |
| Lift Carry | 持ち上げ/運搬 | `lang.LiftCarry` |  |
| Loaded | 装填 | `lang.Loaded` |  |
| Location | 所在地 | `lang.Location` | 2020版: `Location` |
| LOG | 論理 | `lang.LOG` | 2020版: `LOG` |
| Logic | 論理力 | `lang.Logic` |  |
| Loyalty | 忠実値 | `lang.Loyalty` | 2020版: `Loyalty` |
| M | 中距離-1 | `lang.M` |  |
| MAG | 魔力 | `lang.MAG` | 2020版: `MAG` |
| Magic | 魔力 | `lang.Magic` |  |
| Mana | マナ | `lang.Mana` |  |
| Manipulation | 操作 | `lang.Manipulation` |  |
| Manipulation Spells | 操作呪文 | `lang.ManipulationSpells` |  |
| Martial Art | 格闘技 | `lang.MartialArt` | 2020版: `Martial Art` |
| Martial Arts | 格闘技 | `lang.MartialArts` | 2020版: `Martial Arts` |
| Matrix AR | マトリックス(AR) | `lang.MatrixAR` | 2020版: `Matrix AR` |
| Matrix Cold | マトリックス（コールドシム） | `lang.MatrixCold` | 2020版: `Matrix Cold` |
| Matrix Devices | マトリックス機器 | `lang.MatrixDevices` | 2020版: `Matrix Devices` |
| Matrix Hot | マトリックス（ホットシム） | `lang.MatrixHot` | 2020版: `Matrix Hot` |
| Melee Weapons | 近接武器 | `lang.MeleeWeapons` | 2020版: `Melee Weapons` |
| Memory | 記憶 | `lang.Memory` |  |
| Mental | 精神 | `lang.Mental` |  |
| Mental Attributes | 精神能力値 | `lang.MentalAttributes` |  |
| Mental Limit | 精神リミット | `lang.MentalLimit` |  |
| Metatype | メタタイプ | `lang.Metatype` |  |
| Mode | モード | `lang.Mode` |  |
| Month | 月 | `lang.Month` |  |
| Months | 月 | `lang.Months` |  |
| Movement | 移動 | `lang.Movement` |  |
| Name | 名前 | `lang.Name` |  |
| Not Addicted Yet | まだ中毒ではない | `lang.NotAddictedYet` | 2020版: `Not Addicted Yet` |
| Notes | 備考 | `lang.Notes` | 2020版: `Notes` |
| Notoriety | 悪名 | `lang.Notoriety` |  |
| Nuyen | 新円 | `lang.Nuyen` |  |
| Pathogen | 病気 | `lang.Pathogen` |  |
| Physical | 物理 | `lang.Physical` |  |
| Physical Attributes | 身体能力値 | `lang.PhysicalAttributes` |  |
| Physical Limit | 身体リミット | `lang.PhysicalLimit` |  |
| Physical Natural Recovery | 身体自然回復(1 日) | `lang.PhysicalNaturalRecovery` |  |
| Physical Track | 身体ダメージトラック | `lang.PhysicalTrack` |  |
| Physiological | 肉体的 | `lang.Physiological` |  |
| Pilot | パイロット | `lang.Pilot` | 2020版: `Pilot` |
| Points | ポイント | `lang.Points` | 2020版: `Points` |
| Pool | プール | `lang.Pool` | 2020版: `Pool` |
| Power | パワー | `lang.Power` | 2020版: `Power` |
| Primary Arm | 利き腕 | `lang.PrimaryArm` |  |
| Psychological | 精神的 | `lang.Psychological` |  |
| Public Awareness | 公的認知度 | `lang.PublicAwareness` |  |
| Qty | 数量 | `lang.Qty` |  |
| Quality | 資質 | `lang.Quality` |  |
| Radiation | 放射線 | `lang.Radiation` |  |
| Range | 射程 | `lang.Range` |  |
| Ranged Weapons | 射撃武器 | `lang.RangedWeapons` | 2020版: `Ranged Weapons` |
| Rating | レーティング | `lang.Rating` | 2020版: `Rating` |
| RC | 反動補正RC | `lang.RC` |  |
| REA | 反応 | `lang.REA` | 2020版: `REA` |
| Reach | リーチ | `lang.Reach` | 2020版: `Reach` |
| Reaction | 反応力 | `lang.Reaction` |  |
| Reason | 理由 | `lang.Reason` | 2020版: `Reason` |
| RES | 共振 | `lang.RES` | 2020版: `RES` |
| Resistance | 抵抗 | `lang.Resistance` |  |
| Resonance | 共振力 | `lang.Resonance` |  |
| Rigger Initiative | リガー イニシアティブ | `lang.RiggerInitiative` |  |
| Rituals | 儀式呪文 | `lang.Rituals` |  |
| S | 近距離+0 | `lang.S` |  |
| Seats | 乗員 | `lang.Seats` |  |
| Sensor | センサ | `lang.Sensor` |  |
| Services | 助力 | `lang.Services` |  |
| Skill | 技能 | `lang.Skill` | 2020版: `Skill` |
| Skin | 肌の色 | `lang.Skin` |  |
| Sleaze | スリーズ | `lang.Sleaze` |  |
| Social Limit | 社交リミット | `lang.SocialLimit` |  |
| Sonic | 音響 | `lang.Sonic` |  |
| Special Attributes | 特殊能力値 | `lang.SpecialAttributes` |  |
| Speed | 最高速度 | `lang.Speed` |  |
| Spell | 呪文 | `lang.Spell` | 2020版: `Spell` |
| Spells | 呪文 | `lang.Spells` | 2020版: `Spells` |
| Spirit | 精霊 | `lang.Spirit` |  |
| Sprite | スプライト | `lang.Sprite` | 2020版: `Sprite` |
| STR | 筋力 | `lang.STR` | 2020版: `STR` |
| Street Cred | ストリートの評判 | `lang.StreetCred` |  |
| Strength | 筋力 | `lang.Strength` |  |
| Stun | 精神 | `lang.Stun` |  |
| Stun Natural Recovery | 精神自然回復(1 時間) | `lang.StunNaturalRecovery` |  |
| Stun Track | 精神ダメージトラック | `lang.StunTrack` |  |
| Swim | 水泳 | `lang.Swim` |  |
| Target | 対象 | `lang.Target` | 2020版: `Target` |
| Tasks | タスク | `lang.Tasks` | 2020版: `Tasks` |
| Total | 合計 | `lang.Total` | 2020版: `Total` |
| Total Armor | 装備した単体最高の防具とアクセサリーの合計 | `lang.TotalArmor` | 2020版: `Total of equipped single highest armor and accessories` |
| Touch | 接触 | `lang.Touch` | 2020版: `Touch` |
| Toxin | 毒物 | `lang.Toxin` |  |
| Toxins And Pathogens | 毒物と病気 | `lang.ToxinsAndPathogens` |  |
| Tradition | 様式 | `lang.Tradition` |  |
| Vehicle | ヴィークル | `lang.Vehicle` |  |
| Vehicle Body | 強靱力 | `lang.VehicleBody` |  |
| Weapon | 武器 | `lang.Weapon` |  |
| Week | 週 | `lang.Week` | 2020版: `周` |
| Weeks | 週 | `lang.Weeks` | 2020版: `周` |
| Weight | 重量 | `lang.Weight` |  |
| WIL | 意志 | `lang.WIL` | 2020版: `WIL` |
| Willpower | 意志力 | `lang.Willpower` |  |

## 表2: コード・略号 (原文維持)

| English | 表示 | xslt var |
|---|---|---|
| . , (decimal / grouping) | ., | `lang.marks` |
| A/S/D/F | A/S/D/F | `lang.ASDF` |
| Accessories | Accessories | `lang.Accessories` |
| Action | Action | `lang.Action` |
| Adept | Adept | `lang.Adept` |
| AI | AI | `lang.AI` |
| AI Programs and Advanced Programs | AI Programs and Advanced Programs | `lang.AIandAdvanced` |
| AP | AP | `lang.AP` |
| Applicable | Applicable | `lang.Applicable` |
| Apprentice | Apprentice | `lang.Apprentice` |
| AR | AR | `lang.AR` |
| Area | Area | `lang.Area` |
| Arts | Arts | `lang.Arts` |
| as | as | `lang.as` |
| Aspected Magician | Aspected Magician | `lang.AspectedMagician` |
| Astral Reputation | Astral Reputation | `lang.AstralReputation` |
| ATT | ATT | `lang.ATT` |
| Available | Available | `lang.Available` |
| Awakened | Awakened | `lang.Awakened` |
| Aware | Aware | `lang.Aware` |
| Background | Background | `lang.Background` |
| Base | Base | `lang.Base` |
| Bonus | Bonus | `lang.Bonus` |
| Bound | Bound | `lang.Bound` |
| CM | CM | `lang.CM` |
| Combat Skill | Combat Skill | `lang.CombatSkill` |
| Concept | Concept | `lang.Concept` |
| Condition Monitor | Condition Monitor | `lang.ConditionMonitor` |
| Contact List | Contact List | `lang.ContactList` |
| Contacts | Contacts | `lang.Contacts` |
| Core Damage Track | Core Damage Track | `lang.CoreTrack` |
| Critter | Critter | `lang.Critter` |
| Critter Power | Critter Power | `lang.CritterPower` |
| Critter Powers | Critter Powers | `lang.CritterPowers` |
| Critters | Critters | `lang.Critters` |
| Current Form | Current Form | `lang.CurrentForm` |
| Dead | Dead | `lang.Dead` |
| DEP | DEP | `lang.DEP` |
| Depth | Depth | `lang.Depth` |
| Derived Attributes | Derived Attributes | `lang.DerivedAttributes` |
| Description | Description | `lang.Description` |
| Down | Down | `lang.Down` |
| DP | DP | `lang.DP` |
| Drone | Drone | `lang.Drone` |
| DV | DV | `lang.DV` |
| Echo | Echo | `lang.Echo` |
| Echoes | Echoes | `lang.Echoes` |
| Enchanter | Enchanter | `lang.Enchanter` |
| Enchantments | Enchantments | `lang.Enchantments` |
| Enemies | Enemies | `lang.Enemies` |
| Enhancements | Enhancements | `lang.Enhancements` |
| Entries | Entries | `lang.Entries` |
| ESS | ESS | `lang.ESS` |
| Expenses | Expenses | `lang.Expenses` |
| Explorer | Explorer | `lang.Explorer` |
| Fading Value | Fading Value | `lang.FadingValue` |
| Fettered | Fettered | `lang.Fettered` |
| Foci | Foci | `lang.Foci` |
| Force | Force | `lang.Force` |
| FWL | FWL | `lang.FWL` |
| Gear | Gear | `lang.Gear` |
| Heavy | Heavy | `lang.Heavy` |
| hit | hit | `lang.hit` |
| Hobbies/Vice | Hobbies/Vice | `lang.HobbiesVice` |
| I | I | `lang.tstDuration1` |
| Info | Info | `lang.Info` |
| Init | Init | `lang.Init` |
| Initiate Grade | Initiate Grade | `lang.InitiateGrade` |
| Initiation | Initiation | `lang.Initiation` |
| Initiation Grade Notes | Initiation Grade Notes | `lang.InitiationNotes` |
| Instantaneous | Instantaneous | `lang.Instantaneous` |
| Intentions | Intentions | `lang.Intentions` |
| Limit | Limit | `lang.Limit` |
| Limits | Limits | `lang.Limits` |
| Line of Sight | Line of Sight | `lang.LineofSight` |
| Linked SIN | Linked SIN | `lang.LinkedSIN` |
| LOS | LOS | `lang.tstRange2` |
| LOS (A) | LOS (A) | `lang.tstRange4` |
| LOS(A) | LOS(A) | `lang.tstRange3` |
| Magician | Magician | `lang.Magician` |
| Maneuvers | Maneuvers | `lang.Maneuvers` |
| Manual | Manual | `lang.Manual` |
| Matrix Damage Track | Matrix Damage Track | `lang.MatrixTrack` |
| Metamagics | Metamagics | `lang.Metamagics` |
| Mod | Mod | `lang.Mod` |
| Model | Model | `lang.Model` |
| Modifications | Modifications | `lang.Modifications` |
| Mount | Mount | `lang.Mount` |
| Mystic Adept | Mystic Adept | `lang.MysticAdept` |
| Native | Native | `lang.Native` |
| Negative | Negative | `lang.Negative` |
| No | No | `lang.No` |
| No Devices to list | No Devices to list | `lang.Nothing2Show4Devices` |
| No Notes to list | No Notes to list | `lang.Nothing2Show4Notes` |
| No Spirits/Sprites to list | No Spirits/Sprites to list | `lang.Nothing2Show4SpiritsSprites` |
| No Vehicles to list | No Vehicles to list | `lang.Nothing2Show4Vehicles` |
| None | None | `lang.None` |
| Optional Powers | Optional Powers | `lang.OptionalPowers` |
| Other | Other | `lang.Other` |
| Other Armor | Other Armor | `lang.OtherArmor` |
| Other Portraits | Other Portraits | `lang.OtherMugshots` |
| Overflow | Overflow | `lang.Overflow` |
| OVR | OVR&#160; | `lang.OVR` |
| P | P | `lang.tstDamage1` |
| P | P | `lang.tstDuration2` |
| Page Break: | Page Break:  | `lang.PageBreak` |
| Permanent | Permanent | `lang.Permanent` |
| Persona | Persona | `lang.Persona` |
| Personal Data | Personal Data | `lang.PersonalData` |
| Personal Life | Personal Life | `lang.PersonalLife` |
| Pets | Pets | `lang.Pets` |
| Player | Player | `lang.Player` |
| Portrait | Portrait | `lang.Mugshot` |
| Positive | Positive | `lang.Positive` |
| Powers | Powers | `lang.Powers` |
| Preferred Payment Method | Preferred Payment Method | `lang.PreferredPayment` |
| Priorities | Priorities | `lang.Priorities` |
| Processor | Processor | `lang.Processor` |
| Program | Program | `lang.Program` |
| Programs | Programs | `lang.Programs` |
| Qualities | Qualities | `lang.Qualities` |
| Registered | Registered | `lang.Registered` |
| Remaining Available | Remaining Available | `lang.RemainingAvailable` |
| Requires | Requires | `lang.Requires` |
| Resist Drain with | Resist Drain with | `lang.ResistDrain` |
| Resist Fading with | Resist Fading with | `lang.ResistFading` |
| Resistances | Resistances | `lang.Resistances` |
| Resources | Resources | `lang.Resources` |
| Rigger | Rigger | `lang.Rigger` |
| RTG | RTG | `lang.Rtg` |
| Run | Run | `lang.Run` |
| S | S | `lang.tstDamage2` |
| S | S | `lang.tstDuration3` |
| S | S | `lang.tstRange5` |
| S (A) | S (A) | `lang.tstRange7` |
| S(A) | S(A) | `lang.tstRange6` |
| Selected Gear | Selected Gear | `lang.SelectedGear` |
| Self | Self | `lang.Self` |
| Show: | Show:  | `lang.Show` |
| Skill Group | Skill Group | `lang.SkillGroup` |
| Skill Groups | Skill Groups | `lang.SkillGroups` |
| Skills | Skills | `lang.Skills` |
| SLZ | SLZ | `lang.SLZ` |
| Social | Social | `lang.Social` |
| Source | Source | `lang.Source` |
| Special | Special | `lang.Special` |
| Special | Special | `lang.tstRange10` |
| Spirits | Spirits | `lang.Spirits` |
| Sprites | Sprites | `lang.Sprites` |
| Standard | Standard | `lang.Standard` |
| Stream | Stream | `lang.Stream` |
| Street Name | Street Name | `lang.StreetName` |
| Submersion | Submersion | `lang.Submersion` |
| Submersion Grade | Submersion Grade | `lang.SubmersionGrade` |
| Submersion Notes | Submersion Notes | `lang.SubmersionNotes` |
| Sustained | Sustained | `lang.Sustained` |
| T | T | `lang.tstRange1` |
| T (A) | T (A) | `lang.tstRange9` |
| T(A) | T(A) | `lang.tstRange8` |
| Toggle Colors | Toggle Colors | `lang.ToggleColors` |
| Type | Type | `lang.Type` |
| Unbound | Unbound | `lang.Unbound` |
| Under | Under | `lang.Under` |
| Unknown | Unknown | `lang.Unknown` |
| Unnamed Character | Unnamed Character | `lang.UnnamedCharacter` |
| Unregistered | Unregistered | `lang.Unregistered` |
| Vehicle Cost | Vehicle Cost | `lang.VehicleCost` |
| Vehicles | Vehicles | `lang.Vehicles` |
| VR | VR | `lang.VR` |
| W | W | `lang.W` |
| Walk | Walk | `lang.Walk` |
| Weaknesses | Weaknesses | `lang.Weaknesses` |
| Weapons | Weapons | `lang.Weapons` |
| Wild Reputation | Wild Reputation | `lang.WildReputation` |
| with | with | `lang.with` |
| Yes | Yes | `lang.Yes` |
| ¥ (nuyen symbol) | &#165; | `lang.NuyenSymbol` |

