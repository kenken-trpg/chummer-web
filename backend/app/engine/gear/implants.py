"""Commlinks and decks implanted in headware (SR5 p.451-452).

The headware `Commlink` and `Cyberdeck` are housings: `<allowgear>` names
the one gear category each holds, and the device inside is ordinary gear —
Chummer keeps it among the implant's `GearChildren` and adds its own
`TotalCost` to the implant's, unmultiplied by the grade. Here the device
stays in its own bucket, priced there, and `parent_id` names the implant.

Only a parent that is a piece of ware is this module's business: a deck may
also sit in a carried container (a briefcase), which the gear writer nests
as before.
"""

from __future__ import annotations

from typing import Any

from ...models import CharacterState
from ...notices import Notice, notice, term
from ..lookups import _item_by_id, _ware_by_id

#: the gear category of each bucket, as a housing's `<allowgear>` names it
IMPLANT_CATEGORIES = {"commlinks": "Commlinks", "cyberdecks": "Cyberdecks"}


def _ware_specs(state: CharacterState) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for kind in ("cyberware", "bioware"):
        for inst in getattr(state, kind) or []:
            spec = _ware_by_id(kind, inst.ware_id)
            if spec:
                out[inst.id] = spec
    return out


def place_implanted_devices(state: CharacterState) -> tuple[dict[str, str], list[Notice]]:
    """Which commlinks and decks sit in which implant: ``{device id: implant
    name}``. One whose implant does not hold its kind is carried instead, and
    said so."""
    hosts = _ware_specs(state)
    placed: dict[str, str] = {}
    warnings: list[Notice] = []
    for bucket, category in IMPLANT_CATEGORIES.items():
        for inst in getattr(state, bucket) or []:
            host = hosts.get(inst.parent_id or "")
            if host is None:
                continue
            if category in (host.get("allow_gear") or []):
                placed[inst.id] = str(host.get("name") or "")
                continue
            spec = _item_by_id(bucket, inst.gear_id) or {}
            warnings.append(
                notice(
                    "engine.gear.doesNotFit",
                    name=term(str(spec.get("name") or "")),
                    host=term(str(host.get("name") or "")),
                )
            )
            inst.parent_id = None
    return placed, warnings


def mark_implanted(rows: list[dict[str, Any]], placed: dict[str, str], state_rows: list[Any]) -> None:
    """Put the implant on each device row it sits in: ``parent_id`` and its
    name, ``implanted_in``."""
    parents = {inst.id: inst.parent_id for inst in state_rows}
    for row in rows:
        name = placed.get(str(row.get("id") or ""))
        if name is not None:
            row["parent_id"] = parents.get(row["id"])
            row["implanted_in"] = name
