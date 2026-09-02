"""``DerivedDict`` — the shape of ``ctx.state.derived`` (the API payload).

``assemble()`` builds this ~175-key dict literal; the frontend mirrors the
top-level key set as ``Character["derived"]`` in
``frontend/lib/types/character.ts`` (kept honest by
``tests/test_derived_contract.py``). Typing it here makes a key typo or a
wrong value type in ``assemble.py`` a ``mypy`` error.

Nested sub-objects get their own ``TypedDict``; the "public row" lists stay
``list[dict[str, Any]]`` — the same out-of-scope call as the ``Ctx`` bundles
and ``catalog()``. Imports only ``typing`` + the bundle types it re-uses.
"""

from __future__ import annotations

from typing import Any, TypedDict

from ...improvements.effect_rows import (
    ActionDicePoolRow,
    AddSpiritPickRow,
    SpellDicePoolRow,
    UnimplementedRow,
)
from ..bundle_types import FocusLimits, MovementBundle

Row = dict[str, Any]


class _UsedMax(TypedDict):
    used: int
    max: int


class _PoolAttrs(TypedDict):
    pool: int
    attrs: str


class _SumToTen(TypedDict):
    used: int
    max: int
    costs: dict[str, int]
    unique: bool


class _KarmaChargen(TypedDict):
    enabled: bool
    pool: int
    nuyen_karma: int
    nuyen_karma_max: int
    nuyen_per_karma: int
    metatype: int
    attributes: int
    skills: int
    knowledge: int
    specializations: int
    qualities: int
    other: int


class _Limits(TypedDict):
    physical: int
    mental: int
    social: int


class _ConditionMonitor(TypedDict):
    physical: int
    stun: int


class _Initiative(TypedDict):
    value: int
    dice: int


class _SpecialModificationLimit(TypedDict):
    used: int
    max: int


class _KarmaNegative(TypedDict):
    used: int
    max: int | None


class _Karma(TypedDict):
    pool: int
    spent: int
    remaining: int
    negative: _KarmaNegative


class _PowerPoints(TypedDict):
    used: float
    max: float


class _WayDiscount(TypedDict):
    used: float
    max: float


class _SpellPoints(TypedDict):
    used: int
    free: int
    paid: int
    karma: int
    spell_karma: int


class _ComplexFormPoints(TypedDict):
    used: int
    free: int
    paid: int


class _Points(TypedDict):
    attributes: _UsedMax
    special: _UsedMax
    skills: _UsedMax
    skill_groups: _UsedMax
    knowledge: _UsedMax
    contacts: _UsedMax


class _ContactPoints(TypedDict):
    used: int
    free: int
    paid: int
    karma: int
    karma_per_point: int


class _MartialArtPoints(TypedDict):
    styles: int
    style_max: int
    techniques: int
    technique_max: int
    karma: int


class _CmRecovery(TypedDict):
    physical: int
    stun: int


class _Initiation(TypedDict):
    grade: int
    karma: int
    choices: list[Row]
    metamagics: list[Row]
    arts: list[Row]


class _Submersion(TypedDict):
    grade: int
    karma: int
    choices: list[Row]
    echoes: list[Row]


class _MetatypeInfo(TypedDict):
    name: str
    parent: str | None
    attributes: dict[str, dict[str, int | float]]
    source: str | None


class DerivedDict(TypedDict):
    # --- chargen budgets --------------------------------------------------
    errors: list[str]
    warnings: list[str]
    build_method: str
    sum_to_ten: _SumToTen
    karma_chargen: _KarmaChargen
    karma: _Karma
    points: _Points
    power_points: _PowerPoints

    # --- combat / body --------------------------------------------------
    totals: dict[str, int]
    limits: _Limits
    limit_modifiers: list[Row]
    condition_monitor: _ConditionMonitor
    initiative: _Initiative
    movement: MovementBundle
    essence: float
    essence_lost: float
    essence_lost_cyber: float
    essence_lost_bio: float
    essence_penalty: float
    prototype_transhuman_ess: float
    armor: int
    special_armor: dict[str, Any]
    worn_armor: str
    recoil: dict[str, int]
    damage_resistance: int
    unarmed_dv: int
    unarmed_physical: bool
    unarmed_reach: int
    unarmed_ap: int
    reach: int
    throw_str: int
    throw_range_str: int
    fatigue_resist: int
    spell_resistance: int
    spell_defense: dict[str, Any]
    spell_dice_pool: list[SpellDicePoolRow]
    action_dice_pools: list[ActionDicePoolRow]
    test_mods: dict[str, int]
    cm_recovery: _CmRecovery

    # --- gear ----------------------------------------------------------
    armor_items: list[Row]
    armor_mods: list[Row]
    weapons: list[Row]
    weapon_accessories: list[Row]
    active_drugs: list[Row]
    commlinks: list[Row]
    cyberdecks: list[Row]
    rccs: list[Row]
    optics: list[Row]
    programs: list[Row]
    apps: list[Row]
    sensors: list[Row]
    drones: list[Row]
    vehicles: list[Row]
    vehicle_mods: list[Row]
    weapon_mounts: list[Row]
    gear: list[Row]
    lifestyles: list[Row]
    commlink: Row | None
    cyberdeck: Row | None
    rcc: Row | None
    lifestyle: Row | None

    # --- economy -----------------------------------------------------
    nuyen: int
    nuyen_spent: int
    nuyen_pool: int
    nuyen_earned: int
    karma_earned: int
    career: bool
    career_advancement_karma: int
    career_advancement_lines: list[Row]
    nuyen_amt: int
    nuyen_karma_max: int
    trustfund: int
    trustfund_label: str
    ambidextrous: bool
    overclocker: bool
    special_modification_limit: _SpecialModificationLimit
    friends_in_high_places: bool
    made_man: bool
    black_market_discount: bool
    black_market_category: str
    black_market_contact_id: str
    black_market_avail_bonus: int
    dealer_connection_categories: list[str]
    cyberware_ess_multiplier: int
    bioware_ess_multiplier: int
    reward_log: list[Row]
    karma_spend_breakdown: list[Row]
    nuyen_spend_breakdown: list[Row]
    lifestyle_cost_mod: int

    # --- caps -------------------------------------------------------
    skill_rating_max: int
    skill_group_max: int
    avail_limit: int | None
    device_rating_limit: int | None
    ware_attr_limit: int | None
    ware_attr_bonus: dict[str, int]

    # --- magic / adept / resonance --------------------------------
    metagenic: dict[str, Any] | None
    adept_powers: list[Row]
    mystic_pp: int
    way_discount: _WayDiscount
    mentor: Row | None
    needs_mentor: bool
    qi_foci: list[Row]
    foci: list[Row]
    focus_limits: FocusLimits
    spirits: list[Row]
    enhancements: list[Row]
    spells: list[Row]
    spell_points: _SpellPoints
    tradition: Row | None
    drain_resist: _PoolAttrs
    complex_forms: list[Row]
    complex_form_points: _ComplexFormPoints
    sprites: list[Row]
    stream: Row | None
    fade_resist: _PoolAttrs
    living_persona: dict[str, int] | None
    initiate_grade: int
    initiation: _Initiation
    submersion_grade: int
    submersion: _Submersion
    spell_range_gated: bool
    limit_spell_categories: list[str]
    limit_spirit_categories: list[str]
    allow_spell_categories: list[str]
    allow_spell_ranges: list[str]
    block_spell_descriptors: list[str]
    extra_spirits: list[str]
    add_spirit_picks: list[AddSpiritPickRow]
    unlock_skills: list[str]
    burnout_way: bool

    # --- skills / knowledge / contacts / martial --------------
    skill_totals: dict[str, int]
    skill_specializations: dict[str, str]
    skill_expertises: list[Row]
    exotic_skills: list[Row]
    skillsoft: list[Row]
    skillwires: int
    skilljack: int
    skill_bonus: dict[str, int]
    skill_group_bonus: dict[str, int]
    skill_category_bonus: dict[str, int]
    skill_bonus_notes: dict[str, list[str]]
    skill_max_bonus: dict[str, int]
    skill_pick_slots: list[Row]
    native_language_limit: int
    disabled_skills: list[str]
    disabled_skill_groups: list[str]
    blocked_default_categories: list[str]
    knowledge_skills: list[Row]
    contacts: list[Row]
    contact_points: _ContactPoints
    martial_arts: list[Row]
    martial_art_points: _MartialArtPoints
    martial_spec_options: dict[str, list[str]]

    # --- social / misc -------------------------------------------
    street_cred: int
    notoriety: int
    notoriety_quality: int
    notoriety_bonus: int
    fame: int
    public_awareness: int
    erased: bool
    excon: bool
    attribute_max_bonus: dict[str, int]
    disabled_cyberware_grades: list[str]
    disabled_bioware_grades: list[str]

    # --- identity ----------------------------------------------
    enabled_tabs: list[str]
    unimplemented_bonuses: list[UnimplementedRow]
    qualities: list[Row]
    cyberware: list[Row]
    bioware: list[Row]
    ware_ranges: dict[str, dict[str, int]]
    limb_replace: dict[str, Any] | None
    limb_quality: dict[str, Any] | None
    talent: dict[str, Any]
    metatype_info: _MetatypeInfo
    translations: dict[str, str]
