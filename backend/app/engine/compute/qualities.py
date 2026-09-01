"""Phases 2 + 4 — quality gather (talent, qualities, mentor) and the
effects/binder pass (collect_effects, every ``bind_*``, attribute selects,
Cyberseeker) plus the special-attribute start / enabled-tab seed."""

from __future__ import annotations

from typing import Any

from ...improvements import ATTR_ALIASES, EffectsDict, collect_effects
from ...models import CharacterState
from ..constants import MENTOR_SPIRIT_ID
from ..contacts import apply_excon_ware_ban
from ..gear import bind_weapon_category_dv, bind_weapon_skill_accuracy
from ..karma import _skill_groups_for_category
from ..magic import (
    apply_granted_spells,
    bind_spell_category_drain_damage,
    bind_spell_spirit_limits,
    resolve_mentor,
)
from ..priority import resolve_talent_for_method, talent_special
from ..qualities import (
    bind_action_dice_pools,
    bind_select_powers,
    gather_qualities,
)
from ..ware import _clamp_ware_grades, apply_cyberseeker, redliner_incompat_warnings
from .context import Ctx


def resolve_attribute_selects(
    state: CharacterState,
    effects: EffectsDict,
    qualities: list[dict[str, Any]],
) -> tuple[dict[str, int], list[str]]:
    warnings: list[str] = []
    bonus: dict[str, int] = {}
    extras = state.quality_extras or {}
    by_name = {q["name"]: q for q in qualities}
    for sel in effects.get("attribute_selects") or []:
        source = str(sel.get("source") or "")
        spec = by_name.get(source)
        if not spec:
            continue
        picked = ATTR_ALIASES.get(str(extras.get(spec["id"]) or "").strip().upper())
        exclude = {str(item) for item in (sel.get("exclude") or [])}
        max_bonus = max(1, int(sel.get("max") or 1))
        if not picked:
            warnings.append(f"{source} の能力値を選んでください")
            continue
        if picked in exclude or picked in {"ESS"}:
            warnings.append(f"{source} に {picked} は選べません")
            continue
        bonus[picked] = int(bonus.get(picked) or 0) + max_bonus
    return bonus, warnings


def gather(ctx: Ctx) -> None:
    ctx.talent = resolve_talent_for_method(ctx.state.priorities.Talent, ctx.state.talent, ctx.state.build_method)
    ctx.state.talent = ctx.talent["name"]
    ctx.sources = [(ctx.meta["name"], ctx.meta.get("bonus") or [])]
    ctx.qualities, ctx.free_quality_ids, dropped_qualities = gather_qualities(ctx.state, ctx.talent)
    for name in dropped_qualities:
        ctx.warnings.append(f"{name} は他の資質と両立しないため外しました")
    quality_grade_effects = collect_effects([(q["name"], q.get("bonus") or []) for q in ctx.qualities])
    disabled_cyber_grades = set(quality_grade_effects.get("disabled_cyberware_grades") or [])
    disabled_bio_grades = set(quality_grade_effects.get("disabled_bioware_grades") or [])
    ctx.warnings.extend(_clamp_ware_grades("cyberware", ctx.state.cyberware, disabled_cyber_grades))
    ctx.warnings.extend(_clamp_ware_grades("bioware", ctx.state.bioware, disabled_bio_grades))
    for q in ctx.qualities:
        ctx.sources.append((q["name"], q.get("bonus") or []))
    ctx.needs_mentor = any(q["id"] == MENTOR_SPIRIT_ID for q in ctx.qualities)
    ctx.mentor = resolve_mentor(ctx.state, ctx.talent["name"], ctx.needs_mentor, ctx.data["skills"])
    ctx.warnings.extend(ctx.mentor["warnings"])
    ctx.errors.extend(ctx.mentor["errors"])
    ctx.sources.extend(ctx.mentor["bonus_sources"])


def effects_and_binders(ctx: Ctx) -> None:
    ctx.effects = collect_effects(ctx.sources)
    apply_excon_ware_ban(ctx.cyber_installed + ctx.bio_installed, bool(ctx.effects.get("excon")), ctx.errors)
    bind_action_dice_pools(ctx.effects, ctx.qualities, ctx.state)
    bind_spell_spirit_limits(ctx.effects, ctx.qualities, ctx.state, ctx.errors)
    bind_spell_category_drain_damage(ctx.effects, ctx.qualities, ctx.state)
    bind_weapon_category_dv(ctx.effects, ctx.qualities, ctx.state, ctx.warnings)
    bind_weapon_skill_accuracy(ctx.effects, ctx.qualities, ctx.state, ctx.warnings, ctx.data["skills"])
    apply_granted_spells(ctx.state, ctx.effects, ctx.qualities, ctx.warnings)
    bind_select_powers(
        ctx.effects,
        ctx.qualities,
        ctx.state,
        ctx.warnings,
        str((ctx.mentor.get("public") or {}).get("name") or ""),
    )
    for category in ctx.effects.get("disabled_skill_group_categories") or []:
        for group in _skill_groups_for_category(ctx.data["skills"], str(category)):
            if group not in ctx.effects["disabled_skill_groups"]:
                ctx.effects["disabled_skill_groups"].append(group)
    for q in ctx.qualities:
        if not any(node.get("tag") == "skillgroupdisablechoice" for node in (q.get("bonus") or [])):
            continue
        picked = str((ctx.state.quality_extras or {}).get(q["id"]) or "").strip()
        if picked and picked not in ctx.effects["disabled_skill_groups"]:
            ctx.effects["disabled_skill_groups"].append(picked)
    ctx.attr_max_bonus, attr_select_warnings = resolve_attribute_selects(ctx.state, ctx.effects, ctx.qualities)
    ctx.warnings.extend(attr_select_warnings)
    attr_max_mods = {
        key: int(value) for key, value in (ctx.effects.get("attribute_max_mods") or {}).items() if int(value or 0)
    }
    for key, value in attr_max_mods.items():
        ctx.attr_max_bonus[key] = int(ctx.attr_max_bonus.get(key) or 0) + int(value)
    seeker_targets = ctx.effects.get("cyberseeker") or []
    ctx.limb_quality = apply_cyberseeker(ctx.cyber_installed, seeker_targets, ctx.attrs_spec, ctx.state.options)
    ctx.warnings.extend(redliner_incompat_warnings(ctx.installed, seeker_targets))
    if ctx.limb_quality:
        for key, value in (ctx.limb_quality.get("attribute_bonus") or {}).items():
            if key in {"STR", "AGI"}:
                continue
            ctx.effects["attribute_bonus"][key] = int(ctx.effects["attribute_bonus"].get(key, 0)) + int(value)
        ctx.effects["cm_physical"] += int(ctx.limb_quality.get("cm_physical") or 0)

    ctx.special_key, ctx.talent_start = talent_special(ctx.talent)
    if ctx.is_karma and ctx.special_key:
        ctx.talent_start = 1
    ctx.enabled = set(ctx.effects["enabled_tabs"])
    if ctx.special_key:
        ctx.enabled.add(ctx.special_key)
