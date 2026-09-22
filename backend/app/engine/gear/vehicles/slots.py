"""R5 mod-slot accounting (Rigger 5.0 slot categories, drone give-backs) and
the list of gear rows that can host vehicle mods."""

from __future__ import annotations

from typing import Any

from ....data_loader import catalog
from ....models import CharacterState, GearInstall
from ....notices import Notice, notice, term, ui
from ....rules import current_rules
from .._common import (
    _leading_vehicle_stat,
)

R5_MOD_SLOT_CATEGORIES = (
    "Powertrain",
    "Protection",
    "Weapons",
    "Body",
    "Electromagnetic",
    "Cosmetic",
)


R5_SLOT_ADD_KEYS = {
    "Powertrain": "powertrainmodslots",
    "Protection": "protectionmodslots",
    "Weapons": "weaponmodslots",
    "Body": "bodymodslots",
    "Electromagnetic": "electromagneticmodslots",
    "Cosmetic": "cosmeticmodslots",
}


def _host_is_drone(row: dict[str, Any]) -> bool:
    return str(row.get("category") or "").startswith("Drones")


def drone_mod_rules(row: dict[str, Any]) -> bool:
    """Whether Rigger 5.0's optional drone modification rules govern this row:
    the `<dronemods>` setting is on and the row is a drone (Chummer's
    `IsDrone && Settings.DroneMods`). Off, a drone is fitted like any other
    vehicle, one slot track per mod category."""
    return current_rules().drone_mods and _host_is_drone(row)


def _add_vehicle_slot_use(
    parent: dict[str, Any], slots: int, category: str, included: bool, *, downgrade: bool = False
) -> None:
    if included:
        return
    used = max(0, int(slots))
    if drone_mod_rules(parent):
        # A mod that costs a negative number of slots hands them to the drone
        # instead of taking them (`Vehicle.DroneModSlots`). It is banked here
        # and added to the maximum in `_finalize_vehicle_slots`, never
        # subtracted from the used count: Chummer leaves downgrades out of
        # `DroneModSlotsUsed` entirely, which `max(0, ...)` above already does.
        if int(slots) < 0:
            banked = parent.setdefault("_slot_given_back", [])
            banked.append((bool(downgrade), -int(slots)))
        parent["slots_used"] = int(parent.get("slots_used") or 0) + used
        return
    if category not in R5_SLOT_ADD_KEYS:
        return
    tracks = parent.setdefault("_slot_used", {})
    tracks[category] = int(tracks.get(category) or 0) + used


def _drone_slot_bonus(given_back: list[tuple[bool, int]]) -> int:
    """The mod slots a drone gains back from its negative-slot mods.

    `Vehicle.DroneModSlots`: every such mod hands its slots over, except that
    downgrades are capped at one between them — "You receive only one
    additional Mod Point from Downgrades". Trading away handling *and* sensors
    still buys a single slot, so the cheapest downgrade is the only one worth
    fitting for space.
    """
    bonus = 0
    downgraded = False
    for is_downgrade, slots in given_back:
        if is_downgrade:
            if downgraded:
                continue
            downgraded = True
        bonus += slots
    return bonus


def _finalize_vehicle_slots(hosts: list[dict[str, Any]]) -> list[Notice]:
    errors: list[Notice] = []
    for row in hosts:
        body = int((row.get("stats") or {}).get("body") or _leading_vehicle_stat(str(row.get("body") or "0")))
        if drone_mod_rules(row):
            listed = row.get("modslots")
            maximum = int(listed) if listed is not None else body
            maximum += _drone_slot_bonus(row.pop("_slot_given_back", None) or [])
            used = int(row.get("slots_used") or 0)
            row["slots_max"] = maximum
            row["slot_tracks"] = []
            if used > maximum:
                errors.append(
                    notice("engine.gear.vehicleSlotsOver", name=term(str(row["name"])), used=used, max=maximum)
                )
            continue
        used_map = row.pop("_slot_used", None) or {}
        tracks: list[dict[str, Any]] = []
        total_used = 0
        for category in R5_MOD_SLOT_CATEGORIES:
            extra = int(row.get(R5_SLOT_ADD_KEYS[category]) or 0)
            maximum = max(0, body + extra)
            used = int(used_map.get(category) or 0)
            total_used += used
            tracks.append(
                {
                    "category": category,
                    "used": used,
                    "max": maximum,
                }
            )
            if used > maximum:
                errors.append(
                    notice(
                        "engine.gear.vehicleCategorySlotsOver",
                        name=term(str(row["name"])),
                        category=ui(f"engine.vehicleSlot.{category}"),
                        used=used,
                        max=maximum,
                    )
                )
        row["slot_tracks"] = tracks
        row["slots_used"] = total_used
        row["slots_max"] = body
    return errors


def _iter_vehicle_hosts(state: CharacterState) -> list[tuple[GearInstall, dict[str, Any]]]:
    drones = {item["id"]: item for item in catalog().get("drones") or []}
    vehicles = {item["id"]: item for item in catalog().get("vehicles") or []}
    out: list[tuple[GearInstall, dict[str, Any]]] = []
    for inst in list(state.drones or []):
        spec = drones.get(inst.gear_id)
        if spec:
            out.append((inst, spec))
    for inst in list(state.vehicles or []):
        spec = vehicles.get(inst.gear_id)
        if spec:
            out.append((inst, spec))
    return out
