"""Derive modular equip state from ownership, without changing purchase records."""

from typing import Any


def apply_modular_state(rows: list[dict[str, Any]], specs: dict[str, dict[str, Any]]) -> None:
    """Mirror Cyberware.IsModularCurrentlyEquipped's ancestor walk.

    The highest ancestor's mount/plug wins; a node with both is a plug.
    Ordinary ware gets no extra derived fields. Cycles fail closed.
    """
    by_id = {str(row["id"]): row for row in rows}
    for row in rows:
        spec = specs.get(str(row["ware_id"]), {})
        equipped = not spec.get("mounts_to")
        modular = bool(spec.get("mounts_to") or spec.get("modular_mount"))
        seen = {str(row["id"])}
        parent_id = row.get("parent_id")
        while parent_id and str(parent_id) in by_id:
            if str(parent_id) in seen:
                equipped = False
                modular = True
                break
            seen.add(str(parent_id))
            parent = by_id[str(parent_id)]
            parent_spec = specs.get(str(parent["ware_id"]), {})
            if parent_spec.get("modular_mount"):
                equipped = True
                modular = True
            if parent_spec.get("mounts_to"):
                equipped = False
                modular = True
            parent_id = parent.get("parent_id")
        if modular:
            row["modular_equipped"] = equipped
        if not equipped:
            # Clear only calculated improvements. Cost, ownership, wireless
            # preference and the catalog's bonus definitions remain intact.
            row["bonus"] = []
