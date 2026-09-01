"""Vehicle, vehicle-mod, weapon-mount and drone loaders."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from .._xml import DATA_DIR, _int, _text
from ..bonus import parse_bonus
from ..formulas import _is_variable_cost


def _vehicle_constraints(el: ET.Element | None) -> dict[str, Any]:
    names: list[str] = []
    category_contains: list[str] = []
    category_equals: list[str] = []
    body_lte: int | None = None
    body_gte: int | None = None
    if el is None:
        return {
            "names": names,
            "category_contains": category_contains,
            "category_equals": category_equals,
            "body_lte": body_lte,
            "body_gte": body_gte,
        }
    for details in el.findall("vehicledetails"):
        for child in list(details):
            text = _text(child)
            if not text:
                continue
            op = child.attrib.get("operation") or ""
            if child.tag == "name":
                names.append(text)
            elif child.tag == "category":
                if op == "contains":
                    category_contains.append(text)
                else:
                    category_equals.append(text)
            elif child.tag == "body":
                try:
                    value = int(float(text))
                except ValueError:
                    continue
                if op == "lessthanequals":
                    body_lte = value
                elif op in {"greaterthan", "greaterthanorequals"}:
                    body_gte = value
    return {
        "names": names,
        "category_contains": category_contains,
        "category_equals": category_equals,
        "body_lte": body_lte,
        "body_gte": body_gte,
    }


def _mount_part_requirements(el: ET.Element | None) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"control": [], "flexibility": [], "visibility": []}
    if el is None:
        return out
    for details in el.findall("weaponmountdetails"):
        for child in list(details):
            text = _text(child)
            if child.tag in out and text:
                out[child.tag].append(text)
    return out


def load_vehicle_names() -> list[str]:
    path = DATA_DIR / "vehicles.xml"
    if not path.exists():
        return []
    names: list[str] = []
    for el in ET.parse(path).getroot().findall("./vehicles/vehicle"):
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        if name and not name.startswith("ID ERROR"):
            names.append(name)
    return names


def load_vehicle_mods() -> list[dict[str, Any]]:
    path = DATA_DIR / "vehicles.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./mods/mod"):
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        mod_id = _text(el.find("id"))
        cost = _text(el.find("cost"), "0")
        if not name or not mod_id or name.startswith("ID ERROR"):
            continue
        rating_raw = _text(el.find("rating"))
        min_raw = _text(el.find("minrating"))
        qty_rating = rating_raw.lower() == "qty"
        rating_max = _int(el.find("rating"), 0) if rating_raw.isdigit() else 0
        subs_el = el.find("subsystems")
        items.append(
            {
                "id": mod_id,
                "name": name,
                "category": _text(el.find("category")),
                "avail": _text(el.find("avail")),
                "cost": cost,
                "slots": _text(el.find("slots"), "0"),
                "rating": rating_raw,
                "minrating": _int(el.find("minrating"), 1) if rating_max > 0 else 0,
                "maxrating": rating_max,
                "minrating_expr": min_raw,
                "maxrating_expr": rating_raw if rating_raw and not rating_raw.isdigit() else "",
                "purchasable": not _is_variable_cost(cost) and not qty_rating and cost.strip() not in {"0", ""},
                "bonus": parse_bonus(el.find("bonus")),
                "required": _vehicle_constraints(el.find("required")),
                "forbidden": _vehicle_constraints(el.find("forbidden")),
                "optionaldrone": el.find("optionaldrone") is not None,
                "capacity": _text(el.find("capacity")),
                "subsystems": [
                    _text(sub)
                    for sub in list(subs_el if subs_el is not None else [])
                    if sub.tag == "subsystem" and _text(sub)
                ],
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def load_weapon_mounts() -> list[dict[str, Any]]:
    path = DATA_DIR / "vehicles.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./weaponmounts/weaponmount"):
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        mount_id = _text(el.find("id"))
        cost = _text(el.find("cost"), "0")
        if not name or not mount_id or name.startswith("ID ERROR") or _is_variable_cost(cost):
            continue
        required = el.find("required")
        forbidden = el.find("forbidden")
        items.append(
            {
                "id": mount_id,
                "name": name,
                "category": _text(el.find("category")),
                "avail": _text(el.find("avail")),
                "cost": cost,
                "slots": _text(el.find("slots"), "0"),
                "required": _vehicle_constraints(required),
                "forbidden": _vehicle_constraints(forbidden),
                "required_parts": _mount_part_requirements(required),
                "forbidden_parts": _mount_part_requirements(forbidden),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def _drone_included_gears(el: ET.Element) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for gift in el.findall("./gears/gear"):
        name = _text(gift.find("name")) or _text(gift)
        if not name:
            continue
        items.append(
            {
                "name": name,
                "category": _text(gift.find("category")),
                "rating": max(1, _int(gift.find("rating"), 1)),
                "maxrating": _int(gift.find("maxrating"), 0),
            }
        )
    return items


def _drone_included_mods(el: ET.Element) -> list[str]:
    return [_text(node) for node in el.findall("./mods/name") if _text(node)]


def _drone_included_mounts(el: ET.Element) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for node in el.findall("./weaponmounts/weaponmount"):
        items.append(
            {
                "size": _text(node.find("size")),
                "visibility": _text(node.find("visibility")),
                "flexibility": _text(node.find("flexibility")),
                "control": _text(node.find("control")),
                "allowedweapons": _text(node.find("allowedweapons")),
            }
        )
    return items


def _load_vehicle_entries(*, drones: bool) -> list[dict[str, Any]]:
    path = DATA_DIR / "vehicles.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./vehicles/vehicle"):
        if el.find("hide") is not None:
            continue
        category = _text(el.find("category"))
        if category.startswith("Drones") != drones:
            continue
        name = _text(el.find("name"))
        vehicle_id = _text(el.find("id"))
        cost = _text(el.find("cost"), "0")
        if (
            not name
            or not vehicle_id
            or name.startswith("ID ERROR")
            or _is_variable_cost(cost)
            or cost.strip() in {"0", ""}
        ):
            continue
        items.append(
            {
                "id": vehicle_id,
                "name": name,
                "category": category,
                "handling": _text(el.find("handling")),
                "speed": _text(el.find("speed")),
                "accel": _text(el.find("accel")),
                "body": _text(el.find("body")),
                "armor": _text(el.find("armor")),
                "pilot": _text(el.find("pilot")),
                "sensor": _text(el.find("sensor")),
                "seats": _text(el.find("seats")),
                "avail": _text(el.find("avail")),
                "cost": cost,
                "included_gears": _drone_included_gears(el),
                "included_mods": _drone_included_mods(el),
                "included_weaponmounts": _drone_included_mounts(el),
                "modslots": _int(el.find("modslots")) if _text(el.find("modslots")) else None,
                "powertrainmodslots": _int(el.find("powertrainmodslots")),
                "protectionmodslots": _int(el.find("protectionmodslots")),
                "weaponmodslots": _int(el.find("weaponmodslots")),
                "bodymodslots": _int(el.find("bodymodslots")),
                "electromagneticmodslots": _int(el.find("electromagneticmodslots")),
                "cosmeticmodslots": _int(el.find("cosmeticmodslots")),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def load_drones() -> list[dict[str, Any]]:
    return _load_vehicle_entries(drones=True)


def load_vehicles() -> list[dict[str, Any]]:
    return _load_vehicle_entries(drones=False)
