"""Gear resolution, split by concern.

Each submodule owns one cohesive cluster of the (large) gear pipeline that
``app.engine.compute`` drives via ``resolve_gear``. Submodules import only
``catalog`` / engine ``constants`` / already-extracted engine modules / models —
never back into ``app.engine`` itself — so the import graph stays a DAG.

``app.engine`` re-exports the public names these modules provide.
"""

from __future__ import annotations

from ._common import _clamp_rating, _device_rating_of
from .drugs import (
    _DRUG_CATEGORIES,
    _drug_effect_nodes,
    _format_drug_duration,
    apply_active_drugs,
)
from .matrix import _matrix_stats, _normalize_array_order, _resolve_matrix_devices

__all__ = [
    "_DRUG_CATEGORIES",
    "_clamp_rating",
    "_device_rating_of",
    "_drug_effect_nodes",
    "_format_drug_duration",
    "_matrix_stats",
    "_normalize_array_order",
    "_resolve_matrix_devices",
    "apply_active_drugs",
]
