"""Metatype + metavariant loading."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from .._xml import ATTR_KEYS, _int, _text, parse_data
from ..bonus import parse_bonus


def _grants(parent: ET.Element | None, tag: str) -> list[dict[str, Any]]:
    """Keep each grant instance, including repeated names and fixed picks.

    These are references, not purchases. Resolution against the quality or
    critter-power catalog belongs to the consumer; the XML may name an ID.
    """
    if parent is None:
        return []
    return [
        {
            "name": _text(el),
            "select": el.get("select", ""),
            "rating": el.get("rating", ""),
            "removable": el.get("removable", "false").lower() == "true",
        }
        for el in parent.findall(tag)
        if _text(el)
    ]


def _parse_metatype(el: ET.Element, parent_name: str | None = None) -> dict[str, Any]:
    attrs: dict[str, dict[str, int | float]] = {}
    for key in ATTR_KEYS:
        upper = key.upper()
        if key == "dep":
            # Depth is an A.I.'s alone; a custom metatype that leaves the
            # tags out has none, not the 1-6 the other defaults hand out.
            attrs[upper] = {
                "min": _int(el.find("depmin")),
                "max": _int(el.find("depmax")),
                "aug": _int(el.find("depaug")),
            }
            continue
        attrs[upper] = {
            "min": _int(el.find(f"{key}min"), 1 if key != "ess" else 6),
            "max": _int(el.find(f"{key}max"), 6 if key != "ess" else 6),
            "aug": _int(el.find(f"{key}aug"), 10 if key not in {"edg", "mag", "res", "ess"} else 6),
        }
    if attrs["ESS"]["min"] == 1 and el.find("essmin") is None:
        attrs["ESS"] = {"min": 6, "max": 6, "aug": 6}

    variants = []
    mv_root = el.find("metavariants")
    if mv_root is not None:
        for mv in mv_root.findall("metavariant"):
            variants.append(_parse_metatype(mv, _text(el.find("name"))))

    return {
        "id": _text(el.find("id")),
        "name": _text(el.find("name")),
        "parent": parent_name,
        "category": _text(el.find("category"), "Metahuman"),
        "karma": _int(el.find("karma")),
        "attributes": attrs,
        "walk": _text(el.find("walk"), "2/1/0"),
        "run": _text(el.find("run"), "4/0/0"),
        "sprint": _text(el.find("sprint"), "2/1/0"),
        # A shapeshifter's metavariant writes its metahuman form's rates as
        # `<walk alt="2/1/0">1/1/0</walk>`: the text is the animal's.
        **{
            f"{kind}_alt": node.get("alt", "")
            for kind in ("walk", "run", "sprint")
            if (node := el.find(kind)) is not None and node.get("alt")
        },
        "source": _text(el.find("source")),
        "page": _text(el.find("page")),
        "bonus": parse_bonus(el.find("bonus")),
        "qualities": [
            {**grant, "category": category}
            for category in ("Positive", "Negative")
            for grant in _grants(el.find(f"./qualities/{category.lower()}"), "quality")
        ],
        "powers": _grants(el.find("powers"), "power"),
        # An A.I. gets half the Attributes priority's points (Chummer's
        # SelectMetatypePriority divides by two, rounding down).
        "halve_attribute_points": el.find("halveattributepoints") is not None,
        "quality_restriction": _quality_restriction(el.find("qualityrestriction")),
        "metavariants": variants,
    }


def _quality_restriction(el: ET.Element | None) -> dict[str, list[str]] | None:
    """The only qualities this metatype may take, by category, or `None`.

    Chummer's SelectQuality leaves out every quality the list does not name,
    so a category with no entries allows none of its qualities.
    """
    if el is None:
        return None
    return {
        category: [_text(q) for q in el.findall(f"./{category.lower()}/quality") if _text(q)]
        for category in ("Positive", "Negative")
    }


def load_metatypes() -> list[dict[str, Any]]:
    root = parse_data("metatypes.xml")
    items = []
    for el in root.findall("./metatypes/metatype"):
        items.append(_parse_metatype(el))
    return items
