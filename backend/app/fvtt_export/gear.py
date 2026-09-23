"""Cyber- and bioware, and gear — the buckets this app keeps apart and the
print XML walks as one tree, ammunition included."""

from __future__ import annotations

from typing import Any

from ..data_loader import catalog_list
from ._common import _flag, _fullname, _money

#: this app's grade -> the Foundry grade key (the importer lower-cases
#: `grade` and takes it as is). Used and the like have no Foundry grade.
_GRADES = {"Alphaware": "alpha", "Betaware": "beta", "Deltaware": "delta", "Gammaware": "gamma"}


def _vehicle_hosted_ware(derived: dict[str, Any]) -> set[str]:
    """Ids of ware fitted to a vehicle mod, and of what is plugged into it."""
    hosted = {
        str(ware.get("id") or "")
        for key in ("vehicles", "drones")
        for vehicle in derived.get(key) or []
        for mod in vehicle.get("mods") or []
        for ware in mod.get("cyberware") or []
    }
    rows = derived.get("cyberware") or []
    grew = True
    while grew:
        more = {str(row.get("id") or "") for row in rows if str(row.get("parent_id") or "") in hosted}
        grew = not more <= hosted
        hosted |= more
    return hosted


def _wares(derived: dict[str, Any], tr: Any, skip_hosted: bool = True) -> list[dict[str, str]]:
    """Cyberware and bioware in one list, told apart by `improvementsource`.
    Foundry has no nesting, so a plugged-in part comes out as its own item
    (Chummer nests it, and the importer would drop it). Ware fitted to a
    vehicle mod (a drone arm) goes with the vehicle instead."""
    out = []
    hosted = _vehicle_hosted_ware(derived) if skip_hosted else set()
    for source, key in (("Cyberware", "cyberware"), ("Bioware", "bioware")):
        for row in derived.get(key) or []:
            name = str(row.get("name") or "")
            if not name or str(row.get("id") or "") in hosted:
                continue
            extra = " ".join(str(x) for x in (row.get("extra"), row.get("side")) if x)
            category = str(row.get("category") or "")
            out.append(
                {
                    "guid": str(row.get("id") or ""),
                    "sourceid": str(row.get("ware_id") or ""),
                    "name": tr(name, "cyberware"),
                    "name_english": name,
                    "fullname": _fullname(tr(name, "cyberware"), tr(extra) if extra else ""),
                    "fullname_english": _fullname(name, extra),
                    "category": tr(category),
                    "category_english": category,
                    "improvementsource": source,
                    "ess": str(round(float(row.get("essence") or 0), 4)),
                    "capacity": str(float(row.get("capacity_max") or 0)),
                    "grade": _GRADES.get(str(row.get("grade") or ""), "standard"),
                    "rating": str(int(row.get("rating") or 0)),
                    "avail": str(row.get("avail") or ""),
                    "owncost": _money(row.get("nuyen")),
                    "source": str(row.get("source") or ""),
                    "page": str(row.get("page") or ""),
                }
            )
    return out


#: the buckets gear is split into, as the chum5 export walks them
_GEAR_BUCKETS = ("gear", "commlinks", "cyberdecks", "rccs", "sensors", "optics", "programs", "apps")
_DEVICE_BUCKETS = ("commlinks", "cyberdecks", "rccs")


def _is_sin(row: dict[str, Any]) -> bool:
    return row.get("category") == "ID/Credsticks" and "SIN" in str(row.get("name") or "").split()


def _cost_for() -> dict[str, int]:
    return {str(row["id"]): int(row.get("costfor") or 0) for bucket in _GEAR_BUCKETS for row in catalog_list(bucket)}


def _rounds(row: dict[str, Any], cost_for: dict[str, int]) -> int:
    """This app counts lots of `costfor` (a box of 10 rounds); Chummer the rounds."""
    return int(row.get("qty") or 1) * max(1, cost_for.get(str(row.get("gear_id")), 1))


def _gears(derived: dict[str, Any], tr: Any, owners: dict[str, str], owner: str = "") -> list[dict[str, Any]]:
    """Flags steer the importer's split: `iscommlink` makes a device (with
    its matrix attributes), `issin` a SIN, `isammo` ammunition, and the
    program categories a program; the rest is equipment. Foundry has no
    nesting, so a child comes out as its own item — except a license under a
    SIN, which the importer reads from the SIN's `children`. `owner` picks
    whose: the character's ("") or a vehicle's (see `_vehicle_owners`)."""
    cost_for = _cost_for()
    # ammo stowed with a weapon goes out as that weapon's clips (`_clips`)
    weapons = {str(row.get("id")) for row in derived.get("weapons") or []}
    rows = [
        (bucket, row)
        for bucket in _GEAR_BUCKETS
        for row in derived.get(bucket) or []
        if owners.get(str(row.get("id") or ""), "") == owner and str(row.get("parent_id") or "") not in weapons
    ]
    sins = {str(row.get("id")) for _, row in rows if _is_sin(row)}

    def one(bucket: str, row: dict[str, Any]) -> dict[str, Any]:
        name = str(row.get("name") or "")
        custom = str(row.get("custom_name") or "")
        shown = custom or tr(name, "gear")
        extra = str(row.get("extra") or "")
        category = str(row.get("category") or "")
        qty = _rounds(row, cost_for)
        item: dict[str, Any] = {
            "guid": str(row.get("id") or ""),
            "sourceid": str(row.get("gear_id") or ""),
            "name": shown,
            "name_english": custom or name,
            "fullname": _fullname(shown, extra),
            "fullname_english": _fullname(custom or name, extra),
            "extra": extra or None,
            "category": tr(category),
            "category_english": category,
            "rating": str(int(row.get("rating") or 0)),
            "qty": str(qty),
            "avail": str(row.get("avail") or ""),
            "owncost": _money(row.get("nuyen")),
            "equipped": "True",
            "iscommlink": _flag(bucket in _DEVICE_BUCKETS),
            "issin": _flag(_is_sin(row)),
            "isammo": _flag(category == "Ammunition"),
            "source": str(row.get("source") or ""),
            "page": str(row.get("page") or ""),
        }
        if bucket in _DEVICE_BUCKETS:
            item["devicerating"] = str(int(row.get("device_rating") or 0))
            for key in ("attack", "sleaze", "dataprocessing", "firewall"):
                item[key] = str(int(row.get(key) or 0))
        return item

    out: list[dict[str, Any]] = []
    licenses: dict[str, list[dict[str, Any]]] = {}
    for bucket, row in rows:
        parent = str(row.get("parent_id") or "")
        if parent in sins and row.get("category") == "ID/Credsticks":
            licenses.setdefault(parent, []).append(one(bucket, row))
        else:
            out.append(one(bucket, row))
    for item in out:
        if item["guid"] in licenses:
            item["children"] = {"gear": licenses[item["guid"]]}
    return out
