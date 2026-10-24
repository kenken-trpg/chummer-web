"""Bridge RF skill events to the existing compute phases and purchase inputs."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from uuid import NAMESPACE_URL, uuid5

from ...models import CharacterState, ExoticSkillInstall
from ...models.life_modules import life_module_entry_ids, life_skill_policy
from ...notices import NoticeError, notice, term
from ...rules import current_rules
from ..constants import RES_TALENTS, SPELL_TALENTS, SPIRIT_TALENTS
from ..karma import _active_karma_mults, _filter_karma_rules, knowledge_excess_karma
from ..life_module_career import replay_advancements, skill_input_signature
from ..life_module_skill_purchases import resolve_life_skill_purchases
from ..life_module_skills import LifeSkillResolution, life_skill_events, life_skill_key, resolve_life_module_skills
from ..priority import normalize_build_method
from ..skills import exotic_skill_label, resolve_skill_picks
from .context import Ctx


def normalize(state: CharacterState) -> None:
    state.build_method = normalize_build_method(state.build_method)
    if state.build_method != "LifeModule":
        return
    if state.life_module_rules_version is None or (state.life_module_rules_version == 1 and not state.career):
        state.life_module_rules_version = 1 if state.career else 2
        if state.life_module_rules_version == 2:
            state.life_module_entry_ids = life_module_entry_ids(state.id, state.life_modules)
    if state.life_module_rules_version == 2:
        state.life_module_entry_ids = life_module_entry_ids(state.id, state.life_modules, state.life_module_entry_ids)
        for cap in (state.settings.chargen_skill_max, state.settings.chargen_knowledge_skill_max):
            if cap is not None and not 1 <= cap <= 1000:
                raise NoticeError(notice("engine.life.policyInvalid"))


def prepare(ctx: Ctx) -> None:
    if not ctx.life or ctx.state.life_module_rules_version != 2:
        if ctx.life and ctx.career:
            ctx.warn("engine.life.legacyCareer")
        return
    if ctx.career:
        _prepare_career(ctx)
        return
    events, errors = life_skill_events(ctx.life["rows"], ctx.state.life_module_entry_ids, ctx.state.life_module_choices)
    policy = life_skill_policy(
        active_cap=ctx.state.settings.chargen_skill_max,
        knowledge_cap=ctx.state.settings.chargen_knowledge_skill_max,
    )
    unavailable = _unavailable(ctx)
    resolved = resolve_life_module_skills(
        events,
        ctx.data["skills"],
        ctx.state.life_module_transfers,
        policy=policy,
        unavailable_skill_ids=frozenset(unavailable),
        known_knowledge_categories=ctx.life["original"]["knowledge_categories"],
        known_native_languages=frozenset(ctx.life["original"]["native_languages"]),
    )
    ctx.errors.extend(errors)
    ctx.errors.extend(resolved.errors)
    ctx.warnings.extend(resolved.warnings)
    ctx.life["skill_resolution"] = resolved
    public = resolved.public()
    public["module_karma"] = ctx.life["karma"]
    public["skill_catalog"] = ctx.data["skills"]
    public["unavailable_skill_ids"] = sorted(unavailable)
    public["complete"] = resolved.complete and not errors
    ctx.life["skill_public"] = public
    apply_free(ctx, resolved)


def apply_free(ctx: Ctx, resolved: LifeSkillResolution) -> None:
    """Apply free levels only to the working copy, never to saved purchases."""
    original = ctx.life["original"]
    by_id = {s["id"]: s for s in ctx.data["skills"]["skills"]}
    # Group inputs are paid levels. Materialize only legal, uniform groups;
    # the price phase keeps invalid inputs and emits their detailed notices.
    initial = resolve_life_skill_purchases(resolved, ctx.data["skills"], {}, original["skill_groups"])
    ctx.state.skill_groups = dict(initial.group_totals)
    valid_groups = {g: n for g, n in original["skill_groups"].items() if g in initial.group_totals}
    ctx.state.skills = {}
    for skill in ctx.data["skills"]["skills"]:
        if skill.get("exotic"):
            continue
        free = resolved.free_active.get(life_skill_key(skill["id"]), 0)
        bought = max(int(original["skills"].get(skill["name"], 0)), int(valid_groups.get(skill.get("skillgroup"), 0)))
        if free or bought:
            ctx.state.skills[skill["name"]] = free + bought
    # Keep unknown purchases visible to the validator instead of dropping them.
    known = {s["name"] for s in by_id.values()}
    ctx.state.skills.update({name: n for name, n in original["skills"].items() if name not in known})
    ctx.state.knowledge_skills = {
        name: int(original["knowledge_skills"].get(name, 0)) + resolved.free_knowledge.get(name, 0)
        for name in set(original["knowledge_skills"]) | set(resolved.free_knowledge)
    }
    ctx.state.knowledge_categories.update(resolved.knowledge_categories)
    ctx.state.native_languages = list(dict.fromkeys([*ctx.state.native_languages, *resolved.native_languages]))
    existing: set[str] = set()
    for row in ctx.state.exotic_skills:
        skill = next((s for s in by_id.values() if s["name"] == row.skill_name), None)
        if skill:
            key = life_skill_key(skill["id"], row.extra)
            existing.add(key)
            row.rating += resolved.free_active.get(key, 0)
    for key, rating in resolved.free_active.items():
        if not key.startswith("exotic:") or key in existing:
            continue
        _, sid, specific = key.split(":", 2)
        skill = by_id.get(sid)
        if skill:
            ctx.state.exotic_skills.append(
                ExoticSkillInstall(
                    id=str(uuid5(NAMESPACE_URL, f"life-free:{ctx.state.id}:{key}")),
                    skill_name=skill["name"],
                    extra=specific,
                    rating=rating,
                )
            )


def price(ctx: Ctx) -> None:
    resolved: LifeSkillResolution = ctx.life["skill_resolution"]
    original = ctx.life["original"]
    if ctx.career and ctx.state.life_module_skill_snapshot is not None:
        snapshot = ctx.state.life_module_skill_snapshot
        growth = ctx.life["career_skills"]
        knowledge_growth = sum(line["karma"] for line in growth.lines if line["kind"] == "knowledge")
        ctx.skill_buy_karma = snapshot.skill_karma + growth.karma - knowledge_growth
        ctx.knowledge_karma = snapshot.knowledge_karma + knowledge_growth
        ctx.career_adv_karma = growth.karma
        ctx.career_adv_lines = [
            {
                "kind": "skills",
                "notice": {"key": "engine.life.skillGrowthLine", "params": {"levels": line["levels"]}},
                "amount": line["karma"],
            }
            for line in growth.lines
        ]
        _growth_rules(ctx)
        return
    by_name = {s["name"]: s for s in ctx.data["skills"]["skills"]}
    bought: dict[str, int] = {}
    bonuses: dict[str, int] = {}
    for name, rating in original["skills"].items():
        if name in by_name and not by_name[name].get("exotic"):
            bought[life_skill_key(by_name[name]["id"])] = rating
        elif rating:
            ctx.err("engine.life.purchaseInvalid", name=term(name))
    for row in original["exotic_skills"]:
        if row.skill_name in by_name and row.extra.strip():
            key = life_skill_key(by_name[row.skill_name]["id"], row.extra)
            if key in bought:
                ctx.err("engine.life.purchaseInvalid", name=term(row.skill_name))
                continue
            bought[key] = row.rating
    for skill in by_name.values():
        name = skill["name"]
        bonuses[life_skill_key(skill["id"])] = ctx.skill_picks["skill_max_bonus"].get(name, 0)
    for row in ctx.state.exotic_skills:
        skill = by_name.get(row.skill_name)
        if skill:
            bonuses[life_skill_key(skill["id"], row.extra)] = ctx.skill_picks["skill_max_bonus"].get(
                row.skill_name, 0
            ) + ctx.skill_picks["skill_max_bonus"].get(exotic_skill_label(row.skill_name, row.extra), 0)
    purchases = resolve_life_skill_purchases(
        resolved,
        ctx.data["skills"],
        bought,
        original["skill_groups"],
        skill_max_bonuses=bonuses,
        active_karma_mults=_active_karma_mults(ctx.effects.get("skill_category_karma_cost_mult"), career=False),
        active_karma_rules=_filter_karma_rules(ctx.effects.get("active_skill_karma_cost"), career=False),
        group_karma_mults=_active_karma_mults(ctx.effects.get("skill_group_category_karma_cost_mult"), career=False),
        group_karma_rules=_filter_karma_rules(ctx.effects.get("skill_category_karma_cost"), career=False),
    )
    ctx.errors.extend(purchases.errors)
    ctx.skill_buy_karma = purchases.karma
    ctx.knowledge_karma = knowledge_excess_karma(
        {r["name"]: int(r["rating"]) for r in ctx.knowledge["public"] if not r.get("native")},
        ctx.know_max,
        floors=resolved.free_knowledge,
        categories=ctx.state.knowledge_categories,
        karma_mults=_active_karma_mults(ctx.effects.get("skill_category_karma_cost_mult"), career=False),
    )
    for name, paid in original["knowledge_skills"].items():
        requested = paid + resolved.free_knowledge.get(name, 0)
        if requested > resolved.policy.knowledge_cap:
            ctx.err("engine.life.purchaseCap", name=term(name), requested=requested, cap=resolved.policy.knowledge_cap)
    public = ctx.life["skill_public"]
    public["purchase_preview"] = {**asdict(purchases), "karma": purchases.karma}
    public["complete"] = public["complete"] and not purchases.errors
    _growth_rules(ctx)


def _growth_rules(ctx: Ctx) -> None:
    rules = current_rules()
    ctx.life["skill_public"]["growth_rules"] = {
        "active": rules.karma_active_skill,
        "new_active": rules.karma_new_active_skill,
        "group": rules.karma_skill_group,
        "new_group": rules.karma_new_skill_group,
        "knowledge": rules.karma_knowledge,
        "new_knowledge": rules.karma_new_knowledge_skill,
        "active_mults": _active_karma_mults(ctx.effects.get("skill_category_karma_cost_mult"), career=True),
        "group_mults": _active_karma_mults(ctx.effects.get("skill_group_category_karma_cost_mult"), career=True),
        "active_rules": _filter_karma_rules(ctx.effects.get("active_skill_karma_cost"), career=True),
        "knowledge_rules": _filter_karma_rules(ctx.effects.get("knowledge_skill_karma_cost"), career=True),
        "group_rules": _filter_karma_rules(ctx.effects.get("skill_category_karma_cost"), career=True),
    }


def _prepare_career(ctx: Ctx) -> None:
    snapshot = ctx.state.life_module_skill_snapshot
    if snapshot is None:
        ctx.err("engine.life.snapshotRequired")
        resolved = LifeSkillResolution(life_skill_policy())
        ctx.life["skill_resolution"] = resolved
        ctx.life["skill_public"] = {**resolved.public(), "complete": False}
        return
    valid_inputs = skill_input_signature(ctx.state) == snapshot.input_signature
    if not valid_inputs:
        ctx.err("engine.life.careerFrozen")
    resolved = LifeSkillResolution(
        snapshot.policy,
        free_active=dict(snapshot.free_active),
        free_knowledge=dict(snapshot.free_knowledge),
        knowledge_categories=dict(snapshot.knowledge_categories),
        native_languages=list(snapshot.native_languages),
    )
    ctx.life["skill_resolution"] = resolved
    ctx.life["skill_public"] = {
        **deepcopy(snapshot.public),
        "frozen": True,
        "skill_catalog": ctx.data["skills"],
        "unavailable_skill_ids": sorted(_unavailable(ctx)),
    }
    ctx.life["karma"] = int(snapshot.public.get("module_karma", ctx.life["karma"]))
    apply_free(ctx, resolved)
    picks = resolve_skill_picks(
        ctx.state, ctx.data["skills"], ctx.state.skills, skip_ids=ctx.hosted_ware_ids | ctx.inactive_ware_ids
    )
    bonuses = {
        life_skill_key(s["id"]): picks["skill_max_bonus"].get(s["name"], 0) for s in ctx.data["skills"]["skills"]
    }
    for key in set(snapshot.creation_active) | {
        life_skill_key(row.target_id, row.specific)
        for row in ctx.state.life_module_skill_advancements
        if row.kind == "exotic"
    }:
        if key.startswith("exotic:"):
            _, sid, specific = key.split(":", 2)
            spec = next((s for s in ctx.data["skills"]["skills"] if s["id"] == sid), None)
            if spec:
                bonuses[key] = picks["skill_max_bonus"].get(spec["name"], 0) + picks["skill_max_bonus"].get(
                    exotic_skill_label(spec["name"], specific), 0
                )
    growth = replay_advancements(
        snapshot,
        ctx.state.life_module_skill_advancements,
        ctx.data["skills"],
        active_cap=ctx.skill_rating_cap,
        knowledge_cap=ctx.knowledge_rating_cap,
        bonuses=bonuses,
    )
    ctx.errors.extend(growth.errors)
    ctx.life["career_skills"] = growth
    public = ctx.life["skill_public"]
    public.update(
        current_active=growth.active,
        current_knowledge=growth.knowledge,
        growth_lines=growth.lines,
        complete=not growth.errors and valid_inputs,
    )
    ctx.state.skills = {}
    ctx.state.skill_groups = {}
    ctx.state.exotic_skills = []
    by_id = {s["id"]: s for s in ctx.data["skills"]["skills"]}
    for key, rating in growth.active.items():
        if key.startswith("skill:") and key[6:] in by_id:
            ctx.state.skills[by_id[key[6:]]["name"]] = rating
        elif key.startswith("exotic:"):
            _, sid, specific = key.split(":", 2)
            if sid in by_id:
                original = next(
                    (
                        r
                        for r in ctx.life["original"]["exotic_skills"]
                        if r.skill_name == by_id[sid]["name"] and r.extra.lower() == specific
                    ),
                    None,
                )
                ctx.state.exotic_skills.append(
                    ExoticSkillInstall(
                        id=original.id if original else str(uuid5(NAMESPACE_URL, f"life-free:{ctx.state.id}:{key}")),
                        skill_name=by_id[sid]["name"],
                        extra=specific,
                        rating=rating,
                    )
                )
            else:
                ctx.err("engine.life.snapshotRequired")
        else:
            ctx.err("engine.life.snapshotRequired")
    ctx.state.knowledge_skills = growth.knowledge
    ctx.state.knowledge_categories.update(growth.categories)


def _unavailable(ctx: Ctx) -> set[str]:
    disabled = set(ctx.effects.get("disabled_skills") or [])
    disabled_groups = set(ctx.effects.get("disabled_skill_groups") or [])
    unavailable: set[str] = set()
    for skill in ctx.data["skills"]["skills"]:
        group = skill.get("skillgroup")
        if (
            skill["name"] in disabled
            or group in disabled_groups
            or (skill.get("attribute") == "RES" and ctx.state.talent not in RES_TALENTS)
            or (skill.get("attribute") == "MAG" and not ctx.special_floors.get("MAG"))
            or (group == "Sorcery" and ctx.state.talent not in SPELL_TALENTS)
            or (group == "Conjuring" and ctx.state.talent not in SPIRIT_TALENTS)
        ):
            unavailable.add(skill["id"])
    return unavailable
