"""Vehicle & drone resolution: stat formatting, the vehicle/mod constraint
predicates, stat-bonus application, R5 mod-slot accounting, and the
``resolve_gear``-driven resolvers for drones, vehicle mods and weapon mounts.

Imports only ``catalog`` / ``eval_formula`` / already-extracted engine modules
/ models — never back into ``app.engine``.
"""

from __future__ import annotations

from typing import Any

from ...data_loader import catalog, eval_formula
from ...improvements import substitute_rating
from ...models import CharacterState, GearInstall
from ._common import _leading_vehicle_stat


def _format_vehicle_stat(base: str, current: int, offroad: int | None = None) -> str:
    parts = str(base or "").split("/")
    if len(parts) > 1 or offroad is not None:
        off = offroad if offroad is not None else _leading_vehicle_stat(parts[1] if len(parts) > 1 else "")
        return f"{current}/{off}"
    return str(current)


def _vehicle_extras(spec: dict[str, Any], stats: dict[str, int], cost: int) -> dict[str, int | float]:
    return {
        "Body": stats.get("body") or 0,
        "body": stats.get("body") or 0,
        "Armor": stats.get("armor") or 0,
        "Handling": stats.get("handling") or 0,
        "Speed": stats.get("speed") or 0,
        "Acceleration": stats.get("accel") or 0,
        "Sensor": stats.get("sensor") or 0,
        "Pilot": stats.get("pilot") or 0,
        "Seats": stats.get("seats") or 0,
        "Vehicle Cost": cost,
    }


def vehicle_matches(vehicle: dict[str, Any], cons: dict[str, Any] | None) -> bool:
    cons = cons or {}
    names = list(cons.get("names") or [])
    contains = list(cons.get("category_contains") or [])
    equals = list(cons.get("category_equals") or [])
    body_lte = cons.get("body_lte")
    body_gte = cons.get("body_gte")
    if not names and not contains and not equals and body_lte is None and body_gte is None:
        return True
    name = str(vehicle.get("name") or "")
    category = str(vehicle.get("category") or "")
    body = _leading_vehicle_stat(str(vehicle.get("body") or "0"))
    if names and name not in names:
        return False
    if contains and not any(part in category for part in contains):
        return False
    if equals and category not in equals:
        return False
    if body_lte is not None and body > int(body_lte):
        return False
    if body_gte is not None and body < int(body_gte):
        return False
    return True


def mod_fits_vehicle(mod: dict[str, Any], vehicle: dict[str, Any]) -> bool:
    if not vehicle_matches(vehicle, mod.get("required")):
        return False
    forbidden = mod.get("forbidden") or {}
    has_forbidden = bool(
        forbidden.get("names")
        or forbidden.get("category_contains")
        or forbidden.get("category_equals")
        or forbidden.get("body_lte") is not None
        or forbidden.get("body_gte") is not None
    )
    if has_forbidden and vehicle_matches(vehicle, forbidden):
        return False
    return True


def _apply_vehicle_bonus(stats: dict[str, int], nodes: list[dict[str, Any]], rating: int) -> None:
    aliases = {
        "handling": "handling",
        "offroadhandling": "offroadhandling",
        "speed": "speed",
        "accel": "accel",
        "offroadaccel": "offroadaccel",
        "body": "body",
        "armor": "armor",
        "pilot": "pilot",
        "sensor": "sensor",
        "seats": "seats",
    }
    for node in substitute_rating(list(nodes or []), rating):
        tag = str(node.get("tag") or "")
        key = aliases.get(tag)
        if not key:
            continue
        raw = str(node.get("value") or "").strip()
        if raw.lower() == "rating":
            stats[key] = int(rating)
            continue
        delta = int(eval_formula(raw, rating, 0))
        if raw.startswith("+") or raw.startswith("-"):
            stats[key] = int(stats.get(key) or 0) + delta
        else:
            stats[key] = delta


def _clamp_vehicle_rating(spec: dict[str, Any], rating: int, extras: dict[str, int | float]) -> int:
    max_expr = str(spec.get("maxrating_expr") or spec.get("maxrating") or "0")
    min_expr = str(spec.get("minrating_expr") or spec.get("minrating") or "0")
    max_rating = int(eval_formula(max_expr, rating or 1, 0, extras)) if max_expr else int(spec.get("maxrating") or 0)
    if max_rating <= 0:
        return 1
    min_rating = int(eval_formula(min_expr, rating or 1, 1, extras)) if min_expr else 1
    min_rating = max(1, min_rating)
    return max(min_rating, min(max_rating, int(rating or min_rating)))


R5_MOD_SLOT_CATEGORIES = (
    "Powertrain",
    "Protection",
    "Weapons",
    "Body",
    "Electromagnetic",
    "Cosmetic",
)
R5_SLOT_LABELS = {
    "Powertrain": "パワートレイン",
    "Protection": "防護",
    "Weapons": "武器",
    "Body": "ボディ",
    "Electromagnetic": "電磁",
    "Cosmetic": "外装",
}
R5_SLOT_ADD_KEYS = {
    "Powertrain": "powertrainmodslots",
    "Protection": "protectionmodslots",
    "Weapons": "weaponmodslots",
    "Body": "bodymodslots",
    "Electromagnetic": "electromagneticmodslots",
    "Cosmetic": "cosmeticmodslots",
}


def _host_is_drone(row: dict[str, Any]) -> bool:
    return str(row.get("category") or "").startswith("Drones")


def _add_vehicle_slot_use(parent: dict[str, Any], slots: int, category: str, included: bool) -> None:
    if included:
        return
    used = max(0, int(slots))
    if _host_is_drone(parent):
        parent["slots_used"] = int(parent.get("slots_used") or 0) + used
        return
    if category not in R5_SLOT_ADD_KEYS:
        return
    tracks = parent.setdefault("_slot_used", {})
    tracks[category] = int(tracks.get(category) or 0) + used


def _finalize_vehicle_slots(hosts: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for row in hosts:
        body = int((row.get("stats") or {}).get("body") or _leading_vehicle_stat(str(row.get("body") or "0")))
        if _host_is_drone(row):
            listed = row.get("modslots")
            maximum = int(listed) if listed is not None else body
            used = int(row.get("slots_used") or 0)
            row["slots_max"] = maximum
            row["slot_tracks"] = []
            if used > maximum:
                errors.append(f"{row['name']} の改造スロット超過（{used}/{maximum}）")
            continue
        used_map = row.pop("_slot_used", None) or {}
        tracks: list[dict[str, Any]] = []
        total_used = 0
        for category in R5_MOD_SLOT_CATEGORIES:
            extra = int(row.get(R5_SLOT_ADD_KEYS[category]) or 0)
            maximum = max(0, body + extra)
            used = int(used_map.get(category) or 0)
            total_used += used
            tracks.append(
                {
                    "category": category,
                    "label": R5_SLOT_LABELS[category],
                    "used": used,
                    "max": maximum,
                }
            )
            if used > maximum:
                errors.append(f"{row['name']} の{R5_SLOT_LABELS[category]}スロット超過（{used}/{maximum}）")
        row["slot_tracks"] = tracks
        row["slots_used"] = total_used
        row["slots_max"] = body
    return errors


def _iter_vehicle_hosts(state: CharacterState) -> list[tuple[GearInstall, dict[str, Any]]]:
    drones = {item["id"]: item for item in catalog().get("drones") or []}
    vehicles = {item["id"]: item for item in catalog().get("vehicles") or []}
    out: list[tuple[GearInstall, dict[str, Any]]] = []
    for inst in list(state.drones or []):
        spec = drones.get(inst.gear_id)
        if spec:
            out.append((inst, spec))
    for inst in list(state.vehicles or []):
        spec = vehicles.get(inst.gear_id)
        if spec:
            out.append((inst, spec))
    return out
