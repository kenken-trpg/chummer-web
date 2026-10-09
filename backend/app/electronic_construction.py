"""Atomic PATCH rules for construction and immutable consumed purchases."""

from __future__ import annotations

from .data_loader import catalog_list
from .engine.compute.gear import resolve_gear
from .engine.gear.electronic_modifications import requirement
from .models import CharacterState, GearInstall
from .models.gear import ElectronicModificationRecord
from .notices import NoticeError, notice


def prepare_construction_patch(old: CharacterState, new: CharacterState) -> None:
    specs = {str(s["id"]): s for s in catalog_list("gear")}
    old_mods = {r.id for r in old.gear if (specs.get(r.gear_id) or {}).get("category") == "Electronic Modification"}
    active = {r.modification_id for r in new.electronic_modification_records if r.status != "cancelled"}
    incoming_rows = {r.id: r for r in new.gear}
    for row in new.gear:
        if (
            row.id not in old_mods
            and row.id not in active
            and (specs.get(row.gear_id) or {}).get("category") == "Electronic Modification"
        ):
            # A new PATCH without materials is a draft, never a legacy install.
            parent = incoming_rows.get(row.parent_id or "")
            host_id = row.parent_id or ""
            if parent and parent.gear_id in (
                "f860ec1a-b688-4975-95f4-4c11648b04f0",
                "6638ae8f-d6e4-4d0b-ba3f-0fe05ef64ce0",
            ):
                host_id = parent.parent_id or ""
            new.electronic_modification_records.append(
                ElectronicModificationRecord(
                    modification_id=row.id,
                    host_id=host_id,
                    gear_id=row.gear_id,
                )
            )
    old_records = {r.id: r for r in old.electronic_modification_records}
    new_records = {r.id: r for r in new.electronic_modification_records}
    for rid, saved_record in old_records.items():
        if saved_record.status not in ("completed", "historical", "cancelled"):
            continue
        current = new_records.get(rid)
        if current is None:
            raise NoticeError(notice("engine.gear.materialHistoryProtected"))
        if (
            saved_record.status != "cancelled"
            and current.status == "cancelled"
            and current.note.strip()
            and current.model_dump(exclude={"status", "note"}) == saved_record.model_dump(exclude={"status", "note"})
        ):
            continue  # explicit error correction, not removal of the gear
        if current != saved_record:
            raise NoticeError(notice("engine.gear.materialHistoryProtected"))
    protected = {
        a.source_id for r in new.electronic_modification_records if r.status == "completed" for a in r.allocations
    }
    old_rows = {r.id: r for r in old.gear}
    new_rows = {r.id: r for r in new.gear}
    # A used purchase and all quantity/price multipliers up its container chain
    # remain fixed. Split an untouched stack before allocating it.
    for sid in list(protected):
        seen: set[str] = set()
        ancestor: GearInstall | None = old_rows.get(sid)
        while ancestor and ancestor.id not in seen:
            seen.add(ancestor.id)
            replacement = new_rows.get(ancestor.id)
            if replacement is None or any(
                getattr(ancestor, k) != getattr(replacement, k)
                for k in (
                    "gear_id",
                    "qty",
                    "included",
                    "cost",
                    "discounted",
                    "parent_id",
                    "rating",
                    "purchased_parts_units",
                )
            ):
                raise NoticeError(notice("engine.gear.partsPurchaseProtected"))
            ancestor = old_rows.get(ancestor.parent_id or "")
    for record in new.electronic_modification_records:
        previous = old_records.get(record.id)
        if record.status not in ("completed", "historical") or previous and previous.status == record.status:
            continue
        if record.status == "historical":
            if (
                not record.note.strip()
                or record.modification_id not in old_mods
                or any(
                    r.modification_id == record.modification_id and r.status == "pending"
                    for r in old.electronic_modification_records
                )
            ):
                raise NoticeError(notice("engine.gear.materialHistoryProtected"))
            record.allocations = []
        trial = new.model_copy(deep=True)
        bundle = resolve_gear(trial)
        rows = {str(r["id"]): r for r in bundle["gear"]}
        mod = rows.get(record.modification_id)
        hosts = {str(r["id"]): r for b in ("commlinks", "cyberdecks", "rccs") for r in bundle[b]}
        host = hosts.get(record.host_id)
        if mod is None or host is None or mod["gear_id"] != record.gear_id:
            raise NoticeError(notice("engine.gear.materialAllocationInvalid", name=record.modification_id))
        # Rebuild unmodified host stats: construction includes no dongle,
        # Overclocker or this modification's own +1.
        from .engine.compute.gear_rows import resolve_commlink_rows
        from .engine.gear.matrix import _resolve_matrix_devices

        bare = new.model_copy(deep=True)
        _, links, _ = resolve_commlink_rows(bare)
        _, decks, _ = _resolve_matrix_devices("cyberdecks", bare.cyberdecks)
        _, rccs, _ = _resolve_matrix_devices("rccs", bare.rccs)
        bases = {str(r["id"]): r for r in [*links, *decks, *rccs]}
        base = bases[record.host_id]
        host_spec = next(
            (s for b in ("commlinks", "cyberdecks", "rccs") for s in catalog_list(b) if s["id"] == host["gear_id"]), {}
        )
        needed, reason = requirement(specs[record.gear_id], base, host_spec)
        parent = next((r for r in new.gear if r.id == mod.get("parent_id")), None)
        if parent and parent.gear_id in (
            "f860ec1a-b688-4975-95f4-4c11648b04f0",
            "6638ae8f-d6e4-4d0b-ba3f-0fe05ef64ce0",
        ):
            needed, reason = 16, ""
        if needed is None or reason:
            raise NoticeError(notice("engine.gear.materialAllocationInvalid", name=record.modification_id))
        record.required_units = needed
        record.host_snapshot = {
            k: int(base.get(k) or 0) for k in ("device_rating", "attack", "sleaze", "dataprocessing", "firewall")
        }
        if parent and parent.gear_id in (
            "f860ec1a-b688-4975-95f4-4c11648b04f0",
            "6638ae8f-d6e4-4d0b-ba3f-0fe05ef64ce0",
        ):
            record.host_snapshot["attack" if parent.gear_id == "f860ec1a-b688-4975-95f4-4c11648b04f0" else "sleaze"] = 1
    new.electronic_modification_records = [
        r for r in new.electronic_modification_records if r.status != "pending" or r.modification_id in new_rows
    ]
    pending_bundle = resolve_gear(new.model_copy(deep=True))
    pending_rows = {str(r["id"]): r for r in pending_bundle["gear"]}
    for record in new.electronic_modification_records:
        if record.status == "pending":
            value = pending_rows.get(record.modification_id, {}).get("material_required_units")
            record.required_units = int(value or 0)
    old_supplies = {s.id: s for s in old.electronic_parts_supplies}
    new_supplies = {s.id: s for s in new.electronic_parts_supplies}
    for sid in protected:
        if sid in old_supplies and old_supplies[sid] != new_supplies.get(sid):
            raise NoticeError(notice("engine.gear.partsPurchaseProtected"))
    for sid, saved_supply in old_supplies.items():
        if saved_supply.kind == "equipment" and sid in new_supplies and saved_supply != new_supplies[sid]:
            raise NoticeError(notice("engine.gear.partsPurchaseProtected"))
    for supply in new.electronic_parts_supplies:
        if supply.kind != "equipment" or supply.id in old_supplies:
            continue
        equipment = new_rows.get(supply.equipment_id or "")
        equipment_spec = specs.get(equipment.gear_id if equipment else "", {})
        maximum = {"4edec80a-e8df-4817-9728-4a6fc04d183e": 8, "d0c85aa4-5686-452b-9f1a-7c603ac43258": 40}.get(
            str(equipment_spec.get("id")), 0
        )
        if equipment:
            maximum *= max(1, equipment.qty)
        if equipment is None or equipment.extra != "Hardware" or supply.units > maximum or not maximum:
            raise NoticeError(notice("engine.gear.materialAllocationInvalid", name=supply.id))
    # Validate all changes together, so a failed construction is never returned
    # with only the purchase or only the consumption saved.
    check = resolve_gear(new.model_copy(deep=True))
    for record in new.electronic_modification_records:
        previous = old_records.get(record.id)
        if record.status == "completed" and (previous is None or previous.status != "completed"):
            resolved = next((r for r in check["gear"] if r["id"] == record.modification_id), {})
            if not resolved.get("modification_valid"):
                raise NoticeError(notice("engine.gear.materialAllocationInvalid", name=record.modification_id))
    for warning in check["warnings"]:
        if warning["key"] == "engine.gear.materialAllocationInvalid":
            raise NoticeError(warning)
    for resolved_row in check["gear"]:
        if (
            resolved_row.get("category") == "Electronic Modification"
            and resolved_row.get("modification_status") == "completed"
            and resolved_row.get("modification_reason") == "recordMismatch"
        ):
            raise NoticeError(notice("engine.gear.materialHistoryProtected"))
