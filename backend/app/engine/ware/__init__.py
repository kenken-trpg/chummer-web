"""Cyberware / bioware resolution, split by concern.

Each submodule owns one cluster of the 'ware pipeline that
``app.engine.compute`` drives: rating bounds, cyberlimb attributes /
redliner / Cyberseeker, limb sides, grades, subsystems, vehicle-hosted
'ware and required-'ware warnings. Submodules import only ``catalog`` /
``eval_formula`` / already-extracted engine modules / models — never back
into ``app.engine`` — so the import graph stays a DAG.

``app.engine`` re-exports the public names these modules provide.
"""

from __future__ import annotations

from .rating import (
    _clamp_ware_rating,
    racial_formula_extras,
    ware_ranges,
    ware_rating_bounds,
)

__all__ = [
    "_clamp_ware_rating",
    "racial_formula_extras",
    "ware_ranges",
    "ware_rating_bounds",
]
