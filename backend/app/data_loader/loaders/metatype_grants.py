"""Resolve the innate grants of metatypes whose grant path is supported.

Centaur is the first supported set. Loading XML references for another species
does not enable its effects before its chargen rules and removal costs exist.
"""

from __future__ import annotations

from typing import Any


def resolve_metatype_grants(
    meta: dict[str, Any],
    references: list[dict[str, Any]],
    definitions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_id = {row["id"]: row for row in definitions}
    by_name: dict[str, dict[str, Any]] = {}
    for row in definitions:
        by_name.setdefault(row["name"], row)
    grants = []
    for ref in references:
        spec = by_id.get(ref["name"]) or by_name.get(ref["name"])
        grants.append(
            {
                **(spec or {"id": "", "name": ref["name"], "unresolved": True}),
                "origin": "Metatype",
                "origin_id": meta["id"],
                "origin_name": meta["name"],
                "select": ref.get("select") or "",
                "rating": ref.get("rating") or "",
                "removable": bool(ref.get("removable")),
                # Innate metagenic qualities do not spend the SURGE allowance.
                "contributes_to_limit": False,
            }
        )
    return grants
