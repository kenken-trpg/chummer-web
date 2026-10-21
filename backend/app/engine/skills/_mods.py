"""Dice modifiers from `<skillcategory>`, `<skillgroup>` and per-skill bonuses."""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass, field
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
    knowledge = _knowledge_rows(list(skills_data.get("knowledge") or []), extra_categories or {})
    bought_knowledge = {name for name, rating in knowledge_ratings.items() if int(rating or 0) > 0}
    bonuses = _Bonuses()
    by_group: dict[str, list[dict[str, Any]]] = {}
    by_category: dict[str, list[dict[str, Any]]] = {}
    for skill in active + knowledge:
        group = skill.get("skillgroup")
        if group:
            by_group.setdefault(group, []).append(skill)
        category = skill.get("category")
        if category:
            by_category.setdefault(category, []).append(skill)
    group_bonus = _listed_mods(effects.get("skill_group_mods") or [], by_group, bonuses, set())
    category_bonus = _listed_mods(
        effects.get("skill_category_mods") or [],
        by_category,
        bonuses,
        bought_knowledge,
        # a knowledge category reaches only the knowledge skills on the sheet
        sheet_only=KNOWLEDGE_CATEGORIES,
    )
    for spec_mod in effects.get("skill_specific_mods") or []:
        bonuses.add(spec_mod.get("name") or "", int(spec_mod.get("bonus") or 0), spec_mod.get("condition") or "")
    _attribute_mods(effects, active + knowledge, bought_knowledge, bonuses)
    return {
        "skill_bonus": bonuses.total,
        "skill_group_bonus": group_bonus,
        "skill_category_bonus": category_bonus,
        "skill_bonus_notes": bonuses.notes,
    }


@dataclass
class _Bonuses:
    """Dice bonuses per skill name, with the conditions they come with."""

    total: dict[str, int] = field(default_factory=dict)
    notes: dict[str, list[str]] = field(default_factory=dict)

    def add(self, skill_name: str, bonus: int, note: str) -> None:
        if not bonus:
            return
        self.total[skill_name] = int(self.total.get(skill_name, 0)) + int(bonus)
        if note:
            notes = self.notes.setdefault(skill_name, [])
            if note not in notes:
                notes.append(note)


def _knowledge_rows(knowledge: list[dict[str, Any]], extra_categories: dict[str, str]) -> list[dict[str, Any]]:
    """The catalog's knowledge skills, plus the character's own, typed as the character typed them."""
    overridden = {name for name in extra_categories if name}
    # a listed skill whose type was changed is re-described below, not twice
    rows = [skill for skill in knowledge if skill["name"] not in overridden]
    for name, category in extra_categories.items():
        if not name:
            continue
        category = category if category in KNOWLEDGE_CATEGORIES else "Street"
        rows.append(
            {
                "name": name,
                "category": category,
                "attribute": KNOWLEDGE_DEFAULT_ATTR.get(category, "INT"),
                "knowledge": True,
            }
        )
    return rows


def _listed_mods(
    mods: list[Any],
    members: dict[str, list[dict[str, Any]]],
    bonuses: _Bonuses,
    bought_knowledge: set[str],
    sheet_only: Collection[str] = (),
) -> dict[str, int]:
    """Spread `<skillgroup>` / `<skillcategory>` bonuses over their members;
    return the total per group or category."""
    totals: dict[str, int] = {}
    for mod in mods:
        name = mod.get("name") or ""
        bonus = int(mod.get("bonus") or 0)
        if not name or not bonus:
            continue
        totals[name] = int(totals.get(name, 0)) + bonus
        exclude = mod.get("exclude") or ""
        for skill in members.get(name, []):
            if skill["name"] == exclude:
                continue
            if name in sheet_only and skill["name"] not in bought_knowledge:
                continue
            bonuses.add(skill["name"], bonus, mod.get("condition") or "")
    return totals


def _attribute_mods(
    effects: EffectsDict, skills: list[dict[str, Any]], bought_knowledge: set[str], bonuses: _Bonuses
) -> None:
    """`<skillattribute>` / `<skilllinkedattribute>`: a bonus on every skill of an attribute."""
    swapped = _swapped_attributes(effects)
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
        for skill in skills:
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
            bonuses.add(skill_name, bonus, attr_mod.get("condition") or "")


def _swapped_attributes(effects: EffectsDict) -> dict[str, str]:
    """`<swapskillattribute>` moves a skill onto another attribute for good;
    the spec-limited variant only moves the tests that use its
    specialization, so it stays out of the pool maths and is passed on as a
    note instead."""
    swapped: dict[str, str] = {}
    for swap in effects.get("skill_attribute_swaps") or []:
        name = str(swap.get("skill") or "").strip()
        attribute = str(swap.get("attribute") or "").strip().upper()
        if name and attribute and not swap.get("spec"):
            swapped[name] = attribute
    return swapped
