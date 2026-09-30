"""Skill, skill-group and knowledge-skill bonus nodes, plus the per-category karma/point cost modifiers.

One slice of the bonus-node table. Each handler claims its tags with
``@handles`` and is reached by lookup, not by falling down a chain.
"""

from __future__ import annotations

from typing import Any

from .._common import _as_int, _bonus_int
from ..effect_rows import SkillModRow
from ..effects import EffectsDict
from ._registry import handles


@handles("skillgroup", "skillgrouplevel", "skillcategory")
def _skillgroup(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    # `skillgrouplevel` is Chummer's free-level flavour, and the only thing
    # carrying it (Heinzelmännchen, SAG p.121) reads "+1 dice pool modifier for
    # tests using ... the Engineering skill group" — so it is the dice the book
    # promises, not a rating nobody paid for.
    name = (fields.get("name") or node.get("value") or "").strip()
    bonus = _as_int(fields.get("bonus") or fields.get("val") or fields.get("value"))
    if not name or bonus == 0:
        return
    exclude = (fields.get("exclude") or "").strip()
    row: SkillModRow = {
        "name": name,
        "bonus": bonus,
        "exclude": exclude,
        "condition": (fields.get("condition") or "").strip(),
        "source": source,
    }
    if tag in {"skillgroup", "skillgrouplevel"}:
        effects["skill_group_mods"].append(row)
    else:
        effects["skill_category_mods"].append(row)


@handles("unlockskills")
def _unlockskills(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    name = (node.get("attrs") or {}).get("name") or fields.get("name") or node.get("value") or ""
    name = str(name).strip()
    if name and name not in effects["unlock_skills"]:
        effects["unlock_skills"].append(name)


@handles("specificskill")
def _specificskill(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    name = (fields.get("name") or node.get("value") or "").strip()
    bonus = _as_int(fields.get("bonus") or fields.get("val") or fields.get("value"))
    if not name or bonus == 0:
        return
    effects["skill_specific_mods"].append(
        {
            "name": name,
            "bonus": bonus,
            "condition": (fields.get("condition") or "").strip(),
            "source": source,
        }
    )


@handles("addskillspecializationoption")
def _addskillspecializationoption(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    spec_name = str(fields.get("spec") or fields.get("name") or "").strip()
    names = [str(n).strip() for n in ((node.get("nested") or {}).get("skills") or [])]
    names.append(str(fields.get("skill") or "").strip())
    if not spec_name:
        return
    for skill_name in names:
        if not skill_name:
            continue
        bucket = effects["skill_spec_options"].setdefault(skill_name, [])
        if spec_name not in bucket:
            bucket.append(spec_name)


@handles("skillattribute", "skilllinkedattribute")
def _skillattribute(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    name = (fields.get("name") or node.get("value") or "").strip().upper()
    bonus = _as_int(fields.get("bonus") or fields.get("val") or fields.get("value"))
    if not name or bonus == 0:
        return
    effects["skill_attribute_mods"].append(
        {
            "name": name,
            "bonus": bonus,
            "condition": (fields.get("condition") or "").strip(),
            "source": source,
            "linked": tag == "skilllinkedattribute",
        }
    )


@handles("swapskillattribute", "swapskillspecattribute")
def _swapskillattribute(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    attribute = (fields.get("attribute") or "").strip().upper()
    spec = (fields.get("spec") or "").strip() if tag == "swapskillspecattribute" else ""
    for raw in str(fields.get("limittoskill") or "").split(","):
        skill_name = raw.strip()
        if not skill_name or not attribute:
            continue
        effects["skill_attribute_swaps"].append(
            {
                "skill": skill_name,
                "attribute": attribute,
                "spec": spec,
                "source": source,
            }
        )


@handles("skillwire")
def _skillwire(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["skillwires"] = max(
        int(effects.get("skillwires") or 0),
        _bonus_int(node, fields),
    )


@handles("skillsoftaccess")
def _skillsoftaccess(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    effects["skilljack"] = max(
        int(effects.get("skilljack") or 0),
        _bonus_int(node, fields),
    )


@handles("skilldisable")
def _skilldisable(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    name = str(node.get("value") or fields.get("name") or "").strip()
    if name and name not in effects["disabled_skills"]:
        effects["disabled_skills"].append(name)


@handles("skillgroupdisable")
def _skillgroupdisable(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    name = str(node.get("value") or fields.get("name") or "").strip()
    if name and name not in effects["disabled_skill_groups"]:
        effects["disabled_skill_groups"].append(name)


@handles("skillgroupcategorydisable")
def _skillgroupcategorydisable(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    name = str(node.get("value") or fields.get("name") or "").strip()
    if name and name not in effects["disabled_skill_group_categories"]:
        effects["disabled_skill_group_categories"].append(name)


@handles("skillgroupdisablechoice")
def _skillgroupdisablechoice(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    pass


@handles("blockskillcategorydefaulting")
def _blockskillcategorydefaulting(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    name = str(node.get("value") or fields.get("name") or "").strip()
    if name and name not in effects["blocked_default_categories"]:
        effects["blocked_default_categories"].append(name)


@handles("nativelanguagelimit")
def _nativelanguagelimit(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["native_language_limit_bonus"] += _bonus_int(node, fields)


@handles("knowledgeskillpoints")
def _knowledgeskillpoints(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["knowledge_skill_points"] += _bonus_int(node, fields)


@handles("activeskillkarmacost")
def _activeskillkarmacost(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["active_skill_karma_cost"].append(
        {
            "name": str(fields.get("name") or "").strip(),
            "val": _as_int(fields.get("val")),
            "min": _as_int(fields.get("min")),
            "max": _as_int(fields.get("max")) if fields.get("max") not in (None, "") else None,
            "condition": str(fields.get("condition") or ""),
        }
    )


@handles("knowledgeskillkarmacost")
def _knowledgeskillkarmacost(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["knowledge_skill_karma_cost"].append(
        {
            "name": str(fields.get("name") or "").strip(),
            "val": _as_int(fields.get("val")),
            "min": _as_int(fields.get("min")),
            "max": _as_int(fields.get("max")) if fields.get("max") not in (None, "") else None,
            "condition": str(fields.get("condition") or ""),
        }
    )


@handles("knowledgeskillkarmacostmin")
def _knowledgeskillkarmacostmin(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    effects["knowledge_skill_karma_cost_min"].append(
        {
            "name": str(fields.get("name") or "").strip(),
            "val": _as_int(fields.get("val"), 1),
            "min": _as_int(fields.get("min")),
            "max": _as_int(fields.get("max")) if fields.get("max") not in (None, "") else None,
            "condition": str(fields.get("condition") or ""),
        }
    )


@handles("skillcategoryspecializationkarmacostmultiplier")
def _skillcategoryspecializationkarmacostmultiplier(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    name = str(fields.get("name") or node.get("value") or "").strip()
    if name:
        effects["skill_category_spec_karma_cost_mult"].append(
            {
                "name": name,
                "val": _as_int(fields.get("val") or fields.get("bonus"), 100),
                "condition": str(fields.get("condition") or ""),
            }
        )


@handles("skillgroupcategorykarmacostmultiplier")
def _skillgroupcategorykarmacostmultiplier(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    name = str(fields.get("name") or node.get("value") or "").strip()
    if name:
        effects["skill_group_category_karma_cost_mult"].append(
            {
                "name": name,
                "val": _as_int(fields.get("val") or fields.get("bonus"), 100),
                "condition": str(fields.get("condition") or ""),
            }
        )


@handles("skillcategorypointcostmultiplier")
def _skillcategorypointcostmultiplier(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    name = str(fields.get("name") or node.get("value") or "").strip()
    if name:
        effects["skill_category_point_cost_mult"][name] = _as_int(fields.get("val") or fields.get("bonus"), 100)


@handles("skillcategorykarmacostmultiplier")
def _skillcategorykarmacostmultiplier(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
    name = str(fields.get("name") or node.get("value") or "").strip()
    if name:
        effects["skill_category_karma_cost_mult"].append(
            {
                "name": name,
                "val": _as_int(fields.get("val") or fields.get("bonus"), 100),
                "condition": str(fields.get("condition") or ""),
            }
        )


@handles("skillcategorykarmacost")
def _skillcategorykarmacost(
    tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str
) -> None:
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


@handles("selectskill", "hardwires")
def _selectskill(tag: str, node: dict[str, Any], fields: dict[str, Any], effects: EffectsDict, source: str) -> None:
    # Nothing to fold in here: a `<selectskill>` is a *choice*, and the choice
    # is read straight off the node by `engine/skills/_picks.py`
    # (`SKILL_PICK_TAGS`), which also tells the hardwire flavour apart. This
    # says so rather than leaving the tag to be admitted with nobody behind it.
    pass
