"""Life-module purchases above resolved free skill levels.

Purchased inputs keep their existing meaning: individual and group inputs
overlap (max), whereas module grants and transfers are a separate free floor.
No rating is written back to the caller, including an illegal requested value.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from ..notices import Notice, notice, term
from ..rules import current_rules
from .karma import group_first_level, skill_levels_karma_cost
from .life_module_skills import LifeSkillResolution, life_skill_key


@dataclass
class LifeSkillPurchases:
    requested: dict[str, int] = field(default_factory=dict)
    totals: dict[str, int] = field(default_factory=dict)
    group_totals: dict[str, int] = field(default_factory=dict)
    active_karma: int = 0
    group_karma: int = 0
    compensation: int = 0
    errors: list[Notice] = field(default_factory=list)

    @property
    def karma(self) -> int:
        return self.active_karma + self.group_karma + self.compensation


def resolve_life_skill_purchases(
    free: LifeSkillResolution,
    skills_data: dict[str, Any],
    purchased_active: Mapping[str, int],
    purchased_groups: Mapping[str, int],
    *,
    skill_max_bonuses: Mapping[str, int] | None = None,
    active_karma_mults: Mapping[str, int] | None = None,
    active_karma_rules: Sequence[Mapping[str, Any]] | None = None,
    group_karma_mults: Mapping[str, int] | None = None,
    group_karma_rules: Sequence[Mapping[str, Any]] | None = None,
) -> LifeSkillPurchases:
    """Price validated purchases with the existing karma-rule arithmetic.

    Keys in purchased_active are stable skill keys, including concrete Exotic
    keys. The bridge to CharacterState is responsible for translating names.
    """
    rules = current_rules()
    out = LifeSkillPurchases()
    metadata = {life_skill_key(s["id"]): s for s in skills_data["skills"] if not s.get("exotic")}
    for key in set(free.free_active) | set(purchased_active):
        if key in metadata:
            continue
        exotic = next(
            (
                s
                for s in skills_data["skills"]
                if s.get("exotic")
                and key.startswith(f"exotic:{s['id']}:")
                and key.removeprefix(f"exotic:{s['id']}:").strip()
            ),
            None,
        )
        if exotic:
            metadata[key] = exotic
        else:
            out.errors.append(notice("engine.life.purchaseInvalid", name=key))
    bonuses = skill_max_bonuses or {}
    caps = {key: free.policy.active_cap + int(bonuses.get(key, 0)) for key in metadata}
    if any(not 1 <= cap <= 1000 for cap in caps.values()):
        raise ValueError("life-module purchase cap is out of bounds")
    group_members: dict[str, list[str]] = {}
    for key, skill in metadata.items():
        if skill.get("skillgroup") and not skill.get("exotic"):
            group_members.setdefault(skill["skillgroup"], []).append(key)

    def active_cost(key: str, low: int, high: int) -> int:
        return skill_levels_karma_cost(
            {key: high},
            {key: high - low},
            {key: metadata[key].get("category") or ""},
            per_rating=rules.karma_active_skill,
            first_level=rules.karma_new_active_skill,
            karma_mults=active_karma_mults,
            flat_rules=active_karma_rules,
        )

    def group_cost(group: str, low: int, high: int) -> int:
        categories = {metadata[key].get("category") or "" for key in group_members[group]}
        category = next(iter(categories)) if len(categories) == 1 else ""
        return skill_levels_karma_cost(
            {group: high},
            {group: high - low},
            {group: category},
            per_rating=rules.karma_skill_group,
            first_level=group_first_level(low, high),
            karma_mults=group_karma_mults,
            flat_rules=group_karma_rules,
        )

    applied_groups: dict[str, int] = {}
    for group, bought in purchased_groups.items():
        if not _valid_count(bought) or group not in group_members:
            out.errors.append(notice("engine.life.purchaseInvalid", name=term(group)))
            continue
        if not bought:
            continue
        values = {free.free_active.get(key, 0) for key in group_members[group]}
        if len(values) != 1:
            out.errors.append(notice("engine.life.groupPurchaseUnequal", group=term(group)))
            continue
        base = next(iter(values))
        requested = base + bought
        if requested > free.policy.active_cap:
            out.errors.append(
                notice("engine.life.purchaseCap", name=term(group), requested=requested, cap=free.policy.active_cap)
            )
            continue
        applied_groups[group] = bought
        out.group_totals[group] = requested
        out.group_karma += group_cost(group, base, requested)

    for key, skill in metadata.items():
        bought = purchased_active.get(key, 0)
        if not _valid_count(bought):
            out.errors.append(notice("engine.life.purchaseInvalid", name=term(skill["name"])))
            bought = 0
        base = free.free_active.get(key, 0)
        group_bought = applied_groups.get(skill.get("skillgroup") or "", 0)
        requested = base + max(bought, group_bought)
        out.requested[key] = requested
        if requested > caps[key]:
            out.errors.append(
                notice("engine.life.purchaseCap", name=term(skill["name"]), requested=requested, cap=caps[key])
            )
        # Keep the illegal input in requested; do not iterate over a huge input
        # just to generate a price for an unfinished character's preview.
        applied = min(requested, caps[key])
        if applied:
            out.totals[key] = applied
        out.active_karma += active_cost(key, base + group_bought, applied)

    if rules.compensate_skill_group_karma_difference:
        for group, members in group_members.items():
            if group in applied_groups or len(members) < 2:
                continue
            # Only levels bought by EVERY member can receive group pricing.
            # Using the first member's floor would refund another's free levels.
            low = max(free.free_active.get(key, 0) for key in members)
            high = min(out.totals.get(key, 0) for key in members)
            if high > low:
                out.compensation += group_cost(group, low, high) - sum(active_cost(key, low, high) for key in members)
    return out


def _valid_count(value: int) -> bool:
    return type(value) is int and 0 <= value <= 10**12
