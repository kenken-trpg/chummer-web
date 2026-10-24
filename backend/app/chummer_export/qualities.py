"""Qualities, what they grant, and martial arts.

The mirror of :mod:`app.chummer_import.qualities`.
"""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from collections.abc import Callable
from copy import deepcopy
from typing import Any, NamedTuple

from ..data_loader import catalog
from ..data_loader._xml import parse_data
from ..engine.constants import (
    QUALITY_ADDSPIRIT_EXTRA_MARKER,
    quality_attribute_extra_key,
    quality_contact_extra_key,
    quality_optional_power_extra_key,
    quality_spirit_category_extra_key,
    quality_take_extra_key,
)
from ..engine.lookups import critter_power_label
from ..engine.priority import talent_options
from ..engine.qualities import _quality_needs_spell_category, _quality_needs_spirit_category, has_extra_per_take
from ..models import CharacterState
from ._common import _Ctx, _Names, _sub, improvements_of
from .life_modules import export_life_modules
from .metatype import export_metatype_powers, export_metatype_qualities


def _export_qualities(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write qualities, spells, adept powers and complex forms."""
    quals = _sub(root, "qualities")
    specs = {str(row["id"]): row for row in catalog()["qualities"]}
    spell_limits: list[tuple[str, str]] = []
    granted: list[tuple[str, str]] = []  # (granting quality id, granted quality's guid)
    bonuses = {node.findtext("id") or "": node for node in parse_data("qualities.xml").findall("./qualities/quality")}
    effects: list[tuple[str, list[_Imp]]] = []  # (quality guid, its improvements)
    takes: dict[str, int] = {}
    for qid in state.quality_ids:
        q = _sub(quals, "quality")
        _sub(q, "sourceid", qid)
        _sub(q, "name", names["quality"].get(qid, ""))
        take = takes.get(qid, 0)
        takes[qid] = take + 1
        extra, spell_category = _quality_extra_out(
            specs.get(qid) or {}, qid, state.quality_extras, {c.id: c.name for c in state.contacts}
        )
        if take and has_extra_per_take(specs.get(qid) or {}):
            extra = state.quality_extras.get(quality_take_extra_key(qid, take), "")
        if spell_category:
            _sub(q, "guid", qid)
            spell_limits.append((qid, spell_category))
        if q.find("guid") is None and any(
            node.get("tag") == "selectinherentaiprogram" for node in (specs.get(qid) or {}).get("bonus") or []
        ):
            # Inherent Program: the AIProgram improvement in
            # `_export_ai_programs` names this quality by its guid
            _sub(q, "guid", qid)
        _sub(q, "extra", extra)
        _sub(q, "qualitysource", "Selected")
        # what its `<bonus>` made, which Chummer keeps instead of running the
        # bonus again on load: an Adept's tab and skills, a Wanted's text
        definition = bonuses.get(qid)
        rows = []
        # `<firstlevelbonus>` runs for the first take only: a Gremlins' notoriety
        for tag in ("bonus", "firstlevelbonus") if not take else ("bonus",):
            node = definition.find(tag) if definition is not None else None
            if node is not None:
                rows += _bonus_improvements(node, 0, extra, state.mentor_id or "")
        if rows:
            if q.find("guid") is None:
                # a second take needs a guid of its own to own its improvements
                _sub(q, "guid", str(uuid.uuid5(uuid.NAMESPACE_URL, f"{qid}:take:{take}")) if take else qid)
            effects.append((q.findtext("guid") or "", rows))
        # A quality with a `<selectskill>` bonus carries the skill picked for
        # it. Unlike the implant picks in `_export_ware`, these are keyed by
        # the quality's catalog id, which survives an import unchanged.
        prefix = f"quality:{qid}:"
        picks = sorted(
            (key[len(prefix) :], value) for key, value in state.skill_picks.items() if key.startswith(prefix)
        )
        if picks:
            picks_el = _sub(q, "skillpicks")
            for index, skill in picks:
                pick = _sub(picks_el, "pick")
                _sub(pick, "index", index)
                _sub(pick, "skill", skill)
        children = _export_granted_qualities(quals, qid, state, names, specs.get(qid) or {}, bonuses)
        if children and q.find("guid") is None:
            _sub(q, "guid", qid)
        for child_guid, rows in children:
            granted.append((qid, child_guid))
            effects.append((child_guid, rows))
        # a contact the quality added (Made Man): Chummer ties it to the
        # quality with an AddContact improvement, which the import follows back
        if any(c.source_quality_id == qid for c in state.contacts) and q.find("guid") is None:
            _sub(q, "guid", qid)
        # the powers it grants (an Infected's, a drake's): each one's
        # CritterPower improvement names this quality by its guid
        spec = specs.get(qid) or {}
        if (spec.get("critter_powers") or spec.get("optional_powers")) and q.find("guid") is None:
            _sub(q, "guid", qid)

    for guid, bonus, extra in export_metatype_qualities(quals, state, ctx):
        effects.append((guid, _bonus_improvements(bonus, 0, extra, state.mentor_id or "")))
    _export_talent_quality(quals, state, bonuses, effects)
    # Chummer keeps life modules here too, as a quality type of their own.
    export_life_modules(quals, state)
    power_links = _export_quality_critter_powers(root, state)
    _export_bought_critter_powers(root, state)
    export_metatype_powers(root, state, ctx)
    # Chummer keeps a picked spell category only on the improvement
    # `<limitspellcategory />` made, tied to the quality by its guid
    links = [(category, qid, "LimitSpellCategory") for qid, category in spell_limits]
    links += [(child_guid, qid, "SpecificQuality") for qid, child_guid in granted]
    links += [(c.id, c.source_quality_id, "AddContact") for c in state.contacts if c.source_quality_id]
    links += [(power_guid, qid, "CritterPower") for power_guid, qid in power_links]
    if links:
        imps = improvements_of(root)
        for improved, qid, kind in links:
            imp = _sub(imps, "improvement")
            _sub(imp, "improvedname", improved)
            _sub(imp, "sourcename", qid)
            _sub(imp, "improvementttype", kind)
            _sub(imp, "improvementsource", "Quality")
    for guid, rows in effects:
        _write_improvements(root, rows, guid, "Quality")


def _export_granted_qualities(
    quals: ET.Element,
    qid: str,
    state: CharacterState,
    names: _Names,
    spec: dict[str, Any],
    bonuses: dict[str, ET.Element],
) -> list[tuple[str, list[_Imp]]]:
    """`<selectquality>` (Prototype Transhuman) and `<addqualities>` (Pie Iesu
    Domine's High Pain Tolerance): Chummer adds each as a quality of its own,
    sourced from the granting one, which a SpecificQuality improvement ties
    to it so removing that one removes the child. Returns each child's guid
    and what its own bonus made — a Wanted it gave keeps its text."""
    ids_by_name = {str(row["name"]): str(row["id"]) for row in catalog()["qualities"]}
    picked = state.quality_extras.get(qid, "")
    children = []
    if str(spec.get("extra_kind") or "") == "quality" and picked in ids_by_name:
        children.append((picked, f"{qid}:selectquality"))
    definition = bonuses.get(qid)
    for added in definition.findall("./bonus/addqualities/addquality") if definition is not None else []:
        if _text(added) in ids_by_name:
            children.append((_text(added), f"{qid}:addquality:{_text(added)}"))
    out = []
    for child_name, key in children:
        child_guid = str(uuid.uuid5(uuid.NAMESPACE_URL, key))
        child_id = ids_by_name[child_name]
        extra = state.quality_extras.get(child_id, "")
        child = _sub(quals, "quality")
        _sub(child, "guid", child_guid)
        _sub(child, "sourceid", child_id)
        _sub(child, "name", child_name)
        _sub(child, "extra", extra)
        _sub(child, "qualitysource", "Improvement")
        _sub(child, "sourcename", names["quality"].get(qid, ""))
        child_definition = bonuses.get(child_id)
        child_bonus = child_definition.find("bonus") if child_definition is not None else None
        out.append((child_guid, _bonus_improvements(child_bonus, 0, extra) if child_bonus is not None else []))
    return out


def _export_talent_quality(
    quals: ET.Element,
    state: CharacterState,
    bonuses: dict[str, ET.Element],
    effects: list[tuple[str, list[_Imp]]],
) -> None:
    """The quality the talent priority gives (Magician, Adept, Technomancer),
    as Chummer's priority form adds it: `qualitysource` Metatype, outside the
    quality limits, its `<bonus>` and what that bonus made — the SpecialTab
    and SpecialSkills improvements Chummer reads to show the magic or
    resonance tab and to unlock the talent's skills. The import passes over
    a Metatype quality, as the talent says the same."""
    name = next(
        (
            str(talent.get("quality") or "")
            for letter in "ABCDE"
            for talent in talent_options(letter)
            if talent.get("name") == state.talent
        ),
        "",
    )
    spec = next((row for row in catalog()["qualities"] if row["name"] == name), None) if name else None
    if spec is None:
        return
    guid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{state.id}:talent:{spec['id']}"))
    q = _sub(quals, "quality")
    for key, value in {
        "sourceid": spec["id"],
        "guid": guid,
        "name": name,
        "extra": "",
        "bp": spec.get("karma") or 0,
        "qualitytype": spec.get("category") or "Positive",
        "qualitysource": "Metatype",
        "contributetobp": "False",
        "contributetolimit": "False",
        "implemented": "True",
        "print": "True",
        "source": spec.get("source") or "",
        "page": spec.get("page") or "",
    }.items():
        _sub(q, key, value)
    definition = bonuses.get(str(spec["id"]))
    bonus = definition.find("bonus") if definition is not None else None
    if bonus is not None:
        q.append(deepcopy(bonus))
        effects.append((guid, _bonus_improvements(bonus, 0, None)))


def _export_quality_critter_powers(root: ET.Element, state: CharacterState) -> list[tuple[str, str]]:
    """`<critterpowers>`: what a quality grants (an Infected's, a drake's, a
    free insect spirit's), plus its one optional power — where Chummer's
    `critterpowers` / `optionalpowers` improvements put them. The optional
    pick has nowhere else to live in a `.chum5`, so without this it is lost on
    the way out.

    Written the way `CritterPower.Save` does after
    `AddImprovementCollection.critterpowers` made it: the definition's
    fields and `<bonus>`, the quality's rating and pick, `grade` −1 (a power a
    quality gave), and a guid. Returns (power guid, quality id) for the
    CritterPower improvement that ties each power to its quality — which is
    what Chummer follows to take the powers away with the quality.
    """
    by_id = {str(row["id"]): row for row in catalog()["qualities"]}
    rows: dict[str, dict[str, Any]] = {}
    for row in catalog().get("critter_powers") or []:
        rows.setdefault(str(row.get("name") or ""), row)  # the first definition, as `critter_power_spec`
    definitions = {
        node.findtext("id") or "": node for node in parse_data("critterpowers.xml").findall("./powers/power")
    }
    refs: list[tuple[str, dict[str, Any]]] = []
    for qid in state.quality_ids:
        spec = by_id.get(qid) or {}
        refs.extend((qid, ref) for ref in spec.get("critter_powers") or [])
        picked = state.quality_extras.get(quality_optional_power_extra_key(qid), "")
        refs.extend((qid, ref) for ref in spec.get("optional_powers") or [] if critter_power_label(ref) == picked)
    if not refs:
        return []
    powers = _sub(root, "critterpowers")
    links = []
    for index, (qid, ref) in enumerate(refs):
        row = rows.get(str(ref["name"])) or {}
        guid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{state.id}:quality:{qid}:power:{index}:{ref['name']}"))
        el = _sub(powers, "critterpower")
        _sub(el, "sourceid", row.get("id") or "")
        _sub(el, "guid", guid)
        _sub(el, "name", ref["name"])
        for key in ("category", "type", "action", "range", "duration", "source", "page"):
            _sub(el, key, row.get(key) or "")
        rating = int(ref.get("rating") or 0)
        # CritterPower.Create: the pick, else a non-zero rating, is the extra
        _sub(el, "extra", ref.get("select") or (str(rating) if rating else ""))
        _sub(el, "rating", rating)
        _sub(el, "grade", -1)
        definition = definitions.get(str(row.get("id") or ""))
        bonus = definition.find("bonus") if definition is not None else None
        if bonus is not None:
            el.append(deepcopy(bonus))
            _export_power_improvements(root, bonus, guid, rating, str(ref.get("select") or ""))
        links.append((guid, qid))
    return links


def _export_power_improvements(root: ET.Element, bonus: ET.Element, guid: str, rating: int, pick: str) -> None:
    """What `CritterPower.Create` leaves in `<improvements>` when it runs a
    power's `<bonus>` — Chummer keeps saved improvements as they are on load
    and never runs a bonus again, so a power without them does nothing there
    (a drake's Hardened Armor added no armor). Covers the tags the powers a
    quality grants carry; Innate Spell's `enabletab` / `selectspell` waits on
    a spell to pick, which the quality does not give."""
    if bonus.find("selectspell") is not None:
        return
    _write_improvements(root, _bonus_improvements(bonus, rating, pick or None), guid, "CritterPower")


def _bonus_improvements(bonus: ET.Element, rating: int, pick: str | None, mentor: str = "") -> list[_Imp]:
    """The improvements the tags of `bonus` make whose improvement needs
    nothing but the bonus, its rating and its pick — as
    `AddImprovementCollection` makes them. `pick` None: nothing was picked,
    so `<selecttext>` makes nothing. `mentor`: the mentor spirit or paragon
    picked, whose `<mentorspirit>` row `_export_mentor_block` writes with the
    id as its guid."""
    rows: list[_Imp] = []
    for node in bonus:
        if node.tag == "selecttext":
            rows += [_Imp("Text", pick)] if pick is not None else []
        elif node.tag in ("selectmentorspirit", "selectparagon"):
            kind = "MentorSpirit" if node.tag == "selectmentorspirit" else "Paragon"
            rows += [_Imp(kind, mentor, unique=mentor)] if mentor else []
        elif node.tag in _COSTS:
            rows += _cost(node)
        elif node.tag in _NUMBERS:
            text = (node.text or "").strip()
            rows += [_Imp(_NUMBERS[node.tag], val=int(text))] if _is_int(text) else []
        elif node.tag in _READERS:
            rows += _READERS[node.tag](node, rating)
    return rows


def _text(node: ET.Element, field: str | None = None) -> str:
    return ((node.text if field is None else node.findtext(field)) or "").strip()


def _is_int(text: str | None) -> bool:
    return (text or "").strip().lstrip("-").isdigit()


def _precedence(node: ET.Element) -> str:
    """`addlimb` / `conditionmonitor`: a `precedence` attribute is the unique."""
    return f"precedence{node.get('precedence')}" if node.get("precedence") else ""


def _cost(node: ET.Element) -> list[_Imp]:
    kind, named = _COSTS[node.tag]
    numbers = [_text(node, field) or "0" for field in ("val", "min", "max")]
    if not all(_is_int(number) for number in numbers):
        return []
    val, low, high = (int(number) for number in numbers)
    return [
        _Imp(kind, _text(node, "name") if named else "", val=val, min=low, max=high, condition=_text(node, "condition"))
    ]


def _unlockskills(node: ET.Element, rating: int) -> list[_Imp]:
    return [_Imp("SpecialSkills", _text(node), target=node.get("name") or "")] if _text(node) else []


def _enabletab(node: ET.Element, rating: int) -> list[_Imp]:
    tabs = (_TABS.get(_text(name).upper()) for name in node.findall("name"))
    return [_Imp("SpecialTab", tab, unique="enabletab") for tab in tabs if tab]


def _armor(node: ET.Element, rating: int) -> list[_Imp]:
    text = _text(node)
    if text == "Rating":
        return [_Imp("Armor", val=rating)]
    return [_Imp("Armor", val=int(text))] if _is_int(text) else []


def _disablegrade(node: ET.Element, rating: int) -> list[_Imp]:
    kind = "DisableBiowareGrade" if node.tag == "disablebiowaregrade" else "DisableCyberwareGrade"
    return [_Imp(kind, _text(node), unique=node.tag)]


def _specificskill(node: ET.Element, rating: int) -> list[_Imp]:
    amount = _text(node, "bonus")
    return [_Imp("Skill", _text(node, "name"), val=int(amount))] if _is_int(amount) else []


def _flag(node: ET.Element, rating: int) -> list[_Imp]:
    """`ambidextrous`, `fame`: an improvement with no value."""
    return [_Imp(node.tag.capitalize())]


def _sociallimit(node: ET.Element, rating: int) -> list[_Imp]:
    return [_Imp("SocialLimit", "Social", val=int(_text(node)))] if _is_int(_text(node)) else []


def _lifestylecost(node: ET.Element, rating: int) -> list[_Imp]:
    if not _is_int(_text(node)):
        return []
    return [
        _Imp("LifestyleCost", node.get("lifestyle") or "", val=int(_text(node)), condition=node.get("condition") or "")
    ]


def _skillcategory(node: ET.Element, rating: int) -> list[_Imp]:
    """`skillcategory`, `skillgroup`: a bonus to every skill of the name."""
    if not _text(node, "name") or not _is_int(_text(node, "bonus")):
        return []
    return [
        _Imp(
            "SkillCategory" if node.tag == "skillcategory" else "SkillGroup",
            _text(node, "name"),
            val=int(_text(node, "bonus")),
            condition=_text(node, "condition"),
            exclude=_text(node, "exclude"),
            addtorating=_text(node, "applytorating").lower() == "true",
        )
    ]


def _restrictedgear(node: ET.Element, rating: int) -> list[_Imp]:
    """The availability is the value and the amount the rating; an old
    `<restrictedgear>24</restrictedgear>` is one item."""
    availability, amount = _text(node, "availability"), _text(node, "amount")
    if not amount:
        availability, amount = availability or _text(node), "1"
    if not (_is_int(availability) and _is_int(amount)):
        return []
    return [_Imp("RestrictedGear", val=int(availability), rating=int(amount))]


def _movementreplace(node: ET.Element, rating: int) -> list[_Imp]:
    """A walk, run or sprint speed, for its category or for all three."""
    if not _is_int(_text(node, "val")):
        return []
    kind = {"RUN": "RunSpeed", "SPRINT": "SprintSpeed"}.get(_text(node, "speed").upper(), "WalkSpeed")
    categories = [_text(node, "category")] if _text(node, "category") else ["Ground", "Swim", "Fly"]
    return [_Imp(kind, category, val=int(_text(node, "val"))) for category in categories]


def _sprintbonus(node: ET.Element, rating: int) -> list[_Imp]:
    category = _text(node, "category")
    if not category:
        return []
    fields = (("val", "SprintBonus"), ("percent", "SprintBonusPercent"))
    return [
        _Imp(kind, category, val=int(_text(node, field)))
        for field, kind in fields
        if _is_int(_text(node, field)) and int(_text(node, field))
    ]


def _addlimb(node: ET.Element, rating: int) -> list[_Imp]:
    if not _is_int(_text(node, "val")):
        return []
    return [_Imp("AddLimb", _text(node, "limbslot"), unique=_precedence(node), val=int(_text(node, "val")))]


def _cyberseeker(node: ET.Element, rating: int) -> list[_Imp]:
    return [_Imp("Seeker", _text(node))] if _text(node) in _SEEKER else []


def _livingpersona(node: ET.Element, rating: int) -> list[_Imp]:
    """Each attribute's bonus as the improved name, a positive number signed."""
    rows = []
    for child in node:
        amount = _text(child).replace("Rating", str(rating))
        if child.tag in _PERSONA and amount:
            rows.append(_Imp(_PERSONA[child.tag], f"+{amount}" if _is_int(amount) and int(amount) > 0 else amount))
    return rows


def _conditionmonitor(node: ET.Element, rating: int) -> list[_Imp]:
    kinds = {
        "physical": "PhysicalCM",
        "stun": "StunCM",
        "threshold": "CMThreshold",
        "thresholdoffset": "CMThresholdOffset",
    }
    return [
        _Imp(kinds[child.tag], unique=_precedence(child), val=int(_text(child)))
        for child in node
        if child.tag in kinds and _is_int(_text(child))
    ]


_READERS: dict[str, Callable[[ET.Element, int], list[_Imp]]] = {
    "unlockskills": _unlockskills,
    "enabletab": _enabletab,
    "armor": _armor,
    "disablebiowaregrade": _disablegrade,
    "disablecyberwaregrade": _disablegrade,
    "specificskill": _specificskill,
    "ambidextrous": _flag,
    "fame": _flag,
    "sociallimit": _sociallimit,
    "lifestylecost": _lifestylecost,
    "skillcategory": _skillcategory,
    "skillgroup": _skillcategory,
    "restrictedgear": _restrictedgear,
    "movementreplace": _movementreplace,
    "sprintbonus": _sprintbonus,
    "addlimb": _addlimb,
    "cyberseeker": _cyberseeker,
    "livingpersona": _livingpersona,
    "conditionmonitor": _conditionmonitor,
}


class _Imp(NamedTuple):
    """One improvement, in the fields `Improvement.Save` writes that a bonus sets."""

    kind: str
    improved: str = ""
    target: str = ""
    unique: str = ""
    val: int = 0
    min: int = 0
    max: int = 0
    condition: str = ""
    rating: int = 1
    exclude: str = ""
    addtorating: bool = False


#: The karma and point cost tags, (type, whether `<name>` is the improved
#: name): every one of them is a single `CreateImprovement` of its `<name>`,
#: `<val>`, `<min>`, `<max>` and `<condition>`.
_COSTS = {
    "attributekarmacost": ("AttributeKarmaCost", True),
    "activeskillkarmacost": ("ActiveSkillKarmaCost", True),
    "skillgroupkarmacost": ("SkillGroupKarmaCost", True),
    "knowledgeskillkarmacost": ("KnowledgeSkillKarmaCost", True),
    "knowledgeskillkarmacostmin": ("KnowledgeSkillKarmaCostMinimum", False),
    "skillgroupcategorykarmacost": ("SkillGroupCategoryKarmaCost", True),
    "skillcategorykarmacost": ("SkillCategoryKarmaCost", True),
    "skillcategoryspecializationkarmacost": ("SkillCategorySpecializationKarmaCost", True),
    "attributepointcost": ("AttributePointCost", True),
    "activeskillpointcost": ("ActiveSkillPointCost", True),
    "skillgrouppointcost": ("SkillGroupPointCost", True),
    "knowledgeskillpointcost": ("KnowledgeSkillPointCost", True),
    "skillgroupcategorypointcost": ("SkillGroupCategoryPointCost", True),
    "skillcategorypointcost": ("SkillCategoryPointCost", True),
    "attributekarmacostmultiplier": ("AttributeKarmaCostMultiplier", True),
    "activeskillkarmacostmultiplier": ("ActiveSkillKarmaCostMultiplier", True),
    "skillgroupkarmacostmultiplier": ("SkillGroupKarmaCostMultiplier", True),
    "knowledgeskillkarmacostmultiplier": ("KnowledgeSkillKarmaCostMultiplier", True),
    "skillgroupcategorykarmacostmultiplier": ("SkillGroupCategoryKarmaCostMultiplier", True),
    "skillcategorykarmacostmultiplier": ("SkillCategoryKarmaCostMultiplier", True),
    "skillcategoryspecializationkarmacostmultiplier": ("SkillCategorySpecializationKarmaCostMultiplier", True),
    "attributepointcostmultiplier": ("AttributePointCostMultiplier", True),
    "activeskillpointcostmultiplier": ("ActiveSkillPointCostMultiplier", True),
    "skillgrouppointcostmultiplier": ("SkillGroupPointCostMultiplier", True),
    "knowledgeskillpointcostmultiplier": ("KnowledgeSkillPointCostMultiplier", True),
    "skillgroupcategorypointcostmultiplier": ("SkillGroupCategoryPointCostMultiplier", True),
    "skillcategorypointcostmultiplier": ("SkillCategoryPointCostMultiplier", True),
}

#: Tags whose improvement is their number and nothing else — every
#: `AddImprovementCollection` method that is one `CreateImprovement` of the
#: tag's text as the value.
_NUMBERS = {
    "surprise": "Surprise",
    "spellresistance": "SpellResistance",
    "mentalmanipulationresist": "MentalManipulationResist",
    "physicalmanipulationresist": "PhysicalManipulationResist",
    "manaillusionresist": "ManaIllusionResist",
    "physicalillusionresist": "PhysicalIllusionResist",
    "detectionspellresist": "DetectionSpellResist",
    "directmanaspellresist": "DirectManaSpellResist",
    "directphysicalspellresist": "DirectPhysicalSpellResist",
    "decreasebodresist": "DecreaseBODResist",
    "decreaseagiresist": "DecreaseAGIResist",
    "decreaserearesist": "DecreaseREAResist",
    "decreasestrresist": "DecreaseSTRResist",
    "decreasecharesist": "DecreaseCHAResist",
    "decreaseintresist": "DecreaseINTResist",
    "decreaselogresist": "DecreaseLOGResist",
    "decreasewilresist": "DecreaseWILResist",
    "nuyenmaxbp": "NuyenMaxBP",
    "unarmeddv": "UnarmedDV",
    "unarmedap": "UnarmedAP",
    "unarmedreach": "UnarmedReach",
    "initiative": "Initiative",
    "initiativediceadd": "InitiativeDiceAdd",
    "matrixinitiative": "MatrixInitiative",
    "biowareessmultiplier": "BiowareEssCost",
    "biowaretotalessmultiplier": "BiowareTotalEssMultiplier",
    "cyberwareessmultiplier": "CyberwareEssCost",
    "cyberwaretotalessmultiplier": "CyberwareTotalEssMultiplier",
    "biowareessmultipliernonretroactive": "BiowareEssCostNonRetroactive",
    "biowaretotalessmultipliernonretroactive": "BiowareTotalEssMultiplierNonRetroactive",
    "cyberwareessmultipliernonretroactive": "CyberwareEssCostNonRetroactive",
    "cyberwaretotalessmultipliernonretroactive": "CyberwareTotalEssMultiplierNonRetroactive",
    "nativelanguagelimit": "NativeLanguageLimit",
    "freepositivequalities": "FreePositiveQualities",
    "freenegativequalities": "FreeNegativeQualities",
    "freespiritpowerpoints": "FreeSpiritPowerPoints",
    "adeptpowerpoints": "AdeptPowerPoints",
    "armorencumbrancepenalty": "ArmorEncumbrancePenalty",
    "damageresistance": "DamageResistance",
    "judgeintentions": "JudgeIntentions",
    "judgeintentionsoffense": "JudgeIntentionsOffense",
    "judgeintentionsdefense": "JudgeIntentionsDefense",
    "composure": "Composure",
    "liftandcarry": "LiftAndCarry",
    "memory": "Memory",
    "fatigueresist": "FatigueResist",
    "radiationresist": "RadiationResist",
    "sonicresist": "SonicResist",
    "toxincontactresist": "ToxinContactResist",
    "toxiningestionresist": "ToxinIngestionResist",
    "toxininhalationresist": "ToxinInhalationResist",
    "toxininjectionresist": "ToxinInjectionResist",
    "pathogencontactresist": "PathogenContactResist",
    "pathogeningestionresist": "PathogenIngestionResist",
    "pathogeninhalationresist": "PathogenInhalationResist",
    "pathogeninjectionresist": "PathogenInjectionResist",
    "physiologicaladdictionfirsttime": "PhysiologicalAddictionFirstTime",
    "psychologicaladdictionfirsttime": "PsychologicalAddictionFirstTime",
    "physiologicaladdictionalreadyaddicted": "PhysiologicalAddictionAlreadyAddicted",
    "psychologicaladdictionalreadyaddicted": "PsychologicalAddictionAlreadyAddicted",
    "stuncmrecovery": "StunCMRecovery",
    "physicalcmrecovery": "PhysicalCMRecovery",
    "concealability": "Concealability",
    "drainresist": "DrainResistance",
    "fadingresist": "FadingResistance",
    "notoriety": "Notoriety",
    "streetcred": "StreetCred",
    "streetcredmultiplier": "StreetCredMultiplier",
    "complexformlimit": "ComplexFormLimit",
    "spelllimit": "SpellLimit",
    "throwrange": "ThrowRange",
    "throwrangestr": "ThrowRangeSTR",
    "throwstr": "ThrowSTR",
    "essencepenalty": "EssencePenalty",
    "essencepenaltyt100": "EssencePenaltyT100",
    "essencepenaltymagonlyt100": "EssencePenaltyMAGOnlyT100",
    "essencepenaltyresonlyt100": "EssencePenaltyRESOnlyT100",
    "essencepenaltydeponlyt100": "EssencePenaltyDEPOnlyT100",
    "specialattburnmultiplier": "SpecialAttBurn",
    "specialatttotalburnmultiplier": "SpecialAttTotalBurnMultiplier",
    "essencemax": "EssenceMax",
    "publicawareness": "PublicAwareness",
    "metageniclimit": "MetageneticLimit",
    "specialmodificationlimit": "SpecialModificationLimit",
    "contactkarma": "ContactKarmaDiscount",
    "contactkarmaminimum": "ContactKarmaMinimum",
}

#: `livingpersona`'s children, as the types they make
_PERSONA = {
    "devicerating": "LivingPersonaDeviceRating",
    "programlimit": "LivingPersonaProgramLimit",
    "attack": "LivingPersonaAttack",
    "sleaze": "LivingPersonaSleaze",
    "dataprocessing": "LivingPersonaDataProcessing",
    "firewall": "LivingPersonaFirewall",
}

#: `AttributeSection.AttributeStrings`, plus the `BOX` `cyberseeker` takes
_SEEKER = {"BOD", "AGI", "REA", "STR", "CHA", "INT", "LOG", "WIL", "EDG", "MAG", "MAGAdept", "RES", "ESS", "DEP", "BOX"}


#: `AddImprovementCollection.enabletab`: the tab names it knows, as it saves them
_TABS = {
    "MAGICIAN": "Magician",
    "ADEPT": "Adept",
    "TECHNOMANCER": "Technomancer",
    "ADVANCED PROGRAMS": "Advanced Programs",
    "CRITTER": "Critter",
}


def _write_improvements(root: ET.Element, rows: list[_Imp], source_name: str, source: str) -> None:
    if not rows:
        return
    imps = improvements_of(root)
    for row in rows:
        imp = _sub(imps, "improvement")
        if row.unique:
            _sub(imp, "unique", row.unique)
        _sub(imp, "target", row.target)
        _sub(imp, "improvedname", row.improved)
        _sub(imp, "sourcename", source_name)
        _sub(imp, "min", row.min)
        _sub(imp, "max", row.max)
        _sub(imp, "val", row.val)
        _sub(imp, "rating", row.rating)
        _sub(imp, "exclude", row.exclude)
        _sub(imp, "condition", row.condition)
        _sub(imp, "improvementttype", row.kind)
        _sub(imp, "improvementsource", source)
        if row.addtorating:
            _sub(imp, "addtorating", "True")


def _export_bought_critter_powers(root: ET.Element, state: CharacterState) -> None:
    """The powers bought on the Critter Powers tab, as CharacterCreate adds
    them: made from the definition at the picked rating, `grade` 0, its
    `<karma>` kept (the create form sums it), and no improvement — nothing
    granted it, so nothing takes it away."""
    if not state.critter_powers:
        return
    stock = {str(row["id"]): row for row in catalog().get("buyable_critter_powers") or []}
    definitions = {
        node.findtext("id") or "": node for node in parse_data("critterpowers.xml").findall("./powers/power")
    }
    powers = root.find("critterpowers")
    if powers is None:
        powers = _sub(root, "critterpowers")
    for inst in state.critter_powers:
        spec = stock.get(inst.power_id)
        if spec is None:
            continue
        el = _sub(powers, "critterpower")
        _sub(el, "sourceid", spec["id"])
        _sub(el, "guid", inst.id)
        _sub(el, "name", spec["name"])
        for key in ("category", "type", "action", "range", "duration", "source", "page"):
            _sub(el, key, spec.get(key) or "")
        _sub(el, "extra", inst.extra or "")
        _sub(el, "rating", inst.rating or 0)
        _sub(el, "grade", 0)
        _sub(el, "counttowardslimit", "True")
        _sub(el, "karma", int(spec.get("karma") or 0))
        definition = definitions.get(str(spec["id"]))
        bonus = definition.find("bonus") if definition is not None else None
        if bonus is not None:
            el.append(deepcopy(bonus))


def _quality_extra_out(
    spec: dict[str, Any], qid: str, extras: dict[str, str], contact_names: dict[str, str]
) -> tuple[str, str]:
    """A quality's `<extra>` as Chummer writes it, and a spell category that
    has to go on an improvement instead.

    Chummer's `AddSpiritOrSprite` appends every spirit it is given to the
    quality's selected value, `, `-joined: Chain Breaker's two `<addspirit>`
    picks, or Apprentice's `<limitspiritcategory>` spirit — whose
    `<limitspellcategory>` pick is not added, so it rides an improvement.
    `<selectcontact>` appends the contact's name the same way, after Black
    Market Pipeline's category.
    """
    slots = [slot for node in spec.get("bonus") or [] for slot in node.get("attribute_choices") or []]
    if slots:
        attributes = [extras.get(quality_attribute_extra_key(qid, idx), "") for idx in range(len(slots))]
        if all(attributes) and len(set(attributes)) == 1:
            return attributes[0], ""
        return ", ".join(f"{a} ({attributes.count(a)})" for a in dict.fromkeys(attributes) if a), ""
    if str(spec.get("extra_kind") or "") == "add_spirit":
        marker = f"{qid}{QUALITY_ADDSPIRIT_EXTRA_MARKER}"
        picks = sorted(
            (int(key[len(marker) :]), value)
            for key, value in extras.items()
            if key.startswith(marker) and key[len(marker) :].isdigit() and value
        )
        return ", ".join(value for _, value in picks), ""
    if _quality_needs_spirit_category(spec) and _quality_needs_spell_category(spec):
        return extras.get(quality_spirit_category_extra_key(qid), ""), extras.get(qid, "")
    if str(spec.get("extra_kind") or "") == "quality":
        # the pick is a quality of its own; see `_export_qualities`
        return "", ""
    if _quality_selects_contact(spec):
        contact = contact_names.get(extras.get(quality_contact_extra_key(qid), ""), "")
        return ", ".join(part for part in (extras.get(qid, ""), contact) if part), ""
    return extras.get(qid, ""), ""


def _quality_selects_contact(spec: dict[str, Any]) -> bool:
    return any(node.get("tag") == "selectcontact" for node in spec.get("bonus") or [])


def _export_martial_arts(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write martial arts and their techniques."""
    marts = _sub(root, "martialarts")
    for row in state.martial_arts:
        el = _sub(marts, "martialart")
        _sub(el, "sourceid", row.art_id)
        _sub(el, "name", names["martialart"].get(row.art_id, ""))
        techs = _sub(el, "martialarttechniques")
        for tn in row.techniques:
            _sub(_sub(techs, "martialarttechnique"), "name", tn)
