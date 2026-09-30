"""Awakened / Emerged bonus nodes: adept powers, spell & spirit category limits, drain/fading, granted spells / echoes / metamagics / spirits, weapon-skill DV/accuracy slots.

One slice of the bonus-node table. Each handler claims its tags with
``@handles`` and is reached by lookup, not by falling down a chain.
"""

from __future__ import annotations

from typing import Any, cast

from ...data_loader import parse_select_power_slot
from .._common import (
    _as_int,
    _bonus_int,
)
from ..effect_rows import SelectPowerSlotRow
from ..effects import EffectsDict
from ._registry import handles


@handles("adeptpowerpoints")
def _adeptpowerpoints(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["adept_power_points"] += _bonus_int(node, fields)


@handles("magicianswaydiscount")
def _magicianswaydiscount(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["magicians_way"] = True


@handles("selectmentorspirit")
def _selectmentorspirit(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["needs_mentor"] = True


@handles("selectparagon")
def _selectparagon(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["needs_paragon"] = True


@handles("focusbindingkarmacost")
def _focusbindingkarmacost(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["focus_binding"].append(
        {
            "name": str(fields.get("name") or "").strip(),
            "val": _as_int(fields.get("val") or fields.get("value")),
            "extracontains": str(fields.get("extracontains") or "").strip(),
            "source": source,
        }
    )


@handles("spellcategory")
def _spellcategory(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    name = (fields.get("name") or node.get("value") or "").strip()
    bonus = _as_int(fields.get("bonus") or fields.get("val") or fields.get("value"))
    if not name or bonus == 0:
        return
    effects["spell_category_mods"].append(
        {
            "name": name,
            "bonus": bonus,
            "condition": (fields.get("condition") or "").strip(),
            "source": source,
        }
    )


@handles("spelldicepool")
def _spelldicepool(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    name = (fields.get("name") or fields.get("id") or node.get("value") or "").strip()
    bonus = _as_int(fields.get("val") or fields.get("bonus") or fields.get("value") or node.get("value"))
    if bonus == 0:
        return
    effects["spell_dice_pool"].append(
        {
            "name": name,
            "id": str(fields.get("id") or "").strip(),
            "bonus": bonus,
            "source": source,
        }
    )


@handles("limitspellcategory")
def _limitspellcategory(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    attrs = node.get("attrs") or {}
    effects["limit_spell_category_slots"].append(
        {
            "source": source,
            "value": str(node.get("value") or fields.get("category") or "").strip(),
            "exclude": str(attrs.get("exclude") or "").strip(),
        }
    )


@handles("limitspiritcategory")
def _limitspiritcategory(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    raw = fields.get("spirit")
    if raw is None:
        text = str(node.get("value") or "").strip()
        spirits = [text] if text else []
    elif isinstance(raw, list):
        spirits = [str(item).strip() for item in raw if str(item).strip()]
    else:
        text = str(raw).strip()
        spirits = [text] if text else []
    effects["limit_spirit_category_slots"].append({"source": source, "spirits": spirits})


@handles("allowspellcategory")
def _allowspellcategory(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    name = str(node.get("value") or fields.get("category") or "").strip()
    if name and name not in effects["allow_spell_categories"]:
        effects["allow_spell_categories"].append(name)


@handles("allowspellrange")
def _allowspellrange(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    name = str(node.get("value") or fields.get("range") or "").strip()
    if name and name not in effects["allow_spell_ranges"]:
        effects["allow_spell_ranges"].append(name)


@handles("blockspelldescriptor")
def _blockspelldescriptor(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    name = str(node.get("value") or fields.get("name") or "").strip()
    if name and name not in effects["block_spell_descriptors"]:
        effects["block_spell_descriptors"].append(name)


@handles("spellcategorydrain")
def _spellcategorydrain(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["spell_category_drain"].append(
        {
            "source": source,
            "category": str(fields.get("category") or node.get("value") or "").strip(),
            "value": _as_int(fields.get("val") or fields.get("bonus") or fields.get("value")),
        }
    )


@handles("spellcategorydamage")
def _spellcategorydamage(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["spell_category_damage"].append(
        {
            "source": source,
            "category": str(fields.get("category") or node.get("value") or "").strip(),
            "value": _as_int(fields.get("val") or fields.get("bonus") or fields.get("value")),
        }
    )


@handles("spelldescriptordrain")
def _spelldescriptordrain(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["spell_descriptor_drain"].append(
        {
            "source": source,
            "descriptor": str(fields.get("descriptor") or node.get("value") or "").strip(),
            "value": _as_int(fields.get("val") or fields.get("bonus") or fields.get("value")),
        }
    )


@handles("spelldescriptordamage")
def _spelldescriptordamage(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["spell_descriptor_damage"].append(
        {
            "source": source,
            "descriptor": str(fields.get("descriptor") or node.get("value") or "").strip(),
            "value": _as_int(fields.get("val") or fields.get("bonus") or fields.get("value")),
        }
    )


@handles("drainvalue")
def _drainvalue(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["drain_value"] += _bonus_int(node, fields)


@handles("fadingvalue")
def _fadingvalue(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    attrs = node.get("attrs") or {}
    specific = str(attrs.get("specific") or "").strip()
    value = _bonus_int(node, fields)
    if specific:
        effects["fading_value_specific"].append({"specific": specific, "value": value})
    else:
        effects["fading_value"] += value


@handles("fadingresist")
def _fadingresist(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["fading_resist"] += _bonus_int(node, fields)


@handles("drainresist")
def _drainresist(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["drain_resist"] += _bonus_int(node, fields)


@handles("addecho")
def _addecho(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    name = str(node.get("value") or fields.get("name") or "").strip()
    if name:
        effects["grant_echoes"].append({"source": source, "name": name})


@handles("cyberadeptdaemon")
def _cyberadeptdaemon(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["cyberadept_daemon"] = True


@handles("quickeningmetamagic")
def _quickeningmetamagic(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["quickening"] = True


@handles("addspell")
def _addspell(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    attrs = node.get("attrs") or {}
    name = str(node.get("value") or fields.get("name") or "").strip()
    if name:
        effects["grant_spells"].append(
            {
                "source": source,
                "name": name,
                "alchemical": str(attrs.get("alchemical") or "").lower() == "true",
                "extended": str(attrs.get("extended") or "").lower() == "true",
                "limited": str(attrs.get("limited") or "").lower() == "true",
            }
        )


@handles("specificpower")
def _specificpower(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    name = str(node.get("value") or fields.get("name") or "").strip()
    if name:
        effects["grant_powers"].append(
            {
                "source": source,
                "name": name,
                "rating": max(1, _bonus_int(node, fields)),
                "extra": "",
            }
        )


@handles("selectpowers")
def _selectpowers(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    slot = parse_select_power_slot(node)
    if slot.get("needs_select"):
        # parse_select_power_slot returns exactly SelectPowerSlotRow's
        # keys bar ``source``; ``**`` into a TypedDict literal isn't
        # checkable, so cast the merged row.
        effects["select_power_slots"].append(cast(SelectPowerSlotRow, {"source": source, **slot}))


@handles("addspirit")
def _addspirit(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    attrs = node.get("attrs") or {}
    skill = str(attrs.get("skill") or "").strip()
    add_to_selected = str(fields.get("addtoselected") or "True").lower() != "false"
    effects["add_spirit_slots"].append(
        {
            "source": source,
            "skill": skill,
            "rating_divisor": max(1, _as_int(attrs.get("ratingdivisor"), 1)),
            "add_to_selected": add_to_selected,
            "allowed": [
                str(name).strip() for name in ((node.get("nested") or {}).get("spirit") or []) if str(name).strip()
            ],
        }
    )


@handles("addmetamagic")
def _addmetamagic(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    name = str(node.get("value") or "").strip()
    if name:
        effects["free_metamagics"].append(
            {
                "name": name,
                "source": source,
                "forced": str((node.get("attrs") or {}).get("forced") or "").lower() == "true",
            }
        )


@handles("metamagiclimit")
def _metamagiclimit(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    for row in node.get("metamagic_grades") or []:
        name = str(row.get("name") or "").strip()
        grade = _as_int(row.get("grade"))
        if name and grade > 0:
            effects["metamagic_limits"].append({"grade": grade, "name": name, "source": source})


@handles("freespells")
def _freespells(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    attrs = node.get("attrs") or {}
    limit = str(attrs.get("limit") or "").strip()
    skill = str(attrs.get("skill") or "").strip()
    attribute = str(attrs.get("attribute") or "").strip().upper()
    if skill:
        effects["free_spells_skill"].append({"skill": skill, "limit": limit, "source": source})
    elif attribute:
        effects["free_spells_attribute"].append({"attribute": attribute, "limit": limit, "source": source})
    else:
        effects["free_spells_flat"] += _bonus_int(node, fields)


@handles("newspellkarmacost")
def _newspellkarmacost(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    attrs = node.get("attrs") or {}
    effects["new_spell_karma_cost"].append(
        {
            "type": str(attrs.get("type") or "").strip(),
            "value": _bonus_int(node, fields),
            "condition": str(attrs.get("condition") or "").strip(),
            "source": source,
        }
    )


@handles("burnoutsway")
def _burnoutsway(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["burnout_way"] = True


@handles("weaponcategorydice")
def _weaponcategorydice(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    raw = (node.get("nested") or {}).get("category") or []
    for idx in range(0, len(raw) - 1, 2):
        name = str(raw[idx]).strip()
        dice = _as_int(raw[idx + 1])
        if name and dice:
            effects["weapon_category_dice"].append({"category": name, "dice": dice, "source": source})
    if not raw:
        name = str(fields.get("name") or "").strip()
        dice = _as_int(fields.get("bonus") or fields.get("value") or fields.get("val"))
        if name and dice:
            effects["weapon_category_dice"].append({"category": name, "dice": dice, "source": source})


@handles("weaponcategorydv")
def _weaponcategorydv(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    select_attrs = (node.get("field_attrs") or {}).get("selectskill") or {}
    limit_raw = str(select_attrs.get("limittoskill") or "").strip()
    skills = [part.strip() for part in limit_raw.split(",") if part.strip()]
    fixed = str(fields.get("name") or "").strip()
    effects["weapon_category_dv_slots"].append(
        {
            "source": source,
            "skills": skills,
            "name": fixed,
            "bonus": _as_int(fields.get("bonus") or fields.get("val") or fields.get("value")),
            "needs_select": bool(skills) or "selectskill" in (node.get("fields") or {}),
        }
    )


@handles("weaponaccuracy")
def _weaponaccuracy(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    target = str(fields.get("name") or "").strip()
    bonus = _as_int(fields.get("value") or fields.get("val") or fields.get("bonus"))
    if target and bonus:
        effects["weapon_accuracy"].append({"name": target, "bonus": bonus, "source": source})


@handles("weaponskillaccuracy")
def _weaponskillaccuracy(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    select_attrs = dict((node.get("field_attrs") or {}).get("selectskill") or {})
    fixed = str(fields.get("name") or "").strip()
    effects["weapon_skill_accuracy_slots"].append(
        {
            "source": source,
            "name": fixed,
            "bonus": _as_int(fields.get("value") or fields.get("val") or fields.get("bonus")),
            "select_attrs": select_attrs,
            "needs_select": bool(select_attrs) or "selectskill" in (node.get("fields") or {}) or not fixed,
        }
    )


@handles("selectlimit")
def _selectlimit(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    # An adept power that moves a limit the character picks. The node is found
    # again by `engine/magic/powers.py` once the pick is known, so folding
    # anything in from here would apply it to whichever limit was printed.
    pass
