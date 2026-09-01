"""Skill, skill-group and knowledge-skill bonus nodes, plus the per-category karma/point cost modifiers.

One slice of the pre-split ``apply_bonus_nodes`` chain. ``apply`` returns
True iff ``tag`` is one of ours.
"""

from __future__ import annotations

from typing import Any

from .._common import _as_int
from ..effects import EffectsDict


def apply(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> bool:
    for _once in (True,):
        if tag in {"skillgroup", "skillcategory"}:
            name = (fields.get("name") or node.get("value") or "").strip()
            bonus = _as_int(fields.get("bonus") or fields.get("val") or fields.get("value"))
            if not name or bonus == 0:
                continue
            exclude = (fields.get("exclude") or "").strip()
            row = {
                "name": name,
                "bonus": bonus,
                "exclude": exclude,
                "condition": (fields.get("condition") or "").strip(),
                "source": source,
            }
            if tag == "skillgroup":
                effects["skill_group_mods"].append(row)
            else:
                effects["skill_category_mods"].append(row)
        elif tag == "unlockskills":
            name = (node.get("attrs") or {}).get("name") or fields.get("name") or node.get("value") or ""
            name = str(name).strip()
            if name and name not in effects["unlock_skills"]:
                effects["unlock_skills"].append(name)
        elif tag == "specificskill":
            name = (fields.get("name") or node.get("value") or "").strip()
            bonus = _as_int(fields.get("bonus") or fields.get("val") or fields.get("value"))
            if not name or bonus == 0:
                continue
            effects["skill_specific_mods"].append(
                {
                    "name": name,
                    "bonus": bonus,
                    "condition": (fields.get("condition") or "").strip(),
                    "source": source,
                }
            )
        elif tag == "skillattribute":
            name = (fields.get("name") or node.get("value") or "").strip().upper()
            bonus = _as_int(fields.get("bonus") or fields.get("val") or fields.get("value"))
            if not name or bonus == 0:
                continue
            effects["skill_attribute_mods"].append(
                {
                    "name": name,
                    "bonus": bonus,
                    "condition": (fields.get("condition") or "").strip(),
                    "source": source,
                }
            )
        elif tag == "skillwire":
            effects["skillwires"] = max(
                int(effects.get("skillwires") or 0),
                _as_int(node.get("value") or fields.get("val") or fields.get("bonus")),
            )
        elif tag == "skillsoftaccess":
            effects["skilljack"] = max(
                int(effects.get("skilljack") or 0),
                _as_int(node.get("value") or fields.get("val") or fields.get("bonus")),
            )
        elif tag == "skilldisable":
            name = str(node.get("value") or fields.get("name") or "").strip()
            if name and name not in effects["disabled_skills"]:
                effects["disabled_skills"].append(name)
        elif tag == "skillgroupdisable":
            name = str(node.get("value") or fields.get("name") or "").strip()
            if name and name not in effects["disabled_skill_groups"]:
                effects["disabled_skill_groups"].append(name)
        elif tag == "skillgroupcategorydisable":
            name = str(node.get("value") or fields.get("name") or "").strip()
            if name and name not in effects["disabled_skill_group_categories"]:
                effects["disabled_skill_group_categories"].append(name)
        elif tag == "skillgroupdisablechoice":
            # Applied in engine from quality_extras (selected skill group name).
            pass
        elif tag == "blockskillcategorydefaulting":
            name = str(node.get("value") or fields.get("name") or "").strip()
            if name and name not in effects["blocked_default_categories"]:
                effects["blocked_default_categories"].append(name)
        elif tag == "nativelanguagelimit":
            effects["native_language_limit_bonus"] += _as_int(
                node.get("value") or fields.get("val") or fields.get("bonus")
            )
        elif tag == "knowledgeskillpoints":
            effects["knowledge_skill_points"] += _as_int(node.get("value") or fields.get("val") or fields.get("bonus"))
        elif tag == "activeskillkarmacost":
            effects["active_skill_karma_cost"].append(
                {
                    "name": str(fields.get("name") or "").strip(),
                    "val": _as_int(fields.get("val")),
                    "min": _as_int(fields.get("min")),
                    "max": _as_int(fields.get("max")) if fields.get("max") not in (None, "") else None,
                    "condition": str(fields.get("condition") or ""),
                }
            )
        elif tag == "knowledgeskillkarmacost":
            effects["knowledge_skill_karma_cost"].append(
                {
                    "name": str(fields.get("name") or "").strip(),
                    "val": _as_int(fields.get("val")),
                    "min": _as_int(fields.get("min")),
                    "max": _as_int(fields.get("max")) if fields.get("max") not in (None, "") else None,
                    "condition": str(fields.get("condition") or ""),
                }
            )
        elif tag == "knowledgeskillkarmacostmin":
            effects["knowledge_skill_karma_cost_min"].append(
                {
                    "name": str(fields.get("name") or "").strip(),
                    "val": _as_int(fields.get("val"), 1),
                    "min": _as_int(fields.get("min")),
                    "max": _as_int(fields.get("max")) if fields.get("max") not in (None, "") else None,
                    "condition": str(fields.get("condition") or ""),
                }
            )
        elif tag == "skillcategoryspecializationkarmacostmultiplier":
            name = str(fields.get("name") or node.get("value") or "").strip()
            if name:
                effects["skill_category_spec_karma_cost_mult"].append(
                    {
                        "name": name,
                        "val": _as_int(fields.get("val") or fields.get("bonus"), 100),
                        "condition": str(fields.get("condition") or ""),
                    }
                )
        elif tag == "skillgroupcategorykarmacostmultiplier":
            name = str(fields.get("name") or node.get("value") or "").strip()
            if name:
                effects["skill_group_category_karma_cost_mult"].append(
                    {
                        "name": name,
                        "val": _as_int(fields.get("val") or fields.get("bonus"), 100),
                        "condition": str(fields.get("condition") or ""),
                    }
                )

        elif tag == "skillcategorypointcostmultiplier":
            name = str(fields.get("name") or node.get("value") or "").strip()
            if name:
                effects["skill_category_point_cost_mult"][name] = _as_int(fields.get("val") or fields.get("bonus"), 100)
        elif tag == "skillcategorykarmacostmultiplier":
            name = str(fields.get("name") or node.get("value") or "").strip()
            if name:
                effects["skill_category_karma_cost_mult"].append(
                    {
                        "name": name,
                        "val": _as_int(fields.get("val") or fields.get("bonus"), 100),
                        "condition": str(fields.get("condition") or ""),
                    }
                )
        elif tag == "skillcategorykarmacost":
            name = str(fields.get("name") or "").strip()
            if name:
                effects["skill_category_karma_cost"].append(
                    {
                        "name": name,
                        "val": _as_int(fields.get("val")),
                        "min": _as_int(fields.get("min")),
                        "max": _as_int(fields.get("max")) if fields.get("max") not in (None, "") else None,
                        "condition": str(fields.get("condition") or ""),
                    }
                )
        else:
            return False
        return True
    return True
