# 翻訳インポートレポート

**自動生成** — `backend/scripts/regen_ja.sh` (= `import_ja_from_refs.py --write`)。
画面の日本語名は 3 つの層から来る。上流 Chummer の `ja-jp_data.xml`、その上に重ねる
`data.json`、最後にまだ英語の名前にだけ当てるシャドウラン・コデックスの名前
（`app/data_loader/codex.py`）。ここに載るのは `data.json` の全エントリで、出どころの表ごとに分けてある。
訳の表は英語名だけで引くので、「品目」の列には、その名前を持つ品目の種類と本をすべて並べる。

- オーバーレイ合計: **555 件**
- 日本語版のある本: RG, SR5, SRCX（コデックスが再録した品目も日本語版ありと数える）

## 日本語版の無い品目にだけ当たる自前の訳 (246)

サプリの用語は英語のままにする方針（本に無い片仮名を作らない）と食い違う候補。
chumJA（SR4 の訳）は別に数える。

| English | 日本語 | 出どころ | 品目 |
|---|---|---|---|
| Acceleration | 加速値 | import_ja_from_refs.CURATED | category: R5 |
| Adept Accident | アデプト・アクシデント | ja_curated_entities.ENTITIES | powers: HT |
| Adept Spell | アデプト呪文 | ja_curated_entities.ENTITIES | powers: HT |
| Advanced Alchemy | 上級錬金術 | import_ja_from_refs.CURATED | magic_arts: SG / metamagics: SG |
| Advanced Ritual Casting | 上級儀式行使 | import_ja_from_refs.CURATED | magic_arts: SG |
| Advanced Spellcasting | 上級呪文行使 | import_ja_from_refs.CURATED | magic_arts: SG |
| Aegis | イージス | ja_curated_entities.ENTITIES | echoes: KC |
| Air Elemental | 大気のエレメンタル | import_ja_from_refs.CURATED | spirits: FA |
| Air Filter | 空気清浄/エア・フィルター | ja_curated_spells.SPELLS | spells: SSP |
| Alarm Ward | 警報結界 | ja_curated_spells.SPELLS | spells: SG |
| Alleviate [Allergy] | [アレルギー] 緩和/アリーヴィエイト [アラジー] | ja_curated_spells.SPELLS | spells: SG |
| Alpine Wrestling | アルパイン・レスリング | ja_curated_entities.ENTITIES | martial_arts: SAG |
| Alter Ballistics | 弾道変更/オルター・バリスティクス | ja_curated_spells.SPELLS | spells: FA |
| Alter Temperature | 温度変化/オルター・テンパレチャー | ja_curated_spells.SPELLS | spells: SSP |
| Ambidexterity | 両利き/アンビデクステリティ | ja_curated_spells.SPELLS | spells: SG |
| Arbeitskreis INI | アルバイツクライスINI | ja_curated_entities.ENTITIES | martial_arts: SOTG |
| Arc Feedback | アーク・フィードバック | ja_curated_entities.ENTITIES | complex_forms: KC |
| Architect | 建築家 | import_ja_from_refs.CURATED | life_modules: RF / mentors: SOTG / paragons: KC |
| Artist | 芸術家 | import_ja_from_refs.CURATED | mentors: SHB2 |
| Asthenologica | アステノロジカ | ja_curated_entities.ENTITIES | martial_arts: SOTG |
| Astral Doppelganger | アストラル・ドッペルゲンガー | ja_curated_spells.SPELLS | spells: SG |
| Astral Message | アストラル伝言/アストラル・メッセージ | ja_curated_spells.SPELLS | spells: SG |
| Attune Animal | 動物同調 | ja_curated_spells.SPELLS | spells: SG |
| Attune Item | 物品同調 | ja_curated_spells.SPELLS | spells: SG |
| Badger | アナグマ | import_ja_from_refs.CURATED | mentors: SOTG |
| Barrage | 弾幕/バラージュ | ja_curated_spells.SPELLS | enhancements: SG / spells: FA |
| Berserker | バーサーカー | import_ja_from_refs.CURATED | mentors: SG / qualities: RF |
| Berserker's Rage | 狂戦士の怒り | ja_curated_entities.ENTITIES | powers: SG |
| Blood Magic | 血の魔術 | import_ja_from_refs.CURATED | magic_arts: SG |
| Body | 強靱力 | import_ja_from_refs.CURATED | category: R5 |
| Body Sculpt | 肉体成形 | ja_curated_entities.ENTITIES | powers: BLB |
| Bolt Hole | 隠れ家 | ja_curated_entities.ENTITIES | lifestyles: RF |
| Bootleg Program | 海賊版プログラム | ja_curated_entities.ENTITIES | complex_forms: KC |
| Branch | 枝/ブランチ | ja_curated_spells.SPELLS | spells: FA |
| Broadcast | 放送/ブロードキャスト | ja_curated_spells.SPELLS | spells: SSP |
| Brother in Arms | 戦友 | import_ja_from_refs.CURATED | mentors: SOTG |
| Buddhism | 仏教 | import_ja_from_refs.CURATED | traditions: SG |
| Bug Zapper | 殺虫器/バグ・ザッパー | ja_curated_spells.SPELLS | spells: SG |
| Calling [Spirit Type] | [精霊タイプ] 呼び出し | ja_curated_spells.SPELLS | spells: SG |
| Capricorn | カプリコーン | ja_curated_entities.ENTITIES | mentors: SAG |
| Catch | 捕球/キャッチ | ja_curated_spells.SPELLS | spells: HT |
| Causal Nexus | 因果連結 | ja_curated_entities.ENTITIES | complex_forms: KC |
| Charged Ward | 充填結界 | ja_curated_spells.SPELLS | spells: SG |
| Chill | 冷却/チル | ja_curated_spells.SPELLS | spells: SSP |
| Circle Fencing | サークル・フェンシング | ja_curated_entities.ENTITIES | martial_arts: SOTG |
| Circle of Cleansing | 浄化円 | ja_curated_spells.SPELLS | spells: SG |
| Claw | 爪撃/クロウ | ja_curated_spells.SPELLS | spells: FA |
| Comet | 彗星/コメット | ja_curated_spells.SPELLS | spells: FA |
| Commercial | 商業施設 | ja_curated_entities.ENTITIES | lifestyles: RF |
| Companion Sprite | コンパニオン・スプライト | import_ja_from_refs.CURATED | sprites: KC |
| Conceal Scent | 匂い隠し/コンシール・セント | ja_curated_spells.SPELLS | spells: HT |
| Consistency | 一貫性/コンシステンシー | ja_curated_spells.SPELLS | spells: CA |
| Contaminate | コンタミネート | ja_curated_entities.ENTITIES | echoes: DTD |
| Convince | 説得/コンヴィンス | ja_curated_spells.SPELLS | spells: SS |
| Coriolis | コリオリ | ja_curated_entities.ENTITIES | complex_forms: CF |
| Create Ally Spirit | 同盟精霊創造 | ja_curated_spells.SPELLS | spells: SG |
| Death | 死 | import_ja_from_refs.CURATED | mentors: FA |
| Decontamination | 除染/デコンタミネーション | ja_curated_spells.SPELLS | spells: SSP |
| Decoy | 囮/デコイ | ja_curated_spells.SPELLS | spells: SG |
| Decrease Gear Limits | 装備リミット減退/ディクリース・ギア・リミット | ja_curated_spells.SPELLS | spells: SG |
| Decrease Inherent Limits | 固有リミット減退/ディクリース・インヒアレント・リミット | ja_curated_spells.SPELLS | spells: SG |
| Decrease Noise | ノイズ減少/ディクリース・ノイズ | ja_curated_spells.SPELLS | spells: SG |
| Defrag | デフラグ | ja_curated_entities.ENTITIES | echoes: DTR |
| Dehydrate | 脱水/デハイドレート | ja_curated_spells.SPELLS | spells: SSP |
| Demara | ディマラ | ja_curated_entities.ENTITIES | powers: SSP |
| Derezz | デレズ | ja_curated_entities.ENTITIES | complex_forms: DT |
| Destroy [Free Spirit] | [自由精霊] 破壊/デストロイ [フリースピリット] | ja_curated_spells.SPELLS | spells: SG |
| Destroy [Vehicle] | [ヴィークル] 破壊/デストロイ [ヴィークル] | ja_curated_spells.SPELLS | spells: SG |
| Dispersion Circle | 拡散円 | ja_curated_spells.SPELLS | spells: SG |
| Disrupt [Focus] | [収束具] 破壊/ディスラプト [収束具] | ja_curated_spells.SPELLS | spells: SG |
| Dissonance Spike | ディソナンス・スパイク | ja_curated_entities.ENTITIES | complex_forms: KC |
| Divination | 占術 | import_ja_from_refs.CURATED | magic_arts: SG |
| Doberman | ドーベルマン | import_ja_from_refs.CURATED | mentors: SOTG |
| Door Wards | 扉の結界 | ja_curated_spells.SPELLS | spells: SG |
| Dove | 鳩 | import_ja_from_refs.CURATED | mentors: FA |
| Draining Spike | ドレイン・スパイク | ja_curated_entities.ENTITIES | echoes: KC |
| Druid | ドルイド | import_ja_from_refs.CURATED | traditions: SG |
| Earth Elemental | 大地のエレメンタル | import_ja_from_refs.CURATED | spirits: FA |
| Elemental Body | 元素の身体 | ja_curated_entities.ENTITIES | powers: SG |
| Elemental Weapon | 元素の武器 | ja_curated_entities.ENTITIES | powers: SG |
| Esdo | エスド | ja_curated_entities.ENTITIES | martial_arts: SAG |
| Euphoria | 多幸感/ユーフォリア | ja_curated_spells.SPELLS | spells: SG |
| Eurasian Jay | カケス | import_ja_from_refs.CURATED | mentors: SAG |
| Evaporate | 蒸発/エヴァポレイト | ja_curated_spells.SPELLS | spells: SSP |
| Evil Eye | 邪眼/イーヴル・アイ | ja_curated_spells.SPELLS | spells: FA |
| Exorcism | 祓魔術 | import_ja_from_refs.CURATED | magic_arts: SG / metamagics: SG |
| False Impression | 偽りの印象/フォールス・インプレッション | ja_curated_spells.SPELLS | spells: SSP |
| Far Sensing | 遠隔感知 | ja_curated_spells.SPELLS | spells: SG |
| Feign Death | 擬死 | ja_curated_entities.ENTITIES | powers: BB |
| Feign Illness | 仮病 | ja_curated_entities.ENTITIES | powers: BB |
| Fire Elemental | 火のエレメンタル | import_ja_from_refs.CURATED | spirits: FA |
| Flame Burst | 火炎バースト/フレイム・バースト | ja_curated_spells.SPELLS | spells: SSP |
| Focused Archery | 集中射法 | ja_curated_entities.ENTITIES | powers: HT |
| Forced Defense | 強制防御/フォースド・ディフェンス | ja_curated_spells.SPELLS | spells: SG |
| Forced Heuristics | 強制ヒューリスティクス | ja_curated_entities.ENTITIES | complex_forms: KC |
| Frigid | 極寒/フリジッド | ja_curated_spells.SPELLS | spells: SSP |
| Gambler | 賭博師 | import_ja_from_refs.CURATED | mentors: SHB2 |
| Generalist Sprite | ジェネラリスト・スプライト | import_ja_from_refs.CURATED | sprites: KC |
| German Jujitsu | ジャーマン柔術 | ja_curated_entities.ENTITIES | martial_arts: SAG |
| German Shepherd | ジャーマン・シェパード | import_ja_from_refs.CURATED | mentors: SOTG |
| Goddess | 女神 | import_ja_from_refs.CURATED | mentors: BOTL |
| Gravity | 重力/グラヴィティ | ja_curated_spells.SPELLS | spells: FA |
| Gravity Well | 重力井戸/グラヴィティ・ウェル | ja_curated_spells.SPELLS | spells: FA |
| Green Man | グリーンマン | import_ja_from_refs.CURATED | mentors: FA |
| Groundhog | ウッドチャック | import_ja_from_refs.CURATED | mentors: SAG |
| Growth | 成長/グロース | ja_curated_spells.SPELLS | spells: FA |
| Guanyin | 観音 | import_ja_from_refs.CURATED | mentors: BTB |
| Hand of Glory | 栄光の手/ハンド・オブ・グローリー | ja_curated_spells.SPELLS | gear: SG / spells: SG |
| Hang Time | 滞空 | ja_curated_entities.ENTITIES | powers: SG |
| Heightened Concentration | 集中力向上 | ja_curated_entities.ENTITIES | powers: SSP |
| Heinzelmännchen | ハインツェルメンヒェン | ja_curated_entities.ENTITIES | mentors: SAG |
| Hinduism | ヒンドゥー教 | import_ja_from_refs.CURATED | traditions: SG |
| Holy Text | 聖典 | ja_curated_entities.ENTITIES | mentors: FA |
| Host Emulator | ホスト・エミュレータ | ja_curated_entities.ENTITIES | complex_forms: KC |
| Hydrate | 水分補給/ハイドレート | ja_curated_spells.SPELLS | spells: SSP |
| Hyperthreading | ハイパースレッディング | ja_curated_entities.ENTITIES | complex_forms: KC |
| IC Tray | ICトレイ | ja_curated_entities.ENTITIES | complex_forms: DT |
| Ice Spear | 氷槍/アイス・スピア | ja_curated_spells.SPELLS | spells: SG |
| Ice Storm | 氷嵐/アイス・ストーム | ja_curated_spells.SPELLS | spells: SG |
| Incision | 切開/インシジョン | ja_curated_spells.SPELLS | spells: BB |
| Increase Gear Limits | 装備リミット増強/インクリース・ギア・リミット | ja_curated_spells.SPELLS | spells: SG |
| Increase Inherent Limits | 固有リミット増強/インクリース・インヒアレント・リミット | ja_curated_spells.SPELLS | spells: SG |
| Increase Noise | ノイズ増大/インクリース・ノイズ | ja_curated_spells.SPELLS | spells: SG |
| Indomitable Will | 不屈の意志 | ja_curated_entities.ENTITIES | powers: SSP |
| Inflict Disease | 発病/インフリクト・ディジーズ | ja_curated_spells.SPELLS | spells: SSP |
| Insecticide [Insect Spirit] | [昆虫精霊] 殺虫/インセクティサイド [インセクトスピリット] | ja_curated_spells.SPELLS | spells: SG |
| Insulate | 断熱/インシュレイト | ja_curated_spells.SPELLS | spells: SSP |
| Islam | イスラム教 | import_ja_from_refs.CURATED | traditions: SG |
| Keratin Control | ケラチン制御 | ja_curated_entities.ENTITIES | powers: SGE, SSP |
| Kiai | 気合 | ja_curated_entities.ENTITIES | powers: HT |
| Kinesics Mastery | キネシクス習熟 | ja_curated_entities.ENTITIES | powers: SG |
| Kreussler Fencing | クロイスラー・フェンシング | ja_curated_entities.ENTITIES | martial_arts: SOTG |
| Lash | 鞭打ち/ラッシュ | ja_curated_spells.SPELLS | spells: FA |
| Lie Detector | 嘘発見 | ja_curated_entities.ENTITIES | powers: CA |
| Light Touch | 軽い手 | ja_curated_entities.ENTITIES | powers: SS |
| Little Red Riding Hood | 赤ずきん | import_ja_from_refs.CURATED | mentors: SOTG |
| Living Focus | 生体収束具 | import_ja_from_refs.CURATED | powers: SGE, SSP |
| Looking Glass | 姿見/ルッキング・グラス | ja_curated_spells.SPELLS | spells: SSP |
| Magebolt | 魔道破/メイジボルト | ja_curated_spells.SPELLS | spells: SSP |
| Maintain Warmth | 保温 | ja_curated_entities.ENTITIES | powers: SSP |
| Masking Ward | 擬態結界 | ja_curated_spells.SPELLS | spells: SG |
| Master Archer | 弓術の達人 | ja_curated_entities.ENTITIES | powers: HT |
| Memory Displacement | 記憶転移 | ja_curated_entities.ENTITIES | powers: SSP |
| Metavariant | メタバリアント | import_ja_from_refs.CURATED | category: DT, RF |
| Mimic | 模倣 | ja_curated_entities.ENTITIES | powers: SS |
| Mindnet Extended | 広域精神網/エクステンデッド・マインドネット | ja_curated_spells.SPELLS | spells: SG |
| Mirrored Persona | ミラー・ペルソナ | ja_curated_entities.ENTITIES | complex_forms: KC |
| Misread Marks | マーク誤読 | ja_curated_entities.ENTITIES | complex_forms: DT |
| Monkey | 猿 | import_ja_from_refs.CURATED | mentors: HT |
| Moon | 月 | import_ja_from_refs.CURATED | mentors: FA |
| Multiply Food | 食料増殖/マルチプライ・フード | ja_curated_spells.SPELLS | spells: FA |
| Mystic Aptitude | 神秘の適性 | ja_curated_entities.ENTITIES | powers: BTB |
| Mystic Guardian | 神秘の守護者 | ja_curated_entities.ENTITIES | mentors: SOTG |
| Napalm Wall | ナパームの壁/ナパーム・ウォール | ja_curated_spells.SPELLS | spells: SSP |
| Nauseate | 吐き気/ノージエイト | ja_curated_spells.SPELLS | spells: SSP |
| Necromancy | 死霊術 | import_ja_from_refs.CURATED | magic_arts: SG |
| Net Bind | 網の拘束/ネット・バインド | ja_curated_spells.SPELLS | spells: SG |
| Neural Synergy | ニューラル・シナジー | ja_curated_entities.ENTITIES | echoes: KC |
| Obfuscating Ward | 隠蔽結界 | ja_curated_spells.SPELLS | spells: SG |
| Opium Den | 阿片窟/オピウム・デン | ja_curated_spells.SPELLS | spells: SG |
| Oracle | オラクル | import_ja_from_refs.CURATED | mentors: SG |
| Osmosis | 浸透 | ja_curated_entities.ENTITIES | powers: CA |
| Overdrive | オーバードライブ | ja_curated_entities.ENTITIES | complex_forms: KC / drugs: CF / gear: CF |
| Passenger | 同乗/パッセンジャー | ja_curated_spells.SPELLS | spells: SSP |
| Peacemaker | ピースメーカー | import_ja_from_refs.CURATED | mentors: SG |
| Personal Warmth | 保温/パーソナル・ウォームス | ja_curated_spells.SPELLS | spells: SSP |
| Petrify | 石化/ペトリファイ | ja_curated_spells.SPELLS | spells: SSP |
| Pinch | ピンチ | ja_curated_entities.ENTITIES | complex_forms: KC |
| Plague Cloud | 疫病の雲 | ja_curated_entities.ENTITIES | powers: SG |
| Planar Entity | 次元界の存在 | ja_curated_entities.ENTITIES | mentors: FA |
| Polarized Ward | 偏光結界 | ja_curated_spells.SPELLS | spells: SG |
| Pollutant Stream | 汚染物質噴射/ポルータント・ストリーム | ja_curated_spells.SPELLS | spells: SG |
| Pollutant Wave | 汚染物質の波/ポルータント・ウェーブ | ja_curated_spells.SPELLS | spells: SG |
| Power Swimming | 高速水泳 | ja_curated_entities.ENTITIES | powers: SSP |
| Power Swimming (Elf or Troll) | 高速水泳（エルフ／トロール） | ja_curated_entities.ENTITIES | powers: SSP |
| Precision Throwing | 精密投擲 | ja_curated_entities.ENTITIES | powers: HT |
| Predictive Analytics | 予測分析 | ja_curated_entities.ENTITIES | echoes: KC |
| Primed Charge | プライム・チャージ | ja_curated_entities.ENTITIES | complex_forms: KC |
| Protect Vehicle | ヴィークル防護/プロテクト・ヴィークル | ja_curated_spells.SPELLS | spells: SG |
| Pryon | プライオン | ja_curated_entities.ENTITIES | echoes: DTD |
| Radiation Barrier | 放射線障壁/レイディエーション・バリアー | ja_curated_spells.SPELLS | spells: SSP |
| Radiation Beam | 放射線ビーム/レイディエーション・ビーム | ja_curated_spells.SPELLS | spells: SG |
| Radiation Burst | 放射線バースト/レイディエーション・バースト | ja_curated_spells.SPELLS | spells: SG |
| Radiation Shield | 放射線シールド/レイディエーション・シールド | ja_curated_spells.SPELLS | spells: SSP |
| Rapid Draw | 早抜き | ja_curated_entities.ENTITIES | powers: SG |
| Recorded Room | 録画室/レコーデッド・ルーム | ja_curated_spells.SPELLS | spells: SSP |
| Redundancy | 冗長化 | ja_curated_entities.ENTITIES | complex_forms: DT / metatypes: DT / qualities: DT |
| Resonance Bind | 共振バインド | ja_curated_entities.ENTITIES | complex_forms: KC |
| Resonance Cache | 共振キャッシュ | ja_curated_entities.ENTITIES | complex_forms: KC |
| Resonance Resistance | 共振抵抗 | ja_curated_entities.ENTITIES | echoes: KC |
| Rewind | 巻き戻し/リワインド | ja_curated_spells.SPELLS | spells: CA |
| Rooting | 根付き | ja_curated_entities.ENTITIES | powers: SSP |
| Rosebush | 薔薇の茂み/ローズブッシュ | ja_curated_spells.SPELLS | spells: FA |
| Rot | 腐敗/ロット | ja_curated_spells.SPELLS | spells: SSP |
| Search History | 検索履歴 | ja_curated_entities.ENTITIES | complex_forms: KC |
| Secret Handshake | 秘密の握手/シークレット・ハンドシェイク | ja_curated_spells.SPELLS | spells: SSP |
| Sending | 送信/センディング | ja_curated_spells.SPELLS | spells: SSP |
| Services | 助力 | import_ja_from_refs.CURATED | category: RF |
| Siphon | サイフォン | ja_curated_entities.ENTITIES | echoes: DTD |
| Skate | 滑走 | ja_curated_entities.ENTITIES | powers: SG |
| Slash | 斬撃/スラッシュ | ja_curated_spells.SPELLS | spells: FA |
| Slow Vehicle | ヴィークル減速/スロー・ヴィークル | ja_curated_spells.SPELLS | spells: SG |
| Smith | 鍛冶師 | import_ja_from_refs.CURATED | mentors: SHB2 |
| Sourcerer Daemon | ソーサラー・デーモン | ja_curated_entities.ENTITIES | echoes: KC |
| Spirit Claw | 精霊の爪 | ja_curated_entities.ENTITIES | powers: SG |
| Spirit Ram | 精霊の衝角 | ja_curated_entities.ENTITIES | powers: SG |
| Sprite Pet | スプライト・ペット | ja_curated_entities.ENTITIES | complex_forms: KC |
| Squirrel | リス | import_ja_from_refs.CURATED | mentors: SAG |
| Stag | 牡鹿 | import_ja_from_refs.CURATED | mentors: FA |
| State of Purity | 清浄なる境地 | ja_curated_entities.ENTITIES | powers: BTB |
| Sternschutz Tactical | シュテルンシュッツ・タクティカル | ja_curated_entities.ENTITIES | martial_arts: SAG |
| Stillness | 静止 | ja_curated_entities.ENTITIES | powers: SG |
| Sunbeam | 太陽光線/サンビーム | ja_curated_spells.SPELLS | spells: SSP |
| Supernatural Toughness | 超常の頑健さ | ja_curated_entities.ENTITIES | powers: SSP |
| Switch Vehicle Signature | ヴィークル・シグネチャー切替/スイッチ・ヴィークル・シグネチャー | ja_curated_spells.SPELLS | spells: SG |
| Symbolic Link | 象徴リンク/シンボリック・リンク | ja_curated_spells.SPELLS | spells: SG |
| The Adversary | 敵対者 | ja_curated_entities.ENTITIES | mentors: HT |
| The Van der Waals Effect | ファンデルワールス効果 | ja_curated_entities.ENTITIES | echoes: KC |
| Thorn | 棘/ソーン | ja_curated_spells.SPELLS | spells: FA |
| Tide | 潮 | import_ja_from_refs.CURATED | mentors: SAG |
| Tohu Wa-Bohu | トフ・ワ・ボフ | ja_curated_entities.ENTITIES | mentors: FA |
| Toxic Strike | 毒撃 | ja_curated_entities.ENTITIES | powers: SG |
| Transmit Damage | ダメージ転送 | ja_curated_entities.ENTITIES | powers: BB |
| Trap Ward | 罠結界 | ja_curated_spells.SPELLS | spells: SG |
| Traveler | 旅暮らし | ja_curated_entities.ENTITIES | lifestyles: RF |
| Treasure Hunter | トレジャーハンター | import_ja_from_refs.CURATED | mentors: SOTG |
| Turn To Goo | 粘液化/ターン・トゥ・グー | ja_curated_spells.SPELLS | spells: SG |
| Urban Brawl Parkour | アーバンブロウル・パルクール | ja_curated_entities.ENTITIES | martial_arts: SAG |
| Ventriloquism | 腹話術 | ja_curated_entities.ENTITIES | powers: CA |
| Vines | 蔦/ヴァインズ | ja_curated_spells.SPELLS | spells: FA |
| Vodou | ヴォドゥン | import_ja_from_refs.CURATED | traditions: SG |
| War | 戦争 | import_ja_from_refs.CURATED | mentors: FA |
| Water Elemental | 水のエレメンタル | import_ja_from_refs.CURATED | spirits: FA |
| Way of Unified Mana (Hapsum-Do) | 統一マナの道（ハプスムドー） | ja_curated_entities.ENTITIES | martial_arts: FA |
| Weaken Data Bomb | データボム弱体化 | ja_curated_entities.ENTITIES | complex_forms: KC |
| Weaken Encryption | 暗号化弱体化 | ja_curated_entities.ENTITIES | complex_forms: KC |
| Weimaraner | ワイマラナー | import_ja_from_refs.CURATED | mentors: SOTG |
| Whale | 鯨 | import_ja_from_refs.CURATED | mentors: HS |
| Wild Hunt | ワイルドハント | import_ja_from_refs.CURATED | mentors: SAG |
| Will of the Resonance | 共振の意志 | ja_curated_entities.ENTITIES | echoes: KC |
| Zombie | ゾンビ | ja_curated_spells.SPELLS | spells: HT |
| Zoroastrianism | ゾロアスター教 | import_ja_from_refs.CURATED | traditions: SG |
| [Critter] Form | [クリッター] 化/[クリッター] フォーム | ja_curated_spells.SPELLS | spells: SG |
| [Element] Aura | [元素] のオーラ/[エレメント] オーラ | ja_curated_spells.SPELLS | spells: SG |
| [Element] Grenade | [元素] 手榴弾/[エレメント] グレネード | ja_curated_spells.SPELLS | spells: SSP |
| [Element] Wall | [元素] の壁/[エレメント] ウォール | ja_curated_spells.SPELLS | spells: SG |

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

## ja_curated_sr5.SR5 (2)

| English | 日本語 | 品目 |
|---|---|---|
| Heavy [SR5] | 大型武器マウント | weapon_mounts: SR5 |
| Standard [SR5] | 武器マウント | weapon_mounts: SR5 |

## ja_curated_entities.ENTITIES (134)

| English | 日本語 | 品目 |
|---|---|---|
| (Synth)Leather | （合成）レザー | armor_mods: SR5 |
| Adept Accident | アデプト・アクシデント | powers: HT |
| Adept Spell | アデプト呪文 | powers: HT |
| Aegis | イージス | echoes: KC |
| Alpine Wrestling | アルパイン・レスリング | martial_arts: SAG |
| Arbeitskreis INI | アルバイツクライスINI | martial_arts: SOTG |
| Arc Feedback | アーク・フィードバック | complex_forms: KC |
| Asthenologica | アステノロジカ | martial_arts: SOTG |
| Belt-Feed, 100-round | ベルト給弾, 100発 | weapon_accessories: SR5 |
| Berserker Temper | 狂戦士の気質 | — |
| Berserker's Rage | 狂戦士の怒り | powers: SG |
| Body Sculpt | 肉体成形 | powers: BLB |
| Bolt Hole | 隠れ家 | lifestyles: RF |
| Bootleg Program | 海賊版プログラム | complex_forms: KC |
| Capricorn | カプリコーン | mentors: SAG |
| Causal Nexus | 因果連結 | complex_forms: KC |
| Chemical Protection | 化学防護 | armor_mods: SR5 |
| Circle Fencing | サークル・フェンシング | martial_arts: SOTG |
| Commercial | 商業施設 | lifestyles: RF |
| Contaminate | コンタミネート | echoes: DTD |
| Coriolis | コリオリ | complex_forms: CF |
| Cyber Microgrenade Launcher | サイバー・マイクログレネードランチャー | — |
| Defrag | デフラグ | echoes: DTR |
| Demara | ディマラ | powers: SSP |
| Derezz | デレズ | complex_forms: DT |
| Dissonance Spike | ディソナンス・スパイク | complex_forms: KC |
| Draining Spike | ドレイン・スパイク | echoes: KC |
| Drum Magazine, 24-round | ドラムマガジン, 24発 | weapon_accessories: SR5 |
| Drum Magazine, 32-round | ドラムマガジン, 32発 | weapon_accessories: SR5 |
| Electrochromic Clothing | エレクトロクロミック・クロージング | armor_mods: SR5 |
| Elemental Body | 元素の身体 | powers: SG |
| Elemental Weapon | 元素の武器 | powers: SG |
| Esdo | エスド | martial_arts: SAG |
| Essence Antihole | エッセンス・アンチホール | cyberware: SR5 |
| External Power Source | 外部電源 | weapon_accessories: SR5 |
| Feign Death | 擬死 | powers: BB |
| Feign Illness | 仮病 | powers: BB |
| Fire Resistance | 耐火 | armor_mods: SR5 |
| Focused Archery | 集中射法 | powers: HT |
| Forced Heuristics | 強制ヒューリスティクス | complex_forms: KC |
| Full Body Armor: Chemical Seal | フルボディアーマー：化学遮断 | armor_mods: SR5 |
| Full Body Armor: Environment Adaptation | フルボディアーマー：環境適応 | armor_mods: SR5 |
| Full Body Armor: Helmet | フルボディアーマー：ヘルメット | armor_mods: SR5 |
| German Jujitsu | ジャーマン柔術 | martial_arts: SAG |
| Hang Time | 滞空 | powers: SG |
| Heightened Concentration | 集中力向上 | powers: SSP |
| Heinzelmännchen | ハインツェルメンヒェン | mentors: SAG |
| Holy Text | 聖典 | mentors: FA |
| Host Emulator | ホスト・エミュレータ | complex_forms: KC |
| Hyperthreading | ハイパースレッディング | complex_forms: KC |
| IC Tray | ICトレイ | complex_forms: DT |
| Improved Potential (Chaos Mentor) | 潜在力強化：(混沌メンター) | — |
| Indomitable Will | 不屈の意志 | powers: SSP |
| Insulation | 断熱 | armor_mods: SR5 / bioware: CF |
| Keratin Control | ケラチン制御 | powers: SGE, SSP |
| Kiai | 気合 | powers: HT |
| Kinesics Mastery | キネシクス習熟 | powers: SG |
| Kreussler Fencing | クロイスラー・フェンシング | martial_arts: SOTG |
| Lie Detector | 嘘発見 | powers: CA |
| Light Touch | 軽い手 | powers: SS |
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
| Maintain Warmth | 保温 | powers: SSP |
| Master Archer | 弓術の達人 | powers: HT |
| Memory Displacement | 記憶転移 | powers: SSP |
| Mimic | 模倣 | powers: SS |
| Mirrored Persona | ミラー・ペルソナ | complex_forms: KC |
| Misread Marks | マーク誤読 | complex_forms: DT |
| Mystic Aptitude | 神秘の適性 | powers: BTB |
| Mystic Guardian | 神秘の守護者 | mentors: SOTG |
| Neural Synergy | ニューラル・シナジー | echoes: KC |
| Nonconductivity | 非導電 | armor_mods: SR5 |
| Osmosis | 浸透 | powers: CA |
| Overdrive | オーバードライブ | complex_forms: KC / drugs: CF / gear: CF |
| Pinch | ピンチ | complex_forms: KC |
| Plague Cloud | 疫病の雲 | powers: SG |
| Planar Entity | 次元界の存在 | mentors: FA |
| Power Swimming | 高速水泳 | powers: SSP |
| Power Swimming (Elf or Troll) | 高速水泳（エルフ／トロール） | powers: SSP |
| Precision Throwing | 精密投擲 | powers: HT |
| Predictive Analytics | 予測分析 | echoes: KC |
| Primed Charge | プライム・チャージ | complex_forms: KC |
| Pryon | プライオン | echoes: DTD |
| Rapid Draw | 早抜き | powers: SG |
| Redundancy | 冗長化 | complex_forms: DT / metatypes: DT / qualities: DT |
| Resonance Bind | 共振バインド | complex_forms: KC |
| Resonance Cache | 共振キャッシュ | complex_forms: KC |
| Resonance Resistance | 共振抵抗 | echoes: KC |
| Riposte | リポスト | martial_art_techniques: RG / powers: SG |
| Rooting | 根付き | powers: SSP |
| Search History | 検索履歴 | complex_forms: KC |
| Shock Frills | ショックフリル | armor_mods: SR5 |
| Silencer (Ares Light Fire 70) | 消音器（アレス・ライトファイア70） | weapon_accessories: SR5 |
| Silencer (Ares Light Fire 75) | 消音器（アレス・ライトファイア75） | weapon_accessories: SR5 |
| Siphon | サイフォン | echoes: DTD |
| Skate | 滑走 | powers: SG |
| Sourcerer Daemon | ソーサラー・デーモン | echoes: KC |
| Spirit Claw | 精霊の爪 | powers: SG |
| Spirit Ram | 精霊の衝角 | powers: SG |
| Sprite Pet | スプライト・ペット | complex_forms: KC |
| State of Purity | 清浄なる境地 | powers: BTB |
| Sternschutz Tactical | シュテルンシュッツ・タクティカル | martial_arts: SAG |
| Stillness | 静止 | powers: SG |
| Supernatural Toughness | 超常の頑健さ | powers: SSP |
| The Adversary | 敵対者 | mentors: HT |
| The Van der Waals Effect | ファンデルワールス効果 | echoes: KC |
| Thermal Damping | 熱感知抑制 | armor_mods: SR5 |
| Tohu Wa-Bohu | トフ・ワ・ボフ | mentors: FA |
| Toxic Strike | 毒撃 | powers: SG |
| Transmit Damage | ダメージ転送 | powers: BB |
| Traveler | 旅暮らし | lifestyles: RF |
| Urban Brawl Parkour | アーバンブロウル・パルクール | martial_arts: SAG |
| Urban Explorer Jumpsuit: Helmet | アーバンエクスプローラー・ジャンプスーツ：ヘルメット | armor_mods: SR5 |
| Ventriloquism | 腹話術 | powers: CA |
| Way of Unified Mana (Hapsum-Do) | 統一マナの道（ハプスムドー） | martial_arts: FA |
| Weaken Data Bomb | データボム弱体化 | complex_forms: KC |
| Weaken Encryption | 暗号化弱体化 | complex_forms: KC |
| Will of the Resonance | 共振の意志 | echoes: KC |

## ja_curated_spells.SPELLS (100)

| English | 日本語 | 品目 |
|---|---|---|
| Air Filter | 空気清浄/エア・フィルター | spells: SSP |
| Alarm Ward | 警報結界 | spells: SG |
| Alleviate [Allergy] | [アレルギー] 緩和/アリーヴィエイト [アラジー] | spells: SG |
| Alter Ballistics | 弾道変更/オルター・バリスティクス | spells: FA |
| Alter Temperature | 温度変化/オルター・テンパレチャー | spells: SSP |
| Ambidexterity | 両利き/アンビデクステリティ | spells: SG |
| Astral Doppelganger | アストラル・ドッペルゲンガー | spells: SG |
| Astral Message | アストラル伝言/アストラル・メッセージ | spells: SG |
| Attune Animal | 動物同調 | spells: SG |
| Attune Item | 物品同調 | spells: SG |
| Barrage | 弾幕/バラージュ | enhancements: SG / spells: FA |
| Branch | 枝/ブランチ | spells: FA |
| Broadcast | 放送/ブロードキャスト | spells: SSP |
| Bug Zapper | 殺虫器/バグ・ザッパー | spells: SG |
| Calling [Spirit Type] | [精霊タイプ] 呼び出し | spells: SG |
| Catch | 捕球/キャッチ | spells: HT |
| Charged Ward | 充填結界 | spells: SG |
| Chill | 冷却/チル | spells: SSP |
| Circle of Cleansing | 浄化円 | spells: SG |
| Claw | 爪撃/クロウ | spells: FA |
| Comet | 彗星/コメット | spells: FA |
| Conceal Scent | 匂い隠し/コンシール・セント | spells: HT |
| Consistency | 一貫性/コンシステンシー | spells: CA |
| Convince | 説得/コンヴィンス | spells: SS |
| Create Ally Spirit | 同盟精霊創造 | spells: SG |
| Decontamination | 除染/デコンタミネーション | spells: SSP |
| Decoy | 囮/デコイ | spells: SG |
| Decrease Gear Limits | 装備リミット減退/ディクリース・ギア・リミット | spells: SG |
| Decrease Inherent Limits | 固有リミット減退/ディクリース・インヒアレント・リミット | spells: SG |
| Decrease Noise | ノイズ減少/ディクリース・ノイズ | spells: SG |
| Dehydrate | 脱水/デハイドレート | spells: SSP |
| Destroy [Free Spirit] | [自由精霊] 破壊/デストロイ [フリースピリット] | spells: SG |
| Destroy [Vehicle] | [ヴィークル] 破壊/デストロイ [ヴィークル] | spells: SG |
| Dispersion Circle | 拡散円 | spells: SG |
| Disrupt [Focus] | [収束具] 破壊/ディスラプト [収束具] | spells: SG |
| Door Wards | 扉の結界 | spells: SG |
| Euphoria | 多幸感/ユーフォリア | spells: SG |
| Evaporate | 蒸発/エヴァポレイト | spells: SSP |
| Evil Eye | 邪眼/イーヴル・アイ | spells: FA |
| False Impression | 偽りの印象/フォールス・インプレッション | spells: SSP |
| Far Sensing | 遠隔感知 | spells: SG |
| Flame Burst | 火炎バースト/フレイム・バースト | spells: SSP |
| Forced Defense | 強制防御/フォースド・ディフェンス | spells: SG |
| Frigid | 極寒/フリジッド | spells: SSP |
| Gravity | 重力/グラヴィティ | spells: FA |
| Gravity Well | 重力井戸/グラヴィティ・ウェル | spells: FA |
| Growth | 成長/グロース | spells: FA |
| Hand of Glory | 栄光の手/ハンド・オブ・グローリー | gear: SG / spells: SG |
| Hydrate | 水分補給/ハイドレート | spells: SSP |
| Ice Spear | 氷槍/アイス・スピア | spells: SG |
| Ice Storm | 氷嵐/アイス・ストーム | spells: SG |
| Incision | 切開/インシジョン | spells: BB |
| Increase Gear Limits | 装備リミット増強/インクリース・ギア・リミット | spells: SG |
| Increase Inherent Limits | 固有リミット増強/インクリース・インヒアレント・リミット | spells: SG |
| Increase Noise | ノイズ増大/インクリース・ノイズ | spells: SG |
| Inflict Disease | 発病/インフリクト・ディジーズ | spells: SSP |
| Insecticide [Insect Spirit] | [昆虫精霊] 殺虫/インセクティサイド [インセクトスピリット] | spells: SG |
| Insulate | 断熱/インシュレイト | spells: SSP |
| Lash | 鞭打ち/ラッシュ | spells: FA |
| Looking Glass | 姿見/ルッキング・グラス | spells: SSP |
| Magebolt | 魔道破/メイジボルト | spells: SSP |
| Masking Ward | 擬態結界 | spells: SG |
| Mindnet Extended | 広域精神網/エクステンデッド・マインドネット | spells: SG |
| Multiply Food | 食料増殖/マルチプライ・フード | spells: FA |
| Napalm Wall | ナパームの壁/ナパーム・ウォール | spells: SSP |
| Nauseate | 吐き気/ノージエイト | spells: SSP |
| Net Bind | 網の拘束/ネット・バインド | spells: SG |
| Obfuscating Ward | 隠蔽結界 | spells: SG |
| Opium Den | 阿片窟/オピウム・デン | spells: SG |
| Passenger | 同乗/パッセンジャー | spells: SSP |
| Personal Warmth | 保温/パーソナル・ウォームス | spells: SSP |
| Petrify | 石化/ペトリファイ | spells: SSP |
| Polarized Ward | 偏光結界 | spells: SG |
| Pollutant Stream | 汚染物質噴射/ポルータント・ストリーム | spells: SG |
| Pollutant Wave | 汚染物質の波/ポルータント・ウェーブ | spells: SG |
| Protect Vehicle | ヴィークル防護/プロテクト・ヴィークル | spells: SG |
| Radiation Barrier | 放射線障壁/レイディエーション・バリアー | spells: SSP |
| Radiation Beam | 放射線ビーム/レイディエーション・ビーム | spells: SG |
| Radiation Burst | 放射線バースト/レイディエーション・バースト | spells: SG |
| Radiation Shield | 放射線シールド/レイディエーション・シールド | spells: SSP |
| Recorded Room | 録画室/レコーデッド・ルーム | spells: SSP |
| Rewind | 巻き戻し/リワインド | spells: CA |
| Rosebush | 薔薇の茂み/ローズブッシュ | spells: FA |
| Rot | 腐敗/ロット | spells: SSP |
| Secret Handshake | 秘密の握手/シークレット・ハンドシェイク | spells: SSP |
| Sending | 送信/センディング | spells: SSP |
| Slash | 斬撃/スラッシュ | spells: FA |
| Slow Vehicle | ヴィークル減速/スロー・ヴィークル | spells: SG |
| Sunbeam | 太陽光線/サンビーム | spells: SSP |
| Switch Vehicle Signature | ヴィークル・シグネチャー切替/スイッチ・ヴィークル・シグネチャー | spells: SG |
| Symbolic Link | 象徴リンク/シンボリック・リンク | spells: SG |
| Thorn | 棘/ソーン | spells: FA |
| Trap Ward | 罠結界 | spells: SG |
| Turn To Goo | 粘液化/ターン・トゥ・グー | spells: SG |
| Vines | 蔦/ヴァインズ | spells: FA |
| Zombie | ゾンビ | spells: HT |
| [Critter] Form | [クリッター] 化/[クリッター] フォーム | spells: SG |
| [Element] Aura | [元素] のオーラ/[エレメント] オーラ | spells: SG |
| [Element] Grenade | [元素] 手榴弾/[エレメント] グレネード | spells: SSP |
| [Element] Wall | [元素] の壁/[エレメント] ウォール | spells: SG |

## import_ja_from_refs.CURATED (96)

| English | 日本語 | 品目 |
|---|---|---|
| Academic | 学術 | — |
| Acceleration | 加速値 | category: R5 |
| Acting | 演技 | — |
| Advanced Alchemy | 上級錬金術 | magic_arts: SG / metamagics: SG |
| Advanced Ritual Casting | 上級儀式行使 | magic_arts: SG |
| Advanced Spellcasting | 上級呪文行使 | magic_arts: SG |
| Air Elemental | 大気のエレメンタル | spirits: FA |
| Architect | 建築家 | life_modules: RF / mentors: SOTG / paragons: KC |
| Artist | 芸術家 | mentors: SHB2 |
| Athletics | 運動 | — |
| Attributes | 能力値 | — |
| BTLs | BTLチップ | category: CF, SR5 |
| Badger | アナグマ | mentors: SOTG |
| Berserker | バーサーカー | mentors: SG / qualities: RF |
| Biotech | 医療 | category: 2050, BB, CF, NF, SR5 |
| Blood Magic | 血の魔術 | magic_arts: SG |
| Body | 強靱力 | category: R5 |
| Brother in Arms | 戦友 | mentors: SOTG |
| Buddhism | 仏教 | traditions: SG |
| Close Combat | 近接戦闘 | — |
| Combat | 戦闘 | category: FA, HT, SG, SR5, SSP |
| Combat Active | 戦闘系能動技能 | category: SR5 |
| Companion Sprite | コンパニオン・スプライト | sprites: KC |
| Conjuring | 召喚 | — |
| Cracking | クラッキング | — |
| Death | 死 | mentors: FA |
| Detection | 探知 | category: BB, CA, SG, SR5, SSP |
| Divination | 占術 | magic_arts: SG |
| Doberman | ドーベルマン | mentors: SOTG |
| Dove | 鳩 | mentors: FA |
| Druid | ドルイド | traditions: SG |
| Dwarf | ドワーフ | metatypes: SR5 |
| Earth Elemental | 大地のエレメンタル | spirits: FA |
| Electronics | エレクトロニクス | — |
| Elf | エルフ | metatypes: SR5 |
| Enchanting | 付術 | — |
| Eurasian Jay | カケス | mentors: SAG |
| Exorcism | 祓魔術 | magic_arts: SG / metamagics: SG |
| Fire Elemental | 火のエレメンタル | spirits: FA |
| Foci | 収束具 | category: SR5 |
| Gambler | 賭博師 | mentors: SHB2 |
| Generalist Sprite | ジェネラリスト・スプライト | sprites: KC |
| German Shepherd | ジャーマン・シェパード | mentors: SOTG |
| Goddess | 女神 | mentors: BOTL |
| Green Man | グリーンマン | mentors: FA |
| Groundhog | ウッドチャック | mentors: SAG |
| Guanyin | 観音 | mentors: BTB |
| Health | 身体 | category: FA, SG, SR5, SSP |
| Hinduism | ヒンドゥー教 | traditions: SG |
| Human | ヒューマン | metatypes: SR5 |
| Illusion | 幻影 | category: CA, SG, SR5, SS, SSP |
| Interest | 趣味 | — |
| Islam | イスラム教 | traditions: SG |
| Language | 言語 | — |
| Little Red Riding Hood | 赤ずきん | mentors: SOTG |
| Living Focus | 生体収束具 | powers: SGE, SSP |
| Magical Active | 魔法系能動技能 | category: SR5 |
| Manipulation | 操作 | category: BB, BTB, CA, FA, HT, SG, SR5, SS, SSP |
| Metahuman | メタヒューマン | category: RF, SR5 |
| Metavariant | メタバリアント | category: DT, RF |
| Monkey | 猿 | mentors: HT |
| Moon | 月 | mentors: FA |
| Mundane | マンディン | category: SR5 |
| Necromancy | 死霊術 | magic_arts: SG |
| Oracle | オラクル | mentors: SG |
| Ork | オーク | metatypes: SR5 |
| Outdoors | 野外 | — |
| Peacemaker | ピースメーカー | mentors: SG |
| Physical Active | 身体系能動技能 | category: SR5 |
| Power Point | パワー・ポイント | metamagics: SR5 |
| Professional | 職業 | — |
| Resonance Active | 共振力系能動技能 | category: SR5 |
| Rigger Interface | リガー・コマンド・インターフェース | vehicle_mods: SR5 |
| Run and Gun | ラン＆ガン | — |
| Services | 助力 | category: RF |
| Shadowrun 5th Edition | シャドウラン 第5版 | — |
| Smith | 鍛冶師 | mentors: SHB2 |
| Social | 社交 | — |
| Social Active | 社交系能動技能 | category: SR5 |
| Sorcery | 魔術 | — |
| Squirrel | リス | mentors: SAG |
| Stag | 牡鹿 | mentors: FA |
| Street | 街 | lifestyles: SR5 |
| Tasking | タスキング | — |
| Technical Active | 技術系能動技能 | category: SR5 |
| Tide | 潮 | mentors: SAG |
| Treasure Hunter | トレジャーハンター | mentors: SOTG |
| Troll | トロール | metatypes: SR5 |
| Vehicle Active | ヴィークル系能動技能 | category: SR5 |
| Vodou | ヴォドゥン | traditions: SG |
| War | 戦争 | mentors: FA |
| Water Elemental | 水のエレメンタル | spirits: FA |
| Weimaraner | ワイマラナー | mentors: SOTG |
| Whale | 鯨 | mentors: HS |
| Wild Hunt | ワイルドハント | mentors: SAG |
| Zoroastrianism | ゾロアスター教 | traditions: SG |

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
| SR5 | Shadowrun 5th Edition | あり | 931 | 96 | 0 | 62 |
| RF | Run Faster |  | 17 | 18 | 6 | 720 |
| CF | Chrome Flesh |  | 5 | 29 | 15 | 495 |
| RG | Run and Gun | あり | 427 | 34 | 0 | 14 |
| R5 | Rigger 5.0 |  | 7 | 17 | 0 | 362 |
| 2050 | Shadowrun 2050 (German-Only) |  | 14 | 23 | 0 | 341 |
| SG | Street Grimoire |  | 137 | 113 | 0 | 102 |
| FA | Forbidden Arcana |  | 4 | 38 | 0 | 233 |
| KC | Kill Code |  | 1 | 36 | 3 | 171 |
| HT | Hard Targets |  | 10 | 34 | 11 | 147 |
| DT | Data Trails |  | 2 | 21 | 2 | 175 |
| SL | Street Lethal |  | 16 | 12 | 0 | 137 |
| SAG | State of the Art ADL (German-Only) |  | 8 | 26 | 0 | 130 |
| CA | Cutting Aces |  | 7 | 17 | 0 | 106 |
| SS | Stolen Souls |  | 13 | 12 | 0 | 57 |
| SSP | Shadow Spells |  | 1 | 62 | 0 | 11 |
| KK | Krime Katalog |  | 10 | 4 | 0 | 57 |
| SOTG | Datapuls SOTA 2080 (German-Only) |  | 6 | 19 | 0 | 46 |
| DTR | Dark Terrors |  | 2 | 4 | 0 | 62 |
| NF | No Future |  | 2 | 11 | 0 | 53 |
| HS | Howling Shadows |  | 12 | 9 | 0 | 41 |
| PBG | Parabotany (German-Only) |  | 1 | 1 | 0 | 45 |
| BTB | Better Than Bad |  | 0 | 7 | 2 | 37 |
| GH3 | Gun Heaven 3 |  | 11 | 0 | 0 | 34 |
| BB | Bullets & Bandages |  | 0 | 13 | 0 | 31 |
| TCT | The Complete Trog |  | 3 | 6 | 0 | 30 |
| LCD | Lockdown |  | 0 | 4 | 0 | 27 |
| SHB | Schattenhandbuch (German-Only) |  | 3 | 2 | 0 | 23 |
| PGG | Parageology (German-Only) |  | 0 | 1 | 0 | 23 |
| HAMG | Datapuls Hamburg (German-Only) |  | 2 | 3 | 0 | 18 |
| HKS | Hong Kong Sourcebook |  | 0 | 2 | 0 | 17 |
| QSR | Shadowrun Quick-Start Rules |  | 0 | 0 | 0 | 17 |
| SFB | Shadows In Focus: Butte |  | 0 | 2 | 0 | 10 |
| TSG | The Seattle Gambit |  | 1 | 2 | 0 | 9 |
| SHB2 | Schattenhandbuch 2 (German-Only) |  | 3 | 3 | 0 | 5 |
| SHB3 | Schattenhandbuch 3 (German-Only) |  | 0 | 3 | 0 | 8 |
| SFCR | Shadows In Focus: Casablanca-Rabat |  | 0 | 1 | 0 | 9 |
| AP | Assassin's Primer |  | 1 | 2 | 0 | 6 |
| PZG | Parazoology (German-Only) |  | 0 | 2 | 0 | 7 |
| SASS | Sail Away, Sweet Sister |  | 4 | 2 | 0 | 3 |
| SFME | Shadows In Focus: Metropole |  | 0 | 1 | 0 | 7 |
| TCG |  |  | 0 | 0 | 0 | 7 |
| BOTL | Book of the Lost |  | 0 | 2 | 0 | 3 |
| SFMO | Shadows In Focus: Morocco |  | 0 | 0 | 0 | 5 |
| SLG3 | Schattenload 3 (German-Only) |  | 0 | 0 | 0 | 5 |
| SOXG | Datapuls SOX 2080 (German-Only) |  | 0 | 0 | 0 | 4 |
| TVG | The Vladivostok Gauntlet |  | 0 | 1 | 0 | 3 |
| DTD | Data Trails (Dissonant Echoes) |  | 0 | 3 | 0 | 0 |
| SGE | Street Grimoire Errata |  | 1 | 2 | 0 | 0 |
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
| BLB | Bloody Business |  | 0 | 1 | 0 | 0 |
| GE | Grimmes Erwachen (German-Only) |  | 0 | 0 | 0 | 1 |
| SFCC | Shadows In Focus: Sioux Nation: Counting Coup |  | 0 | 1 | 0 | 0 |

