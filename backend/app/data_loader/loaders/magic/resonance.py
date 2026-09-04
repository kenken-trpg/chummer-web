"""The Emerged side: complex forms, streams, sprites and echoes.

The mirror of `spells.py` / `foci.py` for technomancers — a stream is a
tradition, a sprite is a spirit, an echo is a metamagic.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any

from ..._xml import DATA_DIR, _text
from ...bonus import parse_bonus, parse_required, parse_requirement_tree
from ._common import SPIRIT_ATTR_KEYS


def load_complex_forms() -> list[dict[str, Any]]:
    path = DATA_DIR / "complexforms.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./complexforms/complexform"):
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        form_id = _text(el.find("id"))
        if not name or not form_id:
            continue
        items.append(
            {
                "id": form_id,
                "name": name,
                "target": _text(el.find("target")),
                "duration": _text(el.find("duration")),
                "fv": _text(el.find("fv")),
                "needs_extra": "[Matrix Attribute]" in name,
                "required": parse_required(el.find("required")),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def load_streams() -> list[dict[str, Any]]:
    path = DATA_DIR / "streams.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./traditions/tradition"):
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        stream_id = _text(el.find("id"))
        drain = _text(el.find("drain"))
        if not name or not stream_id or not drain:
            continue
        attrs = re.findall(r"\{([A-Za-z]+)\}", drain)
        sprites = [_text(s) for s in el.findall("./spirits/spirit") if _text(s)]
        items.append(
            {
                "id": stream_id,
                "name": name,
                "drain": drain,
                "drain_attrs": [a.upper() for a in attrs],
                "sprites": sprites,
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def load_sprites() -> list[dict[str, Any]]:
    path = DATA_DIR / "streams.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./spirits/spirit"):
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        sprite_id = _text(el.find("id"))
        if not name or not sprite_id:
            continue
        items.append(
            {
                "id": sprite_id,
                "name": name,
                "attributes": {key.upper(): _text(el.find(key), "F") for key in SPIRIT_ATTR_KEYS},
                "powers": [_text(p) for p in el.findall("./powers/power") if _text(p)],
                "skills": [
                    {"name": _text(s), "attribute": (s.get("attr") or "").upper()}
                    for s in el.findall("./skills/skill")
                    if _text(s)
                ],
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def load_echoes() -> list[dict[str, Any]]:
    path = DATA_DIR / "echoes.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./echoes/echo"):
        name = _text(el.find("name"))
        echo_id = _text(el.find("id"))
        if not name or not echo_id:
            continue
        limit_el = el.find("limit")
        limit_raw = _text(limit_el) if limit_el is not None else ""
        if limit_el is None:
            max_takes = 1
        elif limit_raw.lower() == "false":
            max_takes = None
        else:
            try:
                max_takes = max(1, int(limit_raw))
            except ValueError:
                max_takes = 1
        bonus = parse_bonus(el.find("bonus"))
        needs_extra = el.find("./bonus/selecttext") is not None or any(
            node.get("tag") == "selecttext" for node in bonus
        )
        items.append(
            {
                "id": echo_id,
                "name": name,
                "max_takes": max_takes,
                "needs_extra": needs_extra,
                "bonus": bonus,
                "required_tree": parse_requirement_tree(el.find("required")),
                "required": parse_required(el.find("required")),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items
