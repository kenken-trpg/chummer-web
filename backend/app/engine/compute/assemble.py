"""Phase 19 — assemble ``ctx.state.derived``.

Writes ``ctx.state.attributes`` from the resolved ratings and builds the
~195-key ``state.derived`` dict the API returns. Also hosts
``_effective_attr_spec`` (the metatype-info attribute rewrite).
"""

from __future__ import annotations

from ...data_loader import (
    CHARGEN_AVAIL_MAX,
    CHARGEN_DEVICE_RATING_MAX,
    CHARGEN_WARE_ATTR_BONUS_MAX,
)
from ...improvements import compact_limit_modifiers, special_armor_totals
from ..constants import (
    BLACK_MARKET_AVAIL_BONUS,
    KARMA_TO_NUYEN,
    MARTIAL_ART_CHARGEN_STYLE_MAX,
    MARTIAL_ART_CHARGEN_TECHNIQUE_MAX,
    NEGATIVE_QUALITY_KARMA_CAP,
    RES_TALENTS,
    SUM_TO_TEN_BUDGET,
    SUM_TO_TEN_COST,
    TRUST_FUND_STIPEND,
    _normalize_side,
    quality_spirit_category_extra_key,
)
from ..magic import spell_defense_pools, spell_karma_cost
from ..priority import priorities_are_unique, sum_to_ten_spent
from ..qualities import _quality_has_selectside, quality_needs_extra
from ..resonance import living_persona
from ..ware import _public_installed, ware_ranges
from .context import Ctx


def _effective_attr_spec(
    attrs_spec: dict[str, dict[str, int | float]],
    special_key: str | None,
    talent_start: int,
    mag_max_bonus: int = 0,
    res_max_bonus: int = 0,
) -> dict[str, dict[str, int | float]]:
    out = {key: dict(spec) for key, spec in attrs_spec.items()}
    if special_key == "MAG":
        out["MAG"]["min"] = max(talent_start, 1)
        out["MAG"]["max"] = int(out["MAG"].get("max") or 0) + max(0, int(mag_max_bonus))
        out["RES"]["min"] = 0
        out["RES"]["max"] = 0
    elif special_key == "RES":
        out["RES"]["min"] = max(talent_start, 1)
        out["RES"]["max"] = int(out["RES"].get("max") or 0) + max(0, int(res_max_bonus))
        out["MAG"]["min"] = 0
        out["MAG"]["max"] = 0
    else:
        out["MAG"]["min"] = 0
        out["MAG"]["max"] = 0
        out["RES"]["min"] = 0
        out["RES"]["max"] = 0
    return out


def assemble(ctx: Ctx) -> None:
    ctx.state.attributes = ctx.ratings
    sum_spent = sum_to_ten_spent(ctx.state.priorities)
    ctx.state.derived = {
        "errors": ctx.errors,
        "warnings": ctx.warnings,
        "build_method": ctx.state.build_method,
        "sum_to_ten": {
            "used": sum_spent,
            "max": SUM_TO_TEN_BUDGET,
            "costs": dict(SUM_TO_TEN_COST),
            "unique": priorities_are_unique(ctx.state.priorities),
        },
        "karma_chargen": {
            "enabled": ctx.is_karma,
            "pool": ctx.karma_pool if ctx.is_karma else 0,
            "nuyen_karma": int(ctx.state.karma_nuyen or 0),
            "nuyen_karma_max": int(ctx.nuyen_karma_max),
            "nuyen_per_karma": KARMA_TO_NUYEN,
            "metatype": ctx.metatype_karma_cost if ctx.is_karma else 0,
            "attributes": ctx.attr_karma if ctx.is_karma else 0,
            "skills": ctx.skill_buy_karma if ctx.is_karma else 0,
            "knowledge": ctx.knowledge_karma if ctx.is_karma else 0,
            "specializations": ctx.spec_karma if ctx.is_karma else 0,
            "qualities": ctx.karma_from_q,
            "other": ctx.mystic_karma
            + ctx.extra_adept_karma
            + ctx.spell_karma
            + int(ctx.contacts.get("karma") or 0)
            + int(ctx.martial.get("karma") or 0)
            + int(ctx.initiation.get("karma") or 0)
            + int(ctx.submersion.get("karma") or 0),
        },
        "totals": ctx.total,
        "limits": {
            "physical": ctx.physical_limit,
            "mental": ctx.mental_limit,
            "social": ctx.social_limit,
        },
        "limit_modifiers": compact_limit_modifiers(ctx.effects),
        "condition_monitor": {"physical": ctx.cm_phys, "stun": ctx.cm_stun},
        "initiative": {"value": ctx.initiative, "dice": ctx.initiative_dice},
        "movement": ctx.movement,
        "essence": ctx.ess,
        "essence_lost": ctx.ess_lost,
        "essence_lost_cyber": ctx.ess_lost_cyber,
        "essence_lost_bio": ctx.ess_lost_bio,
        "armor": int(ctx.effects["armor"]) + int(ctx.gear.get("armor") or 0),
        "special_armor": special_armor_totals(ctx.effects),
        "worn_armor": ctx.gear.get("worn_name") or "",
        "armor_items": ctx.gear.get("armor_items") or [],
        "armor_mods": ctx.gear.get("armor_mods") or [],
        "weapons": ctx.gear.get("weapons") or [],
        "weapon_accessories": ctx.gear.get("weapon_accessories") or [],
        "recoil": ctx.gear.get("recoil") or {"str": 0, "str_rc": 0, "free": 1},
        "active_drugs": ctx.active_drugs,
        "commlinks": ctx.gear.get("commlinks") or [],
        "cyberdecks": ctx.gear.get("cyberdecks") or [],
        "rccs": ctx.gear.get("rccs") or [],
        "optics": ctx.gear.get("optics") or [],
        "programs": ctx.gear.get("programs") or [],
        "apps": ctx.gear.get("apps") or [],
        "sensors": ctx.gear.get("sensors") or [],
        "drones": ctx.gear.get("drones") or [],
        "vehicles": ctx.gear.get("vehicles") or [],
        "vehicle_mods": ctx.gear.get("vehicle_mods") or [],
        "weapon_mounts": ctx.gear.get("weapon_mounts") or [],
        "gear": ctx.gear.get("gear") or [],
        "lifestyles": ctx.gear.get("lifestyles") or [],
        "commlink": ctx.gear.get("commlink"),
        "cyberdeck": ctx.gear.get("cyberdeck"),
        "rcc": ctx.gear.get("rcc"),
        "lifestyle": ctx.gear.get("lifestyle"),
        "nuyen": ctx.nuyen,
        "nuyen_spent": ctx.nuyen_spent,
        "nuyen_pool": ctx.nuyen_pool,
        "nuyen_earned": int(ctx.state.nuyen_earned or 0),
        "karma_earned": int(ctx.state.karma_earned or 0),
        "career": ctx.career,
        "career_advancement_karma": int(ctx.career_adv_karma),
        "career_advancement_lines": ctx.career_adv_lines,
        "nuyen_amt": int(ctx.effects.get("nuyen_amt") or 0),
        "nuyen_karma_max": int(ctx.nuyen_karma_max),
        "trustfund": int(ctx.effects.get("trustfund") or 0),
        "trustfund_label": TRUST_FUND_STIPEND.get(int(ctx.effects.get("trustfund") or 0), ""),
        "ambidextrous": bool(ctx.effects.get("ambidextrous")),
        "overclocker": bool(ctx.effects.get("overclocker")),
        "special_modification_limit": {
            "used": int(ctx.gear.get("special_modification_used") or 0),
            "max": int(ctx.effects.get("special_modification_limit") or 0),
        },
        "friends_in_high_places": bool(ctx.effects.get("friends_in_high_places")),
        "made_man": bool(ctx.effects.get("made_man")),
        "black_market_discount": bool(ctx.effects.get("black_market_discount")),
        "black_market_category": ctx.bmp_category if ctx.bmp_active else "",
        "black_market_contact_id": ctx.bmp_contact_id if ctx.bmp_active else "",
        "black_market_avail_bonus": BLACK_MARKET_AVAIL_BONUS if ctx.bmp_active else 0,
        "dealer_connection_categories": list(ctx.effects.get("dealer_connection_categories") or []),
        "cyberware_ess_multiplier": int(ctx.effects.get("cyberware_ess_multiplier") or 100),
        "bioware_ess_multiplier": int(ctx.effects.get("bioware_ess_multiplier") or 100),
        "skill_rating_max": ctx.skill_rating_cap,
        "skill_group_max": ctx.skill_group_cap,
        "avail_limit": None if ctx.career else CHARGEN_AVAIL_MAX,
        "device_rating_limit": None if ctx.career else CHARGEN_DEVICE_RATING_MAX,
        "ware_attr_limit": None if ctx.career else CHARGEN_WARE_ATTR_BONUS_MAX,
        "ware_attr_bonus": ctx.ware_attr_bonus,
        "karma": {
            "pool": ctx.karma_pool,
            "spent": ctx.karma_spent,
            "remaining": ctx.karma_left,
            "negative": {
                "used": ctx.negative_quality_karma,
                "max": None if ctx.career else NEGATIVE_QUALITY_KARMA_CAP,
            },
        },
        "power_points": {"used": ctx.power_spent, "max": ctx.power_pool},
        "metagenic": ctx.quality_report.get("metagenic"),
        "adept_powers": ctx.adept["public"],
        "mystic_pp": ctx.state.mystic_pp,
        "way_discount": {"used": ctx.adept.get("discount_used") or 0, "max": ctx.adept.get("discount_max") or 0},
        "mentor": ctx.mentor.get("public"),
        "needs_mentor": ctx.needs_mentor,
        "qi_foci": ctx.qi.get("public") or [],
        "foci": ctx.foci.get("public") or [],
        "focus_limits": ctx.focus_limits,
        "spirits": ctx.spirits.get("public") or [],
        "enhancements": ctx.enhancements.get("public") or [],
        "damage_resistance": int(ctx.effects.get("damage_resistance") or 0),
        "unarmed_dv": int(ctx.effects.get("unarmed_dv") or 0),
        "unarmed_physical": bool(ctx.effects.get("unarmed_physical")),
        "unlock_skills": list(ctx.effects.get("unlock_skills") or []),
        "spells": ctx.magic.get("public") or [],
        "spell_points": {
            "used": ctx.magic.get("used") or 0,
            "free": ctx.magic.get("free_max") or 0,
            "paid": ctx.magic.get("paid") or 0,
            "karma": ctx.magic.get("karma") or 0,
            "spell_karma": spell_karma_cost("spell", ctx.effects),
        },
        "tradition": ctx.magic.get("tradition"),
        "drain_resist": {"pool": ctx.magic.get("resist") or 0, "attrs": ctx.magic.get("resist_attrs") or "WIL+INT"},
        "complex_forms": ctx.resonance.get("public") or [],
        "complex_form_points": {
            "used": ctx.resonance.get("used") or 0,
            "free": ctx.resonance.get("free_max") or 0,
            "paid": ctx.resonance.get("paid") or 0,
        },
        "sprites": ctx.techno_sprites.get("public") or [],
        "stream": ctx.resonance.get("stream"),
        "fade_resist": {
            "pool": ctx.resonance.get("resist") or 0,
            "attrs": ctx.resonance.get("resist_attrs") or "WIL+RES",
        },
        "living_persona": (
            living_persona(
                ctx.total,
                int(ctx.total.get("RES") or 0),
                ctx.effects.get("living_persona") if isinstance(ctx.effects.get("living_persona"), dict) else None,
                int(ctx.effects.get("matrix_initiative_dice") or 0),
            )
            if ctx.talent["name"] in RES_TALENTS
            else None
        ),
        "points": {
            "attributes": {"used": ctx.spent_physical, "max": ctx.attr_points},
            "special": {"used": ctx.spent_special, "max": ctx.special_from_meta},
            "skills": {"used": ctx.skill_spent, "max": ctx.skill_points},
            "skill_groups": {"used": ctx.group_spent, "max": ctx.group_points},
            "knowledge": {"used": ctx.know_spent, "max": ctx.know_max},
            "contacts": {"used": ctx.contacts.get("used") or 0, "max": ctx.contacts.get("free") or 0},
        },
        "knowledge_skills": ctx.knowledge["public"],
        "contacts": ctx.contacts.get("public") or [],
        "contact_points": {
            "used": ctx.contacts.get("used") or 0,
            "free": ctx.contacts.get("free") or 0,
            "paid": ctx.contacts.get("paid") or 0,
            "karma": int(ctx.contacts.get("karma") or 0),
            "karma_per_point": int(ctx.contacts.get("karma_per_point", 1)),
        },
        "martial_arts": ctx.martial.get("public") or [],
        "martial_art_points": {
            "styles": ctx.martial.get("style_count") or 0,
            "style_max": ctx.martial.get("style_max") or MARTIAL_ART_CHARGEN_STYLE_MAX,
            "techniques": ctx.martial.get("technique_count") or 0,
            "technique_max": ctx.martial.get("technique_max") or MARTIAL_ART_CHARGEN_TECHNIQUE_MAX,
            "karma": ctx.martial.get("karma") or 0,
        },
        "martial_spec_options": ctx.martial.get("spec_extras") or {},
        "unarmed_reach": int(ctx.effects.get("unarmed_reach") or 0) + int(ctx.effects.get("reach") or 0),
        "unarmed_ap": int(ctx.effects.get("unarmed_ap") or 0),
        "reach": int(ctx.effects.get("reach") or 0),
        "lifestyle_cost_mod": int(ctx.effects.get("lifestyle_cost") or 0),
        "street_cred": ctx.street_cred_total,
        "notoriety": ctx.notoriety_total,
        "notoriety_quality": ctx.quality_notoriety,
        "notoriety_bonus": int(ctx.state.notoriety_bonus or 0),
        "fame": int(ctx.effects.get("fame") or 0),
        "public_awareness": ctx.public_awareness_total,
        "erased": bool(ctx.effects.get("erased")),
        "excon": bool(ctx.effects.get("excon")),
        "reward_log": [
            {"id": row.id, "label": row.label, "karma": int(row.karma or 0), "nuyen": int(row.nuyen or 0)}
            for row in (ctx.state.reward_log or [])
        ],
        "karma_spend_breakdown": ctx.karma_spend_lines,
        "nuyen_spend_breakdown": ctx.nuyen_spend_lines,
        "fatigue_resist": int(ctx.effects.get("fatigue_resist") or 0),
        "spell_resistance": int(ctx.effects.get("spell_resistance") or 0),
        "spell_defense": spell_defense_pools(ctx.effects),
        "spell_dice_pool": list(ctx.effects.get("spell_dice_pool") or []),
        "action_dice_pools": list(ctx.effects.get("action_dice_pools") or []),
        "test_mods": dict(ctx.effects.get("test_mods") or {}),
        "cm_recovery": {
            "physical": int(ctx.effects.get("cm_recovery_physical") or 0)
            + (int(ctx.ess) if ctx.effects.get("cm_recovery_physical_add_ess") else 0),
            "stun": int(ctx.effects.get("cm_recovery_stun") or 0)
            + (int(ctx.ess) if ctx.effects.get("cm_recovery_stun_add_ess") else 0),
        },
        "essence_penalty": round(float(ctx.effects.get("essence_penalty") or 0), 4),
        "attribute_max_bonus": dict(ctx.attr_max_bonus),
        "disabled_skills": list(ctx.effects.get("disabled_skills") or []),
        "disabled_skill_groups": list(ctx.effects.get("disabled_skill_groups") or []),
        "blocked_default_categories": list(ctx.effects.get("blocked_default_categories") or []),
        "native_language_limit": int(ctx.knowledge.get("native_limit") or 1),
        "prototype_transhuman_ess": float(ctx.effects.get("prototype_transhuman_ess") or 0),
        "burnout_way": bool(ctx.effects.get("burnout_way")),
        "disabled_cyberware_grades": list(ctx.effects.get("disabled_cyberware_grades") or []),
        "disabled_bioware_grades": list(ctx.effects.get("disabled_bioware_grades") or []),
        "limit_spell_categories": list(ctx.effects.get("limit_spell_categories") or []),
        "limit_spirit_categories": list(ctx.effects.get("limit_spirit_categories") or []),
        "allow_spell_categories": list(ctx.effects.get("allow_spell_categories") or []),
        "allow_spell_ranges": list(ctx.effects.get("allow_spell_ranges") or []),
        "spell_range_gated": bool(ctx.magic.get("range_gated")),
        "block_spell_descriptors": list(ctx.effects.get("block_spell_descriptors") or []),
        "extra_spirits": list(ctx.effects.get("extra_spirits") or []),
        "add_spirit_picks": list(ctx.effects.get("add_spirit_picks") or []),
        "initiate_grade": int(ctx.initiation.get("grade") or 0),
        "initiation": {
            "grade": int(ctx.initiation.get("grade") or 0),
            "karma": int(ctx.initiation.get("karma") or 0),
            "choices": ctx.initiation.get("choices") or [],
            "metamagics": ctx.initiation.get("metamagics") or [],
            "arts": ctx.initiation.get("arts") or [],
        },
        "submersion_grade": int(ctx.submersion.get("grade") or 0),
        "submersion": {
            "grade": int(ctx.submersion.get("grade") or 0),
            "karma": int(ctx.submersion.get("karma") or 0),
            "choices": ctx.submersion.get("choices") or [],
            "echoes": ctx.submersion.get("echoes") or [],
        },
        "skill_totals": ctx.skill_totals,
        "skill_specializations": ctx.specs["specs"],
        "skill_expertises": ctx.expertises,
        "exotic_skills": ctx.exotic["public"],
        "skillsoft": ctx.skillsofts["all"],
        "skillwires": ctx.skillsofts["skillwires"],
        "skilljack": ctx.skillsofts["skilljack"],
        "skill_bonus": ctx.skill_mods["skill_bonus"],
        "skill_group_bonus": ctx.skill_mods["skill_group_bonus"],
        "skill_category_bonus": ctx.skill_mods["skill_category_bonus"],
        "skill_bonus_notes": ctx.skill_mods["skill_bonus_notes"],
        "skill_max_bonus": ctx.skill_picks["skill_max_bonus"],
        "skill_pick_slots": ctx.skill_picks["slots"],
        "enabled_tabs": sorted(ctx.enabled),
        "unimplemented_bonuses": ctx.effects["unimplemented"],
        "qualities": [
            {
                "id": q["id"],
                "name": q["name"],
                "karma": 0 if q["id"] in ctx.free_quality_ids else q["karma"],
                "category": q["category"],
                "source": q["source"],
                "needs_extra": quality_needs_extra(q),
                "extra": ctx.state.quality_extras.get(q["id"]) or "",
                "spirit_extra": ctx.state.quality_extras.get(quality_spirit_category_extra_key(q["id"])) or "",
                "extra_kind": q.get("extra_kind"),
                "select_options": list(q.get("select_options") or []),
                "spirit_options": list(q.get("spirit_options") or []),
                "expertise_skill": q.get("expertise_skill") or "",
                "add_spirit_count": int(q.get("add_spirit_count") or 0),
                "selectside": _quality_has_selectside(q),
                "side": _normalize_side(ctx.state.quality_extras.get(q["id"])) if _quality_has_selectside(q) else None,
                "free": q["id"] in ctx.free_quality_ids or bool(q.get("onlyprioritygiven")),
            }
            for q in ctx.qualities
        ],
        "cyberware": [_public_installed(item) for item in ctx.cyber_installed],
        "bioware": [_public_installed(item) for item in ctx.bio_installed],
        "ware_ranges": ware_ranges(ctx.attrs_spec),
        "limb_replace": ctx.limb_replace,
        "limb_quality": ctx.limb_quality,
        "talent": ctx.talent,
        "metatype_info": {
            "name": ctx.meta["name"],
            "parent": ctx.meta.get("parent"),
            "attributes": {
                key: {
                    **spec,
                    "max": int(spec.get("max") or 0) + int(ctx.attr_max_bonus.get(key) or 0),
                    "aug": int(spec.get("aug") or 0) + int(ctx.attr_max_bonus.get(key) or 0),
                }
                for key, spec in _effective_attr_spec(
                    ctx.attrs_spec,
                    ctx.special_key,
                    ctx.talent_start,
                    int(ctx.initiation.get("mag_max_bonus") or 0),
                    int(ctx.submersion.get("res_max_bonus") or 0),
                ).items()
            },
            "source": ctx.meta.get("source"),
        },
        "translations": {
            k: ctx.data["translations"].get(k, k) for k in [ctx.state.metatype, ctx.state.metavariant or ""]
        },
    }
