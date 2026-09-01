"""Lifestyle + lifestyle-quality loaders."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from .._xml import DATA_DIR, _int, _text
from ..bonus import parse_bonus, quality_needs_extra


def load_lifestyles() -> list[dict[str, Any]]:
    path = DATA_DIR / "lifestyles.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./lifestyles/lifestyle"):
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        lifestyle_id = _text(el.find("id"))
        if not name or not lifestyle_id or name.startswith("ID ERROR"):
            continue
        freegrids = [
            {
                "name": _text(fg) or "Grid Subscription",
                "select": fg.attrib.get("select") or "",
            }
            for fg in el.findall("./freegrids/freegrid")
        ]
        items.append(
            {
                "id": lifestyle_id,
                "name": name,
                "cost": _int(el.find("cost")),
                "dice": _int(el.find("dice")),
                "lp": _int(el.find("lp")),
                "multiplier": _int(el.find("multiplier"), 100),
                "cost_for_comforts": _int(el.find("costforcomforts")),
                "cost_for_security": _int(el.find("costforsecurity")),
                "cost_for_area": _int(el.find("costforarea")),
                "increment": _text(el.find("increment"), "month"),
                "freegrids": freegrids,
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def load_lifestyle_qualities() -> list[dict[str, Any]]:
    path = DATA_DIR / "lifestyles.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./qualities/quality"):
        name = _text(el.find("name"))
        qid = _text(el.find("id"))
        if not name or not qid:
            continue
        allowed_raw = _text(el.find("allowed"))
        allowed = [part.strip() for part in allowed_raw.split(",") if part.strip()] if allowed_raw else []
        bonus = parse_bonus(el.find("bonus"))
        items.append(
            {
                "id": qid,
                "name": name,
                "category": _text(el.find("category")),
                "lp": _int(el.find("lp")),
                "cost": _int(el.find("cost")),
                "multiplier": _int(el.find("multiplier")),
                "allowed": allowed,
                "allow_multiple": el.find("allowmultiple") is not None,
                "needs_extra": quality_needs_extra(bonus),
                "bonus": bonus,
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items
