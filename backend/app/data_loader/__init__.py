"""``catalog()`` — assemble every vendored-XML loader into the one cached
mega-dict the app reads, doing the cross-entity wiring (weapon<->gear ids,
drug effects onto gear, quality select-options). Everything else is a
submodule: ``_xml`` / ``formulas`` / ``bonus`` primitives and the
``loaders/`` package. This module stays the public barrel.
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from collections.abc import Iterator
from functools import lru_cache
from typing import Any, cast

from ._xml import (
    DATA_DIR,
    LANG_DIR,  # noqa: F401  (re-exported for tests)
    MATRIX_ATTRIBUTES,  # noqa: F401  (re-exported for engine)
    OVERRIDE_DIR,  # noqa: F401  (re-exported for tests)
    PHYSICAL_ATTRS,  # noqa: F401  (re-exported for engine)
    SPECIAL_ATTRS,  # noqa: F401  (re-exported for engine)
    Overlay,  # noqa: F401  (re-exported for the API layer)
    current_overlay_key,
    using_customdata,  # noqa: F401  (re-exported for the API layer)
)
from .bonus import parse_select_power_slot  # noqa: F401  (re-exported for improvements)
from .bonus_extra import (
    _filter_active_skill_names,
    _weaponskillaccuracy_needs_select,
    _weaponskillaccuracy_select_attrs,
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
    DRUG_CATEGORIES,
    INHERENT_CATEGORIES,
    PROGRAM_HOSTS,  # noqa: F401  (re-exported for engine)
    SPELL_CAST_CATEGORIES,  # noqa: F401  (re-exported for engine)
    SPELL_CATEGORIES,  # noqa: F401  (re-exported for engine)
    _load_ja_overrides,  # noqa: F401  (re-exported for tests)
    boost_drug_attribute,  # noqa: F401  (re-exported for engine)
    drug_effect_summary,  # noqa: F401  (re-exported for engine)
    drug_node_value,  # noqa: F401  (re-exported for engine)
    load_ai_programs,
    load_apps,
    load_armor,
    load_armor_mods,
    load_bioware,
    load_books,
    load_commlinks,
    load_complex_forms,
    load_critter_powers,
    load_custom_drug_components,
    load_custom_drug_grades,
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
    load_paragons,
    load_powers,
    load_priorities,
    load_programs,
    load_qi_focus,
    load_qualities,
    load_quality_levels,
    load_rccs,
    load_sensors,
    load_settings_presets,
    load_skill_group_names,
    load_skills,
    load_spec_names,
    load_spells,
    load_spirits,
    load_sprites,
    load_streams,
    load_text_translations,
    load_traditions,
    load_translations,
    load_translations_by_kind,
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
from .loaders.life_modules import load_life_modules
from .loaders.metatype_grants import resolve_metatype_grants

#: One lock per overlay key, so two requests that arrive on a cold key build
#: it once between them instead of once each. `lru_cache` has no "wait for the
#: caller already computing this" — it just runs the function again, and a
#: build reparses ~24 XML files. On Cloud Run's single vCPU the two then fought
#: each other: 4.75 s for the first `/api/catalog` after an idle period against
#: 0.2 s when one build had the core to itself (see `/api/ready` in `main.py`,
#: which closed the one case where the racer was the warm-up thread).
#:
#: Reentrant, because a loader that reached back for `catalog()` on the same
#: key would otherwise deadlock rather than recurse.
#:
#: Bounded, because an overlay key is a hash of an uploaded custom-data set and
#: a long-lived process sees arbitrarily many of them. Evicting a lock someone
#: still holds is harmless: the holder keeps its reference, and the next caller
#: simply gets a fresh one — back to two concurrent builds, which is where this
#: started. Far above the four catalogs that are actually cached.
MAX_BUILD_LOCKS = 32

_build_locks: OrderedDict[str, threading.RLock] = OrderedDict()
_build_locks_guard = threading.Lock()


def _build_lock(key: str) -> threading.RLock:
    with _build_locks_guard:
        lock = _build_locks.get(key)
        if lock is None:
            lock = _build_locks[key] = threading.RLock()
        _build_locks.move_to_end(key)
        while len(_build_locks) > MAX_BUILD_LOCKS:
            _build_locks.popitem(last=False)
        return lock


def catalog() -> CatalogDict:
    """The assembled data, for whichever custom-data overlay is in force.

    Keyed by the overlay rather than cached once: a table playing with custom
    data and one playing vanilla hit the same process, and rebuilding ~24 XML
    files per request would be far too slow. Four is enough for a handful of
    tables without holding many megabytes of parsed data hostage.

    The lock makes concurrent callers on a cold key wait for the first build
    rather than start their own. A hit costs one uncontended acquire; a miss
    costs the wait, which is the point — the alternative is paying for the
    whole build again on a core that is already busy with it. A build that
    *raises* holds nothing: `lru_cache` does not memoise exceptions, so the
    next caller retries, as before.
    """
    key = current_overlay_key()
    with _build_lock(key):
        return _catalog_for(key)


def _with_metavariants(metatypes: list[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    """Every metatype row, each of its metavariants after it.

    `all_metatypes` cannot stand in for this: it is keyed by name and keeps
    the first row of a repeated name, so a metavariant sharing a name with
    something already seen would never be reached.
    """
    for meta in metatypes:
        yield meta
        yield from meta.get("metavariants") or []


@lru_cache(maxsize=4)
def _catalog_for(_overlay_key: str) -> CatalogDict:
    if not (DATA_DIR / "metatypes.xml").exists():
        raise FileNotFoundError(f"Chummer data not found in {DATA_DIR}. Run backend/scripts/fetch_chummer_data.py")
    metatypes = load_metatypes()
    playable = [
        m
        for m in metatypes
        if m["name"] in {"Centaur", "A.I."}
        or m["category"] == "Shapeshifter"
        or (m["category"] in {"Metahuman", "Metavariant"} and m["name"] in {"Human", "Elf", "Dwarf", "Ork", "Troll"})
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
    drugs = [item for item in gear if item.get("category") in DRUG_CATEGORIES]
    skills = load_skills()
    skills["group_names"] = load_skill_group_names()
    skills["spec_names"] = load_spec_names()
    qualities = load_qualities()
    armor = load_armor()
    # A shield is armour you hit people with, and metagenetic claws are a
    # quality that is also a weapon (RF p.104) — both name the weapon they
    # bring in `<addweapon>`, the same way gear and ware do above.
    for item in list(armor) + list(qualities):
        add_name = str(item.get("add_weapon") or "")
        if add_name:
            item["add_weapon_id"] = weapon_ids.get(add_name) or ""
    # Every species, not only the one that made the path necessary. An elf's
    # low-light vision is the same kind of grant as a centaur's, and leaving
    # it unresolved made the qualities tab answer differently depending on
    # which metatype was chosen. Metavariants are walked too: a `.chum5` can
    # name one even though chargen offers only the six base metatypes.
    grantable_qualities = load_qualities(include_hidden=True)
    grantable_powers = load_critter_powers(include_rules=True)
    for meta in _with_metavariants(metatypes):
        meta["quality_grants"] = resolve_metatype_grants(meta, meta.get("qualities") or [], grantable_qualities)
        for quality in meta["quality_grants"]:
            add_name = str(quality.get("add_weapon") or "")
            if add_name:
                quality["add_weapon_id"] = weapon_ids.get(add_name) or ""
        meta["power_grants"] = resolve_metatype_grants(meta, meta.get("powers") or [], grantable_powers)
    # The same for the powers a quality grants — an Infected's, a drake's, a
    # free insect spirit's. The catalog's own `critter_powers` rows are the
    # descriptive ones (no `<bonus>`), so without this a Dracoform's Hardened
    # Armor was listed and never worn. Only the powers that do something are
    # kept, with the rating and pick the quality gives them: Chummer creates
    # each one with those and runs its bonus at that rating
    # (AddImprovementCollection.critterpowers, CritterPower.Create).
    power_bonus = {row["name"]: row.get("bonus") or [] for row in reversed(grantable_powers)}
    power_bonus.update({row["id"]: row.get("bonus") or [] for row in grantable_powers})
    for quality in qualities:
        effects = []
        for optional, refs in ((False, quality.get("critter_powers")), (True, quality.get("optional_powers"))):
            for ref in refs or []:
                bonus = power_bonus.get(str(ref.get("name") or ""))
                if bonus:
                    select = str(ref.get("select") or "")
                    effects.append(
                        {
                            "label": f"{ref['name']} ({select})" if select else str(ref["name"]),
                            "optional": optional,
                            # an optional power is made at rating 0 (SelectOptionalPower)
                            "rating": "" if optional else str(ref.get("rating") or ""),
                            "bonus": bonus,
                        }
                    )
        if effects:
            quality["critter_power_effects"] = effects
    # What a Critter Powers tab can sell: the categories some quality limits
    # the tab to (`<limitcritterpowercategory>` — Infected, Drake). Nothing in
    # this app opens the tab without one, and the full 291 powers would only
    # be shipped to be filtered out again.
    shop_categories = {
        str(node.get("value") or "").strip()
        for quality in qualities
        for node in quality.get("bonus") or []
        if node.get("tag") == "limitcritterpowercategory"
    }
    buyable_critter_powers = [row for row in grantable_powers if row.get("category") in shop_categories]
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
    sprites = load_sprites()
    for quality in qualities:
        if any(node.get("tag") == "selectsprite" for node in quality.get("bonus") or []):
            quality["select_options"] = [str(s["name"]) for s in sprites if s.get("name")]
    ai_programs = load_ai_programs()
    # the grants too: a Protosapient is born with Inherent Program, and its
    # grant is a copy made from its own load of qualities.xml above
    grants = [q for meta in _with_metavariants(metatypes) for q in meta.get("quality_grants") or []]
    for quality in [*qualities, *grants]:
        if any(node.get("tag") == "selectinherentaiprogram" for node in quality.get("bonus") or []):
            # Inherent Program: one common or hacking program, which the A.I.
            # then has for free (Chummer's `selectinherentaiprogram`).
            quality["select_options"] = [
                str(p["name"]) for p in ai_programs if p.get("category") in INHERENT_CATEGORIES
            ]
    return {
        "metatypes": playable,
        "all_metatypes": all_by_name,
        "skills": skills,
        "qualities": qualities,
        "quality_levels": load_quality_levels(),
        "life_modules": load_life_modules(),
        "cyberware": cyberware,
        "bioware": bioware,
        "powers": load_powers(),
        "enhancements": load_enhancements(),
        "mentors": load_mentors(),
        "paragons": load_paragons(),
        "spells": load_spells(),
        "traditions": load_traditions(),
        "spirits": spirits,
        "critter_powers": load_critter_powers(),
        "buyable_critter_powers": buyable_critter_powers,
        "complex_forms": load_complex_forms(),
        "ai_programs": ai_programs,
        "streams": load_streams(),
        "sprites": sprites,
        "foci": load_foci(),
        "qi_focus": load_qi_focus(),
        "armor": armor,
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
        "drug_components": load_custom_drug_components(),
        "drug_component_grades": load_custom_drug_grades(),
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
        "books": load_books(),
        "settings_presets": load_settings_presets(),
        "translations": translations,
        "translations_by_kind": load_translations_by_kind(),
        "text_translations": load_text_translations(),
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
    _catalog_for.cache_clear()
