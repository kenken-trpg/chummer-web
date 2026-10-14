"""Shared primitives + constant tables for the improvements pipeline.

Pure data + tiny helpers, no imports from the rest of the app, so every
``improvements/`` submodule can pull from here without a cycle.
"""

from __future__ import annotations

import re
from typing import Any

from ..notices import Notice, notice
from ..safe_eval import MAX_EXPRESSION_LENGTH, UnsafeExpression, evaluate_arithmetic

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

SILENT_TAGS = {
    # read off the installed ware in `engine/compute/ware.py`, which drops the
    # quality's own bonus before the effects pass
    "disablequality",
    "selectweapon",
    "selectspell",
    "selecttradition",
    "selectrestricted",
    "activesoft",
    "skillsoft",
    "weaponspecificdice",
    # the Infected's powers: read element by element in
    # `data_loader/loaders/qualities.py` and listed on the quality's row
    "critterpowers",
    "optionalpowers",
    # Narrows what a Critter Powers tab may buy — and there is no such tab
    # here. All 26 sit on an Infected or a Dracoform quality, and both hand
    # their powers over by name in the `<critterpowers>` beside this tag, so
    # the category never decides anything the character sees.
    "limitcritterpowercategory",
    "metageniclimit",
    # Custom Fit (Stack): read off the mod in `engine/gear/armor.py`, which
    # stacks the piece onto the armor it names
    "selectarmor",
    # Sprite Affinity: the pick is the quality's extra, offered from the
    # sprite list in `data_loader` (Chummer's `AddSprite` only widens a
    # stream's sprite list, and every stream here already has them all)
    "selectsprite",
    # Only on `Inherent Program`, a quality an A.I. takes — and `A.I.` is in
    # `SKIP_TALENTS`, so no character here reaches the quality at all. It is
    # also the innate grant of `Protosapient`, an A.I. metavariant, which the
    # chargen list does not offer either.
    "selectinherentaiprogram",
    "selectattribute",
    # Astral Reputation (SG p.35) is a tracked value of its own, like
    # notoriety, and we track none of it. One quality (`Conjuring Geas`)
    # carries the only -1 in the data.
    "astralreputation",
    # Only on `Resonant Burnout`, which is on hold as a whole.
    "specialattburnmultiplier",
    # Permission to Fetter a sprite, on `Resonant Stream: Technoshaman`.
    # Fettering is a career action; nothing here performs it.
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
    # A vehicle mod's stat changes are applied by the vehicle pass itself
    # (`_apply_vehicle_bonus` in `engine/gear/vehicles/stats.py`), which knows
    # the "4/3" on-road/off-road split these tags come in pairs for. The
    # effects pass has no vehicle to add them to.
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

#: How many times each of these sits in the vendored data today.
#:
#: The rest of `SILENT_TAGS` is silent for a structural reason — a vehicle mod
#: has no vehicle in the effects pass, an installed piece of ware is read
#: elsewhere — and that argument holds however often the tag appears. These
#: are silent because of *where* they appear: on the one quality, the one
#: echo, the qualities that enumerate their powers anyway. Spread to somewhere
#: new, the argument may not survive, and silence would hide that forever.
#: A `CHUMMER_REF` bump that moves one of these numbers is asking a human to
#: re-read the comment above the tag, not to update this line.
SILENT_TAG_SITES = {
    "limitcritterpowercategory": 26,
    "metageniclimit": 3,
    "allowspritefettering": 1,
    "astralreputation": 1,
    "devicerating": 1,
    "penaltyfreesustain": 1,
    "selectarmor": 1,
    # one definition, plus the copy carried in `Protosapient`'s grants,
    # which the walk reaches both nested and through `all_metatypes`
    "selectinherentaiprogram": 3,
    "selectsprite": 1,
    "specialattburnmultiplier": 1,
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
    # The Addiction Test (SR5 p.414): BOD + WIL against the drug's threshold
    # for a physiological habit, LOG + WIL for a psychological one. Chummer
    # keeps the first dose apart from the test an already-addicted character
    # makes, and `Drug Tolerant` (CF p.54) is exactly that split — +2 the first
    # time and nothing once the habit is there.
    "physiologicaladdictionfirsttime": "addiction_physiological_first",
    "physiologicaladdictionalreadyaddicted": "addiction_physiological_addicted",
    "psychologicaladdictionfirsttime": "addiction_psychological_first",
    "psychologicaladdictionalreadyaddicted": "addiction_psychological_addicted",
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
#: Chummer's condition tokens -> our dictionary keys.
#:
#: The tokens are what the data files carry (`<condition>LimitCondition_Visible`),
#: and an unmapped one used to fall through as itself — so a character in an
#: Armanté Suit read "社交リミット +2（LimitCondition_Visible）", in either
#: locale, since neither dictionary had the token either. The vendored data names
#: 55 of them and three were mapped, so all of them are listed here and
#: `test_limit_conditions.py` fails when the data names one this does not.
#:
#: Upstream's own `lang/ja-jp.xml` leaves these strings in English, so the
#: Japanese is ours. Skill names follow the translation overlay — Gymnastics is
#: 体術, Sneaking is 忍び歩き — and specialisations stay in English, which is how
#: the skills tab and the sheet show them.
LIMIT_CONDITION_KEYS = {
    "LimitCondition_AttribSkillINT": "engine.limitCond.attrIntSkills",
    "LimitCondition_AttribSkillLOG": "engine.limitCond.attrLogSkills",
    "LimitCondition_BunkerGearVisible": "engine.limitCond.bunkerGearVisible",
    "LimitCondition_ClimbingTests": "engine.limitCond.climbing",
    "LimitCondition_CorporationVisible": "engine.limitCond.corporationVisible",
    "LimitCondition_CyberwareBalanceTail": "engine.limitCond.balanceTail",
    "LimitCondition_CyberwareCyberfins": "engine.limitCond.cyberfins",
    "LimitCondition_CyberwareFootAnchor": "engine.limitCond.footAnchor",
    "LimitCondition_CyberwareHydraulicJacks": "engine.limitCond.hydraulicJacks",
    "LimitCondition_CyberwareMonkeyFoot": "engine.limitCond.monkeyFoot",
    "LimitCondition_CyberwareRaptorFoot": "engine.limitCond.raptorFoot",
    "LimitCondition_CyberwareSnakeFingers": "engine.limitCond.snakeFingers",
    "LimitCondition_ExcludeFansGangers": "engine.limitCond.excludeFansGangers",
    "LimitCondition_ExcludeIntimidation": "engine.limitCond.excludeIntimidation",
    "LimitCondition_ExcludeIntimidationVisible": "engine.limitCond.excludeIntimidationVisible",
    "LimitCondition_GangVisible": "engine.limitCond.gangVisible",
    "LimitCondition_GearAutopicker": "engine.limitCond.autopicker",
    "LimitCondition_InUse": "engine.limitCond.inUse",
    "LimitCondition_Intimidation": "engine.limitCond.intimidation",
    "LimitCondition_IntimidationVisible": "engine.limitCond.intimidationVisible",
    "LimitCondition_Megacorp": "engine.limitCond.megacorp",
    "LimitCondition_NationalLanguageRanks": "engine.limitCond.nationalLanguageRanks",
    "LimitCondition_PublicVisible": "engine.limitCond.publicVisible",
    "LimitCondition_QualityChatty": "engine.limitCond.chatty",
    "LimitCondition_QualityTrustworthy": "engine.limitCond.trustworthy",
    "LimitCondition_ShieldPhysicalPenalty": "engine.limitCond.shieldInTheWay",
    "LimitCondition_SkillGroupStealth": "engine.limitCond.stealthGroup",
    "LimitCondition_SkillGroupStealthNaked": "engine.limitCond.stealthGroupNaked",
    "LimitCondition_SkillsActiveDisguiseImpersonation": "engine.limitCond.disguiseImpersonation",
    "LimitCondition_SkillsActiveEscapeArtist": "engine.limitCond.escapeArtist",
    "LimitCondition_SkillsActiveEscapeArtistGrappleLoose": "engine.limitCond.escapeArtistGrappleLoose",
    "LimitCondition_SkillsActiveFirstAidMedicine": "engine.limitCond.firstAidMedicine",
    "LimitCondition_SkillsActiveGymnasticsClimbing": "engine.limitCond.gymnasticsClimbing",
    "LimitCondition_SkillsActiveLeadership": "engine.limitCond.leadership",
    "LimitCondition_SkillsActiveNavigation": "engine.limitCond.navigation",
    "LimitCondition_SkillsActivePerception": "engine.limitCond.perception",
    "LimitCondition_SkillsActivePerceptionHearing": "engine.limitCond.perceptionHearing",
    "LimitCondition_SkillsActivePerceptionSpatialRecognizer": "engine.limitCond.perceptionSoundSource",
    "LimitCondition_SkillsActivePerceptionVisual": "engine.limitCond.perceptionVisual",
    "LimitCondition_SkillsActivePerformance": "engine.limitCond.performance",
    "LimitCondition_SkillsActivePerformanceSinging": "engine.limitCond.performanceSinging",
    "LimitCondition_SkillsActivePerformanceSynthtrument": "engine.limitCond.performanceSynthtrument",
    "LimitCondition_SkillsActiveSneaking": "engine.limitCond.sneaking",
    "LimitCondition_SkillsActiveSneakingNaked": "engine.limitCond.sneakingNaked",
    "LimitCondition_SkillsActiveSneakingVisible": "engine.limitCond.sneakingVisible",
    "LimitCondition_SkillsActiveSwimming": "engine.limitCond.swimming",
    "LimitCondition_SkillsKnowledgeAcademic": "engine.limitCond.knowledgeAcademic",
    "LimitCondition_SkillsKnowledgeScientificTechnical": "engine.limitCond.knowledgeScientificTechnical",
    "LimitCondition_Skillwires": "engine.limitCond.skillwires",
    "LimitCondition_SportsFans": "engine.limitCond.sportsFans",
    "LimitCondition_SportsRivals": "engine.limitCond.sportsRivals",
    "LimitCondition_Sprawl": "engine.limitCond.sprawl",
    "LimitCondition_TestSneakingThermal": "engine.limitCond.sneakingThermal",
    "LimitCondition_TestSpeech": "engine.limitCond.speech",
    "LimitCondition_TestsEndurance": "engine.limitCond.endurance",
    "LimitCondition_Visible": "engine.limitCond.visible",
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
    leaves ``"3*2"``). Digits and ``+-*/().`` only — no names, calls or powers."""
    expr = value.strip() if isinstance(value, str) else ""
    if len(expr) > MAX_EXPRESSION_LENGTH:
        return default
    if expr and "**" not in expr and _ARITH_RE.match(expr) and not expr.isdigit():
        try:
            return int(evaluate_arithmetic(expr))
        except (UnsafeExpression, ValueError, TypeError):
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
