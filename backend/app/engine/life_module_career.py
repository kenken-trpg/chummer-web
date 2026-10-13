"""Frozen RF creation skill ratings and chronological, priced career raises."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from ..models import CharacterState
from ..models.life_modules import LifeModuleGrowthPrice, LifeModuleSkillAdvancement, LifeModuleSkillSnapshot
from ..notices import Notice, notice
from .karma import skill_levels_karma_cost
from .life_module_skills import life_skill_key

FROZEN_FIELDS = (
    "build_method",
    "metatype",
    "metavariant",
    "talent",
    "life_module_rules_version",
    "life_modules",
    "life_module_entry_ids",
    "life_module_choices",
    "life_module_transfers",
    "skills",
    "skill_groups",
    "exotic_skills",
    "knowledge_skills",
    "knowledge_categories",
    "native_languages",
)


def skill_input_signature(state: CharacterState) -> str:
    raw = state.model_dump(mode="json")
    data = {key: raw[key] for key in FROZEN_FIELDS}
    data["caps"] = [state.settings.chargen_skill_max, state.settings.chargen_knowledge_skill_max]
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


@dataclass
class LifeCareerSkills:
    active: dict[str, int]
    knowledge: dict[str, int]
    categories: dict[str, str]
    karma: int = 0
    lines: list[dict[str, Any]] = field(default_factory=list)
    errors: list[Notice] = field(default_factory=list)


def advancement_targets(
    row: LifeModuleSkillAdvancement, active: dict[str, int], knowledge: dict[str, int], skills_data: dict[str, Any]
) -> dict[str, int]:
    skills = {s["id"]: s for s in skills_data["skills"]}
    if row.kind in {"knowledge", "group"} and row.specific:
        return {}
    if row.kind == "knowledge":
        return {row.target_id: knowledge.get(row.target_id, 0)}
    if row.kind == "group":
        members = [s for s in skills.values() if s.get("skillgroup") == row.target_id and not s.get("exotic")]
        return {life_skill_key(s["id"]): active.get(life_skill_key(s["id"]), 0) for s in members}
    skill = skills.get(row.target_id)
    if row.kind == "exotic" and any(c in row.specific for c in "[]"):
        return {}
    if not skill or bool(skill.get("exotic")) != (row.kind == "exotic") or bool(row.specific) != (row.kind == "exotic"):
        return {}
    key = life_skill_key(skill["id"], row.specific)
    return {key: active.get(key, 0)}


def growth_cost(low: int, high: int, price: LifeModuleGrowthPrice) -> int:
    return skill_levels_karma_cost(
        {"growth": high},
        {"growth": high - low},
        {"growth": price.category},
        per_rating=price.per_rating,
        first_level=price.first_level,
        karma_mults={price.category: price.multiplier},
        flat_rules=price.flat_rules,
    )


def replay_advancements(
    snapshot: LifeModuleSkillSnapshot,
    rows: list[LifeModuleSkillAdvancement],
    skills_data: dict[str, Any],
    *,
    active_cap: int,
    knowledge_cap: int,
    bonuses: dict[str, int] | None = None,
) -> LifeCareerSkills:
    result = LifeCareerSkills(
        dict(snapshot.creation_active), dict(snapshot.creation_knowledge), dict(snapshot.knowledge_categories)
    )
    seen: set[str] = set()
    for row in rows:
        targets = advancement_targets(row, result.active, result.knowledge, skills_data)
        cap = knowledge_cap if row.kind == "knowledge" else active_cap
        if (
            result.errors
            or row.id in seen
            or not targets
            or targets != row.from_ratings
            or row.price is None
            or (row.kind == "knowledge" and row.target_id in snapshot.native_languages)
            or (row.kind == "group" and len(set(targets.values())) != 1)
            or any(
                n + row.levels > cap + (0 if row.kind in {"group", "knowledge"} else (bonuses or {}).get(key, 0))
                for key, n in targets.items()
            )
        ):
            result.errors.append(notice("engine.life.advancementInvalid"))
            continue
        seen.add(row.id)
        low = next(iter(targets.values()))
        cost = growth_cost(low, low + row.levels, row.price)
        destination = result.knowledge if row.kind == "knowledge" else result.active
        destination.update({key: n + row.levels for key, n in targets.items()})
        if row.kind == "knowledge":
            result.categories[row.target_id] = row.category
        result.karma += cost
        result.lines.append(
            {
                "id": row.id,
                "kind": row.kind,
                "target_id": row.target_id,
                "levels": row.levels,
                "from_rating": low,
                "to_rating": low + row.levels,
                "karma": cost,
            }
        )
    return result
