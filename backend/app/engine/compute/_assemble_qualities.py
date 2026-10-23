"""Phase 19 helpers — the quality rows and the metatype-info block of
``derived``, and ``_effective_attr_spec`` (the metatype-info attribute
rewrite)."""

from __future__ import annotations

from typing import Any

from ..constants import (
    _normalize_side,
    quality_optional_power_extra_key,
    quality_spirit_category_extra_key,
)
from ..lookups import critter_power_label, critter_power_rows
from ..qualities import _quality_has_selectside, has_extra_per_take, is_free_take, quality_needs_extra, take_extra_keys
from ._shapeshifter import animal_form, metahuman_form
from .context import Ctx
from .derived_types import _MetatypeInfo


def _nth(rows: list[int | None], idx: int) -> int | None:
    return rows[idx] if idx < len(rows) else None


def _quality_critter_powers(q: dict[str, Any], extras: dict[str, str]) -> dict[str, Any]:
    """The critter powers an Infected quality grants (RF p.126), the list its
    one optional power comes from, and the pick — empty for every other
    quality, so their rows stay as they were."""
    fixed = list(q.get("critter_powers") or [])
    optional = [critter_power_label(row) for row in q.get("optional_powers") or []]
    if not fixed and not optional:
        return {}
    picked = extras.get(quality_optional_power_extra_key(q["id"])) or ""
    labels = [critter_power_label(row) for row in fixed]
    rows = critter_power_rows(labels + ([picked] if picked in optional else []))
    for row, ref in zip(rows, fixed, strict=False):
        if ref.get("rating"):
            row["rating"] = ref["rating"]
    out: dict[str, Any] = {"critter_powers": rows}
    if optional:
        out["optional_powers"] = optional
        out["optional_power"] = picked
    return out


def _effective_attr_spec(
    attrs_spec: dict[str, dict[str, int | float]],
    special_key: str | None,
    talent_start: int,
    mag_max_bonus: int = 0,
    res_max_bonus: int = 0,
    *,
    special_floors: dict[str, int] | None = None,
) -> dict[str, dict[str, int | float]]:
    out = {key: dict(spec) for key, spec in attrs_spec.items()}
    floors = (
        special_floors if special_floors is not None else ({special_key: max(talent_start, 1)} if special_key else {})
    )
    for key, bonus in (("MAG", mag_max_bonus), ("RES", res_max_bonus)):
        out[key]["min"] = floors.get(key, 0)
        out[key]["max"] = int(out[key].get("max") or 0) + max(0, int(bonus)) if key in floors else 0
    if "DEP" in out:
        out["DEP"]["min"] = floors.get("DEP", 0)
        out["DEP"]["max"] = int(out["DEP"].get("max") or 0) if "DEP" in floors else 0
    return out


def quality_rows(ctx: Ctx) -> list[dict[str, Any]]:
    """``derived["qualities"]``: one row per taken quality, in order."""
    extra_keys = take_extra_keys(ctx.qualities)
    return [
        {
            "id": q["id"],
            "name": q["name"],
            "karma": 0 if is_free_take(q, ctx.free_quality_ids) else q["karma"],
            "category": q["category"],
            "source": q["source"],
            "has_levels": bool(q.get("has_levels")),
            "needs_extra": quality_needs_extra(q),
            "extra": ctx.state.quality_extras.get(extra_key) or "",
            # where this take's own text goes (Records on File, twice)
            **({"extra_key": extra_key} if has_extra_per_take(q) else {}),
            "spirit_extra": ctx.state.quality_extras.get(quality_spirit_category_extra_key(q["id"])) or "",
            "extra_kind": q.get("extra_kind"),
            "select_options": list(q.get("select_options") or []),
            "spirit_options": list(q.get("spirit_options") or []),
            "expertise_skill": q.get("expertise_skill") or "",
            "add_spirit_count": int(q.get("add_spirit_count") or 0),
            "selectside": _quality_has_selectside(q),
            "side": _normalize_side(ctx.state.quality_extras.get(q["id"])) if _quality_has_selectside(q) else None,
            "free": is_free_take(q, ctx.free_quality_ids) or bool(q.get("onlyprioritygiven")),
            **(
                {
                    "origin": q["origin"],
                    "origin_id": q["origin_id"],
                    "origin_name": q["origin_name"],
                    "removable": q["removable"],
                    "extra": q.get("select") or "",
                    "page": q.get("page") or "",
                }
                if q.get("origin") == "Metatype"
                else {}
            ),
            **_quality_critter_powers(q, ctx.state.quality_extras),
            # the table value, only when a `<costdiscount>` moved it
            **({"karma_base": q["karma_base"]} if q.get("karma_base") is not None else {}),
            **({"disabled_by": ctx.disabled_qualities[q["id"]]} if q["id"] in ctx.disabled_qualities else {}),
            # taken after chargen: what it cost then (SR5 p.107)
            **({"career_cost": cost} if (cost := _nth(ctx.quality_career_costs, idx)) is not None else {}),
        }
        for idx, (q, extra_key) in enumerate(zip(ctx.qualities, extra_keys, strict=True))
    ]


def removed_innate_rows(ctx: Ctx) -> list[dict[str, Any]]:
    """``derived["removed_innate_qualities"]``: the innate qualities taken
    off at chargen, each with what taking it off cost (negative: given back)."""
    return [
        {
            "id": grant["id"],
            "name": grant["name"],
            "category": grant["category"],
            "karma": -int(grant.get("karma") or 0),
            "origin_name": grant["origin_name"],
        }
        for grant in ctx.removed_innate
    ]


def metatype_info(ctx: Ctx, clamped: set[str]) -> _MetatypeInfo:
    """``derived["metatype_info"]``: the metatype's attribute ranges after
    talent, initiation / submersion and `<attributemaxclamp>`."""
    info: _MetatypeInfo = {
        "name": ctx.meta["name"],
        "parent": ctx.meta.get("parent"),
        "attributes": {
            key: {
                **spec,
                "max": int(spec.get("max") or 0) + int(ctx.attr_max_bonus.get(key) or 0),
                # `<attributemaxclamp>`: no augmented headroom above the natural maximum
                "aug": int(spec.get("max" if key in clamped else "aug") or 0) + int(ctx.attr_max_bonus.get(key) or 0),
            }
            for key, spec in _effective_attr_spec(
                ctx.attrs_spec,
                ctx.special_key,
                ctx.talent_start,
                int(ctx.initiation.get("mag_max_bonus") or 0),
                int(ctx.submersion.get("res_max_bonus") or 0),
                special_floors=ctx.special_floors,
            ).items()
        },
        "source": ctx.meta.get("source"),
        # `<replaceattributes>`: whose ranges these are, when they are not
        # the metatype's own (Infected, Quadriplegic).
        "attributes_replaced_by": list(ctx.attr_replaced_by),
    }
    for key, drop in ctx.special_max_drop.items():
        row = info["attributes"].get(key)
        if drop > 0 and row is not None:
            # where essence loss leaves the range; the slider stays on what
            # was bought, so these sit beside it rather than replacing it
            row["ess_min"] = max(0, int(row["min"]) - ctx.special_min_drop.get(key, 0))
            row["ess_max"] = max(0, int(row["max"]) - drop)
    form = metahuman_form(ctx)
    if form is not None:
        info["metahuman_form"] = form
        info["animal_form"] = animal_form(ctx, ctx.animal_movement) or {}
        info["active_form"] = ctx.state.shapeshifter_form
    if ctx.meta.get("power_grants"):
        info["powers"] = [
            {
                key: power.get(key) or ""
                for key in (
                    "id",
                    "name",
                    "type",
                    "action",
                    "range",
                    "duration",
                    "source",
                    "page",
                    "select",
                    "rating",
                    "origin",
                    "origin_id",
                    "origin_name",
                )
            }
            for power in ctx.meta["power_grants"]
        ]
    return info
