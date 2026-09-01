"""Positive/negative quality list (with parsed bonus + requirement trees)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from .._xml import DATA_DIR, _int, _text
from ..bonus import (
    parse_bonus,
    parse_required,
    parse_requirement_tree,
    quality_extra_meta,
    quality_needs_extra,
)


def load_qualities() -> list[dict[str, Any]]:
    tree = ET.parse(DATA_DIR / "qualities.xml")
    items = []
    for el in tree.getroot().findall("./qualities/quality"):
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        if not name:
            continue
        bonus = parse_bonus(el.find("bonus"))
        extra_meta = quality_extra_meta(bonus)
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
        items.append(
            {
                "id": _text(el.find("id")),
                "name": name,
                "karma": _int(el.find("karma")),
                "category": _text(el.find("category"), "Positive"),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
                "bonus": bonus,
                "max_takes": max_takes,
                "doublecost": _text(el.find("doublecost"), "False").lower() == "true",
                "onlyprioritygiven": el.find("onlyprioritygiven") is not None,
                "chargenonly": el.find("chargenonly") is not None,
                "metagenic": el.find("metagenic") is not None,
                "contributes_to_metagenic_limit": _text(el.find("contributetolimit"), "True").lower() != "false",
                "forbidden": parse_required(el.find("forbidden")),
                "required": parse_required(el.find("required")),
                "required_tree": parse_requirement_tree(el.find("required")),
                "forbidden_tree": parse_requirement_tree(el.find("forbidden")),
                "needs_extra": quality_needs_extra(bonus),
                "extra_kind": extra_meta.get("extra_kind"),
                "select_options": extra_meta.get("select_options") or [],
                "spirit_options": extra_meta.get("spirit_options") or [],
                "expertise_skill": extra_meta.get("expertise_skill") or "",
                "add_spirit_count": int(extra_meta.get("add_spirit_count") or 0),
            }
        )
    return items
