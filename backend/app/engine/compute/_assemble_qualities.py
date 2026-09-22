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
from ..qualities import _quality_has_selectside, quality_needs_extra
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
) -> dict[str, dict[str, int | float]]:
    out = {key: dict(spec) for key, spec in attrs_spec.items()}
    if special_key == "MAG":
        out["MAG"]["min"] = max(talent_start, 1)
        out["MAG"]["max"] = int(out["MAG"].get("max") or 0) + max(0, int(mag_max_bonus))
        out["RES"]["min"] = 0
        out["RES"]["max"] = 0
    elif special_key == "RES":
        out["RES"]["min"] = max(talent_start, 1)
        out["RES"]["max"] = int(out["RES"].get("max") or 0) + max(0, int(res_max_bonus))
        out["MAG"]["min"] = 0
        out["MAG"]["max"] = 0
    else:
        out["MAG"]["min"] = 0
        out["MAG"]["max"] = 0
        out["RES"]["min"] = 0
        out["RES"]["max"] = 0
    return out


def quality_rows(ctx: Ctx) -> list[dict[str, Any]]:
    """``derived["qualities"]``: one row per taken quality, in order."""
    return [
        {
            "id": q["id"],
            "name": q["name"],
            "karma": 0 if q["id"] in ctx.free_quality_ids else q["karma"],
            "category": q["category"],
            "source": q["source"],
            "needs_extra": quality_needs_extra(q),
            "extra": ctx.state.quality_extras.get(q["id"]) or "",
            "spirit_extra": ctx.state.quality_extras.get(quality_spirit_category_extra_key(q["id"])) or "",
            "extra_kind": q.get("extra_kind"),
            "select_options": list(q.get("select_options") or []),
            "spirit_options": list(q.get("spirit_options") or []),
            "expertise_skill": q.get("expertise_skill") or "",
            "add_spirit_count": int(q.get("add_spirit_count") or 0),
            "selectside": _quality_has_selectside(q),
            "side": _normalize_side(ctx.state.quality_extras.get(q["id"])) if _quality_has_selectside(q) else None,
            "free": q["id"] in ctx.free_quality_ids or bool(q.get("onlyprioritygiven")),
            **_quality_critter_powers(q, ctx.state.quality_extras),
            # the table value, only when a `<costdiscount>` moved it
            **({"karma_base": q["karma_base"]} if q.get("karma_base") is not None else {}),
            **({"disabled_by": ctx.disabled_qualities[q["id"]]} if q["id"] in ctx.disabled_qualities else {}),
            # taken after chargen: what it cost then (SR5 p.107)
            **({"career_cost": cost} if (cost := _nth(ctx.quality_career_costs, idx)) is not None else {}),
        }
        for idx, q in enumerate(ctx.qualities)
    ]


def metatype_info(ctx: Ctx, clamped: set[str]) -> _MetatypeInfo:
    """``derived["metatype_info"]``: the metatype's attribute ranges after
    talent, initiation / submersion and `<attributemaxclamp>`."""
    return {
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
            ).items()
        },
        "source": ctx.meta.get("source"),
        # `<replaceattributes>`: whose ranges these are, when they are not
        # the metatype's own (Infected, Quadriplegic).
        "attributes_replaced_by": list(ctx.attr_replaced_by),
    }
