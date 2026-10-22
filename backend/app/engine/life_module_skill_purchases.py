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
    out = LifeSkillPurchases()
    metadata = _skill_metadata(free, skills_data, purchased_active, out)
    bonuses = skill_max_bonuses or {}
    caps = {key: free.policy.active_cap + int(bonuses.get(key, 0)) for key in metadata}
    if any(not 1 <= cap <= 1000 for cap in caps.values()):
        raise ValueError("life-module purchase cap is out of bounds")
    group_members: dict[str, list[str]] = {}
    for key, skill in metadata.items():
        if skill.get("skillgroup") and not skill.get("exotic"):
            group_members.setdefault(skill["skillgroup"], []).append(key)
    prices = _Prices(
        metadata, group_members, active_karma_mults, active_karma_rules, group_karma_mults, group_karma_rules
    )
    applied_groups = _buy_groups(free, purchased_groups, group_members, prices, out)
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
        out.active_karma += prices.active(key, base + group_bought, applied)
    if current_rules().compensate_skill_group_karma_difference:
        out.compensation += _group_compensation(free, group_members, applied_groups, prices, out)
    return out


def _skill_metadata(
    free: LifeSkillResolution,
    skills_data: dict[str, Any],
    purchased_active: Mapping[str, int],
    out: LifeSkillPurchases,
) -> dict[str, dict[str, Any]]:
    """The catalog row behind every skill key, concrete Exotic keys included."""
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
    return metadata


@dataclass
class _Prices:
    """Karma for a run of levels, of one skill or of a whole group."""

    metadata: dict[str, dict[str, Any]]
    group_members: dict[str, list[str]]
    active_karma_mults: Mapping[str, int] | None
    active_karma_rules: Sequence[Mapping[str, Any]] | None
    group_karma_mults: Mapping[str, int] | None
    group_karma_rules: Sequence[Mapping[str, Any]] | None

    def active(self, key: str, low: int, high: int) -> int:
        rules = current_rules()
        return skill_levels_karma_cost(
            {key: high},
            {key: high - low},
            {key: self.metadata[key].get("category") or ""},
            per_rating=rules.karma_active_skill,
            first_level=rules.karma_new_active_skill,
            karma_mults=self.active_karma_mults,
            flat_rules=self.active_karma_rules,
        )

    def group(self, group: str, low: int, high: int) -> int:
        categories = {self.metadata[key].get("category") or "" for key in self.group_members[group]}
        category = next(iter(categories)) if len(categories) == 1 else ""
        return skill_levels_karma_cost(
            {group: high},
            {group: high - low},
            {group: category},
            per_rating=current_rules().karma_skill_group,
            first_level=group_first_level(low, high),
            karma_mults=self.group_karma_mults,
            flat_rules=self.group_karma_rules,
        )


def _buy_groups(
    free: LifeSkillResolution,
    purchased_groups: Mapping[str, int],
    group_members: dict[str, list[str]],
    prices: _Prices,
    out: LifeSkillPurchases,
) -> dict[str, int]:
    """Price the group purchases that are legal; return the levels bought per group."""
    applied: dict[str, int] = {}
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
        applied[group] = bought
        out.group_totals[group] = requested
        out.group_karma += prices.group(group, base, requested)
    return applied


def _group_compensation(
    free: LifeSkillResolution,
    group_members: dict[str, list[str]],
    applied_groups: dict[str, int],
    prices: _Prices,
    out: LifeSkillPurchases,
) -> int:
    """Chummer's group-karma compensation: levels every member bought one by
    one are priced as the group would have been."""
    total = 0
    for group, members in group_members.items():
        if group in applied_groups or len(members) < 2:
            continue
        # Only levels bought by EVERY member can receive group pricing.
        # Using the first member's floor would refund another's free levels.
        low = max(free.free_active.get(key, 0) for key in members)
        high = min(out.totals.get(key, 0) for key in members)
        if high > low:
            total += prices.group(group, low, high) - sum(prices.active(key, low, high) for key in members)
    return total


def _valid_count(value: int) -> bool:
    return type(value) is int and 0 <= value <= 10**12
