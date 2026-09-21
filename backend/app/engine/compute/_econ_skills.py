"""Phase 13 — skill, group, knowledge and specialization spend."""

from __future__ import annotations

import math

from ...notices import notice, term, terms
from ...rules import current_rules
from ..formulas import eval_attribute_expression
from ..karma import (
    _point_cost,
    _skill_category_map,
    knowledge_points_spent,
)
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
    resolve_talent_skills,
)
from .context import Ctx


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
    free_groups, free_skills = _talent_skill_floors(ctx)
    for group, rating in ctx.state.skill_groups.items():
        rating = max(0, min(ctx.skill_group_cap, int(rating)))
        ctx.state.skill_groups[group] = rating
        free = free_groups.get(group, 0)
        group_levels = max(0, min(int(wanted_group_karma.get(group) or 0), rating - free))
        if group_levels:
            ctx.skill_group_karma_levels[group] = group_levels
        ctx.group_spent += max(0, rating - group_levels - free)
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
        base = max(ctx.skill_totals.get(name, 0), free_skills.get(name, 0))
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
    if current_rules().free_martial_art_specialization:
        free_expertise_skills = set(free_expertise_skills) | _martial_art_free_specs(ctx)
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
            # the talent's free levels are the skill's own (`FreeBase`)
            karma_specs_active = {
                name
                for name in paid_active
                if not active_points.get(name) and not free_skills.get(name) and ctx.skill_karma_levels.get(name)
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


def _talent_skill_floors(ctx: Ctx) -> tuple[dict[str, int], dict[str, int]]:
    """The priority talent's free ratings, as ``(groups, skills)``.

    Each pick is raised to the free rating in ``skill_groups`` / ``skills``
    (those hold the total rating), and the free levels are then left out of
    the points the rating costs — Chummer's `FreeBase`, which sits under
    both `<base>` and `<karma>`.
    """
    ctx.talent_skills = resolve_talent_skills(
        list(ctx.state.talent_skills or []), ctx.talent.get("free_skills"), ctx.data["skills"]
    )
    ctx.state.talent_skills = list(ctx.talent_skills["picked"])
    free = ctx.talent_skills["rating"]
    if not free:
        return {}, {}
    floors = dict.fromkeys(ctx.talent_skills["picked"], free)
    target = ctx.state.skill_groups if ctx.talent_skills["group"] else ctx.state.skills
    for name in floors:
        target[name] = max(int(target.get(name) or 0), free)
    return (floors, {}) if ctx.talent_skills["group"] else ({}, floors)


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


def _martial_art_free_specs(ctx: Ctx) -> set[str]:
    """`<freemartialartspecialization>`: a specialization a known style offers
    (`<addskillspecializationoption>`) costs nothing when it is the one taken.
    Nothing is added on its own — the player still picks the specialization."""
    arts = {str(art.get("id")): art for art in ctx.data.get("martial_arts") or []}
    chosen = ctx.state.skill_specializations or {}
    free: set[str] = set()
    for inst in ctx.state.martial_arts or []:
        for node in (arts.get(str(inst.art_id)) or {}).get("bonus") or []:
            if node.get("tag") != "addskillspecializationoption":
                continue
            fields = node.get("fields") or {}
            skill = str(fields.get("skill") or "").strip()
            spec = str(fields.get("spec") or "").strip()
            if skill and spec and str(chosen.get(skill) or "").strip() == spec:
                free.add(skill)
    return free
