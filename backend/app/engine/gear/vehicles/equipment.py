"""Drone equipment the catalog grants a vehicle, kept in step with its host."""

from __future__ import annotations

from ....data_loader import catalog
from ....models import CharacterState, GearInstall, VehicleModInstall, WeaponMountInstall
from .._common import (
    _find_mount_part,
)
from .slots import _iter_vehicle_hosts


def _ensure_drone_equipment(state: CharacterState) -> None:
    sensors = {item["id"]: item for item in catalog().get("sensors") or []}
    sensors_by_name = {item["name"]: item for item in sensors.values()}
    gear = {item["id"]: item for item in catalog().get("gear") or []}
    gear_by_name = {item["name"]: item for item in gear.values()}
    mods = {item["id"]: item for item in catalog().get("vehicle_mods") or []}
    mods_by_name = {item["name"]: item for item in mods.values()}
    have_sensors = {(row.parent_id, (sensors.get(row.gear_id) or {}).get("name")) for row in state.sensors or []}
    extra_sensors: list[GearInstall] = []
    have_gear = {(row.parent_id, (gear.get(row.gear_id) or {}).get("name")) for row in state.gear or []}
    extra_gear: list[GearInstall] = []
    for host, spec in _iter_vehicle_hosts(state):
        for gift in spec.get("included_gears") or []:
            name = gift.get("name") or ""
            child = sensors_by_name.get(name)
            if child:
                if (host.id, child["name"]) in have_sensors:
                    continue
                extra_sensors.append(
                    GearInstall(
                        gear_id=child["id"],
                        parent_id=host.id,
                        included=True,
                        rating=int(gift.get("rating") or 1),
                    )
                )
                have_sensors.add((host.id, child["name"]))
                continue
            child = gear_by_name.get(name)
            if not child or (host.id, child["name"]) in have_gear:
                continue
            extra_gear.append(
                GearInstall(
                    gear_id=child["id"],
                    parent_id=host.id,
                    included=True,
                    rating=int(gift.get("rating") or 1),
                )
            )
            have_gear.add((host.id, child["name"]))
    if extra_sensors:
        state.sensors = list(state.sensors or []) + extra_sensors
    if extra_gear:
        state.gear = list(state.gear or []) + extra_gear

    have_mods = {(row.parent_id, (mods.get(row.mod_id) or {}).get("name")) for row in state.vehicle_mods or []}
    extra_mods: list[VehicleModInstall] = []
    for host, spec in _iter_vehicle_hosts(state):
        for name in spec.get("included_mods") or []:
            child = mods_by_name.get(name)
            if not child or (host.id, child["name"]) in have_mods:
                continue
            extra_mods.append(VehicleModInstall(mod_id=child["id"], parent_id=host.id, included=True))
            have_mods.add((host.id, child["name"]))
    if extra_mods:
        state.vehicle_mods = list(state.vehicle_mods or []) + extra_mods

    have_mounts = {
        (row.parent_id, row.size_id, row.visibility_id, row.flexibility_id, row.control_id)
        for row in state.weapon_mounts or []
    }
    extra_mounts: list[WeaponMountInstall] = []
    for host, spec in _iter_vehicle_hosts(state):
        source = str(spec.get("source") or "")
        for gift in spec.get("included_weaponmounts") or []:
            size = _find_mount_part(gift.get("size") or "", "Size", source)
            vis = _find_mount_part(gift.get("visibility") or "", "Visibility", source)
            flex = _find_mount_part(gift.get("flexibility") or "", "Flexibility", source)
            ctrl = _find_mount_part(gift.get("control") or "", "Control", source)
            if not size:
                continue
            key = (
                host.id,
                size["id"],
                vis["id"] if vis else "",
                flex["id"] if flex else "",
                ctrl["id"] if ctrl else "",
            )
            if key in have_mounts:
                continue
            extra_mounts.append(
                WeaponMountInstall(
                    parent_id=host.id,
                    size_id=size["id"],
                    visibility_id=vis["id"] if vis else "",
                    flexibility_id=flex["id"] if flex else "",
                    control_id=ctrl["id"] if ctrl else "",
                    included=True,
                    allowedweapons=gift.get("allowedweapons") or "",
                )
            )
            have_mounts.add(key)
    if extra_mounts:
        state.weapon_mounts = list(state.weapon_mounts or []) + extra_mounts
