"""Awakened / Emerged bonus nodes: adept powers, spell & spirit category limits, drain/fading, granted spells / echoes / metamagics / spirits, weapon-skill DV/accuracy slots.

One slice of the pre-split ``apply_bonus_nodes`` chain. ``apply`` returns
True iff ``tag`` is one of ours.
"""

from __future__ import annotations

from typing import Any

from ...data_loader import parse_select_power_slot
from .._common import (
    _as_int,
    _bonus_int,
)


def apply(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: dict[str, Any], source: str) -> bool:
    for _once in (True,):
        if tag == "adeptpowerpoints":
            effects["adept_power_points"] += _as_int(node.get("value") or fields.get("bonus") or fields.get("val"))
        elif tag == "magicianswaydiscount":
            effects["magicians_way"] = True
        elif tag == "selectmentorspirit":
            effects["needs_mentor"] = True
        elif tag == "focusbindingkarmacost":
            effects["focus_binding"].append(
                {
                    "name": str(fields.get("name") or "").strip(),
                    "val": _as_int(fields.get("val") or fields.get("value")),
                    "extracontains": str(fields.get("extracontains") or "").strip(),
                    "source": source,
                }
            )
        elif tag == "spellcategory":
            name = (fields.get("name") or node.get("value") or "").strip()
            bonus = _as_int(fields.get("bonus") or fields.get("val") or fields.get("value"))
            if not name or bonus == 0:
                continue
            effects["spell_category_mods"].append(
                {
                    "name": name,
                    "bonus": bonus,
                    "condition": (fields.get("condition") or "").strip(),
                    "source": source,
                }
            )
        elif tag == "spelldicepool":
            name = (fields.get("name") or fields.get("id") or node.get("value") or "").strip()
            bonus = _as_int(fields.get("val") or fields.get("bonus") or fields.get("value") or node.get("value"))
            if bonus == 0:
                continue
            effects["spell_dice_pool"].append(
                {
                    "name": name,
                    "id": str(fields.get("id") or "").strip(),
                    "bonus": bonus,
                    "source": source,
                }
            )
        elif tag == "limitspellcategory":
            attrs = node.get("attrs") or {}
            effects["limit_spell_category_slots"].append(
                {
                    "source": source,
                    "value": str(node.get("value") or fields.get("category") or "").strip(),
                    "exclude": str(attrs.get("exclude") or "").strip(),
                }
            )
        elif tag == "limitspiritcategory":
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
        elif tag == "allowspellcategory":
            name = str(node.get("value") or fields.get("category") or "").strip()
            if name and name not in effects["allow_spell_categories"]:
                effects["allow_spell_categories"].append(name)
        elif tag == "allowspellrange":
            name = str(node.get("value") or fields.get("range") or "").strip()
            if name and name not in effects["allow_spell_ranges"]:
                effects["allow_spell_ranges"].append(name)
        elif tag == "blockspelldescriptor":
            name = str(node.get("value") or fields.get("name") or "").strip()
            if name and name not in effects["block_spell_descriptors"]:
                effects["block_spell_descriptors"].append(name)
        elif tag == "spellcategorydrain":
            effects["spell_category_drain"].append(
                {
                    "source": source,
                    "category": str(fields.get("category") or node.get("value") or "").strip(),
                    "value": _as_int(fields.get("val") or fields.get("bonus") or fields.get("value")),
                }
            )
        elif tag == "spellcategorydamage":
            effects["spell_category_damage"].append(
                {
                    "source": source,
                    "category": str(fields.get("category") or node.get("value") or "").strip(),
                    "value": _as_int(fields.get("val") or fields.get("bonus") or fields.get("value")),
                }
            )
        elif tag == "spelldescriptordrain":
            effects["spell_descriptor_drain"].append(
                {
                    "source": source,
                    "descriptor": str(fields.get("descriptor") or node.get("value") or "").strip(),
                    "value": _as_int(fields.get("val") or fields.get("bonus") or fields.get("value")),
                }
            )
        elif tag == "spelldescriptordamage":
            effects["spell_descriptor_damage"].append(
                {
                    "source": source,
                    "descriptor": str(fields.get("descriptor") or node.get("value") or "").strip(),
                    "value": _as_int(fields.get("val") or fields.get("bonus") or fields.get("value")),
                }
            )
        elif tag == "drainvalue":
            effects["drain_value"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "fadingvalue":
            attrs = node.get("attrs") or {}
            specific = str(attrs.get("specific") or "").strip()
            value = _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
            if specific:
                effects["fading_value_specific"].append({"specific": specific, "value": value})
            else:
                effects["fading_value"] += value
        elif tag == "fadingresist":
            effects["fading_resist"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "drainresist":
            effects["drain_resist"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "addecho":
            name = str(node.get("value") or fields.get("name") or "").strip()
            if name:
                effects["grant_echoes"].append({"source": source, "name": name})
        elif tag == "cyberadeptdaemon":
            effects["cyberadept_daemon"] = True
        elif tag == "addspell":
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
        elif tag == "specificpower":
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
        elif tag == "selectpowers":
            slot = parse_select_power_slot(node)
            if slot.get("needs_select"):
                effects["select_power_slots"].append({"source": source, **slot})
        elif tag == "addspirit":
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
                        str(name).strip()
                        for name in ((node.get("nested") or {}).get("spirit") or [])
                        if str(name).strip()
                    ],
                }
            )
        elif tag == "addmetamagic":
            name = str(node.get("value") or "").strip()
            if name:
                effects["free_metamagics"].append(
                    {
                        "name": name,
                        "source": source,
                        "forced": str((node.get("attrs") or {}).get("forced") or "").lower() == "true",
                    }
                )
        elif tag == "freespells":
            attrs = node.get("attrs") or {}
            limit = str(attrs.get("limit") or "").strip()
            skill = str(attrs.get("skill") or "").strip()
            attribute = str(attrs.get("attribute") or "").strip().upper()
            if skill:
                effects["free_spells_skill"].append({"skill": skill, "limit": limit, "source": source})
            elif attribute:
                effects["free_spells_attribute"].append({"attribute": attribute, "limit": limit, "source": source})
            else:
                effects["free_spells_flat"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "newspellkarmacost":
            attrs = node.get("attrs") or {}
            effects["new_spell_karma_cost"].append(
                {
                    "type": str(attrs.get("type") or "").strip(),
                    "value": _as_int(node.get("value") or fields.get("val") or fields.get("bonus")),
                    "condition": str(attrs.get("condition") or "").strip(),
                    "source": source,
                }
            )
        elif tag == "burnoutsway":
            effects["burnout_way"] = True
        elif tag == "weaponcategorydv":
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
        elif tag == "weaponskillaccuracy":
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
        else:
            return False
        return True
    return True
