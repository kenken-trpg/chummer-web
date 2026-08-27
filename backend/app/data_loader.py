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
    env.setdefault("rating", int(rating))
    lookup = {str(key).lower(): value for key, value in env.items()}
    for key in sorted(env, key=len, reverse=True):
        raw = raw.replace("{" + str(key) + "}", str(env[key]))
    if re.search(r"[{}]", raw):
        return default
    if raw in env:
        return float(env[raw])
    if raw.lower() in lookup:
        return float(lookup[raw.lower()])
    fixed = re.fullmatch(r"FixedValues\((.+)\)", raw, re.I)
    if fixed:
        parts = [p.strip() for p in fixed.group(1).split(",")]
        idx = max(0, min(len(parts) - 1, int(rating) - 1))
        return eval_formula(parts[idx], rating, default, extras)

    def _subst_keys(text: str) -> str:
        out = text
        for key in sorted(env, key=len, reverse=True):
            out = out.replace(str(key), str(env[key]))
        return out

    def _number_repl(match: re.Match[str]) -> str:
        inner = _subst_keys(match.group(1)).replace(" ", "")
        inner = re.sub(r"(?<![<>!=])=(?!=)", "==", inner)
        try:
            if re.search(r"==|!=|<=|>=|<|>", inner):
                return "1" if bool(eval(inner, {"__builtins__": {}}, {})) else "0"
            return str(int(float(eval(inner, {"__builtins__": {}}, {"int": int}))))
        except Exception:
            return "0"

    raw = re.sub(r"number\(([^)]+)\)", _number_repl, raw, flags=re.I)
    s = _subst_keys(raw)
    s = re.sub(r"[RF]$", "", s.strip())
    s = re.sub(r"\bmod\b", "%", s, flags=re.I)
    s = s.replace(" ", "")
    if not re.fullmatch(r"[0-9+\-*/().><=%int]+", s):
        try:
            return float(s)
        except ValueError:
            return default
    try:
        return float(eval(s, {"__builtins__": {}}, {"int": int}))
    except Exception:
        return default


CHARGEN_AVAIL_MAX = 12
CHARGEN_DEVICE_RATING_MAX = 6
CHARGEN_WARE_ATTR_BONUS_MAX = 4


def parse_avail(
    expr: str | None,
    rating: int = 1,
    extras: dict[str, int | float] | None = None,
) -> tuple[int, str, bool]:
    raw = (expr or "").strip()
    if not raw or raw == "-":
        return 0, "", False
    additive = raw.startswith("+")
    if additive:
        raw = raw[1:].lstrip()
    fixed = re.fullmatch(r"FixedValues\((.+)\)", raw, re.I)
    if fixed:
        parts = [part.strip() for part in fixed.group(1).split(",")]
        idx = max(0, min(len(parts) - 1, int(rating) - 1))
        value, suffix, _nested = parse_avail(parts[idx], rating, extras)
        return value, suffix, additive
    suffix = ""
    compact = raw.replace(" ", "")
    if re.search(r"[RF]$", compact, re.I):
        suffix = compact[-1].upper()
        raw = re.sub(r"[RF]\s*$", "", raw, flags=re.I).rstrip()
    value = int(eval_formula(raw, rating, 0, extras))
    return value, suffix, additive


def format_avail(value: int, suffix: str = "") -> str:
    shown = int(value)
    mark = (suffix or "").upper()
    if mark not in {"R", "F"}:
        mark = ""
    if shown <= 0 and not mark:
        return "0"
    return f"{shown}{mark}"


def sum_avail(parts: list[tuple[int, str]]) -> tuple[int, str]:
    total = 0
    suffix = ""
    rank = {"": 0, "R": 1, "F": 2}
    for value, mark in parts:
        total += int(value or 0)
        token = (mark or "").upper()
        if rank.get(token, 0) > rank.get(suffix, 0):
            suffix = token
    return max(0, total), suffix


def parse_capacity(expr: str | None) -> tuple[bool, str]:
    raw = (expr or "").strip()
    if raw.startswith("[") and raw.endswith("]") and "/" not in raw:
        return True, raw[1:-1]
    if "/" in raw:
        return False, raw.split("/", 1)[0].strip()
    return False, raw


def split_capacity(expr: str | None) -> tuple[bool, str, str]:
    raw = (expr or "").strip()
    if not raw:
        return False, "", ""
    if "/" in raw:
        host, rest = raw.split("/", 1)
        rest = rest.strip()
        if rest.startswith("[") and rest.endswith("]"):
            rest = rest[1:-1]
        return False, host.strip(), rest
    if raw.startswith("[") and raw.endswith("]"):
        return True, "", raw[1:-1]
    return False, raw, ""


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
                "avail": _text(el.find("avail")),
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
                "required_parent_names": _parent_name_requirements(el),
                "limbslot": _text(el.find("limbslot")) or None,
                "selectside": el.find("selectside") is not None,
                "limbslotcount": _text(el.find("limbslotcount")) or "1",
                "add_weapon": _text(el.find("addweapon")),
                "devicerating": _text(el.find("devicerating")),
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


def parse_requirement_tree(el: ET.Element | None) -> list[dict[str, Any]]:
    if el is None:
        return []
    return [_parse_requirement_node(child) for child in list(el)]


def _parse_requirement_node(el: ET.Element) -> dict[str, Any]:
    tag = el.tag
    if tag in {"oneof", "allof", "group"}:
        return {"tag": tag, "children": [_parse_requirement_node(child) for child in list(el)]}
    if tag == "skill":
        if len(el) > 0:
            return {
                "tag": "skill",
                "name": _text(el.find("name")),
                "val": _int(el.find("val"), 1),
                "spec": _text(el.find("spec")),
                "type": _text(el.find("type")),
            }
        return {"tag": "skill", "name": _text(el), "val": 1, "spec": "", "type": ""}
    if tag == "ess":
        raw = _text(el) or "0"
        try:
            value = float(raw)
        except ValueError:
            value = 0.0
        node: dict[str, Any] = {"tag": "ess", "value": value}
        if el.attrib.get("grade"):
            node["grade"] = el.attrib.get("grade")
        return node
    node = {"tag": tag, "name": _text(el)}
    if el.attrib:
        node["attrs"] = dict(el.attrib)
    return node


# Common SR5 Matrix actions for Codeslinger-style picks.
MATRIX_ACTION_OPTIONS = [
    "Brute Force",
    "Check Overwatch Score",
    "Control Device",
    "Crack File",
    "Crash Program",
    "Data Spike",
    "Disarm Data Bomb",
    "Edit File",
    "Enter/Exit Host",
    "Erase Mark",
    "Erase Matrix Signature",
    "Format Device",
    "Full Matrix Defense",
    "Hack on the Fly",
    "Hide",
    "Invite Mark",
    "Jack Out",
    "Jam Signals",
    "Jump Into Rigged Device",
    "Matrix Perception",
    "Matrix Search",
    "Reboot Device",
    "Send Message",
    "Set Data Bomb",
    "Snoop",
    "Spoof Command",
    "Switch Interface Mode",
    "Trace Icon",
]

SPELL_SELECT_CATEGORIES = [
    "Combat",
    "Detection",
    "Health",
    "Illusion",
    "Manipulation",
    "Rituals",
]
STANDARD_SPIRIT_NAMES = [
    "Spirit of Air",
    "Spirit of Beasts",
    "Spirit of Earth",
    "Spirit of Fire",
    "Spirit of Man",
    "Spirit of Water",
]


def _limit_spell_category_needs_select(node: dict[str, Any]) -> bool:
    return node.get("tag") == "limitspellcategory" and not str(node.get("value") or "").strip()


def _limit_spirit_category_needs_select(node: dict[str, Any]) -> bool:
    if node.get("tag") != "limitspiritcategory":
        return False
    fields = node.get("fields") or {}
    if fields.get("spirit"):
        return False
    return not str(node.get("value") or "").strip()


def quality_needs_extra(bonus: list[dict[str, Any]] | None) -> bool:
    return any(
        node.get("tag")
        in {
            "selecttext",
            "selectattributes",
            "skillgroupdisablechoice",
            "selectquality",
            "selectside",
            "actiondicepool",
            "selectexpertise",
        }
        or _limit_spell_category_needs_select(node)
        or _limit_spirit_category_needs_select(node)
        for node in (bonus or [])
    )


def quality_extra_meta(bonus: list[dict[str, Any]] | None) -> dict[str, Any]:
    tags = {node.get("tag") for node in (bonus or [])}
    kind = None
    select_options: list[str] = []
    spirit_options: list[str] = []
    spell_exclude: list[str] = []
    expertise_skill = ""
    needs_spell_category = any(_limit_spell_category_needs_select(node) for node in (bonus or []))
    needs_spirit_category = any(_limit_spirit_category_needs_select(node) for node in (bonus or []))
    if "selectexpertise" in tags:
        kind = "expertise"
        for node in bonus or []:
            if node.get("tag") != "selectexpertise":
                continue
            limit = str((node.get("attrs") or {}).get("limittoskill") or node.get("value") or "").strip()
            expertise_skill = next((part.strip() for part in limit.split(",") if part.strip()), "")
            limit_spec = str((node.get("attrs") or {}).get("limittospecialization") or "").strip()
            if limit_spec:
                select_options = [part.strip() for part in limit_spec.split(",") if part.strip()]
            break
    elif "selectquality" in tags:
        kind = "quality"
        for node in bonus or []:
            if node.get("tag") != "selectquality":
                continue
            raw = (node.get("fields") or {}).get("quality") or node.get("value") or []
            for item in raw if isinstance(raw, list) else [raw]:
                text = str(item).strip()
                if text and text not in select_options:
                    select_options.append(text)
    elif "skillgroupdisablechoice" in tags:
        kind = "skillgroup"
    elif "selectside" in tags:
        kind = "side"
    elif "actiondicepool" in tags:
        kind = "matrix_action"
        select_options = list(MATRIX_ACTION_OPTIONS)
    elif needs_spell_category and needs_spirit_category:
        kind = "spell_spirit_category"
    elif needs_spell_category:
        kind = "spell_category"
    elif needs_spirit_category:
        kind = "spirit_category"
    elif "selectattributes" in tags or "selectattribute" in tags:
        kind = "attribute"
    elif "selecttext" in tags:
        kind = "text"
    if needs_spell_category:
        select_options = list(SPELL_SELECT_CATEGORIES)
        for node in bonus or []:
            if not _limit_spell_category_needs_select(node):
                continue
            exclude = str((node.get("attrs") or {}).get("exclude") or "").strip()
            if exclude:
                spell_exclude.append(exclude)
                select_options = [name for name in select_options if name != exclude]
    if needs_spirit_category:
        spirit_options = list(STANDARD_SPIRIT_NAMES)
    return {
        "extra_kind": kind,
        "select_options": select_options,
        "spirit_options": spirit_options,
        "spell_exclude": spell_exclude,
        "expertise_skill": expertise_skill,
    }


def _parent_name_requirements(el: ET.Element) -> list[str]:
    names: list[str] = []
    required_el = el.find("required")
    if required_el is None:
        return names
    for name_el in required_el.findall(".//parentdetails//name"):
        text = _text(name_el)
        if text and text not in names:
            names.append(text)
    return names


def parse_required(el: ET.Element | None) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {
        "bioware": [],
        "cyberware": [],
        "metatype": [],
        "quality": [],
        "power": [],
        "metamagicart": [],
        "metamagic": [],
    }
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


def _skill_specs(el: ET.Element) -> list[str]:
    specs: list[str] = []
    seen: set[str] = set()
    for node in el.findall("./specs/spec"):
        name = _text(node)
        if not name or name in seen:
            continue
        seen.add(name)
        specs.append(name)
    return specs


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
                "default": _text(el.find("default"), "True").lower() == "true",
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
                "knowledge": False,
                "specs": _skill_specs(el),
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
                "specs": _skill_specs(el),
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
                "forbidden": parse_required(el.find("forbidden")),
                "required": parse_required(el.find("required")),
                "required_tree": parse_requirement_tree(el.find("required")),
                "forbidden_tree": parse_requirement_tree(el.find("forbidden")),
                "needs_extra": quality_needs_extra(bonus),
                "extra_kind": extra_meta.get("extra_kind"),
                "select_options": extra_meta.get("select_options") or [],
                "spirit_options": extra_meta.get("spirit_options") or [],
                "expertise_skill": extra_meta.get("expertise_skill") or "",
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


MATRIX_ATTRIBUTES = ("Attack", "Sleaze", "Data Processing", "Firewall")


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


SKIP_WEAPON_CATEGORIES = {
    "Cyberweapon",
    "Bio-Weapon",
    "Quality",
    "Underbarrel Weapons",
    "Micro-Drone Weapons",
}


def _is_variable_cost(cost: str) -> bool:
    return "Variable" in (cost or "")


def _armor_included_mods(el: ET.Element) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for name_el in el.findall("./mods/name"):
        name = _text(name_el)
        if not name:
            continue
        rating = 1
        raw = name_el.attrib.get("rating") or ""
        if raw:
            try:
                rating = int(float(raw))
            except ValueError:
                rating = 1
        items.append({"name": name, "rating": max(1, rating)})
    return items


def _armor_mod_required(el: ET.Element | None) -> dict[str, list[str]]:
    names: list[str] = []
    mods: list[str] = []
    if el is None:
        return {"names": names, "mods": mods}
    for child in el.findall("./parentdetails/name"):
        text = _text(child)
        if text:
            names.append(text)
    for child in el.findall(".//armormod"):
        text = _text(child)
        if text:
            mods.append(text)
    return {"names": names, "mods": mods}


def load_armor() -> list[dict[str, Any]]:
    path = DATA_DIR / "armor.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./armors/armor"):
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        armor_id = _text(el.find("id"))
        cost = _text(el.find("cost"), "0")
        if not name or not armor_id or _is_variable_cost(cost):
            continue
        armor_raw = _text(el.find("armor"), "0")
        rating_max = _int(el.find("rating"), 0)
        items.append(
            {
                "id": armor_id,
                "name": name,
                "category": _text(el.find("category"), "Armor"),
                "armor": armor_raw,
                "armorcapacity": _text(el.find("armorcapacity")),
                "avail": _text(el.find("avail")),
                "cost": cost,
                "minrating": 1 if rating_max > 0 else 0,
                "maxrating": rating_max,
                "additive": armor_raw.startswith("+") or armor_raw.startswith("-"),
                "addmodcategories": [_text(c) for c in el.findall("addmodcategory") if _text(c)],
                "included_mods": _armor_included_mods(el),
                "bonus": parse_bonus(el.find("bonus")),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def load_armor_mods() -> list[dict[str, Any]]:
    path = DATA_DIR / "armor.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./mods/mod"):
        name = _text(el.find("name"))
        mod_id = _text(el.find("id"))
        cost = _text(el.find("cost"), "0")
        if not name or not mod_id or name.startswith("ID ERROR"):
            continue
        rating_max = _int(el.find("maxrating"), 0) or _int(el.find("rating"), 0)
        hidden = el.find("hide") is not None
        bonus_el = el.find("bonus")
        unique = (bonus_el.attrib.get("unique") or "") if bonus_el is not None else ""
        required = _armor_mod_required(el.find("required"))
        items.append(
            {
                "id": mod_id,
                "name": name,
                "category": _text(el.find("category"), "General"),
                "armor": _text(el.find("armor"), "0"),
                "armorcapacity": _text(el.find("armorcapacity")),
                "avail": _text(el.find("avail")),
                "cost": cost,
                "minrating": 1 if rating_max > 1 else 0,
                "maxrating": rating_max,
                "purchasable": (
                    not hidden
                    and not _is_variable_cost(cost)
                    and cost.strip() not in {"0", ""}
                ),
                "unique": unique,
                "required_names": list(required.get("names") or []),
                "required_mods": list(required.get("mods") or []),
                "bonus": parse_bonus(bonus_el),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def _weapon_category_types(root: ET.Element) -> dict[str, str]:
    types: dict[str, str] = {}
    for el in root.findall("./categories/category"):
        name = _text(el)
        kind = (el.attrib.get("type") or "").strip()
        if name and kind:
            types[name] = kind
    return types


def _parse_weaponbonus(el: ET.Element | None) -> dict[str, str]:
    if el is None:
        return {}
    out: dict[str, str] = {}
    for child in list(el):
        text = _text(child)
        if text:
            out[child.tag] = text
    return out


def load_weapons() -> list[dict[str, Any]]:
    path = DATA_DIR / "weapons.xml"
    if not path.exists():
        return []
    root = ET.parse(path).getroot()
    category_types = _weapon_category_types(root)
    items: list[dict[str, Any]] = []
    for el in root.findall("./weapons/weapon"):
        hidden = el.find("hide") is not None
        from_cyberware = _text(el.find("cyberware")).lower() == "true"
        if hidden and not from_cyberware:
            continue
        name = _text(el.find("name"))
        weapon_id = _text(el.find("id"))
        category = _text(el.find("category"))
        cost = _text(el.find("cost"), "0")
        if not name or not weapon_id or category in SKIP_WEAPON_CATEGORIES or _is_variable_cost(cost):
            continue
        weapon_type = _text(el.find("weapontype")) or category_types.get(category) or category.lower()
        items.append(
            {
                "id": weapon_id,
                "name": name,
                "category": category,
                "type": _text(el.find("type")),
                "weapon_type": weapon_type,
                "accuracy": _text(el.find("accuracy")),
                "reach": _text(el.find("reach")),
                "damage": _text(el.find("damage")),
                "ap": _text(el.find("ap")),
                "mode": _text(el.find("mode")),
                "rc": _text(el.find("rc")),
                "ammo": _text(el.find("ammo")),
                "conceal": _text(el.find("conceal")),
                "avail": _text(el.find("avail")),
                "cost": cost,
                "mounts": [_text(m) for m in el.findall("./accessorymounts/mount") if _text(m)],
                "included": [_text(a.find("name")) for a in el.findall("./accessories/accessory") if _text(a.find("name"))],
                "hidden": hidden,
                "from_cyberware": from_cyberware,
                "useskill": _text(el.find("useskill")),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def _weapon_constraints(el: ET.Element | None) -> dict[str, Any]:
    names: list[str] = []
    categories: list[str] = []
    types: list[str] = []
    accessories: list[str] = []
    conceal_lte: int | None = None
    if el is None:
        return {
            "names": names,
            "categories": categories,
            "types": types,
            "accessories": accessories,
            "conceal_lte": conceal_lte,
        }
    for child in el.iter():
        tag = child.tag
        text = _text(child)
        if tag == "name" and text:
            names.append(text)
        elif tag in {"category", "ammocategory"} and text:
            categories.append(text)
        elif tag == "type" and text:
            types.append(text)
        elif tag == "accessory" and text:
            accessories.append(text)
        elif tag == "conceal" and text:
            try:
                value = int(float(text))
            except ValueError:
                continue
            if (child.attrib.get("operation") or "") == "lessthanequals":
                conceal_lte = value
    return {
        "names": names,
        "categories": categories,
        "types": types,
        "accessories": accessories,
        "conceal_lte": conceal_lte,
    }


def load_weapon_accessories() -> list[dict[str, Any]]:
    path = DATA_DIR / "weapons.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./accessories/accessory"):
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        accessory_id = _text(el.find("id"))
        cost = _text(el.find("cost"), "0")
        if not name or not accessory_id or name.startswith("ID ERROR"):
            continue
        mount_raw = _text(el.find("mount"))
        rating_max = _int(el.find("rating"), 0)
        special_modification = _text(el.find("specialmodification")).lower() == "true"
        special_modification_cost = 0
        if special_modification:
            special_modification_cost = 1
            required_el = el.find("required")
            if required_el is not None:
                for child in required_el.iter("specialmodificationlimit"):
                    try:
                        special_modification_cost = max(1, int(_text(child) or "1"))
                    except ValueError:
                        continue
        items.append(
            {
                "id": accessory_id,
                "name": name,
                "mounts": [part for part in mount_raw.split("/") if part],
                "avail": _text(el.find("avail")),
                "cost": cost,
                "purchasable": not _is_variable_cost(cost) and cost.strip() not in {"0", ""},
                "accuracy": _text(el.find("accuracy")),
                "rc": _text(el.find("rc")),
                "conceal": _text(el.find("conceal")),
                "damage": _text(el.find("damage")),
                "ap": _text(el.find("ap")),
                "reach": _text(el.find("reach")),
                "modifyammocapacity": _text(el.find("modifyammocapacity")),
                "specialmodification": special_modification,
                "special_modification_cost": special_modification_cost,
                "minrating": 1 if rating_max > 0 else 0,
                "maxrating": rating_max,
                "required": _weapon_constraints(el.find("required")),
                "forbidden": _weapon_constraints(el.find("forbidden")),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def _is_pi_tac_commlink(name: str, category: str) -> bool:
    return category == "PI-Tac" and name.startswith("PI-Tac")


def load_commlinks() -> list[dict[str, Any]]:
    path = DATA_DIR / "gear.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./gears/gear"):
        category = _text(el.find("category"))
        name = _text(el.find("name"))
        if category != "Commlinks" and not _is_pi_tac_commlink(name, category):
            continue
        if el.find("hide") is not None:
            continue
        gear_id = _text(el.find("id"))
        cost = _text(el.find("cost"), "0")
        if not name or not gear_id or _is_variable_cost(cost):
            continue
        rating_max = _int(el.find("rating"), 0)
        device = _text(el.find("devicerating"), "0")
        processing = _text(el.find("dataprocessing"))
        firewall = _text(el.find("firewall"))
        if _is_pi_tac_commlink(name, category):
            processing = processing or device
            firewall = firewall or device
        items.append(
            {
                "id": gear_id,
                "name": name,
                "category": category or "Commlinks",
                "cost": cost,
                "avail": _text(el.find("avail")),
                "minrating": _int(el.find("minrating"), 1) if rating_max > 0 else 0,
                "maxrating": rating_max,
                "devicerating": device,
                "dataprocessing": processing or "0",
                "firewall": firewall or "0",
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def _load_gear_categories(categories: set[str], *, allow_brackets: bool = False) -> list[dict[str, Any]]:
    path = DATA_DIR / "gear.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./gears/gear"):
        if el.find("hide") is not None:
            continue
        category = _text(el.find("category"))
        if category not in categories:
            continue
        name = _text(el.find("name"))
        gear_id = _text(el.find("id"))
        cost = _text(el.find("cost"), "0")
        if not name or not gear_id or name.startswith("ID ERROR") or _is_variable_cost(cost):
            continue
        if name.startswith("[") and not allow_brackets:
            continue
        rating_max = _int(el.find("rating"), 0)
        cap_raw = _text(el.find("capacity"))
        plugin, cap_expr = parse_capacity(cap_raw)
        _plugin_only, host_expr, plugin_expr = split_capacity(cap_raw)
        included: list[dict[str, Any]] = []
        ammo_types = [part.strip() for part in _text(el.find("ammoforweapontype")).split(",") if part.strip()]
        weapon_details = ""
        bonus_el = el.find("bonus")
        if bonus_el is not None:
            select = bonus_el.find("selectweapon")
            if select is not None:
                weapon_details = (select.attrib.get("weapondetails") or _text(select)).strip()
        for gift in el.findall("./gears/usegear"):
            gift_name = _text(gift.find("name"))
            if not gift_name:
                continue
            included.append(
                {
                    "name": gift_name,
                    "category": _text(gift.find("category")),
                    "rating": max(1, _int(gift.find("rating"), 1)),
                    "capacity": _text(gift.find("capacity")),
                }
            )
        items.append(
            {
                "id": gear_id,
                "name": name,
                "category": category,
                "cost": cost,
                "avail": _text(el.find("avail")),
                "minrating": 1 if rating_max > 0 else 0,
                "maxrating": rating_max,
                "capacity": cap_expr,
                "plugin": plugin,
                "host_capacity": host_expr,
                "plugin_capacity": plugin_expr,
                "requireparent": el.find("requireparent") is not None,
                "addoncategories": [_text(c) for c in el.findall("addoncategory") if _text(c)],
                "required_names": [
                    _text(n)
                    for n in (el.findall("./required/geardetails//name") if el.find("./required/geardetails") is not None else [])
                    if _text(n)
                ],
                "required_categories": [
                    _text(n)
                    for n in (el.findall("./required/geardetails//category") if el.find("./required/geardetails") is not None else [])
                    if _text(n)
                ],
                "included": included,
                "ammo_weapon_types": ammo_types,
                "costfor": max(0, _int(el.find("costfor"), 0)),
                "weapon_details": weapon_details,
                "add_weapon": _text(el.find("addweapon")),
                "weaponbonus": _parse_weaponbonus(el.find("weaponbonus")),
                "bonus": parse_bonus(el.find("bonus")),
                "devicerating": _text(el.find("devicerating"), "0"),
                "attack": _text(el.find("attack"), "0"),
                "sleaze": _text(el.find("sleaze"), "0"),
                "dataprocessing": _text(el.find("dataprocessing"), "0"),
                "firewall": _text(el.find("firewall"), "0"),
                "attributearray": _text(el.find("attributearray")),
                "programs": _text(el.find("programs"), "0"),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def load_cyberdecks() -> list[dict[str, Any]]:
    return _load_gear_categories({"Cyberdecks"})


def load_rccs() -> list[dict[str, Any]]:
    return _load_gear_categories({"Rigger Command Consoles"})


def load_optics() -> list[dict[str, Any]]:
    return _load_gear_categories(
        {"Vision Devices", "Audio Devices", "Vision Enhancements", "Audio Enhancements"}
    )


PROGRAM_HOSTS = {
    "Common Programs": "cyberdecks",
    "Hacking Programs": "cyberdecks",
    "Autosofts": "rccs",
}


def _extra_kind(bonus: list[dict[str, Any]] | None, name: str = "") -> str:
    if str(name or "").startswith("Group Autosoft"):
        return "group"
    tags = {node.get("tag") for node in (bonus or [])}
    if "selectskill" in tags or "activesoft" in tags or "skillsoft" in tags or "knowsoft" in tags or "linguasoft" in tags:
        return "skill"
    if "selecttext" in tags or "selectrestricted" in tags or "selecttradition" in tags:
        return "text"
    return ""


GEAR_SPECIALIZED_CATEGORIES = {
    "Commlinks",
    "Cyberdecks",
    "Rigger Command Consoles",
    "Vision Devices",
    "Audio Devices",
    "Vision Enhancements",
    "Audio Enhancements",
    "Common Programs",
    "Hacking Programs",
    "Autosofts",
    "Software",
    "Sensors",
    "Sensor Housings",
    "Sensor Functions",
}

GEAR_SKIP_CATEGORIES = GEAR_SPECIALIZED_CATEGORIES | {
    "Foci",
    "Formulae",
    "Custom",
    "Custom Cyberdeck Attributes",
    "Custom Drug",
    "Paydata",
    "Commlink Apps",
    "Electronic Modification",
    "Drug Grades",
    "Currency",
}

GEAR_RATING_CAP = 24


def load_gear() -> list[dict[str, Any]]:
    path = DATA_DIR / "gear.xml"
    if not path.exists():
        return []
    cats: set[str] = set()
    for el in ET.parse(path).getroot().findall("./gears/gear"):
        cat = _text(el.find("category"))
        if cat:
            cats.add(cat)
    items: list[dict[str, Any]] = []
    for item in _load_gear_categories(cats - GEAR_SKIP_CATEGORIES):
        cost = str(item.get("cost") or "").strip()
        if "Parent Cost" in cost:
            continue
        if cost.lstrip().startswith("+"):
            item["requireparent"] = True
        if item.get("required_names") or item.get("required_categories"):
            item["requireparent"] = True
        if _is_pi_tac_commlink(str(item.get("name") or ""), str(item.get("category") or "")):
            continue
        if item.get("category") == "PI-Tac Programs":
            item["requireparent"] = True
        if cost in {"0", ""} and not item.get("requireparent"):
            continue
        rating_max = int(item.get("maxrating") or 0)
        if rating_max > GEAR_RATING_CAP:
            item["maxrating"] = 12
            item["minrating"] = 1
        name = item.get("name") or ""
        item["extra_kind"] = _extra_kind(item.get("bonus"), name)
        item["needs_extra"] = bool(item["extra_kind"])
        items.append(item)
    return items


def load_programs() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in _load_gear_categories(
        {"Common Programs", "Hacking Programs", "Autosofts"},
        allow_brackets=True,
    ):
        name = item.get("name") or ""
        if name.startswith("[") and item.get("category") != "Autosofts":
            continue
        if "Parent Cost" in (item.get("cost") or ""):
            continue
        item["requireparent"] = True
        item["program_host"] = PROGRAM_HOSTS.get(item.get("category") or "", "cyberdecks")
        item["extra_kind"] = _extra_kind(item.get("bonus"), name)
        item["needs_extra"] = bool(item["extra_kind"])
        items.append(item)
    return items


def load_apps() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in _load_gear_categories({"Software"}):
        if "Parent Cost" in (item.get("cost") or ""):
            continue
        if (item.get("cost") or "").strip() in {"0", ""}:
            continue
        item["requireparent"] = True
        item["extra_kind"] = _extra_kind(item.get("bonus"), item.get("name") or "")
        item["needs_extra"] = bool(item["extra_kind"])
        items.append(item)
    return items


def load_sensors() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in _load_gear_categories({"Sensors", "Sensor Housings", "Sensor Functions"}):
        if "Parent Cost" in (item.get("cost") or ""):
            continue
        item["requireparent"] = item.get("category") == "Sensor Functions"
        items.append(item)
    return items


def _vehicle_constraints(el: ET.Element | None) -> dict[str, Any]:
    names: list[str] = []
    category_contains: list[str] = []
    category_equals: list[str] = []
    body_lte: int | None = None
    body_gte: int | None = None
    if el is None:
        return {
            "names": names,
            "category_contains": category_contains,
            "category_equals": category_equals,
            "body_lte": body_lte,
            "body_gte": body_gte,
        }
    for details in el.findall("vehicledetails"):
        for child in list(details):
            text = _text(child)
            if not text:
                continue
            op = child.attrib.get("operation") or ""
            if child.tag == "name":
                names.append(text)
            elif child.tag == "category":
                if op == "contains":
                    category_contains.append(text)
                else:
                    category_equals.append(text)
            elif child.tag == "body":
                try:
                    value = int(float(text))
                except ValueError:
                    continue
                if op == "lessthanequals":
                    body_lte = value
                elif op in {"greaterthan", "greaterthanorequals"}:
                    body_gte = value
    return {
        "names": names,
        "category_contains": category_contains,
        "category_equals": category_equals,
        "body_lte": body_lte,
        "body_gte": body_gte,
    }


def _mount_part_requirements(el: ET.Element | None) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"control": [], "flexibility": [], "visibility": []}
    if el is None:
        return out
    for details in el.findall("weaponmountdetails"):
        for child in list(details):
            text = _text(child)
            if child.tag in out and text:
                out[child.tag].append(text)
    return out


def load_vehicle_names() -> list[str]:
    path = DATA_DIR / "vehicles.xml"
    if not path.exists():
        return []
    names: list[str] = []
    for el in ET.parse(path).getroot().findall("./vehicles/vehicle"):
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        if name and not name.startswith("ID ERROR"):
            names.append(name)
    return names


def load_vehicle_mods() -> list[dict[str, Any]]:
    path = DATA_DIR / "vehicles.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./mods/mod"):
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        mod_id = _text(el.find("id"))
        cost = _text(el.find("cost"), "0")
        if not name or not mod_id or name.startswith("ID ERROR"):
            continue
        rating_raw = _text(el.find("rating"))
        min_raw = _text(el.find("minrating"))
        qty_rating = rating_raw.lower() == "qty"
        rating_max = _int(el.find("rating"), 0) if rating_raw.isdigit() else 0
        subs_el = el.find("subsystems")
        items.append(
            {
                "id": mod_id,
                "name": name,
                "category": _text(el.find("category")),
                "avail": _text(el.find("avail")),
                "cost": cost,
                "slots": _text(el.find("slots"), "0"),
                "rating": rating_raw,
                "minrating": _int(el.find("minrating"), 1) if rating_max > 0 else 0,
                "maxrating": rating_max,
                "minrating_expr": min_raw,
                "maxrating_expr": rating_raw if rating_raw and not rating_raw.isdigit() else "",
                "purchasable": not _is_variable_cost(cost) and not qty_rating and cost.strip() not in {"0", ""},
                "bonus": parse_bonus(el.find("bonus")),
                "required": _vehicle_constraints(el.find("required")),
                "forbidden": _vehicle_constraints(el.find("forbidden")),
                "optionaldrone": el.find("optionaldrone") is not None,
                "capacity": _text(el.find("capacity")),
                "subsystems": [
                    _text(sub)
                    for sub in list(subs_el if subs_el is not None else [])
                    if sub.tag == "subsystem" and _text(sub)
                ],
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def load_weapon_mounts() -> list[dict[str, Any]]:
    path = DATA_DIR / "vehicles.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./weaponmounts/weaponmount"):
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        mount_id = _text(el.find("id"))
        cost = _text(el.find("cost"), "0")
        if not name or not mount_id or name.startswith("ID ERROR") or _is_variable_cost(cost):
            continue
        required = el.find("required")
        forbidden = el.find("forbidden")
        items.append(
            {
                "id": mount_id,
                "name": name,
                "category": _text(el.find("category")),
                "avail": _text(el.find("avail")),
                "cost": cost,
                "slots": _text(el.find("slots"), "0"),
                "required": _vehicle_constraints(required),
                "forbidden": _vehicle_constraints(forbidden),
                "required_parts": _mount_part_requirements(required),
                "forbidden_parts": _mount_part_requirements(forbidden),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def _drone_included_gears(el: ET.Element) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for gift in el.findall("./gears/gear"):
        name = _text(gift.find("name")) or _text(gift)
        if not name:
            continue
        items.append(
            {
                "name": name,
                "category": _text(gift.find("category")),
                "rating": max(1, _int(gift.find("rating"), 1)),
                "maxrating": _int(gift.find("maxrating"), 0),
            }
        )
    return items


def _drone_included_mods(el: ET.Element) -> list[str]:
    return [_text(node) for node in el.findall("./mods/name") if _text(node)]


def _drone_included_mounts(el: ET.Element) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for node in el.findall("./weaponmounts/weaponmount"):
        items.append(
            {
                "size": _text(node.find("size")),
                "visibility": _text(node.find("visibility")),
                "flexibility": _text(node.find("flexibility")),
                "control": _text(node.find("control")),
                "allowedweapons": _text(node.find("allowedweapons")),
            }
        )
    return items


def _load_vehicle_entries(*, drones: bool) -> list[dict[str, Any]]:
    path = DATA_DIR / "vehicles.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./vehicles/vehicle"):
        if el.find("hide") is not None:
            continue
        category = _text(el.find("category"))
        if category.startswith("Drones") != drones:
            continue
        name = _text(el.find("name"))
        vehicle_id = _text(el.find("id"))
        cost = _text(el.find("cost"), "0")
        if not name or not vehicle_id or name.startswith("ID ERROR") or _is_variable_cost(cost) or cost.strip() in {"0", ""}:
            continue
        items.append(
            {
                "id": vehicle_id,
                "name": name,
                "category": category,
                "handling": _text(el.find("handling")),
                "speed": _text(el.find("speed")),
                "accel": _text(el.find("accel")),
                "body": _text(el.find("body")),
                "armor": _text(el.find("armor")),
                "pilot": _text(el.find("pilot")),
                "sensor": _text(el.find("sensor")),
                "seats": _text(el.find("seats")),
                "avail": _text(el.find("avail")),
                "cost": cost,
                "included_gears": _drone_included_gears(el),
                "included_mods": _drone_included_mods(el),
                "included_weaponmounts": _drone_included_mounts(el),
                "modslots": _int(el.find("modslots")) if _text(el.find("modslots")) else None,
                "powertrainmodslots": _int(el.find("powertrainmodslots")),
                "protectionmodslots": _int(el.find("protectionmodslots")),
                "weaponmodslots": _int(el.find("weaponmodslots")),
                "bodymodslots": _int(el.find("bodymodslots")),
                "electromagneticmodslots": _int(el.find("electromagneticmodslots")),
                "cosmeticmodslots": _int(el.find("cosmeticmodslots")),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def load_drones() -> list[dict[str, Any]]:
    return _load_vehicle_entries(drones=True)


def load_vehicles() -> list[dict[str, Any]]:
    return _load_vehicle_entries(drones=False)


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


def load_drug_grades() -> list[dict[str, Any]]:
    path = DATA_DIR / "gear.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./gears/gear"):
        if _text(el.find("category")) != "Drug Grades":
            continue
        if el.find("hide") is not None:
            continue
        name = _text(el.find("name"))
        gear_id = _text(el.find("id"))
        if not name or not gear_id:
            continue
        items.append(
            {
                "id": gear_id,
                "name": name,
                "category": "Drug Grades",
                "cost": _text(el.find("cost"), "0"),
                "avail": _text(el.find("avail")),
                "minrating": 0,
                "maxrating": 0,
                "capacity": "",
                "plugin": True,
                "host_capacity": "",
                "plugin_capacity": "0",
                "requireparent": True,
                "addoncategories": [],
                "required_names": [],
                "required_categories": ["Drugs", "Toxins", "Chemicals"],
                "included": [],
                "ammo_weapon_types": [],
                "costfor": 0,
                "weapon_details": "",
                "add_weapon": "",
                "weaponbonus": {},
                "bonus": parse_bonus(el.find("bonus")),
                "devicerating": "0",
                "attack": "0",
                "sleaze": "0",
                "dataprocessing": "0",
                "firewall": "0",
                "attributearray": "",
                "programs": "0",
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
                "extra_kind": "",
                "needs_extra": False,
            }
        )
    return items


def load_martial_art_techniques() -> list[dict[str, Any]]:
    path = DATA_DIR / "martialarts.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./techniques/technique"):
        name = _text(el.find("name"))
        tech_id = _text(el.find("id"))
        if not name or not tech_id:
            continue
        items.append(
            {
                "id": tech_id,
                "name": name,
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
                "bonus": parse_bonus(el.find("bonus")),
            }
        )
    return items


def load_martial_arts() -> list[dict[str, Any]]:
    path = DATA_DIR / "martialarts.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./martialarts/martialart"):
        name = _text(el.find("name"))
        art_id = _text(el.find("id"))
        if not name or not art_id:
            continue
        techniques = [
            tech_name
            for tech in el.findall("./techniques/technique")
            if (tech_name := _text(tech.find("name")))
        ]
        cost_el = el.find("cost")
        items.append(
            {
                "id": art_id,
                "name": name,
                "cost": _int(cost_el, 7) if cost_el is not None else 7,
                "is_quality": _text(el.find("isquality"), "False").lower() == "true",
                "all_techniques": el.find("alltechniques") is not None,
                "techniques": techniques,
                "bonus": parse_bonus(el.find("bonus")),
                "required_tree": parse_requirement_tree(el.find("required")),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def load_metamagics() -> list[dict[str, Any]]:
    path = DATA_DIR / "metamagic.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./metamagics/metamagic"):
        name = _text(el.find("name"))
        mid = _text(el.find("id"))
        if not name or not mid:
            continue
        items.append(
            {
                "id": mid,
                "name": name,
                "adept": _text(el.find("adept"), "False").lower() == "true",
                "magician": _text(el.find("magician"), "False").lower() == "true",
                "repeatable": _text(el.find("limit"), "True").lower() == "false",
                "bonus": parse_bonus(el.find("bonus")),
                "required_tree": parse_requirement_tree(el.find("required")),
                "required": parse_required(el.find("required")),
                "source": _text(el.find("source")),
                "page": _text(el.find("page")),
            }
        )
    return items


def load_magic_arts() -> list[dict[str, Any]]:
    path = DATA_DIR / "metamagic.xml"
    if not path.exists():
        return []
    items: list[dict[str, Any]] = []
    for el in ET.parse(path).getroot().findall("./arts/art"):
        name = _text(el.find("name"))
        art_id = _text(el.find("id"))
        if not name or not art_id:
            continue
        items.append(
            {
                "id": art_id,
                "name": name,
                "bonus": parse_bonus(el.find("bonus")),
                "required_tree": parse_requirement_tree(el.find("required")),
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
                        "spells": _int(t.find("spells")),
                        "cfp": _int(t.find("cfp")),
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
    weapons = load_weapons()
    gear = load_gear()
    drug_grades = load_drug_grades()
    gear_ids = {item["id"] for item in gear}
    for grade in drug_grades:
        if grade["id"] not in gear_ids:
            gear.append(grade)
            gear_ids.add(grade["id"])
    cyberware = load_cyberware()
    bioware = load_bioware()
    weapon_ids = {item["name"]: item["id"] for item in weapons}
    gear_for_weapon: dict[str, str] = {}
    for item in gear:
        add_name = str(item.get("add_weapon") or "")
        if not add_name:
            continue
        item["add_weapon_id"] = weapon_ids.get(add_name) or ""
        gear_for_weapon[add_name] = item["id"]
    for item in list(cyberware.get("items") or []) + list(bioware.get("items") or []):
        add_name = str(item.get("add_weapon") or "")
        if add_name:
            item["add_weapon_id"] = weapon_ids.get(add_name) or ""
    for item in weapons:
        gear_id = gear_for_weapon.get(item["name"]) or ""
        item["from_gear"] = bool(gear_id)
        item["add_gear_id"] = gear_id
    drugs = [item for item in gear if item.get("category") in {"Drugs", "Toxins", "Chemicals"}]
    skills = load_skills()
    qualities = load_qualities()
    skill_specs = {
        str(skill.get("name") or ""): list(skill.get("specs") or [])
        for skill in (skills.get("skills") or [])
        if skill.get("name")
    }
    for quality in qualities:
        if quality.get("extra_kind") != "expertise":
            continue
        skill_name = str(quality.get("expertise_skill") or "").strip()
        if skill_name and not quality.get("select_options"):
            quality["select_options"] = list(skill_specs.get(skill_name) or [])
    return {
        "metatypes": playable,
        "all_metatypes": all_by_name,
        "skills": skills,
        "qualities": qualities,
        "cyberware": cyberware,
        "bioware": bioware,
        "powers": load_powers(),
        "enhancements": load_enhancements(),
        "mentors": load_mentors(),
        "spells": load_spells(),
        "traditions": load_traditions(),
        "spirits": load_spirits(),
        "complex_forms": load_complex_forms(),
        "streams": load_streams(),
        "sprites": load_sprites(),
        "foci": load_foci(),
        "qi_focus": load_qi_focus(),
        "armor": load_armor(),
        "armor_mods": load_armor_mods(),
        "weapons": weapons,
        "weapon_accessories": load_weapon_accessories(),
        "commlinks": load_commlinks(),
        "cyberdecks": load_cyberdecks(),
        "rccs": load_rccs(),
        "optics": load_optics(),
        "programs": load_programs(),
        "apps": load_apps(),
        "sensors": load_sensors(),
        "gear": gear,
        "drugs": drugs,
        "drug_grades": drug_grades,
        "drones": load_drones(),
        "vehicles": load_vehicles(),
        "vehicle_mods": load_vehicle_mods(),
        "weapon_mounts": load_weapon_mounts(),
        "vehicle_names": load_vehicle_names(),
        "lifestyles": load_lifestyles(),
        "lifestyle_qualities": load_lifestyle_qualities(),
        "martial_arts": load_martial_arts(),
        "martial_art_techniques": load_martial_art_techniques(),
        "metamagics": load_metamagics(),
        "magic_arts": load_magic_arts(),
        "echoes": load_echoes(),
        "priorities": load_priorities(),
        "translations": translations,
        "ui_strings": load_ui_strings(),
    }


def reset_catalog() -> None:
    catalog.cache_clear()
