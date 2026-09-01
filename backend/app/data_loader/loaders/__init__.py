"""Per-domain vendored-XML loaders. Each ``load_*`` parses one file into a
``list[dict]`` / ``dict``; cross-entity wiring stays in ``data_loader.catalog``.
"""

from __future__ import annotations

from .armor import load_armor, load_armor_mods
from .drugs import drug_effect_summary, drug_node_value, load_drug_components, load_drug_grades
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
from .lifestyle import load_lifestyle_qualities, load_lifestyles
from .magic import (
    SPELL_CAST_CATEGORIES,
    SPELL_CATEGORIES,
    load_complex_forms,
    load_echoes,
    load_enhancements,
    load_foci,
    load_magic_arts,
    load_mentors,
    load_metamagics,
    load_powers,
    load_qi_focus,
    load_spells,
    load_spirits,
    load_sprites,
    load_streams,
    load_traditions,
)
from .martial_arts import load_martial_art_techniques, load_martial_arts
from .metatypes import load_metatypes
from .priorities import load_priorities
from .qualities import load_qualities
from .skills import load_skills
from .translations import _load_ja_overrides, load_translations, load_ui_strings
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
    "_load_ja_overrides",
    "drug_effect_summary",
    "drug_node_value",
    "load_drug_components",
    "load_drug_grades",
    "load_echoes",
    "load_lifestyle_qualities",
    "load_lifestyles",
    "load_magic_arts",
    "load_martial_art_techniques",
    "load_martial_arts",
    "load_metamagics",
    "load_priorities",
    "load_qi_focus",
    "load_translations",
    "load_ui_strings",
]
