"""The Black Market Pipeline quality: which category and contact it was
taken for, and which rows the buyer marked for its 10% off."""

from __future__ import annotations

from ...models import CharacterState
from ..constants import quality_contact_extra_key
from .context import Ctx


def discounted_ids(state: CharacterState) -> set[str]:
    """Ids of what the buyer took the Black Market Pipeline's 10% off."""
    out: set[str] = set()
    for rows in (
        state.gear,
        state.commlinks,
        state.cyberdecks,
        state.rccs,
        state.optics,
        state.sensors,
        state.programs,
        state.apps,
        state.weapons,
        state.armor,
        state.vehicles,
        state.drones,
        state.cyberware,
        state.bioware,
    ):
        out |= {row.id for row in rows or [] if getattr(row, "discounted", False)}
    return out


def pick_black_market(ctx: Ctx) -> None:
    """Set `ctx.bmp_category` / `bmp_contact_id` / `bmp_active` from the
    quality's picks, warning about the half that is missing."""
    ctx.bmp_category = ""
    ctx.bmp_contact_id = ""
    ctx.bmp_active = False
    if ctx.effects.get("black_market_discount"):
        for q in ctx.qualities:
            if not any(node.get("tag") == "blackmarketdiscount" for node in (q.get("bonus") or [])):
                continue
            ctx.bmp_category = str((ctx.state.quality_extras or {}).get(q["id"]) or "").strip()
            ctx.bmp_contact_id = str(
                (ctx.state.quality_extras or {}).get(quality_contact_extra_key(q["id"])) or ""
            ).strip()
            contact_ids = {str(getattr(c, "id", "") or "") for c in (ctx.state.contacts or [])}
            if not ctx.bmp_category:
                ctx.warn("engine.gear.bmpCategory")
            if not ctx.bmp_contact_id:
                ctx.warn("engine.gear.bmpContact")
            elif ctx.bmp_contact_id not in contact_ids:
                ctx.warn("engine.gear.bmpContactMissing")
                ctx.bmp_contact_id = ""
            ctx.bmp_active = bool(ctx.bmp_category and ctx.bmp_contact_id)
            break
