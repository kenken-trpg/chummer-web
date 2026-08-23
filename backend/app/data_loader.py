from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

VENDOR = Path(__file__).resolve().parents[1] / "vendor" / "chummer"
DATA_DIR = VENDOR / "data"
LANG_DIR = VENDOR / "lang"

ATTR_KEYS = ("bod", "agi", "rea", "str", "cha", "int", "log", "wil", "edg", "mag", "res", "ess")
PHYSICAL_ATTRS = ("BOD", "AGI", "REA", "STR", "WIL", "LOG", "INT", "CHA")
SPECIAL_ATTRS = ("EDG", "MAG", "RES")


def _text(el: ET.Element | None, default: str = "") -> str:
    if el is None or isinstance(el, str):
        return default if el is None else (el or default)
    if el.text is None:
        return default
    return el.text.strip()


def _int(el: ET.Element | None, default: int = 0) -> int:
    raw = _text(el)
    if not raw:
        return default
    try:
        return int(float(raw))
    except ValueError:
        return default


def _float(el: ET.Element | None, default: float = 0.0) -> float:
    raw = _text(el)
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _child(parent: ET.Element, *names: str) -> ET.Element | None:
    for name in names:
        found = parent.find(name)
        if found is not None:
            return found
    return None


def eval_formula(
    expr: str | None,
    rating: int = 1,
    default: float = 0.0,
    extras: dict[str, int | float] | None = None,
) -> float:
    raw = (expr or "").strip()
    if not raw:
        return default
    env: dict[str, int | float] = {**(extras or {}), "Rating": int(rating)}
    for key in sorted(env, key=len, reverse=True):
        raw = raw.replace("{" + str(key) + "}", str(env[key]))
    if re.search(r"[{}]", raw):
        return default
    fixed = re.fullmatch(r"FixedValues\((.+)\)", raw, re.I)
    if fixed:
        parts = [p.strip() for p in fixed.group(1).split(",")]
        idx = max(0, min(len(parts) - 1, int(rating) - 1))
        return eval_formula(parts[idx], rating, default, extras)
    s = re.sub(r"number\(([^)]+)\)", r"int(\1)", raw, flags=re.I)
    for key in sorted(env, key=len, reverse=True):
        s = s.replace(str(key), str(env[key]))
    s = re.sub(r"[RF]$", "", s.strip())
    s = s.replace(" ", "")
    if not re.fullmatch(r"[0-9+\-*/().><=int]+", s):
        try:
            return float(s)
        except ValueError:
            return default
    try:
        return float(eval(s, {"__builtins__": {}}, {"int": int}))
    except Exception:
        return default


def parse_capacity(expr: str | None) -> tuple[bool, str]:
    raw = (expr or "").strip()
    if raw.startswith("[") and raw.endswith("]"):
        return True, raw[1:-1]
    return False, raw


CORE_GRADES = ("Standard", "Used", "Alphaware", "Betaware", "Deltaware")


def _load_grades(root: ET.Element) -> list[dict[str, Any]]:
    grades = []
    for el in root.findall("./grades/grade"):
        name = _text(el.find("name"))
        if not name:
            continue
        grades.append(
            {
                "id": _text(el.find("id")),
                "name": name,
                "ess": _float(el.find("ess"), 1.0),
                "cost": _float(el.find("cost"), 1.0),
                "source": _text(el.find("source")),
                "core": name in CORE_GRADES,
            }
        )
    return grades


def _load_ware_items(root: ET.Element, xpath: str, default_category: str) -> list[dict[str, Any]]:
    items = []
    for el in root.findall(xpath):
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        if not name:
            continue
        cap_raw = _text(el.find("capacity"))
        plugin, cap_expr = parse_capacity(cap_raw)
        rating_raw = _text(el.find("rating"))
        min_raw = _text(el.find("minrating"))
        formula_rating = "{" in rating_raw or "{" in min_raw
        max_rating = 1 if formula_rating else _int(el.find("rating"), 1)
        min_rating = 1 if formula_rating else _int(el.find("minrating"), 1)
        if max_rating <= 0:
            max_rating = 1
        minrating_expr = min_raw or str(min_rating)
        maxrating_expr = rating_raw or str(max_rating)
        subs_el = el.find("subsystems")
        subsystems = [
            _text(sub.find("name"))
            for sub in list(subs_el if subs_el is not None else [])
            if _text(sub.find("name"))
        ]
        items.append(
            {
                "id": _text(el.find("id")),
                "name": name,
                "category": _text(el.find("category"), default_category),
                "ess": _text(el.find("ess"), "0"),
                "cost": _text(el.find("cost"), "0"),
                "avail": _text(el.find("avail")),
                "capacity": cap_expr,
                "minrating": min_rating,
                "maxrating": max_rating,
                "minrating_expr": minrating_expr,
                "maxrating_expr": maxrating_expr,
                "forcegrade": _text(el.find("forcegrade")) or None,
                "plugin": plugin,
                "requireparent": el.find("requireparent") is not None,
                "addtoparentess": el.find("addtoparentess") is not None,
                "formula_rating": formula_rating,
                "allow_subsystems": [_text(c) for c in el.findall("./allowsubsystems/category") if _text(c)],
                "subsystems": subsystems,
                "bonus": parse_bonus(el.find("bonus")),
                "wirelessbonus": parse_bonus(el.find("wirelessbonus")),
                "bannedgrades": [_text(g) for g in el.findall("./bannedgrades/grade") if _text(g)],
                "required": parse_required(el.find("required")),
                "limbslot": _text(el.find("limbslot")) or None,
                "selectside": el.find("selectside") is not None,
                "limbslotcount": _text(el.find("limbslotcount")) or "1",
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def load_cyberware() -> dict[str, Any]:
    path = DATA_DIR / "cyberware.xml"
    if not path.exists():
        return {"grades": [], "items": []}
    root = ET.parse(path).getroot()
    return {"grades": _load_grades(root), "items": _load_ware_items(root, "./cyberwares/cyberware", "Bodyware")}


def load_bioware() -> dict[str, Any]:
    path = DATA_DIR / "bioware.xml"
    if not path.exists():
        return {"grades": [], "items": []}
    root = ET.parse(path).getroot()
    return {"grades": _load_grades(root), "items": _load_ware_items(root, "./biowares/bioware", "Basic")}


def parse_required(el: ET.Element | None) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"bioware": [], "cyberware": [], "metatype": [], "quality": [], "power": []}
    if el is None:
        return out
    for group in list(el):
        for child in list(group):
            tag = child.tag
            name = _text(child)
            if tag in out and name and name not in out[tag]:
                out[tag].append(name)
    return out


def _bonus_fields(child: ET.Element) -> tuple[dict[str, Any], dict[str, list[str]]]:
    fields: dict[str, Any] = {}
    nested: dict[str, list[str]] = {}
    for sub in list(child):
        if len(sub) > 0:
            nested[sub.tag] = [_text(item) for item in list(sub) if _text(item)]
            continue
        value = _text(sub)
        existing = fields.get(sub.tag)
        if existing is None:
            fields[sub.tag] = value
        elif isinstance(existing, list):
            existing.append(value)
        else:
            fields[sub.tag] = [existing, value]
    return fields, nested


def parse_bonus(bonus_el: ET.Element | None) -> list[dict[str, Any]]:
    if bonus_el is None:
        return []
    nodes: list[dict[str, Any]] = []
    for child in list(bonus_el):
        tag = child.tag
        payload: dict[str, Any] = {"tag": tag}
        if child.attrib:
            payload["attrs"] = dict(child.attrib)
        if len(child) == 0:
            payload["value"] = _text(child)
        else:
            fields, nested = _bonus_fields(child)
            payload["fields"] = fields
            if nested:
                payload["nested"] = nested
        nodes.append(payload)
    return nodes


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


def load_skills() -> dict[str, Any]:
    tree = ET.parse(DATA_DIR / "skills.xml")
    root = tree.getroot()
    groups = [_text(g) for g in root.findall("./skillgroups/name") if _text(g)]
    skills = []
    for el in root.findall("./skills/skill"):
        exotic = _text(el.find("exotic"), "False").lower() == "true"
        skills.append(
            {
                "id": _text(el.find("id")),
                "name": _text(el.find("name")),
                "attribute": _text(el.find("attribute")).upper(),
                "category": _text(el.find("category")),
                "skillgroup": _text(el.find("skillgroup")) or None,
                "exotic": exotic,
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
                "knowledge": False,
            }
        )
    knowledge = []
    for el in root.findall("./knowledgeskills/skill"):
        knowledge.append(
            {
                "id": _text(el.find("id")),
                "name": _text(el.find("name")),
                "attribute": (
                    _text(el.find("attribute")) or _text(el.find("defaultattribute")) or "INT"
                ).upper(),
                "category": _text(el.find("category"), "Street"),
                "skillgroup": None,
                "exotic": False,
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
                "knowledge": True,
            }
        )
    return {"groups": groups, "skills": skills, "knowledge": knowledge}


def load_qualities() -> list[dict[str, Any]]:
    tree = ET.parse(DATA_DIR / "qualities.xml")
    items = []
    for el in tree.getroot().findall("./qualities/quality"):
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        if not name:
            continue
        items.append(
            {
                "id": _text(el.find("id")),
                "name": name,
                "karma": _int(el.find("karma")),
                "category": _text(el.find("category"), "Positive"),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
                "bonus": parse_bonus(el.find("bonus")),
                "doublecost": _text(el.find("doublecost"), "False").lower() == "true",
                "onlyprioritygiven": el.find("onlyprioritygiven") is not None,
                "forbidden": parse_required(el.find("forbidden")),
                "required": parse_required(el.find("required")),
            }
        )
    return items


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
        if el.find("hide") is not None:
            continue
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


def _specific_powers(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for node in nodes:
        if node.get("tag") != "specificpower":
            continue
        fields = node.get("fields") or {}
        name = str(fields.get("name") or "").strip()
        if not name:
            continue
        out.append(
            {
                "name": name,
                "rating": max(1, _int_text(fields.get("val"), 1)),
                "select": "skill" if "selectskill" in str(node.get("nested") or {}) else None,
            }
        )
    return out


def _int_text(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


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
        items.append(
            {
                "id": spell_id,
                "name": name,
                "category": _text(el.find("category")),
                "descriptor": _text(el.find("descriptor")),
                "dv": _text(el.find("dv")),
                "range": _text(el.find("range")),
                "duration": _text(el.find("duration")),
                "type": _text(el.find("type")),
                "damage": _text(el.find("damage")),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def load_qi_focus() -> dict[str, Any] | None:
    path = DATA_DIR / "gear.xml"
    if not path.exists():
        return None
    for el in ET.parse(path).getroot().findall("./gears/gear"):
        if _text(el.find("name")) != "Qi Focus":
            continue
        if el.find("hide") is not None:
            continue
        return {
            "id": _text(el.find("id")),
            "name": _text(el.find("name")),
            "category": _text(el.find("category"), "Foci"),
            "maxrating": _int(el.find("rating"), 6),
            "cost": _text(el.find("cost"), "Rating * 3000"),
            "source": _text(el.find("source")),
            "page": _text(el.find("page")),
            "pointsperlevel": 0.25,
        }
    return None


def load_priorities() -> list[dict[str, Any]]:
    tree = ET.parse(DATA_DIR / "priorities.xml")
    rows = []
    for el in tree.getroot().findall("./priorities/priority"):
        category = _text(el.find("category"))
        value = _text(el.find("value"))
        if not category or not value:
            continue
        row: dict[str, Any] = {
            "id": _text(el.find("id")),
            "name": _text(el.find("name")),
            "category": category,
            "value": value,
            "gameplay": _text(_child(el, "gameplay", "prioritytable"), "Standard"),
        }
        if category == "Heritage":
            mets = []
            for m in el.findall("./metatypes/metatype"):
                mets.append(
                    {
                        "name": _text(m.find("name")),
                        "special": _int(m.find("value")),
                        "karma": _int(m.find("karma")),
                        "variants": [
                            {
                                "name": _text(v.find("name")),
                                "special": _int(v.find("value"), _int(m.find("value"))),
                                "karma": _int(v.find("karma")),
                            }
                            for v in m.findall("./metavariants/metavariant")
                        ],
                    }
                )
            row["metatypes"] = mets
        elif category == "Attributes":
            row["attribute_points"] = _int(el.find("attributes"))
        elif category == "Skills":
            row["skill_points"] = _int(el.find("skills"))
            row["skill_group_points"] = _int(el.find("skillgroups"))
        elif category == "Resources":
            row["nuyen"] = _int(el.find("resources"))
        elif category == "Talent":
            talents = []
            for t in el.findall("./talents/talent"):
                magic = _int(t.find("magic"))
                resonance = _int(t.find("resonance"))
                talents.append(
                    {
                        "name": _text(t.find("value")) or _text(t.find("name")),
                        "label": _text(t.find("name")),
                        "magic": magic,
                        "resonance": resonance,
                        "value": magic or resonance,
                        "quality": _text(t.find("./qualities/quality")),
                    }
                )
            row["talents"] = talents
        rows.append(row)
    return rows


def load_translations() -> dict[str, str]:
    mapping: dict[str, str] = {}
    path = LANG_DIR / "ja-jp_data.xml"
    if not path.exists():
        return mapping
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        log.warning("ja-jp_data.xml parse failed: %s", exc)
        return mapping
    for node in root.iter():
        name = _text(node.find("name"))
        trans = _text(node.find("translate"))
        if name and trans:
            mapping[name] = trans
    return mapping


def load_ui_strings() -> dict[str, str]:
    path = LANG_DIR / "ja-jp.xml"
    strings: dict[str, str] = {}
    if not path.exists():
        return strings
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        log.warning("ja-jp.xml parse failed: %s", exc)
        return strings
    for node in root.findall(".//string"):
        key = node.get("key") or _text(node.find("key"))
        text = _text(node.find("text")) or _text(node.find("translate")) or _text(node)
        if key and text:
            strings[key] = text
    return strings


@lru_cache(maxsize=1)
def catalog() -> dict[str, Any]:
    if not (DATA_DIR / "metatypes.xml").exists():
        raise FileNotFoundError(
            f"Chummer data not found in {DATA_DIR}. Run backend/scripts/fetch_chummer_data.py"
        )
    metatypes = load_metatypes()
    playable = [
        m
        for m in metatypes
        if m["category"] in {"Metahuman", "Metavariant"}
        and m["name"] in {"Human", "Elf", "Dwarf", "Ork", "Troll"}
    ]
    translations = load_translations()
    all_by_name: dict[str, dict[str, Any]] = {}
    for m in metatypes:
        all_by_name.setdefault(m["name"], m)
        for mv in m.get("metavariants") or []:
            all_by_name.setdefault(mv["name"], mv)
    return {
        "metatypes": playable,
        "all_metatypes": all_by_name,
        "skills": load_skills(),
        "qualities": load_qualities(),
        "cyberware": load_cyberware(),
        "bioware": load_bioware(),
        "powers": load_powers(),
        "enhancements": load_enhancements(),
        "mentors": load_mentors(),
        "spells": load_spells(),
        "qi_focus": load_qi_focus(),
        "priorities": load_priorities(),
        "translations": translations,
        "ui_strings": load_ui_strings(),
    }


def reset_catalog() -> None:
    catalog.cache_clear()
