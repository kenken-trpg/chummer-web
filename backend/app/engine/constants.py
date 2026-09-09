"""Engine-wide constants: talent groupings, build-method identifiers, and
lookup tables. Pure data — nothing from the rest of the engine (only
``app.notices``, which sits above it), so everything else can import from here
freely.

What is *not* here any more: the numbers a Chummer settings file can change —
the karma price list, the chargen caps, the karma-to-nuyen rate. Those moved to
``app/rules.py`` so they can vary per character, and the engine reads them
through ``current_rules()``. A number belongs here when no settings file can
touch it (the condition-monitor threshold, the A-E sum-to-ten costs).
"""

from __future__ import annotations

from ..notices import Phrase, ui

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
CONTACT_RATING_MIN = 1
CONTACT_RATING_MAX = 6
CONTACT_CHARGEN_COST_MAX = 7
#: Boxes on a condition monitor per −1 wound modifier (SR5 p.169).
CM_THRESHOLD = 3
MARTIAL_ART_CHARGEN_STYLE_MAX = 1
MARTIAL_ART_CHARGEN_TECHNIQUE_MAX = 5
MENTOR_SPIRIT_ID = "ced3fecf-2277-4b20-b1e0-894162ca9ae2"
QI_FOCUS_NAME = "Qi Focus"
DRAIN_MINIMUM = 2
BUILD_METHOD_PRIORITY = "Priority"
BUILD_METHOD_SUM_TO_TEN = "SumToTen"
BUILD_METHOD_KARMA = "Karma"
SUM_TO_TEN_COST = {"A": 4, "B": 3, "C": 2, "D": 1, "E": 0}
MATRIX_ARRAY_KEYS = ("attack", "sleaze", "dataprocessing", "firewall")
TRUST_FUND_LIFESTYLE = {1: "Medium", 2: "Low", 3: "High", 4: "Medium"}
#: The wording lives in the front end (`app.notices`); these are its keys.
TRUST_FUND_STIPEND = {
    1: "engine.trustFund.1",
    2: "engine.trustFund.2",
    3: "engine.trustFund.3",
    4: "engine.trustFund.4",
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
    "combat": "engine.spiritRole.combat",
    "detection": "engine.spiritRole.detection",
    "health": "engine.spiritRole.health",
    "illusion": "engine.spiritRole.illusion",
    "manipulation": "engine.spiritRole.manipulation",
    "extra": "engine.spiritRole.extra",
}


# quality_extras dict keys for quality bonuses that need a player pick beyond the
# quality id itself (a contact, a spirit category, an indexed addspirit slot).
def quality_contact_extra_key(quality_id: str) -> str:
    return f"{quality_id}{QUALITY_CONTACT_EXTRA_SUFFIX}"


def quality_spirit_category_extra_key(quality_id: str) -> str:
    return f"{quality_id}{QUALITY_SPIRIT_CATEGORY_EXTRA_SUFFIX}"


def quality_addspirit_extra_key(quality_id: str, index: int) -> str:
    return f"{quality_id}{QUALITY_ADDSPIRIT_EXTRA_MARKER}{int(index)}"


# Cyberlimb / bioware limb-side maths: Left/Right normalisation plus the limb
# slots the duplicate-side messages name. Shared by the 'ware side pipeline
# (engine/ware/) and the quality selectside validators (apply_quality_rules /
# resolve_quality_sides in engine/qualities.py). The labels themselves are
# dictionary keys now — `engine.side.*` / `engine.slot.*` in messages.ts.
SIDES = ("Left", "Right")
_LIMB_SLOTS = ("arm", "leg", "torso", "skull")


def slot_phrase(slot: str) -> Phrase | str:
    """A limb slot as a dictionary key. Chummer writes both 'skull' and 'head'
    for the same slot; anything unrecognised falls through as its raw id."""
    key = "skull" if slot == "head" else slot
    return ui(f"engine.slot.{key}") if key in _LIMB_SLOTS else slot


def _normalize_side(value: str | None) -> str | None:
    raw = (value or "").strip()
    if raw in SIDES:
        return raw
    lower = raw.lower()
    if lower in {"left", "l", "左"}:
        return "Left"
    if lower in {"right", "r", "右"}:
        return "Right"
    return None
