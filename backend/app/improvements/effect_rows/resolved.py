"""Row shapes produced by a ``bind_*`` in ``app/engine`` rather than by a
``<bonus>`` node — a pick already resolved against the character (group G6 of
``docs/plans/refactor-effect-rows-plan.md``)."""

from __future__ import annotations

from typing import TypedDict


class WeaponDvBonusRow(TypedDict):
    """``weapon_category_dv`` / ``weapon_skill_accuracy`` — a resolved
    (skill/category, bonus) pair, produced by ``bind_weapon_category_dv`` /
    ``bind_weapon_skill_accuracy`` from the matching ``*_slots`` picks."""

    name: str
    bonus: int
    source: str


class AddSpiritPickRow(TypedDict):
    """``add_spirit_picks`` — one resolved ``<addspirit>`` player pick, from
    ``bind_extra_spirits``; surfaced in the derived output."""

    quality_id: str
    quality_name: str
    index: int
    key: str
    value: str
    options: list[str]
    skill: str
