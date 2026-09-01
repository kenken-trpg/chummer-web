"""Armor + armor-mod loaders."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from .._xml import DATA_DIR, _int, _text
from ..bonus import parse_bonus
from ..formulas import _is_variable_cost


def _armor_included_mods(el: ET.Element) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for name_el in el.findall("./mods/name"):
        name = _text(name_el)
        if not name:
            continue
        rating = 1
        raw = name_el.attrib.get("rating") or ""
        if raw:
            try:
                rating = int(float(raw))
            except ValueError:
                rating = 1
        items.append({"name": name, "rating": max(1, rating)})
    return items


def _armor_mod_required(el: ET.Element | None) -> dict[str, list[str]]:
    names: list[str] = []
    mods: list[str] = []
    if el is None:
        return {"names": names, "mods": mods}
    for child in el.findall("./parentdetails/name"):
        text = _text(child)
        if text:
            names.append(text)
    for child in el.findall(".//armormod"):
        text = _text(child)
        if text:
            mods.append(text)
    return {"names": names, "mods": mods}


def load_armor() -> list[dict[str, Any]]:
    path = DATA_DIR / "armor.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./armors/armor"):
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        armor_id = _text(el.find("id"))
        cost = _text(el.find("cost"), "0")
        if not name or not armor_id or _is_variable_cost(cost):
            continue
        armor_raw = _text(el.find("armor"), "0")
        rating_max = _int(el.find("rating"), 0)
        items.append(
            {
                "id": armor_id,
                "name": name,
                "category": _text(el.find("category"), "Armor"),
                "armor": armor_raw,
                "armorcapacity": _text(el.find("armorcapacity")),
                "avail": _text(el.find("avail")),
                "cost": cost,
                "minrating": 1 if rating_max > 0 else 0,
                "maxrating": rating_max,
                "additive": armor_raw.startswith("+") or armor_raw.startswith("-"),
                "addmodcategories": [_text(c) for c in el.findall("addmodcategory") if _text(c)],
                "included_mods": _armor_included_mods(el),
                "bonus": parse_bonus(el.find("bonus")),
                "wirelessbonus": parse_bonus(el.find("wirelessbonus")),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def load_armor_mods() -> list[dict[str, Any]]:
    path = DATA_DIR / "armor.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./mods/mod"):
        name = _text(el.find("name"))
        mod_id = _text(el.find("id"))
        cost = _text(el.find("cost"), "0")
        if not name or not mod_id or name.startswith("ID ERROR"):
            continue
        rating_max = _int(el.find("maxrating"), 0) or _int(el.find("rating"), 0)
        hidden = el.find("hide") is not None
        bonus_el = el.find("bonus")
        unique = (bonus_el.attrib.get("unique") or "") if bonus_el is not None else ""
        required = _armor_mod_required(el.find("required"))
        items.append(
            {
                "id": mod_id,
                "name": name,
                "category": _text(el.find("category"), "General"),
                "armor": _text(el.find("armor"), "0"),
                "armorcapacity": _text(el.find("armorcapacity")),
                "avail": _text(el.find("avail")),
                "cost": cost,
                "minrating": 1 if rating_max > 1 else 0,
                "maxrating": rating_max,
                "purchasable": (not hidden and not _is_variable_cost(cost) and cost.strip() not in {"0", ""}),
                "unique": unique,
                "required_names": list(required.get("names") or []),
                "required_mods": list(required.get("mods") or []),
                "bonus": parse_bonus(bonus_el),
                "wirelessbonus": parse_bonus(el.find("wirelessbonus")),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items
