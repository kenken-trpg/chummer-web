"""Leaf helpers shared across the 'ware resolvers.

Kept dependency-free so both ``ware/resolve.py`` and ``ware/vehicles.py`` can
import them without a cycle (mirrors ``gear/_common.py``).
"""

from __future__ import annotations

from typing import Any

from ...models import CyberwareInstall


def _cascade_orphans(
    items: list[CyberwareInstall],
    extra_parent_ids: set[str] | None = None,
) -> list[CyberwareInstall]:
    ids = {item.id for item in items} | (extra_parent_ids or set())
    keep = [item for item in items if not item.parent_id or item.parent_id in ids]
    if len(keep) == len(items):
        return keep
    return _cascade_orphans(keep, extra_parent_ids)


def _public_installed(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item["id"],
        "ware_id": item["ware_id"],
        "name": item["name"],
        "category": item["category"],
        "rating": item["rating"],
        "grade": item["grade"],
        "wireless": item["wireless"],
        "parent_id": item.get("parent_id"),
        "included": bool(item.get("included")),
        "essence": item["essence"],
        "nuyen": item["nuyen"],
        "capacity_used": item.get("capacity_used") or 0,
        "capacity_max": item.get("capacity_max") or 0,
        "rating_min": item.get("rating_min") or 1,
        "rating_max": item.get("rating_max") or 1,
        "limb_str": item.get("limb_str"),
        "limb_agi": item.get("limb_agi"),
        "limb_armor": item.get("limb_armor"),
        "selectside": bool(item.get("selectside")),
        "side": item.get("side"),
        "avail": item.get("avail") or "",
        "avail_value": int(item.get("avail_value") or 0),
        "restricted_gear": bool(item.get("restricted_gear")),
        "device_rating": int(item.get("device_rating") or 0),
        "source": item.get("source"),
    }
