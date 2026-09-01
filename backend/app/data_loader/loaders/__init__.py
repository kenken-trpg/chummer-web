"""Per-domain vendored-XML loaders. Each ``load_*`` parses one file into a
``list[dict]`` / ``dict``; cross-entity wiring stays in ``data_loader.catalog``.
"""

from __future__ import annotations

from .metatypes import load_metatypes
from .qualities import load_qualities
from .skills import load_skills
from .ware import load_bioware, load_cyberware

__all__ = [
    "load_bioware",
    "load_cyberware",
    "load_metatypes",
    "load_qualities",
    "load_skills",
]
