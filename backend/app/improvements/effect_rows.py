"""``TypedDict`` shapes for the row dicts inside ``EffectsDict``'s list values.

``EffectsDict`` (``effects.py``) fixed the ~134 keys; this module fixes the
shape of the rows in its ``*_mods`` / ``*_slots`` / ``grant_*`` / cost-rule
lists, so ``row.get("nam")`` (typo) is a ``mypy`` error too. Each row is
produced by exactly one ``improvements/nodes/<domain>.py`` branch (or, for a
few, a ``bind_*`` in ``app/engine``) and read by a handful of engine
consumers via string-literal keys.

Imports only ``typing`` — ``effects.py`` imports from here, nothing imports
back, so the ``improvements`` package stays a DAG. See
``docs/refactor-effect-rows-plan.md``.
"""

from __future__ import annotations

from typing import TypedDict


class KarmaCostRow(TypedDict):
    """``active_skill_karma_cost`` / ``knowledge_skill_karma_cost`` /
    ``knowledge_skill_karma_cost_min`` / ``skill_category_karma_cost`` — a
    ``<karmacost>`` flat/min rule for one skill or category."""

    name: str
    val: int
    min: int
    max: int | None
    condition: str


class KarmaMultRow(TypedDict):
    """``skill_category_karma_cost_mult`` /
    ``skill_category_spec_karma_cost_mult`` /
    ``skill_group_category_karma_cost_mult`` — a percentage karma multiplier
    for one skill category (``val`` is a percent, default 100)."""

    name: str
    val: int
    condition: str


class SkillModRow(TypedDict):
    """``skill_group_mods`` / ``skill_category_mods`` — a dice bonus to a
    named skill group / category, with an optional excluded skill."""

    name: str
    bonus: int
    exclude: str
    condition: str
    source: str


class NamedBonusRow(TypedDict):
    """``skill_specific_mods`` / ``skill_attribute_mods`` /
    ``spell_category_mods`` — a dice bonus keyed by a name (skill / attribute
    / spell category)."""

    name: str
    bonus: int
    condition: str
    source: str
