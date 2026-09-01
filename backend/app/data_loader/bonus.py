"""Parsers for the ``<bonus>`` / ``<required>`` / ``<forbidden>`` XML
sub-trees, the select-power-slot shape, and the quality "needs a player
pick" inspectors. Shared by every loader that reads a bonus block.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Mapping
from typing import Any

from ._xml import MATRIX_ATTRIBUTES, _int, _text


def _parse_weaponbonus(el: ET.Element | None) -> dict[str, str]:
    if el is None:
        return {}
    out: dict[str, str] = {}
    for child in list(el):
        text = _text(child)
        if text:
            out[child.tag] = text
    return out


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


def _weapon_category_dv_select_skills(node: dict[str, Any]) -> list[str]:
    if node.get("tag") != "weaponcategorydv":
        return []
    attrs = (node.get("field_attrs") or {}).get("selectskill") or {}
    limit = str(attrs.get("limittoskill") or "").strip()
    return [part.strip() for part in limit.split(",") if part.strip()]


def _weaponskillaccuracy_needs_select(node: dict[str, Any]) -> bool:
    if node.get("tag") != "weaponskillaccuracy":
        return False
    if str((node.get("fields") or {}).get("name") or "").strip():
        return False
    fields = node.get("fields") or {}
    attrs = (node.get("field_attrs") or {}).get("selectskill") or {}
    return "selectskill" in fields or bool(attrs)


def _weaponskillaccuracy_select_attrs(node: dict[str, Any]) -> dict[str, str]:
    if not _weaponskillaccuracy_needs_select(node):
        return {}
    return {str(k): str(v) for k, v in ((node.get("field_attrs") or {}).get("selectskill") or {}).items()}


def _filter_active_skill_names(skills: list[dict[str, Any]], attrs: dict[str, str]) -> list[str]:
    names = {part.strip() for part in str(attrs.get("limittoskill") or "").split(",") if part.strip()}
    cats = {
        part.strip()
        for part in str(attrs.get("limittocategory") or attrs.get("skillcategory") or "").split(",")
        if part.strip()
    }
    exclude_cats = {part.strip() for part in str(attrs.get("excludecategory") or "").split(",") if part.strip()}
    out: list[str] = []
    for skill in skills:
        if skill.get("exotic"):
            continue
        name = str(skill.get("name") or "")
        if not name:
            continue
        if names and name not in names:
            continue
        category = str(skill.get("category") or "")
        if cats and category not in cats:
            continue
        if exclude_cats and category in exclude_cats:
            continue
        out.append(name)
    return sorted(set(out))


def selecttext_catalog_options(attrs: dict[str, Any], catalog_data: Mapping[str, Any]) -> list[str]:
    xml = str(attrs.get("xml") or "")
    xpath = str(attrs.get("xpath") or "")
    if "vehicles.xml" in xml:
        names = list(catalog_data.get("vehicle_names") or [])
        if not names:
            names = [item["name"] for item in catalog_data.get("drones") or []]
        return names
    if "weapons.xml" in xml:
        weapons = catalog_data.get("weapons") or []
        if "Melee" in xpath:
            return [item["name"] for item in weapons if item.get("type") == "Melee"]
        if "Ranged" in xpath:
            return [item["name"] for item in weapons if item.get("type") == "Ranged"]
        return [item["name"] for item in weapons]
    if "skills.xml" in xml:
        skills = catalog_data.get("skills") or {}
        names = [s["name"] for s in skills.get("skills") or []]
        if "knowledge" in xpath.lower():
            names += [s["name"] for s in skills.get("knowledge") or []]
        return names
    if "traditions.xml" in xml:
        spirits = catalog_data.get("spirits") or []
        names = [str(item.get("name") or "") for item in spirits if item.get("name")]
        if "Watcher" in xpath or "Homunculus" in xpath:
            names = [name for name in names if "Watcher" not in name and "Homunculus" not in name]
        return names
    if "strings.xml" in xml and "matrixattributes" in xpath.lower():
        return list(MATRIX_ATTRIBUTES)
    if "programs.xml" in xml:
        return [str(item.get("name") or "") for item in catalog_data.get("programs") or [] if item.get("name")]
    return []


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
        or bool(_weapon_category_dv_select_skills(node))
        or _weaponskillaccuracy_needs_select(node)
        or (node.get("tag") == "addspirit" and not str((node.get("attrs") or {}).get("skill") or "").strip())
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
    weapon_dv_skills: list[str] = []
    weapon_acc_attrs: dict[str, str] = {}
    for node in bonus or []:
        skills = _weapon_category_dv_select_skills(node)
        if skills:
            weapon_dv_skills = skills
            break
    for node in bonus or []:
        if _weaponskillaccuracy_needs_select(node):
            weapon_acc_attrs = _weaponskillaccuracy_select_attrs(node)
            break
    add_spirit_fixed = sum(
        1
        for node in (bonus or [])
        if node.get("tag") == "addspirit" and not str((node.get("attrs") or {}).get("skill") or "").strip()
    )
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
    elif weapon_dv_skills:
        kind = "weapon_skill"
        select_options = list(weapon_dv_skills)
    elif weapon_acc_attrs or any(_weaponskillaccuracy_needs_select(node) for node in (bonus or [])):
        kind = "weapon_skill"
        # Options filled later in catalog() once skills.xml is loaded.
    elif add_spirit_fixed:
        kind = "add_spirit"
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
        "add_spirit_count": add_spirit_fixed,
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


def _bonus_fields(
    child: ET.Element,
) -> tuple[dict[str, Any], dict[str, list[str]], dict[str, dict[str, str]]]:
    fields: dict[str, Any] = {}
    nested: dict[str, list[str]] = {}
    field_attrs: dict[str, dict[str, str]] = {}
    for sub in list(child):
        if sub.attrib:
            field_attrs[sub.tag] = dict(sub.attrib)
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
    return fields, nested, field_attrs


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
            fields, nested, field_attrs = _bonus_fields(child)
            payload["fields"] = fields
            if tag == "selectpowers":
                specs: list[dict[str, Any]] = []
                for sp in child.findall("selectpower"):
                    sp_fields: dict[str, Any] = {}
                    for sub in list(sp):
                        sp_fields[sub.tag] = _text(sub)
                    specs.append({"attrs": dict(sp.attrib), "fields": sp_fields})
                if specs:
                    payload["selectpower_specs"] = specs
            if nested:
                payload["nested"] = nested
            if field_attrs:
                payload["field_attrs"] = field_attrs
        nodes.append(payload)
    return nodes


def parse_select_power_slot(node: dict[str, Any]) -> dict[str, Any]:
    specs = list(node.get("selectpower_specs") or [])
    sp = specs[0] if specs else {}
    attrs = dict(sp.get("attrs") or {})
    if not attrs:
        attrs = dict((node.get("field_attrs") or {}).get("selectpower") or {})
    fields = dict(sp.get("fields") or {})
    limit_raw = str(attrs.get("limittopowers") or "").strip()
    options = [part.strip() for part in limit_raw.split(",") if part.strip()]
    val_raw = str(fields.get("val") or "").strip()
    limit_field = str(fields.get("limit") or "").strip()
    ignore_rating = str(fields.get("ignorerating") or "").lower() == "true"
    points_per_level = 0.25
    points_raw = fields.get("pointsperlevel")
    if points_raw not in (None, ""):
        try:
            points_per_level = float(points_raw)
        except (TypeError, ValueError):
            pass
    nested_vals = (node.get("nested") or {}).get("selectpower") or []
    rating = 1
    rating_expr = ""
    if val_raw.lower() == "rating":
        rating_expr = "Rating"
    elif val_raw:
        try:
            rating = max(1, int(float(val_raw)))
        except (TypeError, ValueError):
            pass
    else:
        for item in nested_vals:
            try:
                rating = max(1, int(float(item)))
                break
            except (TypeError, ValueError):
                continue
    limit_expr = "Rating" if limit_field.lower() == "rating" else ""
    open_select = not options
    return {
        "options": options,
        "rating": rating,
        "rating_expr": rating_expr,
        "limit_expr": limit_expr,
        "points_per_level": points_per_level,
        "ignore_rating": ignore_rating,
        "open_select": open_select,
        "needs_select": bool(options) or open_select,
    }


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
