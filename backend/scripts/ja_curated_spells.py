"""Hand translations for spells / rituals / enchantments still on English
fallback (Phase 2b, see docs/plans/translation-plan.md).

Scope: only entries that are a common English word with an unambiguous JP form,
or a compositional parallel to a spell already translated upstream (the Ward /
Circle / "Increase [X]" / "Extended" families). Obscure supplement-specific
coinages (most blood-magic, necro, geomancy, feng-shui and infected rituals)
are deliberately left on English fallback rather than guessed at.

House style, matching the ~193 entries already translated upstream:
  * spells:      "漢語訳/カタカナ音写"  e.g. 酸噴射/アシッド・ストリーム
  * rituals:     漢語のみ               e.g. 治癒円 / 結界 / 遠隔探知
  * bracketed placeholders kept on both sides:
      [Element]→[元素]/[エレメント], [Critter]→[クリッター]
  * "Extended" variant: 広域〜/エクステンデッド・〜

Consumed by import_ja_from_refs.py; every key is verified against catalog()
by tests/test_translation_overrides.py (orphan check).
"""

from __future__ import annotations

SPELLS: dict[str, str] = {
    # --- Combat ---------------------------------------------------------------
    "Disrupt [Focus]": "[フォーカス] 破壊/ディスラプト [フォーカス]",
    "Destroy [Free Spirit]": "[自由精霊] 破壊/デストロイ [フリースピリット]",
    "Destroy [Vehicle]": "[ヴィークル] 破壊/デストロイ [ヴィークル]",
    "Insecticide [Insect Spirit]": "[昆虫精霊] 殺虫/インセクティサイド [インセクトスピリット]",
    "Ice Spear": "氷槍/アイス・スピア",
    "Ice Storm": "氷嵐/アイス・ストーム",
    "Radiation Beam": "放射線ビーム/レイディエーション・ビーム",
    "Radiation Burst": "放射線バースト/レイディエーション・バースト",
    "Pollutant Stream": "汚染物質噴射/ポルータント・ストリーム",
    "Pollutant Wave": "汚染物質の波/ポルータント・ウェーブ",
    "Chill": "冷却/チル",
    "Frigid": "極寒/フリジッド",
    "Flame Burst": "火炎バースト/フレイム・バースト",
    "Magebolt": "魔道破/メイジボルト",
    "[Element] Grenade": "[元素] 手榴弾/[エレメント] グレネード",
    "Sunbeam": "太陽光線/サンビーム",
    "Lash": "鞭打ち/ラッシュ",
    "Slash": "斬撃/スラッシュ",
    "Claw": "爪撃/クロウ",
    "Barrage": "弾幕/バラージュ",
    "Comet": "彗星/コメット",
    "Evil Eye": "邪眼/イーヴル・アイ",
    # --- Detection ----------------------------------------------------------
    "Astral Message": "アストラル伝言/アストラル・メッセージ",
    "Mindnet Extended": "広域精神網/エクステンデッド・マインドネット",
    "Passenger": "同乗/パッセンジャー",
    "Recorded Room": "録画室/レコーデッド・ルーム",
    "Secret Handshake": "秘密の握手/シークレット・ハンドシェイク",
    "Broadcast": "放送/ブロードキャスト",
    "Sending": "送信/センディング",
    "Consistency": "一貫性/コンシステンシー",
    # --- Health -----------------------------------------------------------
    "Ambidexterity": "両利き/アンビデクステリティ",
    "Alleviate [Allergy]": "[アレルギー] 緩和/アリーヴィエイト [アラジー]",
    "Forced Defense": "強制防御/フォースド・ディフェンス",
    "Increase Inherent Limits": "固有リミット増強/インクリース・インヒアレント・リミット",
    "Decrease Inherent Limits": "固有リミット減退/ディクリース・インヒアレント・リミット",
    "Decontamination": "除染/デコンタミネーション",
    "Dehydrate": "脱水/デハイドレート",
    "Hydrate": "水分補給/ハイドレート",
    "Inflict Disease": "発病/インフリクト・ディジーズ",
    "Nauseate": "吐き気/ノージエイト",
    "Personal Warmth": "保温/パーソナル・ウォームス",
    "Rot": "腐敗/ロット",
    "Multiply Food": "食料増殖/マルチプライ・フード",
    # --- Illusion --------------------------------------------------------
    "Decoy": "囮/デコイ",
    "Euphoria": "多幸感/ユーフォリア",
    "Opium Den": "阿片窟/オピウム・デン",
    "Switch Vehicle Signature": "ヴィークル・シグネチャー切替/スイッチ・ヴィークル・シグネチャー",
    "False Impression": "偽りの印象/フォールス・インプレッション",
    # --- Manipulation --------------------------------------------------
    "Net Bind": "網の拘束/ネット・バインド",
    "Bug Zapper": "殺虫器/バグ・ザッパー",
    "[Element] Aura": "[元素] のオーラ/[エレメント] オーラ",
    "[Element] Wall": "[元素] の壁/[エレメント] ウォール",
    "Increase Noise": "ノイズ増大/インクリース・ノイズ",
    "Decrease Noise": "ノイズ減少/ディクリース・ノイズ",
    "Increase Gear Limits": "装備リミット増強/インクリース・ギア・リミット",
    "Decrease Gear Limits": "装備リミット減退/ディクリース・ギア・リミット",
    "Protect Vehicle": "ヴィークル防護/プロテクト・ヴィークル",
    "Slow Vehicle": "ヴィークル減速/スロー・ヴィークル",
    "[Critter] Form": "[クリッター] 化/[クリッター] フォーム",
    "Turn To Goo": "粘液化/ターン・トゥ・グー",
    "Incision": "切開/インシジョン",
    "Convince": "説得/コンヴィンス",
    "Air Filter": "空気清浄/エア・フィルター",
    "Alter Temperature": "温度変化/オルター・テンパレチャー",
    "Evaporate": "蒸発/エヴァポレイト",
    "Looking Glass": "姿見/ルッキング・グラス",
    "Insulate": "断熱/インシュレイト",
    "Napalm Wall": "ナパームの壁/ナパーム・ウォール",
    "Petrify": "石化/ペトリファイ",
    "Radiation Shield": "放射線シールド/レイディエーション・シールド",
    "Radiation Barrier": "放射線障壁/レイディエーション・バリアー",
    "Catch": "捕球/キャッチ",
    "Conceal Scent": "匂い隠し/コンシール・セント",
    "Rewind": "巻き戻し/リワインド",
    "Branch": "枝/ブランチ",
    "Vines": "蔦/ヴァインズ",
    "Thorn": "棘/ソーン",
    "Rosebush": "薔薇の茂み/ローズブッシュ",
    "Growth": "成長/グロース",
    "Gravity": "重力/グラヴィティ",
    "Gravity Well": "重力井戸/グラヴィティ・ウェル",
    "Alter Ballistics": "弾道変更/オルター・バリスティクス",
    # --- Rituals (漢語のみ; Ward / Circle 系の合成語に限る) --------------------
    "Alarm Ward": "警報結界",
    "Astral Doppelganger": "アストラル・ドッペルゲンガー",
    "Attune Animal": "動物同調",
    "Attune Item": "物品同調",
    "Calling [Spirit Type]": "[精霊タイプ] 呼び出し",
    "Charged Ward": "充填結界",
    "Circle of Cleansing": "浄化円",
    "Create Ally Spirit": "同盟精霊創造",
    "Dispersion Circle": "拡散円",
    "Door Wards": "扉の結界",
    "Far Sensing": "遠隔感知",
    "Masking Ward": "擬態結界",
    "Obfuscating Ward": "隠蔽結界",
    "Polarized Ward": "偏光結界",
    "Trap Ward": "罠結界",
    "Zombie": "ゾンビ",
    # --- Enchantments -------------------------------------------------
    "Hand of Glory": "栄光の手/ハンド・オブ・グローリー",
    "Symbolic Link": "象徴リンク/シンボリック・リンク",
}
