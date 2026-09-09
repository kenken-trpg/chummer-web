"""Attribute / limit / initiative / armor / condition-monitor / movement / unarmed / special-armor bonus nodes.

One slice of the pre-split ``apply_bonus_nodes`` chain. ``apply`` returns
True iff ``tag`` is one of ours.
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


def apply(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> bool:
    if tag == "specificattribute":
        name = ATTR_ALIASES.get((fields.get("name") or "").upper())
        if name:
            bonus = _as_int(fields.get("bonus") or fields.get("val") or fields.get("value"), 0)
            if bonus:
                effects["attribute_bonus"][name] = effects["attribute_bonus"].get(name, 0) + bonus
            if fields.get("max") not in (None, ""):
                effects["attribute_max_mods"][name] = int(effects["attribute_max_mods"].get(name) or 0) + _as_int(
                    fields.get("max")
                )
    elif tag == "attributekarmacost":
        # The skill-side `<karmacost>` rules already shape a per-level cost in
        # `engine/karma.py`; an attribute rule is the same row read by the
        # attribute loops, so it rides the same `KarmaCostRow` shape.
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
    elif tag == "armor":
        effects["armor"] += _as_int(node.get("value"))
    elif tag == "conditionmonitor":
        effects["cm_physical"] += _as_int(fields.get("physical"))
        effects["cm_stun"] += _as_int(fields.get("stun"))
        # `<threshold>` moves the every-third-box penalty step, `<thresholdoffset>`
        # ignores that many boxes before the first penalty (High Pain Tolerance).
        effects["cm_threshold"] += _as_int(fields.get("threshold"))
        effects["cm_threshold_offset"] += _as_int(fields.get("thresholdoffset"))
    elif tag == "drugpositiveattributemodifier":
        effects["drug_positive_attribute"] += _bonus_int(node, fields)
    elif tag == "reflexrecorderoptimization":
        effects["reflex_recorder_optimization"] = True
    elif tag == "addlimb":
        # A pair of Shiva arms is two more limbs to average a cyberlimb's
        # STR/AGI over (SR5 p.456), so the body grows a slot, not a number.
        slot = str(fields.get("limbslot") or "").strip().lower()
        count = _as_int(fields.get("val") or fields.get("value") or node.get("value"))
        if slot and count > 0:
            effects["extra_limbs"][slot] = int(effects["extra_limbs"].get(slot) or 0) + count
    elif tag == "replaceattributes":
        # An Infected character keeps none of their metatype's ranges for the
        # attributes listed (RF p.136); Quadriplegic zeroes three of them.
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
    elif tag == "initiative":
        effects["initiative"] += _bonus_int(node, fields)
    elif tag == "initiativepass":
        effects["initiative_dice"] += _bonus_int(node, fields)
    elif tag == "enabletab":
        names = fields.get("name") or node.get("value") or ""
        values = names if isinstance(names, list) else [names]
        for raw in values:
            text = str(raw).strip()
            name = text.upper() if text.upper() in {"MAG", "RES"} else text.lower()
            if name:
                effects["enabled_tabs"].add(name)
    elif tag == "enableattribute":
        names = fields.get("name") or node.get("value") or ""
        values = names if isinstance(names, list) else [names]
        for raw in values:
            attr = ATTR_ALIASES.get(str(raw).strip().upper())
            if attr in {"MAG", "RES"}:
                effects["enabled_tabs"].add(attr)
            elif attr:
                effects["enabled_tabs"].add(attr.lower())
    elif tag == "mentallimit":
        effects["limit_mental"] += _bonus_int(node, fields)
    elif tag == "sociallimit":
        effects["limit_social"] += _bonus_int(node, fields)
    elif tag == "physicallimit":
        effects["limit_physical"] += _bonus_int(node, fields)
    elif tag == "damageresistance":
        effects["damage_resistance"] += _bonus_int(node, fields)
    elif tag == "unarmeddv":
        effects["unarmed_dv"] += _bonus_int(node, fields)
    elif tag == "unarmeddvphysical":
        effects["unarmed_physical"] = True
    elif tag == "naturalweapon":
        # A Shapeshifter's bite and claws (RF p.104). No `weapons.xml` entry
        # backs these, so the node's own fields *are* the weapon row; the gear
        # phase turns them into rows the sheet renders like any other melee
        # weapon. `source`/`page` are the rulebook the attack is from, hence
        # `weapon_source` — the row's `source` is the metatype that grants it.
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
    elif tag == "unarmedreach":
        effects["unarmed_reach"] += _bonus_int(node, fields)
    elif tag == "unarmedap":
        effects["unarmed_ap"] += _bonus_int(node, fields)
    elif tag == "spellresistance":
        effects["spell_resistance"] += _bonus_int(node, fields)
    elif tag in SPELL_DEFENSE_RESIST_TAGS:
        key = SPELL_DEFENSE_RESIST_TAGS[tag]
        effects["spell_defense_resist"][key] += _bonus_int(node, fields)
    elif tag in SPECIAL_ARMOR_TAGS:
        key = SPECIAL_ARMOR_TAGS[tag]
        effects["special_armor"][key] += _bonus_int(node, fields)
    elif tag == "adapsin":
        # Claimed so it stops showing up as an unimplemented bonus; the work
        # happens in `engine/ware/resolve.py`, which has to know about Adapsin
        # before the effects dict exists (see `has_adapsin`).
        pass
    elif tag in IMMUNE_TAGS:
        effects["immunities"][IMMUNE_TAGS[tag]] = True
    elif tag == "restrictedgear":
        effects["restricted_gear"].append(
            {
                "availability": max(0, _as_int(fields.get("availability") or 24, 24)),
                "amount": max(1, _as_int(fields.get("amount") or 1, 1)),
                "source": source,
            }
        )
    elif tag == "limitmodifier":
        kind = _limit_kind(fields.get("limit") or node.get("value"))
        value = _as_int(fields.get("value") or node.get("value"))
        condition = _as_text(fields.get("condition") or "").strip()
        if not kind or value == 0:
            return True
        effects["limit_modifiers"].append(
            {
                "limit": kind,
                "value": value,
                "condition": condition,
                "condition_label": limit_condition_label(condition),
                "source": source,
            }
        )
    elif tag == "reach":
        effects["reach"] += _bonus_int(node, fields)
    elif tag == "smartlink":
        # Accuracy value of a usable smartlink: 2 (implant), 1 (imaging device).
        # A smartgun system's Accuracy is gated on this being > 0; keep the best.
        effects["smartlink"] = max(
            int(effects.get("smartlink") or 0),
            _bonus_int(node, fields, default=2),
        )
    elif tag == "throwstr":
        # STR added when the client resolves a thrown weapon's {STR} damage.
        effects["throw_str"] += _bonus_int(node, fields)
    elif tag == "throwrangestr":
        # STR added when the client resolves thrown-weapon range bands
        # (Precision Throwing's value is "Rating*2" after substitute_rating).
        effects["throw_range_str"] += _bonus_int(node, fields)
    elif tag in TEST_MOD_TAGS:
        key = TEST_MOD_TAGS[tag]
        effects["test_mods"][key] = int(effects["test_mods"].get(key) or 0) + _bonus_int(node, fields)
    elif tag == "selectattributes":
        nested = node.get("nested") or {}
        vals = nested.get("selectattribute") or []
        if not isinstance(vals, list):
            vals = [vals]
        exclude: list[str] = []
        max_bonus = 1
        for raw in vals:
            text = str(raw).strip()
            attr = ATTR_ALIASES.get(text.upper())
            if attr:
                exclude.append(attr)
            elif text:
                max_bonus = _as_int(text, max_bonus)
        # Also accept structured fields if present.
        for key in ("excludeattribute", "exclude"):
            raw_ex = fields.get(key)
            if not raw_ex:
                continue
            items = raw_ex if isinstance(raw_ex, list) else [raw_ex]
            for item in items:
                attr = ATTR_ALIASES.get(str(item).strip().upper())
                if attr and attr not in exclude:
                    exclude.append(attr)
        if fields.get("max"):
            max_bonus = _as_int(fields.get("max"), max_bonus)
        effects["attribute_selects"].append(
            {
                "exclude": exclude,
                "max": max(1, max_bonus),
                "source": source,
            }
        )
    elif tag == "physicalcmrecovery":
        effects["cm_recovery_physical"] += _bonus_int(node, fields)
    elif tag == "stuncmrecovery":
        effects["cm_recovery_stun"] += _bonus_int(node, fields)
    elif tag == "addesstophysicalcmrecovery":
        effects["cm_recovery_physical_add_ess"] = True
    elif tag == "addesstostuncmrecovery":
        effects["cm_recovery_stun_add_ess"] = True
    elif tag == "walkmultiplier":
        category = str(fields.get("category") or "Ground").strip() or "Ground"
        effects["walk_multiplier"][category] = int(effects["walk_multiplier"].get(category) or 0) + _as_int(
            fields.get("val") or fields.get("bonus") or node.get("value")
        )
    elif tag == "runmultiplier":
        category = str(fields.get("category") or "Ground").strip() or "Ground"
        effects["run_multiplier"][category] = int(effects["run_multiplier"].get(category) or 0) + _as_int(
            fields.get("val") or fields.get("bonus") or node.get("value")
        )
    elif tag == "movementreplace":
        category = str(fields.get("category") or "Ground").strip() or "Ground"
        speed = str(fields.get("speed") or "walk").strip().lower() or "walk"
        effects["movement_replace"][(category, speed)] = _as_int(
            fields.get("val") or fields.get("bonus") or node.get("value")
        )
    elif tag == "sprintbonus":
        category = str(fields.get("category") or "Ground").strip() or "Ground"
        effects["sprint_bonus"][category] = int(effects["sprint_bonus"].get(category) or 0) + _as_int(
            fields.get("val") or fields.get("bonus") or node.get("value")
        )
    elif tag == "fatigueresist":
        effects["fatigue_resist"] += _bonus_int(node, fields)
    elif tag == "livingpersona":
        persona = effects.setdefault(
            "living_persona",
            {"attack": 0, "sleaze": 0, "dataprocessing": 0, "firewall": 0},
        )
        for key in ("attack", "sleaze", "dataprocessing", "firewall"):
            persona[key] = int(persona.get(key) or 0) + _as_int(fields.get(key))
    elif tag in ("matrixinitiativediceadd", "matrixinitiativedice"):
        # Chummer keeps a "set" and an "add" flavour apart; every
        # `matrixinitiativedice` in the data is a +1 module, so both add here.
        effects["matrix_initiative_dice"] = int(effects.get("matrix_initiative_dice") or 0) + _bonus_int(node, fields)
    elif tag == "actiondicepool":
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
    else:
        return False
    return True
