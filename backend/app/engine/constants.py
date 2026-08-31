"""Engine-wide constants: SR5 karma prices, talent groupings, build-method
identifiers, and lookup tables. Pure data — no imports from the rest of the
engine, so everything else can import from here freely.
"""

STANDARD_GAMEPLAY = "Standard"

MAG_TALENTS = {
    "Magician",
    "Aspected Magician",
    "Adept",
    "Mystic Adept",
    "Explorer",
    "Enchanter",
    "Apprentice",
}
RES_TALENTS = {"Technomancer"}
ADEPT_TALENTS = {"Adept", "Mystic Adept"}
SKIP_TALENTS = {"A.I."}
MYSTIC_PP_KARMA = 5
ENHANCEMENT_KARMA = 2
SPELL_KARMA = 5
COMPLEX_FORM_KARMA = 4
CONTACT_FREE_MULT = 3
CONTACT_RATING_MIN = 1
CONTACT_RATING_MAX = 6
CONTACT_CHARGEN_COST_MAX = 7
NEGATIVE_QUALITY_KARMA_CAP = 25
POSITIVE_QUALITY_KARMA_CAP = 25
NUYEN_CHARGEN_KEEP_MAX = 5000
MARTIAL_ART_STYLE_KARMA = 7
MARTIAL_ART_TECHNIQUE_KARMA = 5
MARTIAL_ART_CHARGEN_STYLE_MAX = 1
MARTIAL_ART_CHARGEN_TECHNIQUE_MAX = 5
INITIATION_KARMA_FLAT = 10
INITIATION_KARMA_PER_GRADE = 3
SUBMERSION_KARMA_FLAT = 10
SUBMERSION_KARMA_PER_GRADE = 3
MENTOR_SPIRIT_ID = "ced3fecf-2277-4b20-b1e0-894162ca9ae2"
QI_FOCUS_NAME = "Qi Focus"
DRAIN_MINIMUM = 2
BUILD_METHOD_PRIORITY = "Priority"
BUILD_METHOD_SUM_TO_TEN = "SumToTen"
BUILD_METHOD_KARMA = "Karma"
SUM_TO_TEN_BUDGET = 10
SUM_TO_TEN_COST = {"A": 4, "B": 3, "C": 2, "D": 1, "E": 0}
KARMA_CHARGEN_POOL = 800
KARMA_ATTRIBUTE = 5
KARMA_ACTIVE_SKILL = 2
KARMA_SKILL_GROUP = 5
KARMA_KNOWLEDGE = 1
KARMA_SPECIALIZATION = 7
KARMA_TO_NUYEN = 2000
KARMA_NUYEN_MAX = 235
CAREER_SKILL_MAX = 12
PRIORITY_KARMA_NUYEN_BASE = 10
TRUST_FUND_LIFESTYLE = {1: "Medium", 2: "Low", 3: "High", 4: "Medium"}
TRUST_FUND_STIPEND = {
    1: "Medium ライフスタイル＋毎月 500¥",
    2: "Low ライフスタイル＋毎月 2,000+(3D6×100)¥",
    3: "High ライフスタイル＋毎月 1,000¥",
    4: "Medium ライフスタイル＋毎月 3,000+(6D6×100)¥",
}
DEALER_CONNECTION_MATCH = {
    "Drones": ("Drones",),
    "Groundcraft": ("Cars", "Bikes", "Trucks", "Corpsec/Police/Military", "Municipal/Construction", "Hovercraft"),
    "Watercraft": ("Boats", "Submarines"),
    "Aircraft": ("Rotorcraft", "Fixed-Wing Aircraft", "VTOL/VSTOL", "LTAV"),
}
BLACK_MARKET_CATEGORY_HINTS = {
    "Weapons": ("weapons",),
    "Armor": ("armor_items",),
    "Electronics": ("commlinks", "cyberdecks", "rccs", "optics", "sensors", "programs", "apps"),
    "Vehicles": ("vehicles", "drones"),
    "Cyberware": (),
    "Bioware": (),
    "Drugs": ("gear",),
}
BLACK_MARKET_AVAIL_BONUS = 2
QUALITY_CONTACT_EXTRA_SUFFIX = ":contact"
QUALITY_SPIRIT_CATEGORY_EXTRA_SUFFIX = ":spiritcategory"
QUALITY_ADDSPIRIT_EXTRA_MARKER = ":addspirit:"
# Ex-Con (RF): corp contacts need Loyalty 4+, law enforcement Loyalty 5+.
EXCON_CORP_ROLE_HINTS = (
    "johnson",
    "mr. johnson",
    "corporate",
    "corp ",
    " corp",
    "executive",
    "manager",
    "salaryman",
)
EXCON_LAW_ROLE_HINTS = (
    "cop",
    "police",
    "lone star",
    "knight errant",
    "law enforcement",
    "parole",
    "ke ",
    " ke",
)
ERASED_LIFESTYLE_FORBIDDEN = {"High", "Luxury", "Commercial"}
EXPERTISE_BONUS = 3
SPECIALIZATION_BONUS = 2
CAREER_SKILL_GROUP_MAX = 12
SPELL_TALENTS = {"Magician", "Mystic Adept", "Aspected Magician", "Apprentice", "Enchanter"}
SPIRIT_TALENTS = {"Magician", "Mystic Adept", "Aspected Magician", "Apprentice"}
SPRITE_TALENTS = set(RES_TALENTS)
COMPLEX_FORM_TALENTS = set(RES_TALENTS)
FOCUS_TALENTS = set(MAG_TALENTS)
SPRITE_MATRIX_KEYS = {
    "CHA": "attack",
    "INT": "sleaze",
    "LOG": "dataprocessing",
    "WIL": "firewall",
}
SPIRIT_REAGENT_YEN = 20
FOCUS_FORCE_MULT = 5
SPIRIT_ROLE_LABELS = {
    "combat": "戦闘",
    "detection": "探知",
    "health": "健康",
    "illusion": "幻影",
    "manipulation": "操作",
    "extra": "追加",
}
