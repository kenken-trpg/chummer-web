"""Martial art + technique loaders."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from .._xml import DATA_DIR, _int, _text
from ..bonus import parse_bonus, parse_requirement_tree


def load_martial_art_techniques() -> list[dict[str, Any]]:
    path = DATA_DIR / "martialarts.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./techniques/technique"):
        name = _text(el.find("name"))
        tech_id = _text(el.find("id"))
        if not name or not tech_id:
            continue
        items.append(
            {
                "id": tech_id,
                "name": name,
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
                "bonus": parse_bonus(el.find("bonus")),
            }
        )
    return items


def load_martial_arts() -> list[dict[str, Any]]:
    path = DATA_DIR / "martialarts.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./martialarts/martialart"):
        name = _text(el.find("name"))
        art_id = _text(el.find("id"))
        if not name or not art_id:
            continue
        techniques = [
            tech_name for tech in el.findall("./techniques/technique") if (tech_name := _text(tech.find("name")))
        ]
        cost_el = el.find("cost")
        items.append(
            {
                "id": art_id,
                "name": name,
                "cost": _int(cost_el, 7) if cost_el is not None else 7,
                "is_quality": _text(el.find("isquality"), "False").lower() == "true",
                "all_techniques": el.find("alltechniques") is not None,
                "techniques": techniques,
                "bonus": parse_bonus(el.find("bonus")),
                "required_tree": parse_requirement_tree(el.find("required")),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items
