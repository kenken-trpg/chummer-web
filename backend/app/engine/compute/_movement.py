"""Movement: the metatype's Ground / Swim / Fly rates, worked out the way
Chummer's CalculatedMovement does.

Its own module so that `_shapeshifter` (a metahuman form moves at its own
rates) and `finalize` (which settles the body's movement and asks
`_shapeshifter` about the form) can both use it without importing each other.
"""

from __future__ import annotations

from typing import Any

from ...improvements import EffectsDict
from ..bundle_types import MovementBundle, MovementModeBundle


def _movement_rate(rates: str, index: int) -> float:
    """One component of the metatype's Ground/Swim/Fly rate string."""
    parts = str(rates or "").split("/")
    try:
        return float(parts[index].strip())
    except (ValueError, IndexError):
        return 0.0


def _metres(value: float) -> str:
    """Chummer's `#,0.##`: at most two decimals, no trailing zeros."""
    return f"{round(value, 2):.2f}".rstrip("0").rstrip(".") or "0"


def _resolve_movement_mode(
    meta: dict[str, Any], effects: EffectsDict, category: str, index: int, attribute: float
) -> MovementModeBundle:
    """Chummer's CalculatedMovement rates and category-specific bonuses:
    (rate + multiplier) × (1 + percent) × AGI for walking and running, and
    rate + bonus / 100, scaled by its percent, for sprinting."""
    replace = effects.get("movement_replace") or {}

    def rate(kind: str, default: str) -> float:
        if (category, kind) in replace:
            return float(replace[(category, kind)])
        return _movement_rate(str(meta.get(kind) or default), index)

    rates = {kind: rate(kind, default) for kind, default in (("walk", "2/1/0"), ("run", "4/0/0"), ("sprint", "2/1/0"))}

    def pct(key: str) -> float:
        return 1.0 + int((effects.get(key) or {}).get(category) or 0) / 100.0  # type: ignore[attr-defined]

    walk = (rates["walk"] + int((effects.get("walk_multiplier") or {}).get(category) or 0)) * pct(
        "walk_multiplier_percent"
    )
    run = (rates["run"] + int((effects.get("run_multiplier") or {}).get(category) or 0)) * pct("run_multiplier_percent")
    sprint_bonus = int((effects.get("sprint_bonus") or {}).get(category) or 0)
    sprint = (rates["sprint"] + sprint_bonus / 100.0) * pct("sprint_bonus_percent")
    return {
        "rates": rates,
        "available": any(value != 0 for value in (walk, run, sprint)),
        "walk": _metres(walk * attribute),
        "run": _metres(run * attribute),
        "sprint": _metres(sprint),
        "sprint_bonus": sprint_bonus,
    }


def resolve_movement(
    meta: dict[str, Any],
    effects: EffectsDict,
    agi: int,
    *,
    swim_agi: int | None = None,
    swim_str: int | None = None,
    ground_agi: int | None = None,
) -> MovementBundle:
    """Ground/Fly use meat AGI, Swim uses the limb-inclusive (AGI+STR)/2.

    Only Ground can opt into cyberleg AGI. The old top-level fields remain
    a projection of Ground for saved clients and existing export consumers.
    """
    meat_agi = max(0, int(agi))
    swim_attribute = (
        max(0, swim_agi if swim_agi is not None else agi) + max(0, swim_str if swim_str is not None else agi)
    ) / 2
    modes = {
        "Ground": _resolve_movement_mode(
            meta, effects, "Ground", 0, max(0, ground_agi) if ground_agi is not None else meat_agi
        ),
        "Swim": _resolve_movement_mode(meta, effects, "Swim", 1, swim_attribute),
        "Fly": _resolve_movement_mode(meta, effects, "Fly", 2, meat_agi),
    }
    ground = modes["Ground"]
    return {
        "walk": ground["walk"],
        "run": ground["run"],
        "sprint": ground["sprint"],
        "sprint_bonus": ground["sprint_bonus"],
        "modes": modes,
    }
