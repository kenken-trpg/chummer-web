"""Phases 5 + 6 — essence penalty and the attribute-ratings loop
(racial min/max, MAG/RES caps, ESS)."""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal

from ...rules import current_rules
from ..constants import MAG_TALENTS, RES_TALENTS
from ..pricing import apply_ware_essence_multipliers
from ..resonance import _cyberadept_res_penalty_reduction
from ..special_attributes import is_ai
from .context import Ctx


def _min_drop(floor: int, cap: int, penalty: int, maximum_only: bool) -> int:
    """How far essence loss lowers the minimum of MAG / RES / DEP.

    By the book the minimum falls with the maximum; under
    `<esslossreducesmaximumonly>` only by what the maximum falling would eat
    into it. Never below zero (Chummer's `RawMinimum`).
    """
    drop = max(0, penalty + floor - cap) if maximum_only else penalty
    return min(drop, floor)


def _after_loss(bought: int, floor: int, cap: int, penalty: int, maximum_only: bool) -> int:
    """MAG / RES / DEP once essence loss has taken `penalty` off it.

    Chummer lowers the minimum (`_min_drop`) and the maximum, and stacks
    the points and karma bought on the lowered minimum: a loss deeper than
    the minimum takes the minimum to zero and leaves what was bought above
    it standing, up to the lowered maximum.
    """
    return max(0, min(bought - _min_drop(floor, cap, penalty, maximum_only), cap - penalty))


def _special_penalty(ess_start: float, loss: float) -> int:
    """The points essence loss takes off MAG, RES or DEP."""
    if not current_rules().dont_round_essence_internally:
        # Chummer rounds the essence left (away from zero) to two places
        # before taking MAG / RES off it, so 4.995 left is 5 and costs one
        # point, not two.
        left = Decimal(str(ess_start - loss)).quantize(Decimal("0.01"), ROUND_HALF_UP)
        loss = ess_start - float(left)
    return int(math.ceil(loss - 1e-9)) if loss > 0 else 0


def essence(ctx: Ctx) -> None:
    ess_start = float(ctx.attrs_spec.get("ESS", {}).get("max") or 6) + float(ctx.effects.get("essence_max_mod") or 0)
    ctx.ess_lost_cyber, ctx.ess_lost_bio = apply_ware_essence_multipliers(
        ctx.cyber_installed, ctx.bio_installed, ctx.effects
    )
    ctx.ess_lost = round(ctx.ess_lost_cyber + ctx.ess_lost_bio, 4)
    if ctx.effects.get("disable_bioware") and ctx.bio_installed:
        ctx.err("engine.ware.bioDisabled")
    ess_penalty = float(ctx.effects.get("essence_penalty") or 0)
    ess_penalty_mag_exempt = float(ctx.effects.get("essence_penalty_mag_exempt") or 0)
    rules = current_rules()
    # Six places only strips float noise; two is the sheet's rounding.
    ctx.ess = max(0.0, round(ess_start - ctx.ess_lost - ess_penalty, 6 if rules.dont_round_essence_internally else 2))
    mag_penalty = _special_penalty(ess_start, ctx.ess_lost + max(0.0, ess_penalty - ess_penalty_mag_exempt))
    # An A.I.'s Depth falls with essence as Magic and Resonance do (Chummer's
    # `GetAllAttributeSpecificEssence`): the whole loss, since the MAG-only
    # allowance is MAG's and nothing in the data grants a DEP-only one.
    dep_penalty = _special_penalty(ess_start, ctx.ess_lost + ess_penalty)
    cyberadept_res_reduction = 0
    if ctx.effects.get("cyberadept_daemon") and ctx.talent["name"] in RES_TALENTS:
        cyberadept_res_reduction = _cyberadept_res_penalty_reduction(
            max(0, int(ctx.state.submersion_grade or 0)),
            ctx.ess_lost_cyber,
            ctx.ess_lost_bio,
        )

    initiate_grade = max(0, int(ctx.state.initiate_grade or 0)) if ctx.talent["name"] in MAG_TALENTS else 0
    submersion_grade = max(0, int(ctx.state.submersion_grade or 0)) if ctx.talent["name"] in RES_TALENTS else 0
    if is_ai(ctx.attrs_spec, ctx.special_floors):
        # An A.I.'s Edge is capped by its Depth: Chummer swaps the metatype
        # maximum for DEP's total value, and the maximum improvements
        # (Lucky) still count on top of it.
        dep_spec = ctx.attrs_spec["DEP"]
        dep_cap = int(dep_spec["max"]) + int(ctx.attr_max_bonus.get("DEP") or 0)
        dep = max(ctx.special_floors["DEP"], min(dep_cap, int(ctx.state.attributes.get("DEP", 0))))
        dep = _after_loss(dep, ctx.special_floors["DEP"], dep_cap, dep_penalty, rules.ess_loss_reduces_maximum_only)
        dep_total = dep + int(ctx.effects["attribute_bonus"].get("DEP") or 0)
        edg_max = int(ctx.attrs_spec["EDG"]["max"])
        ctx.attr_max_bonus["EDG"] = int(ctx.attr_max_bonus.get("EDG") or 0) + dep_total - edg_max
    ctx.ratings = {}
    ctx.bought_ratings = {}
    ctx.special_min_drop = {}
    for key, spec in ctx.attrs_spec.items():
        racial_min = int(spec["min"])
        racial_max = int(spec["max"]) + int(ctx.attr_max_bonus.get(key) or 0)
        raw = int(ctx.state.attributes.get(key, racial_min))
        if key == "MAG":
            if key in ctx.special_floors:
                floor = ctx.special_floors[key]
                mag_cap = racial_max + initiate_grade
                raw = max(floor, min(mag_cap, raw))
                ctx.bought_ratings[key] = raw
                ctx.special_min_drop[key] = _min_drop(floor, mag_cap, mag_penalty, rules.ess_loss_reduces_maximum_only)
                raw = _after_loss(raw, floor, mag_cap, mag_penalty, rules.ess_loss_reduces_maximum_only)
            else:
                raw = 0
        elif key == "RES":
            if key in ctx.special_floors:
                floor = ctx.special_floors[key]
                res_cap = racial_max + submersion_grade
                raw = max(floor, min(res_cap, raw))
                ctx.bought_ratings[key] = raw
                res_penalty = max(0, mag_penalty - cyberadept_res_reduction)
                ctx.special_min_drop[key] = _min_drop(floor, res_cap, res_penalty, rules.ess_loss_reduces_maximum_only)
                raw = _after_loss(raw, floor, res_cap, res_penalty, rules.ess_loss_reduces_maximum_only)
            else:
                raw = 0
        elif key == "DEP":
            if key in ctx.special_floors:
                floor = ctx.special_floors[key]
                raw = max(floor, min(racial_max, raw))
                ctx.bought_ratings[key] = raw
                ctx.special_min_drop[key] = _min_drop(
                    floor, racial_max, dep_penalty, rules.ess_loss_reduces_maximum_only
                )
                raw = _after_loss(raw, floor, racial_max, dep_penalty, rules.ess_loss_reduces_maximum_only)
            else:
                raw = 0
        elif key == "ESS":
            raw = int(ctx.ess)
        else:
            raw = max(racial_min, min(racial_max, raw))
        ctx.ratings[key] = raw
        ctx.bought_ratings.setdefault(key, raw)
