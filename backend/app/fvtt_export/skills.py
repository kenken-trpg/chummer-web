"""Active skills, skill groups and knowledge skills, as the print XML lists
them."""

from __future__ import annotations

from typing import Any

from ..data_loader import catalog
from ..models import CharacterState
from ._common import _flag


def _skills(state: CharacterState, derived: dict[str, Any], tr: Any) -> dict[str, list[dict[str, Any]]]:
    """Active skills matched by `name_english` (so it must be the data name),
    knowledge and language skills by `name`, groups by `name_english`.

    Only skills with a rating: the importer lays the system's default skill
    set down first, so an unrated skill is already there.
    """
    data = catalog()["skills"]
    active_rows = {str(r["name"]): r for r in data.get("skills") or []}
    specs = derived.get("skill_specializations") or {}
    out: list[dict[str, Any]] = []

    for name, rating in sorted((derived.get("skill_totals") or {}).items()):
        row = active_rows.get(name)
        if row is None or int(rating or 0) <= 0:
            continue
        out.append(
            {
                "suid": str(row.get("id") or ""),
                "name": tr(name, "skill"),
                "name_english": name,
                "skillgroup_english": str(row.get("skillgroup") or ""),
                "skillcategory_english": str(row.get("category") or ""),
                "attribute": str(row.get("attribute") or ""),
                "default": _flag(row.get("default")),
                "rating": str(int(rating)),
                "knowledge": "False",
                "islanguage": "False",
                "isnativelanguage": "False",
                "skillspecializations": _specs(specs.get(name), tr),
            }
        )

    for exotic in derived.get("exotic_skills") or []:
        name = str(exotic.get("skill_name") or exotic.get("name") or "")
        row = active_rows.get(name)
        if row is None or int(exotic.get("rating") or 0) <= 0:
            continue
        # One skill per weapon: the weapon rides along as the specialization,
        # which is where a Foundry exotic skill keeps it.
        out.append(
            {
                "suid": str(row.get("id") or ""),
                "name": tr(name, "skill"),
                "name_english": name,
                "skillgroup_english": "",
                "skillcategory_english": str(row.get("category") or ""),
                "attribute": str(row.get("attribute") or ""),
                "default": _flag(row.get("default")),
                "rating": str(int(exotic.get("rating") or 0)),
                "knowledge": "False",
                "islanguage": "False",
                "isnativelanguage": "False",
                "skillspecializations": _specs(exotic.get("extra"), tr),
            }
        )

    for row in derived.get("knowledge_skills") or []:
        name = str(row.get("name") or "")
        category = str(row.get("category") or "")
        language = category == "Language"
        native = bool(row.get("native"))
        if not name or (not native and int(row.get("rating") or 0) <= 0):
            continue
        out.append(
            {
                "name": tr(name, "knowledge_skill"),
                "name_english": name,
                "skillcategory_english": category,
                "attribute": str(row.get("attribute") or ""),
                "rating": str(int(row.get("rating") or 0)),
                "knowledge": "True",
                "islanguage": _flag(language),
                "isnativelanguage": _flag(native),
                "skillspecializations": _specs(specs.get(name), tr),
            }
        )

    groups = [
        {"name": tr(name), "name_english": name, "rating": str(int(rating)), "isbroken": "False"}
        for name, rating in sorted(state.skill_groups.items())
        if int(rating or 0) > 0
    ]
    return {"skill": out, "skillgroup": groups}


def _specs(spec: str | None, tr: Any) -> dict[str, list[dict[str, str]]] | None:
    if not spec:
        return None
    return {"skillspecialization": [{"name": tr(spec), "name_english": spec}]}
