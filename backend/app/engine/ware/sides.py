"""Left/Right side assignment for paired cyber/bioware.

``ensure_sides`` fills in each ``selectside`` install's side (inheriting the
parent's for children, auto-picking the first free side otherwise);
``_side_conflicts`` reports duplicate (slot, side) pairs as Japanese error
strings.

Imports only ``_ware_by_id`` (``.lookups``), ``_normalize_side`` /
``_SLOT_JA`` / ``_SIDE_JA`` (``.constants``) and ``CyberwareInstall``
(models) — never back into ``app.engine``.
"""

from __future__ import annotations

from typing import Any

from ...models import CyberwareInstall
from ..constants import _SIDE_JA, _SLOT_JA, _normalize_side
from ..lookups import _ware_by_id


def _occupied_sides(items: list[CyberwareInstall], kind: str, slot: str, skip_id: str | None = None) -> set[str]:
    used: set[str] = set()
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
            used.add(side)
    return used


def _next_free_side(items: list[CyberwareInstall], kind: str, ware: dict[str, Any], skip_id: str | None = None) -> str:
    slot = (ware.get("limbslot") or ware.get("id") or "").lower()
    used = _occupied_sides(items, kind, slot, skip_id=skip_id)
    if "Left" not in used:
        return "Left"
    if "Right" not in used:
        return "Right"
    return "Left"


def ensure_sides(kind: str, items: list[CyberwareInstall]) -> list[CyberwareInstall]:
    by_id = {inst.id: inst for inst in items}
    for inst in items:
        ware = _ware_by_id(kind, inst.ware_id)
        if not ware:
            continue
        if inst.parent_id:
            parent = by_id.get(inst.parent_id)
            if parent and parent.side:
                inst.side = parent.side
            continue
        if not ware.get("selectside"):
            inst.side = None
            continue
        inst.side = _normalize_side(inst.side) or _next_free_side(items, kind, ware, skip_id=inst.id)
    return items


def _side_conflicts(kind: str, items: list[CyberwareInstall]) -> list[str]:
    seen: set[tuple[str, str]] = set()
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
        if key in seen:
            dups.add(key)
        else:
            seen.add(key)
    errors: list[str] = []
    for slot, side in sorted(dups):
        slot_ja = _SLOT_JA.get(slot, slot)
        errors.append(f"{_SIDE_JA.get(side, side)}の{slot_ja}が重複しています")
    return errors
