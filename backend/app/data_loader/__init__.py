"""``catalog()`` — assemble every vendored-XML loader into the one cached
mega-dict the app reads, doing the cross-entity wiring (weapon<->gear ids,
drug effects onto gear, quality select-options). Everything else is a
submodule: ``_xml`` / ``formulas`` / ``bonus`` primitives and the
``loaders/`` package. This module stays the public barrel.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, cast

from ._xml import (
    DATA_DIR,
    LANG_DIR,  # noqa: F401  (re-exported for tests)
    MATRIX_ATTRIBUTES,  # noqa: F401  (re-exported for engine)
    OVERRIDE_DIR,  # noqa: F401  (re-exported for tests)
    PHYSICAL_ATTRS,  # noqa: F401  (re-exported for engine)
)
from .bonus import (
    _filter_active_skill_names,
    _weaponskillaccuracy_needs_select,
    _weaponskillaccuracy_select_attrs,
    parse_select_power_slot,  # noqa: F401  (re-exported for improvements)
    quality_needs_extra,  # noqa: F401  (re-exported for callers of data_loader)
    selecttext_catalog_options,  # noqa: F401  (re-exported for engine)
)
from .catalog_types import CatalogDict
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
    _load_ja_overrides,  # noqa: F401  (re-exported for tests)
    drug_effect_summary,  # noqa: F401  (re-exported for engine)
    drug_node_value,  # noqa: F401  (re-exported for engine)
    load_apps,
    load_armor,
    load_armor_mods,
    load_bioware,
    load_commlinks,
    load_complex_forms,
    load_cyberdecks,
    load_cyberware,
    load_drones,
    load_drug_components,
    load_drug_grades,
    load_echoes,
    load_enhancements,
    load_foci,
    load_gear,
    load_lifestyle_qualities,
    load_lifestyles,
    load_magic_arts,
    load_martial_art_techniques,
    load_martial_arts,
    load_mentors,
    load_metamagics,
    load_metatypes,
    load_optics,
    load_powers,
    load_priorities,
    load_programs,
    load_qi_focus,
    load_qualities,
    load_rccs,
    load_sensors,
    load_skills,
    load_spells,
    load_spirits,
    load_sprites,
    load_streams,
    load_traditions,
    load_translations,
    load_ui_strings,  # noqa: F401  (re-exported for tests)
    load_ui_strings_by_locale,
    load_vehicle_mods,
    load_vehicle_names,
    load_vehicles,
    load_weapon_accessories,
    load_weapon_mounts,
    load_weapon_ranges,
    load_weapons,
)


@lru_cache(maxsize=1)
def catalog() -> CatalogDict:
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
        "ui_strings": load_ui_strings_by_locale(),
    }


def catalog_list(kind: str) -> list[dict[str, Any]]:
    """``catalog()[kind]`` where ``kind`` is computed — the ``CatalogDict``
    escape hatch for the ``list`` buckets (the loaders really do return
    ``list[dict[str, Any]]``; a computed key just can't prove it)."""
    return cast("list[dict[str, Any]]", catalog().get(kind) or [])


def catalog_ware(kind: str) -> dict[str, Any]:
    """Same, for the ``cyberware`` / ``bioware`` buckets (``{grades, items}``)."""
    return cast("dict[str, Any]", catalog().get(kind) or {})


def reset_catalog() -> None:
    catalog.cache_clear()
