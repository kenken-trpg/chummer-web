"""``compute(state)`` and its private resolver helpers.

Relocated verbatim from ``app.engine`` (commit 1 of the compute-phases
split). ``app.engine`` re-exports ``compute`` and the handful of helpers
``store.py`` / tests reference by name.
"""

from __future__ import annotations

from typing import Any

from ...data_loader import (
    CHARGEN_AVAIL_MAX,
    CHARGEN_DEVICE_RATING_MAX,
    CHARGEN_WARE_ATTR_BONUS_MAX,
    catalog,
)
from ...improvements import (
    compact_limit_modifiers,
    special_armor_totals,
)
from ...models import (
    CharacterState,
)
from ..constants import (
    BLACK_MARKET_AVAIL_BONUS,
    KARMA_TO_NUYEN,
    MARTIAL_ART_CHARGEN_STYLE_MAX,
    MARTIAL_ART_CHARGEN_TECHNIQUE_MAX,
    NEGATIVE_QUALITY_KARMA_CAP,
    NUYEN_CHARGEN_KEEP_MAX,
    RES_TALENTS,
    SUM_TO_TEN_BUDGET,
    SUM_TO_TEN_COST,
    TRUST_FUND_STIPEND,
    _normalize_side,
    quality_spirit_category_extra_key,
)
from ..formulas import (  # (stat-expression helpers)
    _add_leading_int,
    _ceil_div,
    _replace_leading_int,
)
from ..limits import (  # (chargen avail / device-rating / ware-attr caps)
    _avail_entries,
    _check_avail_limit,
    _check_device_rating_limit,
    _device_rating_entries,
)
from ..magic import (  # (awakened/emerged pipeline clusters; see engine/magic/)
    attach_focus_tests,
    attach_spirit_tests,
    spell_defense_pools,
    spell_karma_cost,
)
from ..priority import (
    heritage_options,
    priorities_are_unique,
    sum_to_ten_spent,
)
from ..qualities import (  # (quality gather / extra-pick / binder pipeline; see engine/qualities.py)
    _quality_has_selectside,
    apply_quality_rules,
    quality_needs_extra,
    quality_requirement_context,
)
from ..resonance import (  # (technomancer pipeline; see engine/resonance.py)
    attach_complex_form_tests,
    attach_sprite_tests,
    living_persona,
)
from ..ware import (  # (cyberware/bioware pipeline clusters; see engine/ware/)
    _public_installed,
    limb_attribute_replace,
    ware_ranges,
)
from ._career import (  # noqa: F401  (re-exported via app.engine)
    career_raise_karma,
    nuyen_spend_breakdown,
    snapshot_career_baseline,
)
from .bootstrap import (
    bootstrap,
    sync_reward_totals,  # noqa: F401  (re-exported via app.engine)
)
from .context import Ctx
from .economy import economy
from .essence import essence
from .gear import (
    gear_phase,
    resolve_gear,  # noqa: F401  (re-exported via app.engine)
)
from .magic import awakened, spells
from .qualities import (
    effects_and_binders,
    gather,
    resolve_attribute_selects,  # noqa: F401  (re-exported via app.engine)
)
from .ware import ware


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


def default_attributes(meta: dict[str, Any]) -> dict[str, int]:
    out = {}
    for key, spec in meta["attributes"].items():
        if key == "ESS":
            out[key] = int(spec["max"] or 6)
        else:
            out[key] = int(spec["min"])
    return out


def resolve_movement(meta: dict[str, Any], effects: dict[str, Any]) -> dict[str, Any]:
    category = "Ground"
    walk = str(meta.get("walk") or "2/1/0")
    run = str(meta.get("run") or "4/0/0")
    sprint = str(meta.get("sprint") or "2/1/0")
    replace = effects.get("movement_replace") or {}
    if (category, "walk") in replace:
        walk = _replace_leading_int(walk, int(replace[(category, "walk")]))
    if (category, "run") in replace:
        run = _replace_leading_int(run, int(replace[(category, "run")]))
    walk = _add_leading_int(walk, int((effects.get("walk_multiplier") or {}).get(category) or 0))
    run = _add_leading_int(run, int((effects.get("run_multiplier") or {}).get(category) or 0))
    sprint_bonus = int((effects.get("sprint_bonus") or {}).get(category) or 0)
    return {
        "walk": walk,
        "run": run,
        "sprint": sprint,
        "sprint_bonus": sprint_bonus,
    }


def compute(state: CharacterState) -> CharacterState:
    ctx = Ctx(state=state, data=catalog())
    bootstrap(ctx)
    gather(ctx)
    ware(ctx)
    effects_and_binders(ctx)
    essence(ctx)
    awakened(ctx)
    gear_phase(ctx)

    if ctx.talent["name"] == "Adept":
        ctx.power_pool = float(ctx.ratings["MAG"]) + float(ctx.effects.get("adept_power_points") or 0)
    elif ctx.talent["name"] == "Mystic Adept":
        ctx.power_pool = float(ctx.state.mystic_pp) + float(ctx.effects.get("adept_power_points") or 0)
    else:
        ctx.power_pool = 0.0
    ctx.power_spent = float(ctx.adept["spent"])
    if ctx.power_spent > ctx.power_pool + 1e-9:
        ctx.errors.append(f"パワー点が不足しています（使用 {ctx.power_spent:g} / 上限 {ctx.power_pool:g}）")

    bonus = ctx.effects["attribute_bonus"]
    ctx.total = {k: ctx.ratings[k] + int(bonus.get(k, 0)) for k in ctx.ratings}
    # ESS is fractional; the attribute-total consumers only ever read integer
    # attrs (STR / AGI / …), so the dict[str, int] inference stays useful.
    ctx.total["ESS"] = ctx.ess  # type: ignore[assignment]
    ctx.limb_replace = limb_attribute_replace(
        ctx.cyber_installed, int(ctx.total["STR"]), int(ctx.total["AGI"]), ctx.attrs_spec
    )
    if ctx.limb_replace:
        ctx.total["STR"] = int(ctx.limb_replace["str"])
        ctx.total["AGI"] = int(ctx.limb_replace["agi"])

    spells(ctx)

    economy(ctx)

    bod = ctx.total["BOD"]
    agi = ctx.total["AGI"]
    rea = ctx.total["REA"]
    stre = ctx.total["STR"]
    wil = ctx.total["WIL"]
    logi = ctx.total["LOG"]
    intuition = ctx.total["INT"]
    cha = ctx.total["CHA"]

    ctx.physical_limit = _ceil_div((bod * 2 + agi + rea + stre) / 3) + int(ctx.effects.get("limit_physical") or 0)
    ctx.mental_limit = _ceil_div((logi * 2 + intuition + wil) / 3) + int(ctx.effects.get("limit_mental") or 0)
    ctx.social_limit = _ceil_div((cha * 2 + wil + ctx.ess) / 3) + int(ctx.effects.get("limit_social") or 0)
    ctx.cm_phys = 8 + _ceil_div(bod / 2) + ctx.effects["cm_physical"]
    ctx.cm_stun = 8 + _ceil_div(wil / 2) + ctx.effects["cm_stun"]
    ctx.initiative = rea + intuition + ctx.effects["initiative"]
    ctx.initiative_dice = 1 + int(ctx.effects.get("initiative_dice") or 0)
    ctx.warnings.extend(
        attach_spirit_tests(
            list(ctx.spirits.get("public") or []),
            int(ctx.total.get("MAG") or 0),
            ctx.effective_skills,
            ctx.skill_mods["skill_bonus"],
            ctx.total,
            ctx.data["skills"],
        )
    )
    ctx.warnings.extend(
        attach_focus_tests(
            list(ctx.foci.get("public") or []),
            int(ctx.total.get("MAG") or 0),
            ctx.effective_skills,
            ctx.skill_mods["skill_bonus"],
            ctx.total,
            ctx.data["skills"],
            ctx.mental_limit,
        )
    )
    ctx.warnings.extend(
        attach_complex_form_tests(
            list(ctx.resonance.get("public") or []),
            int(ctx.total.get("RES") or 0),
            ctx.effective_skills,
            ctx.skill_mods["skill_bonus"],
            ctx.total,
            ctx.data["skills"],
        )
    )
    ctx.warnings.extend(
        attach_sprite_tests(
            list(ctx.techno_sprites.get("public") or []),
            int(ctx.total.get("RES") or 0),
            ctx.effective_skills,
            ctx.skill_mods["skill_bonus"],
            ctx.total,
            ctx.data["skills"],
        )
    )

    ctx.movement = resolve_movement(ctx.meta, ctx.effects)

    tradition_info = ctx.magic.get("tradition") if isinstance(ctx.magic.get("tradition"), dict) else {}
    ctx.quality_report = {}
    ctx.negative_quality_karma = apply_quality_rules(
        ctx.state,
        ctx.qualities,
        ctx.free_quality_ids,
        quality_requirement_context(
            ctx.state,
            ctx.talent,
            ctx.qualities,
            ctx.meta,
            ctx.ess,
            ctx.ess_lost,
            ctx.effective_skills,
            set(ctx.adept.get("power_names") or []),
            {str(item.get("name") or "") for item in (ctx.magic.get("public") or []) if item.get("name")},
            str((tradition_info or {}).get("name") or ""),
            {item["name"] for item in ctx.cyber_installed},
            {item["name"] for item in ctx.bio_installed},
            ctx.effective_knowledge,
        ),
        ctx.errors,
        career=ctx.career,
        report=ctx.quality_report,
    )

    if not ctx.career:
        at_six = [n for n, r in ctx.skill_totals.items() if r >= 6]
        if len(at_six) > 1:
            ctx.errors.append("作成時にレーティング6の技能は1つまでです")
        # SR5 p.65: no more than one attribute at its natural maximum at
        # character creation (Edge / unused special attributes don't count).
        # Applies to every build method, not just Karma.
        at_natural_max = []
        for key, spec in ctx.attrs_spec.items():
            if key in {"ESS", "EDG", "MAG", "RES"} and key != ctx.special_key:
                continue
            if key not in ctx.ratings:
                continue
            racial_max = int(spec.get("max") or 0) + int(ctx.attr_max_bonus.get(key) or 0)
            if key == "MAG" and ctx.special_key == "MAG":
                racial_max = racial_max + int(ctx.initiation.get("mag_max_bonus") or 0)
            if key == "RES" and ctx.special_key == "RES":
                racial_max = racial_max + int(ctx.submersion.get("res_max_bonus") or 0)
            if racial_max > 0 and int(ctx.ratings.get(key) or 0) >= racial_max:
                at_natural_max.append(key)
        if len(at_natural_max) > 1:
            ctx.errors.append("作成時に自然上限の能力値は1つまでです")
        if not ctx.is_karma:
            if ctx.spent_physical > ctx.attr_points:
                ctx.errors.append(f"能力値点が不足しています（使用 {ctx.spent_physical} / 上限 {ctx.attr_points}）")
            if ctx.spent_special > ctx.special_from_meta:
                ctx.errors.append(
                    f"特殊能力値点が不足しています（使用 {ctx.spent_special} / 上限 {ctx.special_from_meta}）"
                )
            if ctx.skill_spent > ctx.skill_points:
                ctx.errors.append(f"技能点が不足しています（使用 {ctx.skill_spent} / 上限 {ctx.skill_points}）")
            if ctx.group_spent > ctx.group_points:
                ctx.errors.append(f"技能グループ点が不足しています（使用 {ctx.group_spent} / 上限 {ctx.group_points}）")
            if ctx.know_spent > ctx.know_max:
                ctx.errors.append(f"知識技能点が不足しています（使用 {ctx.know_spent} / 上限 {ctx.know_max}）")
    if ctx.karma_left < 0:
        ctx.errors.append(f"カルマが不足しています（残り {ctx.karma_left}）")
    if ctx.nuyen < 0:
        ctx.errors.append(f"ニューエンが不足しています（残り {ctx.nuyen}¥）")
    # SR5 p.98: at Standard power level only 5,000¥ of unspent resources
    # carry over into play (Street 200¥ / Prime 20,000¥). Surface it as a
    # chargen notice rather than silently deleting nuyen, matching Chummer.
    if not ctx.career:
        chargen_leftover = ctx.nuyen - int(ctx.state.nuyen_earned or 0)
        if chargen_leftover > NUYEN_CHARGEN_KEEP_MAX:
            lost = chargen_leftover - NUYEN_CHARGEN_KEEP_MAX
            ctx.warnings.append(
                f"未使用ニューエン {chargen_leftover:,}¥：Standard レベルでは "
                f"{NUYEN_CHARGEN_KEEP_MAX:,}¥ までしか持ち越せません（超過分 {lost:,}¥ は原則失われます）"
            )
    if ctx.ess <= 0:
        ctx.errors.append("エッセンスが0以下です")
    for item in ctx.installed:
        cap_max = float(item.get("capacity_max") or 0)
        if cap_max <= 0:
            continue
        used = float(item.get("capacity_used") or 0)
        if used > cap_max + 1e-9:
            ctx.errors.append(f"{item['name']} の容量超過（{used:g}/{cap_max:g}）")

    if not ctx.is_karma:
        allowed = {e["name"] for e in heritage_options(ctx.state.priorities.Heritage)}
        if allowed and ctx.state.metatype not in allowed:
            ctx.errors.append(f"{ctx.state.metatype} はこの優先度のメタに含まれません")
    if not ctx.career:
        _check_avail_limit(
            _avail_entries(
                ctx.cyber_installed,
                ctx.bio_installed,
                ctx.gear.get("armor_items"),
                ctx.gear.get("armor_mods"),
                ctx.gear.get("weapons"),
                ctx.gear.get("weapon_accessories"),
                ctx.gear.get("commlinks"),
                ctx.gear.get("cyberdecks"),
                ctx.gear.get("rccs"),
                ctx.gear.get("optics"),
                ctx.gear.get("programs"),
                ctx.gear.get("apps"),
                ctx.gear.get("sensors"),
                ctx.gear.get("drones"),
                ctx.gear.get("vehicles"),
                ctx.gear.get("vehicle_mods"),
                ctx.gear.get("weapon_mounts"),
                ctx.gear.get("gear"),
                ctx.gear.get("lifestyles"),
                ctx.foci.get("public"),
            ),
            ctx.effects,
            ctx.errors,
        )
        _check_device_rating_limit(
            _device_rating_entries(
                ctx.cyber_installed,
                ctx.bio_installed,
                ctx.gear.get("commlinks"),
                ctx.gear.get("cyberdecks"),
                ctx.gear.get("rccs"),
                ctx.gear.get("optics"),
                ctx.gear.get("sensors"),
                ctx.gear.get("gear"),
            ),
            ctx.errors,
        )

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
    return ctx.state
