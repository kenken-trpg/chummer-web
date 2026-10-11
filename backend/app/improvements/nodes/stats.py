"""Attribute / limit / initiative / armor / condition-monitor / movement / unarmed / special-armor bonus nodes.

One slice of the bonus-node table. Each handler claims its tags with
``@handles`` and is reached by lookup, not by falling down a chain.
"""

from __future__ import annotations

from typing import Any

from .._common import (
    ATTR_ALIASES,
    IMMUNE_TAGS,
    SPECIAL_ARMOR_TAGS,
    SPELL_DEFENSE_RESIST_TAGS,
    TEST_MOD_TAGS,
    _as_int,
    _as_text,
    _bonus_int,
    _limit_kind,
    limit_condition_label,
)
from ..effects import EffectsDict
from ._registry import handles


def _by_precedence(effects: EffectsDict, node: dict[str, Any], key: str, value: int) -> bool:
    """Park a ``precedence``-tagged bonus for :func:`resolve_precedence`
    instead of adding it; False (add it as usual) when it carries none."""
    precedence = (node.get("attrs") or {}).get("precedence")
    if precedence is None or not value:
        return False
    effects["precedence_bonus"].setdefault(key, {}).setdefault(str(precedence).strip(), []).append(int(value))
    return True


@handles("specificattribute")
def _specificattribute(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    name = ATTR_ALIASES.get((fields.get("name") or "").upper())
    if name:
        bonus = _as_int(fields.get("bonus") or fields.get("val") or fields.get("value"), 0)
        if bonus and not _by_precedence(effects, node, f"attr:{name}", bonus):
            effects["attribute_bonus"][name] = effects["attribute_bonus"].get(name, 0) + bonus
        if fields.get("max") not in (None, ""):
            effects["attribute_max_mods"][name] = int(effects["attribute_max_mods"].get(name) or 0) + _as_int(
                fields.get("max")
            )


@handles("attributemaxclamp")
def _attributemaxclamp(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    name = ATTR_ALIASES.get(_as_text(node.get("value") or fields.get("name")).upper())
    if name and name not in effects["attribute_max_clamp"]:
        effects["attribute_max_clamp"].append(name)


@handles("attributekarmacost")
def _attributekarmacost(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    name = ATTR_ALIASES.get((fields.get("name") or "").upper()) or ""
    if name:
        effects["attribute_karma_cost"].append(
            {
                "name": name,
                "val": _as_int(fields.get("val") or fields.get("value")),
                "min": _as_int(fields.get("min")),
                "max": _as_int(fields.get("max")) if fields.get("max") not in (None, "") else None,
                "condition": str(fields.get("condition") or ""),
            }
        )


@handles("armor")
def _armor(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["armor"] += _as_int(node.get("value"))


@handles("conditionmonitor")
def _conditionmonitor(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["cm_physical"] += _as_int(fields.get("physical"))
    effects["cm_stun"] += _as_int(fields.get("stun"))
    # `<threshold>` moves the every-third-box penalty step, `<thresholdoffset>`
    # ignores that many boxes before the first penalty (High Pain Tolerance).
    effects["cm_threshold"] += _as_int(fields.get("threshold"))
    effects["cm_threshold_offset"] += _as_int(fields.get("thresholdoffset"))


@handles("drugpositiveattributemodifier")
def _drugpositiveattributemodifier(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    category = str((node.get("attrs") or {}).get("category") or "")
    modifiers = effects["drug_positive_attribute"]
    modifiers[category] = modifiers.get(category, 0) + _bonus_int(node, fields)


@handles("reflexrecorderoptimization")
def _reflexrecorderoptimization(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["reflex_recorder_optimization"] = True


@handles("addlimb")
def _addlimb(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    slot = str(fields.get("limbslot") or "").strip().lower()
    count = _as_int(fields.get("val") or fields.get("value") or node.get("value"))
    if slot and count > 0:
        effects["extra_limbs"][slot] = int(effects["extra_limbs"].get(slot) or 0) + count


@handles("replaceattributes")
def _replaceattributes(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    for row in node.get("attribute_ranges") or []:
        name = ATTR_ALIASES.get(str(row.get("name") or "").strip().upper())
        if not name:
            continue
        effects["attribute_replacements"][name] = {
            "min": _as_int(row.get("min")),
            "max": _as_int(row.get("max")),
            "aug": _as_int(row.get("aug")),
            "source": source,
        }


@handles("initiative")
def _initiative(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    value = _bonus_int(node, fields)
    if not _by_precedence(effects, node, "initiative", value):
        effects["initiative"] += value


@handles("initiativepass")
def _initiativepass(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    value = _bonus_int(node, fields)
    if not _by_precedence(effects, node, "initiative_dice", value):
        effects["initiative_dice"] += value


@handles("enabletab")
def _enabletab(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    names = fields.get("name") or node.get("value") or ""
    values = names if isinstance(names, list) else [names]
    for raw in values:
        text = str(raw).strip()
        name = text.upper() if text.upper() in {"MAG", "RES"} else text.lower()
        if name:
            effects["enabled_tabs"].add(name)


@handles("enableattribute")
def _enableattribute(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    names = fields.get("name") or node.get("value") or ""
    values = names if isinstance(names, list) else [names]
    for raw in values:
        attr = ATTR_ALIASES.get(str(raw).strip().upper())
        if attr in {"MAG", "RES"}:
            effects["enabled_tabs"].add(attr)
        elif attr:
            effects["enabled_tabs"].add(attr.lower())


@handles("mentallimit")
def _mentallimit(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["limit_mental"] += _bonus_int(node, fields)


@handles("sociallimit")
def _sociallimit(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["limit_social"] += _bonus_int(node, fields)


@handles("physicallimit")
def _physicallimit(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["limit_physical"] += _bonus_int(node, fields)


@handles("damageresistance")
def _damageresistance(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["damage_resistance"] += _bonus_int(node, fields)


@handles("unarmeddv")
def _unarmeddv(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["unarmed_dv"] += _bonus_int(node, fields)


@handles("unarmeddvphysical")
def _unarmeddvphysical(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["unarmed_physical"] = True


@handles("naturalweapon")
def _naturalweapon(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    name = _as_text(fields.get("name"))
    if name:
        effects["natural_weapons"].append(
            {
                "source": source,
                "name": name,
                "damage": _as_text(fields.get("damage")),
                "ap": _as_text(fields.get("ap")),
                "reach": _as_text(fields.get("reach")),
                "useskill": _as_text(fields.get("useskill")),
                "accuracy": _as_text(fields.get("accuracy")),
                "weapon_source": _as_text(fields.get("source")),
                "page": _as_text(fields.get("page")),
            }
        )


@handles("unarmedreach")
def _unarmedreach(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["unarmed_reach"] += _bonus_int(node, fields)


@handles("unarmedap")
def _unarmedap(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["unarmed_ap"] += _bonus_int(node, fields)


@handles("spellresistance")
def _spellresistance(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["spell_resistance"] += _bonus_int(node, fields)


@handles(*SPELL_DEFENSE_RESIST_TAGS)
def _spell_defense_resist(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    key = SPELL_DEFENSE_RESIST_TAGS[tag]
    effects["spell_defense_resist"][key] += _bonus_int(node, fields)


@handles(*SPECIAL_ARMOR_TAGS)
def _special_armor(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    key = SPECIAL_ARMOR_TAGS[tag]
    effects["special_armor"][key] += _bonus_int(node, fields)


@handles("adapsin")
def _adapsin(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    pass


@handles(*IMMUNE_TAGS)
def _immune(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["immunities"][IMMUNE_TAGS[tag]] = True


@handles("restrictedgear")
def _restrictedgear(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["restricted_gear"].append(
        {
            "availability": max(0, _as_int(fields.get("availability") or 24, 24)),
            "amount": max(1, _as_int(fields.get("amount") or 1, 1)),
            "source": source,
        }
    )


@handles("limitmodifier")
def _limitmodifier(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    kind = _limit_kind(fields.get("limit") or node.get("value"))
    value = _as_int(fields.get("value") or node.get("value"))
    condition = _as_text(fields.get("condition") or "").strip()
    if not kind or value == 0:
        return
    effects["limit_modifiers"].append(
        {
            "limit": kind,
            "value": value,
            "condition": condition,
            "condition_label": limit_condition_label(condition),
            "source": source,
        }
    )


@handles("reach")
def _reach(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["reach"] += _bonus_int(node, fields)


@handles("smartlink")
def _smartlink(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["smartlink"] = max(
        int(effects.get("smartlink") or 0),
        _bonus_int(node, fields, default=2),
    )


@handles("throwstr")
def _throwstr(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["throw_str"] += _bonus_int(node, fields)


@handles("throwrangestr")
def _throwrangestr(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["throw_range_str"] += _bonus_int(node, fields)


@handles(*TEST_MOD_TAGS)
def _test_mod(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    key = TEST_MOD_TAGS[tag]
    effects["test_mods"][key] = int(effects["test_mods"].get(key) or 0) + _bonus_int(node, fields)


@handles("selectattributes")
def _selectattributes(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    for index, choice in enumerate(node.get("attribute_choices") or []):
        effects["attribute_selects"].append(
            {
                "exclude": list(choice.get("exclude") or []),
                "options": list(choice.get("options") or []),
                "val": _as_int(choice.get("val")),
                "max": _as_int(choice.get("max")),
                "index": index,
                "source": source,
            }
        )


@handles("physicalcmrecovery")
def _physicalcmrecovery(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["cm_recovery_physical"] += _bonus_int(node, fields)


@handles("stuncmrecovery")
def _stuncmrecovery(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["cm_recovery_stun"] += _bonus_int(node, fields)


@handles("addesstophysicalcmrecovery")
def _addesstophysicalcmrecovery(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["cm_recovery_physical_add_ess"] = True


@handles("addesstostuncmrecovery")
def _addesstostuncmrecovery(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["cm_recovery_stun_add_ess"] = True


@handles("walkmultiplier", "runmultiplier", "sprintbonus")
def _walkmultiplier(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    category = str(fields.get("category") or "Ground").strip() or "Ground"
    key = {"walkmultiplier": "walk_multiplier", "runmultiplier": "run_multiplier", "sprintbonus": "sprint_bonus"}[tag]
    if fields.get("percent") not in (None, ""):
        bucket = effects[f"{key}_percent"]  # type: ignore[literal-required]
        bucket[category] = int(bucket.get(category) or 0) + _as_int(fields.get("percent"))
    else:
        bucket = effects[key]  # type: ignore[literal-required]
        bucket[category] = int(bucket.get(category) or 0) + _as_int(
            fields.get("val") or fields.get("bonus") or node.get("value")
        )


@handles("movementreplace")
def _movementreplace(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    category = str(fields.get("category") or "Ground").strip() or "Ground"
    speed = str(fields.get("speed") or "walk").strip().lower() or "walk"
    effects["movement_replace"][(category, speed)] = _as_int(
        fields.get("val") or fields.get("bonus") or node.get("value")
    )


@handles("fatigueresist")
def _fatigueresist(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["fatigue_resist"] += _bonus_int(node, fields)


@handles("livingpersona")
def _livingpersona(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    persona = effects.setdefault(
        "living_persona",
        {"attack": 0, "sleaze": 0, "dataprocessing": 0, "firewall": 0},
    )
    for key in ("attack", "sleaze", "dataprocessing", "firewall"):
        persona[key] = int(persona.get(key) or 0) + _as_int(fields.get(key))


@handles("matrixinitiative")
def _matrixinitiative(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["matrix_initiative"] = int(effects.get("matrix_initiative") or 0) + _bonus_int(node, fields)


@handles("matrixinitiativediceadd", "matrixinitiativedice")
def _matrixinitiativediceadd(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["matrix_initiative_dice"] = int(effects.get("matrix_initiative_dice") or 0) + _bonus_int(node, fields)


@handles("actiondicepool")
def _actiondicepool(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    attrs = node.get("attrs") or {}
    category = str(attrs.get("category") or fields.get("category") or "").strip()
    name = str(fields.get("name") or "").strip()
    # Codeslinger XML has empty value; SR5 grants +2 to a chosen Matrix action.
    bonus = _bonus_int(node, fields)
    if bonus == 0:
        bonus = 2
    effects["action_dice_pools"].append(
        {
            "category": category,
            "name": name,
            "bonus": bonus,
            "source": source,
            "needs_action": not bool(name),
        }
    )
