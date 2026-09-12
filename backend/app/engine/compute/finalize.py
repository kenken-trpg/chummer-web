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

from ...improvements import EffectsDict, resolve_precedence
from ...notices import term
from ...rules import current_rules
from ..bundle_types import MovementBundle
from ..formulas import _ceil_div
from ..gear.weapons.bonuses import resolve_attr_formulas, resolve_limit_accuracy
from ..limits import (
    _avail_entries,
    _check_avail_limit,
    _check_device_rating_limit,
    _device_rating_entries,
)
from ..magic import attach_focus_tests, attach_spirit_tests
from ..priority import heritage_options
from ..qualities import apply_quality_rules
from ..resonance import attach_complex_form_tests, attach_sprite_tests
from ..ware import cyberleg_movement_agi, limb_attribute_replace
from ._quality_ctx import quality_req_ctx
from .context import Ctx


def _ground_rate(rates: str) -> float:
    """The Ground entry of a metatype `Ground/Swim/Fly` rate string."""
    head = str(rates or "").split("/")[0].strip()
    try:
        return float(head)
    except ValueError:
        return 0.0


def _metres(value: float) -> str:
    """Chummer's `#,0.##`: at most two decimals, no trailing zeros."""
    return f"{round(value, 2):.2f}".rstrip("0").rstrip(".") or "0"


def resolve_movement(meta: dict[str, Any], effects: EffectsDict, agi: int) -> MovementBundle:
    """Ground walk / run in metres and sprint in metres per hit, the way
    Chummer's `CalculatedMovement("Ground")` works them out:
    (rate + multiplier) × (1 + percent) × AGI for walking and running, and
    rate + bonus / 100, scaled by its percent, for sprinting. `agi` is the
    meat AGI — Chummer leaves cyberlimbs out of it."""
    category = "Ground"
    replace = effects.get("movement_replace") or {}

    def rate(kind: str, default: str) -> float:
        if (category, kind) in replace:
            return float(replace[(category, kind)])
        return _ground_rate(str(meta.get(kind) or default))

    def pct(key: str) -> float:
        return 1.0 + int((effects.get(key) or {}).get(category) or 0) / 100.0  # type: ignore[attr-defined]

    walk = (rate("walk", "2/1/0") + int((effects.get("walk_multiplier") or {}).get(category) or 0)) * pct(
        "walk_multiplier_percent"
    )
    run = (rate("run", "4/0/0") + int((effects.get("run_multiplier") or {}).get(category) or 0)) * pct(
        "run_multiplier_percent"
    )
    sprint_bonus = int((effects.get("sprint_bonus") or {}).get(category) or 0)
    sprint = (rate("sprint", "2/1/0") + sprint_bonus / 100.0) * pct("sprint_bonus_percent")
    agi = max(0, int(agi))
    return {
        "walk": _metres(walk * agi),
        "run": _metres(run * agi),
        "sprint": _metres(sprint),
        "sprint_bonus": sprint_bonus,
    }


def totals(ctx: Ctx) -> None:
    resolve_precedence(ctx.effects)  # powers and drugs arrived after the first pass
    if ctx.talent["name"] == "Adept":
        ctx.power_pool = float(ctx.ratings["MAG"]) + float(ctx.effects.get("adept_power_points") or 0)
    elif ctx.talent["name"] == "Mystic Adept":
        ctx.power_pool = float(ctx.state.mystic_pp) + float(ctx.effects.get("adept_power_points") or 0)
    else:
        ctx.power_pool = 0.0
    ctx.power_spent = float(ctx.adept["spent"])
    if ctx.power_spent > ctx.power_pool + 1e-9:
        ctx.err("engine.adept.powerPointsOver", used=f"{ctx.power_spent:g}", max=f"{ctx.power_pool:g}")

    ctx.total = {k: ctx.ratings[k] + ctx.attr_bonus(k) for k in ctx.ratings}
    # ESS is fractional; the attribute-total consumers only ever read integer
    # attrs (STR / AGI / …), so the dict[str, int] inference stays useful.
    ctx.total["ESS"] = ctx.ess  # type: ignore[assignment]
    ctx.limb_replace = limb_attribute_replace(
        ctx.cyber_installed,
        int(ctx.total["STR"]),
        int(ctx.total["AGI"]),
        ctx.attrs_spec,
        dict(ctx.effects.get("extra_limbs") or {}),
    )
    if ctx.limb_replace:
        ctx.total["STR"] = int(ctx.limb_replace["str"])
        ctx.total["AGI"] = int(ctx.limb_replace["agi"])


def finalize(ctx: Ctx) -> None:
    resolve_precedence(ctx.effects)
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
    resolve_attr_formulas(ctx.gear.get("weapons"), ctx.total, int(ctx.effects.get("throw_str") or 0))
    resolve_limit_accuracy(ctx.gear.get("weapons"), ctx.physical_limit)
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

    # meat AGI: `ctx.total` already carries the cyberlimb replacement
    move_agi = ctx.ratings["AGI"] + ctx.attr_bonus("AGI")
    if current_rules().cyberleg_movement:
        leg_agi = cyberleg_movement_agi(ctx.cyber_installed, dict(ctx.effects.get("extra_limbs") or {}))
        if leg_agi is not None:
            move_agi = leg_agi
    ctx.movement = resolve_movement(ctx.meta, ctx.effects, move_agi)

    ctx.quality_report = {}
    ctx.negative_quality_karma = apply_quality_rules(
        ctx.state,
        ctx.qualities,
        ctx.free_quality_ids,
        quality_req_ctx(ctx),
        ctx.errors,
        career=ctx.career,
        report=ctx.quality_report,
    )

    if not ctx.career:
        at_six = [n for n, r in ctx.skill_totals.items() if r >= 6]
        if len(at_six) > 1:
            ctx.err("engine.skills.oneAtSix")
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
            ctx.err("engine.attrs.oneAtNaturalMax")
        if not ctx.is_karma:
            if ctx.spent_physical > ctx.attr_points:
                ctx.err("engine.attrs.pointsOver", used=ctx.spent_physical, max=ctx.attr_points)
            if ctx.spent_special > ctx.special_from_meta:
                ctx.err("engine.attrs.specialPointsOver", used=ctx.spent_special, max=ctx.special_from_meta)
            if ctx.skill_spent > ctx.skill_points:
                ctx.err("engine.skills.pointsOver", used=ctx.skill_spent, max=ctx.skill_points)
            if ctx.group_spent > ctx.group_points:
                ctx.err("engine.skills.groupPointsOver", used=ctx.group_spent, max=ctx.group_points)
            if ctx.know_spent > ctx.know_max:
                ctx.err("engine.skills.knowledgePointsOver", used=ctx.know_spent, max=ctx.know_max)
    if ctx.karma_left < 0:
        ctx.err("engine.karma.negative", karma=ctx.karma_left)
    if ctx.nuyen < 0:
        ctx.err("engine.nuyen.negative", nuyen=ctx.nuyen)
    # SR5 p.98: at Standard power level only 5,000¥ of unspent resources
    # carry over into play (Street 200¥ / Prime 20,000¥). Surface it as a
    # chargen notice rather than silently deleting nuyen, matching Chummer.
    if not ctx.career:
        chargen_leftover = ctx.nuyen - int(ctx.state.nuyen_earned or 0)
        if chargen_leftover > current_rules().nuyen_chargen_keep_max:
            lost = chargen_leftover - current_rules().nuyen_chargen_keep_max
            ctx.warn(
                "engine.nuyen.chargenCarryOver",
                left=f"{chargen_leftover:,}",
                keep=f"{current_rules().nuyen_chargen_keep_max:,}",
                lost=f"{lost:,}",
            )
    # House rules from the settings file that this app has no implementation
    # for. Said out loud once per build: a GM who set `<mysaddppcareer>` and
    # got a sheet that quietly ignored it is worse off than one who was told.
    unsupported = list(ctx.state.settings.unsupported)
    if unsupported:
        ctx.warn("engine.settings.unsupported", count=len(unsupported), tags=", ".join(unsupported))
    if ctx.ess <= 0:
        ctx.err("engine.attrs.essenceDepleted")
    for item in ctx.installed:
        cap_max = float(item.get("capacity_max") or 0)
        if cap_max <= 0:
            continue
        used = float(item.get("capacity_used") or 0)
        if used > cap_max + 1e-9:
            ctx.err("engine.ware.capacityOver", name=term(str(item["name"])), used=f"{used:g}", max=f"{cap_max:g}")

    if not ctx.is_karma:
        allowed = {e["name"] for e in heritage_options(ctx.state.priorities.Heritage)}
        if allowed and ctx.state.metatype not in allowed:
            ctx.err("engine.meta.notInPriority", name=term(ctx.state.metatype))
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
                ctx.gear.get("custom_drugs"),
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
