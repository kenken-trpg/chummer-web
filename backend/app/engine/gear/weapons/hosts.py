"""The installed ware that owns a generated weapon (also while detached)."""

from typing import Any

from ....models import CharacterState
from ...lookups import _item_by_id, _ware_by_id


def ware_weapon_specs(state: CharacterState) -> dict[str, dict[str, Any]]:
    hosts: dict[str, dict[str, Any]] = {}
    for kind in ("cyberware", "bioware"):
        for inst in getattr(state, kind):
            ware = _ware_by_id(kind, inst.ware_id) or {}
            spec = _item_by_id("weapons", str(ware.get("add_weapon_id") or ""))
            if spec:
                hosts[inst.id] = spec
    return hosts
