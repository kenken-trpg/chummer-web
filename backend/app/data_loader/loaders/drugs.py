"""Drug component + drug-grade loaders and the drug-effect summariser."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from ...notices import Notice, notice, term, ui
from .._xml import DATA_DIR, _text
from ..bonus import parse_bonus

_DRUG_LIMIT_KEY = {
    "physical": "engine.drugLimit.physical",
    "mental": "engine.drugLimit.mental",
    "social": "engine.drugLimit.social",
}


def drug_node_value(node: dict[str, Any]) -> str:
    fields = node.get("fields") or {}
    return str(fields.get("value") or fields.get("val") or fields.get("bonus") or node.get("value") or "").strip()


def boost_drug_attribute(value: str, positive_attribute: int) -> str:
    """One attribute modifier after ``<drugpositiveattributemodifier>``.

    Narco lifts what a drug *gives* by its rating and leaves what a drug takes
    alone (CF p.159), so a negative — or an unparseable — modifier is returned
    untouched.
    """
    if not positive_attribute:
        return value
    try:
        amount = int(str(value).strip().lstrip("+"))
    except ValueError:
        return value
    return str(amount + positive_attribute) if amount > 0 else value


def drug_effect_summary(nodes: list[dict[str, Any]], positive_attribute: int = 0) -> list[Notice]:
    """A drug's ``<bonus>`` nodes as one notice per effect, for the client to
    join into a line (see ``app.notices``).

    ``positive_attribute`` is Narco's lift, so the line reads what the engine
    actually applied rather than what the book prints for the drug alone.
    """
    parts: list[Notice] = []
    for node in nodes or []:
        tag = node.get("tag")
        fields = node.get("fields") or {}
        val = drug_node_value(node)
        if tag == "attribute":
            val = boost_drug_attribute(val, positive_attribute)
        signed = val if val.startswith(("-", "+")) else (f"+{val}" if val else "")
        if tag == "attribute" and val:
            parts.append(
                notice("engine.drugEffect.attribute", name=str(fields.get("name") or "").upper(), value=signed)
            )
        elif tag == "limit" and val:
            raw = str(fields.get("name") or "").strip()
            key = _DRUG_LIMIT_KEY.get(raw.lower())
            parts.append(notice("engine.drugEffect.limit", limit=ui(key) if key else raw, value=signed))
        elif tag in ("initiativedice", "initiativepass") and val:
            parts.append(notice("engine.drugEffect.initiativeDice", value=val))
        elif tag == "initiative" and val:
            parts.append(notice("engine.drugEffect.initiative", value=signed))
        elif tag == "specificskill" and val:
            parts.append(notice("engine.drugEffect.skill", name=term(str(fields.get("name") or "")), value=signed))
        elif tag == "quality":
            rating = (node.get("attrs") or {}).get("rating")
            name = term(str(node.get("value") or ""))
            if rating:
                parts.append(notice("engine.drugEffect.qualityRated", name=name, rating=str(rating)))
            else:
                parts.append(notice("engine.drugEffect.quality", name=name))
    return parts


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
