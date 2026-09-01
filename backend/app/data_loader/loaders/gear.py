"""Commlink / cyberdeck / RCC / optics / gear / program / app / sensor loaders."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from .._xml import DATA_DIR, _int, _text
from ..bonus import _parse_weaponbonus, parse_bonus
from ..formulas import _is_variable_cost, parse_capacity, split_capacity


def _is_pi_tac_commlink(name: str, category: str) -> bool:
    return category == "PI-Tac" and name.startswith("PI-Tac")


def load_commlinks() -> list[dict[str, Any]]:
    path = DATA_DIR / "gear.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./gears/gear"):
        category = _text(el.find("category"))
        name = _text(el.find("name"))
        if category != "Commlinks" and not _is_pi_tac_commlink(name, category):
            continue
        if el.find("hide") is not None:
            continue
        gear_id = _text(el.find("id"))
        cost = _text(el.find("cost"), "0")
        if not name or not gear_id or _is_variable_cost(cost):
            continue
        rating_max = _int(el.find("rating"), 0)
        device = _text(el.find("devicerating"), "0")
        processing = _text(el.find("dataprocessing"))
        firewall = _text(el.find("firewall"))
        if _is_pi_tac_commlink(name, category):
            processing = processing or device
            firewall = firewall or device
        items.append(
            {
                "id": gear_id,
                "name": name,
                "category": category or "Commlinks",
                "cost": cost,
                "avail": _text(el.find("avail")),
                "minrating": _int(el.find("minrating"), 1) if rating_max > 0 else 0,
                "maxrating": rating_max,
                "devicerating": device,
                "dataprocessing": processing or "0",
                "firewall": firewall or "0",
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def _load_gear_categories(categories: set[str], *, allow_brackets: bool = False) -> list[dict[str, Any]]:
    path = DATA_DIR / "gear.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./gears/gear"):
        if el.find("hide") is not None:
            continue
        category = _text(el.find("category"))
        if category not in categories:
            continue
        name = _text(el.find("name"))
        gear_id = _text(el.find("id"))
        cost = _text(el.find("cost"), "0")
        if not name or not gear_id or name.startswith("ID ERROR") or _is_variable_cost(cost):
            continue
        if name.startswith("[") and not allow_brackets:
            continue
        rating_max = _int(el.find("rating"), 0)
        cap_raw = _text(el.find("capacity"))
        plugin, cap_expr = parse_capacity(cap_raw)
        _plugin_only, host_expr, plugin_expr = split_capacity(cap_raw)
        included: list[dict[str, Any]] = []
        ammo_types = [part.strip() for part in _text(el.find("ammoforweapontype")).split(",") if part.strip()]
        weapon_details = ""
        bonus_el = el.find("bonus")
        if bonus_el is not None:
            select = bonus_el.find("selectweapon")
            if select is not None:
                weapon_details = (select.attrib.get("weapondetails") or _text(select)).strip()
        for gift in el.findall("./gears/usegear"):
            gift_name = _text(gift.find("name"))
            if not gift_name:
                continue
            included.append(
                {
                    "name": gift_name,
                    "category": _text(gift.find("category")),
                    "rating": max(1, _int(gift.find("rating"), 1)),
                    "capacity": _text(gift.find("capacity")),
                }
            )
        items.append(
            {
                "id": gear_id,
                "name": name,
                "category": category,
                "cost": cost,
                "avail": _text(el.find("avail")),
                "minrating": 1 if rating_max > 0 else 0,
                "maxrating": rating_max,
                "capacity": cap_expr,
                "plugin": plugin,
                "host_capacity": host_expr,
                "plugin_capacity": plugin_expr,
                "requireparent": el.find("requireparent") is not None,
                "addoncategories": [_text(c) for c in el.findall("addoncategory") if _text(c)],
                "required_names": [
                    _text(n)
                    for n in (
                        el.findall("./required/geardetails//name")
                        if el.find("./required/geardetails") is not None
                        else []
                    )
                    if _text(n)
                ],
                "required_categories": [
                    _text(n)
                    for n in (
                        el.findall("./required/geardetails//category")
                        if el.find("./required/geardetails") is not None
                        else []
                    )
                    if _text(n)
                ],
                "included": included,
                "ammo_weapon_types": ammo_types,
                "costfor": max(0, _int(el.find("costfor"), 0)),
                "weapon_details": weapon_details,
                "add_weapon": _text(el.find("addweapon")),
                "weaponbonus": _parse_weaponbonus(el.find("weaponbonus")),
                "bonus": parse_bonus(el.find("bonus")),
                "devicerating": _text(el.find("devicerating"), "0"),
                "attack": _text(el.find("attack"), "0"),
                "sleaze": _text(el.find("sleaze"), "0"),
                "dataprocessing": _text(el.find("dataprocessing"), "0"),
                "firewall": _text(el.find("firewall"), "0"),
                "attributearray": _text(el.find("attributearray")),
                "programs": _text(el.find("programs"), "0"),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def load_cyberdecks() -> list[dict[str, Any]]:
    return _load_gear_categories({"Cyberdecks"})


def load_rccs() -> list[dict[str, Any]]:
    return _load_gear_categories({"Rigger Command Consoles"})


def load_optics() -> list[dict[str, Any]]:
    return _load_gear_categories({"Vision Devices", "Audio Devices", "Vision Enhancements", "Audio Enhancements"})


PROGRAM_HOSTS = {
    "Common Programs": "cyberdecks",
    "Hacking Programs": "cyberdecks",
    "Autosofts": "rccs",
}


def _extra_kind(bonus: list[dict[str, Any]] | None, name: str = "") -> str:
    if str(name or "").startswith("Group Autosoft"):
        return "group"
    tags = {node.get("tag") for node in (bonus or [])}
    if (
        "selectskill" in tags
        or "activesoft" in tags
        or "skillsoft" in tags
        or "knowsoft" in tags
        or "linguasoft" in tags
    ):
        return "skill"
    if "selecttext" in tags or "selectrestricted" in tags or "selecttradition" in tags:
        return "text"
    return ""


GEAR_SPECIALIZED_CATEGORIES = {
    "Commlinks",
    "Cyberdecks",
    "Rigger Command Consoles",
    "Vision Devices",
    "Audio Devices",
    "Vision Enhancements",
    "Audio Enhancements",
    "Common Programs",
    "Hacking Programs",
    "Autosofts",
    "Software",
    "Sensors",
    "Sensor Housings",
    "Sensor Functions",
}

GEAR_SKIP_CATEGORIES = GEAR_SPECIALIZED_CATEGORIES | {
    "Foci",
    "Formulae",
    "Custom",
    "Custom Cyberdeck Attributes",
    "Custom Drug",
    "Paydata",
    "Commlink Apps",
    "Electronic Modification",
    "Drug Grades",
    "Currency",
}

GEAR_RATING_CAP = 24


def load_gear() -> list[dict[str, Any]]:
    path = DATA_DIR / "gear.xml"
    if not path.exists():
        return []
    cats: set[str] = set()
    for el in ET.parse(path).getroot().findall("./gears/gear"):
        cat = _text(el.find("category"))
        if cat:
            cats.add(cat)
    items: list[dict[str, Any]] = []
    for item in _load_gear_categories(cats - GEAR_SKIP_CATEGORIES):
        cost = str(item.get("cost") or "").strip()
        if "Parent Cost" in cost:
            continue
        if cost.lstrip().startswith("+"):
            item["requireparent"] = True
        if item.get("required_names") or item.get("required_categories"):
            item["requireparent"] = True
        if _is_pi_tac_commlink(str(item.get("name") or ""), str(item.get("category") or "")):
            continue
        if item.get("category") == "PI-Tac Programs":
            item["requireparent"] = True
        if cost in {"0", ""} and not item.get("requireparent"):
            continue
        rating_max = int(item.get("maxrating") or 0)
        if rating_max > GEAR_RATING_CAP:
            item["maxrating"] = 12
            item["minrating"] = 1
        name = item.get("name") or ""
        item["extra_kind"] = _extra_kind(item.get("bonus"), name)
        item["needs_extra"] = bool(item["extra_kind"])
        items.append(item)
    return items


def load_programs() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in _load_gear_categories(
        {"Common Programs", "Hacking Programs", "Autosofts"},
        allow_brackets=True,
    ):
        name = item.get("name") or ""
        if name.startswith("[") and item.get("category") != "Autosofts":
            continue
        if "Parent Cost" in (item.get("cost") or ""):
            continue
        item["requireparent"] = True
        item["program_host"] = PROGRAM_HOSTS.get(item.get("category") or "", "cyberdecks")
        item["extra_kind"] = _extra_kind(item.get("bonus"), name)
        item["needs_extra"] = bool(item["extra_kind"])
        items.append(item)
    return items


def load_apps() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in _load_gear_categories({"Software"}):
        if "Parent Cost" in (item.get("cost") or ""):
            continue
        if (item.get("cost") or "").strip() in {"0", ""}:
            continue
        item["requireparent"] = True
        item["extra_kind"] = _extra_kind(item.get("bonus"), item.get("name") or "")
        item["needs_extra"] = bool(item["extra_kind"])
        items.append(item)
    return items


def load_sensors() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in _load_gear_categories({"Sensors", "Sensor Housings", "Sensor Functions"}):
        if "Parent Cost" in (item.get("cost") or ""):
            continue
        item["requireparent"] = item.get("category") == "Sensor Functions"
        items.append(item)
    return items
