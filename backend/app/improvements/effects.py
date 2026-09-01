"""``EffectsDict`` + the empty effects dict + the special-armor / limit-modifier compactors."""

from __future__ import annotations

from typing import Any, TypedDict

from ._common import (
    ATTR_ALIASES,
    IMMUNE_KEYS,
    LIMIT_KINDS,
    SPECIAL_ARMOR_KEYS,
    SPELL_DEFENSE_RESIST_TAGS,
    TEST_MOD_TAGS,
    limit_condition_label,
)


class EffectsDict(TypedDict):
    """The engine's central bonus accumulator.

    ``empty_effects()`` seeds it, ``improvements/nodes/**`` fold ``<bonus>``
    nodes into it via ``apply_bonus_nodes``, and ~25 engine modules read it.
    ``total=True`` (the default): every key is present from ``empty_effects()``
    on, so ``effects["initiave_dice"]`` (typo) is now a ``mypy`` error rather
    than a silent ``None``. The scalars and the obvious nested dicts are typed
    precisely; the ``*_mods`` / ``*_slots`` / ``grant_*`` / ``add_*`` row lists
    stay ``list[dict[str, Any]]`` — their row shapes are out of scope, exactly
    as with the other ``Ctx`` bundles (see
    ``docs/refactor-effects-typeddict-plan.md``).

    ``enabled_tabs`` is a ``set[str]`` throughout the pipeline; callers that
    need an ordered list ``sorted(...)`` it at the point of use.
    """

    # --- scalars ---------------------------------------------------------
    armor: int
    cm_physical: int
    cm_stun: int
    initiative: int
    initiative_dice: int
    limit_physical: int
    limit_mental: int
    limit_social: int
    adept_power_points: int
    damage_resistance: int
    unarmed_dv: int
    unarmed_physical: bool
    unarmed_reach: int
    unarmed_ap: int
    magicians_way: bool
    needs_mentor: bool
    spell_resistance: int
    skillwires: int
    skilljack: int
    matrix_initiative_dice: int
    reach: int
    lifestyle_cost: int
    notoriety: int
    fame: int
    public_awareness: int
    essence_penalty: float
    essence_penalty_mag_exempt: float
    fatigue_resist: int
    cm_recovery_physical: int
    cm_recovery_stun: int
    cm_recovery_physical_add_ess: bool
    cm_recovery_stun_add_ess: bool
    nuyen_max_bp: int
    nuyen_amt: int
    trustfund: int
    black_market_discount: bool
    friends_in_high_places: bool
    made_man: bool
    contact_karma_adj: int
    contact_karma_min: int
    overclocker: bool
    ambidextrous: bool
    cyberware_ess_multiplier: int
    bioware_ess_multiplier: int
    cyberware_total_ess_multiplier: int
    essence_max_mod: int
    disable_bioware: bool
    special_modification_limit: int
    erased: bool
    excon: bool
    drain_value: int
    fading_value: int
    fading_resist: int
    drain_resist: int
    cyberadept_daemon: bool
    free_spells_flat: int
    prototype_transhuman_ess: float
    burnout_way: bool
    native_language_limit_bonus: int
    knowledge_skill_points: int

    # --- precisely-typed nested containers ------------------------------
    attribute_bonus: dict[str, int]
    attribute_max_mods: dict[str, int]
    test_mods: dict[str, int]
    spell_defense_resist: dict[str, int]
    special_armor: dict[str, int]
    walk_multiplier: dict[str, int]
    run_multiplier: dict[str, int]
    sprint_bonus: dict[str, int]
    skill_category_point_cost_mult: dict[str, int]
    living_persona: dict[str, int]
    immunities: dict[str, bool]
    movement_replace: dict[tuple[str, str], int]
    enabled_tabs: set[str]

    # --- string lists --------------------------------------------------
    cyberseeker: list[str]
    unlock_skills: list[str]
    free_qualities: list[str]
    add_qualities: list[str]
    disabled_skills: list[str]
    disabled_skill_groups: list[str]
    disabled_skill_group_categories: list[str]
    blocked_default_categories: list[str]
    dealer_connection_categories: list[str]
    disabled_cyberware_grades: list[str]
    disabled_bioware_grades: list[str]
    allow_spell_categories: list[str]
    allow_spell_ranges: list[str]
    block_spell_descriptors: list[str]
    limit_spell_categories: list[str]
    limit_spirit_categories: list[str]
    extra_spirits: list[str]

    # --- row lists (row shapes out of scope) --------------------------
    skill_group_mods: list[dict[str, Any]]
    skill_category_mods: list[dict[str, Any]]
    skill_specific_mods: list[dict[str, Any]]
    focus_binding: list[dict[str, Any]]
    skill_attribute_mods: list[dict[str, Any]]
    spell_category_mods: list[dict[str, Any]]
    spell_dice_pool: list[dict[str, Any]]
    action_dice_pools: list[dict[str, Any]]
    restricted_gear: list[dict[str, Any]]
    limit_modifiers: list[dict[str, Any]]
    attribute_selects: list[dict[str, Any]]
    add_contacts: list[dict[str, Any]]
    free_martial_arts: list[dict[str, Any]]
    limit_spell_category_slots: list[dict[str, Any]]
    limit_spirit_category_slots: list[dict[str, Any]]
    expertise_slots: list[dict[str, Any]]
    spell_category_drain: list[dict[str, Any]]
    spell_category_damage: list[dict[str, Any]]
    spell_descriptor_drain: list[dict[str, Any]]
    spell_descriptor_damage: list[dict[str, Any]]
    fading_value_specific: list[dict[str, Any]]
    grant_echoes: list[dict[str, Any]]
    grant_spells: list[dict[str, Any]]
    grant_powers: list[dict[str, Any]]
    select_power_slots: list[dict[str, Any]]
    weapon_category_dv_slots: list[dict[str, Any]]
    weapon_category_dv: list[dict[str, Any]]
    weapon_skill_accuracy_slots: list[dict[str, Any]]
    weapon_skill_accuracy: list[dict[str, Any]]
    add_spirit_slots: list[dict[str, Any]]
    add_spirit_picks: list[dict[str, Any]]
    free_metamagics: list[dict[str, Any]]
    free_spells_skill: list[dict[str, Any]]
    free_spells_attribute: list[dict[str, Any]]
    new_spell_karma_cost: list[dict[str, Any]]
    skill_category_karma_cost_mult: list[dict[str, Any]]
    skill_category_karma_cost: list[dict[str, Any]]
    skill_category_spec_karma_cost_mult: list[dict[str, Any]]
    skill_group_category_karma_cost_mult: list[dict[str, Any]]
    active_skill_karma_cost: list[dict[str, Any]]
    knowledge_skill_karma_cost: list[dict[str, Any]]
    knowledge_skill_karma_cost_min: list[dict[str, Any]]
    select_quality_slots: list[dict[str, Any]]
    unimplemented: list[dict[str, Any]]


def empty_effects() -> EffectsDict:
    return {
        "attribute_bonus": {k: 0 for k in ATTR_ALIASES.values() if len(k) <= 3},
        "armor": 0,
        "cm_physical": 0,
        "cm_stun": 0,
        "initiative": 0,
        "initiative_dice": 0,
        "enabled_tabs": set(),
        "cyberseeker": [],
        "limit_physical": 0,
        "limit_mental": 0,
        "limit_social": 0,
        "skill_group_mods": [],
        "skill_category_mods": [],
        "skill_specific_mods": [],
        "adept_power_points": 0,
        "unlock_skills": [],
        "damage_resistance": 0,
        "unarmed_dv": 0,
        "unarmed_physical": False,
        "unarmed_reach": 0,
        "unarmed_ap": 0,
        "magicians_way": False,
        "free_qualities": [],
        "add_qualities": [],
        "needs_mentor": False,
        "focus_binding": [],
        "skill_attribute_mods": [],
        "spell_category_mods": [],
        "spell_dice_pool": [],
        "action_dice_pools": [],
        "spell_resistance": 0,
        "spell_defense_resist": dict.fromkeys(SPELL_DEFENSE_RESIST_TAGS.values(), 0),
        "special_armor": dict.fromkeys(SPECIAL_ARMOR_KEYS, 0),
        "immunities": dict.fromkeys(IMMUNE_KEYS, False),
        "restricted_gear": [],
        "limit_modifiers": [],
        "skillwires": 0,
        "skilljack": 0,
        "living_persona": {"attack": 0, "sleaze": 0, "dataprocessing": 0, "firewall": 0},
        "matrix_initiative_dice": 0,
        "reach": 0,
        "lifestyle_cost": 0,
        "notoriety": 0,
        "fame": 0,
        "public_awareness": 0,
        "essence_penalty": 0.0,
        "essence_penalty_mag_exempt": 0.0,
        "walk_multiplier": {},
        "run_multiplier": {},
        "movement_replace": {},
        "sprint_bonus": {},
        "fatigue_resist": 0,
        "test_mods": dict.fromkeys(TEST_MOD_TAGS.values(), 0),
        "attribute_selects": [],
        "cm_recovery_physical": 0,
        "cm_recovery_stun": 0,
        "cm_recovery_physical_add_ess": False,
        "cm_recovery_stun_add_ess": False,
        "disabled_skills": [],
        "disabled_skill_groups": [],
        "disabled_skill_group_categories": [],
        "blocked_default_categories": [],
        "nuyen_max_bp": 0,
        "nuyen_amt": 0,
        "trustfund": 0,
        "black_market_discount": False,
        "dealer_connection_categories": [],
        "friends_in_high_places": False,
        "made_man": False,
        "add_contacts": [],
        "contact_karma_adj": 0,
        "contact_karma_min": 0,
        "overclocker": False,
        "ambidextrous": False,
        "cyberware_ess_multiplier": 100,
        "bioware_ess_multiplier": 100,
        "cyberware_total_ess_multiplier": 100,
        "essence_max_mod": 0,
        "disable_bioware": False,
        "disabled_cyberware_grades": [],
        "disabled_bioware_grades": [],
        "free_martial_arts": [],
        "limit_spell_category_slots": [],
        "limit_spirit_category_slots": [],
        "allow_spell_categories": [],
        "allow_spell_ranges": [],
        "block_spell_descriptors": [],
        "limit_spell_categories": [],
        "limit_spirit_categories": [],
        "special_modification_limit": 0,
        "erased": False,
        "excon": False,
        "expertise_slots": [],
        "spell_category_drain": [],
        "spell_category_damage": [],
        "spell_descriptor_drain": [],
        "spell_descriptor_damage": [],
        "drain_value": 0,
        "fading_value": 0,
        "fading_value_specific": [],
        "fading_resist": 0,
        "drain_resist": 0,
        "grant_echoes": [],
        "cyberadept_daemon": False,
        "grant_spells": [],
        "grant_powers": [],
        "select_power_slots": [],
        "weapon_category_dv_slots": [],
        "weapon_category_dv": [],
        "weapon_skill_accuracy_slots": [],
        "weapon_skill_accuracy": [],
        "add_spirit_slots": [],
        "add_spirit_picks": [],
        "extra_spirits": [],
        "free_metamagics": [],
        "free_spells_flat": 0,
        "free_spells_skill": [],
        "free_spells_attribute": [],
        "new_spell_karma_cost": [],
        "prototype_transhuman_ess": 0.0,
        "burnout_way": False,
        "native_language_limit_bonus": 0,
        "knowledge_skill_points": 0,
        "attribute_max_mods": {},
        "skill_category_point_cost_mult": {},
        "skill_category_karma_cost_mult": [],
        "skill_category_karma_cost": [],
        "skill_category_spec_karma_cost_mult": [],
        "skill_group_category_karma_cost_mult": [],
        "active_skill_karma_cost": [],
        "knowledge_skill_karma_cost": [],
        "knowledge_skill_karma_cost_min": [],
        "select_quality_slots": [],
        "unimplemented": [],
    }


def special_armor_totals(effects: EffectsDict) -> dict[str, Any]:
    return {
        **{key: int(effects.get("special_armor", {}).get(key) or 0) for key in SPECIAL_ARMOR_KEYS},
        "immunities": {key: bool((effects.get("immunities") or {}).get(key)) for key in IMMUNE_KEYS},
    }


def compact_special_armor(effects: EffectsDict) -> dict[str, Any] | None:
    nums = {
        key: int(effects.get("special_armor", {}).get(key) or 0)
        for key in SPECIAL_ARMOR_KEYS
        if int(effects.get("special_armor", {}).get(key) or 0)
    }
    immunities = {key: True for key, value in (effects.get("immunities") or {}).items() if value}
    if not nums and not immunities:
        return None
    out: dict[str, Any] = dict(nums)
    if immunities:
        out["immunities"] = immunities
    return out


def compact_limit_modifiers(effects: EffectsDict) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in effects.get("limit_modifiers") or []:
        kind = str(row.get("limit") or "")
        value = int(row.get("value") or 0)
        if kind not in LIMIT_KINDS or value == 0:
            continue
        condition = str(row.get("condition") or "")
        out.append(
            {
                "limit": kind,
                "value": value,
                "condition": condition,
                "condition_label": str(row.get("condition_label") or limit_condition_label(condition)),
                "source": str(row.get("source") or ""),
            }
        )
    return out
