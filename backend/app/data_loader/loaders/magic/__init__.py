"""Awakened and Emerged catalog loaders, split the way the rules are.

One 606-line module became four along the lines the game already draws:
`powers` (adept), `spells` (magician), `foci` (what an initiation grade buys)
and `resonance` (technomancer — where a stream is a tradition, a sprite a
spirit, an echo a metamagic). The same split as `engine/magic/`, so a loader
and the rules that consume it are found under the same name.
"""

from __future__ import annotations

from .foci import load_foci, load_focus_formulae, load_magic_arts, load_metamagics
from .powers import load_enhancements, load_mentors, load_powers, load_qi_focus
from .resonance import load_complex_forms, load_echoes, load_sprites, load_streams
from .spells import (
    SPELL_CAST_CATEGORIES,
    SPELL_CATEGORIES,
    load_spells,
    load_spirits,
    load_traditions,
    spell_kind,
)

__all__ = [
    "SPELL_CAST_CATEGORIES",
    "SPELL_CATEGORIES",
    "load_complex_forms",
    "load_echoes",
    "load_enhancements",
    "load_foci",
    "load_focus_formulae",
    "load_magic_arts",
    "load_mentors",
    "load_metamagics",
    "load_powers",
    "load_qi_focus",
    "load_spells",
    "load_spirits",
    "load_sprites",
    "load_streams",
    "load_traditions",
    "spell_kind",
]
