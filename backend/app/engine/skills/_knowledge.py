"""Knowledge skills: the free pool, native languages, and the type each one is filed under."""

from __future__ import annotations

from typing import Any

from ...models import CharacterState
from ...notices import Notice, notice

KNOWLEDGE_CATEGORIES = {"Academic", "Interest", "Language", "Professional", "Street"}


KNOWLEDGE_DEFAULT_ATTR = {
    "Academic": "LOG",
    "Professional": "LOG",
    "Street": "INT",
    "Interest": "INT",
    "Language": "INT",
}


def knowledge_pool(intuition: int, logic: int) -> int:
    return (max(1, int(intuition)) + max(1, int(logic))) * 2


def resolve_knowledge(
    state: CharacterState,
    skills_data: dict[str, Any],
    totals: dict[str, int],
    *,
    rating_cap: int = 6,
    native_limit: int = 1,
) -> dict[str, Any]:
    catalog_by_name = {skill["name"]: skill for skill in (skills_data.get("knowledge") or [])}
    warnings: list[Notice] = []
    ratings: dict[str, int] = {}
    for name, rating in (state.knowledge_skills or {}).items():
        name = str(name).strip()
        value = max(0, min(int(rating_cap), int(rating or 0)))
        if name and value > 0:
            ratings[name] = value

    natives: list[str] = []
    seen: set[str] = set()
    extras: list[str] = []
    limit = max(1, int(native_limit or 1))
    for name in state.native_languages or []:
        name = str(name).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        if len(natives) >= limit:
            extras.append(name)
            continue
        natives.append(name)
        ratings.pop(name, None)
    if extras:
        warnings.append(notice("engine.skills.nativeLimit", limit=limit))

    extra_categories: dict[str, str] = {}
    owned = set(ratings) | set(natives)
    for name, category in (state.knowledge_categories or {}).items():
        name = str(name).strip()
        if name not in owned or name in natives:
            continue
        category = str(category)
        if name in catalog_by_name:
            # Chummer lets a knowledge skill's type be changed while the
            # character is being built, listed ones included
            # (`KnowledgeSkill.AllowTypeChange`), so a saved type that differs
            # from the list is a choice, and what the costs follow — College
            # Education halves Academic points, whatever the list said.
            if category in KNOWLEDGE_CATEGORIES and category != catalog_by_name[name].get("category"):
                extra_categories[name] = category
            continue
        extra_categories[name] = category if category in KNOWLEDGE_CATEGORIES else "Street"
    for name in natives:
        if name not in catalog_by_name:
            extra_categories.setdefault(name, "Language")

    public: list[dict[str, Any]] = []
    names = list(natives) + sorted(name for name in ratings if name not in natives)
    for name in names:
        spec = catalog_by_name.get(name) or {}
        native = name in natives
        chosen = extra_categories.get(name)
        category = str(chosen or spec.get("category") or ("Language" if native else "Street"))
        if category not in KNOWLEDGE_CATEGORIES:
            category = "Street"
        # a changed type brings its default attribute with it, as in Chummer
        listed = None if chosen and spec else spec.get("attribute")
        attribute = str(listed or KNOWLEDGE_DEFAULT_ATTR.get(category) or "INT").upper()
        public.append(
            {
                "name": name,
                "category": category,
                "attribute": attribute,
                "rating": 0 if native else ratings[name],
                "native": native,
            }
        )

    state.knowledge_skills = ratings
    state.native_languages = natives
    state.knowledge_categories = extra_categories
    return {
        "spent": sum(ratings.values()),
        "max": knowledge_pool(int(totals.get("INT") or 1), int(totals.get("LOG") or 1)),
        "public": public,
        "warnings": warnings,
        "native_limit": limit,
    }
