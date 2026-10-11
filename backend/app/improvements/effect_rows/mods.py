"""Row shapes for the karma-cost rules and the dice mods (groups G1 and G2 of
``docs/plans/refactor-effect-rows-plan.md``), plus the two rows that move an
attribute or its range."""

from __future__ import annotations

from typing import NotRequired, TypedDict


class KarmaCostRow(TypedDict):
    """``active_skill_karma_cost`` / ``knowledge_skill_karma_cost`` /
    ``knowledge_skill_karma_cost_min`` / ``skill_category_karma_cost`` /
    ``attribute_karma_cost`` — a ``<karmacost>`` flat/min rule for one skill,
    category or attribute."""

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


class AttributeRangeRow(TypedDict):
    """``attribute_replacements`` — ``<replaceattributes>``: the metatype's
    range for one attribute, replaced wholesale (the Infected qualities,
    Quadriplegic)."""

    min: int
    max: int
    aug: int
    source: str


class SkillAttributeSwapRow(TypedDict):
    """``skill_attribute_swaps`` — ``<swapskillattribute>`` /
    ``<swapskillspecattribute>``: the skill rolls off ``attribute`` instead of
    its printed one. ``spec`` is empty for a swap that always applies, and the
    specialization's name when only tests using it swap."""

    skill: str
    attribute: str
    spec: str
    source: str


class NamedBonusRow(TypedDict):
    """``skill_specific_mods`` / ``skill_attribute_mods`` /
    ``spell_category_mods`` — a dice bonus keyed by a name (skill / attribute
    / spell category)."""

    name: str
    bonus: int
    condition: str
    source: str
    #: ``skill_attribute_mods`` only: the row came from
    #: ``<skilllinkedattribute>``, so it reads the skill's *printed* attribute
    #: rather than the one a ``SkillAttributeSwapRow`` moved it to.
    linked: NotRequired[bool]
