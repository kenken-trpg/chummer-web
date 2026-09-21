"""Phases 12 + 13 + 14 + 15 — priority points / nuyen, skills, karma
totals and the social pass (contacts, martial arts, spend breakdowns,
notoriety / public awareness)."""

from __future__ import annotations

import math
from typing import Any, cast

from ...data_loader import PHYSICAL_ATTRS
from ...improvements import apply_bonus_nodes
from ...notices import notice, term, terms
from ...rules import current_rules
from ..contacts import resolve_contacts, sync_quality_contacts
from ..formulas import eval_attribute_expression
from ..gear import apply_unarmed_bonuses
from ..karma import (
    _active_karma_mults,
    _filter_karma_rules,
    _point_cost,
    _skill_category_map,
    attribute_karma_cost,
    attribute_levels_karma_cost,
    knowledge_excess_karma,
    knowledge_points_spent,
    skill_karma_cost,
    skill_levels_karma_cost,
)
from ..martial_arts import resolve_martial_arts, sync_quality_martial_arts
from ..priority import heritage_cost, priority_value
from ..qualities import apply_cost_discounts, counts_toward_quality_limit, surge_metagenic_limit
from ..skills import (
    _attach_skillsoft_knowledge,
    _attach_specializations,
    _copy_exotic_skill_bonuses,
    _merge_skill_ratings,
    apply_select_expertise,
    resolve_exotic_skills,
    resolve_knowledge,
    resolve_skill_mods,
    resolve_skill_picks,
    resolve_skillsofts,
    resolve_specializations,
)
from ._career import (
    _GEAR_ROW_KEYS,
    career_raise_karma,
    nuyen_spend_breakdown,
    restricted_markup,
    snapshot_career_baseline,
)
from ._career_qualities import career_quality_karma
from ._quality_ctx import quality_req_ctx
from .context import Ctx

#: The karma-for-nuyen cap under `<unrestrictednuyen>`: no rule stops it,
#: and spending past the karma the build has is already an error.
UNRESTRICTED_NUYEN_KARMA = 10_000


def economy(ctx: Ctx) -> None:
    """Phases 12 + 13 + 14 + 15.

    Four passes that used to be one 480-line function. They talk to each other
    only through `ctx`, which is what made the split mechanical: the two locals
    that crossed a boundary (`current_rules()` and the skill-category map) are
    both pure projections, recomputed where they are needed rather than
    threaded through.
    """
    _priority_points(ctx)
    _skill_spend(ctx)
    _karma_totals(ctx)
    _social_pass(ctx)


def _priority_points(ctx: Ctx) -> None:
    """Phase 12 — what the priority table hands out: attribute and skill
    points, the special points the metatype adds, and the nuyen pool."""
    attr_row = priority_value("Attributes", ctx.state.priorities.Attributes)
    skill_row = priority_value("Skills", ctx.state.priorities.Skills)
    res_row = priority_value("Resources", ctx.state.priorities.Resources)
    ctx.special_from_meta, extra_karma = heritage_cost(
        ctx.state.priorities.Heritage, ctx.state.metatype, ctx.state.metavariant
    )

    floors = {key: int(ctx.attrs_spec[key]["min"]) for key in (*PHYSICAL_ATTRS, "EDG")}
    if ctx.special_key in ("MAG", "RES"):
        floors[ctx.special_key] = ctx.talent_start
    ctx.attr_floors = floors
    ctx.attr_karma_levels = _attribute_karma_levels(ctx, floors)
    ctx.spent_physical = 0
    for key in PHYSICAL_ATTRS:
        ctx.spent_physical += max(0, ctx.bought_ratings[key] - floors[key] - ctx.attr_karma_levels.get(key, 0))
    ctx.spent_special = 0
    for key in ("EDG", "MAG", "RES"):
        if key in floors:
            ctx.spent_special += max(0, ctx.bought_ratings[key] - floors[key] - ctx.attr_karma_levels.get(key, 0))

    ctx.nuyen_karma_max = current_rules().karma_nuyen_max
    if ctx.is_karma:
        ctx.attr_points = 0
        ctx.skill_points = 0
        ctx.group_points = 0
        ctx.special_from_meta = 0
        ctx.nuyen_karma_max = current_rules().karma_nuyen_max
        if current_rules().unrestricted_nuyen:
            ctx.nuyen_karma_max = UNRESTRICTED_NUYEN_KARMA
        ctx.state.karma_nuyen = max(0, min(ctx.nuyen_karma_max, int(ctx.state.karma_nuyen or 0)))
        ctx.nuyen_pool = int(ctx.state.karma_nuyen) * current_rules().karma_to_nuyen
        ctx.metatype_karma_cost = (
            max(0, int(ctx.meta.get("karma") or 0)) * current_rules().metatype_costs_karma_multiplier
        )
        ctx.heritage_karma_cost = 0
    else:
        ctx.attr_points = int(attr_row.get("attribute_points") or 0)
        ctx.skill_points = int(skill_row.get("skill_points") or 0)
        ctx.group_points = int(skill_row.get("skill_group_points") or 0)
        ctx.nuyen_pool = int(res_row.get("nuyen") or 0)
        ctx.metatype_karma_cost = 0
        # Priority chargen: metatypes.xml <karma> is for Karma/Sum-to-Ten, not Priority.
        # Heritage table <karma> is an extra cost for some metavariants / rare races.
        ctx.heritage_karma_cost = extra_karma
        # Leftover chargen karma may buy nuyen (SR5 p.94); Born Rich raises the cap.
        ctx.nuyen_karma_max = max(
            0, current_rules().priority_karma_nuyen_base + int(ctx.effects.get("nuyen_max_bp") or 0)
        )
        if current_rules().unrestricted_nuyen:
            ctx.nuyen_karma_max = UNRESTRICTED_NUYEN_KARMA
        ctx.state.karma_nuyen = max(0, min(ctx.nuyen_karma_max, int(ctx.state.karma_nuyen or 0)))
        ctx.nuyen_pool += int(ctx.state.karma_nuyen) * current_rules().karma_to_nuyen

    ctx.nuyen_pool += int(ctx.state.nuyen_earned or 0)
    ctx.nuyen_pool += int(ctx.state.nuyen_adjust or 0) if ctx.career else 0
    ctx.nuyen_pool += int(ctx.effects.get("nuyen_amt") or 0)
    ctx.nuyen_spent = (
        sum(int(item["nuyen"]) for item in ctx.installed)
        + int(ctx.qi.get("nuyen") or 0)
        + int(ctx.foci.get("nuyen") or 0)
        + int(ctx.spirits.get("nuyen") or 0)
        + int(ctx.gear.get("nuyen") or 0)
    )
    if ctx.career:
        rows = [
            *ctx.installed,
            *(ctx.foci.get("public") or []),
            *(ctx.qi.get("public") or []),
            *(row for key in _GEAR_ROW_KEYS for row in cast("list[dict[str, Any]]", ctx.gear.get(key) or [])),
        ]
        ctx.nuyen_markup = restricted_markup(ctx.state.career_baseline, rows)
        ctx.nuyen_spent += ctx.nuyen_markup
    ctx.nuyen = ctx.nuyen_pool - ctx.nuyen_spent


def _skill_spend(ctx: Ctx) -> None:
    """Phase 13 — skills: ratings, groups, exotic, knowledge, skillsofts and
    specializations, and what all of that costs in points."""
    ctx.skill_spent = 0
    ctx.group_spent = 0
    ctx.skill_totals = {}
    exotic_names = {s["name"] for s in ctx.data["skills"]["skills"] if s.get("exotic")}
    if exotic_names:
        ctx.state.skills = {name: rating for name, rating in ctx.state.skills.items() if name not in exotic_names}
    # Priority / Sum-to-Ten: a group's top levels bought with karma are not
    # group points (Chummer's `<karma>` beside `<base>` on a group).
    wanted_group_karma = {} if ctx.is_karma else dict(ctx.state.skill_group_karma or {})
    for group, rating in ctx.state.skill_groups.items():
        rating = max(0, min(ctx.skill_group_cap, int(rating)))
        ctx.state.skill_groups[group] = rating
        group_levels = max(0, min(int(wanted_group_karma.get(group) or 0), rating))
        if group_levels:
            ctx.skill_group_karma_levels[group] = group_levels
        ctx.group_spent += rating - group_levels
        for s in ctx.data["skills"]["skills"]:
            if s.get("skillgroup") == group and not s.get("exotic"):
                ctx.skill_totals[s["name"]] = max(ctx.skill_totals.get(s["name"], 0), rating)
    ctx.state.skill_group_karma = dict(ctx.skill_group_karma_levels)
    tentative = dict(ctx.skill_totals)
    for name, rating in ctx.state.skills.items():
        tentative[name] = max(tentative.get(name, 0), max(0, min(ctx.skill_rating_cap + 1, int(rating))))
    ctx.skill_picks = resolve_skill_picks(
        ctx.state,
        ctx.data["skills"],
        tentative,
        reflex_optimized=bool(ctx.effects.get("reflex_recorder_optimization")),
        skip_ids=ctx.hosted_ware_ids,
    )
    ctx.warnings.extend(ctx.skill_picks["warnings"])
    skill_cat_map = _skill_category_map(ctx.data["skills"])
    point_mults = dict(ctx.effects.get("skill_category_point_cost_mult") or {})
    # Priority / Sum-to-Ten: the top levels bought with karma are not skill
    # points. A Karma build has no points to split from, so it keeps none.
    wanted_karma = {} if ctx.is_karma else dict(ctx.state.skill_karma or {})
    # Points above the group rating and below the karma-bought levels, per
    # skill. Priced once the specializations are known — see below.
    active_points: dict[str, int] = {}
    for name, rating in ctx.state.skills.items():
        cap = ctx.skill_rating_cap + int(ctx.skill_picks["skill_max_bonus"].get(name, 0))
        rating = max(0, min(cap, int(rating)))
        ctx.state.skills[name] = rating
        base = ctx.skill_totals.get(name, 0)
        levels = max(0, min(int(wanted_karma.get(name) or 0), rating - base))
        if levels:
            ctx.skill_karma_levels[name] = levels
        active_points[name] = max(0, rating - base - levels)
        ctx.skill_totals[name] = max(base, rating)
    ctx.state.skill_karma = dict(ctx.skill_karma_levels)
    if not ctx.career:
        _check_grouped_skills(ctx, active_points)
    ctx.exotic = resolve_exotic_skills(
        ctx.state,
        ctx.data["skills"],
        ctx.skill_picks["skill_max_bonus"],
        rating_cap=ctx.skill_rating_cap,
    )
    ctx.warnings.extend(ctx.exotic["warnings"])
    ctx.skill_spent += int(ctx.exotic["spent"])
    ctx.skill_totals.update(ctx.exotic["totals"])
    ctx.knowledge = resolve_knowledge(
        ctx.state,
        ctx.data["skills"],
        # Chummer's `({INTUnaug} + {LOGUnaug}) * 2`: a cerebral booster makes
        # the character smarter, not better schooled.
        ctx.ratings,
        rating_cap=ctx.knowledge_rating_cap,
        native_limit=1 + int(ctx.effects.get("native_language_limit_bonus") or 0),
    )
    ctx.warnings.extend(ctx.knowledge["warnings"])
    if not ctx.is_karma:
        for row in ctx.knowledge["public"]:
            name = str(row.get("name") or "")
            wanted = int((ctx.state.knowledge_karma or {}).get(name) or 0)
            levels = 0 if row.get("native") else max(0, min(wanted, int(row.get("rating") or 0)))
            if levels:
                ctx.knowledge_karma_levels[name] = levels
    ctx.state.knowledge_karma = dict(ctx.knowledge_karma_levels)
    ctx.know_max = _knowledge_points(ctx) + int(ctx.effects.get("knowledge_skill_points") or 0)
    bought_knowledge = dict(ctx.state.knowledge_skills)
    for name in ctx.state.native_languages:
        bought_knowledge[name] = max(int(bought_knowledge.get(name) or 0), 1)
    ctx.skill_mods = resolve_skill_mods(
        ctx.data["skills"], ctx.effects, bought_knowledge, ctx.state.knowledge_categories
    )
    for name, bonus in ctx.skill_picks["skill_bonus"].items():
        ctx.skill_mods["skill_bonus"][name] = int(ctx.skill_mods["skill_bonus"].get(name, 0)) + int(bonus)
    for name, notes in ctx.skill_picks["skill_bonus_notes"].items():
        existing = ctx.skill_mods["skill_bonus_notes"].setdefault(name, [])
        for note in notes:
            if note not in existing:
                existing.append(note)
    _copy_exotic_skill_bonuses(ctx.skill_mods, ctx.exotic["public"])
    for name in ctx.effects.get("disabled_skills") or []:
        if int(ctx.skill_totals.get(name) or 0) > 0 or int(ctx.state.skills.get(name) or 0) > 0:
            ctx.warn("engine.skills.disabled", name=term(name))
    for group in ctx.effects.get("disabled_skill_groups") or []:
        if int(ctx.state.skill_groups.get(group) or 0) > 0:
            ctx.warn("engine.skills.groupDisabled", name=term(group))
    blocked_defaults = list(ctx.effects.get("blocked_default_categories") or [])
    if blocked_defaults:
        ctx.warn("engine.skills.noDefaulting", categories=terms(blocked_defaults))
    ctx.skillsofts = resolve_skillsofts(
        list(ctx.gear.get("gear") or []),
        ctx.data["skills"],
        ctx.effects,
        ctx.warnings,
        hardwires=ctx.skill_picks["hardwires"],
    )
    _attach_skillsoft_knowledge(ctx.knowledge["public"], ctx.skillsofts["knowledge"], ctx.data["skills"])
    ctx.expertises, free_expertise_skills = apply_select_expertise(
        ctx.state,
        ctx.effects,
        ctx.qualities,
        ctx.skill_totals,
        ctx.skillsofts["active"],
        ctx.warnings,
    )
    ctx.specs = resolve_specializations(
        ctx.state,
        ctx.data["skills"],
        ctx.skill_totals,
        ctx.skillsofts["active"],
        ctx.skillsofts["knowledge"],
        free_expertise_skills=free_expertise_skills,
    )
    ctx.warnings.extend(ctx.specs["warnings"])
    # Keep expertise picks even if resolve dropped a conflicting row.
    for row in ctx.expertises:
        skill_name = str(row.get("skill") or "")
        spec_name = str(row.get("spec") or "")
        if skill_name and spec_name:
            ctx.specs["specs"][skill_name] = spec_name
            ctx.state.skill_specializations[skill_name] = spec_name
    spec_active = int(ctx.specs["active_spent"])
    spec_knowledge = int(ctx.specs["knowledge_spent"])
    # Points, priced the way Chummer's `CurrentSpCost` does: a skill's points
    # and its specialization together, through the category multiplier, rounded
    # up once. A Karma build buys its specializations with karma (above), so
    # only the ratings count there.
    paid_active = set() if ctx.is_karma or ctx.career else set(ctx.specs["active_paid"])
    paid_knowledge = set() if ctx.is_karma or ctx.career else set(ctx.specs["knowledge_paid"])
    # Chummer's `Skill.ForcedBuyWithKarma`: a skill with karma levels and no
    # points of its own takes its specialization for karma too, unless the
    # settings allow a point for it. A group's rating is not the skill's own
    # points, so a grouped skill raised only with karma counts as well.
    karma_specs_active: set[str] = set()
    karma_specs_knowledge: set[str] = set()
    if paid_active or paid_knowledge:
        if not current_rules().allow_point_buy_specializations_on_karma_skills:
            karma_specs_active = {
                name for name in paid_active if not active_points.get(name) and ctx.skill_karma_levels.get(name)
            }
            know_points = {
                str(row.get("name") or ""): int(row.get("rating") or 0)
                - int(ctx.knowledge_karma_levels.get(str(row.get("name") or ""), 0))
                for row in ctx.knowledge["public"]
                if not row.get("native")
            }
            karma_specs_knowledge = {
                name
                for name in paid_knowledge
                if know_points.get(name, 0) <= 0 and ctx.knowledge_karma_levels.get(name)
            }
    paid_active -= karma_specs_active
    paid_knowledge -= karma_specs_knowledge
    for name in set(active_points) | paid_active:
        units = int(active_points.get(name, 0)) + (1 if name in paid_active else 0)
        cat = skill_cat_map.get(name, "")
        ctx.skill_spent += _point_cost(units, int(point_mults.get(cat, 100)))
    ctx.know_spent = knowledge_points_spent(
        ctx.knowledge["public"], point_mults, ctx.knowledge_karma_levels, paid_knowledge
    )
    if ctx.is_karma:
        rules = current_rules()
        ctx.spec_karma = (
            spec_active * rules.karma_specialization + spec_knowledge * rules.karma_knowledge_specialization
        )
    elif ctx.career:
        # Priority career: new specs cost karma (baseline settles chargen specs).
        ctx.spec_karma = 0
    else:
        rules = current_rules()
        ctx.spec_karma = (
            len(karma_specs_active) * rules.karma_specialization
            + len(karma_specs_knowledge) * rules.karma_knowledge_specialization
        )
        # Chummer's `SkillPointsSpentOnKnoskills`: on a priority sheet the
        # knowledge a character has no knowledge points left for is paid with
        # active skill points ("even if it is stupid"), not refused.
        overflow = max(0, ctx.know_spent - ctx.know_max)
        if overflow:
            ctx.skill_spent += overflow
            ctx.know_spent = ctx.know_max
            ctx.warn("engine.skills.knowledgeOnSkillPoints", points=overflow)
    _attach_specializations(ctx.knowledge["public"], ctx.specs["specs"])
    ctx.effective_skills = _merge_skill_ratings(ctx.skill_totals, ctx.skillsofts["active"])
    ctx.effective_knowledge = _merge_skill_ratings(dict(ctx.state.knowledge_skills or {}), ctx.skillsofts["knowledge"])


def _knowledge_points(ctx: Ctx) -> int:
    """Free knowledge points off `<knowledgepointsexpression>`, rounded up
    (Chummer's `KnowledgeSkillPoints`). `{INTUnaug}` is the bought rating, so
    a cerebral booster makes the character smarter, not better schooled;
    `{INT}` counts it."""
    values: dict[str, float] = {}
    for key, rating in ctx.ratings.items():
        values[f"{key}Unaug"] = int(rating)
        values[key] = int(rating) + ctx.attr_bonus(key)
    points = eval_attribute_expression(current_rules().knowledge_points_expression, values)
    if points is None:
        return int(ctx.knowledge["max"])
    return max(0, math.ceil(points - 1e-9))


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
        )
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
            ctx.bought_ratings, ctx.attr_karma_levels, rules=ctx.effects.get("attribute_karma_cost")
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
            )
            ctx.karma_spent += ctx.career_adv_karma


def _social_pass(ctx: Ctx) -> None:
    """Phase 15 — contacts and martial arts (both karma, so after the ledger
    opens), the spend breakdowns, and notoriety / street cred / public
    awareness."""
    # Chummer's `{CHAUnaug}`: free contact points come off natural Charisma,
    # so a tailored-pheromones bonus does not buy a bigger network.
    cha = ctx.ratings["CHA"]
    ctx.warnings.extend(sync_quality_contacts(ctx.state, ctx.effects, ctx.qualities))
    ctx.contacts = resolve_contacts(
        ctx.state,
        int(cha or 0),
        career=ctx.career,
        friends_in_high_places=bool(ctx.effects.get("friends_in_high_places")),
        black_market_contact_id=ctx.bmp_contact_id if ctx.bmp_active else "",
        contact_karma_adj=int(ctx.effects.get("contact_karma_adj") or 0),
        contact_karma_min=int(ctx.effects.get("contact_karma_min") or 0),
        excon=bool(ctx.effects.get("excon")),
    )
    ctx.warnings.extend(ctx.contacts["warnings"])
    ctx.karma_spent += int(ctx.contacts.get("karma") or 0)

    martial_ctx = quality_req_ctx(ctx)
    martial_ctx = {
        **martial_ctx,
        "qualities": set(martial_ctx.get("qualities") or []) | {ctx.talent["name"]},
    }
    ctx.warnings.extend(sync_quality_martial_arts(ctx.state, ctx.effects, ctx.qualities))
    ctx.martial = resolve_martial_arts(ctx.state, martial_ctx, ctx.errors, career=ctx.career)
    ctx.warnings.extend(ctx.martial["warnings"])
    for source, nodes in ctx.martial.get("bonus_sources") or []:
        apply_bonus_nodes(nodes, ctx.effects, source)
    apply_unarmed_bonuses(
        ctx.gear.get("weapons"),
        int(ctx.effects.get("unarmed_reach") or 0),
        int(ctx.effects.get("unarmed_ap") or 0),
    )
    ctx.karma_spent += int(ctx.martial.get("karma") or 0)
    ctx.karma_spent += int(ctx.initiation.get("karma") or 0)
    ctx.karma_spent += int(ctx.submersion.get("karma") or 0)
    baseline_qualities = ctx.state.career_baseline.quality_ids if ctx.state.career_baseline else None
    if ctx.career and baseline_qualities is not None:
        ctx.quality_career_pricing = True
        ctx.quality_career_karma, ctx.quality_career_costs, ctx.qualities_removed = career_quality_karma(
            ctx.qualities, ctx.free_quality_ids, baseline_qualities
        )
        ctx.karma_spent += ctx.quality_career_karma
    if ctx.career:
        ctx.karma_pool += int(ctx.state.karma_adjust or 0)
    ctx.karma_left = ctx.karma_pool - ctx.karma_spent

    ctx.karma_spend_lines = list(ctx.career_adv_lines)
    for key, amount in (
        ("engine.spend.qualities", ctx.karma_from_q),
        ("engine.spend.qualitiesCareer", ctx.quality_career_karma),
        ("engine.spend.metatype", ctx.metatype_karma_cost if ctx.is_karma else ctx.heritage_karma_cost),
        ("engine.spend.attributesKarma", ctx.attr_karma),
        ("engine.spend.skillsKarma", ctx.skill_buy_karma),
        ("engine.spend.knowledgeKarma", ctx.knowledge_karma),
        ("engine.spend.specializations", ctx.spec_karma),
        ("engine.spend.nuyenExchange", int(ctx.state.karma_nuyen or 0)),
        ("engine.spend.mysticPP", ctx.mystic_karma),
        ("engine.spend.adeptPower", ctx.extra_adept_karma),
        ("engine.spend.spells", ctx.spell_karma),
        ("engine.spend.spiritServices", ctx.spirit_karma),
        ("engine.spend.contactsOver", int(ctx.contacts.get("karma") or 0)),
        ("engine.spend.martialArts", int(ctx.martial.get("karma") or 0)),
        ("engine.spend.initiation", int(ctx.initiation.get("karma") or 0)),
        ("engine.spend.submersion", int(ctx.submersion.get("karma") or 0)),
    ):
        if amount:
            ctx.karma_spend_lines.append({"kind": "other", "notice": notice(key), "amount": int(amount)})
    ctx.nuyen_spend_lines = nuyen_spend_breakdown(
        ctx.cyber_installed,
        ctx.bio_installed,
        ctx.gear,
        qi_nuyen=int(ctx.qi.get("nuyen") or 0),
        foci_nuyen=int(ctx.foci.get("nuyen") or 0),
        spirits_nuyen=int(ctx.spirits.get("nuyen") or 0),
        markup_nuyen=ctx.nuyen_markup,
    )

    ctx.quality_notoriety = int(ctx.effects.get("notoriety") or 0)
    # Chummer `CalculatedNotoriety`: burned Street Cred, two for one
    ctx.notoriety_total = (
        ctx.quality_notoriety + int(ctx.state.notoriety_bonus or 0) - int(ctx.state.burnt_street_cred or 0) // 2
    )
    # SR5 p.372: a point of Street Cred per 10 karma earned in play, on top of
    # what the table hands out (`street_cred`, Chummer's own manual field).
    # Consummate Professional (AP p.17) raises the 10.
    ctx.street_cred_divisor = max(1, 10 + int(ctx.effects.get("street_cred_divisor") or 0))
    ctx.street_cred_earned = int(ctx.state.karma_earned or 0) // ctx.street_cred_divisor if ctx.career else 0
    ctx.street_cred_total = max(
        0, ctx.street_cred_earned + int(ctx.state.street_cred or 0) - int(ctx.state.burnt_street_cred or 0)
    )
    # Chummer `TotalPublicAwareness`: what the GM awarded, what qualities
    # give, and — only under `<usecalculatedpublicawareness>`, off in every
    # preset it ships — a point per three of Street Cred and Notoriety.
    quality_pa = int(ctx.effects.get("public_awareness") or 0)
    earned_pa = (
        (ctx.street_cred_total + max(0, ctx.notoriety_total)) // 3
        if current_rules().use_calculated_public_awareness
        else 0
    )
    ctx.public_awareness_total = max(0, int(ctx.state.public_awareness or 0) + quality_pa + earned_pa)
    if ctx.effects.get("erased") and ctx.public_awareness_total >= 1:
        ctx.public_awareness_total = 1


def _attribute_karma_levels(ctx: Ctx, floors: dict[str, int]) -> dict[str, int]:
    """`state.attribute_karma`, clamped to what each rating has above its floor.

    A Karma build has no points to split from, so it keeps none. The cleaned
    map is written back, so a lowered rating cannot leave karma levels behind
    that it no longer has.
    """
    levels: dict[str, int] = {}
    if not ctx.is_karma:
        for key, count in (ctx.state.attribute_karma or {}).items():
            if key not in floors:
                continue
            kept = max(0, min(int(count or 0), int(ctx.bought_ratings.get(key) or 0) - floors[key]))
            if kept:
                levels[key] = kept
    ctx.state.attribute_karma = dict(levels)
    return levels


def _check_grouped_skills(ctx: Ctx, active_points: dict[str, int]) -> None:
    """Chargen limits on a skill of a group that has a rating (Chummer's
    `Skill.BaseUnlocked` / `KarmaUnlocked`).

    `<breakskillgroupsincreatemode>` (Chummer's `StrictSkillGroupsInCreateMode`)
    forbids the skill any level of its own. Otherwise, while the group holds
    group points, the skill may not take skill points unless
    `<usepointsonbrokengroups>` allows it; karma levels are always fine.
    """
    rules = current_rules()
    member_of = {
        str(s["name"]): str(s.get("skillgroup") or "")
        for s in ctx.data["skills"]["skills"]
        if s.get("skillgroup") and not s.get("exotic")
    }
    for name in ctx.state.skills:
        group = member_of.get(name)
        if not group:
            continue
        rating = int(ctx.state.skill_groups.get(group) or 0)
        if rating <= 0:
            continue
        own = active_points.get(name, 0) + int(ctx.skill_karma_levels.get(name) or 0)
        if rules.strict_skill_groups_in_create_mode:
            if own:
                ctx.errors.append(notice("engine.skills.groupedSkillLocked", name=term(name), group=term(group)))
            continue
        if ctx.is_karma or rules.use_points_on_broken_groups:
            continue
        group_points = rating - int(ctx.skill_group_karma_levels.get(group) or 0)
        if group_points > 0 and active_points.get(name):
            ctx.errors.append(notice("engine.skills.pointsOnGroupedSkill", name=term(name), group=term(group)))


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
