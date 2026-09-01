"""Lifestyle resolution: monthly cost, the LP budget, lifestyle qualities
(freegrids + user picks + cost multipliers) and the post-resolve
lifestyle-cost-modifier bonus.

The last gear category ``resolve_gear`` drives inline — now its own module
like every sibling. Imports only ``catalog`` (``..data_loader``),
``_item_by_id`` (``..lookups``) and models — never back into ``app.engine``.
"""

from __future__ import annotations

from typing import Any

from ...data_loader import catalog
from ...models import CharacterState, LifestyleInstall
from ..lookups import _item_by_id


def _resolve_one_lifestyle(
    inst: LifestyleInstall,
    spec: dict[str, Any],
    quality_specs: dict[str, dict[str, Any]],
    quality_by_name: dict[str, dict[str, Any]],
    warnings: list[str],
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
    quality_monthly = 0
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
        allowed = [str(name) for name in (qspec.get("allowed") or [])]
        free = bool(from_freegrid) or (bool(allowed) and lifestyle_name in allowed)
        if allowed and lifestyle_name not in allowed and not from_freegrid:
            warnings.append(f"{qspec['name']} は {lifestyle_name} では取得できません")
            return
        lp_cost = int(qspec.get("lp") or 0)
        lp_used += lp_cost
        add_cost = 0 if free else int(qspec.get("cost") or 0)
        quality_monthly += add_cost
        multiplier_pct += int(qspec.get("multiplier") or 0)
        extra_val = str(extra or extras.get(qid) or "").strip()
        if qspec.get("needs_extra") and not extra_val:
            warnings.append(f"{qspec['name']} の対象を入力してください")
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

    if lp_max > 0 and lp_used > lp_max:
        warnings.append(f"{lifestyle_name} のライフスタイルポイント超過（使用 {lp_used} / 上限 {lp_max}）")

    monthly = int(round(base_monthly * (100 + multiplier_pct) / 100.0)) + quality_monthly
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
        "quality_monthly": quality_monthly,
        "multiplier_pct": multiplier_pct,
        "nuyen": cost,
        "lp_used": lp_used,
        "lp_max": lp_max,
        "dice": int(spec.get("dice") or 0),
        "qualities": kept_qualities,
        "avail": spec.get("avail") or "",
        "source": spec.get("source") or "",
        "page": spec.get("page") or "",
    }
    return row, cost


def resolve_lifestyles(
    state: CharacterState,
) -> tuple[list[dict[str, Any]], int, list[str], list[tuple[str, list[dict[str, Any]]]]]:
    """Resolve every lifestyle install → (rows, total nuyen, warnings, bonus_sources).

    Sets ``state.lifestyles`` to the kept installs (matches the in-place
    mutation ``resolve_gear`` did before the extraction).
    """
    quality_specs = {item["id"]: item for item in catalog().get("lifestyle_qualities") or []}
    quality_by_name = {item["name"]: item for item in quality_specs.values()}
    kept_lifestyles: list[LifestyleInstall] = []
    rows: list[dict[str, Any]] = []
    nuyen = 0
    warnings: list[str] = []
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


def apply_lifestyle_cost_mod(gear: dict[str, Any], percent: int) -> None:
    if not percent:
        return
    factor = (100 + int(percent)) / 100.0
    delta = 0
    for row in gear.get("lifestyles") or []:
        before = int(row.get("nuyen") or 0)
        monthly = int(row.get("monthly") or 0)
        after = int(round(before * factor))
        row["monthly"] = int(round(monthly * factor))
        row["nuyen"] = after
        row["lifestyle_cost_mod"] = int(percent)
        delta += after - before
    if gear.get("lifestyle") and (gear.get("lifestyles") or []):
        gear["lifestyle"] = (gear.get("lifestyles") or [])[0]
    gear["nuyen"] = int(gear.get("nuyen") or 0) + delta
