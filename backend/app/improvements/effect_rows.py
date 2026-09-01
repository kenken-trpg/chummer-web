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

from typing import NotRequired, TypedDict


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


# --- grants (G3) ---------------------------------------------------------


class GrantEchoRow(TypedDict):
    """``grant_echoes`` — an ``<addecho>`` grant."""

    source: str
    name: str


class GrantSpellRow(TypedDict):
    """``grant_spells`` — an ``<addspell>`` grant with its variant flags."""

    source: str
    name: str
    alchemical: bool
    extended: bool
    limited: bool


class GrantPowerRow(TypedDict):
    """``grant_powers`` — a ``<specificpower>`` / resolved ``<selectpowers>``
    grant."""

    source: str
    name: str
    rating: int
    extra: str


class FreeMartialArtRow(TypedDict):
    """``free_martial_arts`` — a ``<martialart>`` quality grant."""

    name: str
    source: str


class FreeMetamagicRow(TypedDict):
    """``free_metamagics`` — an ``<addmetamagic>`` grant (``forced`` skips the
    normal grade gate)."""

    name: str
    source: str
    forced: bool


# --- misc effect rows (G5) --------------------------------------------


class RestrictedGearRow(TypedDict):
    """``restricted_gear`` — a ``<restrictedgear>`` availability-cap slot."""

    availability: int
    amount: int
    source: str


class LimitModifierRow(TypedDict):
    """``limit_modifiers`` — a ``<limitmodifier>`` (physical/mental/social),
    optionally conditional."""

    limit: str
    value: int
    condition: str
    condition_label: str
    source: str


class ActionDicePoolRow(TypedDict):
    """``action_dice_pools`` — an ``<actiondicepool>`` bonus. ``needs_action``
    marks a still-unchosen Matrix action; ``bind_action_dice_pools`` resolves
    it and drops the key."""

    category: str
    name: str
    bonus: int
    source: str
    needs_action: NotRequired[bool]


class FocusBindingRow(TypedDict):
    """``focus_binding`` — a ``<focusbindingkarmacost>`` discount rule."""

    name: str
    val: int
    extracontains: str
    source: str


class SpellDicePoolRow(TypedDict):
    """``spell_dice_pool`` — a ``<spelldicepool>`` bonus to one named spell."""

    name: str
    id: str
    bonus: int
    source: str


class SpellCategoryValueRow(TypedDict):
    """``spell_category_drain`` / ``spell_category_damage`` — a per-category
    drain / damage modifier (``category`` filled from the quality pick when
    the node leaves it blank)."""

    source: str
    category: str
    value: int


class SpellDescriptorValueRow(TypedDict):
    """``spell_descriptor_drain`` / ``spell_descriptor_damage`` — the
    descriptor-keyed counterparts."""

    source: str
    descriptor: str
    value: int


class FadingValueSpecificRow(TypedDict):
    """``fading_value_specific`` — a ``<fadingvalue specific=...>`` override for
    one complex form."""

    specific: str
    value: int


class FreeSpellsSkillRow(TypedDict):
    """``free_spells_skill`` — a ``<freespells skill=...>`` allowance."""

    skill: str
    limit: str
    source: str


class FreeSpellsAttributeRow(TypedDict):
    """``free_spells_attribute`` — a ``<freespells attribute=...>`` allowance."""

    attribute: str
    limit: str
    source: str


class NewSpellKarmaCostRow(TypedDict):
    """``new_spell_karma_cost`` — a ``<newspellkarmacost>`` override for a
    spell type."""

    type: str
    value: int
    condition: str
    source: str


class AddContactRow(TypedDict):
    """``add_contacts`` — an ``<addcontact>`` quality-granted contact."""

    source: str
    connection: int
    loyalty: int
    forced_loyalty: int | None
    free: bool
    group: bool
    force_group: bool


class UnimplementedRow(TypedDict):
    """``unimplemented`` — a seen-but-unhandled ``<bonus>`` tag, surfaced in
    the derived output for visibility."""

    source: str
    tag: str


# --- slot / select rows (G4) -----------------------------------------


class AttributeSelectRow(TypedDict):
    """``attribute_selects`` — a ``<selectattributes>`` pick slot (``exclude``
    lists attributes already spoken for)."""

    exclude: list[str]
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


# --- resolved / bind_*-produced rows (G6) ----------------------------


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
