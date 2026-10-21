"""Electronic construction, allocations and stock. Resolution never consumes stock.

DT pp.65–66: acquisition remains priced on the original row; records account
for reservations and consumption in integer quarter-packs. Successful tests
are registered by the user, not rolled by this engine.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from ...data_loader import catalog_list
from ...models import CharacterState
from ...models.gear import ElectronicModificationRecord
from ...notices import Notice, notice, term
from .deck_modules import ADD_MODULE
from .misc import _held_multiplier

SINGLE_PARTS = "f56affe6-0159-4f7a-ba4d-b5283bd25c44"
FIVE_PARTS = "ec53ae4e-086f-4817-8cc2-ec574aa7cd51"
ADD_ATTACK = "f860ec1a-b688-4975-95f4-4c11648b04f0"
ADD_SLEAZE = "6638ae8f-d6e4-4d0b-ba3f-0fe05ef64ce0"
PERSONA = "48f8cb8e-dc9f-405e-b49a-fce3d61a1bda"


def modification_rule(spec: dict[str, Any]) -> tuple[str, str]:
    gid = str(spec.get("id") or "")
    if gid in (ADD_ATTACK, ADD_SLEAZE):
        return "add", "attack" if gid == ADD_ATTACK else "sleaze"
    if gid == ADD_MODULE:
        return "module", ""
    if gid == PERSONA:
        return "persona", ""
    # Stable catalog IDs are published by the loader as the rule contract;
    # unknown/custom records without a rule remain unsupported.
    return str(spec.get("electronic_rule") or ""), str(spec.get("electronic_attribute") or "")


def requirement(spec: dict[str, Any], host: dict[str, Any], host_spec: dict[str, Any]) -> tuple[int | None, str]:
    rule, attr = modification_rule(spec)
    if rule == "add":
        if host_spec.get("attributearray") or int(host.get(attr) or 0) > 0:
            return None, "attributeExists"
        return int(host.get("device_rating") or 0) * 8, ""
    if rule == "increase":
        value = int(host.get(attr) or 0)
        if value <= 0:
            return None, "attributeMissing"
        return (value + 1) * 8, ""
    if rule == "modify":
        deltas = [int(x) for x in str(spec.get("modattributearray") or "").split(",") if x]
        if deltas and not host_spec.get("attributearray"):
            return None, "arrayRequired"
        values = list(host.get("array") or [])
        if deltas and (len(values) != 4 or any(v + d < 0 for v, d in zip(values, deltas, strict=False))):
            return None, "attributeMissing"
        if not deltas:
            for key in ("attack", "sleaze", "dataprocessing", "firewall"):
                delta = int(spec.get("mod" + key) or 0)
                if delta and (int(host.get(key) or 0) <= 0 or int(host.get(key) or 0) + delta < 0):
                    return None, "attributeMissing"
        return 16, ""
    if rule == "module":
        return 8, ""
    if rule == "persona":
        # All three matrix-device buckets already provide personas. Other hosts
        # are deliberately unsupported until their eligibility is specified.
        return None, "personaExists"
    return None, "unsupportedRule"


def resolve_electronic_modifications(
    state: CharacterState,
    hosts: list[dict[str, Any]],
    gear: list[dict[str, Any]],
) -> list[Notice]:
    warnings: list[Notice] = []
    specs = {str(s["id"]): s for s in catalog_list("gear")}
    host_by_id = {str(h["id"]): h for h in hosts}
    for base_host in hosts:
        # UI estimates must use the same preconstruction values as completion,
        # before dongles, qualities and modifications alter the displayed ASDF.
        base_host["construction_attributes"] = {
            k: int(base_host.get(k) or 0) for k in ("device_rating", "attack", "sleaze", "dataprocessing", "firewall")
        }
    rows = {str(r["id"]): r for r in gear}
    stock = _stock(state, specs)
    sources_invalid = _sources_invalid(state, stock)
    if sources_invalid:
        warnings.append(notice("engine.gear.materialAllocationInvalid", name="parts sources"))
    records = state.electronic_modification_records
    used, reserved = _allocated(records)
    bad_records = _bad_records(records, specs, stock, used, reserved, sources_invalid, warnings)
    active: dict[str, ElectronicModificationRecord] = {r.modification_id: r for r in records}
    active.update({r.modification_id: r for r in records if r.status != "cancelled"})
    available = sum(max(0, n - used[sid] - reserved[sid]) for sid, n in stock.items())
    host_specs = {str(s["id"]): s for b in ("cyberdecks", "rccs", "commlinks") for s in catalog_list(b)}
    roots: dict[str, list[dict[str, Any]]] = {}
    for row in gear:
        if row.get("category") != "Electronic Modification":
            continue
        host = _judge_modification(row, rows, host_by_id, active, specs, host_specs, bad_records, available, warnings)
        if host is not None and row.get("parent_id") == host["id"] and row["modification_status"] != "pending":
            roots.setdefault(str(host["id"]), []).append(row)
    for hid, mods in roots.items():
        if sum(int(r.get("qty") or 1) for r in mods if not r.get("included")) > 1:
            warnings.append(notice("engine.gear.modificationsOver", name=term(str(host_by_id[hid]["name"]))))
            for row in mods:
                if not row.get("included"):
                    row.update(modification_valid=False, modification_reason="modificationLimit")
    for row in gear:
        parent = rows.get(str(row.get("parent_id") or ""))
        if (
            row.get("category") == "Electronic Modification"
            and parent
            and parent.get("category") == "Electronic Modification"
            and not parent.get("modification_valid")
        ):
            row.update(modification_valid=False, modification_reason="invalidParent")
    _add_supply_rows(state, gear, rows)
    _show_stock(stock, rows, used, reserved)
    return warnings


def _stock(state: CharacterState, specs: dict[str, dict[str, Any]]) -> dict[str, int]:
    """Quarter-packs per parts source: bought Electronic Parts rows and recorded supplies."""
    installs = {r.id: r for r in state.gear}
    stock: dict[str, int] = {}
    for inst in state.gear:
        if inst.gear_id in (SINGLE_PARTS, FIVE_PARTS):
            stock[inst.id] = (
                inst.purchased_parts_units
                if inst.purchased_parts_units is not None
                else max(1, inst.qty) * (20 if inst.gear_id == FIVE_PARTS else 4)
            ) * _held_multiplier(inst, installs, specs)
    for supply in state.electronic_parts_supplies:
        stock[supply.id] = supply.units
    return stock


def _sources_invalid(state: CharacterState, stock: dict[str, int]) -> bool:
    """Two sources share an id, or a piece of equipment is missing or listed twice."""
    duplicate_sources = len(stock) != sum(i.gear_id in (SINGLE_PARTS, FIVE_PARTS) for i in state.gear) + len(
        state.electronic_parts_supplies
    )
    equipment = [s.equipment_id for s in state.electronic_parts_supplies if s.kind == "equipment"]
    return duplicate_sources or len(equipment) != len(set(equipment)) or any(not e for e in equipment)


def _allocated(records: list[ElectronicModificationRecord]) -> tuple[Counter[str], Counter[str]]:
    """Units per source, as ``(used by completed, reserved by pending)``."""
    used: Counter[str] = Counter()
    reserved: Counter[str] = Counter()
    for record in records:
        totals = used if record.status == "completed" else reserved if record.status == "pending" else None
        if totals is not None:
            for a in record.allocations:
                totals[a.source_id] += a.units
    return used, reserved


def _frozen_required(record: ElectronicModificationRecord, specs: dict[str, dict[str, Any]]) -> int | None:
    """The units a completed record needed, recomputed off its host snapshot."""
    rule, attr = modification_rule(specs.get(record.gear_id) or {})
    snap = record.host_snapshot
    if not snap:
        return None
    if rule == "add":
        return int(snap.get("device_rating") or 0) * 8
    if rule == "increase":
        return (int(snap.get(attr) or 0) + 1) * 8
    return {"module": 8, "modify": 16}.get(rule)


def _bad_records(
    records: list[ElectronicModificationRecord],
    specs: dict[str, dict[str, Any]],
    stock: dict[str, int],
    used: Counter[str],
    reserved: Counter[str],
    sources_invalid: bool,
    warnings: list[Notice],
) -> set[str]:
    """Records whose allocations or bookkeeping do not add up, each warned about."""
    record_ids = Counter(r.id for r in records)
    mod_ids = Counter(r.modification_id for r in records if r.status != "cancelled")
    bad_sources = {sid for sid in used.keys() | reserved.keys() if used[sid] + reserved[sid] > stock.get(sid, 0)}
    bad: set[str] = set()
    for record in records:
        ids = [a.source_id for a in record.allocations]
        allocated = sum(a.units for a in record.allocations)
        frozen_required = _frozen_required(record, specs) if record.status == "completed" else None
        if (
            (
                record.status == "completed"
                and (frozen_required is None or frozen_required != record.required_units or frozen_required <= 0)
            )
            or record_ids[record.id] > 1
            or mod_ids[record.modification_id] > 1
            or (record.status in ("completed", "pending") and len(ids) != len(set(ids)))
            or (record.status in ("completed", "pending") and any(s not in stock or s in bad_sources for s in ids))
            or (record.status == "completed" and allocated != record.required_units)
            or (record.status == "pending" and allocated > record.required_units)
            or sources_invalid
        ):
            bad.add(record.id)
            warnings.append(notice("engine.gear.materialAllocationInvalid", name=record.modification_id))
    return bad


def _judge_modification(
    row: dict[str, Any],
    rows: dict[str, dict[str, Any]],
    host_by_id: dict[str, dict[str, Any]],
    active: dict[str, ElectronicModificationRecord],
    specs: dict[str, dict[str, Any]],
    host_specs: dict[str, dict[str, Any]],
    bad_records: set[str],
    available: int,
    warnings: list[Notice],
) -> dict[str, Any] | None:
    """Mark one modification row's status, validity and material; return its host."""
    parent = rows.get(str(row.get("parent_id") or ""))
    host = host_by_id.get(str(row.get("parent_id") or ""))
    # DT allows Increase nested below the corresponding Add.
    if host is None and parent and parent.get("gear_id") in (ADD_ATTACK, ADD_SLEAZE):
        host = host_by_id.get(str(parent.get("parent_id") or ""))
    rec = active.get(str(row["id"]))
    status = ("pending" if rec.status == "cancelled" else rec.status) if rec else "unverified"
    spec = specs.get(str(row["gear_id"])) or {}
    required, reason = requirement(spec, host or {}, host_specs.get(str((host or {}).get("gear_id"))) or {})
    if host is None or int(row.get("qty") or 1) != 1:
        reason = "invalidHost"
    if parent and parent.get("gear_id") in (ADD_ATTACK, ADD_SLEAZE):
        attr = "attack" if parent["gear_id"] == ADD_ATTACK else "sleaze"
        rule, target = modification_rule(spec)
        if rule != "increase" or target != attr:
            reason = "invalidHost"
        else:
            required, reason = 16, ""  # new attribute 1 -> 2
    if rec and (rec.gear_id != row["gear_id"] or rec.host_id != str((host or {}).get("id")) or rec.id in bad_records):
        reason = "recordMismatch"
    valid = not reason and status in ("unverified", "historical", "completed")
    row.update(
        modification_status=status,
        modification_valid=valid,
        modification_reason=reason,
        material_required_units=rec.required_units if rec and status in ("completed", "historical") else required,
        material_available_units=available,
        material_allocated_units=sum(a.units for a in rec.allocations) if rec else 0,
        modification_host_id=(host or {}).get("id"),
    )
    if status == "unverified":
        warnings.append(notice("engine.gear.materialHistoryUnverified", name=term(str(row["name"]))))
    return host


def _add_supply_rows(state: CharacterState, gear: list[dict[str, Any]], rows: dict[str, dict[str, Any]]) -> None:
    """Show each recorded parts supply as an Electronic Parts row of its own."""
    for supply in state.electronic_parts_supplies:
        if supply.id in rows:
            continue
        row = {
            "id": supply.id,
            "gear_id": SINGLE_PARTS,
            "name": "Electronic Parts",
            "label": f"Electronic Parts ({supply.note})",
            "category": "Electronic Parts",
            "rating": 1,
            "rating_max": 0,
            "qty": supply.units / 4,
            "parent_id": None,
            "nuyen": 0,
            "included": True,
            "granted_by": supply.note or supply.kind,
            "parts_supply": True,
            "source": "DT",
            "page": "66",
        }
        gear.append(row)
        rows[supply.id] = row


def _show_stock(
    stock: dict[str, int], rows: dict[str, dict[str, Any]], used: Counter[str], reserved: Counter[str]
) -> None:
    for sid, total in stock.items():
        if sid not in rows:
            continue
        row = rows[sid]
        row.update(
            parts_purchased_units=total,
            parts_used_units=used[sid],
            parts_reserved_units=reserved[sid],
            parts_remaining_units=max(0, total - used[sid]),
            parts_available_units=max(0, total - used[sid] - reserved[sid]),
            purchased_qty=row["qty"],
        )
        # Carrying/export quantity in packs; state retains purchased sales lots.
        row["qty"] = max(0, total - used[sid]) / 4
        row["costfor"] = 1
