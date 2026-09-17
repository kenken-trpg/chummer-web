"""Lifestyle resolution: monthly cost, the LP budget, lifestyle qualities
(freegrids + user picks + cost multipliers) and the post-resolve
lifestyle-cost-modifier bonus.

The last gear category ``resolve_gear`` drives inline — now its own module
like every sibling. Imports only ``catalog`` (``..data_loader``),
``_item_by_id`` (``..lookups``), ``GearBundle`` (``..bundle_types``, a leaf)
and models — never back into ``app.engine``.
"""

from __future__ import annotations

from typing import Any

from ...data_loader import catalog
from ...models import CharacterState, LifestyleInstall
from ...notices import Notice, notice, term
from ..bundle_types import GearBundle
from ..lookups import _item_by_id


def _resolve_one_lifestyle(
    inst: LifestyleInstall,
    spec: dict[str, Any],
    quality_specs: dict[str, dict[str, Any]],
    quality_by_name: dict[str, dict[str, Any]],
    warnings: list[Notice],
    bonus_sources: list[tuple[str, list[dict[str, Any]]]],
) -> tuple[dict[str, Any], int]:
    """Resolve one lifestyle install → (public row, monthly * months cost).

    Mutates ``inst`` (months clamp + persisted quality picks).
    """
    months = max(1, int(inst.months or 1))
    inst.months = months
    lifestyle_name = str(spec.get("name") or "")
    base_monthly = int(spec.get("cost") or 0)
    lp_max = int(spec.get("lp") or 0)
    quality_ids = list(inst.quality_ids or [])
    extras = dict(inst.quality_extras or {})

    kept_qualities: list[dict[str, Any]] = []
    seen_quality: set[str] = set()
    lp_used = 0
    quality_monthly = 0.0
    multiplier_pct = 0

    def _append_lifestyle_quality(
        qid: str,
        *,
        extra: str = "",
        from_freegrid: bool = False,
    ) -> None:
        nonlocal lp_used, quality_monthly, multiplier_pct
        qspec = quality_specs.get(qid)
        if not qspec:
            return
        if qid in seen_quality and not qspec.get("allow_multiple"):
            return
        seen_quality.add(qid)
        # `<allowed>` (Chummer's `AllowedFreeLifestyles`) is not a list of the
        # only lifestyles that may take the quality — a Low lifestyle buys a
        # Grid Subscription at its price — but of those where it takes no
        # LP (`LPFree`). It is still paid for in nuyen unless the player
        # chose to spend LP on it instead, which Chummer's default is not.
        # Only the lifestyle's own built-in qualities cost nothing.
        allowed = [str(name) for name in (qspec.get("allowed") or [])]
        free = bool(from_freegrid)
        lp_cost = 0 if free or lifestyle_name in allowed else int(qspec.get("lp") or 0)
        lp_used += lp_cost
        add_cost = 0 if free else float(qspec.get("cost") or 0)
        quality_monthly += add_cost
        multiplier_pct += int(qspec.get("multiplier") or 0)
        extra_val = str(extra or extras.get(qid) or "").strip()
        if qspec.get("needs_extra") and not extra_val:
            warnings.append(notice("engine.gear.pickExtra", name=term(str(qspec["name"]))))
        nodes = list(qspec.get("bonus") or [])
        bonus_nodes = [node for node in nodes if node.get("tag") != "selecttext"]
        if bonus_nodes:
            bonus_sources.append((f"{lifestyle_name}:{qspec['name']}", bonus_nodes))
        kept_qualities.append(
            {
                "id": f"{qid}:{len(kept_qualities)}",
                "quality_id": qid,
                "name": qspec["name"],
                "category": qspec.get("category") or "",
                "lp": lp_cost,
                "cost": add_cost,
                "free": free,
                "from_freegrid": from_freegrid,
                "multiplier": int(qspec.get("multiplier") or 0),
                "base_multiplier": int(qspec.get("base_multiplier") or 0),
                "extra": extra_val,
                "needs_extra": bool(qspec.get("needs_extra")),
                "source": qspec.get("source") or "",
                "page": qspec.get("page") or "",
            }
        )

    # Freegrids are always derived from the lifestyle (may repeat with different selects).
    for grid in spec.get("freegrids") or []:
        grid_name = str(grid.get("name") or "Grid Subscription")
        grid_spec = quality_by_name.get(grid_name)
        if not grid_spec:
            continue
        # allow_multiple freegrids share one quality id; clear seen for each instance.
        if grid_spec.get("allow_multiple"):
            seen_quality.discard(grid_spec["id"])
        _append_lifestyle_quality(
            grid_spec["id"],
            extra=str(grid.get("select") or "").strip(),
            from_freegrid=True,
        )

    for qid in quality_ids:
        _append_lifestyle_quality(qid)

    raise_max = dict(spec.get("raise_max") or {})
    raised: dict[str, int] = {}
    for key in ("comforts", "area", "security"):
        value = max(0, min(int(getattr(inst, key) or 0), int(raise_max.get(key, 0))))
        setattr(inst, key, value)
        raised[key] = value
    # every point raised is a point of LP (Chummer's `TotalLP`)
    lp_used += sum(raised.values())
    if lp_max > 0 and lp_used > lp_max:
        warnings.append(notice("engine.gear.lifestylePointsOver", name=term(lifestyle_name), used=lp_used, max=lp_max))
    pre_mod, after_mod = _monthly_cost_parts(
        base_monthly,
        [row for row in kept_qualities if not row.get("from_freegrid")],
        raised=raised,
        cost_for={key: int(spec.get(f"cost_for_{key}") or 0) for key in raised},
    )
    monthly = int(round(pre_mod + after_mod))
    cost = monthly * months
    # Persist user picks only; freegrids are re-derived each compute.
    inst.quality_ids = [row["quality_id"] for row in kept_qualities if not row.get("from_freegrid")]
    inst.quality_extras = {
        row["quality_id"]: row["extra"] for row in kept_qualities if row.get("extra") and not row.get("from_freegrid")
    }
    row = {
        "id": inst.id,
        "lifestyle_id": spec["id"],
        "name": lifestyle_name,
        "months": months,
        "increment": spec.get("increment") or "month",
        "monthly": monthly,
        "base_monthly": base_monthly,
        "quality_monthly": round(quality_monthly, 2),
        "multiplier_pct": multiplier_pct,
        "nuyen": cost,
        # the two halves a character's `<lifestylecost>` splits: it scales the
        # first, not the outings, services and contracts in the second
        "_pre_mod": pre_mod,
        "_after_mod": after_mod,
        "lp_used": lp_used,
        "lp_max": lp_max,
        "raised": raised,
        "raise_max": {key: int(raise_max.get(key, 0)) for key in raised},
        "dice": int(spec.get("dice") or 0),
        "qualities": kept_qualities,
        "avail": spec.get("avail") or "",
        "source": spec.get("source") or "",
        "page": spec.get("page") or "",
    }
    return row, cost


def _monthly_cost_parts(
    base: int,
    qualities: list[dict[str, Any]],
    *,
    raised: dict[str, int] | None = None,
    cost_for: dict[str, int] | None = None,
) -> tuple[float, float]:
    """A lifestyle's monthly cost the way Chummer works it out
    (`Lifestyle.CostPreSplit` / `GetTotalMonthlyCost`, after HT p.139).

    Multipliers compound rather than add, and apply stage by stage: a quality's
    base multiplier on the base cost; then the entertainment assets, their
    multipliers on everything so far and their prices after; then every other
    quality that is neither entertainment nor a contract (Cramped, Dangerous
    Area, Safehouse) the same way, floored at zero; then services and
    outings; contracts are added last, untouched. A lifestyle's own built-in
    qualities (its free Grid Subscription) take no part.
    """

    def kind(row: dict[str, Any]) -> str:
        category = str(row.get("category") or "")
        if category == "Contracts":
            return "contract"
        if category.startswith("Entertainment"):
            return "asset" if "Asset" in category else "outing"
        return "other"

    def stage(cost: float, rows: list[dict[str, Any]]) -> float:
        for row in rows:
            cost *= 1 + int(row.get("multiplier") or 0) / 100
        return cost + sum(float(row.get("cost") or 0) for row in rows)

    cost = float(base)
    for row in qualities:
        cost *= 1 + int(row.get("base_multiplier") or 0) / 100
    # each raised point of Comforts / Neighborhood / Security: +10% and its price
    points = raised or {}
    cost *= 1 + 0.1 * sum(points.values())
    cost += sum(int(points[key]) * int((cost_for or {}).get(key, 0)) for key in points)
    cost = stage(cost, [row for row in qualities if kind(row) == "asset"])
    cost = max(0.0, stage(cost, [row for row in qualities if kind(row) == "other"]))
    # Here Chummer applies the character's own `<lifestylecost>` (a troll's
    # +100%), which is why the rest is returned apart.
    outings = [row for row in qualities if kind(row) == "outing"]
    factor = 1.0
    for row in outings:
        factor *= 1 + int(row.get("multiplier") or 0) / 100
    after = sum(float(row.get("cost") or 0) for row in outings)
    after += sum(float(row.get("cost") or 0) for row in qualities if kind(row) == "contract")
    return cost * factor, after


def resolve_lifestyles(
    state: CharacterState,
) -> tuple[list[dict[str, Any]], int, list[Notice], list[tuple[str, list[dict[str, Any]]]]]:
    """Resolve every lifestyle install → (rows, total nuyen, warnings, bonus_sources).

    Sets ``state.lifestyles`` to the kept installs (matches the in-place
    mutation ``resolve_gear`` did before the extraction).
    """
    quality_specs = {item["id"]: item for item in catalog().get("lifestyle_qualities") or []}
    quality_by_name = {item["name"]: item for item in quality_specs.values()}
    kept_lifestyles: list[LifestyleInstall] = []
    rows: list[dict[str, Any]] = []
    nuyen = 0
    warnings: list[Notice] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    for inst in state.lifestyles:
        spec = _item_by_id("lifestyles", inst.lifestyle_id)
        if not spec:
            continue
        row, cost = _resolve_one_lifestyle(inst, spec, quality_specs, quality_by_name, warnings, bonus_sources)
        nuyen += cost
        kept_lifestyles.append(inst)
        rows.append(row)
    state.lifestyles = kept_lifestyles
    return rows, nuyen, warnings, bonus_sources


def lifestyle_cost_factor(mods: list[dict[str, Any]], metatype_sources: set[str]) -> float:
    """Chummer's `Lifestyle.GetTotalMonthlyCost`: a Dependents quality's
    percentages add up, so do the metatype's, and every other one compounds —
    +10%, -10% and -10% make 0.891, not 0.9."""
    dependents = sum(int(m["value"]) for m in mods if "Dependent" in str(m.get("source") or ""))
    metatype = sum(
        int(m["value"])
        for m in mods
        if "Dependent" not in str(m.get("source") or "") and str(m.get("source") or "") in metatype_sources
    )
    factor = (1 + dependents / 100) * (1 + metatype / 100)
    for m in mods:
        source = str(m.get("source") or "")
        if "Dependent" not in source and source not in metatype_sources:
            factor *= 1 + int(m["value"]) / 100
    return factor


def apply_lifestyle_cost_mod(gear: GearBundle, percent: int, factor: float | None = None) -> None:
    """Scale every lifestyle by the character's `<lifestylecost>` total.

    ``factor`` is the compounded multiplier (`lifestyle_cost_factor`);
    ``percent`` is only the summed figure the sheet shows."""
    if factor is None:
        factor = (100 + int(percent)) / 100.0
    if factor == 1.0:
        return
    delta = 0
    for row in gear.get("lifestyles") or []:
        before = int(row.get("nuyen") or 0)
        months = int(row.get("months") or 1)
        pre = float(row.get("_pre_mod") or 0.0)
        post = float(row.get("_after_mod") or 0.0)
        monthly = int(round(max(0.0, pre * factor) + post))
        after = monthly * months
        row["monthly"] = monthly
        row["nuyen"] = after
        row["lifestyle_cost_mod"] = int(percent)
        delta += after - before
    if gear.get("lifestyle") and (gear.get("lifestyles") or []):
        gear["lifestyle"] = (gear.get("lifestyles") or [])[0]
    gear["nuyen"] = int(gear.get("nuyen") or 0) + delta
    # the per-line tally has to move with the total, or the sidebar's breakdown
    # stops adding up to the money it is breaking down
    by_bucket = gear.get("nuyen_by_bucket")
    if by_bucket is not None:
        by_bucket["lifestyles"] = int(by_bucket.get("lifestyles") or 0) + delta
