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

from ._common import _cascade_orphans, _public_installed
from .limbs import (
    CYBERLIMB_BASE_ATTR,
    LIMB_BODY_PARTS,
    LIMB_BODY_SLOTS,
    REDLINER_BASE_SLOTS,
    _apply_limb_attributes,
    _is_body_limb,
    _is_full_limb,
    _is_redliner_limb,
    _limb_slot_count,
    apply_cyberseeker,
    count_redliner_limbs,
    limb_attribute_replace,
    redliner_incompat_warnings,
    redliner_slot_caps,
)
from .rating import (
    _clamp_ware_rating,
    racial_formula_extras,
    ware_ranges,
    ware_rating_bounds,
)
from .resolve import (
    _clamp_ware_grades,
    _ensure_kind_subsystems,
    _first_allowed_grade,
    _installed_ware_names,
    _required_warnings,
    ensure_subsystems,
    resolve_ware,
)
from .sides import (
    _next_free_side,
    _occupied_sides,
    _side_conflicts,
    ensure_sides,
)
from .vehicles import (
    _attach_ware_to_vehicle_mods,
    _drop_invalid_vehicle_ware,
    _vehicle_hosted_ware_ids,
    _vehicle_mod_hosts,
    _ware_fits_vehicle_mod,
    _zero_vehicle_hosted_essence,
)

__all__ = [
    "CYBERLIMB_BASE_ATTR",
    "LIMB_BODY_PARTS",
    "LIMB_BODY_SLOTS",
    "REDLINER_BASE_SLOTS",
    "_apply_limb_attributes",
    "_attach_ware_to_vehicle_mods",
    "_cascade_orphans",
    "_clamp_ware_grades",
    "_clamp_ware_rating",
    "_drop_invalid_vehicle_ware",
    "_ensure_kind_subsystems",
    "_first_allowed_grade",
    "_installed_ware_names",
    "_is_body_limb",
    "_is_full_limb",
    "_is_redliner_limb",
    "_limb_slot_count",
    "_next_free_side",
    "_occupied_sides",
    "_public_installed",
    "_required_warnings",
    "_side_conflicts",
    "_vehicle_hosted_ware_ids",
    "_vehicle_mod_hosts",
    "_ware_fits_vehicle_mod",
    "_zero_vehicle_hosted_essence",
    "apply_cyberseeker",
    "count_redliner_limbs",
    "ensure_sides",
    "ensure_subsystems",
    "limb_attribute_replace",
    "racial_formula_extras",
    "redliner_incompat_warnings",
    "redliner_slot_caps",
    "resolve_ware",
    "ware_ranges",
    "ware_rating_bounds",
]
