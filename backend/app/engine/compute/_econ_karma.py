"""Phase 14 — karma totals."""

from __future__ import annotations

from ...notices import notice
from ...rules import current_rules
from ..karma import (
    _active_karma_mults,
    _filter_karma_rules,
    _skill_category_map,
    attribute_karma_cost,
    attribute_levels_karma_cost,
    group_karma_compensation,
    knowledge_excess_karma,
    skill_karma_cost,
    skill_levels_karma_cost,
)
from ..qualities import apply_cost_discounts, counts_toward_quality_limit, surge_metagenic_limit
from ._career import (
    career_raise_karma,
    snapshot_career_baseline,
)
from ._quality_ctx import quality_req_ctx
from .context import Ctx


def _karma_totals(ctx: Ctx) -> None:
    """Phase 14 — the karma ledger: what the qualities, attributes, skills,
    magic and career advancement each take out of the pool."""
    # a pure projection of the catalog, so cheaper to rebuild than to thread
    skill_cat_map = _skill_category_map(ctx.data["skills"])
    # `<costdiscount>` decides what a quality costs, so before the sum
    ctx.qualities = apply_cost_discounts(ctx.qualities, quality_req_ctx(ctx))
    paid_qualities = [
        q for q in ctx.qualities if not q.get("onlyprioritygiven") and q["id"] not in ctx.free_quality_ids
    ]
    ctx.karma_from_q = sum(q["karma"] for q in paid_qualities)
    rules = current_rules()
    if rules.quality_exceed_negative_no_bonus:
        # Chummer's `NegativeQualityKarma`: past the limit, a negative
        # quality is still taken but its karma is not handed out.
        surge = surge_metagenic_limit(ctx.qualities) > 0
        negative = sum(
            -int(q["karma"]) for q in paid_qualities if int(q["karma"]) < 0 and counts_toward_quality_limit(q, surge)
        )
        excess = max(0, negative - rules.quality_karma_cap_negative)
        if excess:
            ctx.karma_from_q += excess
            ctx.warn("engine.qualities.negativeNoBonus", karma=excess, limit=rules.quality_karma_cap_negative)
    ctx.mystic_karma = int(ctx.state.mystic_pp) * current_rules().karma_mystic_pp
    _check_career_mystic_pp(ctx)
    ctx.extra_adept_karma = (
        int(ctx.enhancements.get("karma") or 0) + int(ctx.qi.get("karma") or 0) + int(ctx.foci.get("karma") or 0)
    )
    ctx.spell_karma = int(ctx.magic.get("karma") or 0) + int(ctx.resonance.get("karma") or 0)
    ctx.spirit_karma = _spirit_karma(ctx)
    ctx.career_adv_karma = 0
    ctx.career_adv_lines = []
    if ctx.is_karma:
        ctx.attr_karma = attribute_karma_cost(
            ctx.bought_ratings, ctx.attrs_spec, ctx.special_key, rules=ctx.effects.get("attribute_karma_cost")
        )
        ctx.skill_buy_karma = skill_karma_cost(
            ctx.state.skill_groups, ctx.skill_totals, ctx.data["skills"], group_cap=ctx.skill_group_cap
        ) + group_karma_compensation(ctx.state.skill_groups, ctx.skill_totals, {}, ctx.data["skills"])
        know_cats = {
            str(row.get("name") or ""): str(row.get("category") or "")
            for row in (ctx.knowledge.get("public") or [])
            if row.get("name")
        }
        ctx.knowledge_karma = knowledge_excess_karma(
            dict(ctx.state.knowledge_skills or {}),
            ctx.know_max,
            categories=know_cats,
            karma_mults=_active_karma_mults(ctx.effects.get("skill_category_karma_cost_mult"), career=False),
        )
        nuyen_karma = int(ctx.state.karma_nuyen or 0)
        ctx.karma_pool = current_rules().karma_chargen_pool + int(ctx.state.karma_earned or 0)
        ctx.karma_spent = (
            ctx.karma_from_q
            + ctx.metatype_karma_cost
            + ctx.mystic_karma
            + ctx.extra_adept_karma
            + ctx.spell_karma
            + ctx.spirit_karma
            + ctx.attr_karma
            + ctx.skill_buy_karma
            + ctx.knowledge_karma
            + ctx.spec_karma
            + nuyen_karma
        )
    else:
        ctx.attr_karma = attribute_levels_karma_cost(
            ctx.bought_ratings,
            ctx.attr_karma_levels,
            rules=ctx.effects.get("attribute_karma_cost"),
            minimums=_attribute_minimums(ctx),
        )
        ctx.skill_buy_karma = skill_levels_karma_cost(
            ctx.skill_totals,
            ctx.skill_karma_levels,
            skill_cat_map,
            per_rating=current_rules().karma_active_skill,
            first_level=current_rules().karma_new_active_skill,
            karma_mults=_active_karma_mults(ctx.effects.get("skill_category_karma_cost_mult"), career=False),
            flat_rules=_filter_karma_rules(ctx.effects.get("active_skill_karma_cost"), career=False),
        )
        know_rows = ctx.knowledge.get("public") or []
        ctx.knowledge_karma = skill_levels_karma_cost(
            {str(row.get("name") or ""): int(row.get("rating") or 0) for row in know_rows},
            ctx.knowledge_karma_levels,
            {str(row.get("name") or ""): str(row.get("category") or "") for row in know_rows},
            per_rating=current_rules().karma_knowledge,
            first_level=current_rules().karma_new_knowledge_skill,
            karma_mults=_active_karma_mults(ctx.effects.get("skill_category_karma_cost_mult"), career=False),
            flat_rules=_filter_karma_rules(
                list(ctx.effects.get("skill_category_karma_cost") or [])
                + list(ctx.effects.get("knowledge_skill_karma_cost") or []),
                career=False,
            ),
            min_rules=_filter_karma_rules(ctx.effects.get("knowledge_skill_karma_cost_min"), career=False),
        )
        ctx.skill_buy_karma += skill_levels_karma_cost(
            ctx.state.skill_groups,
            ctx.skill_group_karma_levels,
            {},
            per_rating=current_rules().karma_skill_group,
        )
        ctx.skill_buy_karma += group_karma_compensation(
            ctx.state.skill_groups,
            ctx.skill_totals,
            {name: int(total) - int(ctx.skill_karma_levels.get(name) or 0) for name, total in ctx.skill_totals.items()},
            ctx.data["skills"],
        )
        ctx.karma_pool = 25 + int(ctx.state.karma_earned or 0)
        ctx.karma_spent = (
            ctx.karma_from_q
            + ctx.heritage_karma_cost
            + ctx.mystic_karma
            + ctx.extra_adept_karma
            + ctx.spell_karma
            + ctx.spirit_karma
            + ctx.attr_karma
            + ctx.skill_buy_karma
            + ctx.knowledge_karma
            + ctx.spec_karma
            + int(ctx.state.karma_nuyen or 0)
        )
        if ctx.career:
            baseline = ctx.state.career_baseline
            if baseline is None:
                # From the ratings this pass settles on, not the raw input: a
                # Chummer save carries MAGADEPT, and a mundane's RES as 0 that
                # a re-read of our own export would bring back differently.
                baseline = snapshot_career_baseline(ctx.state)
                baseline.attributes = {k: int(v) for k, v in ctx.bought_ratings.items() if k != "ESS"}
                ctx.state.career_baseline = baseline
            ctx.career_adv_karma, ctx.career_adv_lines = career_raise_karma(
                ctx.state,
                baseline,
                ctx.skill_totals,
                ctx.data["skills"],
                effects=ctx.effects,
                ratings=ctx.bought_ratings,
                minimums=_attribute_minimums(ctx),
            )
            ctx.karma_spent += ctx.career_adv_karma


def _attribute_minimums(ctx: Ctx) -> dict[str, int]:
    """Each attribute's metatype minimum, for `alternate_attribute_shift`."""
    return {key: int((spec or {}).get("min") or 1) for key, spec in ctx.attrs_spec.items()}


def _check_career_mystic_pp(ctx: Ctx) -> None:
    """A mystic adept buys power points in career only under
    `<mysaddppcareer>` (Chummer's `MysAdeptAllowPPCareer`)."""
    baseline = ctx.state.career_baseline if ctx.career else None
    if baseline is None or baseline.mystic_pp is None or current_rules().mystic_adept_pp_in_career:
        return
    if int(ctx.state.mystic_pp or 0) > baseline.mystic_pp:
        ctx.errors.append(notice("engine.adept.mysticPpInCareer", before=baseline.mystic_pp, after=ctx.state.mystic_pp))


def _spirit_karma(ctx: Ctx) -> int:
    """Chargen karma for the spirits and sprites that start with the
    character: `<karmaspirit>` per service owed (Chummer's `CalculateBP`).

    Binding one in career is reagents and drain, not karma, so a career
    character keeps paying only for what was already there when play began.
    """
    baseline = ctx.state.career_baseline if ctx.career else None
    known = set(baseline.item_ids) if baseline is not None and baseline.item_ids is not None else None
    services = 0
    for row in list(ctx.spirits.get("public") or []) + list(ctx.techno_sprites.get("public") or []):
        if known is not None and str(row.get("id") or "") not in known:
            continue
        services += max(0, int(row.get("services") or 0))
    return services * current_rules().karma_spirit
