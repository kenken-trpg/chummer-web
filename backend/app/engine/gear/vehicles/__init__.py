"""Vehicle & drone resolution: stat formatting, the vehicle/mod constraint
predicates, stat-bonus application, R5 mod-slot accounting, and the
``resolve_gear``-driven resolvers for drones, vehicle mods and weapon mounts.

Imports only ``catalog`` / ``eval_formula`` / already-extracted engine modules
/ models — never back into ``app.engine``.

It was one 624-line module, split by stage: `stats` and `slots` are the
shared helpers, `equipment`, `mods` and `drones` the resolvers.
"""

from __future__ import annotations

from .drones import _publish_drone_stats, _resolve_drones
from .equipment import _ensure_drone_equipment
from .mods import _resolve_vehicle_mods, _resolve_weapon_mounts
from .slots import (
    _add_vehicle_slot_use,
    _finalize_vehicle_slots,
    _iter_vehicle_hosts,
)
from .stats import (
    _apply_vehicle_bonus,
    _clamp_vehicle_rating,
    _format_vehicle_stat,
    _vehicle_extras,
    mod_fits_vehicle,
    vehicle_matches,
)

__all__ = [
    "_add_vehicle_slot_use",
    "_apply_vehicle_bonus",
    "_clamp_vehicle_rating",
    "_ensure_drone_equipment",
    "_finalize_vehicle_slots",
    "_format_vehicle_stat",
    "_iter_vehicle_hosts",
    "_publish_drone_stats",
    "_resolve_drones",
    "_resolve_vehicle_mods",
    "_resolve_weapon_mounts",
    "_vehicle_extras",
    "mod_fits_vehicle",
    "vehicle_matches",
]
