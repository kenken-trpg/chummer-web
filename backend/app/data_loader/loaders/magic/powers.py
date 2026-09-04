"""The adept side: powers, their enhancements, mentor spirits, qi foci.

Mentor spirits sit here rather than with spells because Chummer files an
adept's and a magician's mentor in the same list, distinguished only by an
`Adept:` / `Magician:` name prefix — which `_mentor_audience` reads back out.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from ..._xml import DATA_DIR, _float, _int, _text
from ...bonus import _specific_powers, parse_bonus, parse_required, parse_select_power_slot


def _power_required_names(el: ET.Element) -> list[str]:
    names: list[str] = []
    required = el.find("required")
    if required is None:
        return names
    for child in required.iter("power"):
        name = _text(child)
        if name and name not in names:
            names.append(name)
    return names


def _way_quality_names(el: ET.Element | None) -> list[str]:
    names: list[str] = []
    if el is None:
        return names
    for child in el.iter("quality"):
        name = _text(child)
        if name and name not in names:
            names.append(name)
    return names


def _power_select_kind(nodes: list[dict[str, Any]]) -> str | None:
    tags = {node.get("tag") for node in nodes}
    if "selectskill" in tags:
        return "skill"
    if "selectattribute" in tags:
        return "attribute"
    if "selectspell" in tags:
        return "spell"
    return None


def load_powers() -> list[dict[str, Any]]:
    path = DATA_DIR / "powers.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./powers/power"):
        hidden = el.find("hide") is not None
        name = _text(el.find("name"))
        power_id = _text(el.find("id"))
        if not name or not power_id:
            continue
        bonus = parse_bonus(el.find("bonus"))
        items.append(
            {
                "id": power_id,
                "name": name,
                "points": _float(el.find("points")),
                "levels": _text(el.find("levels"), "False").lower() == "true",
                "maxlevels": _int(el.find("maxlevels")),
                "extrapointcost": _float(el.find("extrapointcost")),
                "limit": _int(el.find("limit"), 1),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
                "bonus": bonus,
                "required": _power_required_names(el),
                "select": _power_select_kind(bonus),
                "adeptway": _float(el.find("adeptway")),
                "adeptwayrequires": _way_quality_names(el.find("adeptwayrequires")),
                "magicianswayforbids": el.find(".//magicianswayforbids") is not None,
                "hidden": hidden,
            }
        )
    return items


def load_enhancements() -> list[dict[str, Any]]:
    path = DATA_DIR / "powers.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./enhancements/enhancement"):
        name = _text(el.find("name"))
        enh_id = _text(el.find("id"))
        if not name or not enh_id:
            continue
        items.append(
            {
                "id": enh_id,
                "name": name,
                "power": _text(el.find("power")) or None,
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
                "bonus": parse_bonus(el.find("bonus")),
                "required": parse_required(el.find("required")),
            }
        )
    return items


def load_mentors() -> list[dict[str, Any]]:
    path = DATA_DIR / "mentors.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./mentors/mentor"):
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        mentor_id = _text(el.find("id"))
        if not name or not mentor_id:
            continue
        choices = []
        for choice in el.findall("./choices/choice"):
            choice_name = _text(choice.find("name"))
            if not choice_name:
                continue
            bonus = parse_bonus(choice.find("bonus"))
            choices.append(
                {
                    "name": choice_name,
                    "set": choice.get("set") or "",
                    "audience": _mentor_audience(choice_name),
                    "bonus": bonus,
                    "powers": _specific_powers(bonus),
                }
            )
        items.append(
            {
                "id": mentor_id,
                "name": name,
                "advantage": _text(el.find("advantage")),
                "disadvantage": _text(el.find("disadvantage")),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
                "bonus": parse_bonus(el.find("bonus")),
                "choices": choices,
            }
        )
    return items


def _mentor_audience(name: str) -> str:
    lowered = name.lower()
    if lowered.startswith("adept:"):
        return "adept"
    if lowered.startswith("magician:"):
        return "magician"
    return "all"


def load_qi_focus() -> dict[str, Any] | None:
    path = DATA_DIR / "gear.xml"
    if not path.exists():
        return None
    for el in ET.parse(path).getroot().findall("./gears/gear"):
        if _text(el.find("name")) != "Qi Focus":
            continue
        if el.find("hide") is not None:
            continue
        bonus = parse_bonus(el.find("bonus"))
        select_power = None
        for node in bonus:
            if node.get("tag") == "selectpowers":
                select_power = parse_select_power_slot(node)
                break
        return {
            "id": _text(el.find("id")),
            "name": _text(el.find("name")),
            "category": _text(el.find("category"), "Foci"),
            "maxrating": _int(el.find("rating"), 6),
            "cost": _text(el.find("cost"), "Rating * 3000"),
            "source": _text(el.find("source")),
            "page": _text(el.find("page")),
            "select_power": select_power,
            "pointsperlevel": float((select_power or {}).get("points_per_level") or 0.25),
        }
    return None
