"""The quality "needs a player pick" inspectors: whether a bonus block asks
the player to choose something, what kind of choice, and its options."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ._xml import MATRIX_ATTRIBUTES

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
        weapons = [w for w in (catalog_data.get("weapons") or []) if w.get("purchasable")]
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
            "selectsprite",
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
    elif "selecttext" in tags or "selectsprite" in tags:
        # `selectsprite` (Sprite Affinity): options filled in catalog() once
        # the sprites are loaded
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
