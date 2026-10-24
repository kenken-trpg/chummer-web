"""Hand translations for the smaller entity buckets still on English fallback
(Phase 2b, see docs/plans/translation-plan.md): mentors, lifestyles, martial arts,
adept powers, echoes, complex forms, plus SR5 core-rulebook gear.

House style matches what upstream already translated:
  * meanings for concept words (強打, 反射強化), katakana for proper names
  * parenthetical mentor variants "(Alt)" / "(SHB)" are left on English fallback,
    the same as the upstream file does.

Gear policy: only entries whose ``source`` is ``SR5`` (core rulebook) are
translated here. Weapons/armor/gear from supplements (SL, 2050, CF, RF, R5,
RG, KK, …) — ~2,200 items — are deliberately left on English fallback; pure
model codes (AK-97, FN HAR) also stay as-is, matching their siblings.

On 2026-10-24 every entry that reached only supplement rows with no Japanese
edition went back to English (the supplement-terms-stay-English policy): all
the mentors, lifestyles, martial arts and complex forms, and most adept powers
and echoes. What is left also names a row a Japanese book prints.

Consumed by import_ja_from_refs.py; every key is checked against catalog() by
tests/test_translation_overrides.py.
"""

from __future__ import annotations

ENTITIES: dict[str, str] = {
    # --- adept powers (meaning-based, cf. 反射強化 / 危険関知) ------------------
    "Improved Potential (Chaos Mentor)": "潜在力強化：(混沌メンター)",
    "Riposte": "リポスト",
    "Berserker Temper": "狂戦士の気質",
    # --- echoes (technomancer; katakana / 共振〜, cf. 共振リンク) ---------------
    "Fight or Flight Filter": "闘争逃走フィルター",
    "Mathemagics": "マスマジック",
    "Quiet": "クワイエット",
    "Resonance Riding": "共振ライディング",
    "Resonance Scream": "共振スクリーム",
    "Sleepwalker": "スリープウォーカー",
    # --- SR5 core gear (source == "SR5" only; supplements stay English) --------
    # weapons
    "Cyber Microgrenade Launcher": "サイバー・マイクログレネードランチャー",
    # weapon accessories (cf. Silencer/Suppressor = 消音器)
    "Silencer (Ares Light Fire 70)": "消音器（アレス・ライトファイア70）",
    "Silencer (Ares Light Fire 75)": "消音器（アレス・ライトファイア75）",
    "Belt-Feed, 100-round": "ベルト給弾, 100発",
    "Drum Magazine, 24-round": "ドラムマガジン, 24発",
    "Drum Magazine, 32-round": "ドラムマガジン, 32発",
    "External Power Source": "外部電源",
    # armor mods
    "Electrochromic Clothing": "エレクトロクロミック・クロージング",
    "(Synth)Leather": "（合成）レザー",
    "Chemical Protection": "化学防護",
    "Fire Resistance": "耐火",
    "Insulation": "断熱",
    "Nonconductivity": "非導電",
    "Thermal Damping": "熱感知抑制",
    "Shock Frills": "ショックフリル",
    "Full Body Armor: Helmet": "フルボディアーマー：ヘルメット",
    "Full Body Armor: Chemical Seal": "フルボディアーマー：化学遮断",
    "Full Body Armor: Environment Adaptation": "フルボディアーマー：環境適応",
    "Urban Explorer Jumpsuit: Helmet": "アーバンエクスプローラー・ジャンプスーツ：ヘルメット",
    "Liner - Fire Resistance (6)": "ライナー - 耐火 (6)",
    "Liner - Fire Resistance (5)": "ライナー - 耐火 (5)",
    "Liner - Fire Resistance (4)": "ライナー - 耐火 (4)",
    "Liner - Fire Resistance (3)": "ライナー - 耐火 (3)",
    "Liner - Fire Resistance (2)": "ライナー - 耐火 (2)",
    "Liner - Fire Resistance (1)": "ライナー - 耐火 (1)",
    "Liner - Chemical Protection (6)": "ライナー - 化学防護 (6)",
    "Liner - Chemical Protection (5)": "ライナー - 化学防護 (5)",
    "Liner - Chemical Protection (4)": "ライナー - 化学防護 (4)",
    "Liner - Chemical Protection (3)": "ライナー - 化学防護 (3)",
    "Liner - Chemical Protection (2)": "ライナー - 化学防護 (2)",
    "Liner - Chemical Protection (1)": "ライナー - 化学防護 (1)",
    "Liner - Insulation (6)": "ライナー - 断熱 (6)",
    "Liner - Insulation (5)": "ライナー - 断熱 (5)",
    "Liner - Insulation (4)": "ライナー - 断熱 (4)",
    "Liner - Insulation (3)": "ライナー - 断熱 (3)",
    "Liner - Insulation (2)": "ライナー - 断熱 (2)",
    "Liner - Insulation (1)": "ライナー - 断熱 (1)",
    # cyberware
    "Essence Antihole": "エッセンス・アンチホール",
}
