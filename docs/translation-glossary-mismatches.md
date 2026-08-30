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

## D. sr5eja 由来で ui.json 未収録の用語 (seed 候補)

Foundry SR5e 日本語化にあり、当方の `ui.json` に無い用語。descriptor・ルール語の参照や `ui.json` 追加の材料。

| English | sr5eja | 2021版 |
|---|---|---|
| Accessory | アクセサリ |  |
| Action | アクション |  |
| Action Type | タイプ |  |
| Action Type None | なし |  |
| Action Type Varies | 変動 |  |
| Active Defense | 能動防御 |  |
| Add Ammo | 弾薬を追加 |  |
| Add Five To Overwatch | 監視指数+5 |  |
| Add One To Overwatch | 監視指数+1 |  |
| Add Skill | 技能の追加 |  |
| adept power | アデプト・パワー |  |
| Agent | エージェント |  |
| Ammo Full | 弾薬満タン |  |
| Ammo Gel Rounds | ゲル弾 |  |
| Aoe | 効果範囲 |  |
| Apply Wounds | 負傷を適用 |  |
| Armor Hardened | 硬化 |  |
| Armor Hardened Full | 硬化装甲 |  |
| Attack | 攻撃 | アタック |
| Attacker | 攻撃者 |  |
| Attacker Hits | 攻撃側のヒット数 |  |
| Attacker Net Hits | 攻撃側純ヒット数 |  |
| Attr Intuition | 直感力 |  |
| Availability | 入手値 |  |
| Awakened | 覚醒者 |  |
| Awakened Emerged | 覚醒者/発現者 |  |
| Barrel | バレル |  |
| Base | 基本 |  |
| Base Value | 基本値 |  |
| Biofeedback Damage | 生体信号フィードバックダメージ |  |
| Biography | 経歴 |  |
| Blast Radius | 爆発半径 |  |
| Blitz | 速攻 |  |
| Block | ブロック |  |
| Bonus | ボーナス |  |
| Bonuses | ボーナス |  |
| Broken | 破壊 |  |
| Bullet | ラウンド |  |
| Bullet Count | 弾丸の数 |  |
| Bullets | ラウンド |  |
| Buy Hits | ヒットの購入 |  |
| call in action | 召喚／コンパイル |  |
| Can Default | デフォルティング可 |  |
| Capacity | 容量 |  |
| Career Karma | 通算カルマ |  |
| character | キャラクター |  |
| Clear Marks | マークを消す |  |
| Collapse | 折りたたむ |  |
| Collapse All | 全て折りたたむ |  |
| Common Program | 一般プログラム |  |
| Conceal | 隠蔽 |  |
| Connect To Network | ネットワークに接続 |  |
| Connection | コネクション | コネ値 |
| contact | コネ | コンタクト |
| Contact Type | 種類 |  |
| Continue | 続行 |  |
| Control Rig | コントロール・リグ |  |
| Cover | 遮蔽 |  |
| Create | {type}を作成 |  |
| critter power | クリッター・パワー |  |
| Cyberware Grade | 等級 |  |
| Cyberware Grade Alpha | アルファ |  |
| Cyberware Grade Beta | ベータ |  |
| Cyberware Grade Delta | デルタ |  |
| Cyberware Grade Gamma | ガンマ |  |
| Cyberware Grade Grey | グレイ |  |
| Cyberware Grade Standard | スタンダード |  |
| Cyberware Grade Used | 中古 |  |
| Damage | ダメージ | ダメージ(DV) |
| Damage Replace | ダメージ置換 |  |
| Damage Type | 種別 | ダメージタイプ |
| Default Category Visibility | 空のカテゴリを表示 |  |
| Defender | 防御側 |  |
| Defender Net Hits | 防御側純ヒット数 |  |
| Defense | 防御 | 回避 |
| Defense Test | 防御テスト |  |
| Delete Ammo | 弾薬を削除 |  |
| Delete Item | アイテムを削除 |  |
| Delete License | ライセンスを削除 |  |
| Delete Mod | 改造・モジュールを削除 |  |
| Delete Skill | 技能を削除 |  |
| Description | 解説 |  |
| Descriptors | 特性子 |  |
| Details | 詳細 |  |
| Detection Spell Extended | 超広域 |  |
| device | デバイス | 機器 |
| Device Cat Cyberdeck | サイバーデッキ |  |
| Device Type | 種別 |  |
| Direct Connection | 直結 |  |
| Dmg Type Matrix | マトリックス |  |
| Dodge | 回避 |  |
| Dont Apply Wounds | 負傷を適用しない |  |
| Drain | ドレイン | ドレイン |
| Drain Attribute | ドレイン能力値 |  |
| Drain Value | ドレイン |  |
| Dropoff | 外す |  |
| Duck Or Cover | 伏せもしくは遮蔽を取る |  |
| Duration | 効果時間 | 効果時間 |
| Duration Instant | インスタント |  |
| Edit Ammo | 弾薬を編集 |  |
| Edit Item | アイテムを編集 |  |
| Edit Skill | スキルを編集 |  |
| Effect | 効果 |  |
| Effects | 効果 |  |
| Emerged | 発現者 |  |
| Environment High | 高 |  |
| Environment Low | 低 |  |
| Environment Medium | 中 |  |
| Environment Modifier | 環境修正 |  |
| Environment None | なし |  |
| Environment Very High | 非常に高い |  |
| Expand | 展開 |  |
| Expand All | すべて展開 |  |
| Extend | 継続 |  |
| Extended | 継続 |  |
| Extended Hits | 蓄積ヒット数 |  |
| Extended Test | 継続テスト |  |
| Fade | フェイディング |  |
| Fade Attribute | フェイディングに使用する能力値 |  |
| Fade Value | フェイディング |  |
| Filter | フィルター |  |
| Fire Mode | 射撃モード |  |
| Full Defense | 全力防御 |  |
| Full Defense Attribute | 全力防御使用能力値 |  |
| Full Matrix Defense | マトリックス全力防御 |  |
| Glitch | グリッチ! |  |
| Glitch Critical | クリティカルグリッジ！ |  |
| Glitches | グリッジ: |  |
| Good Cover | 完全遮蔽 |  |
| grid | グリッド |  |
| Grids | グリッド |  |
| Hacking Program | ハッキングプログラム |  |
| Hardened Armor | 硬化装甲 |  |
| Help | ヘルプ |  |
| Hits | ヒット |  |
| Hot Sim | ホットシム |  |
| Immunity | 完全耐性 |  |
| Immunity To Normal Weapons | 通常武器完全耐性 |  |
| Import Character | キャラクターをインポートする |  |
| Incoming Damage | 抵抗前ダメージ値 |  |
| Incoming Drain | 抵抗前ドレイン値 |  |
| Incoming Fade | 抵抗前フェイディング値 |  |
| Information | 情報 |  |
| Init Cat Matrix | マトリックス |  |
| Internal | 内蔵 |  |
| Is Critter | クリッター |  |
| Is Grunt | グラント |  |
| Item Mod | アイテム修正 |  |
| Item Name | アイテム |  |
| Knocked Down | 転倒 |  |
| Knowledge Skill Academic | 学術 |  |
| Knowledge Skill Interests | 趣味 |  |
| Knowledge Skill Professional | 職業 |  |
| Knowledge Skill Street | ストリート |  |
| Languages | 言語 |  |
| Last Roll | 最後に促されたロール |  |
| License | 免許 |  |
| Licenses | 免許 |  |
| Lifestyle Comforts | 快適さ |  |
| Lifestyle Guests | 同居人 |  |
| Lifestyle High | 上流 |  |
| Lifestyle Low | 下流 |  |
| Lifestyle Luxory | 贅沢 |  |
| Lifestyle Middle | 中流 |  |
| Lifestyle Neighborhood | 近隣環境 |  |
| Lifestyle Security | 治安 |  |
| Lifestyle Squatter | 不法居住 |  |
| Lifestyle Street | ストリート |  |
| Lifestyle Type | 種別 |  |
| Limit Mental | 精神リミット |  |
| Limit Physical | 身体リミット |  |
| Limit Social | 社交リミット |  |
| Load | ロード |  |
| Loaded | ロード済 | 装填 |
| Loyalty | 忠実度 | 忠実値 |
| Magic | 魔法 | 魔力 |
| Manual | 手動 |  |
| Manual Override | 手動操作優先 |  |
| Marks | マーク |  |
| Matrix Defense | マトリックス防御 |  |
| Matrix Full Defense Attribute | マトリックス全力防御能力値 |  |
| Matrix Target | マトリックスターゲット |  |
| Melee Weapon Attack | 近接武器攻撃 |  |
| Mental Limit | 精神リミット | 精神リミット |
| Migration Complete | マイグレーション完了 |  |
| Mod Points | 改造スロット |  |
| modification | 装備改造 |  |
| Modification Categories | 改造のカテゴリー |  |
| Modification Category | 改造カテゴリー |  |
| Modification Slots | 改造スロット |  |
| Modified | 修正後 |  |
| Modified Armor | 修正装甲値 |  |
| Modified Damage | 修正後ダメージ |  |
| Modified Drain | 修正後ドレイン |  |
| Modified Fade | 修正後フェイディング |  |
| Modify Roll | ロールを修正 |  |
| Mount Point | マウント箇所 |  |
| Move Item Inventory | アイテムをインベントリに移動する |  |
| Movement | 移動 | 移動 |
| Mundane | マンディン |  |
| Net Hits | 純ヒット |  |
| New | 新しい |  |
| No Cover | 遮蔽なし |  |
| Normal | ノーマル |  |
| Normal Skill Button | ノーマル |  |
| Normal Spell Button | ノーマル |  |
| Not Extended | 継続なし |  |
| Notoriety | 悪評 | 悪名 |
| Open Network Manager | ネットワークマネージャーを開く |  |
| Open Origin | アイテムを開く |  |
| Opposed Type | タイプ |  |
| Opposing Hits | 対抗側ヒット数 |  |
| Opposing Net Hits | 純ヒット数 |  |
| Original Dice Pool | 元のダイスプール |  |
| Out Of Range | 射程距離外 |  |
| Overflow | オバーフロー |  |
| Override | 上書き |  |
| Overwatch Score | 監視指数(OS) |  |
| Owner | オーナー |  |
| Parry | 受け流し |  |
| Partial Cover | 部分遮蔽 |  |
| Physical Limit | 身体リミット | 身体リミット |
| Physical Track | 身体トラック | 身体ダメージトラック |
| Place Template | テンプレートの場所 |  |
| Plus Fifteen Minutes | +15分 |  |
| Power Type | パワータイプ |  |
| Program Type | タイプ |  |
| Public Awareness | 公的認知度 | 公的認知度 |
| Public Grid | 公共グリッド |  |
| Push The Limit | 限界突破 |  |
| Qty | 個数 | 数量 |
| Quality Type | 資質タイプ |  |
| Quality Type Life Module | ライフモジュール |  |
| Quality Type Negative | 不利 |  |
| Quality Type Positive | 有利 |  |
| Quantity | 数量 |  |
| Range Weapon Attack | 射撃 |  |
| Reagent | 原質 |  |
| Reckless Spell Button | 無謀な呪文行使 |  |
| Recoil | 反動 |  |
| Recoil Compensation | 反動修正 |  |
| Refresh | リフレッシュ |  |
| Remove Bonus | ボーナスを削除する |  |
| Remove Specialization | 専門化を削除する |  |
| Resist | 抵抗 |  |
| Restore Default Skills | デフォルトのスキルに戻す |  |
| Result Override | 結果上書き |  |
| Result Override Glitches | グリッチ数 |  |
| Result Override Hits | 成功数 |  |
| Right Click To Clear | 右クリックでクリア |  |
| Roll | ロール |  |
| Roll Composure | 冷静 |  |
| Roll Custom | カスタム |  |
| Roll Defense | 防御 |  |
| Roll Drain | ドレイン |  |
| Roll Fade | フェイディング |  |
| Roll Judge Intentions | 意図を図る |  |
| Roll Lift Carry | 持ち上げ/運搬 |  |
| Roll Memory | 記憶 |  |
| Roll Mode | ロールモード |  |
| Roll Soak | ダメージ抵抗 |  |
| Rounds Remaining | 残弾数 |  |
| Run | 走行 |  |
| Running Silent | サイレント状態 |  |
| Running Speed | 走行速度 |  |
| Same Grid | 同一グリッド |  |
| Second Attribute | 副能力値 |  |
| Second Chance | 振り直し |  |
| Selected Targets | 目標選択 |  |
| Sheet Actor | アクターシート |  |
| Sheet Item | アイテムシート |  |
| Side | サイド |  |
| Situational Modifier | 状況修正 |  |
| Soak | ダメージ抵抗 |  |
| Soak Test | ダメージ抵抗テスト |  |
| Social Limit | 社交リミット | 社交リミット |
| Source | 資料 |  |
| Spare Clips | 予備クリップ |  |
| sprite power | スプライト・パワー |  |
| Stun Track | 精神ＣＭ | 精神ダメージトラック |
| Suppressing | 制圧 |  |
| Target | 目標 | 対象 |
| Target Device | デバイス |  |
| Temporary | 一時的 |  |
| Temporary Modifiers | 一時的な修正 |  |
| Test | テスト |  |
| Threshold | 目標値 |  |
| Toggle Active | 有効状態切替 |  |
| Toggle Breakdown | 内訳を表示 |  |
| Toggle Equip | 装備状態切替 |  |
| Toggle Wireless | ワイヤレス状態切替 |  |
| Top | トップ |  |
| Total | トータル | 合計 |
| Under Barrel | アンダーバレル |  |
| Value | 数値 |  |
| vehicle | ヴィークル／ドローン | ヴィークル |
| Walk | 歩行 |  |
| Walking Speed | 歩行速度 |  |
| Wireless | ワイヤレス |  |
| Wireless Offline | オフライン |  |
| Wireless Online | オンライン |  |
| Wireless Unavailable | 利用不可 |  |

