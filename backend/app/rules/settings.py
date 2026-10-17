"""Chummer's ``SettingsState`` resolved into a :class:`Rules`.

A settings file says what it *changes*, so every field here is an override on
top of the printed SR5 values in ``core.py``: a field left unset keeps the
printed one. The plain carried-through numbers are a table (``_DIRECT``);
anything needing arithmetic or a different shape gets a branch in
``rules_for``.
"""

from __future__ import annotations

from dataclasses import fields

from .core import DEFAULT_RULES, Rules

#: `SettingsState` field -> `Rules` field, for the fields that are a plain
#: number carried straight through. Anything needing arithmetic or a different
#: shape (`banned_ware_grades`) is handled in `rules_for` instead.
_DIRECT: dict[str, str] = {
    "sum_to_ten": "sum_to_ten_budget",
    "chargen_karma": "chargen_karma",
    "karma_chargen_pool": "karma_chargen_pool",
    "karma_attribute": "karma_attribute",
    "karma_active_skill": "karma_active_skill",
    "karma_skill_group": "karma_skill_group",
    "karma_knowledge": "karma_knowledge",
    "karma_specialization": "karma_specialization",
    "karma_knowledge_specialization": "karma_knowledge_specialization",
    "karma_spell": "karma_spell",
    "karma_complex_form": "karma_complex_form",
    "karma_ai_program": "karma_ai_program",
    "karma_ai_advanced_program": "karma_ai_advanced_program",
    "karma_enhancement": "karma_enhancement",
    "karma_mystic_pp": "karma_mystic_pp",
    "karma_martial_technique": "karma_martial_technique",
    "karma_new_active_skill": "karma_new_active_skill",
    "karma_new_knowledge_skill": "karma_new_knowledge_skill",
    "karma_new_skill_group": "karma_new_skill_group",
    "karma_alchemical_focus": "karma_alchemical_focus",
    "karma_banishing_focus": "karma_banishing_focus",
    "karma_binding_focus": "karma_binding_focus",
    "karma_centering_focus": "karma_centering_focus",
    "karma_counterspelling_focus": "karma_counterspelling_focus",
    "karma_disenchanting_focus": "karma_disenchanting_focus",
    "karma_flexible_signature_focus": "karma_flexible_signature_focus",
    "karma_masking_focus": "karma_masking_focus",
    "karma_power_focus": "karma_power_focus",
    "karma_qi_focus": "karma_qi_focus",
    "karma_ritual_spellcasting_focus": "karma_ritual_spellcasting_focus",
    "karma_spell_shaping_focus": "karma_spell_shaping_focus",
    "karma_spellcasting_focus": "karma_spellcasting_focus",
    "karma_summoning_focus": "karma_summoning_focus",
    "karma_sustaining_focus": "karma_sustaining_focus",
    "karma_weapon_focus": "karma_weapon_focus",
    "karma_initiation_flat": "karma_initiation_flat",
    "karma_initiation_per_grade": "karma_initiation_per_grade",
    "karma_submersion_flat": "karma_submersion_flat",
    "karma_submersion_per_grade": "karma_submersion_per_grade",
    "chargen_skill_max": "chargen_skill_max",
    "chargen_knowledge_skill_max": "chargen_knowledge_skill_max",
    "chargen_attributes_at_max": "chargen_attributes_at_max",
    "career_skill_max": "career_skill_max",
    "career_knowledge_skill_max": "career_knowledge_skill_max",
    "chargen_avail_max": "chargen_avail_max",
    "min_initiative_dice": "min_initiative_dice",
    "max_initiative_dice": "max_initiative_dice",
    "min_coldsim_initiative_dice": "min_coldsim_initiative_dice",
    "max_coldsim_initiative_dice": "max_coldsim_initiative_dice",
    "min_hotsim_initiative_dice": "min_hotsim_initiative_dice",
    "max_hotsim_initiative_dice": "max_hotsim_initiative_dice",
    "min_astral_initiative_dice": "min_astral_initiative_dice",
    "max_astral_initiative_dice": "max_astral_initiative_dice",
    "limb_count": "limb_count",
    "cyberlimb_attribute_bonus_cap": "cyberlimb_attribute_bonus_cap",
    "karma_to_nuyen": "karma_to_nuyen",
    "metatype_costs_karma_multiplier": "metatype_costs_karma_multiplier",
    "karma_spirit": "karma_spirit",
    "karma_carryover": "karma_carryover",
    "priority_karma_nuyen_base": "priority_karma_nuyen_base",
    "contact_free_mult": "contact_free_mult",
    "drone_armor_multiplier": "drone_armor_multiplier",
}

#: Every `Rules` field name — `test_settings.py` asserts `_DIRECT` only names
#: real ones, so a rename on either side fails loudly instead of silently
#: dropping an override.
RULE_FIELDS = frozenset(f.name for f in fields(Rules))


def rules_for(settings: object | None) -> Rules:
    """`SettingsState` -> `Rules`. `None`, or a field left unset, keeps the
    printed SR5 value: a settings file says what it changes, not everything."""
    if settings is None:
        return DEFAULT_RULES
    overrides: dict[str, object] = {}
    for src, dest in _DIRECT.items():
        value = getattr(settings, src, None)
        if value is not None:
            overrides[dest] = int(value)
    # `<qualitykarmalimit>` is one number in Chummer and caps both directions.
    limit = getattr(settings, "quality_karma_limit", None)
    if limit is not None:
        overrides["quality_karma_cap_positive"] = int(limit)
        overrides["quality_karma_cap_negative"] = int(limit)
    for src, dest in (
        ("exceed_negative_qualities", "quality_exceed_negative"),
        ("exceed_negative_qualities_no_bonus", "quality_exceed_negative_no_bonus"),
        ("exceed_positive_qualities", "quality_exceed_positive"),
        ("dont_double_quality_purchases", "quality_dont_double_purchases"),
        ("dont_double_quality_refunds", "quality_dont_double_refunds"),
        ("cyberleg_movement", "cyberleg_movement"),
        ("unarmed_improvements_apply_to_weapons", "unarmed_improvements_apply_to_weapons"),
        ("dont_use_cyberlimb_calculation", "dont_use_cyberlimb_calculation"),
        ("enforce_capacity", "enforce_capacity"),
        ("restrict_recoil", "restrict_recoil"),
        ("unrestricted_nuyen", "unrestricted_nuyen"),
        ("use_calculated_public_awareness", "use_calculated_public_awareness"),
        ("no_armor_encumbrance", "no_armor_encumbrance"),
        ("uncapped_armor_accessory_bonuses", "uncapped_armor_accessory_bonuses"),
        ("ess_loss_reduces_maximum_only", "ess_loss_reduces_maximum_only"),
        ("dont_round_essence_internally", "dont_round_essence_internally"),
        ("allow_initiation_in_create_mode", "allow_initiation_in_create_mode"),
        ("ignore_art", "ignore_art"),
        ("use_points_on_broken_groups", "use_points_on_broken_groups"),
        ("strict_skill_groups_in_create_mode", "strict_skill_groups_in_create_mode"),
        ("drone_armor_multiplier_enabled", "drone_armor_multiplier_enabled"),
        ("drone_mods", "drone_mods"),
        ("drone_mods_maximum_pilot", "drone_mods_maximum_pilot"),
        ("alternate_metatype_attribute_karma", "alternate_metatype_attribute_karma"),
        ("compensate_skill_group_karma_difference", "compensate_skill_group_karma_difference"),
        ("increased_improved_ability_modifier", "increased_improved_ability_modifier"),
        ("mystic_adept_pp_in_career", "mystic_adept_pp_in_career"),
        ("spirit_force_based_on_total_mag", "spirit_force_based_on_total_mag"),
        ("free_martial_art_specialization", "free_martial_art_specialization"),
        ("allow_free_grids", "allow_free_grids"),
        ("allow_cyberware_ess_discounts", "allow_cyberware_ess_discounts"),
        (
            "allow_point_buy_specializations_on_karma_skills",
            "allow_point_buy_specializations_on_karma_skills",
        ),
    ):
        flag = getattr(settings, src, None)
        if flag is not None:
            overrides[dest] = bool(flag)
    # Ticking Rigger 5.0 among the books turns its drone modification rules on
    # too, unless the settings file switched them off outright.
    if "R5" in (getattr(settings, "books", None) or []) and getattr(settings, "drone_mods", None) is not False:
        overrides["drone_mods"] = True
    for switch, factor, dest in (
        ("multiply_restricted_cost", "restricted_cost_multiplier", "career_restricted_cost_multiplier"),
        ("multiply_forbidden_cost", "forbidden_cost_multiplier", "career_forbidden_cost_multiplier"),
    ):
        if getattr(settings, switch, None):
            overrides[dest] = max(1, int(getattr(settings, factor, None) or 1))
    grades = getattr(settings, "banned_ware_grades", None)
    if grades:
        overrides["banned_ware_grades"] = tuple(str(g) for g in grades)
    for attr_field in ("bound_spirit_attr", "registered_sprite_attr"):
        attr = getattr(settings, attr_field, None)
        if attr:
            overrides[attr_field] = str(attr)
    knowledge = getattr(settings, "knowledge_points_expression", None)
    if knowledge:
        overrides["knowledge_points_expression"] = str(knowledge)
    redliner = getattr(settings, "redliner_exclusion", None)
    if redliner is not None:
        overrides["redliner_excludes"] = tuple(str(limb) for limb in redliner)
    exclude = getattr(settings, "exclude_limb_slot", None)
    if exclude:
        overrides["exclude_limb_slot"] = str(exclude)
    table = getattr(settings, "priority_table", None)
    if table:
        overrides["priority_table"] = str(table)
    return Rules(**overrides)  # type: ignore[arg-type]
