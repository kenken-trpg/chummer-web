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
from .foci import (
    apply_focus_limits,
    attach_focus_tests,
    attach_weapon_focus_dice,
    focus_bind_karma,
    qi_focus_granted_power_rating,
    resolve_foci,
    resolve_qi_foci,
)
from .mentor import resolve_mentor
from .powers import (
    bind_power_bonus,
    power_max_rating,
    power_point_cost,
    power_select_options,
    resolve_adept_powers,
    way_discount_cap,
    way_discount_eligible,
)
from .spells import (
    apply_granted_spells,
    apply_tradition_bonuses,
    bind_spell_category_drain_damage,
    bind_spell_spirit_limits,
    free_spell_bonus_points,
    resolve_spells,
    spell_defense_pools,
    spell_karma_cost,
)
from .spirits import (
    addspirit_option_names,
    attach_spirit_tests,
    bind_extra_spirits,
    resolve_spirits,
    spirit_attributes,
)

__all__ = [
    "_active_skill_rating_from_state",
    "_magic_grade_discount",
    "_spell_category_mod_total",
    "_spell_descriptor_mod_total",
    "_spell_descriptor_pattern_matches",
    "_spell_descriptor_tokens",
    "addspirit_option_names",
    "apply_focus_limits",
    "apply_granted_spells",
    "apply_tradition_bonuses",
    "attach_focus_tests",
    "attach_spirit_tests",
    "attach_weapon_focus_dice",
    "bind_extra_spirits",
    "bind_power_bonus",
    "bind_spell_category_drain_damage",
    "bind_spell_spirit_limits",
    "focus_bind_karma",
    "free_spell_bonus_points",
    "power_max_rating",
    "power_point_cost",
    "power_select_options",
    "qi_focus_granted_power_rating",
    "resolve_adept_powers",
    "resolve_foci",
    "resolve_mentor",
    "resolve_qi_foci",
    "resolve_spells",
    "resolve_spirits",
    "spell_cast_info",
    "spell_defense_pools",
    "spell_drain_value",
    "spell_karma_cost",
    "spirit_attributes",
    "tradition_resist",
    "way_discount_cap",
    "way_discount_eligible",
]
