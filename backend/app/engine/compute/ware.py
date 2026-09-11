"""Phase 3 — ware: resolve cyber/bioware, quality sides, vehicle-hosted
essence and the chargen ware-attribute cap."""

from __future__ import annotations

from typing import Any

from ...improvements.effect_rows import GrantWareRow
from ...models import CyberwareInstall
from ..limits import (
    _check_ware_attribute_cap,
    _finalize_avail_tree,
    _ware_attribute_aug,
    _ware_attribute_bonuses,
)
from ..lookups import _quality_by_id, _quality_by_name, _ware_by_name
from ..qualities import resolve_quality_sides
from ..skills import ware_accuracy_picks
from ..ware import (
    _vehicle_hosted_ware_ids,
    _vehicle_mod_hosts,
    _zero_vehicle_hosted_essence,
    check_ware_targets,
    has_adapsin,
    resolve_ware,
)
from ..ware.pairs import apply_wireless_pairs, pair_bonus_sources
from .context import Ctx


def _granted_ware_installs(grants: list[GrantWareRow], kind: str) -> tuple[list[CyberwareInstall], dict[str, str]]:
    """``<addware>`` grants for one kind of ware, as installs.

    Like a quality's gear, they stay out of the character: the quality is what
    carries them, so removing it takes the implant — and its Essence — with it,
    and the ware tab has nothing of its own to delete.
    """
    installs: list[CyberwareInstall] = []
    sources: dict[str, str] = {}
    for index, grant in enumerate(grants):
        if str(grant.get("kind") or "cyberware").lower() != kind:
            continue
        spec = _ware_by_name(kind, str(grant.get("name") or ""))
        if not spec:
            continue
        install_id = f"granted:{index}"
        sources[install_id] = str(grant.get("source") or "")
        installs.append(
            CyberwareInstall(
                id=install_id,
                ware_id=str(spec["id"]),
                grade=str(grant.get("grade") or spec.get("forcegrade") or "Standard"),
            )
        )
    return installs, sources


def _mark_granted(rows: list[dict[str, Any]], sources: dict[str, str]) -> None:
    for row in rows:
        row["granted_by"] = sources.get(str(row.get("id") or ""), "")


def ware(ctx: Ctx) -> None:
    vehicle_hosts = set(_vehicle_mod_hosts(ctx.state))
    granted_bio, bio_sources = _granted_ware_installs(ctx.granted_ware, "bioware")
    granted_cyber, cyber_sources = _granted_ware_installs(ctx.granted_ware, "cyberware")
    # Bioware first: Adapsin lives there and changes what a cyberware grade
    # costs in Essence, so cyberware cannot be resolved until we know.
    ctx.bio_installed = resolve_ware("bioware", [*ctx.state.bioware, *granted_bio], ctx.attrs_spec)
    ctx.adapsin = has_adapsin(ctx.bio_installed)
    ctx.cyber_installed = resolve_ware(
        "cyberware", [*ctx.state.cyberware, *granted_cyber], ctx.attrs_spec, adapsin=ctx.adapsin
    )
    _mark_granted(ctx.bio_installed, bio_sources)
    _mark_granted(ctx.cyber_installed, cyber_sources)
    resolve_quality_sides(ctx.qualities, ctx.state, ctx.cyber_installed, ctx.bio_installed, ctx.errors)
    ctx.warnings.extend(check_ware_targets("cyberware", ctx.state.cyberware, ctx.cyber_installed))
    ctx.warnings.extend(check_ware_targets("bioware", ctx.state.bioware, ctx.bio_installed))
    _finalize_avail_tree(ctx.cyber_installed, grade_kind="cyberware")
    _finalize_avail_tree(ctx.bio_installed, grade_kind="bioware")
    _zero_vehicle_hosted_essence(ctx.cyber_installed, vehicle_hosts)
    ctx.installed = ctx.cyber_installed + ctx.bio_installed
    hosted_ids = _vehicle_hosted_ware_ids(ctx.cyber_installed, vehicle_hosts)
    ctx.hosted_ware_ids = set(hosted_ids)
    apply_wireless_pairs(
        [
            *(("cyberware", item) for item in ctx.cyber_installed if item.get("id") not in hosted_ids),
            *(("bioware", item) for item in ctx.bio_installed),
        ]
    )
    owned_qualities = {q["id"] for q in ctx.qualities}
    for item in ctx.installed:
        if item.get("id") in hosted_ids:
            continue
        ctx.sources.append((item["name"], item.get("bonus") or []))
        # `<disablequality>`: the ware does the quality's job, so the quality
        # stops working (Wired Reflexes over Lightning Reflexes, RF p.148).
        for node in item.get("bonus") or []:
            if node.get("tag") != "disablequality":
                continue
            ref = str(node.get("value") or "").strip()
            target = _quality_by_id(ref) or _quality_by_name(ref)
            if target and target["id"] in owned_qualities:
                ctx.disabled_qualities.setdefault(target["id"], str(item["name"]))
    # What a pair adds on top of the two halves (two lower limbs: +1 box).
    picks = ctx.state.skill_picks or {}
    optimized = {
        inst_id: str(picks.get(key) or "")
        for key, _name, _kind, inst_id, _node in ware_accuracy_picks(ctx.state, hosted_ids)
    }
    ctx.sources.extend(
        pair_bonus_sources(
            [
                *(("cyberware", item) for item in ctx.cyber_installed if item.get("id") not in hosted_ids),
                *(("bioware", item) for item in ctx.bio_installed),
            ],
            optimized,
        )
    )
    own_ware = [item for item in ctx.installed if item.get("id") not in hosted_ids]
    ctx.ware_attr_bonus = _ware_attribute_bonuses(own_ware)
    if not ctx.career:
        _check_ware_attribute_cap(ctx.ware_attr_bonus, ctx.errors, _ware_attribute_aug(own_ware))
