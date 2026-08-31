"""Gear resolution, split by concern.

Each submodule owns one cohesive cluster of the (large) gear pipeline that
``app.engine.compute`` drives via ``resolve_gear``. Submodules import only
``catalog`` / engine ``constants`` / already-extracted engine modules / models —
never back into ``app.engine`` itself — so the import graph stays a DAG.

``app.engine`` re-exports the public names these modules provide.
"""

from __future__ import annotations

from ._common import (
    _capacity_value,
    _cascade_optics,
    _clamp_rating,
    _device_rating_of,
)
from .armor import (
    _recompute_worn_armor,
    _resolve_armor_mods,
    armor_mod_fits,
    armor_plugin_capacity,
)
from .drugs import (
    _DRUG_CATEGORIES,
    _drug_effect_nodes,
    _format_drug_duration,
    apply_active_drugs,
)
from .matrix import _matrix_stats, _normalize_array_order, _resolve_matrix_devices
from .optics import _resolve_optics

__all__ = [
    "_DRUG_CATEGORIES",
    "_capacity_value",
    "_cascade_optics",
    "_clamp_rating",
    "_device_rating_of",
    "_drug_effect_nodes",
    "_format_drug_duration",
    "_matrix_stats",
    "_normalize_array_order",
    "_recompute_worn_armor",
    "_resolve_armor_mods",
    "_resolve_matrix_devices",
    "_resolve_optics",
    "apply_active_drugs",
    "armor_mod_fits",
    "armor_plugin_capacity",
]
