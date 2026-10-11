"""The compactors: an ``EffectsDict`` boiled down to what the derived output
carries. Each one reads the accumulator and returns a plain dict or list —
nothing here mutates ``effects``, and the shapes are the ones
``compute/assemble.py`` hands to the client (the catalog uses the two
``*_from_nodes`` wrappers in ``__init__.py`` for a single item's preview)."""

from __future__ import annotations

from typing import Any

from ._common import (
    IMMUNE_KEYS,
    LIMIT_KINDS,
    SPECIAL_ARMOR_KEYS,
    limit_condition_label,
)
from .effects import EffectsDict


def special_armor_totals(effects: EffectsDict) -> dict[str, Any]:
    return {
        **{key: int(effects.get("special_armor", {}).get(key) or 0) for key in SPECIAL_ARMOR_KEYS},
        "immunities": {key: bool((effects.get("immunities") or {}).get(key)) for key in IMMUNE_KEYS},
    }


def compact_special_armor(effects: EffectsDict) -> dict[str, Any] | None:
    nums = {
        key: int(effects.get("special_armor", {}).get(key) or 0)
        for key in SPECIAL_ARMOR_KEYS
        if int(effects.get("special_armor", {}).get(key) or 0)
    }
    immunities = {key: True for key, value in (effects.get("immunities") or {}).items() if value}
    if not nums and not immunities:
        return None
    out: dict[str, Any] = dict(nums)
    if immunities:
        out["immunities"] = immunities
    return out


def compact_limit_modifiers(effects: EffectsDict) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in effects.get("limit_modifiers") or []:
        kind = str(row.get("limit") or "")
        value = int(row.get("value") or 0)
        if kind not in LIMIT_KINDS or value == 0:
            continue
        condition = str(row.get("condition") or "")
        out.append(
            {
                "limit": kind,
                "value": value,
                "condition": condition,
                "condition_label": row.get("condition_label") or limit_condition_label(condition),
                "source": str(row.get("source") or ""),
            }
        )
    return out
