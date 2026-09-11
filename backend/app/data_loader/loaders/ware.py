"""Cyberware / bioware grades + item lists."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from .._xml import _float, _int, _text, data_root
from ..bonus import (
    _parent_name_requirements,
    parse_bonus,
    parse_required,
)
from ..formulas import parse_capacity

CORE_GRADES = ("Standard", "Used", "Alphaware", "Betaware", "Deltaware")


ADAPSIN_SUFFIX = " (Adapsin)"


def _attr(el: ET.Element | None, name: str) -> str:
    return str(el.get(name) or "") if el is not None else ""


def _load_grades(root: ET.Element) -> list[dict[str, Any]]:
    """The grade table, with the Adapsin twins folded into their base grade.

    ``cyberware.xml`` ships every grade twice — "Alphaware" and "Alphaware
    (Adapsin)" — because Chummer models the Adapsin bioware by swapping the
    grade under the character. That is not a grade anyone picks, so the twins
    never reach the picker: each base grade carries its Adapsin essence
    multiplier in ``ess_adapsin`` instead, and the engine chooses between the
    two. The numbers have to come from the file — the discount is neither a
    clean multiply nor a clean subtraction (Standard 1 → 0.9 and Used 1.25 →
    1.125 are ×0.9, but Alphaware 0.8 → 0.7 is −0.1).
    """
    grades: list[dict[str, Any]] = []
    adapsin: dict[str, float] = {}
    for el in root.findall("./grades/grade"):
        name = _text(el.find("name"))
        if not name:
            continue
        if name.endswith(ADAPSIN_SUFFIX):
            adapsin[name[: -len(ADAPSIN_SUFFIX)]] = _float(el.find("ess"), 1.0)
            continue
        grades.append(
            {
                "id": _text(el.find("id")),
                "name": name,
                "ess": _float(el.find("ess"), 1.0),
                "cost": _float(el.find("cost"), 1.0),
                "avail": _text(el.find("avail")),
                "source": _text(el.find("source")),
                "core": name in CORE_GRADES,
            }
        )
    for grade in grades:
        grade["ess_adapsin"] = adapsin.get(str(grade["name"]), grade["ess"])
    return grades


def _load_ware_items(root: ET.Element, xpath: str, default_category: str) -> list[dict[str, Any]]:
    items = []
    for el in root.findall(xpath):
        # Chummer hides the ware nothing may buy (Busted Ware, a metavariant's
        # claws). It stays in the catalog so a `<addware>` grant can name it,
        # and `catalog_view` keeps it out of the pickers.
        hidden = el.find("hide") is not None
        name = _text(el.find("name"))
        if not name:
            continue
        cap_raw = _text(el.find("capacity"))
        plugin, cap_expr = parse_capacity(cap_raw)
        rating_raw = _text(el.find("rating"))
        min_raw = _text(el.find("minrating"))
        formula_rating = "{" in rating_raw or "{" in min_raw
        max_rating = 1 if formula_rating else _int(el.find("rating"), 1)
        min_rating = 1 if formula_rating else _int(el.find("minrating"), 1)
        if max_rating <= 0:
            max_rating = 1
        minrating_expr = min_raw or str(min_rating)
        maxrating_expr = rating_raw or str(max_rating)
        subs_el = el.find("subsystems")
        subsystems = [
            _text(sub.find("name")) for sub in list(subs_el if subs_el is not None else []) if _text(sub.find("name"))
        ]
        items.append(
            {
                "id": _text(el.find("id")),
                "name": name,
                "hidden": hidden,
                "category": _text(el.find("category"), default_category),
                "ess": _text(el.find("ess"), "0"),
                "cost": _text(el.find("cost"), "0"),
                "avail": _text(el.find("avail")),
                "capacity": cap_expr,
                "minrating": min_rating,
                "maxrating": max_rating,
                "minrating_expr": minrating_expr,
                "maxrating_expr": maxrating_expr,
                "forcegrade": _text(el.find("forcegrade")) or None,
                "plugin": plugin,
                "requireparent": el.find("requireparent") is not None,
                "addtoparentess": el.find("addtoparentess") is not None,
                "formula_rating": formula_rating,
                "allow_subsystems": [_text(c) for c in el.findall("./allowsubsystems/category") if _text(c)],
                "subsystems": subsystems,
                "bonus": parse_bonus(el.find("bonus")),
                "wirelessbonus": parse_bonus(el.find("wirelessbonus")),
                "pairbonus": parse_bonus(el.find("pairbonus")),
                "pairinclude": [_text(n) for n in el.findall("./pairinclude/name") if _text(n)],
                "wirelesspairbonus": parse_bonus(el.find("wirelesspairbonus")),
                "wirelesspairmode": _attr(el.find("wirelesspairbonus"), "mode"),
                "wirelesspairinclude": [_text(n) for n in el.findall("./wirelesspairinclude/name") if _text(n)],
                "bannedgrades": [_text(g) for g in el.findall("./bannedgrades/grade") if _text(g)],
                "required": parse_required(el.find("required")),
                "required_parent_names": _parent_name_requirements(el),
                "limbslot": _text(el.find("limbslot")) or None,
                "selectside": el.find("selectside") is not None,
                "limbslotcount": _text(el.find("limbslotcount")) or "1",
                "add_weapon": _text(el.find("addweapon")),
                "devicerating": _text(el.find("devicerating")),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def load_cyberware() -> dict[str, Any]:
    root = data_root("cyberware.xml")
    if root is None:
        return {"grades": [], "items": []}
    root = root
    return {"grades": _load_grades(root), "items": _load_ware_items(root, "./cyberwares/cyberware", "Bodyware")}


def load_bioware() -> dict[str, Any]:
    root = data_root("bioware.xml")
    if root is None:
        return {"grades": [], "items": []}
    root = root
    return {"grades": _load_grades(root), "items": _load_ware_items(root, "./biowares/bioware", "Basic")}
