"""'ware rating bounds and formula-driven rating ranges.

Leaf of the ``engine/ware/`` package: ``ware_rating_bounds`` /
``_clamp_ware_rating`` feed ``ware/resolve.py`` and ``ware/sides.py``, and
``ware_ranges`` is published in the ``compute`` derived block. Imports only
``catalog`` / ``eval_formula`` — never back into ``app.engine``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ...data_loader import catalog_ware, eval_formula


def racial_formula_extras(attrs_spec: dict[str, dict[str, int | float]]) -> dict[str, int]:
    extras: dict[str, int] = {}
    for key, spec in attrs_spec.items():
        extras[f"{key}Minimum"] = int(spec.get("min") or 1)
        extras[f"{key}Maximum"] = int(spec.get("max") or 6)
    return extras


def ware_rating_bounds(
    ware: dict[str, Any],
    extras: Mapping[str, float] | None = None,
) -> tuple[int, int]:
    extras = extras or {}
    lo = int(eval_formula(ware.get("minrating_expr") or str(ware.get("minrating") or 1), 1, default=1, extras=extras))
    hi = int(eval_formula(ware.get("maxrating_expr") or str(ware.get("maxrating") or 1), 1, default=1, extras=extras))
    if hi < lo:
        hi = lo
    return lo, hi


def _clamp_ware_rating(ware: dict[str, Any], rating: int, extras: Mapping[str, float] | None = None) -> int:
    lo, hi = ware_rating_bounds(ware, extras)
    return max(lo, min(hi, int(rating or lo)))


def ware_ranges(attrs_spec: dict[str, dict[str, int | float]]) -> dict[str, dict[str, int]]:
    extras = racial_formula_extras(attrs_spec)
    out: dict[str, dict[str, int]] = {}
    for kind in ("cyberware", "bioware"):
        for ware in catalog_ware(kind).get("items") or []:
            if not ware.get("formula_rating"):
                continue
            lo, hi = ware_rating_bounds(ware, extras)
            out[ware["id"]] = {"min": lo, "max": hi}
    return out
