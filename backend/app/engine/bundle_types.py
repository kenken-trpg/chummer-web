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


class AdeptBundle(TypedDict):
    """``resolve_adept_powers`` — chosen powers, power-point spend, Way discount."""

    warnings: list[str]
    errors: list[str]
    public: list[dict[str, Any]]
    bonus_sources: list[BonusSource]
    spent: float
    discount_used: float
    discount_max: float
    mystic_pp: int
    power_names: set[str]


class EnhancementsBundle(TypedDict):
    """``resolve_enhancements`` — adept enhancement picks + their karma."""

    warnings: list[str]
    public: list[dict[str, Any]]
    bonus_sources: list[BonusSource]
    karma: int


class FociBundle(TypedDict):
    """``resolve_foci`` — bonded foci, their nuyen / karma and bonus nodes."""

    warnings: list[str]
    public: list[dict[str, Any]]
    bonus_sources: list[BonusSource]
    nuyen: int
    karma: int


class QiFociBundle(TypedDict):
    """``resolve_qi_foci`` — Qi foci, granted free powers, nuyen / karma."""

    warnings: list[str]
    errors: list[str]
    public: list[dict[str, Any]]
    free_powers: list[dict[str, Any]]
    nuyen: int
    karma: int


class FocusLimits(TypedDict):
    """``apply_focus_limits`` — bonded-focus count / force ceilings."""

    count: int
    count_max: int
    force: int
    force_max: int


class SpellsBundle(TypedDict):
    """``resolve_spells`` — spell list, free/paid allowance, tradition + drain resist."""

    warnings: list[str]
    public: list[dict[str, Any]]
    free_max: int
    used: int
    paid: int
    karma: int
    tradition: dict[str, Any] | None
    resist: int
    resist_attrs: str
    range_gated: bool


class SpiritsBundle(TypedDict):
    """``resolve_spirits`` — bound / unbound spirits and their reagent nuyen."""

    warnings: list[str]
    public: list[dict[str, Any]]
    nuyen: int


class ComplexFormsBundle(TypedDict):
    """``resolve_complex_forms`` — complex forms, free/paid allowance, stream + fade resist."""

    warnings: list[str]
    public: list[dict[str, Any]]
    free_max: int
    used: int
    paid: int
    karma: int
    stream: dict[str, Any] | None
    resist: int
    resist_attrs: str


class SpritesBundle(TypedDict):
    """``resolve_sprites`` — compiled / registered sprites."""

    warnings: list[str]
    errors: list[str]
    public: list[dict[str, Any]]


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


def empty_adept() -> AdeptBundle:
    return AdeptBundle(
        warnings=[],
        errors=[],
        public=[],
        bonus_sources=[],
        spent=0.0,
        discount_used=0.0,
        discount_max=0.0,
        mystic_pp=0,
        power_names=set(),
    )


def empty_enhancements() -> EnhancementsBundle:
    return EnhancementsBundle(warnings=[], public=[], bonus_sources=[], karma=0)


def empty_foci() -> FociBundle:
    return FociBundle(warnings=[], public=[], bonus_sources=[], nuyen=0, karma=0)


def empty_qi_foci() -> QiFociBundle:
    return QiFociBundle(warnings=[], errors=[], public=[], free_powers=[], nuyen=0, karma=0)


def empty_focus_limits() -> FocusLimits:
    return FocusLimits(count=0, count_max=0, force=0, force_max=0)


def empty_spells() -> SpellsBundle:
    return SpellsBundle(
        warnings=[],
        public=[],
        free_max=0,
        used=0,
        paid=0,
        karma=0,
        tradition=None,
        resist=0,
        resist_attrs="",
        range_gated=False,
    )


def empty_spirits() -> SpiritsBundle:
    return SpiritsBundle(warnings=[], public=[], nuyen=0)


def empty_complex_forms() -> ComplexFormsBundle:
    return ComplexFormsBundle(
        warnings=[],
        public=[],
        free_max=0,
        used=0,
        paid=0,
        karma=0,
        stream=None,
        resist=0,
        resist_attrs="",
    )


def empty_sprites() -> SpritesBundle:
    return SpritesBundle(warnings=[], errors=[], public=[])
