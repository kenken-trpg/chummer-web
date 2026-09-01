"""Catalog accessors: ``id`` / ``name`` -> catalog row.

These are the only place code should reach into ``catalog()`` to find a single
entry. They depend on nothing else in the engine, so they live in their own
module and are re-exported from ``app.engine``.
"""

from __future__ import annotations

from typing import Any

from ..data_loader import catalog

DEFAULT_STREAM_NAME = "Default"


def _quality_by_id(qid: str) -> dict[str, Any] | None:
    for q in catalog()["qualities"]:
        if q["id"] == qid:
            return q
    return None


def _quality_by_name(name: str) -> dict[str, Any] | None:
    for q in catalog()["qualities"]:
        if q["name"] == name:
            return q
    return None


def _power_by_id(pid: str) -> dict[str, Any] | None:
    for item in catalog().get("powers") or []:
        if item["id"] == pid:
            return item
    return None


def _power_by_name(name: str) -> dict[str, Any] | None:
    for item in catalog().get("powers") or []:
        if item["name"] == name:
            return item
    return None


def _enhancement_by_id(eid: str) -> dict[str, Any] | None:
    for item in catalog().get("enhancements") or []:
        if item["id"] == eid:
            return item
    return None


def _mentor_by_id(mid: str) -> dict[str, Any] | None:
    for item in catalog().get("mentors") or []:
        if item["id"] == mid:
            return item
    return None


def _spell_by_name(name: str) -> dict[str, Any] | None:
    for item in catalog().get("spells") or []:
        if item["name"] == name:
            return item
    return None


def _spell_by_id(sid: str) -> dict[str, Any] | None:
    for item in catalog().get("spells") or []:
        if item["id"] == sid:
            return item
    return None


def _tradition_by_id(tid: str | None) -> dict[str, Any] | None:
    if not tid:
        return None
    for item in catalog().get("traditions") or []:
        if item["id"] == tid:
            return item
    return None


def _spirit_by_id(sid: str) -> dict[str, Any] | None:
    for item in catalog().get("spirits") or []:
        if item["id"] == sid:
            return item
    return None


def _stream_by_id(sid: str | None) -> dict[str, Any] | None:
    if not sid:
        return None
    for item in catalog().get("streams") or []:
        if item["id"] == sid:
            return item
    return None


def _default_stream() -> dict[str, Any] | None:
    for item in catalog().get("streams") or []:
        if item["name"] == DEFAULT_STREAM_NAME:
            return item
    streams = catalog().get("streams") or []
    return streams[0] if streams else None


def _complex_form_by_id(fid: str) -> dict[str, Any] | None:
    for item in catalog().get("complex_forms") or []:
        if item["id"] == fid:
            return item
    return None


def _sprite_by_id(sid: str) -> dict[str, Any] | None:
    for item in catalog().get("sprites") or []:
        if item["id"] == sid:
            return item
    return None


def _focus_by_id(gid: str) -> dict[str, Any] | None:
    for item in catalog().get("foci") or []:
        if item["id"] == gid:
            return item
    return None


def _metamagic_by_id(mid: str) -> dict[str, Any] | None:
    for item in catalog().get("metamagics") or []:
        if item["id"] == mid:
            return item
    return None


def _metamagic_by_name(name: str) -> dict[str, Any] | None:
    for item in catalog().get("metamagics") or []:
        if item.get("name") == name:
            return item
    return None


def _magic_art_by_id(art_id: str) -> dict[str, Any] | None:
    for item in catalog().get("magic_arts") or []:
        if item["id"] == art_id:
            return item
    return None


def _echo_by_id(echo_id: str) -> dict[str, Any] | None:
    for item in catalog().get("echoes") or []:
        if item["id"] == echo_id:
            return item
    return None


def _echo_by_name(name: str) -> dict[str, Any] | None:
    target = str(name or "").strip()
    if not target:
        return None
    for item in catalog().get("echoes") or []:
        if item.get("name") == target:
            return item
    return None


def _ware_by_id(kind: str, wid: str) -> dict[str, Any] | None:
    for item in catalog().get(kind, {}).get("items") or []:
        if item["id"] == wid:
            return item
    return None


def _ware_by_name(kind: str, name: str) -> dict[str, Any] | None:
    for item in catalog().get(kind, {}).get("items") or []:
        if item["name"] == name:
            return item
    return None


def _grade_by_name(kind: str, name: str) -> dict[str, Any]:
    grades = catalog().get(kind, {}).get("grades") or []
    for g in grades:
        if g["name"] == name:
            return g
    other = "bioware" if kind == "cyberware" else "cyberware"
    for g in catalog().get(other, {}).get("grades") or []:
        if g["name"] == name:
            return g
    return next((g for g in grades if g["name"] == "Standard"), {"name": "Standard", "ess": 1.0, "cost": 1.0})


def _item_by_id(kind: str, item_id: str) -> dict[str, Any] | None:
    for item in catalog().get(kind) or []:
        if item["id"] == item_id:
            return item
    return None


def find_metatype(name: str, variant: str | None) -> dict[str, Any]:
    data = catalog()
    by_name = data["all_metatypes"]
    if variant:
        for base in data["metatypes"]:
            if base["name"] != name:
                continue
            for mv in base.get("metavariants", []):
                if mv["name"] == variant:
                    return mv
        if variant in by_name:
            return by_name[variant]
    if name in by_name:
        return by_name[name]
    raise KeyError(f"Unknown metatype: {name}/{variant}")
