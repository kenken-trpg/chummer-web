"""Per-domain vendored-XML loaders. Each ``load_*`` parses one file into a
``list[dict]`` / ``dict``; cross-entity wiring stays in ``data_loader.catalog``.
"""

from __future__ import annotations

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
from .ware import load_bioware, load_cyberware

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
]
