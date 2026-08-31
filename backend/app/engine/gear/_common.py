"""Primitives shared across the gear resolvers.

Kept tiny and dependency-light (``eval_formula`` + the ``GearInstall`` model)
so every ``gear/`` submodule and ``app.engine`` itself can import them without a
cycle.
"""

from __future__ import annotations

from typing import Any

from ...data_loader import eval_formula
from ...models import GearInstall

SENSOR_DEVICE_CATEGORIES = {"Sensors"}


def _capacity_value(expr: str | None, rating: int) -> float:
    raw = (expr or "").strip()
    if not raw or raw == "*":
        return 0.0
    if "/" in raw:
        raw = raw.split("/", 1)[0].strip()
    return eval_formula(raw, rating, default=0.0)


def _cascade_optics(items: list[GearInstall], extra_parents: set[str] | None = None) -> list[GearInstall]:
    """Drop installs whose ``parent_id`` points at something no longer present,
    repeating until the set is stable (a removed parent can orphan a chain)."""
    ids = {item.id for item in items} | set(extra_parents or [])
    keep = [item for item in items if not item.parent_id or item.parent_id in ids]
    if len(keep) == len(items):
        return keep
    return _cascade_optics(keep, extra_parents)


def _program_label(spec: dict[str, Any], extra: str | None) -> str:
    """Display name for a program / app / autosoft, folding the chosen ``extra``
    into any ``[Model]`` / ``[Weapon]`` placeholder in the catalog name."""
    name = str(spec.get("name") or "")
    extra = (extra or "").strip()
    if extra:
        for token in ("[Model]", "[Weapon]"):
            if token in name:
                return f"{name.replace(token, '').strip()} ({extra})"
        return f"{name} ({extra})"
    return name


def _clamp_rating(spec: dict[str, Any], rating: int) -> int:
    max_rating = int(spec.get("maxrating") or 0)
    if max_rating <= 0:
        return 1
    min_rating = max(1, int(spec.get("minrating") or 1))
    return max(min_rating, min(max_rating, int(rating or min_rating)))


def _device_rating_of(spec: dict[str, Any] | None, rating: int) -> int:
    raw = str((spec or {}).get("devicerating") or "").strip()
    if raw and raw not in {"0", "-"}:
        return max(0, int(eval_formula(raw, rating, 0)))
    if str((spec or {}).get("category") or "") in SENSOR_DEVICE_CATEGORIES:
        return max(0, int(rating or 0))
    return 0
