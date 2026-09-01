"""Dice-pool and opposed-test builders shared across subsystems.

``skill_dice_pool`` turns a skill + attribute + situational bonus into the pool
the UI shows (with defaulting / "missing" flags). ``magic_opposed_test`` layers
Force limits, opposed hits and drain on top — it is used for summoning/binding,
focus artificing, and (despite the name) technomancer compiling/registering.

Depends only on ``catalog`` and ``DRAIN_MINIMUM``.
"""

from __future__ import annotations

from typing import Any

from ..data_loader import catalog
from .constants import DRAIN_MINIMUM


def _skill_spec(name: str, skills_data: dict[str, Any] | None = None) -> dict[str, Any] | None:
    data = skills_data if skills_data is not None else catalog().get("skills") or {}
    skills: list[dict[str, Any]] = data.get("skills") or []
    for item in skills:
        if item["name"] == name:
            return item
    return None


def skill_dice_pool(
    skill_name: str,
    skill_totals: dict[str, int],
    skill_bonus: dict[str, int],
    attrs: dict[str, int],
    skills_data: dict[str, Any] | None = None,
    attr_override: str | None = None,
) -> dict[str, Any]:
    spec = _skill_spec(skill_name, skills_data)
    attr_name = attr_override or (spec or {}).get("attribute") or "MAG"
    rating = int(skill_totals.get(skill_name) or 0)
    bonus = int(skill_bonus.get(skill_name) or 0)
    attr_value = int(attrs.get(attr_name) or 0)
    can_default = bool((spec or {}).get("default"))
    if rating <= 0:
        if can_default:
            pool = max(0, attr_value - 1) + bonus
            return {
                "skill": skill_name,
                "rating": 0,
                "attr": attr_name,
                "attr_value": attr_value,
                "bonus": bonus,
                "pool": pool,
                "defaulted": True,
                "missing": False,
            }
        return {
            "skill": skill_name,
            "rating": 0,
            "attr": attr_name,
            "attr_value": attr_value,
            "bonus": bonus,
            "pool": 0,
            "defaulted": False,
            "missing": True,
        }
    return {
        "skill": skill_name,
        "rating": rating,
        "attr": attr_name,
        "attr_value": attr_value,
        "bonus": bonus,
        "pool": rating + attr_value + bonus,
        "defaulted": False,
        "missing": False,
    }


def magic_opposed_test(
    skill_name: str,
    force: int,
    vs: int,
    mag: int,
    skill_totals: dict[str, int],
    skill_bonus: dict[str, int],
    attrs: dict[str, int],
    hits: int | None = None,
    opposed_hits: int | None = None,
    limit: int | None = None,
    limit_name: str = "Force",
    days: int | None = None,
    skills_data: dict[str, Any] | None = None,
    attr_override: str | None = None,
) -> dict[str, Any]:
    dice = skill_dice_pool(skill_name, skill_totals, skill_bonus, attrs, skills_data, attr_override=attr_override)
    used_limit = int(limit if limit is not None else force)
    my_hits = None if hits is None else max(0, int(hits))
    their_hits = None if opposed_hits is None else max(0, int(opposed_hits))
    net = None if my_hits is None or their_hits is None else my_hits - their_hits
    drain = None if their_hits is None else max(DRAIN_MINIMUM, their_hits * 2)
    physical = bool(mag) and int(force) > int(mag)
    return {
        **dice,
        "force": int(force),
        "limit": used_limit,
        "limit_name": limit_name,
        "vs": int(vs),
        "hits": my_hits,
        "opposed_hits": their_hits,
        "net": net,
        "drain": drain,
        "drain_code": None if drain is None else ("P" if physical else "S"),
        "physical": physical,
        "days": days,
    }
