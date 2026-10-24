"""Pure RF life-module skill grants and constrained overflow transfers.

The caller validates module availability, families and prerequisites first.
This layer processes resolved acquisitions, without touching purchased ratings,
CharacterState, the current career cap, or previously cached derived values.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from ..models.life_modules import LifeModuleSkillPolicy, LifeModuleTransfer
from ..notices import Notice, notice, term

STAGES = ("Nationality", "Formative Years", "Teen Years", "Further Education", "Real Life")


@dataclass(frozen=True)
class LifeSkillGrant:
    kind: Literal["skills", "skill_groups", "knowledge_skills"]
    name: str
    amount: int
    category: str = "Professional"


@dataclass(frozen=True)
class LifeSkillEvent:
    entry_id: str
    module_id: str
    name: str
    stage: str
    grants: tuple[LifeSkillGrant, ...]


@dataclass
class LifeSkillCandidate:
    skill_id: str
    name: str
    attribute: str
    specific_required: bool
    capacity: int
    unavailable_reason: str = ""


@dataclass
class LifeSkillPool:
    key: str
    entry_id: str
    source_skill_id: str
    source_name: str
    stage: str
    before: int
    grant: int
    kept: int
    total: int
    grant_fingerprint: str
    candidates: list[LifeSkillCandidate]
    kind: Literal["active", "knowledge"] = "active"
    allocated: int = 0
    remaining: int = 0
    unallocatable: int = 0
    status: Literal["complete", "pending", "invalid", "unallocatable"] = "pending"
    transfers: list[dict[str, Any]] = field(default_factory=list)
    provisional: bool = False


@dataclass
class LifeSkillResolution:
    policy: LifeModuleSkillPolicy
    free_active: dict[str, int] = field(default_factory=dict)
    free_knowledge: dict[str, int] = field(default_factory=dict)
    requested_knowledge: dict[str, int] = field(default_factory=dict)
    knowledge_categories: dict[str, str] = field(default_factory=dict)
    native_languages: list[str] = field(default_factory=list)
    groups: list[dict[str, Any]] = field(default_factory=list)
    pools: list[LifeSkillPool] = field(default_factory=list)
    losses: list[dict[str, Any]] = field(default_factory=list)
    errors: list[Notice] = field(default_factory=list)
    warnings: list[Notice] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return not self.errors

    def public(self) -> dict[str, Any]:
        """JSON-compatible engine output; no Pydantic objects on the wire."""
        out = asdict(self)
        out["policy"] = self.policy.model_dump()
        return {"version": 2, **out, "complete": self.complete, "frozen": False, "legacy": False}


def life_skill_key(skill_id: str, specific: str = "") -> str:
    """Use the same case-insensitive concrete target identity as Exotic skills."""
    return f"exotic:{skill_id}:{specific.strip().lower()}" if specific else f"skill:{skill_id}"


def life_skill_events(
    rows: list[dict[str, Any]], entry_ids: list[str], choices: dict[str, str]
) -> tuple[list[LifeSkillEvent], list[Notice]]:
    """Resolve catalog grants without losing the saved choice's occurrence.

    Rows are the validated selections from the existing life-module prepare
    phase. It supplies ``occurrence`` even when an earlier entry was rejected.
    """
    events: list[LifeSkillEvent] = []
    errors: list[Notice] = []
    for index, row in enumerate(rows):
        occurrence = int(row.get("occurrence", index))
        if not 0 <= occurrence < len(entry_ids):
            raise ValueError("life-module acquisition has no entry ID")
        by_choice = {c["key"]: c for c in row["choices"]}
        resolved: list[LifeSkillGrant] = []
        for grant in row["grants"]:
            kind = grant["kind"]
            if kind not in {"skills", "skill_groups", "knowledge_skills"}:
                continue
            name = grant["name"]
            if not name:
                slot = f"{occurrence}:{grant['choice']}"
                name = choices.get(slot, "").strip()
                choice = by_choice.get(grant["choice"])
                if (
                    not choice
                    or not name
                    or (choice["options"] and name not in choice["options"] and not choice.get("allow_custom"))
                    or (choice.get("allow_custom") and "[" in name)
                ):
                    errors.append(notice("engine.life.choice", name=term(row["name"]), slot=slot))
                    continue
            category = grant.get("category") or "Professional"
            if grant.get("category_choice"):
                slot = f"{occurrence}:{grant['category_choice']}"
                category = choices.get(slot, "")
                choice = by_choice.get(grant["category_choice"])
                if not choice or category not in choice["options"]:
                    errors.append(notice("engine.life.choice", name=term(row["name"]), slot=slot))
                    continue
            resolved.append(LifeSkillGrant(kind=kind, name=name.strip(), amount=grant["value"], category=category))
        events.append(
            LifeSkillEvent(
                entry_id=entry_ids[occurrence],
                module_id=row["id"],
                name=row["name"],
                stage=row["stage"],
                grants=tuple(resolved),
            )
        )
    return events, errors


def _fingerprint(event: LifeSkillEvent, skill: dict[str, Any], amount: int, policy: LifeModuleSkillPolicy) -> str:
    # Semantic fields only: translating or reordering XML never expires a pick.
    data = {
        "module": event.module_id,
        "stage": event.stage,
        "skill": skill["id"],
        "attribute": skill.get("attribute"),
        "group": skill.get("skillgroup") or "",
        "amount": amount,
        "policy": policy.model_dump(),
    }
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _knowledge_fingerprint(
    event: LifeSkillEvent, name: str, category: str, amount: int, policy: LifeModuleSkillPolicy
) -> str:
    data = {
        "module": event.module_id,
        "stage": event.stage,
        "knowledge": name,
        "category": category,
        "amount": amount,
        "cap": policy.knowledge_cap,
        "rule": "knowledge-free-distribution-v1",
    }
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _capacity(free: dict[str, int], skill: dict[str, Any], policy: LifeModuleSkillPolicy, specific: str = "") -> int:
    return max(0, policy.active_cap - free.get(life_skill_key(skill["id"], specific), 0))


def resolve_life_module_skills(
    events: list[LifeSkillEvent],
    skills_data: dict[str, Any],
    transfers: list[LifeModuleTransfer],
    *,
    policy: LifeModuleSkillPolicy | None = None,
    unavailable_skill_ids: frozenset[str] = frozenset(),
    known_knowledge_categories: dict[str, str] | None = None,
    known_native_languages: frozenset[str] = frozenset(),
) -> LifeSkillResolution:
    """Resolve life-stage events, module grants, then each module's transfers.

    ``unavailable_skill_ids`` comes from the caller's resolved talent and
    disabled-skill rules. Defaultability does not mean learnability.
    Transfer pools are atomic: invalid rows are preserved but none is applied.
    """
    policy = policy or LifeModuleSkillPolicy()
    if len(events) > 512 or len(transfers) > 4096:
        raise ValueError("too many life-module skill events or transfers")
    if len({event.entry_id for event in events}) != len(events):
        raise ValueError("duplicate life-module entry ID")
    result = LifeSkillResolution(policy=policy)
    skills = {str(s["id"]): s for s in skills_data["skills"]}
    knowledge_categories = {
        **{str(s["name"]): str(s["category"]) for s in skills_data.get("knowledge", [])},
        **(known_knowledge_categories or {}),
    }
    native_names = set(known_native_languages) | {
        grant.name
        for event in events
        for grant in event.grants
        if grant.kind == "knowledge_skills" and grant.category == "Language" and grant.amount == 0
    }
    by_name = {str(s["name"]): s for s in skills.values()}
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for skill in skills.values():
        if skill.get("skillgroup") and not skill.get("exotic"):
            groups[skill["skillgroup"]].append(skill)
    picks: dict[tuple[str, str, str], list[LifeModuleTransfer]] = defaultdict(list)
    for transfer in transfers:
        picks[(transfer.entry_id, transfer.source_kind, transfer.source_skill_id)].append(transfer)
    duplicate_ids = {key for key, count in Counter(t.id for t in transfers).items() if count > 1}
    consumed: set[tuple[str, str, str]] = set()
    # Physical acquisition order within each stage is significant. Neither
    # caller input nor stored positional choices are reordered in place.
    ordered = sorted(
        enumerate(events), key=lambda item: (STAGES.index(item[1].stage) if item[1].stage in STAGES else 99, item[0])
    )
    for _, event in ordered:
        if event.stage not in STAGES:
            result.errors.append(notice("engine.life.skillGrantInvalid", name=term(event.name)))
            continue
        amounts = _event_amounts(result, event, by_name, groups)
        # All direct grants are applied before any transfers from this event.
        pools = _apply_direct(result, event, amounts, skills) + _apply_knowledge(result, event)
        for pool in pools:
            pool.provisional = bool(result.errors)
            if pool.kind == "active":
                pool.candidates = _candidates(result, pool, skills, unavailable_skill_ids)
            group_key = (event.entry_id, pool.kind, pool.source_skill_id)
            consumed.add(group_key)
            if pool.kind == "knowledge":
                _allocate_knowledge(
                    result, pool, picks.get(group_key, []), duplicate_ids, knowledge_categories, native_names
                )
            else:
                _allocate(result, pool, picks.get(group_key, []), skills, unavailable_skill_ids, duplicate_ids)
            result.pools.append(pool)
    for orphan_key, rows in picks.items():
        if orphan_key not in consumed:
            result.errors.extend(notice("engine.life.transferOrphan", transfer=t.id) for t in rows)
    _summarize_groups(result, groups)
    return result


def _event_amounts(
    result: LifeSkillResolution,
    event: LifeSkillEvent,
    by_name: dict[str, dict[str, Any]],
    groups: dict[str, list[dict[str, Any]]],
) -> dict[str, int]:
    """Free active levels per skill id from one module."""
    amounts: dict[str, int] = defaultdict(int)
    for grant in event.grants:
        if type(grant.amount) is not int or not 0 <= grant.amount <= 1000:
            result.errors.append(notice("engine.life.skillGrantInvalid", name=term(grant.name)))
            continue
        if grant.kind == "knowledge_skills":
            continue
        if grant.kind == "skill_groups":
            if grant.name not in groups:
                result.errors.append(notice("engine.life.skillGrantInvalid", name=term(grant.name)))
            for member in groups.get(grant.name, []):
                amounts[member["id"]] += grant.amount
            continue
        skill = by_name.get(grant.name)
        if not skill or skill.get("exotic") or skill.get("knowledge"):
            result.errors.append(notice("engine.life.skillGrantInvalid", name=term(grant.name)))
            continue
        amounts[skill["id"]] += grant.amount
    return amounts


def _apply_direct(
    result: LifeSkillResolution, event: LifeSkillEvent, amounts: dict[str, int], skills: dict[str, dict[str, Any]]
) -> list[LifeSkillPool]:
    """Raise each skill up to the cap. What does not fit opens a transfer pool
    in Real Life for an ungrouped skill, and is lost everywhere else."""
    pools: list[LifeSkillPool] = []
    for sid, amount in sorted(amounts.items()):
        skill = skills[sid]
        key = life_skill_key(sid)
        before = result.free_active.get(key, 0)
        kept = min(amount, max(0, result.policy.active_cap - before))
        if kept:
            result.free_active[key] = before + kept
        excess = amount - kept
        if not excess:
            continue
        if event.stage == "Real Life" and not skill.get("skillgroup"):
            pools.append(
                LifeSkillPool(
                    key=f"{event.entry_id}:{sid}",
                    entry_id=event.entry_id,
                    source_skill_id=sid,
                    source_name=skill["name"],
                    stage=event.stage,
                    before=before,
                    grant=amount,
                    kept=kept,
                    total=excess,
                    remaining=excess,
                    grant_fingerprint=_fingerprint(event, skill, amount, result.policy),
                    candidates=[],
                )
            )
            continue
        result.losses.append(
            {
                "entry_id": event.entry_id,
                "skill_key": key,
                "before": before,
                "grant": amount,
                "kept": kept,
                "lost": excess,
                "reason": "grouped" if skill.get("skillgroup") else "general",
            }
        )
        result.warnings.append(
            notice("engine.life.skillExcessLost", name=term(skill["name"]), lost=excess, stage=event.stage)
        )
    return pools


def _candidates(
    result: LifeSkillResolution,
    pool: LifeSkillPool,
    skills: dict[str, dict[str, Any]],
    unavailable: frozenset[str],
) -> list[LifeSkillCandidate]:
    """The active skills on the same attribute the pool's excess may move to."""
    source = skills[pool.source_skill_id]
    return [
        LifeSkillCandidate(
            skill_id=sid,
            name=s["name"],
            attribute=s.get("attribute") or "",
            specific_required=bool(s.get("exotic")),
            capacity=0 if sid in unavailable else _capacity(result.free_active, s, result.policy),
            unavailable_reason="unavailable" if sid in unavailable else "",
        )
        for sid, s in sorted(skills.items())
        if sid != pool.source_skill_id and s.get("attribute") == source.get("attribute") and not s.get("knowledge")
    ]


def _summarize_groups(result: LifeSkillResolution, groups: dict[str, list[dict[str, Any]]]) -> None:
    for name, members in sorted(groups.items()):
        values = {life_skill_key(s["id"]): result.free_active.get(life_skill_key(s["id"]), 0) for s in members}
        uniform = len(set(values.values())) == 1
        result.groups.append(
            {
                "name": name,
                "member_keys": list(values),
                "member_free_ratings": values,
                "uniform": uniform,
                "free_uniform_rating": next(iter(values.values())) if uniform else None,
            }
        )


def _apply_knowledge(result: LifeSkillResolution, event: LifeSkillEvent) -> list[LifeSkillPool]:
    """Apply a module's knowledge grants together, before distributing excess."""
    amounts: dict[str, int] = defaultdict(int)
    categories: dict[str, str] = {}
    for grant in event.grants:
        if grant.kind != "knowledge_skills" or type(grant.amount) is not int or not 0 <= grant.amount <= 1000:
            continue
        if grant.category == "Language" and grant.amount == 0:
            if grant.name not in result.native_languages:
                result.native_languages.append(grant.name)
            continue
        amounts[grant.name] += grant.amount
        if grant.name in categories and categories[grant.name] != grant.category:
            result.errors.append(notice("engine.life.skillGrantInvalid", name=term(grant.name)))
        categories[grant.name] = grant.category
    pools: list[LifeSkillPool] = []
    for name, amount in sorted(amounts.items()):
        before = result.free_knowledge.get(name, 0)
        kept = min(amount, max(0, result.policy.knowledge_cap - before))
        result.requested_knowledge[name] = result.requested_knowledge.get(name, 0) + amount
        result.free_knowledge[name] = before + kept
        result.knowledge_categories[name] = categories[name]
        excess = amount - kept
        if excess:
            pools.append(
                LifeSkillPool(
                    key=f"{event.entry_id}:knowledge:{name}",
                    entry_id=event.entry_id,
                    source_skill_id=name,
                    source_name=name,
                    stage=event.stage,
                    before=before,
                    grant=amount,
                    kept=kept,
                    total=excess,
                    remaining=excess,
                    grant_fingerprint=_knowledge_fingerprint(event, name, categories[name], amount, result.policy),
                    candidates=[],
                    kind="knowledge",
                )
            )
    return pools


def _allocate_knowledge(
    result: LifeSkillResolution,
    pool: LifeSkillPool,
    rows: list[LifeModuleTransfer],
    duplicate_ids: set[str],
    known_categories: dict[str, str],
    native_names: set[str],
) -> None:
    errors: list[Notice] = []
    destinations: set[str] = set()
    requested = sum(row.ranks for row in rows)
    if requested > pool.total:
        errors.append(
            notice(
                "engine.life.transferOverallocated", name=term(pool.source_name), total=pool.total, requested=requested
            )
        )
    for row in rows:
        name = row.destination_skill_id.strip()
        category = row.destination_category
        if row.grant_fingerprint != pool.grant_fingerprint:
            errors.append(notice("engine.life.transferSourceChanged", name=term(pool.source_name)))
        if (
            not name
            or name == pool.source_name
            or name in result.native_languages
            or name in native_names
            or "[" in name
            or "]" in name
            or row.destination_specific
            or category is None
            or (name in result.knowledge_categories and result.knowledge_categories[name] != category)
            or (name in known_categories and known_categories[name] != category)
        ):
            errors.append(notice("engine.life.transferInvalidTarget", transfer=row.id))
            continue
        if name in destinations or row.id in duplicate_ids:
            errors.append(notice("engine.life.transferDuplicate", transfer=row.id))
        destinations.add(name)
        capacity = max(0, result.policy.knowledge_cap - result.free_knowledge.get(name, 0))
        if row.ranks > capacity:
            errors.append(
                notice("engine.life.transferCapacity", name=term(name), requested=row.ranks, capacity=capacity)
            )
    pool.transfers = [
        {
            "id": row.id,
            "requested": row.ranks,
            "applied": 0 if errors else row.ranks,
            "status": "invalid" if errors else "applied",
            "error_key": errors[0]["key"] if errors else "",
        }
        for row in rows
    ]
    if errors:
        pool.status = "invalid"
        result.errors.extend(errors)
        return
    for row in rows:
        name = row.destination_skill_id.strip()
        result.free_knowledge[name] = result.free_knowledge.get(name, 0) + row.ranks
        result.knowledge_categories[name] = row.destination_category or "Professional"
        pool.allocated += row.ranks
    pool.remaining = pool.total - pool.allocated
    pool.status = "complete" if pool.remaining == 0 else "pending"
    if pool.remaining:
        result.errors.append(
            notice("engine.life.transferPending", name=term(pool.source_name), remaining=pool.remaining)
        )


def _allocate(
    result: LifeSkillResolution,
    pool: LifeSkillPool,
    rows: list[LifeModuleTransfer],
    skills: dict[str, dict[str, Any]],
    unavailable: frozenset[str],
    duplicate_ids: set[str],
) -> None:
    errors: list[Notice] = []
    destinations: set[str] = set()
    valid: list[tuple[LifeModuleTransfer, str]] = []
    candidates = {candidate.skill_id for candidate in pool.candidates}
    requested = sum(t.ranks for t in rows)
    if requested > pool.total:
        errors.append(
            notice(
                "engine.life.transferOverallocated", name=term(pool.source_name), total=pool.total, requested=requested
            )
        )
    for row in rows:
        skill = skills.get(row.destination_skill_id)
        specific = row.destination_specific
        if row.destination_category is not None:
            errors.append(notice("engine.life.transferInvalidTarget", transfer=row.id))
        if row.grant_fingerprint != pool.grant_fingerprint:
            errors.append(notice("engine.life.transferSourceChanged", name=term(pool.source_name)))
        if not skill or row.destination_skill_id not in candidates or row.destination_skill_id in unavailable:
            errors.append(notice("engine.life.transferInvalidTarget", transfer=row.id))
            continue
        if bool(skill.get("exotic")) != bool(specific) or "[" in specific or "]" in specific:
            errors.append(notice("engine.life.transferInvalidTarget", transfer=row.id))
            continue
        key = life_skill_key(skill["id"], specific)
        if key in destinations or row.id in duplicate_ids:
            errors.append(notice("engine.life.transferDuplicate", transfer=row.id))
        destinations.add(key)
        capacity = _capacity(result.free_active, skill, result.policy, specific)
        if row.ranks > capacity:
            errors.append(
                notice("engine.life.transferCapacity", name=term(skill["name"]), requested=row.ranks, capacity=capacity)
            )
        valid.append((row, key))
    pool.transfers = [
        {
            "id": row.id,
            "requested": row.ranks,
            "applied": 0,
            "status": "invalid" if errors else "applied",
            "error_key": errors[0]["key"] if errors else "",
        }
        for row in rows
    ]
    if errors:
        pool.status = "invalid"
        result.errors.extend(errors)
        return
    for row, key in valid:
        result.free_active[key] = result.free_active.get(key, 0) + row.ranks
        pool.allocated += row.ranks
    for entry in pool.transfers:
        entry["applied"] = entry["requested"]
    pool.remaining = pool.total - pool.allocated
    if not pool.remaining:
        pool.status = "complete"
        return
    # An Exotic can always have another concrete target. Do not enumerate an
    # unbounded set, and do not claim it has no capacity because one is full.
    available = [c for c in pool.candidates if c.skill_id not in unavailable]
    capacity = (
        pool.remaining
        if any(c.specific_required for c in available)
        else sum(_capacity(result.free_active, skills[c.skill_id], result.policy) for c in available)
    )
    if capacity < pool.remaining:
        pool.unallocatable = pool.remaining - capacity
        pool.remaining = capacity
        result.warnings.append(
            notice("engine.life.transferUnallocatable", name=term(pool.source_name), lost=pool.unallocatable)
        )
    if pool.remaining:
        pool.status = "pending"
        result.errors.append(
            notice("engine.life.transferPending", name=term(pool.source_name), remaining=pool.remaining)
        )
    else:
        pool.status = "unallocatable"
