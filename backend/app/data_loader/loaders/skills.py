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
    groups = [_text(g) for g in root.findall("./skillgroups/name") if _text(g)]
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
    return {"groups": groups, "skills": skills, "knowledge": knowledge}
