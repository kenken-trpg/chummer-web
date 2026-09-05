"""Phases 10 + 16 + 17 + 18 — the finishing passes.

``totals(ctx)`` settles ``ctx.total`` (ratings + attribute_bonus, the ESS
override, cyberlimb STR/AGI replace) and the power-point check.
``finalize(ctx)`` derives limits / condition monitor / initiative, attaches
the spirit / focus / complex-form / sprite tests, resolves movement, runs
``apply_quality_rules`` and every chargen validation (rating-6, natural-max,
point overspend, karma / nuyen / essence, capacity, heritage, avail /
device-rating limits).
"""

from __future__ import annotations

from typing import Any

from ...improvements import EffectsDict
from ..bundle_types import MovementBundle
from ..constants import NUYEN_CHARGEN_KEEP_MAX
from ..formulas import _add_leading_int, _ceil_div, _replace_leading_int
from ..limits import (
    _avail_entries,
    _check_avail_limit,
    _check_device_rating_limit,
    _device_rating_entries,
)
from ..magic import attach_focus_tests, attach_spirit_tests
from ..priority import heritage_options
from ..qualities import apply_quality_rules, quality_requirement_context
from ..resonance import attach_complex_form_tests, attach_sprite_tests
from ..ware import limb_attribute_replace
from .context import Ctx


def resolve_movement(meta: dict[str, Any], effects: EffectsDict) -> MovementBundle:
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


def totals(ctx: Ctx) -> None:
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


def finalize(ctx: Ctx) -> None:
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
        ctx.errors.append(f"新円が不足しています（残り {ctx.nuyen}¥）")
    # SR5 p.98: at Standard power level only 5,000¥ of unspent resources
    # carry over into play (Street 200¥ / Prime 20,000¥). Surface it as a
    # chargen notice rather than silently deleting nuyen, matching Chummer.
    if not ctx.career:
        chargen_leftover = ctx.nuyen - int(ctx.state.nuyen_earned or 0)
        if chargen_leftover > NUYEN_CHARGEN_KEEP_MAX:
            lost = chargen_leftover - NUYEN_CHARGEN_KEEP_MAX
            ctx.warnings.append(
                f"未使用新円 {chargen_leftover:,}¥：Standard レベルでは "
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
