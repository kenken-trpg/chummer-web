"""Row shapes for the rows that hold a choice the player still has to make, or
has made — attributes, qualities, powers, spirits, weapons (group G4 of
``docs/plans/refactor-effect-rows-plan.md``)."""

from __future__ import annotations

from typing import TypedDict


class AttributeSelectRow(TypedDict):
    """One ordered attribute choice: allowed/excluded attributes, rating and max modifiers."""

    exclude: list[str]
    options: list[str]
    val: int
    index: int
    max: int
    source: str


class SelectQualitySlotRow(TypedDict):
    """``select_quality_slots`` — a ``<selectquality>`` pick slot."""

    source: str
    options: list[str]


class ExpertiseSlotRow(TypedDict):
    """``expertise_slots`` — a ``<selectexpertise>`` free-Expertise pick slot."""

    source: str
    skills: list[str]
    limit_to_specialization: str


class LimitSpellCategorySlotRow(TypedDict):
    """``limit_spell_category_slots`` — a ``<limitspellcategory>`` slot
    (``value`` empty until the quality pick is resolved)."""

    source: str
    value: str
    exclude: str


class LimitSpiritCategorySlotRow(TypedDict):
    """``limit_spirit_category_slots`` — a ``<limitspiritcategory>`` slot."""

    source: str
    spirits: list[str]


class AddSpiritSlotRow(TypedDict):
    """``add_spirit_slots`` — an ``<addspirit>`` slot (``rating_divisor`` scales
    the summonable count off a skill rating)."""

    source: str
    skill: str
    rating_divisor: int
    add_to_selected: bool
    allowed: list[str]


class SelectPowerSlotRow(TypedDict):
    """``select_power_slots`` — a ``<selectpowers>`` pick slot:
    ``parse_select_power_slot(node)`` output plus its ``source``."""

    source: str
    options: list[str]
    rating: int
    rating_expr: str
    limit_expr: str
    points_per_level: float
    ignore_rating: bool
    open_select: bool
    needs_select: bool


class WeaponCategoryDvSlotRow(TypedDict):
    """``weapon_category_dv_slots`` — a ``<weaponcategorydv>`` pick slot."""

    source: str
    skills: list[str]
    name: str
    bonus: int
    needs_select: bool


class WeaponSkillAccuracySlotRow(TypedDict):
    """``weapon_skill_accuracy_slots`` — a ``<weaponskillaccuracy>`` pick slot."""

    source: str
    name: str
    bonus: int
    select_attrs: dict[str, str]
    needs_select: bool


class NaturalWeaponRow(TypedDict):
    """``natural_weapons`` — a ``<naturalweapon>`` attack the character was
    born with: a Shapeshifter's bite and claws (RF p.104). It has no entry in
    ``weapons.xml``, so the node's own fields are the whole weapon."""

    source: str
    name: str
    damage: str
    ap: str
    reach: str
    useskill: str
    accuracy: str
    weapon_source: str
    page: str


class WeaponCategoryDiceRow(TypedDict):
    """``weapon_category_dice`` — a ``<weaponcategorydice>`` attack dice-pool
    bonus for one weapon category (e.g. Master Archer: Bows +1)."""

    category: str
    dice: int
    source: str
