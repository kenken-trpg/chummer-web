"""Drug component + drug-grade loaders and the drug-effect summariser."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from ...notices import Notice, notice, term, ui
from .._xml import _text, data_root
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

    ``drugs.xml`` carries the ``<bonus>`` (attribute / limit / initiativedice /
    quality / specificskill), the ``<duration>`` formula (seconds, may use
    ``{BOD}`` / ``{D6}``), ``<speed>`` and ``<vectors>`` that the flat
    ``gear.xml`` ``Drugs`` entries omit. Upstream kept all of this in
    ``drugcomponents.xml`` until it split the premade drugs — the BTLs among
    them — into a file of their own.
    """
    root = data_root("drugs.xml")
    if root is None:
        return {}
    out: dict[str, dict[str, Any]] = {}
    for el in root.findall("./drugs/drug"):
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
    root = data_root("gear.xml")
    if root is None:
        return []
    items: list[dict[str, Any]] = []
    for el in root.findall("./gears/gear"):
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


_EFFECT_SCALARS = {"level", "crashdamage", "speed", "duration", "info"}


def _component_effects(el: ET.Element) -> list[dict[str, Any]]:
    """One entry per ``<effect>``, keyed by the level it belongs to.

    The ``<bonus>`` vocabulary a component's effect speaks is the one premade
    drugs already speak (``attribute`` / ``limit`` / ``quality`` /
    ``initiativedice`` / ``specificskill``), so the nodes are kept in
    ``parse_bonus`` shape and go through the same translation the engine
    already applies to a premade drug. The rest — level, crash damage, onset,
    duration, the free-text ``<info>`` — is not a bonus and is pulled out here.
    """
    effects: list[dict[str, Any]] = []
    for effect_el in el.findall("./effects/effect"):
        nodes = parse_bonus(effect_el)
        scalars = {node["tag"]: str(node.get("value") or "") for node in nodes if node["tag"] in _EFFECT_SCALARS}
        effects.append(
            {
                "level": _int_text(scalars.get("level")),
                "nodes": [node for node in nodes if node["tag"] not in _EFFECT_SCALARS],
                "crash_damage": _int_text(scalars.get("crashdamage")),
                "speed": _int_text(scalars.get("speed")),
                "duration": _int_text(scalars.get("duration")),
                "info": scalars.get("info") or "",
            }
        )
    return effects


def _int_text(value: str | None, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def load_custom_drug_components() -> list[dict[str, Any]]:
    """The Foundation / Block / Enhancer parts a custom drug is mixed from
    (CF p.190). BTLs used to be mixable parts too; upstream moved them to
    ``drugs.xml``, where each is a premade drug of its own.

    ``rating`` / ``threshold`` in the XML are the component's *addiction*
    rating and threshold, not a gear rating — they are renamed here so nothing
    downstream mistakes them for one. ``limit`` is how many of the component
    one drug may hold; absent means unlimited.
    """
    root = data_root("drugcomponents.xml")
    if root is None:
        return []
    items: list[dict[str, Any]] = []
    for el in root.findall("./drugcomponents/drugcomponent"):
        comp_id = _text(el.find("id"))
        name = _text(el.find("name"))
        if not comp_id or not name:
            continue
        items.append(
            {
                "id": comp_id,
                "name": name,
                "category": _text(el.find("category")),
                "cost": _text(el.find("cost"), "0"),
                "avail": _text(el.find("availability")),
                "addiction_rating": _int_text(_text(el.find("rating"))),
                "addiction_threshold": _int_text(_text(el.find("threshold"))),
                "limit": _int_text(_text(el.find("limit"))),
                "effects": _component_effects(el),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def load_custom_drug_grades() -> list[dict[str, Any]]:
    """The quality a custom drug is cooked to (``<grades>`` in ``drugs.xml``):
    a cost multiplier and, for Pharmaceutical, an addiction-threshold
    modifier."""
    root = data_root("drugs.xml")
    if root is None:
        return []
    items: list[dict[str, Any]] = []
    for el in root.findall("./grades/grade"):
        name = _text(el.find("name"))
        if not name:
            continue
        raw_cost = _text(el.find("cost"), "1")
        try:
            cost_mult = float(raw_cost)
        except ValueError:
            cost_mult = 1.0
        items.append(
            {
                "id": _text(el.find("id")),
                "name": name,
                "cost_multiplier": cost_mult,
                "addiction_threshold": _int_text(_text(el.find("addictionthreshold"))),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items
