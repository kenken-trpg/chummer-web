"""Row shapes for the effect rows that are neither a grant nor a player slot:
availability caps, limit modifiers, dice pools, contacts, and the
seen-but-unhandled tags (group G5 of
``docs/plans/refactor-effect-rows-plan.md``)."""

from __future__ import annotations

from typing import NotRequired, TypedDict

from ...notices import Notice


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
    condition_label: Notice | None
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
