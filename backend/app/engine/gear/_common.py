"""Primitives shared across the gear resolvers.

Kept tiny and dependency-free (only ``eval_formula``) so every ``gear/``
submodule and ``app.engine`` itself can import them without a cycle.
"""

from __future__ import annotations

from typing import Any

from ...data_loader import eval_formula

SENSOR_DEVICE_CATEGORIES = {"Sensors"}


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
