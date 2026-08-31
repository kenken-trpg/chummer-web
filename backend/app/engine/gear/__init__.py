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
    _default_mount_parts,
    _device_rating_of,
    _find_mount_part,
    _has_weapon_constraints,
    _leading_vehicle_stat,
    _limb_attr_effect,
    _pick_accessory_mount,
    _program_label,
    _weapon_matches_or,
    accessory_fits_weapon,
)
from .ammo import _apply_loaded_ammo, _pick_loaded_ammo, ammo_fits_weapon
from .apps import _resolve_apps
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
from .programs import _resolve_programs
from .sensors import _resolve_sensors
from .weapons import (
    _append_gear_weapons,
    _append_ware_weapons,
    _apply_recoil_totals,
    _public_weapon,
    _resolve_weapon_accessories,
    apply_reach_bonus,
    apply_unarmed_bonuses,
    apply_weapon_category_dv,
    apply_weapon_skill_accuracy,
    bind_weapon_category_dv,
    bind_weapon_skill_accuracy,
)

__all__ = [
    "_DRUG_CATEGORIES",
    "_append_gear_weapons",
    "_append_ware_weapons",
    "_apply_loaded_ammo",
    "_apply_recoil_totals",
    "_capacity_value",
    "_cascade_optics",
    "_clamp_rating",
    "_default_mount_parts",
    "_device_rating_of",
    "_drug_effect_nodes",
    "_find_mount_part",
    "_format_drug_duration",
    "_has_weapon_constraints",
    "_leading_vehicle_stat",
    "_limb_attr_effect",
    "_pick_accessory_mount",
    "_pick_loaded_ammo",
    "_matrix_stats",
    "_normalize_array_order",
    "_program_label",
    "_public_weapon",
    "_recompute_worn_armor",
    "_resolve_apps",
    "_resolve_armor_mods",
    "_resolve_matrix_devices",
    "_resolve_optics",
    "_resolve_programs",
    "_resolve_sensors",
    "_resolve_weapon_accessories",
    "_weapon_matches_or",
    "accessory_fits_weapon",
    "ammo_fits_weapon",
    "apply_active_drugs",
    "apply_reach_bonus",
    "apply_unarmed_bonuses",
    "apply_weapon_category_dv",
    "apply_weapon_skill_accuracy",
    "armor_mod_fits",
    "armor_plugin_capacity",
    "bind_weapon_category_dv",
    "bind_weapon_skill_accuracy",
]
