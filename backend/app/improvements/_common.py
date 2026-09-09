"""Shared primitives + constant tables for the improvements pipeline.

Pure data + tiny helpers, no imports from the rest of the app, so every
``improvements/`` submodule can pull from here without a cycle.
"""

from __future__ import annotations

import re
from typing import Any

from ..notices import Notice, notice

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
    "addlimb",
    "addgear",
    "addware",
    "replaceattributes",
    "drugpositiveattributemodifier",
    "reflexrecorderoptimization",
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
    "selectcyberware",
    "selectlimit",
    "hardwires",
    "adeptpowerpoints",
    "unlockskills",
    "damageresistance",
    "unarmeddv",
    "unarmeddvphysical",
    "naturalweapon",
    "magicianswaydiscount",
    "freequality",
    "addqualities",
    "addquality",
    "selectmentorspirit",
    "metamagiclimit",
    "focusbindingkarmacost",
    "skillattribute",
    "skilllinkedattribute",
    "spellcategory",
    "spelldicepool",
    "spellresistance",
    "firearmor",
    "coldarmor",
    "electricityarmor",
    "radiationresist",
    "sonicresist",
    "adapsin",
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
    "defensetest",
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
    "attributekarmacost",
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
    "swapskillattribute",
    "swapskillspecattribute",
    "skillgrouplevel",
    "quickeningmetamagic",
    "matrixinitiativedice",
    *SPELL_DEFENSE_RESIST_TAGS.keys(),
}
SILENT_TAGS = {
    "disablequality",
    "selectweapon",
    "addgears",
    "addweapon",
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
    # `Muzzle` sharpens a `Fangs` natural weapon; natural weapons live on
    # critters and metavariants we do not build, so there is no row to sharpen.
    "weaponaccuracy",
    "addskillspecializationoption",
    "critterpowers",
    "limitcritterpowercategory",
    "optionalpowers",
    "physiologicaladdictionfirsttime",
    "physiologicaladdictionalreadyaddicted",
    "psychologicaladdictionfirsttime",
    "psychologicaladdictionalreadyaddicted",
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
    # A vehicle's Device Rating is nowhere in `vehicles.xml`; Chummer derives
    # it, and we do not model it at all, so the one mod that raises it has
    # nothing to raise.
    "devicerating",
    # Only on the hidden `Sourcerer Daemon` echo, whose `(Rating - 1) / 2`
    # comes out at 0 for the single level a character can hold — and we do
    # not model sustaining penalties to spend it on either.
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
    "sonicresist": "sonic",
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
    "sonic",
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
    # `defensetest` rides the `dodge` bucket: both end up in the same defense
    # pool (REA + INT + these), and Chummer prints them in the same place.
    "defensetest": "dodge",
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
#: Chummer's condition tokens -> our dictionary keys. An unlisted token falls
#: through as itself, which renders as itself (`app.notices`) — the same
#: visible-but-harmless fallback the key had before it was a key.
LIMIT_CONDITION_KEYS = {
    "LimitCondition_TestSneakingThermal": "engine.limitCond.sneakingThermal",
    "LimitCondition_SkillsActiveSneaking": "engine.limitCond.sneakingThermal",
    "LimitCondition_Skillwires": "engine.limitCond.skillwires",
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


def limit_condition_label(condition: str) -> Notice | None:
    token = (condition or "").strip()
    if not token:
        return None
    return notice(LIMIT_CONDITION_KEYS.get(token, token))


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
    leaves ``"3*2"``). Digits and ``+-*/().`` only — no names, no calls, and no
    ``**`` (``9**9**9`` passes the char-class regex but would blow up ``eval``)."""
    expr = value.strip() if isinstance(value, str) else ""
    if expr and "**" not in expr and _ARITH_RE.match(expr) and not expr.isdigit():
        try:
            return int(eval(expr, {"__builtins__": {}}, {}))  # noqa: S307 - guarded by _ARITH_RE
        except (ArithmeticError, SyntaxError, ValueError):
            return default
    return _as_int(value, default)


def _bonus_int(node: dict[str, Any], fields: dict[str, Any] | None = None, *, rating: int = 1, default: int = 0) -> int:
    """The one way a ``<bonus>`` child's magnitude is read.

    ``parse_bonus`` puts a childless element's text in ``node["value"]`` and a
    parent element's children in ``fields``, so exactly one of the four keys
    below is ever populated — the chain is a shape probe, not a precedence
    rule. Ends in ``_eval_int`` because ``substitute_rating`` leaves arithmetic
    behind: ``<skillwire>Rating * 2</skillwire>`` arrives as ``"2 * 2"``.
    """
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
    return _eval_int(raw, default)


def granted_quality_names(node: dict[str, Any]) -> list[tuple[str, str]]:
    """``<addquality>`` — bare or inside ``<addqualities>`` — as (name, pick).

    The pick is the ``select=`` the data puts on the grant itself: how a
    tradition hands Code of Honor the code it demands (FA p.74). Chummer's
    ``forced="True"`` says the follower cannot refuse, which is what granting
    it at all already means here, so it is not read back out.
    """
    grants = node.get("quality_grants")
    if grants:
        return [
            (str(row.get("name") or "").strip(), str(row.get("select") or "").strip())
            for row in grants
            if str(row.get("name") or "").strip()
        ]
    if node.get("tag") == "addquality":
        name = str(node.get("value") or "").strip()
        select = str((node.get("attrs") or {}).get("select") or "").strip()
        return [(name, select)] if name else []
    raw = (node.get("fields") or {}).get("addquality") or node.get("value") or ""
    names = raw if isinstance(raw, list) else [raw]
    return [(str(name).strip(), "") for name in names if str(name).strip()]
