"""Positive/negative quality list (with parsed bonus + requirement trees)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from .._xml import _int, _text, parse_data
from ..bonus import (
    parse_bonus,
    parse_required,
    parse_requirement_tree,
    quality_extra_meta,
    quality_needs_extra,
)


def _critter_power_refs(parent: ET.Element | None, tag: str) -> list[dict[str, Any]]:
    """`<critterpowers><power select="Wood">Allergy</power>` and the
    `<optionalpowers><optionalpower>` twin, one row per element.

    `parse_bonus` folds repeated children into one list and keeps a single
    `select`, which loses which Allergy is to Wood; these read the elements.
    """
    if parent is None:
        return []
    rows: list[dict[str, Any]] = []
    for el in parent.findall(tag):
        name = _text(el)
        if not name:
            continue
        row: dict[str, Any] = {"name": name, "select": el.attrib.get("select") or ""}
        if el.attrib.get("rating"):
            row["rating"] = el.attrib["rating"]
        rows.append(row)
    return rows


def load_qualities() -> list[dict[str, Any]]:
    root = parse_data("qualities.xml")
    items = []
    for el in root.findall("./qualities/quality"):
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
                # applied once, however many levels are taken (Gremlins: +1 Notoriety)
                "firstlevelbonus": parse_bonus(el.find("firstlevelbonus")),
                # counted together toward the limit (Indomitable: three kinds, 3 in all)
                "includeinlimit": [_text(n) for n in el.findall("./includeinlimit/name") if _text(n)],
                # the shared cap when it differs from `limit` (Tough as Nails: 4)
                "limitwithinclusions": _int(el.find("limitwithinclusions"), 0),
                "add_weapon": _text(el.find("addweapon")),
                "max_takes": max_takes,
                "doublecost": _text(el.find("doublecost"), "False").lower() == "true",
                # SR5 p.107: bought in play at twice the karma; False opts out
                "double_career": _text(el.find("doublecareer"), "True").lower() == "true",
                "onlyprioritygiven": el.find("onlyprioritygiven") is not None,
                "chargenonly": el.find("chargenonly") is not None,
                "metagenic": el.find("metagenic") is not None,
                "contributes_to_metagenic_limit": _text(el.find("contributetolimit"), "True").lower() != "false",
                "forbidden": parse_required(el.find("forbidden")),
                "required": parse_required(el.find("required")),
                "required_tree": parse_requirement_tree(el.find("required")),
                # karma moves by `value` when the tree is met (Blind: worth 5, not 15, to
                # someone who can see astrally — RF p.153)
                "cost_discount": {
                    "required_tree": parse_requirement_tree(el.find("./costdiscount/required")),
                    "value": _int(el.find("./costdiscount/value"), 0),
                }
                if el.find("costdiscount") is not None
                else None,
                "forbidden_tree": parse_requirement_tree(el.find("forbidden")),
                "needs_extra": quality_needs_extra(bonus),
                "extra_kind": extra_meta.get("extra_kind"),
                "select_options": extra_meta.get("select_options") or [],
                "spirit_options": extra_meta.get("spirit_options") or [],
                "expertise_skill": extra_meta.get("expertise_skill") or "",
                "add_spirit_count": int(extra_meta.get("add_spirit_count") or 0),
                # `<critterpowers>` / `<optionalpowers>` (the Infected, RF p.126):
                # the powers it grants, and the list the player picks one from
                "critter_powers": _critter_power_refs(el.find("./bonus/critterpowers"), "power"),
                "optional_powers": _critter_power_refs(el.find("./bonus/optionalpowers"), "optionalpower"),
            }
        )
    return items
