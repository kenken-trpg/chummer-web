"""Drug component + drug-grade loaders and the drug-effect summariser."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from .._xml import DATA_DIR, _text
from ..bonus import parse_bonus

_DRUG_LIMIT_LABEL = {"physical": "肉体上限", "mental": "精神上限", "social": "社会上限"}


def drug_node_value(node: dict[str, Any]) -> str:
    fields = node.get("fields") or {}
    return str(fields.get("value") or fields.get("val") or fields.get("bonus") or node.get("value") or "").strip()


def drug_effect_summary(nodes: list[dict[str, Any]]) -> str:
    """Human-readable one-liner for a drug's ``<bonus>`` nodes."""
    parts: list[str] = []
    for node in nodes or []:
        tag = node.get("tag")
        fields = node.get("fields") or {}
        val = drug_node_value(node)
        signed = val if val.startswith(("-", "+")) else (f"+{val}" if val else "")
        if tag == "attribute" and val:
            parts.append(f"{str(fields.get('name') or '').upper()} {signed}")
        elif tag == "limit" and val:
            label = _DRUG_LIMIT_LABEL.get(str(fields.get("name") or "").strip().lower(), str(fields.get("name") or ""))
            parts.append(f"{label} {signed}")
        elif tag in ("initiativedice", "initiativepass") and val:
            parts.append(f"イニシアチブ +{val}D6")
        elif tag == "initiative" and val:
            parts.append(f"イニシアチブ {signed}")
        elif tag == "specificskill" and val:
            parts.append(f"{str(fields.get('name') or '')} {signed}")
        elif tag == "quality":
            rating = (node.get("attrs") or {}).get("rating")
            name = str(node.get("value") or "")
            parts.append(f"資質 {name}" + (f"({rating})" if rating else ""))
    return " / ".join(p for p in parts if p.strip())


def load_drug_components() -> dict[str, dict[str, Any]]:
    """Mechanical data for premade drugs, keyed by the shared drug/gear id.

    ``drugcomponents.xml`` carries the ``<bonus>`` (attribute / limit /
    initiativedice / quality / specificskill), the ``<duration>`` formula
    (seconds, may use ``{BOD}`` / ``{D6}``), ``<speed>`` and ``<vectors>`` that
    the flat ``gear.xml`` ``Drugs`` entries omit.
    """
    path = DATA_DIR / "drugcomponents.xml"
    if not path.exists():
        return {}
    out: dict[str, dict[str, Any]] = {}
    for el in ET.parse(path).getroot().findall("./drugs/drug"):
        drug_id = _text(el.find("id"))
        bonus = parse_bonus(el.find("bonus"))
        duration = _text(el.find("duration"))
        speed = _text(el.find("speed"))
        vectors = _text(el.find("vectors"))
        if not drug_id or not (bonus or duration or speed or vectors):
            continue
        out[drug_id] = {
            "drug_bonus": bonus,
            "drug_duration": duration,
            "drug_speed": speed,
            "drug_vectors": [v.strip() for v in vectors.split(",") if v.strip()],
        }
    return out


def load_drug_grades() -> list[dict[str, Any]]:
    path = DATA_DIR / "gear.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./gears/gear"):
        if _text(el.find("category")) != "Drug Grades":
            continue
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        gear_id = _text(el.find("id"))
        if not name or not gear_id:
            continue
        items.append(
            {
                "id": gear_id,
                "name": name,
                "category": "Drug Grades",
                "cost": _text(el.find("cost"), "0"),
                "avail": _text(el.find("avail")),
                "minrating": 0,
                "maxrating": 0,
                "capacity": "",
                "plugin": True,
                "host_capacity": "",
                "plugin_capacity": "0",
                "requireparent": True,
                "addoncategories": [],
                "required_names": [],
                "required_categories": ["Drugs", "Toxins", "Chemicals"],
                "included": [],
                "ammo_weapon_types": [],
                "costfor": 0,
                "weapon_details": "",
                "add_weapon": "",
                "weaponbonus": {},
                "bonus": parse_bonus(el.find("bonus")),
                "devicerating": "0",
                "attack": "0",
                "sleaze": "0",
                "dataprocessing": "0",
                "firewall": "0",
                "attributearray": "",
                "programs": "0",
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
                "extra_kind": "",
                "needs_extra": False,
            }
        )
    return items
