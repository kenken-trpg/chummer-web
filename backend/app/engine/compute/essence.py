"""Phases 5 + 6 — essence penalty and the attribute-ratings loop
(racial min/max, MAG/RES caps, ESS)."""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal

from ...rules import current_rules
from ..constants import MAG_TALENTS, RES_TALENTS
from ..pricing import apply_ware_essence_multipliers
from ..resonance import _cyberadept_res_penalty_reduction
from .context import Ctx


def _after_loss(bought: int, cap: int, penalty: int, maximum_only: bool) -> int:
    """MAG / RES once essence loss has taken `penalty` off it. By the book
    the rating falls with the maximum; under `<esslossreducesmaximumonly>`
    only the maximum falls, and the rating just cannot sit above it."""
    if maximum_only:
        return max(0, min(bought, cap - penalty))
    return max(0, bought - penalty)


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
    mag_relevant_loss = ctx.ess_lost + max(0.0, ess_penalty - ess_penalty_mag_exempt)
    if not rules.dont_round_essence_internally:
        # Chummer rounds the essence left (away from zero) to two places
        # before taking MAG / RES off it, so 4.995 left is 5 and costs one
        # point, not two.
        left = Decimal(str(ess_start - mag_relevant_loss)).quantize(Decimal("0.01"), ROUND_HALF_UP)
        mag_relevant_loss = ess_start - float(left)
    mag_penalty = int(math.ceil(mag_relevant_loss - 1e-9)) if mag_relevant_loss > 0 else 0
    cyberadept_res_reduction = 0
    if ctx.effects.get("cyberadept_daemon") and ctx.talent["name"] in RES_TALENTS:
        cyberadept_res_reduction = _cyberadept_res_penalty_reduction(
            max(0, int(ctx.state.submersion_grade or 0)),
            ctx.ess_lost_cyber,
            ctx.ess_lost_bio,
        )

    initiate_grade = max(0, int(ctx.state.initiate_grade or 0)) if ctx.talent["name"] in MAG_TALENTS else 0
    submersion_grade = max(0, int(ctx.state.submersion_grade or 0)) if ctx.talent["name"] in RES_TALENTS else 0
    ctx.ratings = {}
    ctx.bought_ratings = {}
    for key, spec in ctx.attrs_spec.items():
        racial_min = int(spec["min"])
        racial_max = int(spec["max"]) + int(ctx.attr_max_bonus.get(key) or 0)
        raw = int(ctx.state.attributes.get(key, racial_min))
        if key == "MAG":
            if ctx.special_key == "MAG":
                floor = max(ctx.talent_start, 1)
                mag_cap = racial_max + initiate_grade
                raw = max(floor, min(mag_cap, raw))
                ctx.bought_ratings[key] = raw
                raw = _after_loss(raw, mag_cap, mag_penalty, rules.ess_loss_reduces_maximum_only)
            else:
                raw = 0
        elif key == "RES":
            if ctx.special_key == "RES":
                floor = max(ctx.talent_start, 1)
                res_cap = racial_max + submersion_grade
                raw = max(floor, min(res_cap, raw))
                ctx.bought_ratings[key] = raw
                res_penalty = max(0, mag_penalty - cyberadept_res_reduction)
                raw = _after_loss(raw, res_cap, res_penalty, rules.ess_loss_reduces_maximum_only)
            else:
                raw = 0
        elif key == "ESS":
            raw = int(ctx.ess)
        else:
            raw = max(racial_min, min(racial_max, raw))
        ctx.ratings[key] = raw
        ctx.bought_ratings.setdefault(key, raw)
