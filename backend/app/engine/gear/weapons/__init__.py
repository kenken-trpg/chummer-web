"""Weapon resolution, split by what each part does to a weapon row.

`rows` builds them (including the ones granted by gear, ware and drones),
`bonuses` modifies them once they exist, `accessories` resolves what is bolted
onto them and the recoil that follows. It was one 657-line module; the three
concerns never called into each other except through the row itself, which is
why it splits cleanly.

Imports only `catalog` / `eval_formula` / already-extracted engine modules /
models — never back into `app.engine`.
"""

from __future__ import annotations

from .accessories import _apply_recoil_totals, _resolve_weapon_accessories
from .bonuses import (
    apply_reach_bonus,
    apply_smartlink_accuracy,
    apply_unarmed_bonuses,
    apply_weapon_category_dice,
    apply_weapon_category_dv,
    apply_weapon_skill_accuracy,
    bind_weapon_category_dv,
    bind_weapon_skill_accuracy,
    weapon_skill_dictionary_key,
)
from .rows import _append_gear_weapons, _append_ware_weapons, _public_weapon

__all__ = [
    "_append_gear_weapons",
    "_append_ware_weapons",
    "_apply_recoil_totals",
    "_public_weapon",
    "_resolve_weapon_accessories",
    "apply_reach_bonus",
    "apply_smartlink_accuracy",
    "apply_unarmed_bonuses",
    "apply_weapon_category_dice",
    "apply_weapon_category_dv",
    "apply_weapon_skill_accuracy",
    "bind_weapon_category_dv",
    "bind_weapon_skill_accuracy",
    "weapon_skill_dictionary_key",
]
