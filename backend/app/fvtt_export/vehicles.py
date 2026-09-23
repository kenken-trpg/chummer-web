"""Vehicles and drones: their mods, the ware built into them, and what is
stowed or mounted on board."""

from __future__ import annotations

from typing import Any

from ..models import CharacterState
from ._common import _flag, _fullname, _html, _money
from .combat import _weapons
from .gear import _GEAR_BUCKETS, _gears, _wares


def _vehicle_owners(state: CharacterState, derived: dict[str, Any]) -> dict[str, str]:
    """Row id -> the vehicle or drone it sits in, for gear stowed in one (or
    in something stowed in one) and the gun on one of its weapon mounts.
    Foundry makes each vehicle an actor of its own, so these go on it rather
    than on the character."""
    vehicles = {str(row.get("id")) for key in ("vehicles", "drones") for row in derived.get(key) or []}
    parents: dict[str, str] = {}
    for bucket in _GEAR_BUCKETS:
        for row in derived.get(bucket) or []:
            parents[str(row.get("id"))] = str(row.get("parent_id") or "")
    for mod in state.vehicle_mods:
        parents[mod.id] = mod.parent_id or ""
    # set by the engine only for a gun its mount check let through
    for weapon in derived.get("weapons") or []:
        parents[str(weapon.get("id"))] = str(weapon.get("mounted_on") or "")

    def owner(row_id: str) -> str:
        seen: set[str] = set()
        while row_id and row_id not in seen:
            if row_id in vehicles:
                return row_id
            seen.add(row_id)
            row_id = parents.get(row_id, "")
        return ""

    found = {row_id: owner(row_id) for row_id in parents if row_id not in vehicles}
    return {row_id: vehicle for row_id, vehicle in found.items() if vehicle}


_VEHICLE_STATS = ("handling", "accel", "speed", "pilot", "body", "armor", "seats", "sensor")


def _vehicles(derived: dict[str, Any], tr: Any, owners: dict[str, str]) -> list[dict[str, Any]]:
    """Vehicles and drones with the stats the sheet shows (mods worked in).
    The importer makes each one a vehicle actor driven by the character and
    reads handling / speed / accel as "on-road/off-road". Ware in a mod (a
    drone arm) sits under it as in Chummer; the importer never reads that, so
    it is also listed in the mod's `notes`, which becomes its description."""
    out = []
    names = {
        str(row.get("id") or ""): _fullname(
            tr(str(row.get("name") or ""), "cyberware"),
            " ".join(tr(str(x)) for x in (row.get("extra"), row.get("side")) if x),
        )
        for row in derived.get("cyberware") or []
    }
    parents = {str(row.get("id") or ""): str(row.get("parent_id") or "") for row in derived.get("cyberware") or []}
    wares = {str(row.get("guid") or ""): row for row in _wares(derived, tr, skip_hosted=False)}
    for key in ("vehicles", "drones"):
        for row in derived.get(key) or []:
            vid = str(row.get("id") or "")
            name = str(row.get("name") or "")
            category = str(row.get("category") or "")
            mods = [
                {
                    "guid": str(mod.get("id") or ""),
                    "sourceid": str(mod.get("mod_id") or ""),
                    "name": tr(str(mod["name"])),
                    "name_english": str(mod["name"]),
                    "category": tr(str(mod.get("category") or "")),
                    "category_english": str(mod.get("category") or ""),
                    "rating": str(int(mod.get("rating") or 0)),
                    "included": _flag(mod.get("included")),
                    "avail": str(mod.get("avail") or ""),
                    "owncost": _money(mod.get("nuyen")),
                    "source": str(mod.get("source") or ""),
                    "page": str(mod.get("page") or ""),
                    **_mod_wares(mod, names, parents, wares),
                }
                for mod in row.get("mods") or []
                if mod.get("name")
            ]
            out.append(
                {
                    "guid": vid,
                    "sourceid": str(row.get("gear_id") or ""),
                    "name": tr(name),
                    "name_english": name,
                    "fullname": tr(name),
                    "fullname_english": name,
                    "category": tr(category),
                    "category_english": category,
                    "isdrone": _flag(key == "drones"),
                    **{stat: str(row.get(stat) or "0") for stat in _VEHICLE_STATS},
                    "avail": str(row.get("avail") or ""),
                    "owncost": _money(row.get("nuyen")),
                    "source": str(row.get("source") or ""),
                    "page": str(row.get("page") or ""),
                    "mods": {"mod": mods},
                    "gears": {"gear": _gears(derived, tr, owners, vid)},
                    "weapons": {"weapon": _weapons(derived, tr, owners, vid)},
                }
            )
    return out


def _mod_wares(
    mod: dict[str, Any], names: dict[str, str], parents: dict[str, str], wares: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """`cyberwares` (with plugged-in parts as `children`) and a `notes` list."""
    top = [str(ware.get("id") or "") for ware in mod.get("cyberware") or []]
    if not top:
        return {}

    def node(wid: str) -> dict[str, Any]:
        kids = [node(cid) for cid, pid in parents.items() if pid == wid and cid in wares]
        return {**wares[wid], "children": {"cyberware": kids} if kids else None}

    def lines(wid: str, depth: int) -> list[str]:
        out = ["\u3000" * depth + names.get(wid, "")]
        for cid, pid in parents.items():
            if pid == wid:
                out += lines(cid, depth + 1)
        return out

    return {
        "cyberwares": {"cyberware": [node(wid) for wid in top if wid in wares]},
        "notes": _html("\n".join(line for wid in top for line in lines(wid, 0))),
    }
