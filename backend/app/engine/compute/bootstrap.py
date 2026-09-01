"""Phase 1 — bootstrap: build method, career flags, reward totals, skill
caps, metatype spec and cyber/bioware sanity checks."""

from __future__ import annotations

from ...models import CharacterState, RewardEntry
from ..constants import BUILD_METHOD_KARMA, CAREER_SKILL_GROUP_MAX, CAREER_SKILL_MAX
from ..lookups import find_metatype
from ..priority import normalize_build_method, validate_priorities
from ..ware import (
    _drop_invalid_vehicle_ware,
    _installed_ware_names,
    _required_warnings,
    _side_conflicts,
    ensure_subsystems,
)
from .context import Ctx


def sync_reward_totals(state: CharacterState) -> None:
    """Keep earned pools aligned with reward_log when the ledger has rows."""
    log = list(getattr(state, "reward_log", None) or [])
    cleaned: list[RewardEntry] = []
    for raw in log:
        if isinstance(raw, RewardEntry):
            entry = raw
        elif isinstance(raw, dict):
            entry = RewardEntry.model_validate(raw)
        else:
            continue
        entry.karma = max(0, int(entry.karma or 0))
        entry.nuyen = max(0, int(entry.nuyen or 0))
        entry.label = str(entry.label or "").strip() or "報酬"
        cleaned.append(entry)
    state.reward_log = cleaned
    if cleaned:
        state.karma_earned = sum(int(row.karma or 0) for row in cleaned)
        state.nuyen_earned = sum(int(row.nuyen or 0) for row in cleaned)


def bootstrap(ctx: Ctx) -> None:
    ctx.state.build_method = normalize_build_method(getattr(ctx.state, "build_method", None))
    ctx.is_karma = ctx.state.build_method == BUILD_METHOD_KARMA
    ctx.career = bool(getattr(ctx.state, "career", False))
    ctx.state.career = ctx.career
    ctx.state.street_cred = max(0, int(getattr(ctx.state, "street_cred", 0) or 0))
    ctx.state.notoriety_bonus = int(getattr(ctx.state, "notoriety_bonus", 0) or 0)
    sync_reward_totals(ctx.state)
    ctx.state.karma_earned = max(0, int(getattr(ctx.state, "karma_earned", 0) or 0))
    ctx.state.nuyen_earned = max(0, int(getattr(ctx.state, "nuyen_earned", 0) or 0))
    ctx.skill_rating_cap = CAREER_SKILL_MAX if ctx.career else 6
    ctx.skill_group_cap = CAREER_SKILL_GROUP_MAX if ctx.career else 6
    ctx.errors = validate_priorities(ctx.state.priorities, ctx.state.build_method)
    ctx.meta = find_metatype(ctx.state.metatype, ctx.state.metavariant)
    ctx.attrs_spec = ctx.meta["attributes"]
    ctx.warnings = _drop_invalid_vehicle_ware(ctx.state)
    ensure_subsystems(ctx.state)
    ctx.errors.extend(_side_conflicts("cyberware", ctx.state.cyberware))
    ctx.errors.extend(_side_conflicts("bioware", ctx.state.bioware))
    installed_names = {
        "cyberware": _installed_ware_names("cyberware", ctx.state.cyberware),
        "bioware": _installed_ware_names("bioware", ctx.state.bioware),
    }
    ctx.warnings.extend(
        _required_warnings("cyberware", ctx.state.cyberware, installed_names, ctx.state.metatype, ctx.state.metavariant)
    )
    ctx.warnings.extend(
        _required_warnings("bioware", ctx.state.bioware, installed_names, ctx.state.metatype, ctx.state.metavariant)
    )
