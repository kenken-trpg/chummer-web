"""Priority-table loader."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from .._xml import DATA_DIR, _child, _int, _text


def load_priorities() -> list[dict[str, Any]]:
    tree = ET.parse(DATA_DIR / "priorities.xml")
    rows = []
    for el in tree.getroot().findall("./priorities/priority"):
        category = _text(el.find("category"))
        value = _text(el.find("value"))
        if not category or not value:
            continue
        row: dict[str, Any] = {
            "id": _text(el.find("id")),
            "name": _text(el.find("name")),
            "category": category,
            "value": value,
            "gameplay": _text(_child(el, "gameplay", "prioritytable"), "Standard"),
        }
        if category == "Heritage":
            mets = []
            for m in el.findall("./metatypes/metatype"):
                mets.append(
                    {
                        "name": _text(m.find("name")),
                        "special": _int(m.find("value")),
                        "karma": _int(m.find("karma")),
                        "variants": [
                            {
                                "name": _text(v.find("name")),
                                "special": _int(v.find("value"), _int(m.find("value"))),
                                "karma": _int(v.find("karma")),
                            }
                            for v in m.findall("./metavariants/metavariant")
                        ],
                    }
                )
            row["metatypes"] = mets
        elif category == "Attributes":
            row["attribute_points"] = _int(el.find("attributes"))
        elif category == "Skills":
            row["skill_points"] = _int(el.find("skills"))
            row["skill_group_points"] = _int(el.find("skillgroups"))
        elif category == "Resources":
            row["nuyen"] = _int(el.find("resources"))
        elif category == "Talent":
            talents = []
            for t in el.findall("./talents/talent"):
                magic = _int(t.find("magic"))
                resonance = _int(t.find("resonance"))
                talents.append(
                    {
                        "name": _text(t.find("value")) or _text(t.find("name")),
                        "label": _text(t.find("name")),
                        "magic": magic,
                        "resonance": resonance,
                        "value": magic or resonance,
                        "quality": _text(t.find("./qualities/quality")),
                        "spells": _int(t.find("spells")),
                        "cfp": _int(t.find("cfp")),
                    }
                )
            row["talents"] = talents
        rows.append(row)
    return rows
