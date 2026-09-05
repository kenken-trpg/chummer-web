"""Phases 12 + 13 + 14 + 15 — priority points / nuyen, skills, karma
totals and the social pass (contacts, martial arts, spend breakdowns,
notoriety / public awareness)."""

from __future__ import annotations

from ...data_loader import PHYSICAL_ATTRS
from ...improvements import apply_bonus_nodes
from ..constants import (
    KARMA_CHARGEN_POOL,
    KARMA_NUYEN_MAX,
    KARMA_SPECIALIZATION,
    KARMA_TO_NUYEN,
    MYSTIC_PP_KARMA,
    PRIORITY_KARMA_NUYEN_BASE,
)
from ..contacts import resolve_contacts, sync_quality_contacts
from ..gear import apply_unarmed_bonuses
from ..karma import (
    _active_karma_mults,
    _point_cost,
    _skill_category_map,
    attribute_karma_cost,
    knowledge_excess_karma,
    knowledge_points_spent,
    skill_karma_cost,
)
from ..martial_arts import resolve_martial_arts, sync_quality_martial_arts
from ..priority import priority_value
from ..qualities import quality_requirement_context
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
from ._career import career_raise_karma, nuyen_spend_breakdown, snapshot_career_baseline
from .context import Ctx


def economy(ctx: Ctx) -> None:
    attr_row = priority_value("Attributes", ctx.state.priorities.Attributes)
    skill_row = priority_value("Skills", ctx.state.priorities.Skills)
    res_row = priority_value("Resources", ctx.state.priorities.Resources)
    her_row = priority_value("Heritage", ctx.state.priorities.Heritage)

    ctx.special_from_meta = 0
    extra_karma = 0
    for entry in her_row.get("metatypes") or []:
        if entry["name"] == ctx.state.metatype:
            ctx.special_from_meta = entry.get("special", 0)
            extra_karma += entry.get("karma", 0)
            if ctx.state.metavariant:
                for v in entry.get("variants") or []:
                    if v["name"] == ctx.state.metavariant:
                        ctx.special_from_meta = v.get("special", ctx.special_from_meta)
                        extra_karma += v.get("karma", 0)
            break

    ctx.spent_physical = 0
    for key in PHYSICAL_ATTRS:
        ctx.spent_physical += max(0, ctx.ratings[key] - int(ctx.attrs_spec[key]["min"]))
    ctx.spent_special = max(0, ctx.ratings["EDG"] - int(ctx.attrs_spec["EDG"]["min"]))
    if ctx.special_key == "MAG":
        ctx.spent_special += max(0, ctx.ratings["MAG"] - ctx.talent_start)
    elif ctx.special_key == "RES":
        ctx.spent_special += max(0, ctx.ratings["RES"] - ctx.talent_start)

    ctx.nuyen_karma_max = KARMA_NUYEN_MAX
    if ctx.is_karma:
        ctx.attr_points = 0
        ctx.skill_points = 0
        ctx.group_points = 0
        ctx.special_from_meta = 0
        ctx.nuyen_karma_max = KARMA_NUYEN_MAX
        ctx.state.karma_nuyen = max(0, min(ctx.nuyen_karma_max, int(ctx.state.karma_nuyen or 0)))
        ctx.nuyen_pool = int(ctx.state.karma_nuyen) * KARMA_TO_NUYEN
        ctx.metatype_karma_cost = max(0, int(ctx.meta.get("karma") or 0))
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
        ctx.nuyen_karma_max = max(0, PRIORITY_KARMA_NUYEN_BASE + int(ctx.effects.get("nuyen_max_bp") or 0))
        ctx.state.karma_nuyen = max(0, min(ctx.nuyen_karma_max, int(ctx.state.karma_nuyen or 0)))
        ctx.nuyen_pool += int(ctx.state.karma_nuyen) * KARMA_TO_NUYEN

    ctx.nuyen_pool += int(ctx.state.nuyen_earned or 0)
    ctx.nuyen_pool += int(ctx.effects.get("nuyen_amt") or 0)
    ctx.nuyen_spent = (
        sum(int(item["nuyen"]) for item in ctx.installed)
        + int(ctx.qi.get("nuyen") or 0)
        + int(ctx.foci.get("nuyen") or 0)
        + int(ctx.spirits.get("nuyen") or 0)
        + int(ctx.gear.get("nuyen") or 0)
    )
    ctx.nuyen = ctx.nuyen_pool - ctx.nuyen_spent

    ctx.skill_spent = 0
    ctx.group_spent = 0
    ctx.skill_totals = {}
    exotic_names = {s["name"] for s in ctx.data["skills"]["skills"] if s.get("exotic")}
    if exotic_names:
        ctx.state.skills = {name: rating for name, rating in ctx.state.skills.items() if name not in exotic_names}
    for group, rating in ctx.state.skill_groups.items():
        rating = max(0, min(ctx.skill_group_cap, int(rating)))
        ctx.state.skill_groups[group] = rating
        ctx.group_spent += rating
        for s in ctx.data["skills"]["skills"]:
            if s.get("skillgroup") == group and not s.get("exotic"):
                ctx.skill_totals[s["name"]] = max(ctx.skill_totals.get(s["name"], 0), rating)
    tentative = dict(ctx.skill_totals)
    for name, rating in ctx.state.skills.items():
        tentative[name] = max(tentative.get(name, 0), max(0, min(ctx.skill_rating_cap + 1, int(rating))))
    ctx.skill_picks = resolve_skill_picks(ctx.state, ctx.data["skills"], tentative)
    ctx.warnings.extend(ctx.skill_picks["warnings"])
    skill_cat_map = _skill_category_map(ctx.data["skills"])
    point_mults = dict(ctx.effects.get("skill_category_point_cost_mult") or {})
    for name, rating in ctx.state.skills.items():
        cap = ctx.skill_rating_cap + int(ctx.skill_picks["skill_max_bonus"].get(name, 0))
        rating = max(0, min(cap, int(rating)))
        ctx.state.skills[name] = rating
        base = ctx.skill_totals.get(name, 0)
        extra = max(0, rating - base)
        cat = skill_cat_map.get(name, "")
        ctx.skill_spent += _point_cost(extra, int(point_mults.get(cat, 100)))
        ctx.skill_totals[name] = max(base, rating)
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
        ctx.total,
        rating_cap=ctx.skill_rating_cap,
        native_limit=1 + int(ctx.effects.get("native_language_limit_bonus") or 0),
    )
    ctx.warnings.extend(ctx.knowledge["warnings"])
    ctx.know_spent = knowledge_points_spent(ctx.knowledge["public"], point_mults)
    ctx.know_max = int(ctx.knowledge["max"]) + int(ctx.effects.get("knowledge_skill_points") or 0)
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
            ctx.warnings.append(f"{name} は無効化されている技能です")
    for group in ctx.effects.get("disabled_skill_groups") or []:
        if int(ctx.state.skill_groups.get(group) or 0) > 0:
            ctx.warnings.append(f"技能グループ {group} は無効化されています")
    blocked_defaults = list(ctx.effects.get("blocked_default_categories") or [])
    if blocked_defaults:
        ctx.warnings.append("デフォルト不可: " + "、".join(blocked_defaults))
    ctx.skillsofts = resolve_skillsofts(list(ctx.gear.get("gear") or []), ctx.data["skills"], ctx.effects, ctx.warnings)
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
    if ctx.is_karma:
        ctx.spec_karma = (spec_active + spec_knowledge) * KARMA_SPECIALIZATION
    elif ctx.career:
        # Priority career: new specs cost karma (baseline settles chargen specs).
        ctx.spec_karma = 0
    else:
        ctx.skill_spent += spec_active
        ctx.know_spent += spec_knowledge
        ctx.spec_karma = 0
    _attach_specializations(ctx.knowledge["public"], ctx.specs["specs"])
    ctx.effective_skills = _merge_skill_ratings(ctx.skill_totals, ctx.skillsofts["active"])
    ctx.effective_knowledge = _merge_skill_ratings(dict(ctx.state.knowledge_skills or {}), ctx.skillsofts["knowledge"])

    ctx.karma_from_q = sum(
        q["karma"] for q in ctx.qualities if not q.get("onlyprioritygiven") and q["id"] not in ctx.free_quality_ids
    )
    ctx.mystic_karma = int(ctx.state.mystic_pp) * MYSTIC_PP_KARMA
    ctx.extra_adept_karma = (
        int(ctx.enhancements.get("karma") or 0) + int(ctx.qi.get("karma") or 0) + int(ctx.foci.get("karma") or 0)
    )
    ctx.spell_karma = int(ctx.magic.get("karma") or 0) + int(ctx.resonance.get("karma") or 0)
    ctx.career_adv_karma = 0
    ctx.career_adv_lines = []
    if ctx.is_karma:
        ctx.attr_karma = attribute_karma_cost(ctx.ratings, ctx.attrs_spec, ctx.special_key)
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
        ctx.karma_pool = KARMA_CHARGEN_POOL + int(ctx.state.karma_earned or 0)
        ctx.karma_spent = (
            ctx.karma_from_q
            + ctx.metatype_karma_cost
            + ctx.mystic_karma
            + ctx.extra_adept_karma
            + ctx.spell_karma
            + ctx.attr_karma
            + ctx.skill_buy_karma
            + ctx.knowledge_karma
            + ctx.spec_karma
            + nuyen_karma
        )
    else:
        ctx.attr_karma = 0
        ctx.skill_buy_karma = 0
        ctx.knowledge_karma = 0
        nuyen_karma = 0
        ctx.karma_pool = 25 + int(ctx.state.karma_earned or 0)
        ctx.karma_spent = (
            ctx.karma_from_q
            + ctx.heritage_karma_cost
            + ctx.mystic_karma
            + ctx.extra_adept_karma
            + ctx.spell_karma
            + int(ctx.state.karma_nuyen or 0)
        )
        if ctx.career:
            baseline = ctx.state.career_baseline
            if baseline is None:
                baseline = snapshot_career_baseline(ctx.state)
                ctx.state.career_baseline = baseline
            ctx.career_adv_karma, ctx.career_adv_lines = career_raise_karma(
                ctx.state, baseline, ctx.skill_totals, ctx.data["skills"], effects=ctx.effects
            )
            ctx.karma_spent += ctx.career_adv_karma

    cha = ctx.total["CHA"]
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

    martial_ctx = quality_requirement_context(
        ctx.state,
        ctx.talent,
        ctx.qualities,
        ctx.meta,
        ctx.ess,
        ctx.ess_lost,
        ctx.effective_skills,
        set(ctx.adept.get("power_names") or []),
        {str(item.get("name") or "") for item in (ctx.magic.get("public") or []) if item.get("name")},
        str(
            ((ctx.magic.get("tradition") if isinstance(ctx.magic.get("tradition"), dict) else {}) or {}).get("name")
            or ""
        ),
        {item["name"] for item in ctx.cyber_installed},
        {item["name"] for item in ctx.bio_installed},
        ctx.effective_knowledge,
    )
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
    ctx.karma_left = ctx.karma_pool - ctx.karma_spent

    ctx.karma_spend_lines = list(ctx.career_adv_lines)
    for label, amount in (
        ("資質", ctx.karma_from_q),
        ("メタ", ctx.metatype_karma_cost if ctx.is_karma else ctx.heritage_karma_cost),
        ("能力値（カルマ作成）", ctx.attr_karma if ctx.is_karma else 0),
        ("技能（カルマ作成）", ctx.skill_buy_karma if ctx.is_karma else 0),
        ("知識（カルマ作成）", ctx.knowledge_karma if ctx.is_karma else 0),
        ("専門化", ctx.spec_karma),
        ("新円交換", int(ctx.state.karma_nuyen or 0)),
        ("ミスティックPP", ctx.mystic_karma),
        ("アデプト／気／フォーカス", ctx.extra_adept_karma),
        ("術式／複合体", ctx.spell_karma),
        ("コンタクト超過", int(ctx.contacts.get("karma") or 0)),
        ("武道", int(ctx.martial.get("karma") or 0)),
        ("イニシエーション", int(ctx.initiation.get("karma") or 0)),
        ("サブマージョン", int(ctx.submersion.get("karma") or 0)),
    ):
        if amount:
            ctx.karma_spend_lines.append({"kind": "other", "label": label, "amount": int(amount)})
    ctx.nuyen_spend_lines = nuyen_spend_breakdown(
        ctx.cyber_installed,
        ctx.bio_installed,
        ctx.gear,
        qi_nuyen=int(ctx.qi.get("nuyen") or 0),
        foci_nuyen=int(ctx.foci.get("nuyen") or 0),
        spirits_nuyen=int(ctx.spirits.get("nuyen") or 0),
    )

    ctx.quality_notoriety = int(ctx.effects.get("notoriety") or 0)
    ctx.notoriety_total = ctx.quality_notoriety + int(ctx.state.notoriety_bonus or 0)
    ctx.street_cred_total = int(ctx.state.street_cred or 0)
    quality_pa = int(ctx.effects.get("public_awareness") or 0)
    ctx.public_awareness_total = max(0, (ctx.street_cred_total + max(0, ctx.notoriety_total)) // 3 + quality_pa)
    if ctx.effects.get("erased") and ctx.public_awareness_total >= 1:
        ctx.public_awareness_total = 1
