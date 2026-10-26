"""The quality "needs a player pick" inspectors: whether a bonus block asks
the player to choose something, what kind of choice, and its options."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ._xml import ELEMENTS, MATRIX_ATTRIBUTES

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


def _weaponcategorydv_categories(node: dict[str, Any]) -> list[str]:
    """The categories a `<weaponcategorydv>` asks to pick from with its own
    `<selectcategory>` (Critical Strike) — melee skill names."""
    if node.get("tag") != "weaponcategorydv":
        return []
    return [str(name) for name in (node.get("nested") or {}).get("selectcategory") or [] if str(name).strip()]


def _weaponskillaccuracy_select_attrs(node: dict[str, Any]) -> dict[str, str]:
    if not _weaponskillaccuracy_needs_select(node):
        return {}
    return {str(k): str(v) for k, v in ((node.get("field_attrs") or {}).get("selectskill") or {}).items()}


def _filter_active_skill_names(skills: list[dict[str, Any]], attrs: dict[str, str]) -> list[str]:
    names = {part.strip() for part in str(attrs.get("limittoskill") or "").split(",") if part.strip()}
    excluded = {part.strip() for part in str(attrs.get("excludeskill") or "").split(",") if part.strip()}
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
        if names and name not in names or name in excluded:
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
    if "strings.xml" in xml and "elements" in xpath.lower():
        return list(ELEMENTS)
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
            "selectinherentaiprogram",
        }
        or _limit_spell_category_needs_select(node)
        or _limit_spirit_category_needs_select(node)
        or bool(_weapon_category_dv_select_skills(node))
        or _weaponskillaccuracy_needs_select(node)
        or (node.get("tag") == "addspirit" and not str((node.get("attrs") or {}).get("skill") or "").strip())
        for node in (bonus or [])
    )


def quality_extra_meta(bonus: list[dict[str, Any]] | None) -> dict[str, Any]:
    nodes = bonus or []
    kind = _extra_kind(nodes)
    select_options: list[str] = []
    expertise_skill = ""
    if kind == "expertise":
        expertise_skill, select_options = _expertise_pick(nodes)
    elif kind == "weapon_skill":
        # Empty for `weaponskillaccuracy`: filled later in catalog() once
        # skills.xml is loaded.
        select_options = _weapon_dv_skills(nodes)
    elif kind == "quality":
        select_options = _selectquality_options(nodes)
    elif kind == "matrix_action":
        select_options = list(MATRIX_ACTION_OPTIONS)
    spell_exclude: list[str] = []
    if any(_limit_spell_category_needs_select(node) for node in nodes):
        select_options, spell_exclude = _spell_categories(nodes)
    needs_spirit_category = any(_limit_spirit_category_needs_select(node) for node in nodes)
    return {
        "extra_kind": kind,
        "select_options": select_options,
        "spirit_options": list(STANDARD_SPIRIT_NAMES) if needs_spirit_category else [],
        "spell_exclude": spell_exclude,
        "expertise_skill": expertise_skill,
        "add_spirit_count": _fixed_add_spirits(nodes),
    }


def _extra_kind(nodes: list[dict[str, Any]]) -> str | None:
    """What the player picks for the quality; the first rule that matches wins."""
    tags = {node.get("tag") for node in nodes}
    needs_spell_category = any(_limit_spell_category_needs_select(node) for node in nodes)
    needs_spirit_category = any(_limit_spirit_category_needs_select(node) for node in nodes)
    if "selectexpertise" in tags:
        return "expertise"
    if _weapon_dv_skills(nodes) or any(_weaponskillaccuracy_needs_select(node) for node in nodes):
        return "weapon_skill"
    if _fixed_add_spirits(nodes):
        return "add_spirit"
    for tag, kind in (
        ("selectquality", "quality"),
        ("skillgroupdisablechoice", "skillgroup"),
        ("selectside", "side"),
        ("actiondicepool", "matrix_action"),
    ):
        if tag in tags:
            return kind
    if needs_spell_category and needs_spirit_category:
        return "spell_spirit_category"
    if needs_spell_category:
        return "spell_category"
    if needs_spirit_category:
        return "spirit_category"
    if "selectattributes" in tags or "selectattribute" in tags:
        return "attribute"
    # `selectsprite` (Sprite Affinity) and `selectinherentaiprogram`
    # (Inherent Program): options filled in catalog() once the sprites
    # and the A.I. programs are loaded
    if tags & {"selecttext", "selectsprite", "selectinherentaiprogram"}:
        return "text"
    return None


def _weapon_dv_skills(nodes: list[dict[str, Any]]) -> list[str]:
    """The skills of the first `weaponcategorydv` that asks for one."""
    return next((skills for node in nodes if (skills := _weapon_category_dv_select_skills(node))), [])


def _fixed_add_spirits(nodes: list[dict[str, Any]]) -> int:
    """`addspirit` grants with no skill of their own: the player names the spirit."""
    return sum(
        1
        for node in nodes
        if node.get("tag") == "addspirit" and not str((node.get("attrs") or {}).get("skill") or "").strip()
    )


def _expertise_pick(nodes: list[dict[str, Any]]) -> tuple[str, list[str]]:
    """The first `selectexpertise`'s skill and its allowed specializations."""
    node = next(node for node in nodes if node.get("tag") == "selectexpertise")
    attrs = node.get("attrs") or {}
    limit = str(attrs.get("limittoskill") or node.get("value") or "").strip()
    skill = next((part.strip() for part in limit.split(",") if part.strip()), "")
    limit_spec = str(attrs.get("limittospecialization") or "").strip()
    return skill, [part.strip() for part in limit_spec.split(",") if part.strip()]


def _selectquality_options(nodes: list[dict[str, Any]]) -> list[str]:
    options: list[str] = []
    for node in nodes:
        if node.get("tag") != "selectquality":
            continue
        raw = (node.get("fields") or {}).get("quality") or node.get("value") or []
        for item in raw if isinstance(raw, list) else [raw]:
            text = str(item).strip()
            if text and text not in options:
                options.append(text)
    return options


def _spell_categories(nodes: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    """The spell categories on offer, and the ones `limitspellcategory` excludes."""
    options = list(SPELL_SELECT_CATEGORIES)
    excluded: list[str] = []
    for node in nodes:
        if not _limit_spell_category_needs_select(node):
            continue
        exclude = str((node.get("attrs") or {}).get("exclude") or "").strip()
        if exclude:
            excluded.append(exclude)
            options = [name for name in options if name != exclude]
    return options, excluded
