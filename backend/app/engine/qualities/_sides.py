"""Quality-level `<selectside>`: which limb a quality claims.

Crystal Limb and its kind pick a side the way cyberware does, and they compete
for the same slot — a left arm already claimed by an implant cannot also be the
quality's.
"""

from __future__ import annotations

from typing import Any

from ...models import CharacterState
from ...notices import Notice, notice, term, ui
from ..constants import _normalize_side, slot_phrase
from ._picks import _quality_has_selectside, _quality_limb_slot


def resolve_quality_sides(
    qualities: list[dict[str, Any]],
    state: CharacterState,
    cyber_installed: list[dict[str, Any]],
    bio_installed: list[dict[str, Any]],
    errors: list[Notice],
) -> dict[str, str]:
    """Validate quality selectside extras; return quality_id → Left/Right."""
    chosen: dict[str, str] = {}
    occupied: dict[tuple[str, str], str] = {}
    for item in list(cyber_installed) + list(bio_installed):
        if item.get("parent_id") or not item.get("selectside"):
            continue
        side = _normalize_side(str(item.get("side") or ""))
        slot = str(item.get("limbslot") or "").lower()
        if side and slot:
            occupied[(slot, side)] = str(item.get("name") or "")

    extras = state.quality_extras or {}
    for spec in qualities:
        if not _quality_has_selectside(spec):
            continue
        raw = str(extras.get(spec["id"]) or "").strip()
        side = _normalize_side(raw)
        if not side:
            if raw:
                errors.append(notice("engine.qualities.sideInvalid", name=term(str(spec["name"]))))
            continue
        chosen[spec["id"]] = side
        limb_slot = _quality_limb_slot(spec)
        if not limb_slot:
            continue
        key = (limb_slot, side)
        if key in occupied:
            errors.append(
                notice(
                    "engine.qualities.sideDuplicate",
                    name=term(str(spec["name"])),
                    other=term(occupied[key]) if occupied[key] else ui("engine.term.ware"),
                    side=ui(f"engine.side.{side}"),
                    slot=slot_phrase(limb_slot),
                )
            )
            continue
        occupied[key] = spec["name"]
    # Normalize valid sides back into extras for persistence.
    if chosen:
        next_extras = dict(state.quality_extras or {})
        for qid, side in chosen.items():
            next_extras[qid] = side
        state.quality_extras = next_extras
    return chosen
