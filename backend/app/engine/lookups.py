"""Catalog accessors: ``id`` / ``name`` -> catalog row.

These are the only place code should reach into ``catalog()`` to find a single
entry. They depend on nothing else in the engine, so they live in their own
module and are re-exported from ``app.engine``.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ..data_loader import catalog, catalog_list, catalog_ware

DEFAULT_STREAM_NAME = "Default"


def _match_by(rows: Iterable[dict[str, Any]] | None, field: str, value: object) -> dict[str, Any] | None:
    """First row whose ``field`` equals ``value`` (the catalog row itself, not a copy)."""
    for row in rows or []:
        if row.get(field) == value:
            return row
    return None


def _quality_by_id(qid: str) -> dict[str, Any] | None:
    return _match_by(catalog().get("qualities"), "id", qid)


def _quality_by_name(name: str) -> dict[str, Any] | None:
    return _match_by(catalog().get("qualities"), "name", name)


def _power_by_id(pid: str) -> dict[str, Any] | None:
    return _match_by(catalog().get("powers"), "id", pid)


def _power_by_name(name: str) -> dict[str, Any] | None:
    return _match_by(catalog().get("powers"), "name", name)


def critter_power_rows(names: list[str]) -> list[dict[str, Any]]:
    """Spirit / sprite power names with what SR5 p.394 gives each one.

    `traditions.xml` and `streams.xml` name the powers and nothing else, so
    every name is looked up in `critterpowers.xml` for its type, action, range
    and duration. A name the data does not know still comes back as a row with
    the name alone — the sheet prints it either way.
    """
    by_name = {str(row.get("name") or ""): row for row in catalog().get("critter_powers") or []}
    rows: list[dict[str, Any]] = []
    for name in names:
        # A spirit names the flavour it comes in — `Engulf (Fire)`, `Enhanced
        # Senses (Smell)` — where the power itself is the part before the
        # bracket, which is what carries the action and the duration.
        spec = by_name.get(name) or by_name.get(name.split(" (")[0].strip()) or {}
        rows.append(
            {
                "name": name,
                "type": spec.get("type") or "",
                "action": spec.get("action") or "",
                "range": spec.get("range") or "",
                "duration": spec.get("duration") or "",
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
    return rows


def _enhancement_by_id(eid: str) -> dict[str, Any] | None:
    return _match_by(catalog().get("enhancements"), "id", eid)


def _mentor_by_id(mid: str) -> dict[str, Any] | None:
    return _match_by(catalog().get("mentors"), "id", mid)


def _paragon_by_id(pid: str) -> dict[str, Any] | None:
    return _match_by(catalog().get("paragons"), "id", pid)


def _spell_by_name(name: str) -> dict[str, Any] | None:
    return _match_by(catalog().get("spells"), "name", name)


def _spell_by_id(sid: str) -> dict[str, Any] | None:
    return _match_by(catalog().get("spells"), "id", sid)


def _tradition_by_id(tid: str | None) -> dict[str, Any] | None:
    if not tid:
        return None
    return _match_by(catalog().get("traditions"), "id", tid)


def _spirit_by_id(sid: str) -> dict[str, Any] | None:
    return _match_by(catalog().get("spirits"), "id", sid)


def _stream_by_id(sid: str | None) -> dict[str, Any] | None:
    if not sid:
        return None
    return _match_by(catalog().get("streams"), "id", sid)


def _default_stream() -> dict[str, Any] | None:
    streams: list[dict[str, Any]] = catalog().get("streams") or []
    match = _match_by(streams, "name", DEFAULT_STREAM_NAME)
    if match is not None:
        return match
    return streams[0] if streams else None


def _complex_form_by_id(fid: str) -> dict[str, Any] | None:
    return _match_by(catalog().get("complex_forms"), "id", fid)


def _sprite_by_id(sid: str) -> dict[str, Any] | None:
    return _match_by(catalog().get("sprites"), "id", sid)


def _focus_by_id(gid: str) -> dict[str, Any] | None:
    return _match_by(catalog().get("foci"), "id", gid)


def _metamagic_by_id(mid: str) -> dict[str, Any] | None:
    return _match_by(catalog().get("metamagics"), "id", mid)


def _metamagic_by_name(name: str) -> dict[str, Any] | None:
    return _match_by(catalog().get("metamagics"), "name", name)


def _magic_art_by_id(art_id: str) -> dict[str, Any] | None:
    return _match_by(catalog().get("magic_arts"), "id", art_id)


def _echo_by_id(echo_id: str) -> dict[str, Any] | None:
    return _match_by(catalog().get("echoes"), "id", echo_id)


def _echo_by_name(name: str) -> dict[str, Any] | None:
    target = str(name or "").strip()
    if not target:
        return None
    return _match_by(catalog().get("echoes"), "name", target)


def _ware_by_id(kind: str, wid: str) -> dict[str, Any] | None:
    return _match_by(catalog_ware(kind).get("items"), "id", wid)


def _ware_by_name(kind: str, name: str) -> dict[str, Any] | None:
    return _match_by(catalog_ware(kind).get("items"), "name", name)


def _grade_by_name(kind: str, name: str) -> dict[str, Any]:
    grades: list[dict[str, Any]] = catalog_ware(kind).get("grades") or []
    match = _match_by(grades, "name", name)
    if match is not None:
        return match
    other = "bioware" if kind == "cyberware" else "cyberware"
    other_match = _match_by(catalog_ware(other).get("grades"), "name", name)
    if other_match is not None:
        return other_match
    fallback: dict[str, Any] = {"name": "Standard", "ess": 1.0, "cost": 1.0}
    return next((g for g in grades if g.get("name") == "Standard"), fallback)


def _item_by_id(kind: str, item_id: str) -> dict[str, Any] | None:
    return _match_by(catalog_list(kind), "id", item_id)


def find_metatype(name: str, variant: str | None) -> dict[str, Any]:
    data = catalog()
    by_name: dict[str, dict[str, Any]] = data["all_metatypes"]
    if variant:
        base_list: list[dict[str, Any]] = data["metatypes"]
        for base in base_list:
            if base.get("name") != name:
                continue
            metavariants: list[dict[str, Any]] = base.get("metavariants") or []
            for mv in metavariants:
                if mv.get("name") == variant:
                    return mv
        if variant in by_name:
            return by_name[variant]
    if name in by_name:
        return by_name[name]
    raise KeyError(f"Unknown metatype: {name}/{variant}")
