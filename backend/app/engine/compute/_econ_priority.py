"""Phase 12 — priority points, nuyen and the attribute-karma floors."""

from __future__ import annotations

from typing import Any, cast

from ...data_loader import PHYSICAL_ATTRS
from ...rules import current_rules
from ..priority import heritage_cost, priority_value
from ._career import (
    _GEAR_ROW_KEYS,
    restricted_markup,
)
from .context import Ctx

#: The karma-for-nuyen cap under `<unrestrictednuyen>`: no rule stops it,
#: and spending past the karma the build has is already an error.
UNRESTRICTED_NUYEN_KARMA = 10_000


def _priority_points(ctx: Ctx) -> None:
    """Phase 12 — what the priority table hands out: attribute and skill
    points, the special points the metatype adds, and the nuyen pool."""
    attr_row = priority_value("Attributes", ctx.state.priorities.Attributes)
    skill_row = priority_value("Skills", ctx.state.priorities.Skills)
    res_row = priority_value("Resources", ctx.state.priorities.Resources)
    ctx.special_from_meta, extra_karma = heritage_cost(
        ctx.state.priorities.Heritage, ctx.state.metatype, ctx.state.metavariant
    )

    floors = {key: int(ctx.attrs_spec[key]["min"]) for key in (*PHYSICAL_ATTRS, "EDG")}
    if ctx.special_key in ("MAG", "RES"):
        floors[ctx.special_key] = ctx.talent_start
    ctx.attr_floors = floors
    ctx.attr_karma_levels = _attribute_karma_levels(ctx, floors)
    ctx.spent_physical = 0
    for key in PHYSICAL_ATTRS:
        ctx.spent_physical += max(0, ctx.bought_ratings[key] - floors[key] - ctx.attr_karma_levels.get(key, 0))
    ctx.spent_special = 0
    for key in ("EDG", "MAG", "RES"):
        if key in floors:
            ctx.spent_special += max(0, ctx.bought_ratings[key] - floors[key] - ctx.attr_karma_levels.get(key, 0))

    ctx.nuyen_karma_max = current_rules().karma_nuyen_max
    if ctx.is_karma:
        ctx.attr_points = 0
        ctx.skill_points = 0
        ctx.group_points = 0
        ctx.special_from_meta = 0
        ctx.nuyen_karma_max = current_rules().karma_nuyen_max
        if current_rules().unrestricted_nuyen:
            ctx.nuyen_karma_max = UNRESTRICTED_NUYEN_KARMA
        ctx.state.karma_nuyen = max(0, min(ctx.nuyen_karma_max, int(ctx.state.karma_nuyen or 0)))
        ctx.nuyen_pool = int(ctx.state.karma_nuyen) * current_rules().karma_to_nuyen
        ctx.metatype_karma_cost = (
            max(0, int(ctx.meta.get("karma") or 0)) * current_rules().metatype_costs_karma_multiplier
        )
        ctx.heritage_karma_cost = 0
    else:
        ctx.attr_points = int(attr_row.get("attribute_points") or 0)
        ctx.skill_points = int(skill_row.get("skill_points") or 0)
        ctx.group_points = int(skill_row.get("skill_group_points") or 0)
        ctx.nuyen_pool = int(res_row.get("nuyen") or 0)
        ctx.metatype_karma_cost = 0
        # Priority chargen: metatypes.xml <karma> is for Karma/Sum-to-Ten, not Priority.
        # Heritage table <karma> is an extra cost for some metavariants / rare races.
        ctx.heritage_karma_cost = extra_karma
        # Leftover chargen karma may buy nuyen (SR5 p.94); Born Rich raises the cap.
        ctx.nuyen_karma_max = max(
            0, current_rules().priority_karma_nuyen_base + int(ctx.effects.get("nuyen_max_bp") or 0)
        )
        if current_rules().unrestricted_nuyen:
            ctx.nuyen_karma_max = UNRESTRICTED_NUYEN_KARMA
        ctx.state.karma_nuyen = max(0, min(ctx.nuyen_karma_max, int(ctx.state.karma_nuyen or 0)))
        ctx.nuyen_pool += int(ctx.state.karma_nuyen) * current_rules().karma_to_nuyen

    ctx.nuyen_pool += int(ctx.state.nuyen_earned or 0)
    ctx.nuyen_pool += int(ctx.state.nuyen_adjust or 0) if ctx.career else 0
    ctx.nuyen_pool += int(ctx.effects.get("nuyen_amt") or 0)
    ctx.nuyen_spent = (
        sum(int(item["nuyen"]) for item in ctx.installed)
        + int(ctx.qi.get("nuyen") or 0)
        + int(ctx.foci.get("nuyen") or 0)
        + int(ctx.spirits.get("nuyen") or 0)
        + int(ctx.gear.get("nuyen") or 0)
    )
    if ctx.career:
        rows = [
            *ctx.installed,
            *(ctx.foci.get("public") or []),
            *(ctx.qi.get("public") or []),
            *(row for key in _GEAR_ROW_KEYS for row in cast("list[dict[str, Any]]", ctx.gear.get(key) or [])),
        ]
        ctx.nuyen_markup = restricted_markup(ctx.state.career_baseline, rows)
        ctx.nuyen_spent += ctx.nuyen_markup
    ctx.nuyen = ctx.nuyen_pool - ctx.nuyen_spent


def _attribute_karma_levels(ctx: Ctx, floors: dict[str, int]) -> dict[str, int]:
    """`state.attribute_karma`, clamped to what each rating has above its floor.

    A Karma build has no points to split from, so it keeps none. The cleaned
    map is written back, so a lowered rating cannot leave karma levels behind
    that it no longer has.
    """
    levels: dict[str, int] = {}
    if not ctx.is_karma:
        for key, count in (ctx.state.attribute_karma or {}).items():
            if key not in floors:
                continue
            kept = max(0, min(int(count or 0), int(ctx.bought_ratings.get(key) or 0) - floors[key]))
            if kept:
                levels[key] = kept
    ctx.state.attribute_karma = dict(levels)
    return levels
