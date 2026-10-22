"""Phases 2 + 4 — quality gather (talent, qualities, mentor) and the
effects/binder pass (collect_effects, every ``bind_*``, attribute selects,
Cyberseeker) plus the special-attribute start / enabled-tab seed."""

from __future__ import annotations

from typing import Any

from ...improvements import ATTR_ALIASES, EffectsDict, collect_effects
from ...improvements._common import substitute_rating
from ...models import CharacterState
from ...notices import Notice, notice, term
from ..constants import MENTOR_SPIRIT_ID, PARAGON_ID, quality_attribute_extra_key, quality_optional_power_extra_key
from ..contacts import apply_excon_ware_ban
from ..critter_powers import bought_power_sources
from ..gear import bind_weapon_category_dv, bind_weapon_skill_accuracy
from ..karma import _skill_groups_for_category
from ..magic import (
    apply_granted_spells,
    bind_spell_category_drain_damage,
    bind_spell_spirit_limits,
    resolve_mentor,
)
from ..priority import resolve_talent_for_method, talent_allowed, talent_special
from ..qualities import (
    bind_action_dice_pools,
    bind_select_powers,
    gather_qualities,
    resolve_quality_sides,
)
from ..skills import bind_ware_skill_accuracy
from ..special_attributes import special_attribute_floors
from ..ware import _clamp_ware_grades, apply_cyberseeker, redliner_incompat_warnings
from ..ware.sides import _side_conflicts
from .context import Ctx


def resolve_attribute_selects(
    state: CharacterState,
    effects: EffectsDict,
    qualities: list[dict[str, Any]],
) -> tuple[dict[str, int], list[Notice]]:
    warnings: list[Notice] = []
    bonus: dict[str, int] = {}
    extras = state.quality_extras or {}
    by_name = {q["name"]: q for q in qualities}
    for sel in effects.get("attribute_selects") or []:
        source = str(sel.get("source") or "")
        spec = by_name.get(source)
        if not spec:
            continue
        picked = ATTR_ALIASES.get(
            str(extras.get(quality_attribute_extra_key(spec["id"], sel["index"])) or "").strip().upper()
        )
        exclude = {str(item) for item in (sel.get("exclude") or [])}
        max_bonus = int(sel.get("max") or 0)
        allowed = set(sel.get("options") or [])
        if not picked:
            warnings.append(notice("engine.attrs.pickAttribute", source=term(source)))
            continue
        if picked in exclude or picked == "ESS" or (allowed and picked not in allowed):
            warnings.append(notice("engine.attrs.attributeNotAllowed", source=term(source), picked=picked))
            continue
        if max_bonus:
            bonus[picked] = int(bonus.get(picked) or 0) + max_bonus
        effects["attribute_bonus"][picked] = int(effects["attribute_bonus"].get(picked) or 0) + int(sel.get("val") or 0)
    return bonus, warnings


def _critter_power_sources(q: dict[str, Any], extras: dict[str, str]) -> list[tuple[str, list[dict[str, Any]]]]:
    """What the powers a quality grants do (`critter_power_effects`, built at
    load): each fixed one, and the one optional power if it was picked.

    Chummer makes each power at the rating the quality names and runs its
    bonus at that rating, so a Dracoform's Hardened Armor 2 is 2 points of
    armor; an optional power is made at rating 0.
    """
    picked = extras.get(quality_optional_power_extra_key(q["id"])) or ""
    out = []
    for power in q.get("critter_power_effects") or []:
        if power["optional"] and power["label"] != picked:
            continue
        rating = int(power["rating"] or 0)
        nodes = substitute_rating(list(power["bonus"]), rating) if power["rating"] else list(power["bonus"])
        out.append((power["label"], nodes))
    return out


def _without_removed(ctx: Ctx) -> list[dict[str, Any]]:
    """The metatype's grants less the `removable` ones taken off at chargen.

    Only a `removable="True"` grant can go (Chummer refuses the rest), and a
    pick left over from another metatype names nothing here, so the list is
    trimmed to what this metatype still offers.
    """
    removed = set(ctx.state.removed_innate_qualities)
    kept: list[dict[str, Any]] = []
    ctx.removed_innate = []
    for grant in ctx.meta.get("quality_grants") or []:
        if grant.get("removable") and grant.get("id") in removed:
            ctx.removed_innate.append(grant)
        else:
            kept.append(grant)
    ctx.state.removed_innate_qualities = [str(grant["id"]) for grant in ctx.removed_innate]
    return kept


def gather(ctx: Ctx) -> None:
    ctx.talent = resolve_talent_for_method(
        ctx.state.priorities.Talent, ctx.state.talent, ctx.state.build_method, ctx.state.metatype
    )
    ctx.state.talent = ctx.talent["name"]
    if not talent_allowed(ctx.talent, ctx.state.metatype) and not (ctx.is_karma and ctx.talent["name"] == "Mundane"):
        # A Karma build has no Talent priority: Mundane there only means no
        # talent was bought, which an A.I. is free to do.
        ctx.err(
            "engine.priority.talentNotAllowed",
            talent=term(str(ctx.talent.get("label") or ctx.talent["name"])),
            metatype=term(ctx.state.metatype),
        )
    ctx.sources = [(ctx.meta["name"], ctx.meta.get("bonus") or [])]
    innate_grants = _without_removed(ctx)
    quality_grants = [*innate_grants, *(ctx.life.get("qualities") or [])]
    power_grants = ctx.meta.get("power_grants") or []
    for grant in quality_grants + power_grants:
        if grant.get("unresolved"):
            ctx.warn("engine.meta.unknownGrant", name=term(grant["name"]), metatype=term(ctx.meta["name"]))
    ctx.sources.extend((p["name"], p.get("bonus") or []) for p in power_grants if not p.get("unresolved"))
    ctx.qualities, ctx.free_quality_ids, dropped_qualities = gather_qualities(ctx.state, ctx.talent, quality_grants)
    for name in dropped_qualities:
        ctx.warn("engine.qualities.droppedIncompatible", name=term(name))
    # The powers a quality grants count here too: Regeneration is what bars an
    # Infected from cyberware grades (RF p.134), not the quality around it.
    quality_grade_effects = collect_effects(
        [(q["name"], q.get("bonus") or []) for q in ctx.qualities]
        + [src for q in ctx.qualities for src in _critter_power_sources(q, ctx.state.quality_extras)]
    )
    ctx.granted_ware = list(quality_grade_effects["grant_ware"])
    # `<replaceattributes>`: an Infected character stops being their metatype
    # where these attributes are concerned (RF p.136), and a Quadriplegic's
    # AGI/REA/STR are gone (BTB p.139). The whole pipeline reads the ranges off
    # `attrs_spec`, so replacing them here is enough — on a copy, because the
    # metatype's own dict belongs to the cached catalog.
    replacements = quality_grade_effects["attribute_replacements"]
    if replacements:
        ctx.attrs_spec = {
            key: {**spec, **{k: v for k, v in replacements[key].items() if k != "source"}}
            if key in replacements
            else spec
            for key, spec in ctx.attrs_spec.items()
        }
        ctx.attr_replaced_by = sorted({str(row["source"]) for row in replacements.values() if row.get("source")})
    # The Critter Powers tab: open, and to which categories, is the qualities'
    # say; what was bought there joins the effects pass with the rest.
    ctx.critter_power_categories = set(quality_grade_effects["critter_power_categories"])
    ctx.sources.extend(bought_power_sources(ctx.state, set(quality_grade_effects["enabled_tabs"])))
    disabled_cyber_grades = set(quality_grade_effects.get("disabled_cyberware_grades") or [])
    disabled_bio_grades = set(quality_grade_effects.get("disabled_bioware_grades") or [])
    ctx.warnings.extend(_clamp_ware_grades("cyberware", ctx.state.cyberware, disabled_cyber_grades))
    ctx.warnings.extend(_clamp_ware_grades("bioware", ctx.state.bioware, disabled_bio_grades))
    first_levels: set[str] = set()
    for q in ctx.qualities:
        ctx.sources.append((q["name"], q.get("bonus") or []))
        # a leveled quality is listed once per level; `<firstlevelbonus>`
        # rides the first one only (Chummer `Quality.FirstLevelBonus`)
        if q.get("firstlevelbonus") and q["id"] not in first_levels:
            first_levels.add(q["id"])
            ctx.sources.append((q["name"], q["firstlevelbonus"]))
        ctx.sources.extend(_critter_power_sources(q, ctx.state.quality_extras))
    ctx.needs_mentor = any(q["id"] == MENTOR_SPIRIT_ID for q in ctx.qualities)
    # Paragon is Mentor Spirit for a technomancer and shares `mentor_id`; the
    # two qualities gate on opposite talents, so at most one is ever set.
    ctx.needs_paragon = any(q["id"] == PARAGON_ID for q in ctx.qualities)
    ctx.mentor = resolve_mentor(
        ctx.state,
        ctx.talent["name"],
        ctx.needs_mentor or ctx.needs_paragon,
        ctx.data["skills"],
        paragon=ctx.needs_paragon,
    )
    ctx.warnings.extend(ctx.mentor["warnings"])
    ctx.errors.extend(ctx.mentor["errors"])
    ctx.sources.extend(ctx.mentor["bonus_sources"])


def effects_and_binders(ctx: Ctx) -> None:
    if ctx.disabled_qualities:
        off = {q["name"] for q in ctx.qualities if q["id"] in ctx.disabled_qualities}
        quality_names = {q["name"] for q in ctx.qualities}
        ctx.sources = [(name, nodes) for name, nodes in ctx.sources if not (name in off and name in quality_names)]
    ctx.effects = collect_effects(ctx.sources)
    extra_limbs = ctx.effects["extra_limbs"]
    ctx.errors.extend(_side_conflicts("cyberware", ctx.state.cyberware, extra_limbs))
    ctx.errors.extend(_side_conflicts("bioware", ctx.state.bioware, extra_limbs))
    resolve_quality_sides(ctx.qualities, ctx.state, ctx.cyber_installed, ctx.bio_installed, ctx.errors, extra_limbs)
    apply_excon_ware_ban(ctx.cyber_installed + ctx.bio_installed, bool(ctx.effects.get("excon")), ctx.errors)
    bind_action_dice_pools(ctx.effects, ctx.qualities, ctx.state)
    bind_spell_spirit_limits(ctx.effects, ctx.qualities, ctx.state, ctx.errors)
    bind_spell_category_drain_damage(ctx.effects, ctx.qualities, ctx.state)
    bind_weapon_category_dv(ctx.effects, ctx.qualities, ctx.state, ctx.warnings)
    bind_weapon_skill_accuracy(ctx.effects, ctx.qualities, ctx.state, ctx.warnings, ctx.data["skills"])
    bind_ware_skill_accuracy(ctx.effects, ctx.state, ctx.data["skills"], ctx.hosted_ware_ids | ctx.inactive_ware_ids)
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
    ctx.limb_quality = apply_cyberseeker(
        ctx.cyber_installed, seeker_targets, ctx.attrs_spec, ctx.state.options, ctx.effects["extra_limbs"]
    )
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
    ctx.special_floors = special_attribute_floors(ctx.meta, ctx.talent, is_karma=ctx.is_karma)
    ctx.enabled = set(ctx.effects["enabled_tabs"])
    ctx.enabled.update(ctx.special_floors)
