"""Foci, the formulae used to craft them, and what initiation grants.

Metamagics and magic arts live with foci rather than with spells: they are all
things bought with an initiation grade rather than with karma or nuyen.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from ..._xml import DATA_DIR, _int, _text
from ...bonus import parse_bonus, parse_required, parse_requirement_tree


def _focus_effect(nodes: list[dict[str, Any]]) -> str:
    bits: list[str] = []
    for node in nodes:
        tag = node.get("tag") or ""
        fields = node.get("fields") or {}
        if tag == "specificskill":
            name = str(fields.get("name") or "").strip()
            if name:
                bits.append(f"{name} +Rating")
        elif tag == "skillattribute":
            name = str(fields.get("name") or "").strip()
            if name:
                bits.append(f"{name} skills +Rating")
        elif tag == "spellcategory":
            name = str(fields.get("name") or "").strip()
            if name:
                bits.append(f"{name} spells +Rating")
        elif tag == "weaponspecificdice":
            kind = str((node.get("attrs") or {}).get("type") or "Melee").strip() or "Melee"
            bits.append(f"{kind} weapon +Rating")
    return " / ".join(bits)


def _focus_weapon_type(nodes: list[dict[str, Any]]) -> str:
    for node in nodes:
        if node.get("tag") != "weaponspecificdice":
            continue
        return str((node.get("attrs") or {}).get("type") or "Melee").strip() or "Melee"
    return ""


def load_foci() -> list[dict[str, Any]]:
    path = DATA_DIR / "gear.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./gears/gear"):
        if _text(el.find("category")) != "Foci":
            continue
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        gear_id = _text(el.find("id"))
        if not name or not gear_id:
            continue
        if name == "Qi Focus" or "Individualized" in name or "Formula" in name:
            continue
        bonus = parse_bonus(el.find("bonus"))
        weapon_type = _focus_weapon_type(bonus)
        items.append(
            {
                "id": gear_id,
                "name": name,
                "category": "Foci",
                "maxrating": _int(el.find("rating"), 6),
                "cost": _text(el.find("cost"), "Rating * 4000"),
                "avail": _text(el.find("avail")),
                "bonus": bonus,
                "effect": _focus_effect(bonus),
                "needs_weapon": bool(weapon_type),
                "weapon_type": weapon_type,
                "formula": None,
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    formulae = load_focus_formulae()
    for item in items:
        formula = formulae.get(item["name"])
        if formula:
            item["formula"] = formula
    return items


def _focus_name_from_formula(name: str) -> str:
    return name.replace(" Formula", "", 1)


def load_focus_formulae() -> dict[str, dict[str, Any]]:
    path = DATA_DIR / "gear.xml"
    if not path.exists():
        return {}
    items: dict[str, dict[str, Any]] = {}
    for el in ET.parse(path).getroot().findall("./gears/gear"):
        if _text(el.find("category")) != "Formulae":
            continue
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        if "Focus Formula" not in name or "Individualized" in name:
            continue
        focus_name = _focus_name_from_formula(name)
        items[focus_name] = {
            "id": _text(el.find("id")),
            "name": name,
            "cost": _text(el.find("cost"), "Rating * 1000"),
            "source": _text(el.find("source")),
            "page": _text(el.find("page")),
        }
    return items


def load_metamagics() -> list[dict[str, Any]]:
    path = DATA_DIR / "metamagic.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./metamagics/metamagic"):
        name = _text(el.find("name"))
        mid = _text(el.find("id"))
        if not name or not mid:
            continue
        items.append(
            {
                "id": mid,
                "name": name,
                "adept": _text(el.find("adept"), "False").lower() == "true",
                "magician": _text(el.find("magician"), "False").lower() == "true",
                "repeatable": _text(el.find("limit"), "True").lower() == "false",
                "bonus": parse_bonus(el.find("bonus")),
                "required_tree": parse_requirement_tree(el.find("required")),
                "required": parse_required(el.find("required")),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def load_magic_arts() -> list[dict[str, Any]]:
    path = DATA_DIR / "metamagic.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./arts/art"):
        name = _text(el.find("name"))
        art_id = _text(el.find("id"))
        if not name or not art_id:
            continue
        items.append(
            {
                "id": art_id,
                "name": name,
                "bonus": parse_bonus(el.find("bonus")),
                "required_tree": parse_requirement_tree(el.find("required")),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items
