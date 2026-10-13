"""Atomic RF career entry/exit and server-priced skill growth patches."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from .engine import compute, snapshot_career_baseline
from .engine.life_module_career import advancement_targets, replay_advancements, skill_input_signature
from .models import CharacterState
from .models.life_modules import LifeModuleGrowthPrice, LifeModuleSkillSnapshot
from .notices import NoticeError, notice


def finish_life_patch(previous: CharacterState, data: dict[str, Any]) -> None:
    """Run after all patch merges, talent changes and ordinary career setup."""
    if previous.career and previous.build_method == "LifeModule" and previous.life_module_rules_version == 2:
        if not data.get("career"):
            _return_to_creation(previous, data)
            return
        candidate = CharacterState.model_validate(data)
        snapshot = previous.life_module_skill_snapshot
        if snapshot is None:
            raise NoticeError(notice("engine.life.snapshotRequired"))
        if (
            skill_input_signature(candidate) != snapshot.input_signature
            or candidate.life_module_skill_snapshot != snapshot
            or candidate.life_module_skill_advancement_history != previous.life_module_skill_advancement_history
        ):
            raise NoticeError(notice("engine.life.careerFrozen"))
        _growth_patch(previous, candidate, data)
        return
    if data.get("career") and not previous.career and data.get("build_method") == "LifeModule":
        candidate = compute(CharacterState.model_validate({**data, "career": False}))
        public = candidate.derived.get("life_module_skills")
        if candidate.derived["errors"] or not public or not public["complete"]:
            raise NoticeError(notice("engine.life.creationIncomplete"))
        snapshot = LifeModuleSkillSnapshot(
            input_signature=skill_input_signature(candidate),
            policy=public["policy"],
            public=public,
            free_active=public["free_active"],
            free_knowledge=public["free_knowledge"],
            knowledge_categories=candidate.knowledge_categories | public["knowledge_categories"],
            native_languages=list(dict.fromkeys([*candidate.native_languages, *public["native_languages"]])),
            creation_active=public["purchase_preview"]["totals"],
            creation_knowledge={
                row["name"]: row["rating"] for row in candidate.derived["knowledge_skills"] if not row.get("native")
            },
            skill_karma=candidate.derived["karma_chargen"]["skills"],
            knowledge_karma=candidate.derived["karma_chargen"]["knowledge"],
        )
        data.update(candidate.model_dump())
        data["career"] = True
        baseline = snapshot_career_baseline(candidate)
        baseline.quality_ids = list(dict.fromkeys(q["id"] for q in candidate.derived["qualities"]))
        data["career_baseline"] = baseline.model_dump()
        data["life_module_skill_snapshot"] = snapshot.model_dump()
        data["life_module_skill_advancement_history"] = [
            r.model_dump()
            for r in [*candidate.life_module_skill_advancement_history, *candidate.life_module_skill_advancements]
        ]
        data["life_module_skill_advancements"] = []


def _growth_patch(previous: CharacterState, candidate: CharacterState, data: dict[str, Any]) -> None:
    snapshot = previous.life_module_skill_snapshot
    if snapshot is None:
        raise NoticeError(notice("engine.life.snapshotRequired"))
    old = previous.life_module_skill_advancements
    rows = candidate.life_module_skill_advancements
    # Preserve the history prefix; removing the tail is an explicit undo.
    if rows[: min(len(old), len(rows))] != old[: min(len(old), len(rows))]:
        raise NoticeError(notice("engine.life.advancementInvalid"))
    if len(rows) <= len(old):
        return
    current = compute(candidate.model_copy(update={"life_module_skill_advancements": list(old)}))
    public = current.derived["life_module_skills"]
    assert public is not None
    active = dict(public["current_active"])
    knowledge = dict(public["current_knowledge"])
    skills_data = public["skill_catalog"]
    metadata = {s["id"]: s for s in skills_data["skills"]}
    rules = public["growth_rules"]
    prices = []
    for row in rows[len(old) :]:
        if row.price is not None or row.from_ratings:
            raise NoticeError(notice("engine.life.advancementInvalid"))
        targets = advancement_targets(row, active, knowledge, skills_data)
        if (
            (row.kind == "knowledge" and row.target_id in snapshot.native_languages)
            or not targets
            or (row.kind != "knowledge" and row.target_id in public.get("unavailable_skill_ids", []))
        ):
            raise NoticeError(notice("engine.life.advancementInvalid"))
        low = next(iter(targets.values()))
        if row.kind == "group":
            category_set = {s.get("category", "") for s in metadata.values() if s.get("skillgroup") == row.target_id}
            category = next(iter(category_set)) if len(category_set) == 1 else ""
            price = LifeModuleGrowthPrice(
                per_rating=rules["group"],
                first_level=rules["new_group"] if low == 0 and row.levels == 1 else None,
                category=category,
                multiplier=rules["group_mults"].get(category, 100),
                flat_rules=rules["group_rules"],
            )
        else:
            category = row.category if row.kind == "knowledge" else metadata[row.target_id].get("category", "")
            kind = "knowledge" if row.kind == "knowledge" else "active"
            price = LifeModuleGrowthPrice(
                per_rating=rules[kind],
                first_level=rules[f"new_{kind}"],
                category=category,
                multiplier=rules["active_mults"].get(category, 100),
                flat_rules=rules[f"{kind}_rules"],
            )
        saved = row.model_copy(update={"from_ratings": targets, "price": price})
        prices.append(saved)
        if row.kind == "knowledge":
            knowledge.update({key: n + row.levels for key, n in targets.items()})
        else:
            active.update({key: n + row.levels for key, n in targets.items()})
    snapshot = previous.life_module_skill_snapshot
    assert snapshot is not None
    bonuses = {}
    for key in active:
        sid = key.split(":", 2)[1]
        spec = metadata.get(sid)
        if spec:
            bonuses[key] = current.derived["skill_max_bonus"].get(spec["name"], 0)
            if key.startswith("exotic:"):
                specific = key.split(":", 2)[2]
                bonuses[key] += current.derived["skill_max_bonus"].get(f"{spec['name']} ({specific})", 0)
    replay = replay_advancements(
        snapshot,
        [*old, *prices],
        skills_data,
        active_cap=current.derived["skill_rating_max"],
        knowledge_cap=current.derived["knowledge_rating_max"],
        bonuses=bonuses,
    )
    if replay.errors:
        raise NoticeError(notice("engine.life.advancementInvalid"))
    data["life_module_skill_advancements"] = [r.model_dump() for r in [*old, *prices]]


def _return_to_creation(previous: CharacterState, data: dict[str, Any]) -> None:
    current = compute(previous)
    public = current.derived["life_module_skills"]
    snapshot = previous.life_module_skill_snapshot
    if public is None or snapshot is None or not public["complete"]:
        raise NoticeError(notice("engine.life.snapshotRequired"))
    metadata = {s["id"]: s for s in public["skill_catalog"]["skills"]}
    skills: dict[str, int] = {}
    exotic = []
    for key, total in public["current_active"].items():
        bought = total - snapshot.free_active.get(key, 0)
        if not bought:
            continue
        sid = key.split(":", 2)[1]
        if sid not in metadata:
            raise NoticeError(notice("engine.life.snapshotRequired"))
        if key.startswith("exotic:"):
            exotic.append(
                {
                    "id": str(uuid4()),
                    "skill_name": metadata[sid]["name"],
                    "extra": key.split(":", 2)[2],
                    "rating": bought,
                }
            )
        else:
            skills[metadata[sid]["name"]] = bought
    data.update(
        skills=skills,
        skill_groups={},
        exotic_skills=exotic,
        knowledge_skills={
            name: n - snapshot.free_knowledge.get(name, 0)
            for name, n in public["current_knowledge"].items()
            if n > snapshot.free_knowledge.get(name, 0)
        },
        knowledge_categories=snapshot.knowledge_categories
        | {r.target_id: r.category for r in previous.life_module_skill_advancements if r.kind == "knowledge"},
        life_module_skill_snapshot=None,
    )
