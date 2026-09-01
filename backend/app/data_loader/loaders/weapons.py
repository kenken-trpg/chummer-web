"""Weapon, range, weapon-accessory loaders."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from .._xml import DATA_DIR, _int, _text
from ..formulas import _is_variable_cost

SKIP_WEAPON_CATEGORIES = {
    "Cyberweapon",
    "Bio-Weapon",
    "Quality",
    "Underbarrel Weapons",
    "Micro-Drone Weapons",
}


def _weapon_category_types(root: ET.Element) -> dict[str, str]:
    types: dict[str, str] = {}
    for el in root.findall("./categories/category"):
        name = _text(el)
        kind = (el.attrib.get("type") or "").strip()
        if name and kind:
            types[name] = kind
    return types


def load_weapons() -> list[dict[str, Any]]:
    path = DATA_DIR / "weapons.xml"
    if not path.exists():
        return []
    root = ET.parse(path).getroot()
    category_types = _weapon_category_types(root)
    items: list[dict[str, Any]] = []
    for el in root.findall("./weapons/weapon"):
        hidden = el.find("hide") is not None
        from_cyberware = _text(el.find("cyberware")).lower() == "true"
        if hidden and not from_cyberware:
            continue
        name = _text(el.find("name"))
        weapon_id = _text(el.find("id"))
        category = _text(el.find("category"))
        cost = _text(el.find("cost"), "0")
        if not name or not weapon_id or category in SKIP_WEAPON_CATEGORIES or _is_variable_cost(cost):
            continue
        weapon_type = _text(el.find("weapontype")) or category_types.get(category) or category.lower()
        items.append(
            {
                "id": weapon_id,
                "name": name,
                "category": category,
                "type": _text(el.find("type")),
                "weapon_type": weapon_type,
                "accuracy": _text(el.find("accuracy")),
                "reach": _text(el.find("reach")),
                "damage": _text(el.find("damage")),
                "ap": _text(el.find("ap")),
                "mode": _text(el.find("mode")),
                "rc": _text(el.find("rc")),
                "ammo": _text(el.find("ammo")),
                "conceal": _text(el.find("conceal")),
                "avail": _text(el.find("avail")),
                "cost": cost,
                "range": _text(el.find("range")) or None,
                "alt_range": _text(el.find("alternaterange")) or None,
                "mounts": [_text(m) for m in el.findall("./accessorymounts/mount") if _text(m)],
                "included": [
                    _text(a.find("name")) for a in el.findall("./accessories/accessory") if _text(a.find("name"))
                ],
                "hidden": hidden,
                "from_cyberware": from_cyberware,
                "useskill": _text(el.find("useskill")),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


_RANGE_BANDS = ("min", "short", "medium", "long", "extreme")


def load_weapon_ranges() -> dict[str, dict[str, str]]:
    """ranges.xml → {range name: {min/short/medium/long/extreme: formula}}.

    Formulas are kept as raw strings; firearm bands are literal integers,
    Strength-scaled bands (bows, thrown) use ``{STR}`` (e.g. ``{STR}*10``).
    """
    path = DATA_DIR / "ranges.xml"
    if not path.exists():
        return {}
    root = ET.parse(path).getroot()
    out: dict[str, dict[str, str]] = {}
    for el in root.findall("./ranges/range"):
        name = _text(el.find("name"))
        if not name:
            continue
        out[name] = {band: _text(el.find(band), "0") for band in _RANGE_BANDS}
    return out


def _weapon_constraints(el: ET.Element | None) -> dict[str, Any]:
    names: list[str] = []
    categories: list[str] = []
    types: list[str] = []
    accessories: list[str] = []
    conceal_lte: int | None = None
    if el is None:
        return {
            "names": names,
            "categories": categories,
            "types": types,
            "accessories": accessories,
            "conceal_lte": conceal_lte,
        }
    for child in el.iter():
        tag = child.tag
        text = _text(child)
        if tag == "name" and text:
            names.append(text)
        elif tag in {"category", "ammocategory"} and text:
            categories.append(text)
        elif tag == "type" and text:
            types.append(text)
        elif tag == "accessory" and text:
            accessories.append(text)
        elif tag == "conceal" and text:
            try:
                value = int(float(text))
            except ValueError:
                continue
            if (child.attrib.get("operation") or "") == "lessthanequals":
                conceal_lte = value
    return {
        "names": names,
        "categories": categories,
        "types": types,
        "accessories": accessories,
        "conceal_lte": conceal_lte,
    }


def load_weapon_accessories() -> list[dict[str, Any]]:
    path = DATA_DIR / "weapons.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./accessories/accessory"):
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        accessory_id = _text(el.find("id"))
        cost = _text(el.find("cost"), "0")
        if not name or not accessory_id or name.startswith("ID ERROR"):
            continue
        mount_raw = _text(el.find("mount"))
        rating_max = _int(el.find("rating"), 0)
        special_modification = _text(el.find("specialmodification")).lower() == "true"
        special_modification_cost = 0
        if special_modification:
            special_modification_cost = 1
            required_el = el.find("required")
            if required_el is not None:
                for child in required_el.iter("specialmodificationlimit"):
                    try:
                        special_modification_cost = max(1, int(_text(child) or "1"))
                    except ValueError:
                        continue
        items.append(
            {
                "id": accessory_id,
                "name": name,
                "mounts": [part for part in mount_raw.split("/") if part],
                "avail": _text(el.find("avail")),
                "cost": cost,
                "purchasable": not _is_variable_cost(cost) and cost.strip() not in {"0", ""},
                "accuracy": _text(el.find("accuracy")),
                "rc": _text(el.find("rc")),
                "conceal": _text(el.find("conceal")),
                "damage": _text(el.find("damage")),
                "ap": _text(el.find("ap")),
                "reach": _text(el.find("reach")),
                "modifyammocapacity": _text(el.find("modifyammocapacity")),
                "specialmodification": special_modification,
                "special_modification_cost": special_modification_cost,
                "minrating": 1 if rating_max > 0 else 0,
                "maxrating": rating_max,
                "required": _weapon_constraints(el.find("required")),
                "forbidden": _weapon_constraints(el.find("forbidden")),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items
