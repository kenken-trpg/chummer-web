"""Active skills, skill groups, specialisations, knowledge skills and the
priority talent's free levels."""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET  # the Element type only — parsing goes through parse_untrusted
from typing import Any

from ..data_loader import CatalogDict
from ..data_loader._xml import _int, _text
from ..notices import Notice, notice, ui


def _skill_nodes(root: ET.Element, section: str) -> list[ET.Element]:
    """One skills section in both layouts: `<newskills>` is what Chummer writes
    (`skills` / `knoskills` / `groups`); `<skills>` is this app's older export."""
    return root.findall(f"./newskills/{section}") + root.findall(f"./skills/{section}")


def _talent_free_ratings(root: ET.Element) -> tuple[dict[str, int], dict[str, int]]:
    """The priority talent's free skills and groups, name -> free rating.

    Chummer keeps them as `Heritage` improvements (`SkillBase` /
    `SkillGroupBase`) rather than on the skill, whose `<base>` holds only
    what points bought.
    """
    skills: dict[str, int] = {}
    groups: dict[str, int] = {}
    for imp in root.findall("./improvements/improvement"):
        if _text(imp.find("improvementsource")) != "Heritage":
            continue
        kind = _text(imp.find("improvementttype"))
        target = skills if kind == "SkillBase" else groups if kind == "SkillGroupBase" else None
        name = _text(imp.find("improvedname"))
        if target is not None and name:
            target[name] = target.get(name, 0) + _int(imp.find("val"))
    return skills, groups


def _import_skills(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read active skills, groups, specialisations and knowledge.

    Chummer names an active skill only by its skills.xml id (`<suid>`); a
    knowledge skill and a group carry their `<name>`.
    """
    rows = cat["skills"].get("skills") or []
    names_by_id = {str(row["id"]): str(row["name"]) for row in rows}
    exotic_names = {row["name"] for row in rows if row.get("exotic")}
    skills: dict[str, int] = {}
    specs: dict[str, str] = {}
    exotic: list[dict[str, Any]] = []
    # Before creation is finished, <karma> is the top levels bought with karma
    # rather than skill points (as for attributes); after it, every career
    # raise is in there too, which the career baseline already accounts for.
    split = not st.get("career")
    skill_karma: dict[str, int] = {}
    knowledge_karma: dict[str, int] = {}
    free_skills, free_groups = _talent_free_ratings(root)
    st["talent_skills"] = list(free_skills or free_groups)
    for s in _skill_nodes(root, "skills/skill"):
        name = _text(s.find("name")) or names_by_id.get(_text(s.find("suid")), "")
        # `<base>` is the points only: the talent's free levels sit under it
        rating = _int(s.find("base")) + _int(s.find("karma")) + free_skills.get(name, 0)
        if not name:
            if rating > 0:
                warn.append(
                    notice("engine.import.skippedUnknown", kind=ui("engine.kind.skill"), name=_text(s.find("suid")))
                )
            continue
        # An exotic skill is one row per weapon, told apart by `<specific>` —
        # two of them share a name, so they cannot go in the `skills` map.
        if name in exotic_names:
            exotic.append(
                {
                    "id": str(uuid.uuid4()),
                    "skill_name": name,
                    "extra": _text(s.find("specific")),
                    "rating": max(1, rating),
                }
            )
            continue
        if rating > 0:
            skills[name] = rating
            if split and _int(s.find("karma")) > 0:
                skill_karma[name] = _int(s.find("karma"))
        sp = (
            _text(s.find("./specs/spec/name"))
            or _text(s.find("./specializations/spec/name"))
            or _text(s.find("./specializations/skillspecialization/name"))
        )
        if sp:
            specs[name] = sp
    st["skills"] = skills
    st["skill_karma"] = skill_karma
    st["skill_specializations"] = specs
    st["exotic_skills"] = exotic
    st["skill_specs_karma"] = _specs_bought_with_karma(root, names_by_id)

    groups: dict[str, int] = {}
    group_karma: dict[str, int] = {}
    for g in _skill_nodes(root, "groups/group"):
        name = _text(g.find("name"))
        r = _int(g.find("base")) + _int(g.find("karma")) + free_groups.get(name, 0)
        if r > 0 and name:
            groups[name] = r
            if split and _int(g.find("karma")) > 0:
                group_karma[name] = _int(g.find("karma"))
    st["skill_groups"] = groups
    st["skill_group_karma"] = group_karma

    know: dict[str, int] = {}
    know_cat: dict[str, str] = {}
    natives: list[str] = []
    for s in _skill_nodes(root, "knoskills/skill"):
        name = _text(s.find("name"))
        if not name:
            continue
        know_spec = _text(s.find("./specs/spec/name"))
        if know_spec:
            specs[name] = know_spec
        r = _int(s.find("base")) + _int(s.find("karma"))
        typ = _text(s.find("skillcategory")) or _text(s.find("type"))
        native = _text(s.find("isnativelanguage")).lower()
        # Saves from before Chummer 5.212.72 carry no flag: Chummer reads a
        # language nobody put a point into as the native one (KnowledgeSkill.Load).
        if native == "true" or (not native and typ == "Language" and r == 0):
            natives.append(name)
            continue
        if r > 0:
            know[name] = r
            if split and _int(s.find("karma")) > 0:
                knowledge_karma[name] = _int(s.find("karma"))
        if typ:
            know_cat[name] = typ
    st["knowledge_skills"] = know
    st["knowledge_karma"] = knowledge_karma
    st["knowledge_categories"] = know_cat
    st["native_languages"] = natives


def _specs_bought_with_karma(root: ET.Element, names_by_id: dict[str, str]) -> list[str]:
    """Skills whose specialization the player ticked to pay with karma
    (`<buywithkarma>`). Chummer also writes True for the ones it forces to
    karma, which the engine works out again on its own."""
    picked: list[str] = []
    for s in _skill_nodes(root, "skills/skill") + _skill_nodes(root, "knoskills/skill"):
        if _text(s.find("buywithkarma")).lower() != "true":
            continue
        name = _text(s.find("name")) or names_by_id.get(_text(s.find("suid")), "")
        if name and name not in picked:
            picked.append(name)
    return picked
