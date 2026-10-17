"""Life-module free ratings, separate from the player's purchased ratings.

Only the working copy receives grants. Persisted input always holds purchases,
so removing a module and recomputing cannot leave or duplicate its benefits.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from ...models import CharacterState, ContactInstall
from ...notices import term
from ...rules import current_rules
from ..karma import attribute_levels_karma_cost, knowledge_excess_karma, skill_levels_karma_cost
from ..priority import resolve_talent_for_method
from .context import Ctx

STAGES = ("Nationality", "Formative Years", "Teen Years", "Further Education", "Real Life")
FIELDS = (
    "attributes",
    "skills",
    "skill_groups",
    "knowledge_skills",
    "knowledge_categories",
    "quality_extras",
    "native_languages",
    "skill_specializations",
    "contacts",
    "quality_ids",
    "exotic_skills",
)


def prepare(ctx: Ctx) -> None:
    if ctx.state.build_method != "LifeModule":
        return
    ctx.life["original"] = {key: deepcopy(getattr(ctx.state, key)) for key in FIELDS}
    by_id = {row["id"]: row for row in ctx.data.get("life_modules") or []}
    chosen: list[dict[str, Any]] = []
    seen: set[str] = set()
    families: set[str] = set()
    for occurrence, mid in enumerate(ctx.state.life_modules):
        row = by_id.get(mid)
        if not row:
            ctx.err("engine.life.unknown", name=mid)
            continue
        if row["unsupported"]:
            ctx.err("engine.life.unsupported", name=term(row["name"]), tags=", ".join(row["unsupported"]))
            continue
        if not _requirements_met(ctx, row.get("required") or []):
            ctx.err("engine.life.requirement", name=term(row["name"]))
            continue
        # Multiple adult careers are allowed, but each parent module only once.
        stage = row["stage"]
        if stage in STAGES[:3] and stage in seen:
            ctx.err("engine.life.duplicateStage", stage=stage)
            continue
        family = row.get("family_id") or row["id"]
        if family in families:
            ctx.err("engine.life.duplicateModule", name=term(row.get("parent") or row["name"]))
            continue
        families.add(family)
        seen.add(stage)
        chosen.append({**row, "occurrence": occurrence})
    for stage in STAGES:
        if stage not in seen and not ctx.career:
            ctx.err("engine.life.missingStage", stage=stage)
    levels_by_group: dict[str, int] = {}
    for row in chosen:
        for grant in row.get("quality_levels", []):
            group = str(grant["group"])
            levels_by_group[group] = max(levels_by_group.get(group, 0), int(grant["level"]))
    if levels_by_group:
        groups = ctx.data.get("quality_levels") or {}
        quality_by_name = {str(q["name"]): q for q in ctx.data["qualities"]}
        names_by_group = {
            group: {name: level for level, name in groups.get(group, {}).items()} for group in levels_by_group
        }
        # Existing picks in a quality-level group participate in the same
        # highest-level resolution as Life Module grants.
        for quality_id in list(ctx.state.quality_ids or []):
            quality = next((q for q in ctx.data["qualities"] if q["id"] == quality_id), None)
            if not quality:
                continue
            for group, names in names_by_group.items():
                level = names.get(quality["name"])
                if level:
                    levels_by_group[group] = max(levels_by_group[group], int(level))
        grouped_names = {name for names in names_by_group.values() for name in names}
        ctx.state.quality_ids = [
            quality_id
            for quality_id in (ctx.state.quality_ids or [])
            if not any(q["id"] == quality_id and q["name"] in grouped_names for q in ctx.data["qualities"])
        ]
        for group, level in levels_by_group.items():
            quality_name = groups[group].get(level)
            quality = quality_by_name.get(str(quality_name or ""))
            if not quality:
                ctx.err("engine.life.qualityLevelUnknown", name=term(str(quality_name or group)))
                continue
            ctx.state.quality_ids.append(str(quality["id"]))
    bonuses: dict[str, dict[str, int]] = {key: {} for key in FIELDS[:4]}
    quality_grants: list[dict[str, Any]] = []
    specialization_grants: set[tuple[str, str]] = set()
    for row in chosen:
        index = row["occurrence"]
        # Choice keys retain the original positions, including rejected entries.
        for grant in row["grants"]:
            if ctx.state.life_module_rules_version == 2 and grant["kind"] in {
                "skills",
                "skill_groups",
                "knowledge_skills",
            }:
                continue
            name = grant["name"]
            if not name:
                key = f"{index}:{grant['choice']}"
                name = ctx.state.life_module_choices.get(key, "")
                choice = next(c for c in row["choices"] if c["key"] == grant["choice"])
                options = choice["options"]
                if (
                    (options and name not in options and not choice.get("allow_custom"))
                    or not name.strip()
                    or (choice.get("allow_custom") and "[" in name)
                ):
                    ctx.err("engine.life.choice", name=term(row["name"]), slot=key)
                    continue
            name = name.strip()
            kind = grant["kind"]
            category = grant["category"]
            if grant.get("category_choice"):
                key = f"{index}:{grant['category_choice']}"
                category = ctx.state.life_module_choices.get(key, "")
                options = next(c["options"] for c in row["choices"] if c["key"] == grant["category_choice"])
                if category not in options:
                    ctx.err("engine.life.choice", name=term(row["name"]), slot=key)
                    continue
            if kind == "qualities":
                quality = next((q for q in ctx.data["qualities"] if q["name"] == name), None)
                if quality is None:
                    ctx.err("engine.life.qualityUnknown", name=term(name))
                    continue
                if grant.get("extra_choice"):
                    # The level was picked above; its own free text is a second
                    # slot, so a placeholder never passes for an answer.
                    key = f"{index}:{grant['extra_choice']}"
                    extra = ctx.state.life_module_choices.get(key, "").strip()
                    if not extra or "[" in extra:
                        ctx.err("engine.life.choice", name=term(row["name"]), slot=key)
                        continue
                    taken = (ctx.state.quality_extras.get(quality["id"]) or "").strip()
                    if taken and taken != extra:
                        ctx.err("engine.life.qualityChoiceConflict", name=term(quality["name"]))
                        continue
                    ctx.state.quality_extras[quality["id"]] = extra
                quality_grants.append(quality)
                continue
            if kind == "knowledge_skills" and category == "Language" and grant["value"] == 0:
                if name not in ctx.state.native_languages:
                    ctx.state.native_languages.append(name)
                continue
            bonuses[kind][name] = bonuses[kind].get(name, 0) + grant["value"]
            if kind == "knowledge_skills":
                ctx.state.knowledge_categories[name] = category
        quality_grants.extend(row["quality_grants"])
        for grant in row.get("quality_choice_grants", []):
            key = f"{index}:{grant['choice']}"
            picked = (grant["value"] or ctx.state.life_module_choices.get(key, "")).strip()
            quality = next((q for q in ctx.data["qualities"] if q["id"] == grant["quality_id"]), None)
            if quality is None:
                ctx.err("engine.life.qualityUnknown", name=grant["quality_id"])
                continue
            options = (
                ctx.data["skills"]["groups"]
                if quality.get("extra_kind") == "skillgroup"
                else quality.get("select_options") or []
            )
            if not picked or (options and picked not in options):
                ctx.err("engine.life.choice", name=term(row["name"]), slot=key)
                continue
            existing = (ctx.state.quality_extras.get(quality["id"]) or "").strip()
            if existing and existing != picked:
                ctx.err("engine.life.qualityChoiceConflict", name=term(quality["name"]))
                continue
            ctx.state.quality_extras[quality["id"]] = picked
            quality_grants.append(quality)
        for grant in row.get("specialization_grants", []):
            skill, spec = grant["skill"], grant["spec"]
            if grant.get("choice"):
                key = f"{index}:{grant['choice']}"
                spec = ctx.state.life_module_choices.get(key, "").strip()
                if not spec:
                    ctx.err("engine.life.choice", name=term(row["name"]), slot=key)
                    continue
            existing_spec = ctx.state.skill_specializations.get(skill)
            if existing_spec and existing_spec != spec:
                ctx.err("engine.life.specializationConflict", name=term(skill))
                continue
            ctx.state.skill_specializations[skill] = spec
            specialization_grants.add((skill, spec))
        for contact_index, grant in enumerate(row.get("contact_grants", [])):
            connection = max(1, min(12, int(grant["connection"])))
            loyalty = max(1, min(12, int(grant["loyalty"])))
            ctx.state.contacts.append(
                ContactInstall(
                    id=str(
                        uuid5(
                            NAMESPACE_URL,
                            f"chummer-web:{ctx.state.id}:life-contact:{row['id']}:{index}:{contact_index}",
                        )
                    ),
                    name=row["name"],
                    connection=connection,
                    loyalty=loyalty,
                    free=bool(grant["free"]),
                    free_connection=connection if grant["free"] else 0,
                    free_loyalty=loyalty if grant["free"] else 0,
                )
            )
    # Each module's group levels also add to members' individual free levels.
    for skill in ctx.data["skills"]["skills"]:
        group_bonus = bonuses["skill_groups"].get(skill.get("skillgroup"), 0)
        if group_bonus and not skill.get("exotic"):
            name = skill["name"]
            bonuses["skills"][name] = bonuses["skills"].get(name, 0) + group_bonus
    for kind, values in bonuses.items():
        target = getattr(ctx.state, kind)
        for name, amount in values.items():
            minimum = int((ctx.attrs_spec.get(name) or {}).get("min") or 0) if kind == "attributes" else 0
            bought = int(target.get(name) or minimum)
            if kind == "skills":
                paid_group_name = next(
                    (s.get("skillgroup") for s in ctx.data["skills"]["skills"] if s["name"] == name), ""
                )
                bought = max(bought, ctx.life["original"]["skill_groups"].get(paid_group_name, 0))
            target[name] = max(minimum, bought) + amount
    rated_grants: dict[str, dict[str, Any]] = {}
    for quality in quality_grants:
        if "life_rating" in quality:
            qid = quality["id"]
            previous = rated_grants.get(qid, {}).get("life_rating", 0)
            rated_grants[qid] = {**quality, "life_rating": previous + quality["life_rating"]}
    quality_grants = [q for q in quality_grants if q["id"] not in rated_grants]
    for qid, quality in rated_grants.items():
        if qid in ctx.life["original"]["quality_ids"]:
            ctx.err("engine.life.ratedQualityConflict", name=term(quality["name"]))
        elif quality["life_rating"] > quality["max_takes"]:
            ctx.err(
                "engine.life.ratingCap",
                name=term(quality["name"]),
                rating=quality["life_rating"],
                cap=quality["max_takes"],
            )
        else:
            quality_grants.append(quality)
    ctx.life.update(
        bonuses=bonuses,
        rows=chosen,
        qualities=quality_grants,
        karma=sum(row["karma"] for row in chosen),
        nuyen=sum(int(row.get("nuyen") or 0) for row in chosen),
        free_positive_qualities=sum(int(row.get("free_positive_qualities") or 0) for row in chosen),
        free_negative_qualities=sum(int(row.get("free_negative_qualities") or 0) for row in chosen),
        free_specializations=specialization_grants,
    )


def price(ctx: Ctx) -> None:
    if not ctx.life:
        return
    bonuses = ctx.life["bonuses"]
    rules = current_rules()
    for kind, grants in bonuses.items():
        for name, free in grants.items():
            if kind == "attributes":
                spec = ctx.attrs_spec.get(name) or {}
                cap = int(spec.get("max") or 0) + ctx.attr_max_bonus.get(name, 0)
                if name in {"MAG", "RES"} and name not in ctx.special_floors:
                    cap = 0
                floor = max(int(spec.get("min") or 0), ctx.special_floors.get(name, 0))
            else:
                cap = ctx.knowledge_rating_cap if kind == "knowledge_skills" else ctx.skill_rating_cap
                if kind == "skills":
                    cap += ctx.skill_picks["skill_max_bonus"].get(name, 0)
                floor = 0
            if free + floor > cap:
                ctx.err("engine.life.ratingCap", name=term(name), rating=free + floor, cap=cap)
    attr_levels = {
        key: max(
            0,
            rating
            - max(int((ctx.attrs_spec.get(key) or {}).get("min") or 0), ctx.special_floors.get(key, 0))
            - bonuses["attributes"].get(key, 0),
        )
        for key, rating in ctx.bought_ratings.items()
        if key != "ESS" and (key not in {"MAG", "RES"} or key in ctx.special_floors)
    }
    ctx.attr_karma = attribute_levels_karma_cost(
        ctx.bought_ratings,
        attr_levels,
        rules=ctx.effects.get("attribute_karma_cost"),
        minimums={key: int(spec["min"]) for key, spec in ctx.attrs_spec.items()},
    )
    if ctx.state.life_module_rules_version == 2:
        from ._life_module_skills import price

        price(ctx)
        return
    group_floors: dict[str, int] = {}
    for skill in ctx.data["skills"]["skills"]:
        name = skill["name"]
        group = skill.get("skillgroup")
        own_free = bonuses["skills"].get(name, 0) - bonuses["skill_groups"].get(group, 0)
        group_floors[name] = ctx.state.skill_groups.get(group, 0) + max(0, own_free)
    ctx.skill_buy_karma = skill_levels_karma_cost(
        ctx.skill_totals,
        {
            name: max(0, rating - max(group_floors.get(name, 0), bonuses["skills"].get(name, 0)))
            for name, rating in ctx.skill_totals.items()
        },
        {},
        per_rating=rules.karma_active_skill,
        first_level=rules.karma_new_active_skill,
    )
    ctx.skill_buy_karma += skill_levels_karma_cost(
        ctx.state.skill_groups,
        {
            name: max(0, rating - bonuses["skill_groups"].get(name, 0))
            for name, rating in ctx.state.skill_groups.items()
        },
        {},
        per_rating=rules.karma_skill_group,
    )
    # Module knowledge is already paid for by the module. Remaining purchased
    # knowledge retains the normal free-knowledge-point allowance.
    ctx.knowledge_karma = knowledge_excess_karma(
        {row["name"]: int(row["rating"]) for row in ctx.knowledge["public"] if not row.get("native")},
        ctx.know_max,
        floors=bonuses["knowledge_skills"],
        categories=ctx.state.knowledge_categories,
    )


def restore(ctx: Ctx) -> CharacterState:
    if ctx.life:
        for key, value in ctx.life["original"].items():
            setattr(ctx.state, key, value)
    return ctx.state


def _requirements_met(ctx: Ctx, tree: list[dict[str, Any]]) -> bool:
    if not tree:
        return True
    quality_by_id = {str(q["id"]): str(q["name"]) for q in ctx.data["qualities"]}
    quality_names = {quality_by_id[qid] for qid in (ctx.state.quality_ids or []) if qid in quality_by_id}
    talent = resolve_talent_for_method(
        ctx.state.priorities.Talent, ctx.state.talent, ctx.state.build_method, ctx.state.metatype
    )
    if talent.get("quality"):
        quality_names.add(str(talent["quality"]))
    metatype_names = {str(ctx.meta.get("name") or ""), str(ctx.state.metatype or "")}
    if ctx.state.metavariant:
        metatype_names.add(str(ctx.state.metavariant))

    def matches(node: dict[str, Any]) -> bool:
        tag = str(node.get("tag") or "")
        children = list(node.get("children") or [])
        if tag == "oneof":
            return any(matches(child) for child in children)
        if tag in {"allof", "group"}:
            return all(matches(child) for child in children)
        name = str(node.get("name") or "")
        if tag == "quality":
            return name in quality_names
        if tag == "metatype":
            return name in metatype_names
        return False

    return all(matches(node) for node in tree)
