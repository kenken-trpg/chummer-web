"""Active, knowledge and language skills, and skill groups."""

from __future__ import annotations

from typing import Any

from ..data_loader import CatalogDict
from ..notices import Notice, notice, ui
from ._common import _d, _l, _num

#: Foundry `knowledgeType` -> Chummer's knowledge skill category
_KNOWLEDGE_TYPES = {"academic": "Academic", "interest": "Interest", "professional": "Professional", "street": "Street"}


def _import_skills(items: list[dict[str, Any]], cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    active = {str(r["name"]).lower(): str(r["name"]) for r in cat["skills"].get("skills") or []}
    groups = {str(g).lower(): str(g) for g in cat["skills"].get("group_names") or []}
    skills: dict[str, int] = {}
    know: dict[str, int] = {}
    know_cat: dict[str, str] = {}
    natives: list[str] = []
    specs: dict[str, str] = {}
    skill_groups: dict[str, int] = {}
    for item in items:
        if item.get("type") != "skill":
            continue
        system = _d(item.get("system"))
        name = str(item.get("name") or "").strip()
        if system.get("type") == "group":
            rating = _num(_d(system.get("group")).get("rating"))
            if rating > 0:
                if name.lower() in groups:
                    skill_groups[groups[name.lower()]] = rating
                else:
                    warn.append(notice("engine.import.skippedUnknown", kind=ui("engine.kind.skill"), name=name))
            continue
        skill = _d(system.get("skill"))
        rating = _num(skill.get("rating"))
        category = str(skill.get("category") or "active")
        spec = next((str(s.get("name") or "") for s in _l(skill.get("specializations")) if s.get("name")), "")
        if category == "active":
            if rating <= 0:
                continue
            if name.lower() not in active:
                warn.append(notice("engine.import.skippedUnknown", kind=ui("engine.kind.skill"), name=name))
                continue
            name = active[name.lower()]
            skills[name] = rating
        elif category == "language" and _d(skill.get("language")).get("isNative"):
            natives.append(name)
            continue
        else:
            if rating <= 0:
                continue
            know[name] = rating
            know_cat[name] = (
                "Language"
                if category == "language"
                else _KNOWLEDGE_TYPES.get(str(skill.get("knowledgeType") or ""), "Academic")
            )
        if spec:
            specs[name] = spec
    st.update(
        skills=skills,
        skill_groups=skill_groups,
        skill_specializations=specs,
        knowledge_skills=know,
        knowledge_categories=know_cat,
        native_languages=natives,
    )
