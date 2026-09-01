"""``TypedDict`` shapes for the ``Ctx`` bundle fields.

Each phase resolver in ``app/engine`` returns one of these; the matching
``Ctx`` field (``app/engine/compute/context.py``) is annotated with it, so a
mistyped key or wrong value type at a phase seam is a ``mypy`` error.

This module imports nothing from ``app.engine`` — it sits below every engine
module so both the resolvers and ``context.py`` can import it without a
cycle. Nested "public" row lists stay ``list[dict[str, Any]]``; typing those
is out of scope (see ``docs/refactor-ctx-bundles-plan.md``).
"""

from __future__ import annotations

from typing import Any, TypedDict

# One (source_label, bonus_nodes) pair — the element type of every
# ``bonus_sources`` list a resolver hands back for the effects pass.
BonusSource = tuple[str, list[dict[str, Any]]]


class SkillMods(TypedDict):
    """``resolve_skill_mods`` — skill / group / category dice modifiers."""

    skill_bonus: dict[str, int]
    skill_group_bonus: dict[str, int]
    skill_category_bonus: dict[str, int]
    skill_bonus_notes: dict[str, list[str]]


class SkillPicks(TypedDict):
    """``resolve_skill_picks`` — ``<selectskill>`` slots and their bonuses."""

    slots: list[dict[str, Any]]
    warnings: list[str]
    skill_max_bonus: dict[str, int]
    skill_bonus: dict[str, int]
    skill_bonus_notes: dict[str, list[str]]


class ContactsBundle(TypedDict):
    """``resolve_contacts`` — the contact network + point / karma accounting."""

    warnings: list[str]
    public: list[dict[str, Any]]
    used: int
    free: int
    paid: int
    karma: int
    karma_per_point: int


class MartialBundle(TypedDict):
    """``resolve_martial_arts`` — styles, techniques, their karma + spec extras."""

    warnings: list[str]
    public: list[dict[str, Any]]
    karma: int
    style_count: int
    technique_count: int
    style_max: int
    technique_max: int
    spec_extras: dict[str, list[str]]
    bonus_sources: list[BonusSource]


class MovementBundle(TypedDict):
    """``resolve_movement`` — the walk / run / sprint rate strings."""

    walk: str
    run: str
    sprint: str
    sprint_bonus: int


class InitiationBundle(TypedDict):
    """``resolve_initiation`` — grade, chosen metamagics / arts, MAG max bonus."""

    warnings: list[str]
    grade: int
    karma: int
    choices: list[dict[str, Any]]
    metamagics: list[dict[str, Any]]
    arts: list[dict[str, Any]]
    art_names: set[str]
    metamagic_names: set[str]
    bonus_sources: list[BonusSource]
    mag_max_bonus: int


class SubmersionBundle(TypedDict):
    """``resolve_submersion`` — grade, chosen echoes, RES max bonus."""

    warnings: list[str]
    grade: int
    karma: int
    choices: list[dict[str, Any]]
    echoes: list[dict[str, Any]]
    echo_names: list[str]
    bonus_sources: list[BonusSource]
    res_max_bonus: int


# --- empty-bundle factories -------------------------------------------------
# ``Ctx`` fields need a default; the producing phase always overwrites it
# before any consumer reads, but the placeholder is a structurally-valid
# bundle so the field can stay typed (not ``| None``).


def empty_skill_mods() -> SkillMods:
    return SkillMods(skill_bonus={}, skill_group_bonus={}, skill_category_bonus={}, skill_bonus_notes={})


def empty_skill_picks() -> SkillPicks:
    return SkillPicks(slots=[], warnings=[], skill_max_bonus={}, skill_bonus={}, skill_bonus_notes={})


def empty_contacts() -> ContactsBundle:
    return ContactsBundle(warnings=[], public=[], used=0, free=0, paid=0, karma=0, karma_per_point=1)


def empty_martial() -> MartialBundle:
    return MartialBundle(
        warnings=[],
        public=[],
        karma=0,
        style_count=0,
        technique_count=0,
        style_max=0,
        technique_max=0,
        spec_extras={},
        bonus_sources=[],
    )


def empty_movement() -> MovementBundle:
    return MovementBundle(walk="", run="", sprint="", sprint_bonus=0)


def empty_initiation() -> InitiationBundle:
    return InitiationBundle(
        warnings=[],
        grade=0,
        karma=0,
        choices=[],
        metamagics=[],
        arts=[],
        art_names=set(),
        metamagic_names=set(),
        bonus_sources=[],
        mag_max_bonus=0,
    )


def empty_submersion() -> SubmersionBundle:
    return SubmersionBundle(
        warnings=[],
        grade=0,
        karma=0,
        choices=[],
        echoes=[],
        echo_names=[],
        bonus_sources=[],
        res_max_bonus=0,
    )
