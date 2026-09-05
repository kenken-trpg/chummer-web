"""Active + knowledge skill list."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from .._xml import DATA_DIR, _text


def _skill_specs(el: ET.Element) -> list[str]:
    specs: list[str] = []
    seen: set[str] = set()
    for node in el.findall("./specs/spec"):
        name = _text(node)
        if not name or name in seen:
            continue
        seen.add(name)
        specs.append(name)
    return specs


def load_skills() -> dict[str, Any]:
    tree = ET.parse(DATA_DIR / "skills.xml")
    root = tree.getroot()
    # SR5 p.130 and the official sheet both list skill groups alphabetically;
    # the vendored file is alphabetical except that Engineering sits after
    # Influence, so sort rather than trusting document order.
    groups = sorted(_text(g) for g in root.findall("./skillgroups/name") if _text(g))
    # The rulebook's chapter order (Combat, Physical, Social, Magical,
    # Resonance, Technical, Vehicle) — which is what `<categories>` already
    # holds. Skills come out of the file grouped by category in a *different*
    # order, so the UI needs this list to sort by.
    active_categories = [
        _text(c) for c in root.findall("./categories/category") if c.get("type") == "active" and _text(c)
    ]
    skills = []
    for el in root.findall("./skills/skill"):
        exotic = _text(el.find("exotic"), "False").lower() == "true"
        skills.append(
            {
                "id": _text(el.find("id")),
                "name": _text(el.find("name")),
                "attribute": _text(el.find("attribute")).upper(),
                "category": _text(el.find("category")),
                "skillgroup": _text(el.find("skillgroup")) or None,
                "exotic": exotic,
                "default": _text(el.find("default"), "True").lower() == "true",
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
                "knowledge": False,
                "specs": _skill_specs(el),
            }
        )
    knowledge = []
    for el in root.findall("./knowledgeskills/skill"):
        knowledge.append(
            {
                "id": _text(el.find("id")),
                "name": _text(el.find("name")),
                "attribute": (_text(el.find("attribute")) or _text(el.find("defaultattribute")) or "INT").upper(),
                "category": _text(el.find("category"), "Street"),
                "skillgroup": None,
                "exotic": False,
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
                "knowledge": True,
                "specs": _skill_specs(el),
            }
        )
    return {
        "groups": groups,
        "active_categories": active_categories,
        "skills": skills,
        "knowledge": knowledge,
    }
