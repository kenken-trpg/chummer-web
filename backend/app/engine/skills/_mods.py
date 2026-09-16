"""Dice modifiers from `<skillcategory>`, `<skillgroup>` and per-skill bonuses."""

from __future__ import annotations

from typing import Any

from ...improvements import EffectsDict
from ..bundle_types import SkillMods
from ._knowledge import KNOWLEDGE_CATEGORIES, KNOWLEDGE_DEFAULT_ATTR


def resolve_skill_mods(
    skills_data: dict[str, Any],
    effects: EffectsDict,
    knowledge_ratings: dict[str, int],
    extra_categories: dict[str, str] | None = None,
) -> SkillMods:
    active = list(skills_data.get("skills") or [])
    knowledge = list(skills_data.get("knowledge") or [])
    overridden = {name for name in (extra_categories or {}) if name}
    # a listed skill whose type was changed is re-described below, not twice
    knowledge = [skill for skill in knowledge if skill["name"] not in overridden]
    for name, category in (extra_categories or {}).items():
        if not name:
            continue
        category = category if category in KNOWLEDGE_CATEGORIES else "Street"
        knowledge.append(
            {
                "name": name,
                "category": category,
                "attribute": KNOWLEDGE_DEFAULT_ATTR.get(category, "INT"),
                "knowledge": True,
            }
        )
    bought_knowledge = {name for name, rating in knowledge_ratings.items() if int(rating or 0) > 0}
    skill_bonus: dict[str, int] = {}
    skill_notes: dict[str, list[str]] = {}

    def add_bonus(skill_name: str, bonus: int, note: str) -> None:
        if not bonus:
            return
        skill_bonus[skill_name] = int(skill_bonus.get(skill_name, 0)) + int(bonus)
        if note:
            notes = skill_notes.setdefault(skill_name, [])
            if note not in notes:
                notes.append(note)

    by_group: dict[str, list[dict[str, Any]]] = {}
    by_category: dict[str, list[dict[str, Any]]] = {}
    for skill in active + knowledge:
        group = skill.get("skillgroup")
        if group:
            by_group.setdefault(group, []).append(skill)
        category = skill.get("category")
        if category:
            by_category.setdefault(category, []).append(skill)

    group_bonus: dict[str, int] = {}
    for mod in effects.get("skill_group_mods") or []:
        name = mod.get("name") or ""
        bonus = int(mod.get("bonus") or 0)
        if not name or not bonus:
            continue
        group_bonus[name] = int(group_bonus.get(name, 0)) + bonus
        exclude = mod.get("exclude") or ""
        for skill in by_group.get(name, []):
            if skill["name"] == exclude:
                continue
            add_bonus(skill["name"], bonus, mod.get("condition") or "")

    category_bonus: dict[str, int] = {}
    for mod in effects.get("skill_category_mods") or []:
        name = mod.get("name") or ""
        bonus = int(mod.get("bonus") or 0)
        if not name or not bonus:
            continue
        category_bonus[name] = int(category_bonus.get(name, 0)) + bonus
        exclude = mod.get("exclude") or ""
        for skill in by_category.get(name, []):
            if skill["name"] == exclude:
                continue
            if name in KNOWLEDGE_CATEGORIES and skill["name"] not in bought_knowledge:
                continue
            add_bonus(skill["name"], bonus, mod.get("condition") or "")

    for spec_mod in effects.get("skill_specific_mods") or []:
        add_bonus(spec_mod.get("name") or "", int(spec_mod.get("bonus") or 0), spec_mod.get("condition") or "")

    # `<swapskillattribute>` moves a skill onto another attribute for good;
    # the spec-limited variant only moves the tests that use its
    # specialization, so it stays out of the pool maths and is passed on as a
    # note instead.
    swapped: dict[str, str] = {}
    for swap in effects.get("skill_attribute_swaps") or []:
        name = str(swap.get("skill") or "").strip()
        attribute = str(swap.get("attribute") or "").strip().upper()
        if name and attribute and not swap.get("spec"):
            swapped[name] = attribute

    for attr_mod in effects.get("skill_attribute_mods") or []:
        attr = (attr_mod.get("name") or "").upper()
        bonus = int(attr_mod.get("bonus") or 0)
        if not attr or not bonus:
            continue
        # `skill_bonus` is keyed by name, and a handful of names (Medicine,
        # Chemistry, Cybertechnology) sit in both lists — walk unique names so
        # such a skill is not paid twice. Unbought knowledge skills are skipped
        # for the same reason the category loop skips them: `knowledge` holds
        # the whole catalog, not the character's sheet.
        seen: set[str] = set()
        for skill in active + knowledge:
            skill_name = str(skill["name"])
            printed = (skill.get("attribute") or "").upper()
            # `<skilllinkedattribute>` reads the printed attribute even after a
            # swap; `<skillattribute>` follows the skill where it went.
            if (printed if attr_mod.get("linked") else swapped.get(skill_name, printed)) != attr:
                continue
            if skill_name in seen:
                continue
            if skill.get("knowledge") and skill_name not in bought_knowledge:
                continue
            seen.add(skill_name)
            add_bonus(skill_name, bonus, attr_mod.get("condition") or "")

    return {
        "skill_bonus": skill_bonus,
        "skill_group_bonus": group_bonus,
        "skill_category_bonus": category_bonus,
        "skill_bonus_notes": skill_notes,
    }
