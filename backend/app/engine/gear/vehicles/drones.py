"""Drone and vehicle rows, and the stats published on them."""

from __future__ import annotations

from typing import Any

from ....data_loader import eval_formula
from ....models import CharacterState, GearInstall
from ...lookups import _item_by_id
from .._common import (
    _leading_vehicle_stat,
)
from .stats import _format_vehicle_stat


def _resolve_drones(state: CharacterState, kind: str = "drones") -> tuple[list[dict[str, Any]], int]:
    kept: list[GearInstall] = []
    public: list[dict[str, Any]] = []
    nuyen = 0
    for inst in list(getattr(state, kind) or []):
        spec = _item_by_id(kind, inst.gear_id)
        if not spec:
            continue
        cost = int(eval_formula(str(spec.get("cost") or "0"), 1, 0))
        nuyen += cost
        stats = {
            "handling": _leading_vehicle_stat(spec.get("handling")),
            "speed": _leading_vehicle_stat(spec.get("speed")),
            "accel": _leading_vehicle_stat(spec.get("accel")),
            "body": _leading_vehicle_stat(spec.get("body")),
            "armor": _leading_vehicle_stat(spec.get("armor")),
            "pilot": _leading_vehicle_stat(spec.get("pilot")),
            "sensor": _leading_vehicle_stat(spec.get("sensor")),
            "seats": _leading_vehicle_stat(spec.get("seats")),
        }
        for stat in ("handling", "speed", "accel"):
            parts = str(spec.get(stat) or "").split("/")
            if len(parts) > 1:
                stats[f"offroad{stat}"] = _leading_vehicle_stat(parts[1])
        kept.append(inst)
        public.append(
            {
                "id": inst.id,
                "gear_id": spec["id"],
                "name": spec["name"],
                "category": spec.get("category") or "",
                "handling": spec.get("handling") or "",
                "speed": spec.get("speed") or "",
                "accel": spec.get("accel") or "",
                "body": spec.get("body") or "",
                "armor": spec.get("armor") or "",
                "pilot": spec.get("pilot") or "",
                "sensor": spec.get("sensor") or "",
                "seats": spec.get("seats") or "",
                "stats": stats,
                "base_nuyen": cost,
                "nuyen": cost,
                "slots_used": 0,
                "slots_max": stats["body"],
                "slot_tracks": [],
                "modslots": spec.get("modslots"),
                "powertrainmodslots": int(spec.get("powertrainmodslots") or 0),
                "protectionmodslots": int(spec.get("protectionmodslots") or 0),
                "weaponmodslots": int(spec.get("weaponmodslots") or 0),
                "bodymodslots": int(spec.get("bodymodslots") or 0),
                "electromagneticmodslots": int(spec.get("electromagneticmodslots") or 0),
                "cosmeticmodslots": int(spec.get("cosmeticmodslots") or 0),
                "mods": [],
                "weapon_mounts": [],
                "sensors": [],
                "gear": [],
                "avail": spec.get("avail") or "",
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
    setattr(state, kind, kept)
    return public, nuyen


def _publish_drone_stats(drones: list[dict[str, Any]], sensors: list[dict[str, Any]]) -> None:
    children: dict[str, list[dict[str, Any]]] = {}
    for item in sensors:
        if item.get("parent_id"):
            children.setdefault(str(item.get("parent_id") or ""), []).append(item)
    for row in drones:
        stats = row.get("stats") or {}
        for stat in ("handling", "speed", "accel"):
            if stat not in stats:
                continue
            row[stat] = _format_vehicle_stat(
                str(row.get(stat) or ""), int(stats.get(stat) or 0), stats.get(f"offroad{stat}")
            )
        row["body"] = str(stats.get("body") or row.get("body") or "")
        row["armor"] = str(stats.get("armor") or row.get("armor") or "")
        row["pilot"] = str(stats.get("pilot") or row.get("pilot") or "")
        row["sensor"] = str(stats.get("sensor") or row.get("sensor") or "")
        row["seats"] = str(stats.get("seats") or row.get("seats") or "")
        row["sensors"] = children.get(str(row.get("id") or "")) or []
        row.pop("stats", None)
        row.pop("base_nuyen", None)
        row.pop("modslots", None)
        row.pop("powertrainmodslots", None)
        row.pop("protectionmodslots", None)
        row.pop("weaponmodslots", None)
        row.pop("bodymodslots", None)
        row.pop("electromagneticmodslots", None)
        row.pop("cosmeticmodslots", None)
