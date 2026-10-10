"""Left/Right side assignment for paired cyber/bioware.

``ensure_sides`` fills in each ``selectside`` install's side (inheriting the
parent's for children, auto-picking the first free side otherwise);
``_side_conflicts`` reports installs exceeding the body's per-side capacity.
Additional limbs share Left/Right and remain distinct by install ID.

Imports only ``_ware_by_id`` (``.lookups``), ``_normalize_side`` /
``_SLOT_JA`` / ``_SIDE_JA`` (``.constants``) and ``CyberwareInstall``
(models) — never back into ``app.engine``.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from ...models import CyberwareInstall
from ...notices import Notice, notice, ui
from ..constants import _normalize_side, slot_phrase
from ..lookups import _ware_by_id
from .limbs import _limb_slot_count, body_limb_slots, side_slot_capacity


def _occupied_sides(
    items: list[CyberwareInstall],
    kind: str,
    slot: str,
    skip_id: str | None = None,
    extra_limbs: dict[str, int] | None = None,
) -> Counter[str]:
    used: Counter[str] = Counter()
    for inst in items:
        if inst.id == skip_id or inst.parent_id:
            continue
        ware = _ware_by_id(kind, inst.ware_id)
        if not ware or not ware.get("selectside"):
            continue
        if (ware.get("limbslot") or ware.get("id") or "").lower() != slot:
            continue
        side = _normalize_side(inst.side)
        if side:
            used[side] += _limb_slot_count(ware, body_limb_slots(extra_limbs))
    return used


def _next_free_side(
    items: list[CyberwareInstall],
    kind: str,
    ware: dict[str, Any],
    skip_id: str | None = None,
    extra_limbs: dict[str, int] | None = None,
) -> str:
    slot = (ware.get("limbslot") or ware.get("id") or "").lower()
    used = _occupied_sides(items, kind, slot, skip_id=skip_id, extra_limbs=extra_limbs)
    capacity = side_slot_capacity(slot, extra_limbs)
    needed = _limb_slot_count(ware, body_limb_slots(extra_limbs))
    if used["Left"] + needed <= capacity and used["Left"] <= used["Right"]:
        return "Left"
    if used["Right"] + needed <= capacity:
        return "Right"
    return "Left"


def ensure_sides(
    kind: str, items: list[CyberwareInstall], extra_limbs: dict[str, int] | None = None
) -> list[CyberwareInstall]:
    by_id = {inst.id: inst for inst in items}
    for inst in items:
        ware = _ware_by_id(kind, inst.ware_id)
        if not ware:
            continue
        if inst.parent_id:
            continue
        if not ware.get("selectside"):
            inst.side = None
            continue
        inst.side = _normalize_side(inst.side) or _next_free_side(
            items, kind, ware, skip_id=inst.id, extra_limbs=extra_limbs
        )
    # Children may precede their parents in an import or patch. Inherit the
    # highest sided ancestor, including a sided subsystem in an unsided body.
    for inst in items:
        parent = inst
        seen = {inst.id}
        inherited_side = None
        while parent.parent_id and parent.parent_id in by_id and parent.parent_id not in seen:
            parent = by_id[parent.parent_id]
            seen.add(parent.id)
            if parent.side:
                inherited_side = parent.side
        if inherited_side:
            inst.side = inherited_side
    return items


def _side_conflicts(
    kind: str, items: list[CyberwareInstall], extra_limbs: dict[str, int] | None = None
) -> list[Notice]:
    used: Counter[tuple[str, str]] = Counter()
    dups: set[tuple[str, str]] = set()
    for inst in items:
        if inst.parent_id:
            continue
        ware = _ware_by_id(kind, inst.ware_id)
        if not ware or not ware.get("selectside"):
            continue
        side = _normalize_side(inst.side)
        if not side:
            continue
        slot = (ware.get("limbslot") or ware.get("id") or "").lower()
        key = (slot, side)
        used[key] += _limb_slot_count(ware, body_limb_slots(extra_limbs))
        if used[key] > side_slot_capacity(slot, extra_limbs):
            dups.add(key)
    errors: list[Notice] = []
    for slot, side in sorted(dups):
        errors.append(notice("engine.ware.sideDuplicate", side=ui(f"engine.side.{side}"), slot=slot_phrase(slot)))
    return errors
