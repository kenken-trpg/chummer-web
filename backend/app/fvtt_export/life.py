"""What the runner is outside a run: qualities, contacts and lifestyles."""

from __future__ import annotations

from typing import Any


def _qualities(derived: dict[str, Any], tr: Any) -> list[dict[str, str]]:
    """The importer takes `bp` as the karma per level and `extra` as the
    rating, so a chosen extra that is text (Allergy's allergen) reads as 0."""
    out = []
    for row in derived.get("qualities") or []:
        name = str(row.get("name") or "")
        if not name:
            continue
        extra = str(row.get("extra") or "")
        out.append(
            {
                "sourceid": str(row.get("id") or ""),
                "name": tr(name),
                "name_english": name,
                "extra": extra or None,
                "qualitytype_english": str(row.get("category") or "Positive"),
                "bp": str(int(row.get("karma") or 0)),
                "source": str(row.get("source") or ""),
                "page": str(row.get("page") or ""),
            }
        )
    return out


def _contacts(derived: dict[str, Any]) -> list[dict[str, str]]:
    """Free text on both sides, so nothing to translate. A group contact's
    connection goes out bare: the importer reads a number or `Group(n)` alike."""
    return [
        {
            "guid": str(row.get("id") or ""),
            "name": str(row.get("name") or ""),
            "role": str(row.get("role") or ""),
            "connection": str(int(row.get("connection") or 0)),
            "loyalty": str(int(row.get("loyalty") or 0)),
            "type": "Group" if row.get("group") else "Contact",
            "forcedloyalty": str(int(row.get("forced_loyalty") or 0)),
            "family": "False",
            "blackmail": "False",
        }
        for row in derived.get("contacts") or []
    ]


def _lifestyles(derived: dict[str, Any], tr: Any) -> list[dict[str, str]]:
    """`baselifestyle` lower-cased is the Foundry type ("medium", ...), so it
    stays the data name; the monthly cost is the finished one."""
    out = []
    for row in derived.get("lifestyles") or []:
        base = str(row.get("name") or "")
        out.append(
            {
                "guid": str(row.get("id") or ""),
                "sourceid": str(row.get("lifestyle_id") or ""),
                "name": tr(base),
                "baselifestyle": base,
                "baselifestyle_english": base,
                "totalmonthlycost": str(int(row.get("monthly") or 0)),
                "months": str(int(row.get("months") or 0)),
                "increment": str(row.get("increment") or "month"),
                "purchased": "False",
                "source": str(row.get("source") or ""),
                "page": str(row.get("page") or ""),
            }
        )
    return out
