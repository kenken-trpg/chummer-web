"""Vehicles, with their mods and what is mounted or stowed in them."""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET  # the Element type only — parsing goes through parse_untrusted
from typing import Any

from ..data_loader import CatalogDict
from ..data_loader._xml import _int, _text
from ..notices import Notice, notice, ui
from ._common import _Resolver, _unexpected_children


def _import_vehicles(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read vehicles, drones and vehicle mods."""
    veh_r = _Resolver(cat["vehicles"])
    drone_r = _Resolver(cat["drones"])
    vmod_r = _Resolver(cat["vehicle_mods"])
    mount_r = _Resolver(cat["weapon_mounts"])
    mount_categories = {row["id"]: row.get("category") or "" for row in cat["weapon_mounts"]}
    mod_ware: dict[int, list[dict[str, Any]]] = dict(st.pop("_vehicle_mod_ware", None) or {})
    # A mount points at a weapon row by name: ids are regenerated on import.
    weapon_ids: dict[str, str] = {}
    for wrow in st.get("weapons") or []:
        wname = next((w["name"] for w in cat["weapons"] if w["id"] == wrow.get("weapon_id")), "")
        weapon_ids.setdefault(wname.lower(), wrow["id"])
    st_mounts: list[dict[str, Any]] = []
    st_veh: list[dict[str, Any]] = list(st.get("drones") or [])  # gear rows come later
    st_veh_only: list[dict[str, Any]] = []
    st_vmods: list[dict[str, Any]] = []
    carried: list[tuple[str, ET.Element]] = []
    for v in root.findall("./vehicles/vehicle"):
        is_drone = veh_r.resolve(v, [], ui("engine.kind.vehicle")) is None
        vid = (
            drone_r.resolve(v, [], ui("engine.kind.drone"))
            if is_drone
            else veh_r.resolve(v, warn, ui("engine.kind.vehicle"))
        )
        if not vid:
            vid = veh_r.resolve(v, [], ui("engine.kind.vehicle")) or drone_r.resolve(v, warn, ui("engine.kind.drone"))
        if not vid:
            continue
        row = {"id": str(uuid.uuid4()), "gear_id": vid, "rating": 1, "qty": 1}
        (st_veh if is_drone else st_veh_only).append(row)
        for m in v.findall("./mods/mod") + v.findall("./vehiclemods/vehiclemod"):
            mid = vmod_r.resolve(m, warn, ui("engine.kind.vehicleMod"))
            held_ware = mod_ware.pop(id(m), [])
            if mid:
                mod_row = {
                    "id": str(uuid.uuid4()),
                    "mod_id": mid,
                    "parent_id": row["id"],
                    "rating": max(1, _int(m.find("rating"), 1)),
                    "included": _text(m.find("included")).lower() == "true",
                }
                st_vmods.append(mod_row)
                for ware_row in held_ware:
                    # only the mod's own implants: what is plugged into those
                    # already has its parent
                    ware_row.setdefault("parent_id", mod_row["id"])
        for m in v.findall("./weaponmounts/weaponmount"):
            size_id = mount_r.resolve(m, warn, ui("engine.kind.weaponMount"))
            if not size_id:
                continue
            parts = {"Visibility": "", "Flexibility": "", "Control": ""}
            for opt in m.findall("./weaponmountoptions/weaponmountoption"):
                part_id = mount_r.resolve(opt, warn, ui("engine.kind.weaponMount"))
                if part_id and mount_categories.get(part_id) in parts:
                    parts[mount_categories[part_id]] = part_id
            st_mounts.append(
                {
                    "id": str(uuid.uuid4()),
                    "parent_id": row["id"],
                    "size_id": size_id,
                    "visibility_id": parts["Visibility"],
                    "flexibility_id": parts["Flexibility"],
                    "control_id": parts["Control"],
                    "included": _text(m.find("included")).lower() == "true",
                    "weapon_install_id": weapon_ids.get(_text(m.find("mountedweaponname")).lower()),
                    "allowedweapons": _text(m.find("weaponmountcategories")),
                }
            )
        vehicle_id = str(row["id"])
        carried += [
            (vehicle_id, g)
            for g in _unexpected_children(vid, v.findall("./gears/gear"))
            # Chummer builds a vehicle's Sensor Array from its sensor rating
            # and saves it as gear; this app keeps the rating instead
            if _text(g.find("name")) != "Sensor Array"
        ]
        if _unexpected_children(vid, v.findall("./weapons/weapon")):
            warn.append(notice("engine.import.vehicleLoadSkipped", name=_text(v.find("name"))))
    # implants in a mod that could not be read have nowhere to go
    orphans = {id(row) for rows in mod_ware.values() for row in rows}
    if orphans:
        st["cyberware"] = [row for row in st.get("cyberware") or [] if id(row) not in orphans]
    st["drones"] = st_veh
    st["vehicles"] = st_veh_only
    st["vehicle_mods"] = st_vmods
    st["weapon_mounts"] = st_mounts
    # what is stowed in them — `_import_gear` knows the buckets
    st["_vehicle_gear"] = carried
