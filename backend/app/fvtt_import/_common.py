"""Helpers every part of the Foundry VTT import shares: reading the author's
fields without trusting their shape, and matching an item to the catalog."""

from __future__ import annotations

from typing import Any

from ..chummer_import._common import _by_name
from ..notices import Notice, notice, ui

#: Foundry attribute key -> this app's
_ATTRIBUTES = {
    "body": "BOD",
    "agility": "AGI",
    "reaction": "REA",
    "strength": "STR",
    "charisma": "CHA",
    "intuition": "INT",
    "logic": "LOG",
    "willpower": "WIL",
    "edge": "EDG",
    "magic": "MAG",
    "resonance": "RES",
}

#: the most of one row the models take (`qty`, le=999)
_MAX_QTY = 999


def _num(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError, OverflowError):
        return default


def _d(value: Any) -> dict[str, Any]:
    """`value` if it is an object, else an empty one: every field of the file is
    the author's, and a string where an object belongs must not crash the read."""
    return value if isinstance(value, dict) else {}


def _l(value: Any) -> list[dict[str, Any]]:
    """The objects in `value`, if it is a list."""
    return [v for v in value if isinstance(v, dict)] if isinstance(value, list) else []


def _flags(item: dict[str, Any]) -> dict[str, Any]:
    return _d(_d(item.get("system")).get("importFlags"))


class _Matcher:
    """Foundry item -> catalog id for one bucket: GUID, English name, name."""

    def __init__(self, rows: list[dict[str, Any]]):
        self.ids = {str(r["id"]).lower(): str(r["id"]) for r in rows}
        self.by_name = _by_name(rows)

    def find(self, item: dict[str, Any]) -> str | None:
        flags = _flags(item)
        sid = str(flags.get("sourceid") or "").strip().lower()
        if sid in self.ids:
            return self.ids[sid]
        for name in (flags.get("name"), item.get("name"), _base_name(str(item.get("name") or ""))):
            got = self.by_name.get(str(name or "").strip().lower())
            if got:
                return got
        return None

    def match(self, item: dict[str, Any], warn: list[Notice], kind: str) -> str | None:
        got = self.find(item)
        if not got:
            warn.append(notice("engine.import.skippedUnknown", kind=ui(kind), name=str(item.get("name") or "")))
        return got


def _paren(name: str) -> tuple[str, str] | None:
    """ "Improved Ability (Pistols)" -> ("Improved Ability", "Pistols").
    Slicing, not a regex: the name comes from an uploaded file (ReDoS)."""
    rest = name.rstrip()
    if not rest.endswith(")"):
        return None
    start = rest.rfind("(", 0, -1)
    if start < 0 or ")" in rest[start + 1 : -1]:
        return None
    return rest[:start].rstrip(), rest[start + 1 : -1]


def _base_name(name: str) -> str:
    """ "Improved Ability (Pistols)" -> "Improved Ability"."""
    got = _paren(name)
    return got[0] if got else name


def _extra(item: dict[str, Any]) -> str | None:
    """What the name carries in parentheses past the English name — the
    Chummer importer names an item by its `fullname`."""
    name = str(item.get("name") or "")
    got = _paren(name)
    if not got:
        return None
    english = str(_flags(item).get("name") or "")
    return None if english and english == name else got[1].strip() or None


def _tech(item: dict[str, Any]) -> dict[str, Any]:
    return _d(_d(item.get("system")).get("technology"))


def _rating(item: dict[str, Any]) -> int:
    return max(1, _num(_tech(item).get("rating"), 1))


def _embedded(item: dict[str, Any]) -> list[dict[str, Any]]:
    """What Foundry keeps inside an item: a weapon's accessories and ammo, an
    armor's mods."""
    got = _d(_d(item.get("flags")).get("shadowrun5e")).get("embeddedItems")
    return [i for i in got if isinstance(i, dict)] if isinstance(got, list) else []
