"""Metatype + metavariant loading."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from .._xml import ATTR_KEYS, DATA_DIR, _int, _text
from ..bonus import parse_bonus


def _parse_metatype(el: ET.Element, parent_name: str | None = None) -> dict[str, Any]:
    attrs: dict[str, dict[str, int | float]] = {}
    for key in ATTR_KEYS:
        upper = key.upper()
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
        "source": _text(el.find("source")),
        "page": _text(el.find("page")),
        "bonus": parse_bonus(el.find("bonus")),
        "metavariants": variants,
    }


def load_metatypes() -> list[dict[str, Any]]:
    tree = ET.parse(DATA_DIR / "metatypes.xml")
    items = []
    for el in tree.getroot().findall("./metatypes/metatype"):
        items.append(_parse_metatype(el))
    return items
