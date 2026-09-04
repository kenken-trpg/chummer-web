"""The magician side: spells, traditions and the spirits a tradition summons.

`SPELL_CATEGORIES` is the learnable set — Chummer's spell list also carries
entries the character sheet shows but nobody buys, which is what `learnable`
marks.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any

from ..._xml import DATA_DIR, _text
from ...bonus import parse_bonus, parse_required
from ._common import SPIRIT_ATTR_KEYS

SPELL_CAST_CATEGORIES = frozenset({"Combat", "Detection", "Health", "Illusion", "Manipulation"})
SPELL_CATEGORIES = SPELL_CAST_CATEGORIES | frozenset({"Rituals", "Enchantments"})
CATEGORY_SKILL = {
    "Combat": "Spellcasting",
    "Detection": "Spellcasting",
    "Health": "Spellcasting",
    "Illusion": "Spellcasting",
    "Manipulation": "Spellcasting",
    "Rituals": "Ritual Spellcasting",
    "Enchantments": "Artificing",
}


def spell_kind(category: str) -> str:
    if category == "Rituals":
        return "ritual"
    if category == "Enchantments":
        return "enchantment"
    return "spell"


def load_spells() -> list[dict[str, Any]]:
    path = DATA_DIR / "spells.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./spells/spell"):
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        spell_id = _text(el.find("id"))
        if not name or not spell_id:
            continue
        category = _text(el.find("category"))
        items.append(
            {
                "id": spell_id,
                "name": name,
                "category": category,
                "kind": spell_kind(category),
                "useskill": CATEGORY_SKILL.get(category, "Spellcasting"),
                "descriptor": _text(el.find("descriptor")),
                "dv": _text(el.find("dv")),
                "range": _text(el.find("range")),
                "duration": _text(el.find("duration")),
                "type": _text(el.find("type")),
                "damage": _text(el.find("damage")),
                "learnable": category in SPELL_CATEGORIES,
                "required": parse_required(el.find("required")),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


SPIRIT_SLOTS = (
    ("spiritcombat", "combat"),
    ("spiritdetection", "detection"),
    ("spirithealth", "health"),
    ("spiritillusion", "illusion"),
    ("spiritmanipulation", "manipulation"),
)


def load_traditions() -> list[dict[str, Any]]:
    path = DATA_DIR / "traditions.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./traditions/tradition"):
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        trad_id = _text(el.find("id"))
        drain = _text(el.find("drain"))
        if not name or not trad_id or not drain:
            continue
        attrs = re.findall(r"\{([A-Za-z]+)\}", drain)
        spirits: dict[str, str] = {}
        spirits_el = el.find("spirits")
        if spirits_el is not None:
            for tag, role in SPIRIT_SLOTS:
                spirit_name = _text(spirits_el.find(tag))
                if spirit_name:
                    spirits[role] = spirit_name
        items.append(
            {
                "id": trad_id,
                "name": name,
                "drain": drain,
                "drain_attrs": [a.upper() for a in attrs],
                "spirits": spirits,
                "bonus": parse_bonus(el.find("bonus")),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def load_spirits() -> list[dict[str, Any]]:
    path = DATA_DIR / "traditions.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./spirits/spirit"):
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        spirit_id = _text(el.find("id"))
        if not name or not spirit_id:
            continue
        items.append(
            {
                "id": spirit_id,
                "name": name,
                "attributes": {key.upper(): _text(el.find(key), "F") for key in SPIRIT_ATTR_KEYS},
                "powers": [_text(p) for p in el.findall("./powers/power") if _text(p)],
                "optionalpowers": [_text(p) for p in el.findall("./optionalpowers/power") if _text(p)],
                "skills": [
                    {"name": _text(s), "attribute": (s.get("attr") or "").upper()}
                    for s in el.findall("./skills/skill")
                    if _text(s)
                ],
                "weaknesses": [_text(w) for w in el.findall("./weaknesses/weakness") if _text(w)],
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items
