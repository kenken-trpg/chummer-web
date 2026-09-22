"""Vehicles and drones, their mods, and the mounts weapons hang off."""

from __future__ import annotations

from ..data_loader import CatalogDict


def _free_drone_mod(mod: dict) -> bool:
    return bool(mod.get("optionaldrone")) and str(mod.get("cost") or "").strip() == "0"


def section(raw: CatalogDict) -> dict:
    return {
        "drones": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "",
                "handling": c.get("handling") or "",
                "speed": c.get("speed") or "",
                "accel": c.get("accel") or "",
                "body": c.get("body") or "",
                "armor": c.get("armor") or "",
                "pilot": c.get("pilot") or "",
                "sensor": c.get("sensor") or "",
                "seats": c.get("seats") or "",
                "avail": c.get("avail") or "",
                "cost": c.get("cost") or "0",
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("drones") or []
        ],
        "vehicles": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "",
                "handling": c.get("handling") or "",
                "speed": c.get("speed") or "",
                "accel": c.get("accel") or "",
                "body": c.get("body") or "",
                "armor": c.get("armor") or "",
                "pilot": c.get("pilot") or "",
                "sensor": c.get("sensor") or "",
                "seats": c.get("seats") or "",
                "avail": c.get("avail") or "",
                "cost": c.get("cost") or "0",
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("vehicles") or []
        ],
        "vehicle_mods": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "",
                "cost": c.get("cost") or "0",
                "slots": c.get("slots") or "0",
                "avail": c.get("avail") or "",
                "minrating": int(c.get("minrating") or 0),
                "maxrating": int(c.get("maxrating") or 0),
                "purchasable": bool(c.get("purchasable")),
                "optionaldrone": bool(c.get("optionaldrone")),
                "required": c.get("required") or {},
                "forbidden": c.get("forbidden") or {},
                "capacity": c.get("capacity") or "",
                "subsystems": list(c.get("subsystems") or []),
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("vehicle_mods") or []
            # the free drone mods (downgrades, Immobile, Fragile) cost nothing
            # yet are fitted by hand under `<dronemods>`
            if c.get("purchasable") or _free_drone_mod(c)
        ],
        "weapon_mounts": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "",
                "cost": c.get("cost") or "0",
                "slots": c.get("slots") or "0",
                "avail": c.get("avail") or "",
                "optionaldrone": bool(c.get("optionaldrone")),
                "required": c.get("required") or {},
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("weapon_mounts") or []
        ],
    }
