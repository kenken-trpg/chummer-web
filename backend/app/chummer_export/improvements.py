"""The improvements a `<bonus>` makes, as Chummer's `AddImprovementCollection`
makes them, for the export to write beside the row that owns the bonus.

Chummer never runs a bonus again when it opens a file: it keeps the saved
improvements as they are. So a quality, an implant or a power exported
without them does nothing there. Each tag this knows is read by the
function `AddImprovementCollection` would run for it, from the bonus, the
owner's rating and its pick; a tag it does not know makes nothing.
"""

from __future__ import annotations

import ast
import re
import uuid
import xml.etree.ElementTree as ET
from collections.abc import Callable
from copy import deepcopy
from typing import NamedTuple

from ..data_loader import catalog_list
from ..data_loader._xml import parse_data
from ._common import _sub, improvements_of


def _bonus_improvements(
    bonus: ET.Element,
    rating: int,
    pick: str | None,
    mentor: str = "",
    contact: str = "",
    attributes: list[str] | None = None,
    skills: dict[str, str] | None = None,
    spell_category: str = "",
) -> list[_Imp]:
    """The improvements the tags of `bonus` make whose improvement needs
    nothing but the bonus, its rating and its pick — as
    `AddImprovementCollection` makes them. `pick` None: nothing was picked,
    so `<selecttext>` makes nothing. `mentor`: the mentor spirit or paragon
    picked, whose `<mentorspirit>` row `_export_mentor_block` writes with the
    id as its guid. `contact`: the id of the contact the quality added.
    `attributes`: the attribute picked for each `<selectattribute>`, in order.
    `skills`: the skill picks, keyed as `resolve_skill_picks` numbers them —
    `0`, `1`… for each `<selectskill>` / `<hardwires>`, `acc0`… for each
    `<weaponskillaccuracy>` that asks for one. `spell_category`: the category
    an empty `<limitspellcategory />` picked, which Chummer keeps on that
    improvement rather than in the extra; a `<spellcategorydrain>` with no
    category of its own is that one's (Hedge Witch/Wizard)."""
    rows: list[_Imp] = []
    picked = accuracy = 0
    # the spirits `AddSpiritOrSprite` asked for, in the order the tags ask:
    # Chain Breaker's two `<addspirit />` are the first and second of its pick
    # (an Apprentice's extra leads with its spell category, which is not one)
    spirits = [part.strip() for part in (pick or "").split(",") if part.strip() and part.strip() != spell_category]
    for node in _rated(bonus, rating) if rating else bonus:
        if node.tag in ("selectskill", "hardwires"):
            # the first pick is also the owner's own pick (`SelectedValue`,
            # which Chummer saves as the extra), when no slot holds it
            name = (skills or {}).get(str(picked), "") or (pick or "" if not picked else "")
            picked += 1
            rows += _selectskill(node, name) if node.tag == "selectskill" and name else []
            continue
        if node.tag == "weaponskillaccuracy":
            if node.find("selectskill") is not None:
                name = (skills or {}).get(f"acc{accuracy}", "") or (pick or "" if not accuracy else "")
                accuracy += 1
            else:
                name = _text(node, "name")
            value = _text(node, "value")
            rows += [_Imp("WeaponSkillAccuracy", name, val=int(value))] if name and _is_int(value) else []
            continue
        if node.tag in ("selecttext", "selectweapon"):
            rows += [_Imp("Text", pick)] if pick is not None else []
        elif node.tag == "weaponspecificdice":
            # the weapon picked, by its guid
            value = _text(node)
            rows += [_Imp("WeaponSpecificDice", pick, val=int(value))] if pick and _is_int(value) else []
        elif node.tag in _PICKS:
            rows += [_Imp(_PICKS[node.tag], pick)] if pick else []
        elif node.tag in ("selectmentorspirit", "selectparagon"):
            kind = "MentorSpirit" if node.tag == "selectmentorspirit" else "Paragon"
            rows += [_Imp(kind, mentor, unique=mentor)] if mentor else []
        elif node.tag == "selectattribute":
            options = {_text(option) for option in node.findall("attribute")} or _SEEKER - {
                "BOX",
                "ESS",
                *(_text(option) for option in node.findall("excludeattribute")),
            }
            rows += _attribute(node, pick) if pick and pick in options else []
        elif node.tag == "selectattributes":
            rows += _selectattributes(node, attributes or [])
        elif node.tag in ("limitspiritcategory", "addspirit"):
            rows += _spirit_pick(node, spirits)
        elif node.tag in _SPELL_DRAIN:
            kind, field = _SPELL_DRAIN[node.tag]
            named = _text(node, field) or (spell_category if node.tag == "spellcategorydrain" else "")
            value = _text(node, "val")
            rows += [_Imp(kind, named, val=int(value))] if named and _is_int(value) else []
        elif node.tag == "addcontact":
            rows += _addcontact(node, contact) if contact else []
        elif node.tag in _COSTS:
            rows += _cost(node)
        elif node.tag in _NUMBERS:
            text = (node.text or "").strip()
            rows += [_Imp(_NUMBERS[node.tag], val=int(text))] if _is_int(text) else []
        elif node.tag in _READERS:
            rows += _READERS[node.tag](node, rating)
    # `<bonus unique="…">` is the unique name of every improvement the tags
    # make that does not name its own: Chemical Protection twice counts once
    unique = bonus.get("unique") or ""
    return [row._replace(unique=row.unique or unique) for row in rows]


def _rated(bonus: ET.Element, rating: int) -> ET.Element:
    """A copy of `bonus` with every value that depends on the rating worked
    out, as `ImprovementManager.ValueToDec` does: `Rating`, `{Rating}`,
    `FixedValues(3,6,9)` (the rating-th), `number(Rating >= 2)` and plain
    arithmetic of them. A value that comes out fractional is left as it was,
    so it makes nothing."""
    out = deepcopy(bonus)
    for el in out.iter():
        text = (el.text or "").strip()
        if not text or not re.search(r"Rating|FixedValues", text):
            continue
        text = re.sub(
            r"FixedValues\(([^)]*)\)",
            lambda m: m.group(1).split(",")[max(0, min(rating, len(m.group(1).split(","))) - 1)].strip(),
            text,
        )
        text = re.sub(
            r"number\(\s*\{?Rating\}?\s*>=\s*(\d+)\s*\)", lambda m: "1" if rating >= int(m.group(1)) else "0", text
        )
        text = re.sub(r"\{?Rating\}?", str(rating), text)
        if re.fullmatch(r"[\d\s+\-*/().]+", text):
            value = _arithmetic(ast.parse(text, mode="eval").body)
            if value is not None and float(value).is_integer():
                el.text = str(int(value))
    return out


def _arithmetic(node: ast.expr) -> float | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _arithmetic(node.operand)
        return None if inner is None else -inner
    if isinstance(node, ast.BinOp):
        left, right = _arithmetic(node.left), _arithmetic(node.right)
        if left is None or right is None:
            return None
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div) and right:
            return left / right
    return None


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


#: `armor` and the elemental armor tags, as the types they make
_ARMORS = {
    "armor": "Armor",
    "firearmor": "FireArmor",
    "coldarmor": "ColdArmor",
    "electricityarmor": "ElectricityArmor",
    "acidarmor": "AcidArmor",
}


def _armor(node: ET.Element, rating: int) -> list[_Imp]:
    """A `precedence` or `group` attribute is the unique name, as
    `AddImprovementCollection.armor` makes it."""
    text = _text(node)
    if text == "Rating":
        text = str(rating)
    if not _is_int(text):
        return []
    precedence, group = node.get("precedence"), node.get("group")
    unique = f"precedence{precedence}" if precedence else f"group{group}" if group else ""
    return [_Imp(_ARMORS[node.tag], val=int(text), unique=unique)]


def _disablegrade(node: ET.Element, rating: int) -> list[_Imp]:
    kind = "DisableBiowareGrade" if node.tag == "disablebiowaregrade" else "DisableCyberwareGrade"
    return [_Imp(kind, _text(node), unique=node.tag)]


def _specificskill(node: ET.Element, rating: int) -> list[_Imp]:
    amount = _text(node, "bonus")
    return [_Imp("Skill", _text(node, "name"), val=int(amount))] if _is_int(amount) else []


def _selectskill(node: ET.Element, name: str) -> list[_Imp]:
    """The picked skill's bonus, its specialization switch and its cap, each
    an improvement of its own, as `selectskill` makes them."""
    addtorating = _text(node, "applytorating").lower() == "true"
    rows = []
    if _is_int(_text(node, "val")):
        rows.append(_Imp("Skill", name, val=int(_text(node, "val")), addtorating=addtorating))
    if _text(node, "disablespecializationeffects").lower() == "true":
        rows.append(_Imp("DisableSpecializationEffects", name))
    if _is_int(_text(node, "max")):
        rows.append(_Imp("Skill", name, max=int(_text(node, "max")), addtorating=addtorating))
    return rows


#: Tags whose improvement names the owner's pick, as the types they make:
#: a Fake License's license, the tradition of a magical supply
_PICKS = {"selectrestricted": "Restricted", "selecttradition": "Tradition"}


#: Tags whose improvement carries no value, as the types they make
_FLAGS = {
    "ambidextrous": ("Ambidextrous", ""),
    "fame": ("Fame", ""),
    "mademan": ("MadeMan", ""),
    "unarmeddvphysical": ("UnarmedDVPhysical", ""),
    "adapsin": ("Adapsin", "adapsin"),
    # Resonant Stream: Technoshaman: Chummer lets a sprite be fettered only
    # while this improvement is there, and nothing here fetters one
    "allowspritefettering": ("AllowSpriteFettering", ""),
    **{
        f"{kind}{vector}immune": (f"{kind.title()}{vector.title()}Immune", "")
        for kind in ("toxin", "pathogen")
        for vector in ("contact", "ingestion", "inhalation", "injection")
    },
}


def _flag(node: ET.Element, rating: int) -> list[_Imp]:
    kind, unique = _FLAGS[node.tag]
    return [_Imp(kind, unique=unique)]


def _limit(node: ET.Element, rating: int) -> list[_Imp]:
    """`physicallimit`, `mentallimit`, `sociallimit`: the limit is the improved name."""
    limit = node.tag.removesuffix("limit").capitalize()
    return [_Imp(f"{limit}Limit", limit, val=int(_text(node)))] if _is_int(_text(node)) else []


def _smartlink(node: ET.Element, rating: int) -> list[_Imp]:
    return [_Imp("Smartlink", unique="smartlink", val=int(_text(node)))] if _is_int(_text(node)) else []


def _named(kind: str) -> Callable[[ET.Element, int], list[_Imp]]:
    """A tag whose text is the one thing it names: `<skilldisable>Binding`,
    `<limitspellcategory>Rituals`. An empty `<limitspellcategory />` is a
    pick, which `_export_qualities` writes."""

    def read(node: ET.Element, rating: int) -> list[_Imp]:
        return [_Imp(kind, _text(node))] if _text(node) else []

    return read


#: (type, the field naming the category or the descriptor) for the tags that
#: change the drain or the damage of some spells.
_SPELL_DRAIN = {
    "spellcategorydrain": ("SpellCategoryDrain", "category"),
    "spellcategorydamage": ("SpellCategoryDamage", "category"),
    "spelldescriptordrain": ("SpellDescriptorDrain", "descriptor"),
    "spelldescriptordamage": ("SpellDescriptorDamage", "descriptor"),
}


def _spirit_pick(node: ET.Element, spirits: list[str]) -> list[_Imp]:
    """`limitspiritcategory`, `addspirit`: one spirit each, from the list the
    tag gives when it gives one alone (Elementalist's, a Watcher's), or else
    the next of the spirits picked (`spirits`, taken from the front). A
    Dedicated Conjurer's `skill` adds the AddSpiritSkill that counts its
    picks, with the divisor as the improvement's rating."""
    rows = []
    if node.tag == "addspirit" and node.get("skill"):
        divisor = node.get("ratingdivisor") or "1"
        rows.append(_Imp("AddSpiritSkill", node.get("skill") or "", rating=int(divisor) if _is_int(divisor) else 1))
        # how many it asks for follows the skill's rating, which the bonus
        # alone does not know, and this app keeps no pick for them
        return rows
    listed = [_text(spirit) for spirit in node.findall("spirit") if _text(spirit)]
    kind = "LimitSpiritCategory" if node.tag == "limitspiritcategory" else "AddSpirit"
    if len(listed) == 1:
        if spirits and spirits[0] == listed[0]:
            spirits.pop(0)
        return [*rows, _Imp(kind, listed[0])]
    if spirits and (not listed or spirits[0] in listed):
        return [*rows, _Imp(kind, spirits.pop(0))]
    return rows


def _focus_binding(node: ET.Element, rating: int) -> list[_Imp]:
    """`focusbindingkarmacost`, `focusbindingkarmamultiplier`: the focus is
    the improved name and `extracontains` (the power a Qi Focus must hold,
    for The Artisan's Way) the target, as `AddImprovementCollection` passes
    it."""
    kind = "FocusBindingKarmaCost" if node.tag == "focusbindingkarmacost" else "FocusBindingKarmaMultiplier"
    value = _text(node, "val")
    if not _text(node, "name") or not _is_int(value):
        return []
    return [_Imp(kind, _text(node, "name"), target=_text(node, "extracontains"), val=int(value))]


def _specialization_option(node: ET.Element, rating: int) -> list[_Imp]:
    """`addskillspecializationoption`: one SkillSpecializationOption for each
    skill it names, the skill as the improved name and the specialization as
    the unique (a martial art's style, Electroception's own)."""
    skills = [_text(skill) for skill in node.findall("./skills/skill")] or [_text(node, "skill")]
    spec = _text(node, "spec")
    return [_Imp("SkillSpecializationOption", skill, unique=spec) for skill in skills if skill and spec]


def _drain_or_fading(node: ET.Element, rating: int) -> list[_Imp]:
    """`drainvalue`, `fadingvalue`: a change to the drain or fading of every
    spell or form, or of the one its `specific` names."""
    kind = {"drainvalue": "DrainValue", "fadingvalue": "FadingValue"}[node.tag]
    return [_Imp(kind, node.get("specific") or "", val=int(_text(node)))] if _is_int(_text(node)) else []


def _dodge(node: ET.Element, rating: int) -> list[_Imp]:
    if not _is_int(_text(node)):
        return []
    unique = _precedence(node) or (f"group{node.get('group')}" if node.get("group") else "")
    return [_Imp("Dodge", unique=unique, val=int(_text(node)))]


def _initiativedice(node: ET.Element, rating: int) -> list[_Imp]:
    """`initiativedice` and `initiativepass` (the same): the tag name is the
    unique unless a precedence says otherwise."""
    if not _is_int(_text(node)):
        return []
    return [_Imp("InitiativeDice", unique=_precedence(node) or node.tag, val=int(_text(node)))]


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


def _attribute(node: ET.Element, name: str, unique: str = "") -> list[_Imp]:
    """An Attribute improvement from `<min>`, `<val>` (the aug), `<max>` and
    `<aug>` (the aug max), as `specificattribute` and `selectattributes`
    read them; `affectbase` aims it at the base. A `-natural` maximum
    depends on the metatype, so it is left out."""
    numbers = {field: _text(node, field) or "0" for field in ("min", "val", "max", "aug")}
    if not name or not all(_is_int(number) for number in numbers.values()):
        return []
    return [
        _Imp(
            "Attribute",
            name + ("Base" if node.find("affectbase") is not None else ""),
            unique=unique,
            min=int(numbers["min"]),
            max=int(numbers["max"]),
            aug=int(numbers["val"]),
            augmax=int(numbers["aug"]),
            condition=_text(node, "condition"),
        )
    ]


def _specificattribute(node: ET.Element, rating: int) -> list[_Imp]:
    named = node.find("name")
    precedence = node.get("precedence") or (named.get("precedence") if named is not None else None)
    return _attribute(node, _text(node, "name"), f"precedence{precedence}" if precedence else "")


def _selectattributes(node: ET.Element, attributes: list[str]) -> list[_Imp]:
    """One Attribute improvement per `<selectattribute>`, of the attribute
    picked for it (Exceptional Attribute's one, an Infected's four)."""
    rows = []
    for choice, picked in zip(node.findall("selectattribute"), attributes, strict=False):
        if picked in _SEEKER - {"BOX", "ESS"}:
            rows += _attribute(choice, picked)
    return rows


def _enableattribute(node: ET.Element, rating: int) -> list[_Imp]:
    name = _text(node, "name").upper()
    return [_Imp("Attribute", name, unique="enableattribute")] if name in ("MAG", "RES", "DEP") else []


def _addcontact(node: ET.Element, contact: str) -> list[_Imp]:
    """AddContact names the contact, which is its unique too; the forced
    loyalty, free and forced group flags each name it again."""
    rows = [_Imp("AddContact", contact, unique=contact)]
    if _is_int(_text(node, "forcedloyalty")):
        rows.append(_Imp("ContactForcedLoyalty", contact, val=int(_text(node, "forcedloyalty"))))
    if node.find("free") is not None:
        rows.append(_Imp("ContactMakeFree", contact))
    if node.find("forcegroup") is not None:
        rows.append(_Imp("ContactForceGroup", contact))
    return rows


def _skillattribute(node: ET.Element, rating: int) -> list[_Imp]:
    """Dice for every skill of an attribute (a Power Focus's MAG)."""
    if not _text(node, "name") or not _is_int(_text(node, "bonus")):
        return []
    named = node.find("name")
    precedence = node.get("precedence") or (named.get("precedence") if named is not None else None)
    return [
        _Imp(
            "SkillAttribute",
            _text(node, "name"),
            unique=f"precedence{precedence}" if precedence else "",
            val=int(_text(node, "bonus")),
            exclude=_text(node, "exclude"),
            addtorating=_text(node, "applytorating").lower() == "true",
            condition=_text(node, "condition"),
        )
    ]


def _spellcategory(node: ET.Element, rating: int) -> list[_Imp]:
    """`spellcategory` / `spellcategorydicepool`: dice for a spell category."""
    if not _is_int(_text(node, "val")):
        return []
    return [_Imp("SpellCategory", _text(node, "name"), val=int(_text(node, "val")), condition=_text(node, "condition"))]


def _spelldicepool(node: ET.Element, rating: int) -> list[_Imp]:
    if not _is_int(_text(node, "val")):
        return []
    return [_Imp("SpellDicePool", _text(node, "id") or _text(node, "name"), val=int(_text(node, "val")))]


def _specificpower(node: ET.Element, rating: int) -> list[_Imp]:
    """Free levels of an adept power, the levels as the rating — or points,
    with `pointsperlevel`. Chummer makes it for an adept only, which the
    caller checks."""
    levels = int(_text(node, "val")) if _is_int(_text(node, "val")) else 0
    kind = "AdeptPowerFreePoints" if _text(node, "pointsperlevel") else "AdeptPowerFreeLevels"
    return [_Imp(kind, _text(node, "name"), rating=levels)] if _text(node, "name") else []


def _prototypetranshuman(node: ET.Element, rating: int) -> list[_Imp]:
    return [_Imp("PrototypeTranshuman", _text(node))] if _text(node) else []


def _limitmodifier(node: ET.Element, rating: int) -> list[_Imp]:
    """A limit modifier row to write; `_with_rows` makes it and names it."""
    if not _is_int(_text(node, "value")):
        return []
    return [
        _Imp(
            "LimitModifier",
            target=_text(node, "limit"),
            val=int(_text(node, "value")),
            condition=_text(node, "condition"),
        )
    ]


def _addgear(node: ET.Element, rating: int) -> list[_Imp]:
    """A gear row to write; `_with_rows` makes it. Only gear with no children
    and none of this app's own (a Technomancer's Living Persona): a Dead SIN's
    Fake SIN would read back as bought gear."""
    if node.find("children") is not None:
        return []
    return [_Imp("Gear", _text(node, "name"), target=_text(node, "category"), rating=int(_text(node, "rating") or 0))]


def _own_gear_ids() -> set[str]:
    buckets = ("gear", "commlinks", "cyberdecks", "rccs", "sensors", "optics", "programs", "apps")
    return {str(row["id"]) for bucket in buckets for row in catalog_list(bucket)}


def _with_rows(root: ET.Element, rows: list[_Imp], guid: str, owner: str) -> list[_Imp]:
    """The rows a LimitModifier or Gear improvement names, written, and the
    improvements pointing at them by guid — `limitmodifier` and `addgear` make
    the row and the improvement together. The import reads neither back."""
    out = []
    for index, row in enumerate(rows):
        if row.kind == "LimitModifier":
            row_guid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{guid}:limitmodifier:{index}"))
            parent = root.find("limitmodifiers")
            el = _sub(parent if parent is not None else _sub(root, "limitmodifiers"), "limitmodifier")
            for key, value in (
                ("guid", row_guid),
                ("name", owner),
                ("limit", row.target),
                ("condition", row.condition),
            ):
                _sub(el, key, value)
            _sub(el, "bonus", row.val)
            out.append(_Imp("LimitModifier", row_guid, val=row.val, condition=row.condition))
        elif row.kind == "Gear":
            definition = next(
                (
                    gear
                    for gear in parse_data("gear.xml").findall("./gears/gear")
                    if gear.findtext("name") == row.improved and gear.findtext("category") == row.target
                ),
                None,
            )
            if definition is None or str(definition.findtext("id")) in _own_gear_ids():
                continue
            row_guid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{guid}:addgear:{index}"))
            parent = root.find("gears")
            el = _sub(parent if parent is not None else _sub(root, "gears"), "gear")
            _sub(el, "guid", row_guid)
            _sub(el, "sourceid", definition.findtext("id") or "")
            for field in definition:
                if field.tag not in ("id", "hide", "rating", "cost"):
                    el.append(deepcopy(field))
            _sub(el, "rating", row.rating)
            _sub(el, "qty", 1)
            _sub(el, "cost", 0)
            _sub(el, "parentid", guid)
            out.append(_Imp("Gear", row_guid))
        else:
            out.append(row)
    return out


_READERS: dict[str, Callable[[ET.Element, int], list[_Imp]]] = {
    "prototypetranshuman": _prototypetranshuman,
    "skillattribute": _skillattribute,
    "spellcategory": _spellcategory,
    "spellcategorydicepool": _spellcategory,
    "spelldicepool": _spelldicepool,
    "specificpower": _specificpower,
    "limitmodifier": _limitmodifier,
    "addgear": _addgear,
    "unlockskills": _unlockskills,
    "enabletab": _enabletab,
    **dict.fromkeys(_ARMORS, _armor),
    "disablebiowaregrade": _disablegrade,
    "disablecyberwaregrade": _disablegrade,
    "specificskill": _specificskill,
    **dict.fromkeys(_FLAGS, _flag),
    "physicallimit": _limit,
    "mentallimit": _limit,
    "smartlink": _smartlink,
    "focusbindingkarmacost": _focus_binding,
    "focusbindingkarmamultiplier": _focus_binding,
    "addskillspecializationoption": _specialization_option,
    "skilldisable": _named("SkillDisable"),
    "skillgroupdisable": _named("SkillGroupDisable"),
    "limitspellcategory": _named("LimitSpellCategory"),
    "drainvalue": _drain_or_fading,
    "fadingvalue": _drain_or_fading,
    "dodge": _dodge,
    "initiativedice": _initiativedice,
    "initiativepass": _initiativedice,
    "specificattribute": _specificattribute,
    "enableattribute": _enableattribute,
    "sociallimit": _limit,
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
    aug: int = 0
    augmax: int = 0


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


def _write_improvements(
    root: ET.Element, rows: list[_Imp], source_name: str, source: str, enabled: bool = True
) -> None:
    """`enabled` False: the owner is off (armor not worn), whose improvements
    Chummer keeps but disables."""
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
        _sub(imp, "aug", row.aug)
        _sub(imp, "augmax", row.augmax)
        _sub(imp, "val", row.val)
        _sub(imp, "rating", row.rating)
        _sub(imp, "exclude", row.exclude)
        _sub(imp, "condition", row.condition)
        _sub(imp, "improvementttype", row.kind)
        _sub(imp, "improvementsource", source)
        if row.addtorating:
            _sub(imp, "addtorating", "True")
        if not enabled:
            _sub(imp, "enabled", 0)
