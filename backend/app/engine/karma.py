"""Karma & knowledge-point cost maths: attribute / active-skill / skill-group
raise costs, knowledge free-point spend and overflow karma, and the
custom-karma-rule (`<karmacost>`) helpers. Pure arithmetic over the catalog
skill list — no other engine imports.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

from ..data_loader import PHYSICAL_ATTRS
from .constants import (
    KARMA_ACTIVE_SKILL,
    KARMA_ATTRIBUTE,
    KARMA_KNOWLEDGE,
    KARMA_SKILL_GROUP,
)


def _karma_raise_cost(from_rating: int, to_rating: int, per_rating: int) -> int:
    low = max(0, int(from_rating))
    high = max(0, int(to_rating))
    if high <= low or per_rating <= 0:
        return 0
    return sum(level * int(per_rating) for level in range(low + 1, high + 1))


def attribute_karma_cost(
    ratings: dict[str, int],
    attrs_spec: dict[str, dict[str, int | float]],
    special_key: str | None,
) -> int:
    total = 0
    for key in (*PHYSICAL_ATTRS, "EDG"):
        spec = attrs_spec.get(key) or {}
        racial_min = int(spec.get("min") or 1)
        total += _karma_raise_cost(racial_min, int(ratings.get(key) or racial_min), KARMA_ATTRIBUTE)
    if special_key == "MAG":
        total += _karma_raise_cost(1, int(ratings.get("MAG") or 0), KARMA_ATTRIBUTE)
    elif special_key == "RES":
        total += _karma_raise_cost(1, int(ratings.get("RES") or 0), KARMA_ATTRIBUTE)
    return total


def skill_karma_cost(
    skill_groups: dict[str, int],
    skill_totals: dict[str, int],
    skills_data: dict[str, Any],
    *,
    group_cap: int = 6,
) -> int:
    total = 0
    group_floor: dict[str, int] = {}
    for group, rating in (skill_groups or {}).items():
        grade = max(0, min(int(group_cap), int(rating or 0)))
        total += _karma_raise_cost(0, grade, KARMA_SKILL_GROUP)
        for skill in skills_data.get("skills") or []:
            if skill.get("skillgroup") == group and not skill.get("exotic"):
                name = skill.get("name") or ""
                if name:
                    group_floor[name] = max(group_floor.get(name, 0), grade)
    for name, rating in (skill_totals or {}).items():
        floor = int(group_floor.get(name) or 0)
        total += _karma_raise_cost(floor, int(rating or 0), KARMA_ACTIVE_SKILL)
    return total


def _group_floor_map(skill_groups: dict[str, int], skills_data: dict[str, Any]) -> dict[str, int]:
    floors: dict[str, int] = {}
    for group, rating in (skill_groups or {}).items():
        grade = max(0, int(rating or 0))
        for skill in skills_data.get("skills") or []:
            if skill.get("skillgroup") == group and not skill.get("exotic"):
                name = str(skill.get("name") or "")
                if name:
                    floors[name] = max(floors.get(name, 0), grade)
    return floors


def _floor_tenth(value: float) -> float:
    return math.floor(float(value) * 10.0 + 1e-9) / 10.0


def _point_cost(rating: int, mult_pct: int) -> int:
    rating = max(0, int(rating or 0))
    mult = max(0, int(mult_pct if mult_pct is not None else 100))
    if rating <= 0:
        return 0
    return int(math.ceil(rating * mult / 100.0))


def _skill_category_map(skills_data: dict[str, Any]) -> dict[str, str]:
    return {
        str(skill.get("name") or ""): str(skill.get("category") or "")
        for skill in (skills_data.get("skills") or [])
        if skill.get("name")
    }


def knowledge_points_spent(
    public: list[dict[str, Any]],
    point_mults: dict[str, int],
) -> int:
    total = 0
    for row in public or []:
        if row.get("native"):
            continue
        rating = int(row.get("rating") or 0)
        cat = str(row.get("category") or "")
        total += _point_cost(rating, int(point_mults.get(cat, 100)))
    return total


def _karma_cost_with_category_mods(
    from_rating: int,
    to_rating: int,
    per_rating: int,
    *,
    mult_pct: int = 100,
    flat_adj: int = 0,
    flat_min: int = 0,
    flat_rules: Sequence[Mapping[str, Any]] | None = None,
    min_rules: Sequence[Mapping[str, Any]] | None = None,
) -> int:
    low = max(0, int(from_rating))
    high = max(0, int(to_rating))
    if high <= low or per_rating <= 0:
        return 0
    rules = list(flat_rules or [])
    if flat_adj and not rules:
        rules.append({"val": int(flat_adj), "min": int(flat_min or 0), "max": None})
    total = 0
    for level in range(low + 1, high + 1):
        base = level * int(per_rating)
        for rule in rules:
            rmin = int(rule.get("min") or 0)
            rmax = rule.get("max")
            if level < rmin:
                continue
            if rmax is not None and str(rmax) != "" and level > int(rmax):
                continue
            base += int(rule.get("val") or 0)
        floor = 1
        for rule in min_rules or []:
            rmin = int(rule.get("min") or 0)
            rmax = rule.get("max")
            if level < rmin:
                continue
            if rmax is not None and str(rmax) != "" and level > int(rmax):
                continue
            floor = max(floor, int(rule.get("val") or 1))
        total += max(floor, int(math.ceil(base * mult_pct / 100.0)))
    return total


def _active_karma_mults(rules: Sequence[Mapping[str, Any]] | None, *, career: bool) -> dict[str, int]:
    out: dict[str, int] = {}
    for rule in rules or []:
        name = str(rule.get("name") or "").strip()
        if not name:
            continue
        cond = str(rule.get("condition") or "").replace(" ", "")
        if cond in {"/character/created=false", "/character/created=False"} and career:
            continue
        if cond == "/character/created" and not career:
            continue
        # Later rules override earlier for same category.
        out[name] = int(rule.get("val") or 100)
    return out


def _filter_karma_rules(rules: Sequence[Mapping[str, Any]] | None, *, career: bool) -> list[Mapping[str, Any]]:
    out: list[Mapping[str, Any]] = []
    for rule in rules or []:
        cond = str(rule.get("condition") or "").replace(" ", "")
        if cond in {"/character/created=false", "/character/created=False"} and career:
            continue
        if cond == "/character/created" and not career:
            continue
        out.append(rule)
    return out


def _matching_karma_rules(rules: Sequence[Mapping[str, Any]] | None, name: str) -> list[Mapping[str, Any]]:
    target = str(name or "")
    matched: list[Mapping[str, Any]] = []
    for rule in rules or []:
        rname = str(rule.get("name") or "")
        if rname == "" or rname == target:
            matched.append(rule)
    return matched


def _skill_groups_for_category(skills_data: dict[str, Any], category: str) -> list[str]:
    """Groups whose every skill belongs to the given category."""
    by_group: dict[str, list[str]] = {}
    for skill in skills_data.get("skills") or []:
        group = str(skill.get("skillgroup") or "").strip()
        if not group:
            continue
        by_group.setdefault(group, []).append(str(skill.get("category") or ""))
    out: list[str] = []
    for group, cats in by_group.items():
        if cats and all(cat == category for cat in cats):
            out.append(group)
    return out


def _skill_group_category_map(skills_data: dict[str, Any]) -> dict[str, str]:
    """Map skill group → category when all member skills share one category."""
    by_group: dict[str, list[str]] = {}
    for skill in skills_data.get("skills") or []:
        group = str(skill.get("skillgroup") or "").strip()
        if not group:
            continue
        by_group.setdefault(group, []).append(str(skill.get("category") or ""))
    out: dict[str, str] = {}
    for group, cats in by_group.items():
        uniq = {cat for cat in cats if cat}
        if len(uniq) == 1:
            out[group] = next(iter(uniq))
    return out


def knowledge_excess_karma(
    ratings: dict[str, int],
    free_points: int,
    *,
    categories: dict[str, str] | None = None,
    karma_mults: dict[str, int] | None = None,
) -> int:
    cats = categories or {}
    mults = karma_mults or {}
    levels: list[int] = []
    for name, rating in (ratings or {}).items():
        cat = str(cats.get(name) or "")
        mult = int(mults.get(cat, 100))
        for level in range(1, max(0, int(rating or 0)) + 1):
            levels.append(max(1, int(math.ceil(level * KARMA_KNOWLEDGE * mult / 100.0))))
    levels.sort()
    free = max(0, int(free_points))
    if free >= len(levels):
        return 0
    return sum(levels[free:])
