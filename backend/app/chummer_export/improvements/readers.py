"""What each tag makes, one function per `AddImprovementCollection` method.

Most take the tag and the owner's rating and are found through `_READERS`;
the few that need a pick (`_selectskill`, `_spirit_pick`, `_attribute`,
`_selectattributes`, `_addcontact`, `_cost`, `_weapon_category`) are called by `_bonus_improvements`
with it."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Callable

from ._imp import _Imp, _is_int, _precedence, _text
from .tables import _ARMORS, _COSTS, _FLAGS, _PERSONA, _SEEKER, _TABS, _WEAPON_CATEGORY


def _cost(node: ET.Element) -> list[_Imp]:
    kind, named = _COSTS[node.tag]
    numbers = [_text(node, field) or "0" for field in ("val", "min", "max")]
    if not all(_is_int(number) for number in numbers):
        return []
    val, low, high = (int(number) for number in numbers)
    return [
        _Imp(kind, _text(node, "name") if named else "", val=val, min=low, max=high, condition=_text(node, "condition"))
    ]


def _weapon_category(node: ET.Element, pick: str | None) -> list[_Imp]:
    """`CreateWeaponCategoryImprovement`: the category is the owner's pick
    when the tag asks for a skill or a category (Critical Strike, Death
    Dealer), else its `<name>` (Master Archer's Bows). The value is
    `<bonus>`, except that a `<selectcategory>` reads its own `<value>` — which
    Critical Strike's has none of, so Chummer today makes it 0 where its
    saves (and the rule, and this app's sheet) have the `<bonus>` of 1; the
    export keeps the `<bonus>` when there is no `<value>`."""
    select = node.find("selectcategory")
    if node.find("selectskill") is not None or select is not None:
        name = pick or ""
    else:
        name = _text(node, "name")
    value = (_text(select, "value") if select is not None else "") or _text(node, "bonus")
    return [_Imp(_WEAPON_CATEGORY[node.tag], name, val=int(value))] if name and _is_int(value) else []


def _unlockskills(node: ET.Element, rating: int) -> list[_Imp]:
    return [_Imp("SpecialSkills", _text(node), target=node.get("name") or "")] if _text(node) else []


def _enabletab(node: ET.Element, rating: int) -> list[_Imp]:
    tabs = (_TABS.get(_text(name).upper()) for name in node.findall("name"))
    return [_Imp("SpecialTab", tab, unique="enabletab") for tab in tabs if tab]


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


def _skilllinkedattribute(node: ET.Element, rating: int) -> list[_Imp]:
    """`skilllinkedattribute`: every skill linked to the attribute it names
    (Neural Amplifiers, PuSHed, Qualia), with the `applytorating`, `exclude`
    and `condition` `specificskill`'s `Skill` does not need, and a
    `precedence` on the tag or its name as the unique."""
    amount = _text(node, "bonus")
    if not _text(node, "name") or not _is_int(amount):
        return []
    name = node.find("name")
    precedence = node.get("precedence") or (name.get("precedence") if name is not None else None)
    return [
        _Imp(
            "SkillLinkedAttribute",
            _text(node, "name"),
            unique=f"precedence{precedence}" if precedence else "",
            val=int(amount),
            exclude=_text(node, "exclude"),
            addtorating=_text(node, "applytorating").lower() == "true",
            condition=_text(node, "condition"),
        )
    ]


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
    "skilllinkedattribute": _skilllinkedattribute,
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
