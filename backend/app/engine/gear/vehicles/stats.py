"""Vehicle stats: formatting, the vehicle / mod constraint predicates,
stat-bonus application and the rating clamp."""

from __future__ import annotations

import math
from typing import Any

from ....data_loader import eval_formula
from ....improvements import substitute_rating
from ....rules import current_rules
from .._common import (
    _leading_vehicle_stat,
)


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
        "offroadspeed": "offroadspeed",
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
        # off-road only exists where the vehicle prints a second value ("4/3")
        if key.startswith("offroad") and key not in stats:
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


#: what an uncapped Chummer maximum (`int.MaxValue`) comes to here
UNCAPPED = 10**6


def _is_drone(vehicle: dict[str, Any]) -> bool:
    return "Drone" in str(vehicle.get("category") or "")


def _max_vehicle_armor(vehicle: dict[str, Any]) -> int:
    """The most armor a vehicle carries, mods included (Chummer's
    `Vehicle.MaxArmor`): its printed Body + Armor (Rigger 5.0 p.159), or for a
    drone under `<dronearmormultiplierenabled>` that sum times
    `<dronearmorflatnumber>`, with a Body of 0 counted as 0.5. The optional
    drone modification rules (`<dronemods>`) lift a drone's ceiling
    altogether."""
    body = _leading_vehicle_stat(str(vehicle.get("body") or "0"))
    armor = _leading_vehicle_stat(str(vehicle.get("armor") or "0"))
    rules = current_rules()
    if rules.drone_mods and _is_drone(vehicle):
        return UNCAPPED
    if rules.drone_armor_multiplier_enabled and _is_drone(vehicle):
        return math.floor((max(body, 0.5) + armor) * rules.drone_armor_multiplier + 0.5)
    return max(body + armor, 1)


def _clamp_vehicle_rating(spec: dict[str, Any], rating: int, extras: dict[str, int | float]) -> int:
    max_expr = str(spec.get("maxrating_expr") or spec.get("maxrating") or "0")
    min_expr = str(spec.get("minrating_expr") or spec.get("minrating") or "0")
    max_rating = int(eval_formula(max_expr, rating or 1, 0, extras)) if max_expr else int(spec.get("maxrating") or 0)
    if max_rating <= 0:
        return 1
    min_rating = int(eval_formula(min_expr, rating or 1, 1, extras)) if min_expr else 1
    min_rating = max(1, min_rating)
    return max(min_rating, min(max_rating, int(rating or min_rating)))


#: the printed stat a drone mod of each category may at most double
_DOUBLED_STAT = {
    "HANDLING": "handling",
    "SPEED": "speed",
    "ACCELERATION": "accel",
    "SENSOR": "sensor",
}


def drone_stat_ceiling(mod: dict[str, Any], vehicle: dict[str, Any]) -> int:
    """The highest rating a drone may give a stat mod (`VehicleMod.MaxRating`):
    no drone attribute goes past twice its printed value (Rigger 5.0 p.123),
    with 0 counted as 0.5. Pilot is held to that only under
    `<dronemodsmaximumpilot>` (`Vehicle.MaxPilot`)."""
    if not _is_drone(vehicle):
        return UNCAPPED
    stat = _DOUBLED_STAT.get(str(mod.get("category") or "").upper())
    if stat is None and (
        str(mod.get("category") or "").upper() == "PILOT"
        or str(mod.get("name") or "").lower().startswith("pilot program")
    ):
        stat = "pilot" if current_rules().drone_mods_maximum_pilot else None
    if stat is None:
        return UNCAPPED
    return max(_leading_vehicle_stat(str(vehicle.get(stat) or "0")) * 2, 1)


def apply_armor_penalty(vehicle: dict[str, Any], stats: dict[str, int], *, drone_rules: bool) -> None:
    """Take off the speed an overloaded vehicle loses (Chummer's
    `Vehicle.TotalSpeed` / `TotalHandling` / `TotalAccel`): each 3 points of
    armor past three times its Body cost a point of Speed and of Handling,
    each 6 a point of Acceleration, off-road values alike. Only under the
    drone modification rules does a drone's added armor count; otherwise it
    is the printed armor, which never goes that high."""
    armor = int(stats.get("armor") or 0) if drone_rules else _leading_vehicle_stat(str(vehicle.get("armor") or "0"))
    over = min(armor, _max_vehicle_armor(vehicle)) - int(stats.get("body") or 0) * 3
    if over <= 0:
        return
    for key, step in (("speed", 3), ("handling", 3), ("accel", 6)):
        for stat in (key, f"offroad{key}"):
            if stat in stats and over // step:
                stats[stat] = int(stats[stat] or 0) - over // step
