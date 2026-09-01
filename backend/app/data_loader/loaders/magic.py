"""Awakened / Emerged catalog loaders: powers, enhancements, mentors,
spells, traditions, spirits, complex forms, streams, sprites, foci and
focus formulae.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any

from .._xml import DATA_DIR, _float, _int, _text
from ..bonus import _specific_powers, parse_bonus, parse_required


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
SPIRIT_ATTR_KEYS = ("bod", "agi", "rea", "str", "cha", "int", "log", "wil", "ini")


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


def _focus_effect(nodes: list[dict[str, Any]]) -> str:
    bits: list[str] = []
    for node in nodes:
        tag = node.get("tag") or ""
        fields = node.get("fields") or {}
        if tag == "specificskill":
            name = str(fields.get("name") or "").strip()
            if name:
                bits.append(f"{name} +Rating")
        elif tag == "skillattribute":
            name = str(fields.get("name") or "").strip()
            if name:
                bits.append(f"{name} skills +Rating")
        elif tag == "spellcategory":
            name = str(fields.get("name") or "").strip()
            if name:
                bits.append(f"{name} spells +Rating")
        elif tag == "weaponspecificdice":
            kind = str((node.get("attrs") or {}).get("type") or "Melee").strip() or "Melee"
            bits.append(f"{kind} weapon +Rating")
    return " / ".join(bits)


def _focus_weapon_type(nodes: list[dict[str, Any]]) -> str:
    for node in nodes:
        if node.get("tag") != "weaponspecificdice":
            continue
        return str((node.get("attrs") or {}).get("type") or "Melee").strip() or "Melee"
    return ""


def load_foci() -> list[dict[str, Any]]:
    path = DATA_DIR / "gear.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./gears/gear"):
        if _text(el.find("category")) != "Foci":
            continue
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        gear_id = _text(el.find("id"))
        if not name or not gear_id:
            continue
        if name == "Qi Focus" or "Individualized" in name or "Formula" in name:
            continue
        bonus = parse_bonus(el.find("bonus"))
        weapon_type = _focus_weapon_type(bonus)
        items.append(
            {
                "id": gear_id,
                "name": name,
                "category": "Foci",
                "maxrating": _int(el.find("rating"), 6),
                "cost": _text(el.find("cost"), "Rating * 4000"),
                "avail": _text(el.find("avail")),
                "bonus": bonus,
                "effect": _focus_effect(bonus),
                "needs_weapon": bool(weapon_type),
                "weapon_type": weapon_type,
                "formula": None,
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    formulae = load_focus_formulae()
    for item in items:
        formula = formulae.get(item["name"])
        if formula:
            item["formula"] = formula
    return items


def _focus_name_from_formula(name: str) -> str:
    return name.replace(" Formula", "", 1)


def load_focus_formulae() -> dict[str, dict[str, Any]]:
    path = DATA_DIR / "gear.xml"
    if not path.exists():
        return {}
    items: dict[str, dict[str, Any]] = {}
    for el in ET.parse(path).getroot().findall("./gears/gear"):
        if _text(el.find("category")) != "Formulae":
            continue
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        if "Focus Formula" not in name or "Individualized" in name:
            continue
        focus_name = _focus_name_from_formula(name)
        items[focus_name] = {
            "id": _text(el.find("id")),
            "name": name,
            "cost": _text(el.find("cost"), "Rating * 1000"),
            "source": _text(el.find("source")),
            "page": _text(el.find("page")),
        }
    return items
