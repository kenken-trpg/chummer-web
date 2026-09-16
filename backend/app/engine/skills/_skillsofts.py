"""Activesofts and knowsofts: ratings a skilljack or skillwires lets a character use."""

from __future__ import annotations

from typing import Any

from ...data_loader import catalog
from ...improvements import EffectsDict, _as_int, substitute_rating
from ...notices import Notice, notice, term
from ..selects import (
    _skillsoft_kind,
    skillsoft_options,
)
from ._knowledge import KNOWLEDGE_DEFAULT_ATTR


def _skillsoft_value(node: dict[str, Any]) -> int:
    fields = node.get("fields") or {}
    return _as_int(fields.get("val") or fields.get("value") or node.get("value"))


def _merge_skill_ratings(base: dict[str, int], extra: dict[str, int]) -> dict[str, int]:
    out = dict(base)
    for name, rating in extra.items():
        name = str(name or "").strip()
        value = int(rating or 0)
        if not name or value <= 0:
            continue
        out[name] = max(int(out.get(name) or 0), value)
    return out


def resolve_skillsofts(
    gear_items: list[dict[str, Any]],
    skills_data: dict[str, Any],
    effects: EffectsDict,
    warnings: list[Notice],
    *,
    hardwires: dict[str, dict[str, int]] | None = None,
) -> dict[str, Any]:
    """Ratings a skillsoft / autosoft (or a hardwire) supplies instead of training.

    ``hardwires`` seeds the two buckets because Chummer reads hardwired ratings
    off the same cyberware rating a skillsoft does — but a hardwire carries its
    own rating, so it is not gated on skillwires or a skilljack.
    """
    wires = int(effects.get("skillwires") or 0)
    jack = int(effects.get("skilljack") or 0)
    specs = {item["id"]: item for item in catalog().get("gear") or []}
    active_names = {skill["name"] for skill in skills_data.get("skills") or []}
    knowledge_names = {skill["name"] for skill in skills_data.get("knowledge") or []}
    active: dict[str, int] = dict((hardwires or {}).get("active") or {})
    knowledge: dict[str, int] = dict((hardwires or {}).get("knowledge") or {})

    def add_rating(bucket: dict[str, int], name: str, rating: int) -> None:
        if not name or rating <= 0:
            return
        bucket[name] = max(int(bucket.get(name) or 0), int(rating))

    for item in gear_items:
        spec = specs.get(str(item.get("gear_id") or ""))
        if not spec:
            continue
        extra = str(item.get("extra") or "").strip()
        nodes = substitute_rating(list(spec.get("bonus") or []), int(item.get("rating") or 1))
        for node in nodes:
            kind = _skillsoft_kind(node)
            if not kind:
                continue
            label = str(item.get("label") or spec.get("name") or "")
            value = _skillsoft_value(node)
            options = set(skillsoft_options(node, skills_data))
            if extra and extra not in options:
                continue
            if not extra:
                continue
            if kind == "active":
                if extra not in active_names:
                    continue
                if wires <= 0:
                    warnings.append(notice("engine.skills.needsSkillwires", name=term(label)))
                    continue
                if value > wires:
                    warnings.append(notice("engine.skills.overSkillwires", name=term(label), rating=value, limit=wires))
                add_rating(active, extra, min(value, wires))
            else:
                if extra not in knowledge_names:
                    continue
                if jack <= 0:
                    warnings.append(notice("engine.skills.needsSkilljack", name=term(label)))
                    continue
                if value > jack:
                    warnings.append(notice("engine.skills.overSkilljack", name=term(label), rating=value, limit=jack))
                add_rating(knowledge, extra, min(value, jack))
    return {
        "active": active,
        "knowledge": knowledge,
        "all": {**knowledge, **active},
        "skillwires": wires,
        "skilljack": jack,
    }


def _attach_skillsoft_knowledge(
    public: list[dict[str, Any]],
    skillsoft: dict[str, int],
    skills_data: dict[str, Any],
) -> None:
    catalog_by_name = {skill["name"]: skill for skill in skills_data.get("knowledge") or []}
    by_name = {row["name"]: row for row in public}
    for name, rating in skillsoft.items():
        spec = catalog_by_name.get(name)
        if not spec:
            continue
        row = by_name.get(name)
        if row:
            row["skillsoft"] = int(rating)
            continue
        public.append(
            {
                "name": name,
                "category": spec.get("category") or "Street",
                "attribute": str(
                    spec.get("attribute") or KNOWLEDGE_DEFAULT_ATTR.get(spec.get("category") or "", "INT")
                ).upper(),
                "rating": 0,
                "native": False,
                "skillsoft": int(rating),
            }
        )
