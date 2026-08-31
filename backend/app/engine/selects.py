"""Enumerate the choices behind a ``<select*>`` / ``*soft`` bonus node.

Given a parsed bonus node (and the skills catalog), these return the list of
legal picks for a skill / skill-group / text / skillsoft selection. Shared by
gear resolvers (a program's [Skill] slot), quality resolution, and skill picks,
so they live in their own leaf module with no engine-internal imports.
"""

from __future__ import annotations

from typing import Any

from ..data_loader import catalog, selecttext_catalog_options
from ..improvements import _as_int


def parse_selectskill_spec(node: dict[str, Any]) -> dict[str, Any]:
    fields = node.get("fields") or {}
    attrs = node.get("attrs") or {}
    knowledge = str(attrs.get("knowledgeskills") or "False").lower() == "true"
    return {
        "bonus": _as_int(fields.get("val") or fields.get("bonus") or fields.get("value") or node.get("value")),
        "max": _as_int(fields.get("max")),
        "applytorating": str(fields.get("applytorating") or "").lower() == "true",
        "limittoattribute": attrs.get("limittoattribute") or "",
        "limittoskill": attrs.get("limittoskill") or "",
        "limittoskillgroup": attrs.get("limittoskillgroup") or "",
        "limittocategory": attrs.get("limittocategory")
        or attrs.get("skillcategory")
        or ", ".join((node.get("nested") or {}).get("skillcategories") or []),
        "excludecategory": attrs.get("excludecategory") or "",
        "knowledgeskills": knowledge,
        "minimumrating": _as_int(attrs.get("minimumrating")),
        "condition": (fields.get("condition") or "").strip(),
    }


def selectskill_options(
    spec: dict[str, Any],
    skills_data: dict[str, Any],
    skill_totals: dict[str, int],
) -> list[str]:
    if spec.get("knowledgeskills"):
        pool = list(skills_data.get("knowledge") or [])
    else:
        pool = [skill for skill in (skills_data.get("skills") or []) if not skill.get("exotic")]
    attrs = {part.strip().upper() for part in (spec.get("limittoattribute") or "").split(",") if part.strip()}
    names = {part.strip() for part in (spec.get("limittoskill") or "").split(",") if part.strip()}
    groups = {part.strip() for part in (spec.get("limittoskillgroup") or "").split(",") if part.strip()}
    cats = {part.strip() for part in (spec.get("limittocategory") or "").split(",") if part.strip()}
    exclude_cats = {part.strip() for part in (spec.get("excludecategory") or "").split(",") if part.strip()}
    minimum = int(spec.get("minimumrating") or 0)
    out: list[str] = []
    for skill in pool:
        if attrs and (skill.get("attribute") or "").upper() not in attrs:
            continue
        if names and skill["name"] not in names:
            continue
        if groups and (skill.get("skillgroup") or "") not in groups:
            continue
        if cats and (skill.get("category") or "") not in cats:
            continue
        if exclude_cats and (skill.get("category") or "") in exclude_cats:
            continue
        if minimum and int(skill_totals.get(skill["name"], 0)) < minimum:
            continue
        out.append(skill["name"])
    return sorted(set(out))


def _csv_names(value: Any) -> set[str]:
    if isinstance(value, list):
        parts = [str(item).strip() for item in value]
    else:
        parts = [part.strip() for part in str(value or "").split(",")]
    return {part for part in parts if part}


def _skillsoft_kind(node: dict[str, Any]) -> str:
    tag = str(node.get("tag") or "")
    fields = node.get("fields") or {}
    attrs = node.get("attrs") or {}
    cats = _csv_names(fields.get("skillcategory") or attrs.get("skillcategory"))
    exclude = _csv_names(fields.get("excludecategory") or attrs.get("excludecategory"))
    if tag == "activesoft":
        return "active"
    if tag == "linguasoft" or "Language" in cats:
        return "language"
    if tag in {"skillsoft", "knowsoft"}:
        if "Language" in exclude:
            return "knowledge"
        if "Language" in cats:
            return "language"
        return "knowledge"
    return ""


def skillsoft_options(node: dict[str, Any], skills_data: dict[str, Any]) -> list[str]:
    kind = _skillsoft_kind(node)
    if kind == "active":
        return [skill["name"] for skill in skills_data.get("skills") or []]
    knowledge = list(skills_data.get("knowledge") or [])
    fields = node.get("fields") or {}
    attrs = node.get("attrs") or {}
    cats = _csv_names(fields.get("skillcategory") or attrs.get("skillcategory"))
    exclude = _csv_names(fields.get("excludecategory") or attrs.get("excludecategory"))
    if kind == "language":
        cats = cats or {"Language"}
    out: list[str] = []
    for skill in knowledge:
        category = str(skill.get("category") or "")
        if cats and category not in cats:
            continue
        if category in exclude:
            continue
        out.append(skill["name"])
    return out


def selecttext_options(attrs: dict[str, Any]) -> list[str]:
    return selecttext_catalog_options(attrs, catalog())


def gear_extra_options(spec: dict[str, Any], skills_data: dict[str, Any] | None = None) -> list[str]:
    data = skills_data if skills_data is not None else catalog().get("skills") or {}
    extra_kind = str(spec.get("extra_kind") or "")
    if extra_kind == "group" or str(spec.get("name") or "").startswith("Group Autosoft"):
        return list(data.get("groups") or [])
    for node in spec.get("bonus") or []:
        tag = node.get("tag")
        if tag == "selectskill":
            return selectskill_options(parse_selectskill_spec(node), data, {})
        if tag == "selecttext":
            return selecttext_options(node.get("attrs") or {})
        if tag in {"activesoft", "skillsoft", "knowsoft", "linguasoft"}:
            return skillsoft_options(node, data)
        if tag == "selecttradition":
            return [t["name"] for t in catalog().get("traditions") or []]
    return []
