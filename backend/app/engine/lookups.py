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


def _item_by_id(kind: str, item_id: str) -> dict[str, Any] | None:
    for item in catalog().get(kind) or []:
        if item["id"] == item_id:
            return item
    return None
