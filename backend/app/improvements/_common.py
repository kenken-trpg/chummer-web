"""Shared primitives + constant tables for the improvements pipeline.

Pure data + tiny helpers, no imports from the rest of the app, so every
``improvements/`` submodule can pull from here without a cycle.
"""

from __future__ import annotations

import re
from typing import Any

SPELL_DEFENSE_RESIST_TAGS = {
    "directmanaspellresist": "direct_mana",
    "detectionspellresist": "detection",
    "mentalmanipulationresist": "mental_manipulation",
    "manaillusionresist": "mana_illusion",
    "physicalillusionresist": "physical_illusion",
    "decreasebodresist": "decrease_bod",
    "decreaseagiresist": "decrease_agi",
    "decreaserearesist": "decrease_rea",
    "decreasestrresist": "decrease_str",
    "decreasecharesist": "decrease_cha",
    "decreaselogresist": "decrease_log",
    "decreaseintresist": "decrease_int",
    "decreasewilresist": "decrease_wil",
}

IMPLEMENTED = {
    "specificattribute",
    "armor",
    "conditionmonitor",
    "initiative",
    "initiativepass",
    "enabletab",
    "enableattribute",
    "cyberseeker",
    "mentallimit",
    "sociallimit",
    "physicallimit",
    "skillgroup",
    "skillcategory",
    "specificskill",
    "selectskill",
    "adeptpowerpoints",
    "unlockskills",
    "damageresistance",
    "unarmeddv",
    "unarmeddvphysical",
    "magicianswaydiscount",
    "freequality",
    "addqualities",
    "selectmentorspirit",
    "focusbindingkarmacost",
    "skillattribute",
    "spellcategory",
    "spelldicepool",
    "spellresistance",
    "firearmor",
    "coldarmor",
    "electricityarmor",
    "radiationresist",
    "toxincontactresist",
    "toxiningestionresist",
    "toxininhalationresist",
    "toxininjectionresist",
    "pathogencontactresist",
    "pathogeningestionresist",
    "pathogeninhalationresist",
    "pathogeninjectionresist",
    "toxincontactimmune",
    "toxininhalationimmune",
    "pathogencontactimmune",
    "pathogeninhalationimmune",
    "restrictedgear",
    "limitmodifier",
    "skillwire",
    "skillsoftaccess",
    "livingpersona",
    "matrixinitiativediceadd",
    "reach",
    "lifestylecost",
    "notoriety",
    "fame",
    "publicawareness",
    "essencepenalty",
    "essencepenaltyt100",
    "essencepenaltymagonlyt100",
    "walkmultiplier",
    "runmultiplier",
    "movementreplace",
    "sprintbonus",
    "fatigueresist",
    "memory",
    "composure",
    "judgeintentions",
    "judgeintentionsdefense",
    "judgeintentionsoffense",
    "dodge",
    "surprise",
    "selectattributes",
    "physicalcmrecovery",
    "stuncmrecovery",
    "addesstophysicalcmrecovery",
    "addesstostuncmrecovery",
    "skilldisable",
    "skillgroupdisable",
    "skillgroupcategorydisable",
    "skillgroupdisablechoice",
    "blockskillcategorydefaulting",
    "nuyenmaxbp",
    "nuyenamt",
    "trustfund",
    "blackmarketdiscount",
    "selectcontact",
    "dealerconnection",
    "friendsinhighplaces",
    "mademan",
    "overclocker",
    "ambidextrous",
    "cyberwareessmultiplier",
    "biowareessmultiplier",
    "cyberwaretotalessmultiplier",
    "essencemax",
    "disablebioware",
    "skillcategorykarmacostmultiplier",
    "skillcategorypointcostmultiplier",
    "skillcategorykarmacost",
    "skillcategoryspecializationkarmacostmultiplier",
    "skillgroupcategorykarmacostmultiplier",
    "nativelanguagelimit",
    "knowledgeskillpoints",
    "knowledgeskillkarmacost",
    "knowledgeskillkarmacostmin",
    "activeskillkarmacost",
    "selectquality",
    "selectside",
    "prototypetranshuman",
    "burnoutsway",
    "actiondicepool",
    "addcontact",
    "contactkarma",
    "contactkarmaminimum",
    "disablecyberwaregrade",
    "disablebiowaregrade",
    "martialart",
    "limitspellcategory",
    "limitspiritcategory",
    "allowspellcategory",
    "blockspelldescriptor",
    "specialmodificationlimit",
    "erased",
    "excon",
    "selectexpertise",
    "spellcategorydrain",
    "spellcategorydamage",
    "weaponcategorydv",
    "addspirit",
    "addmetamagic",
    "freespells",
    "newspellkarmacost",
    "spelldescriptordrain",
    "spelldescriptordamage",
    "allowspellrange",
    "weaponskillaccuracy",
    "drainvalue",
    "fadingvalue",
    "fadingresist",
    "drainresist",
    "selecttext",
    "addecho",
    "cyberadeptdaemon",
    "addspell",
    "specificpower",
    "selectpowers",
    "unarmedreach",
    "unarmedap",
    "smartlink",
    "throwstr",
    "throwrangestr",
    "weaponcategorydice",
    *SPELL_DEFENSE_RESIST_TAGS.keys(),
}
SILENT_TAGS = {
    "disablequality",
    "selectweapon",
    "addgears",
    "addweapon",
    "addgear",
    "limit",
    "selectspell",
    "selectpower",
    "selecttradition",
    "selectrestricted",
    "activesoft",
    "knowsoft",
    "linguasoft",
    "skillsoft",
    "weaponspecificdice",
    "addskillspecializationoption",
    "critterpowers",
    "limitcritterpowercategory",
    "optionalpowers",
    "replaceattributes",
    "physiologicaladdictionfirsttime",
    "physiologicaladdictionalreadyaddicted",
    "psychologicaladdictionfirsttime",
    "psychologicaladdictionalreadyaddicted",
    "addware",
    "addlimb",
    "metageniclimit",
    "selectarmor",
    "selectsprite",
    "selectparagon",
    "selectinherentaiprogram",
    "selectattribute",
    "streetcredmultiplier",
    "astralreputation",
    "specialattburnmultiplier",
    "allowspritefettering",
    "defensetest",
    "swapskillattribute",
    "swapskillspecattribute",
    "skillgrouplevel",
    "matrixinitiativedice",
    "devicerating",
    "quickeningmetamagic",
    "penaltyfreesustain",
    "availability",
    "handling",
    "offroadhandling",
    "speed",
    "offroadspeed",
    "accel",
    "offroadaccel",
    "body",
    "pilot",
    "sensor",
    "seats",
}

SPECIAL_ARMOR_TAGS = {
    "firearmor": "fire",
    "coldarmor": "cold",
    "electricityarmor": "electricity",
    "radiationresist": "radiation",
    "toxincontactresist": "toxin_contact",
    "toxiningestionresist": "toxin_ingestion",
    "toxininhalationresist": "toxin_inhalation",
    "toxininjectionresist": "toxin_injection",
    "pathogencontactresist": "pathogen_contact",
    "pathogeningestionresist": "pathogen_ingestion",
    "pathogeninhalationresist": "pathogen_inhalation",
    "pathogeninjectionresist": "pathogen_injection",
}
IMMUNE_TAGS = {
    "toxincontactimmune": "toxin_contact",
    "toxininhalationimmune": "toxin_inhalation",
    "pathogencontactimmune": "pathogen_contact",
    "pathogeninhalationimmune": "pathogen_inhalation",
}

SPECIAL_ARMOR_KEYS = (
    "fire",
    "cold",
    "electricity",
    "radiation",
    "toxin_contact",
    "toxin_ingestion",
    "toxin_inhalation",
    "toxin_injection",
    "pathogen_contact",
    "pathogen_ingestion",
    "pathogen_inhalation",
    "pathogen_injection",
)
IMMUNE_KEYS = ("toxin_contact", "toxin_inhalation", "pathogen_contact", "pathogen_inhalation")
TEST_MOD_TAGS = {
    "memory": "memory",
    "composure": "composure",
    "judgeintentions": "judge_intentions",
    "judgeintentionsdefense": "judge_intentions_defense",
    "judgeintentionsoffense": "judge_intentions_offense",
    "dodge": "dodge",
    "surprise": "surprise",
}
LIMIT_KINDS = ("physical", "mental", "social")
LIMIT_KIND_ALIASES = {
    "physical": "physical",
    "physicallimit": "physical",
    "mental": "mental",
    "mentallimit": "mental",
    "social": "social",
    "sociallimit": "social",
}
LIMIT_CONDITION_JA = {
    "LimitCondition_TestSneakingThermal": "熱視覚／熱センサーに対する潜伏",
    "LimitCondition_SkillsActiveSneaking": "熱視覚／熱センサーに対する潜伏",
    "LimitCondition_Skillwires": "スキルワイヤ",
}

ATTR_ALIASES = {
    "BOD": "BOD",
    "BODY": "BOD",
    "AGI": "AGI",
    "AGILITY": "AGI",
    "REA": "REA",
    "REACTION": "REA",
    "STR": "STR",
    "STRENGTH": "STR",
    "CHA": "CHA",
    "CHARISMA": "CHA",
    "INT": "INT",
    "INTUITION": "INT",
    "LOG": "LOG",
    "LOGIC": "LOG",
    "WIL": "WIL",
    "WILLPOWER": "WIL",
    "EDG": "EDG",
    "EDGE": "EDG",
    "MAG": "MAG",
    "MAGIC": "MAG",
    "RES": "RES",
    "RESONANCE": "RES",
    "ESS": "ESS",
    "ESSENCE": "ESS",
}


def _replace_rating(value: Any, rating: int) -> Any:
    if value is None or isinstance(value, (int, float)):
        return value
    return str(value).replace("Rating", str(int(rating)))


def substitute_rating(nodes: list[dict[str, Any]], rating: int) -> list[dict[str, Any]]:
    out = []
    for node in nodes:
        copied = dict(node)
        if "value" in copied:
            copied["value"] = _replace_rating(copied["value"], rating)
        if "fields" in copied:
            copied["fields"] = {k: _replace_rating(v, rating) for k, v in (copied["fields"] or {}).items()}
        out.append(copied)
    return out


def _as_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, list):
        return str(value[0]) if value else default
    return str(value)


def _limit_kind(value: Any) -> str:
    raw = _as_text(value).strip().lower().replace(" ", "")
    return LIMIT_KIND_ALIASES.get(raw, "")


def limit_condition_label(condition: str) -> str:
    key = (condition or "").strip()
    if not key:
        return ""
    return LIMIT_CONDITION_JA.get(key, key)


def _as_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    if isinstance(value, (int, float)):
        return int(value)
    raw = str(value).strip()
    try:
        return int(float(raw))
    except ValueError:
        return default


_ARITH_RE = re.compile(r"^[0-9+\-*/(). ]+$")


def _eval_int(value: Any, default: int = 0) -> int:
    """``_as_int`` plus bare arithmetic (``Rating*2`` after ``substitute_rating``
    leaves ``"3*2"``). Digits and ``+-*/().`` only — no names, no calls."""
    if isinstance(value, str) and _ARITH_RE.match(value.strip()) and not value.strip().isdigit():
        try:
            return int(eval(value.strip(), {"__builtins__": {}}, {}))  # noqa: S307 - guarded by _ARITH_RE
        except (ArithmeticError, SyntaxError, ValueError):
            return default
    return _as_int(value, default)


def _bonus_int(node: dict[str, Any], fields: dict[str, Any] | None = None, *, rating: int = 1) -> int:
    fields = fields or {}
    raw = node.get("value")
    if raw is None or raw == "":
        raw = fields.get("val")
    if raw is None or raw == "":
        raw = fields.get("bonus")
    if raw is None or raw == "":
        raw = fields.get("value")
    if isinstance(raw, str) and "Rating" in raw:
        raw = _replace_rating(raw, rating)
    return _as_int(raw)
