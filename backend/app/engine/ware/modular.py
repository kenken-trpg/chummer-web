"""Derive modular equip state from ownership, without changing purchase records."""

from typing import Any

from ...notices import Notice, notice, term, terms


def check_modular_mounts(rows: list[dict[str, Any]], specs: dict[str, dict[str, Any]]) -> list[Notice]:
    """Validate direct connections using ConstructModularCyberlimbList's rules.

    Unparented plugs are owned, detached equipment. Report invalid stored
    connections without deleting purchases or choosing an occupancy winner.
    Side assignment belongs to ensure_sides, which inherits the host's side.
    """
    by_id = {str(row["id"]): row for row in rows}
    occupants: dict[str, list[dict[str, Any]]] = {}
    errors: list[Notice] = []
    for row in rows:
        plug = str(specs.get(str(row["ware_id"]), {}).get("mounts_to") or "")
        parent_id = str(row.get("parent_id") or "")
        if not plug or not parent_id:
            continue
        parent = by_id.get(parent_id)
        if parent is None:
            # Vehicle hosts and orphan cleanup have their own validation.
            continue
        mount = str(specs.get(str(parent["ware_id"]), {}).get("modular_mount") or "")
        if plug != mount:
            errors.append(
                notice(
                    "engine.ware.modularMountMismatch",
                    name=term(str(row["name"])),
                    parent=term(str(parent["name"])),
                    mount=plug,
                )
            )
            continue
        occupants.setdefault(parent_id, []).append(row)
        if row.get("grade") != parent.get("grade"):
            errors.append(
                notice(
                    "engine.ware.modularGradeMismatch",
                    name=term(str(row["name"])),
                    parent=term(str(parent["name"])),
                    grade=term(str(row["grade"])),
                    parent_grade=term(str(parent["grade"])),
                )
            )
    for parent_id, children in occupants.items():
        if len(children) > 1:
            errors.append(
                notice(
                    "engine.ware.modularMountOccupied",
                    name=term(str(by_id[parent_id]["name"])),
                    count=len(children),
                    children=terms(str(child["name"]) for child in children),
                )
            )
    return errors


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
