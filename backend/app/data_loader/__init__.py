from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from functools import lru_cache
from typing import Any

from ._xml import (
    DATA_DIR,
    LANG_DIR,  # noqa: F401  (re-exported for tests)
    MATRIX_ATTRIBUTES,  # noqa: F401  (re-exported for engine)
    OVERRIDE_DIR,  # noqa: F401  (re-exported for tests)
    PHYSICAL_ATTRS,  # noqa: F401  (re-exported for engine)
    _child,
    _int,
    _text,
    log,
)
from .bonus import (
    _filter_active_skill_names,
    _weaponskillaccuracy_needs_select,
    _weaponskillaccuracy_select_attrs,
    parse_bonus,
    parse_required,
    parse_requirement_tree,
    parse_select_power_slot,  # noqa: F401  (re-exported for improvements)
    quality_needs_extra,
    selecttext_catalog_options,  # noqa: F401  (re-exported for engine)
)
from .formulas import (
    CHARGEN_AVAIL_MAX,  # noqa: F401  (re-exported for engine)
    CHARGEN_DEVICE_RATING_MAX,  # noqa: F401  (re-exported for engine)
    CHARGEN_WARE_ATTR_BONUS_MAX,  # noqa: F401  (re-exported for engine)
    eval_formula,  # noqa: F401  (re-exported for engine / gear / magic)
    format_avail,  # noqa: F401  (re-exported for engine)
    parse_avail,  # noqa: F401  (re-exported for engine / tests)
    parse_capacity,  # noqa: F401  (re-exported for engine / gear)
    sum_avail,  # noqa: F401  (re-exported for engine)
)
from .loaders import (  # noqa: E402  (domain loaders; see data_loader/loaders/)
    PROGRAM_HOSTS,  # noqa: F401  (re-exported for engine)
    SPELL_CAST_CATEGORIES,  # noqa: F401  (re-exported for engine)
    SPELL_CATEGORIES,  # noqa: F401  (re-exported for engine)
    load_apps,
    load_armor,
    load_armor_mods,
    load_bioware,
    load_commlinks,
    load_complex_forms,
    load_cyberdecks,
    load_cyberware,
    load_drones,
    load_enhancements,
    load_foci,
    load_gear,
    load_mentors,
    load_metatypes,
    load_optics,
    load_powers,
    load_programs,
    load_qualities,
    load_rccs,
    load_sensors,
    load_skills,
    load_spells,
    load_spirits,
    load_sprites,
    load_streams,
    load_traditions,
    load_vehicle_mods,
    load_vehicle_names,
    load_vehicles,
    load_weapon_accessories,
    load_weapon_mounts,
    load_weapon_ranges,
    load_weapons,
)


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


_DRUG_LIMIT_LABEL = {"physical": "肉体上限", "mental": "精神上限", "social": "社会上限"}


def drug_node_value(node: dict[str, Any]) -> str:
    fields = node.get("fields") or {}
    return str(fields.get("value") or fields.get("val") or fields.get("bonus") or node.get("value") or "").strip()


def drug_effect_summary(nodes: list[dict[str, Any]]) -> str:
    """Human-readable one-liner for a drug's ``<bonus>`` nodes."""
    parts: list[str] = []
    for node in nodes or []:
        tag = node.get("tag")
        fields = node.get("fields") or {}
        val = drug_node_value(node)
        signed = val if val.startswith(("-", "+")) else (f"+{val}" if val else "")
        if tag == "attribute" and val:
            parts.append(f"{str(fields.get('name') or '').upper()} {signed}")
        elif tag == "limit" and val:
            label = _DRUG_LIMIT_LABEL.get(str(fields.get("name") or "").strip().lower(), str(fields.get("name") or ""))
            parts.append(f"{label} {signed}")
        elif tag in ("initiativedice", "initiativepass") and val:
            parts.append(f"イニシアチブ +{val}D6")
        elif tag == "initiative" and val:
            parts.append(f"イニシアチブ {signed}")
        elif tag == "specificskill" and val:
            parts.append(f"{str(fields.get('name') or '')} {signed}")
        elif tag == "quality":
            rating = (node.get("attrs") or {}).get("rating")
            name = str(node.get("value") or "")
            parts.append(f"資質 {name}" + (f"({rating})" if rating else ""))
    return " / ".join(p for p in parts if p.strip())


def load_drug_components() -> dict[str, dict[str, Any]]:
    """Mechanical data for premade drugs, keyed by the shared drug/gear id.

    ``drugcomponents.xml`` carries the ``<bonus>`` (attribute / limit /
    initiativedice / quality / specificskill), the ``<duration>`` formula
    (seconds, may use ``{BOD}`` / ``{D6}``), ``<speed>`` and ``<vectors>`` that
    the flat ``gear.xml`` ``Drugs`` entries omit.
    """
    path = DATA_DIR / "drugcomponents.xml"
    if not path.exists():
        return {}
    out: dict[str, dict[str, Any]] = {}
    for el in ET.parse(path).getroot().findall("./drugs/drug"):
        drug_id = _text(el.find("id"))
        bonus = parse_bonus(el.find("bonus"))
        duration = _text(el.find("duration"))
        speed = _text(el.find("speed"))
        vectors = _text(el.find("vectors"))
        if not drug_id or not (bonus or duration or speed or vectors):
            continue
        out[drug_id] = {
            "drug_bonus": bonus,
            "drug_duration": duration,
            "drug_speed": speed,
            "drug_vectors": [v.strip() for v in vectors.split(",") if v.strip()],
        }
    return out


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
            tech_name for tech in el.findall("./techniques/technique") if (tech_name := _text(tech.find("name")))
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


def _load_ja_overrides(filename: str) -> dict[str, str]:
    """Read a Git-tracked JSON overlay of {key: japanese}. Missing or malformed
    files are ignored so a bad edit never breaks catalog loading."""
    path = OVERRIDE_DIR / filename
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        log.warning("ja override %s load failed: %s", filename, exc)
        return {}
    if not isinstance(raw, dict):
        log.warning("ja override %s is not a JSON object", filename)
        return {}
    result: dict[str, str] = {}
    for key, value in raw.items():
        if isinstance(key, str) and isinstance(value, str) and value.strip():
            result[key] = value
    return result


def load_translations() -> dict[str, str]:
    mapping: dict[str, str] = {}
    path = LANG_DIR / "ja-jp_data.xml"
    if path.exists():
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            log.warning("ja-jp_data.xml parse failed: %s", exc)
        else:
            for node in root.iter():
                name = _text(node.find("name"))
                trans = _text(node.find("translate"))
                if name and trans:
                    mapping[name] = trans
    overrides = _load_ja_overrides("data.json")
    if overrides:
        log.info("applied %d ja_overrides/data.json entries", len(overrides))
        mapping.update(overrides)
    return mapping


def load_ui_strings() -> dict[str, str]:
    path = LANG_DIR / "ja-jp.xml"
    strings: dict[str, str] = {}
    if path.exists():
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            log.warning("ja-jp.xml parse failed: %s", exc)
        else:
            for node in root.findall(".//string"):
                key = node.get("key") or _text(node.find("key"))
                text = _text(node.find("text")) or _text(node.find("translate")) or _text(node)
                if key and text:
                    strings[key] = text
    overrides = _load_ja_overrides("ui.json")
    if overrides:
        log.info("applied %d ja_overrides/ui.json entries", len(overrides))
        strings.update(overrides)
    return strings


@lru_cache(maxsize=1)
def catalog() -> dict[str, Any]:
    if not (DATA_DIR / "metatypes.xml").exists():
        raise FileNotFoundError(f"Chummer data not found in {DATA_DIR}. Run backend/scripts/fetch_chummer_data.py")
    metatypes = load_metatypes()
    playable = [
        m
        for m in metatypes
        if m["category"] in {"Metahuman", "Metavariant"} and m["name"] in {"Human", "Elf", "Dwarf", "Ork", "Troll"}
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
    drug_effects = load_drug_components()
    for item in gear:
        eff = drug_effects.get(item["id"])
        if eff:
            item.update(eff)
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
    active_skills = list(skills.get("skills") or [])
    for quality in qualities:
        if quality.get("extra_kind") != "weapon_skill" or quality.get("select_options"):
            continue
        for node in quality.get("bonus") or []:
            if not _weaponskillaccuracy_needs_select(node):
                continue
            quality["select_options"] = _filter_active_skill_names(
                active_skills, _weaponskillaccuracy_select_attrs(node)
            )
            break
    spirits = load_spirits()
    programs = load_programs()
    selecttext_data = {
        "vehicle_names": load_vehicle_names(),
        "drones": load_drones(),
        "weapons": weapons,
        "skills": skills,
        "spirits": spirits,
        "programs": programs,
    }
    for quality in qualities:
        if quality.get("extra_kind") != "text" or quality.get("select_options"):
            continue
        options: list[str] = []
        for node in quality.get("bonus") or []:
            if node.get("tag") != "selecttext":
                continue
            for name in selecttext_catalog_options(node.get("attrs") or {}, selecttext_data):
                if name and name not in options:
                    options.append(name)
        if options:
            quality["select_options"] = options
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
        "spirits": spirits,
        "complex_forms": load_complex_forms(),
        "streams": load_streams(),
        "sprites": load_sprites(),
        "foci": load_foci(),
        "qi_focus": load_qi_focus(),
        "armor": load_armor(),
        "armor_mods": load_armor_mods(),
        "weapons": weapons,
        "weapon_ranges": load_weapon_ranges(),
        "weapon_accessories": load_weapon_accessories(),
        "commlinks": load_commlinks(),
        "cyberdecks": load_cyberdecks(),
        "rccs": load_rccs(),
        "optics": load_optics(),
        "programs": programs,
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
