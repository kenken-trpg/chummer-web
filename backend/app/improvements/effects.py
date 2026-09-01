"""The empty effects dict + the special-armor / limit-modifier compactors."""

from __future__ import annotations

from typing import Any

from ._common import (
    ATTR_ALIASES,
    IMMUNE_KEYS,
    LIMIT_KINDS,
    SPECIAL_ARMOR_KEYS,
    SPELL_DEFENSE_RESIST_TAGS,
    TEST_MOD_TAGS,
    limit_condition_label,
)


def empty_effects() -> dict[str, Any]:
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


def special_armor_totals(effects: dict[str, Any]) -> dict[str, Any]:
    return {
        **{key: int(effects.get("special_armor", {}).get(key) or 0) for key in SPECIAL_ARMOR_KEYS},
        "immunities": {key: bool((effects.get("immunities") or {}).get(key)) for key in IMMUNE_KEYS},
    }


def compact_special_armor(effects: dict[str, Any]) -> dict[str, Any] | None:
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


def compact_limit_modifiers(effects: dict[str, Any]) -> list[dict[str, Any]]:
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
