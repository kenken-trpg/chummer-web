"""Per-domain vendored-XML loaders. Each ``load_*`` parses one file into a
``list[dict]`` / ``dict``; cross-entity wiring stays in ``data_loader.catalog``.
"""

from __future__ import annotations

from .armor import load_armor, load_armor_mods
from .gear import (
    PROGRAM_HOSTS,
    load_apps,
    load_commlinks,
    load_cyberdecks,
    load_gear,
    load_optics,
    load_programs,
    load_rccs,
    load_sensors,
)
from .magic import (
    SPELL_CAST_CATEGORIES,
    SPELL_CATEGORIES,
    load_complex_forms,
    load_enhancements,
    load_foci,
    load_mentors,
    load_powers,
    load_spells,
    load_spirits,
    load_sprites,
    load_streams,
    load_traditions,
)
from .metatypes import load_metatypes
from .qualities import load_qualities
from .skills import load_skills
from .vehicles import (
    load_drones,
    load_vehicle_mods,
    load_vehicle_names,
    load_vehicles,
    load_weapon_mounts,
)
from .ware import load_bioware, load_cyberware
from .weapons import load_weapon_accessories, load_weapon_ranges, load_weapons

__all__ = [
    "SPELL_CAST_CATEGORIES",
    "SPELL_CATEGORIES",
    "load_bioware",
    "load_complex_forms",
    "load_cyberware",
    "load_enhancements",
    "load_foci",
    "load_mentors",
    "load_powers",
    "load_metatypes",
    "load_qualities",
    "load_skills",
    "load_spells",
    "load_spirits",
    "load_sprites",
    "load_streams",
    "load_traditions",
    "PROGRAM_HOSTS",
    "load_apps",
    "load_armor",
    "load_armor_mods",
    "load_commlinks",
    "load_cyberdecks",
    "load_drones",
    "load_gear",
    "load_optics",
    "load_programs",
    "load_rccs",
    "load_sensors",
    "load_vehicle_mods",
    "load_vehicle_names",
    "load_vehicles",
    "load_weapon_accessories",
    "load_weapon_mounts",
    "load_weapon_ranges",
    "load_weapons",
]
