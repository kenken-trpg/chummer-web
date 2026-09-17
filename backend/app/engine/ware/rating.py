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


#: Chummer's base Strength and Agility for any cyberlimb (`Cyberware._intMinStrength`
#: / `_intMinAgility`). A formula inside a limb reads `{STRMinimum}` /
#: `{AGIMinimum}` from the limb, not from the character, so Customized Agility
#: starts at 4 — and its `(Rating - MinRating + 1) * 5000` price with it.
LIMB_BASE_ATTRIBUTE = 3

#: `<category>` of the enhancements that only ever go into a cyberlimb.
LIMB_ENHANCEMENT_CATEGORY = "Cyberlimb Enhancement"


def is_limb(ware: Mapping[str, Any]) -> bool:
    """Chummer's `Category == "Cyberlimb" || IsLimb` (a non-empty limb slot)."""
    return ware.get("category") == "Cyberlimb" or bool(ware.get("limbslot"))


def limb_formula_extras(extras: Mapping[str, float]) -> dict[str, float]:
    """``extras`` as a formula inside a cyberlimb sees them."""
    return {**extras, "STRMinimum": LIMB_BASE_ATTRIBUTE, "AGIMinimum": LIMB_BASE_ATTRIBUTE}


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
            # The enhancements can only be installed in a limb, so their range
            # is the one they have there.
            in_limb = ware.get("category") == LIMB_ENHANCEMENT_CATEGORY or is_limb(ware)
            lo, hi = ware_rating_bounds(ware, limb_formula_extras(extras) if in_limb else extras)
            out[ware["id"]] = {"min": lo, "max": hi}
    return out
