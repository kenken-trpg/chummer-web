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


def apply(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: dict[str, Any], source: str) -> bool:
    for _once in (True,):
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
        elif tag == "armor":
            effects["armor"] += _as_int(node.get("value"))
        elif tag == "conditionmonitor":
            effects["cm_physical"] += _as_int(fields.get("physical"))
            effects["cm_stun"] += _as_int(fields.get("stun"))
        elif tag == "initiative":
            effects["initiative"] += _as_int(node.get("value") or fields.get("bonus") or fields.get("val"))
        elif tag == "initiativepass":
            effects["initiative_dice"] += _as_int(node.get("value") or fields.get("bonus") or fields.get("val"))
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
            effects["limit_mental"] += _as_int(node.get("value") or fields.get("bonus") or fields.get("val"))
        elif tag == "sociallimit":
            effects["limit_social"] += _as_int(node.get("value") or fields.get("bonus") or fields.get("val"))
        elif tag == "physicallimit":
            effects["limit_physical"] += _as_int(node.get("value") or fields.get("bonus") or fields.get("val"))
        elif tag == "damageresistance":
            effects["damage_resistance"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "unarmeddv":
            effects["unarmed_dv"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "unarmeddvphysical":
            effects["unarmed_physical"] = True
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
            effects["special_armor"][key] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
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
                continue
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
            effects["reach"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag in TEST_MOD_TAGS:
            key = TEST_MOD_TAGS[tag]
            effects["test_mods"][key] = int(effects["test_mods"].get(key) or 0) + _as_int(
                node.get("value") or fields.get("val") or fields.get("bonus")
            )
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
            effects["cm_recovery_physical"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "stuncmrecovery":
            effects["cm_recovery_stun"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
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
            effects["fatigue_resist"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "livingpersona":
            persona = effects.setdefault(
                "living_persona",
                {"attack": 0, "sleaze": 0, "dataprocessing": 0, "firewall": 0},
            )
            for key in ("attack", "sleaze", "dataprocessing", "firewall"):
                persona[key] = int(persona.get(key) or 0) + _as_int(fields.get(key))
        elif tag == "matrixinitiativediceadd":
            effects["matrix_initiative_dice"] = int(effects.get("matrix_initiative_dice") or 0) + _as_int(
                node.get("value") or fields.get("bonus") or fields.get("val")
            )
        elif tag == "actiondicepool":
            attrs = node.get("attrs") or {}
            category = str(attrs.get("category") or fields.get("category") or "").strip()
            name = str(fields.get("name") or "").strip()
            # Codeslinger XML has empty value; SR5 grants +2 to a chosen Matrix action.
            bonus = _as_int(node.get("value") or fields.get("val") or fields.get("bonus") or fields.get("value"), 0)
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
    return True
