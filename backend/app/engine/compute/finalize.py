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

from collections.abc import Mapping

from ...data_loader import PHYSICAL_ATTRS
from ...improvements import resolve_precedence
from ...notices import term
from ...rules import current_rules
from ..formulas import _ceil_div
from ..gear.weapons.bonuses import resolve_attr_formulas, resolve_limit_accuracy
from ..home_node import resolve_home_node
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
from ..special_attributes import is_ai
from ..ware import cyberleg_movement_agi, limb_attribute_replace
from ._movement import resolve_movement
from ._quality_ctx import quality_req_ctx
from ._shapeshifter import in_metahuman_form, into_metahuman_form, metahuman_form
from .context import Ctx


def _inherent_limits(total: Mapping[str, int | float], essence: float) -> tuple[int, int, int]:
    """Calculate the SR5 physical, mental and social limits before modifiers."""
    body = int(total["BOD"])
    reaction = int(total["REA"])
    strength = int(total["STR"])
    willpower = int(total["WIL"])
    logic = int(total["LOG"])
    intuition = int(total["INT"])
    charisma = int(total["CHA"])

    return (
        _ceil_div((strength * 2 + body + reaction) / 3),
        _ceil_div((logic * 2 + intuition + willpower) / 3),
        _ceil_div((charisma * 2 + willpower + _ceil_div(essence)) / 3),
    )


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
    metahuman = in_metahuman_form(ctx)
    if metahuman:
        ctx.animal_total = dict(ctx.total)
        ctx.total = into_metahuman_form(ctx, ctx.total)
    # `<dontusecyberlimbcalculation>`: the body keeps its own STR / AGI
    ctx.limb_replace = (
        None
        if current_rules().dont_use_cyberlimb_calculation
        else limb_attribute_replace(
            ctx.cyber_installed,
            int(ctx.total["STR"]),
            int(ctx.total["AGI"]),
            ctx.attrs_spec,
            dict(ctx.effects.get("extra_limbs") or {}),
        )
    )
    if ctx.limb_replace:
        ctx.total["STR"] = int(ctx.limb_replace["str"])
        ctx.total["AGI"] = int(ctx.limb_replace["agi"])
    if not metahuman:
        ctx.animal_total = ctx.total


def finalize(ctx: Ctx) -> None:
    resolve_precedence(ctx.effects)
    _limits(ctx)
    _condition_monitors(ctx)
    _initiative(ctx)
    _attach_tests(ctx)
    _movement(ctx)
    ctx.quality_report = {}
    ctx.negative_quality_karma = apply_quality_rules(
        ctx.state,
        ctx.qualities,
        ctx.free_quality_ids,
        quality_req_ctx(ctx),
        ctx.errors,
        career=ctx.career,
        report=ctx.quality_report,
        warnings=ctx.warnings,
        free_positive_karma=int(ctx.life.get("free_positive_qualities") or 0),
        free_negative_karma=int(ctx.life.get("free_negative_qualities") or 0),
        restriction=ctx.meta.get("quality_restriction"),
    )

    if not ctx.career:
        _check_chargen_points(ctx)
    if ctx.karma_left < 0:
        ctx.err("engine.karma.negative", karma=ctx.karma_left)
    if ctx.nuyen < 0:
        ctx.err("engine.nuyen.negative", nuyen=ctx.nuyen)
    if not ctx.career:
        _carryover_notices(ctx)
    # House rules from the settings file that this app has no implementation
    # for. Said out loud once per build: a GM who set `<mysaddppcareer>` and
    # got a sheet that quietly ignored it is worse off than one who was told.
    unsupported = list(ctx.state.settings.unsupported)
    if unsupported:
        ctx.warn("engine.settings.unsupported", count=len(unsupported), tags=", ".join(unsupported))
    if ctx.ess <= 0:
        ctx.err("engine.attrs.essenceDepleted")
    _check_capacity(ctx)
    if not ctx.is_karma:
        allowed = {e["name"] for e in heritage_options(ctx.state.priorities.Heritage)}
        if allowed and ctx.state.metatype not in allowed:
            ctx.err("engine.meta.notInPriority", name=term(ctx.state.metatype))
    if not ctx.career:
        _check_gear_limits(ctx)


def _limits(ctx: Ctx) -> None:
    """The three limits, the A.I.'s home node they may come from, and the
    weapon values that read the physical one."""
    physical_base, mental_base, social_base = _inherent_limits(ctx.total, ctx.ess)
    ctx.is_ai = is_ai(ctx.attrs_spec, ctx.special_floors)
    ctx.home_node, node_warnings = resolve_home_node(
        ctx.state, ctx.gear, ai=ctx.is_ai, depth=int(ctx.total.get("DEP") or 0)
    )
    ctx.warnings.extend(node_warnings)
    if ctx.home_node:
        # Chummer `LimitMental` / `LimitSocial` with a home node: its Data
        # Processing where higher, and in place of the second CHA
        # a vehicle's Pilot where higher, and its Sensor for the mental one
        dp = max(ctx.home_node["dataprocessing"], ctx.home_node["pilot"])
        mental_base = max(mental_base, dp, ctx.home_node["sensor"])
        social_base = _ceil_div((int(ctx.total["CHA"]) + dp + int(ctx.total["WIL"]) + _ceil_div(ctx.ess)) / 3)
    if ctx.is_ai:
        # Chummer `LimitPhysical`: an A.I.'s is its vehicle's Handling, or
        # nothing outside one; no modifier applies
        ctx.physical_limit = ctx.home_node["handling"] if ctx.home_node and ctx.home_node["vehicle"] else 0
    else:
        ctx.physical_limit = physical_base + int(ctx.effects.get("limit_physical") or 0)
    ctx.mental_limit = mental_base + int(ctx.effects.get("limit_mental") or 0)
    ctx.social_limit = social_base + int(ctx.effects.get("limit_social") or 0)
    resolve_attr_formulas(ctx.gear.get("weapons"), ctx.total, int(ctx.effects.get("throw_str") or 0))
    resolve_limit_accuracy(ctx.gear.get("weapons"), ctx.physical_limit)


def _condition_monitors(ctx: Ctx) -> None:
    if ctx.is_ai:
        # Chummer `PhysicalCM`: an A.I.'s is its Core monitor, 8 + DEP / 2;
        # `StunCM` is its home node's Matrix monitor, or nothing at all.
        if ctx.home_node and ctx.home_node["vehicle"]:
            # in a vehicle or drone, its own damage track (`Vehicle.PhysicalCM`)
            ctx.cm_phys = ctx.home_node["physical_cm"]
        else:
            ctx.cm_phys = 8 + _ceil_div(int(ctx.total.get("DEP") or 0) / 2) + ctx.effects["cm_physical"]
        ctx.cm_stun = ctx.home_node["matrix_cm"] if ctx.home_node else 0
    else:
        ctx.cm_phys = 8 + _ceil_div(ctx.total["BOD"] / 2) + ctx.effects["cm_physical"]
        ctx.cm_stun = 8 + _ceil_div(ctx.total["WIL"] / 2) + ctx.effects["cm_stun"]


def _initiative(ctx: Ctx) -> None:
    ctx.initiative = ctx.total["REA"] + ctx.total["INT"] + ctx.effects["initiative"]
    # Chummer `InitiativeDice`: the settings' minimum plus what augmentations
    # add, never past the maximum — Wired Reflexes 3 on top of Synaptic
    # Booster 3 is still five dice.
    ctx.initiative_dice = min(
        current_rules().min_initiative_dice + int(ctx.effects.get("initiative_dice") or 0),
        current_rules().max_initiative_dice,
    )


def _attach_tests(ctx: Ctx) -> None:
    """The dice pools of what the character summons, binds and threads."""
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


def _movement(ctx: Ctx) -> None:
    # meat AGI: `ctx.total` already carries the cyberlimb replacement
    move_agi = ctx.ratings["AGI"] + ctx.attr_bonus("AGI")
    leg_agi = None
    if current_rules().cyberleg_movement:
        leg_agi = cyberleg_movement_agi(ctx.cyber_installed, dict(ctx.effects.get("extra_limbs") or {}))
    # the animal's, which a shapeshifter in the metahuman form keeps beside
    ctx.animal_movement = resolve_movement(
        ctx.meta,
        ctx.effects,
        move_agi,
        swim_agi=int(ctx.animal_total["AGI"]),
        swim_str=int(ctx.animal_total["STR"]),
        ground_agi=leg_agi,
    )
    form = metahuman_form(ctx) if in_metahuman_form(ctx) else None
    ctx.movement = (form or {}).get("movement") or ctx.animal_movement


def _check_chargen_points(ctx: Ctx) -> None:
    """Creation only: attributes at their natural maximum, and every point
    pool a priority build can overspend."""
    # No count of skills at rating 6 here: "one at 6 or two at 5" is the
    # SR4 creation rule. SR5 caps a skill at 6 (7 with Aptitude) and no
    # more — the cap is `skill_rating_cap` — and Chummer checks the same.
    # SR5 p.65: no more than one attribute at its natural maximum at
    # character creation. Chummer counts its `AttributeList` — BOD to WIL
    # — and not the special attributes: an Adept with MAG 6 may still
    # take AGI to 6. Applies to every build method, not just Karma.
    at_natural_max = []
    for key in PHYSICAL_ATTRS:
        spec = ctx.attrs_spec.get(key)
        if spec is None or key not in ctx.ratings:
            continue
        racial_max = int(spec.get("max") or 0) + int(ctx.attr_max_bonus.get(key) or 0)
        if racial_max > 0 and int(ctx.ratings.get(key) or 0) >= racial_max:
            at_natural_max.append(key)
    limit = current_rules().chargen_attributes_at_max
    if len(at_natural_max) > limit:
        ctx.err("engine.attrs.oneAtNaturalMax", count=len(at_natural_max), limit=limit)
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


def _carryover_notices(ctx: Ctx) -> None:
    """Creation only: what of the unspent nuyen and karma does not survive
    into play."""
    # SR5 p.98: at Standard power level only 5,000¥ of unspent resources
    # carry over into play (Street 200¥ / Prime 20,000¥). Surface it as a
    # chargen notice rather than silently deleting nuyen, matching Chummer.
    chargen_leftover = ctx.nuyen - int(ctx.state.nuyen_earned or 0)
    if chargen_leftover > current_rules().nuyen_chargen_keep_max:
        lost = chargen_leftover - current_rules().nuyen_chargen_keep_max
        ctx.warn(
            "engine.nuyen.chargenCarryOver",
            left=f"{chargen_leftover:,}",
            keep=f"{current_rules().nuyen_chargen_keep_max:,}",
            lost=f"{lost:,}",
        )
    # `<karmacarryover>` (SR5 p.107: 7): unspent chargen karma past it is
    # lost when play starts. Chummer asks before finishing; a notice here.
    karma_leftover = ctx.karma_left - int(ctx.state.karma_earned or 0)
    keep = current_rules().karma_carryover
    if karma_leftover > keep:
        ctx.warn("engine.karma.chargenCarryOver", left=karma_leftover, keep=keep, lost=karma_leftover - keep)


def _check_capacity(ctx: Ctx) -> None:
    # `<enforcecapacity>` off: a ware may hold more than its capacity
    for item in ctx.installed if current_rules().enforce_capacity else []:
        cap_max = float(item.get("capacity_max") or 0)
        if cap_max <= 0:
            continue
        used = float(item.get("capacity_used") or 0)
        if used > cap_max + 1e-9:
            ctx.err("engine.ware.capacityOver", name=term(str(item["name"])), used=f"{used:g}", max=f"{cap_max:g}")


def _check_gear_limits(ctx: Ctx) -> None:
    """Creation only: the availability and device-rating caps."""
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
