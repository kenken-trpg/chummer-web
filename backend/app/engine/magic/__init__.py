"""Awakened / Emerged resolution, split by concern.

Each submodule owns one cluster of the magic pipeline that ``app.engine.compute``
drives: mentor spirit, adept powers, foci, spirits, spells, initiation and
submersion. Submodules import only ``catalog`` / ``eval_formula`` /
already-extracted engine modules / models — never back into ``app.engine`` —
so the import graph stays a DAG.

``app.engine`` re-exports the public names these modules provide.
"""

from __future__ import annotations

from ._common import (
    _active_skill_rating_from_state,
    _magic_grade_discount,
    _spell_category_mod_total,
    _spell_descriptor_mod_total,
    _spell_descriptor_pattern_matches,
    _spell_descriptor_tokens,
    spell_cast_info,
    spell_drain_value,
    tradition_resist,
)

__all__ = [
    "_active_skill_rating_from_state",
    "_magic_grade_discount",
    "_spell_category_mod_total",
    "_spell_descriptor_mod_total",
    "_spell_descriptor_pattern_matches",
    "_spell_descriptor_tokens",
    "spell_cast_info",
    "spell_drain_value",
    "tradition_resist",
]
