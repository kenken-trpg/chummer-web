"""Phases 7 + 8 + 11 — the awakened/emerged pipeline: initiation,
submersion, foci, adept powers and enhancements (``awakened``); then spells,
spirits, complex forms and sprites once ``ctx.total`` is settled (``spells``)."""

from __future__ import annotations

from ...improvements import apply_bonus_nodes
from ..constants import (
    COMPLEX_FORM_TALENTS,
    FOCUS_TALENTS,
    MAG_TALENTS,
    RES_TALENTS,
    SPELL_TALENTS,
    SPIRIT_TALENTS,
    SPRITE_TALENTS,
)
from ..limits import _finalize_avail_tree
from ..lookups import _tradition_by_id
from ..magic import (
    apply_focus_limits,
    apply_free_metamagics,
    apply_tradition_bonuses,
    bind_extra_spirits,
    resolve_adept_powers,
    resolve_enhancements,
    resolve_foci,
    resolve_initiation,
    resolve_qi_foci,
    resolve_spells,
    resolve_spirits,
    resolve_submersion,
    spell_cast_info,
)
from ..qualities import free_powers_from_grants
from ..resonance import apply_granted_echoes, resolve_complex_forms, resolve_sprites
from .context import Ctx


def awakened(ctx: Ctx) -> None:
    ctx.quality_names = {q["name"] for q in ctx.qualities}
    ctx.initiation = resolve_initiation(
        ctx.state,
        ctx.talent["name"],
        int(ctx.ratings.get("MAG") or 0),
        ctx.quality_names,
        ctx.errors,
    )
    apply_free_metamagics(ctx.effects, ctx.initiation, ctx.talent["name"], ctx.warnings)
    ctx.warnings.extend(ctx.initiation["warnings"])
    for source, nodes in ctx.initiation["bonus_sources"]:
        apply_bonus_nodes(nodes, ctx.effects, source)
    if ctx.talent["name"] in MAG_TALENTS:
        ctx.enabled.add("initiation")
    ctx.submersion = resolve_submersion(
        ctx.state,
        ctx.talent["name"],
        int(ctx.ratings.get("RES") or 0),
        ctx.quality_names,
        ctx.errors,
    )
    apply_granted_echoes(ctx.effects, ctx.submersion, ctx.qualities, ctx.warnings)
    ctx.warnings.extend(ctx.submersion["warnings"])
    for source, nodes in ctx.submersion["bonus_sources"]:
        apply_bonus_nodes(nodes, ctx.effects, source)
    if ctx.talent["name"] in RES_TALENTS:
        ctx.enabled.add("submersion")
    ctx.qi = resolve_qi_foci(
        ctx.state,
        ctx.talent["name"],
        int(ctx.ratings.get("MAG") or 0),
        ctx.data["skills"],
        list(ctx.effects.get("focus_binding") or []),
    )
    ctx.warnings.extend(ctx.qi["warnings"])
    ctx.errors.extend(ctx.qi["errors"])
    ctx.foci = resolve_foci(
        ctx.state,
        ctx.talent["name"],
        int(ctx.ratings.get("MAG") or 0),
        list(ctx.effects.get("focus_binding") or []),
    )
    ctx.warnings.extend(ctx.foci["warnings"])
    _finalize_avail_tree(list(ctx.foci.get("public") or []), rating_key="force")
    for source, nodes in ctx.foci["bonus_sources"]:
        apply_bonus_nodes(nodes, ctx.effects, source)
    ctx.focus_limits = apply_focus_limits(
        int(ctx.ratings.get("MAG") or 0),
        list(ctx.qi.get("public") or []),
        list(ctx.foci.get("public") or []),
        ctx.errors,
    )
    apply_tradition_bonuses(ctx.effects, _tradition_by_id(ctx.state.tradition_id))
    granted_powers = free_powers_from_grants(ctx.effects, ctx.warnings)
    ctx.adept = resolve_adept_powers(
        ctx.state,
        ctx.talent["name"],
        int(ctx.ratings.get("MAG") or 0),
        ctx.data["skills"],
        ctx.quality_names,
        bool(ctx.effects.get("magicians_way")),
        list(ctx.mentor.get("free_powers") or []) + list(ctx.qi.get("free_powers") or []) + granted_powers,
        int(ctx.ratings.get("WIL") or 1),
        int(ctx.ratings.get("INT") or 1),
    )
    ctx.warnings.extend(ctx.adept["warnings"])
    ctx.errors.extend(ctx.adept["errors"])
    ctx.state.mystic_pp = int(ctx.adept["mystic_pp"])
    ctx.enhancements = resolve_enhancements(
        ctx.state, ctx.talent["name"], ctx.quality_names, set(ctx.adept.get("power_names") or [])
    )
    ctx.warnings.extend(ctx.enhancements["warnings"])
    ctx.effects["enabled_tabs"] = set(ctx.effects["enabled_tabs"])
    for source, nodes in ctx.adept["bonus_sources"] + ctx.enhancements["bonus_sources"]:
        apply_bonus_nodes(nodes, ctx.effects, source)
    ctx.attr_totals = {
        key: int(ctx.ratings.get(key) or 0) + int((ctx.effects.get("attribute_bonus") or {}).get(key, 0))
        for key in ctx.ratings
    }


def spells(ctx: Ctx) -> None:
    owned_magic_names = set(ctx.initiation.get("art_names") or set()) | set(
        ctx.initiation.get("metamagic_names") or set()
    )
    ctx.magic = resolve_spells(
        ctx.state, ctx.talent, int(ctx.total.get("MAG") or 0), ctx.total, owned_magic_names, ctx.effects
    )
    ctx.warnings.extend(ctx.magic["warnings"])
    spell_focus = {mod["name"]: int(mod.get("bonus") or 0) for mod in (ctx.effects.get("spell_category_mods") or [])}
    for item in ctx.magic.get("public") or []:
        bonus = int(spell_focus.get(item.get("category") or "", 0))
        if bonus:
            item["focus_bonus"] = bonus
    bind_extra_spirits(ctx.effects, ctx.qualities, ctx.state, ctx.warnings, ctx.data["skills"])
    ctx.spirits = resolve_spirits(
        ctx.state,
        ctx.talent["name"],
        int(ctx.total.get("MAG") or 0),
        _tradition_by_id(ctx.state.tradition_id),
        limit_spirits=list(ctx.effects.get("limit_spirit_categories") or []),
        extra_spirits=list(ctx.effects.get("extra_spirits") or []),
    )
    ctx.warnings.extend(ctx.spirits["warnings"])
    if ctx.talent["name"] in SPELL_TALENTS or (ctx.effects.get("allow_spell_ranges") or []):
        ctx.enabled.add("spells")
    if ctx.talent["name"] in SPIRIT_TALENTS:
        ctx.enabled.add("spirits")
    ctx.resonance = resolve_complex_forms(
        ctx.state,
        ctx.talent["name"],
        int(ctx.total.get("RES") or 0),
        ctx.total,
        ctx.quality_names,
        ctx.effects,
    )
    ctx.warnings.extend(ctx.resonance["warnings"])
    ctx.techno_sprites = resolve_sprites(
        ctx.state,
        ctx.talent["name"],
        int(ctx.total.get("RES") or 0),
        ctx.resonance.get("stream"),
    )
    ctx.warnings.extend(ctx.techno_sprites["warnings"])
    ctx.errors.extend(ctx.techno_sprites["errors"])
    if ctx.talent["name"] in COMPLEX_FORM_TALENTS:
        ctx.enabled.add("complexforms")
    if ctx.talent["name"] in SPRITE_TALENTS:
        ctx.enabled.add("sprites")
    if ctx.talent["name"] in FOCUS_TALENTS:
        ctx.enabled.add("foci")
    for item in ctx.adept.get("public") or []:
        extra = item.get("extra")
        if item.get("select") != "spell" or not extra:
            continue
        force = (item.get("spell") or {}).get("force")
        item["spell"] = spell_cast_info(
            extra,
            force,
            int(ctx.total.get("MAG") or 0),
            int(ctx.magic["resist"]),
            str(ctx.magic["resist_attrs"]),
            effects=ctx.effects,
        )
