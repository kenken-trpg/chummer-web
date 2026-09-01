"""Phase 3 — ware: resolve cyber/bioware, quality sides, vehicle-hosted
essence and the chargen ware-attribute cap."""

from __future__ import annotations

from ..limits import _check_ware_attribute_cap, _finalize_avail_tree, _ware_attribute_bonuses
from ..qualities import resolve_quality_sides
from ..ware import (
    _vehicle_hosted_ware_ids,
    _vehicle_mod_hosts,
    _zero_vehicle_hosted_essence,
    resolve_ware,
)
from .context import Ctx


def ware(ctx: Ctx) -> None:
    vehicle_hosts = set(_vehicle_mod_hosts(ctx.state))
    ctx.cyber_installed = resolve_ware("cyberware", ctx.state.cyberware, ctx.attrs_spec)
    ctx.bio_installed = resolve_ware("bioware", ctx.state.bioware, ctx.attrs_spec)
    resolve_quality_sides(ctx.qualities, ctx.state, ctx.cyber_installed, ctx.bio_installed, ctx.errors)
    _finalize_avail_tree(ctx.cyber_installed, grade_kind="cyberware")
    _finalize_avail_tree(ctx.bio_installed, grade_kind="bioware")
    _zero_vehicle_hosted_essence(ctx.cyber_installed, vehicle_hosts)
    ctx.installed = ctx.cyber_installed + ctx.bio_installed
    hosted_ids = _vehicle_hosted_ware_ids(ctx.cyber_installed, vehicle_hosts)
    for item in ctx.installed:
        if item.get("id") in hosted_ids:
            continue
        ctx.sources.append((item["name"], item.get("bonus") or []))
    ctx.ware_attr_bonus = _ware_attribute_bonuses([item for item in ctx.installed if item.get("id") not in hosted_ids])
    if not ctx.career:
        _check_ware_attribute_cap(ctx.ware_attr_bonus, ctx.errors)
