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
from ...models import CharacterState, GearInstall, VehicleModInstall, WeaponMountInstall
from ..lookups import _item_by_id
from ._common import (
    _capacity_value,
    _default_mount_parts,
    _find_mount_part,
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


def _ensure_drone_equipment(state: CharacterState) -> None:
    sensors = {item["id"]: item for item in catalog().get("sensors") or []}
    sensors_by_name = {item["name"]: item for item in sensors.values()}
    gear = {item["id"]: item for item in catalog().get("gear") or []}
    gear_by_name = {item["name"]: item for item in gear.values()}
    mods = {item["id"]: item for item in catalog().get("vehicle_mods") or []}
    mods_by_name = {item["name"]: item for item in mods.values()}
    have_sensors = {(row.parent_id, (sensors.get(row.gear_id) or {}).get("name")) for row in state.sensors or []}
    extra_sensors: list[GearInstall] = []
    have_gear = {(row.parent_id, (gear.get(row.gear_id) or {}).get("name")) for row in state.gear or []}
    extra_gear: list[GearInstall] = []
    for host, spec in _iter_vehicle_hosts(state):
        for gift in spec.get("included_gears") or []:
            name = gift.get("name") or ""
            child = sensors_by_name.get(name)
            if child:
                if (host.id, child["name"]) in have_sensors:
                    continue
                extra_sensors.append(
                    GearInstall(
                        gear_id=child["id"],
                        parent_id=host.id,
                        included=True,
                        rating=int(gift.get("rating") or 1),
                    )
                )
                have_sensors.add((host.id, child["name"]))
                continue
            child = gear_by_name.get(name)
            if not child or (host.id, child["name"]) in have_gear:
                continue
            extra_gear.append(
                GearInstall(
                    gear_id=child["id"],
                    parent_id=host.id,
                    included=True,
                    rating=int(gift.get("rating") or 1),
                )
            )
            have_gear.add((host.id, child["name"]))
    if extra_sensors:
        state.sensors = list(state.sensors or []) + extra_sensors
    if extra_gear:
        state.gear = list(state.gear or []) + extra_gear

    have_mods = {(row.parent_id, (mods.get(row.mod_id) or {}).get("name")) for row in state.vehicle_mods or []}
    extra_mods: list[VehicleModInstall] = []
    for host, spec in _iter_vehicle_hosts(state):
        for name in spec.get("included_mods") or []:
            child = mods_by_name.get(name)
            if not child or (host.id, child["name"]) in have_mods:
                continue
            extra_mods.append(VehicleModInstall(mod_id=child["id"], parent_id=host.id, included=True))
            have_mods.add((host.id, child["name"]))
    if extra_mods:
        state.vehicle_mods = list(state.vehicle_mods or []) + extra_mods

    have_mounts = {
        (row.parent_id, row.size_id, row.visibility_id, row.flexibility_id, row.control_id)
        for row in state.weapon_mounts or []
    }
    extra_mounts: list[WeaponMountInstall] = []
    for host, spec in _iter_vehicle_hosts(state):
        source = str(spec.get("source") or "")
        for gift in spec.get("included_weaponmounts") or []:
            size = _find_mount_part(gift.get("size") or "", "Size", source)
            vis = _find_mount_part(gift.get("visibility") or "", "Visibility", source)
            flex = _find_mount_part(gift.get("flexibility") or "", "Flexibility", source)
            ctrl = _find_mount_part(gift.get("control") or "", "Control", source)
            if not size:
                continue
            key = (
                host.id,
                size["id"],
                vis["id"] if vis else "",
                flex["id"] if flex else "",
                ctrl["id"] if ctrl else "",
            )
            if key in have_mounts:
                continue
            extra_mounts.append(
                WeaponMountInstall(
                    parent_id=host.id,
                    size_id=size["id"],
                    visibility_id=vis["id"] if vis else "",
                    flexibility_id=flex["id"] if flex else "",
                    control_id=ctrl["id"] if ctrl else "",
                    included=True,
                    allowedweapons=gift.get("allowedweapons") or "",
                )
            )
            have_mounts.add(key)
    if extra_mounts:
        state.weapon_mounts = list(state.weapon_mounts or []) + extra_mounts


def _resolve_vehicle_mods(
    state: CharacterState,
    drones: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int, list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    specs = {item["id"]: item for item in catalog().get("vehicle_mods") or []}
    by_drone = {str(row.get("id") or ""): row for row in drones}
    kept: list[VehicleModInstall] = []
    public: list[dict[str, Any]] = []
    nuyen = 0
    for inst in list(state.vehicle_mods or []):
        spec = specs.get(inst.mod_id)
        parent = by_drone.get(inst.parent_id or "")
        if not spec or not parent:
            if spec:
                warnings.append(f"{spec['name']} は車両に装着してください")
            continue
        if not inst.included and not mod_fits_vehicle(spec, parent):
            warnings.append(f"{spec['name']} は {parent['name']} に装着できません")
            continue
        extras = _vehicle_extras(
            parent, parent.get("stats") or {}, int(parent.get("base_nuyen") or parent.get("nuyen") or 0)
        )
        rating = (
            _clamp_vehicle_rating(spec, inst.rating, extras)
            if int(spec.get("maxrating") or 0) > 0 or spec.get("maxrating_expr")
            else 1
        )
        inst.rating = rating
        cost = 0 if inst.included else int(eval_formula(str(spec.get("cost") or "0"), rating, 0, extras))
        slots = int(eval_formula(str(spec.get("slots") or "0"), rating, 0, extras))
        nuyen += cost
        if spec.get("bonus"):
            _apply_vehicle_bonus(parent.setdefault("stats", {}), list(spec.get("bonus") or []), rating)
        parent["nuyen"] = int(parent.get("nuyen") or 0) + cost
        _add_vehicle_slot_use(parent, slots, str(spec.get("category") or ""), bool(inst.included))
        kept.append(inst)
        public.append(
            {
                "id": inst.id,
                "mod_id": spec["id"],
                "name": spec["name"],
                "category": spec.get("category") or "",
                "parent_id": inst.parent_id,
                "included": bool(inst.included),
                "rating": rating,
                "rating_max": int(spec.get("maxrating") or 0),
                "slots": slots,
                "nuyen": cost,
                "avail": spec.get("avail") or "",
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
                "capacity_max": _capacity_value(spec.get("capacity"), rating),
                "capacity_used": 0.0,
                "subsystems": list(spec.get("subsystems") or []),
                "cyberware": [],
            }
        )
    children: dict[str, list[dict[str, Any]]] = {}
    for item in public:
        children.setdefault(str(item.get("parent_id") or ""), []).append(item)
    for row in drones:
        row["mods"] = children.get(str(row.get("id") or "")) or []
    state.vehicle_mods = kept
    return public, nuyen, warnings, errors


def _resolve_weapon_mounts(
    state: CharacterState,
    drones: list[dict[str, Any]],
    weapons: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int, list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    parts = {item["id"]: item for item in catalog().get("weapon_mounts") or []}
    by_drone = {str(row.get("id") or ""): row for row in drones}
    weapons_by_id = {str(row.get("id") or ""): row for row in weapons}
    kept: list[WeaponMountInstall] = []
    public: list[dict[str, Any]] = []
    nuyen = 0
    used_weapons: set[str] = set()
    for inst in list(state.weapon_mounts or []):
        parent = by_drone.get(inst.parent_id or "")
        size = parts.get(inst.size_id)
        if not parent or not size or size.get("category") != "Size":
            if size:
                warnings.append(f"{size['name']} は車両に装着してください")
            continue
        if not inst.included and not vehicle_matches(parent, size.get("required")):
            warnings.append(f"{size['name']} は {parent['name']} に装着できません")
            continue
        defaults = _default_mount_parts(size)
        vis = parts.get(inst.visibility_id) or defaults.get("visibility")
        flex = parts.get(inst.flexibility_id) or defaults.get("flexibility")
        ctrl = parts.get(inst.control_id) or defaults.get("control")
        inst.visibility_id = str((vis or {}).get("id") or "")
        inst.flexibility_id = str((flex or {}).get("id") or "")
        inst.control_id = str((ctrl or {}).get("id") or "")
        bundle = [part for part in (size, vis, flex, ctrl) if part]
        extras = _vehicle_extras(parent, parent.get("stats") or {}, int(parent.get("base_nuyen") or 0))
        cost = (
            0
            if inst.included
            else sum(int(eval_formula(str(part.get("cost") or "0"), 1, 0, extras)) for part in bundle)
        )
        slots = sum(int(eval_formula(str(part.get("slots") or "0"), 1, 0, extras)) for part in bundle)
        nuyen += cost
        parent["nuyen"] = int(parent.get("nuyen") or 0) + cost
        _add_vehicle_slot_use(parent, slots, "Weapons", bool(inst.included))
        weapon = weapons_by_id.get(inst.weapon_install_id or "")
        if inst.weapon_install_id and not weapon:
            warnings.append(f"{parent['name']} の武器マウントに武器がありません")
            inst.weapon_install_id = None
        elif weapon and weapon["id"] in used_weapons:
            warnings.append(f"{weapon['name']} は既に搭載されています")
            weapon = None
            inst.weapon_install_id = None
        elif weapon:
            allowed = (inst.allowedweapons or "").strip()
            if allowed and weapon["name"] not in {part.strip() for part in allowed.split(",") if part.strip()}:
                warnings.append(f"{weapon['name']} は {parent['name']} のマウントに搭載できません")
                weapon = None
                inst.weapon_install_id = None
            else:
                used_weapons.add(weapon["id"])
                weapon["mounted_on"] = parent["id"]
                weapon["mounted_label"] = parent["name"]
        kept.append(inst)
        public.append(
            {
                "id": inst.id,
                "parent_id": inst.parent_id,
                "size_id": inst.size_id,
                "visibility_id": inst.visibility_id,
                "flexibility_id": inst.flexibility_id,
                "control_id": inst.control_id,
                "included": bool(inst.included),
                "name": size["name"],
                "label": " / ".join(part["name"] for part in bundle),
                "slots": slots,
                "nuyen": cost,
                "weapon_install_id": inst.weapon_install_id,
                "weapon_name": weapon["name"] if weapon else "",
                "allowedweapons": inst.allowedweapons or "",
                "source": size.get("source") or "",
                "page": size.get("page") or "",
            }
        )
    children: dict[str, list[dict[str, Any]]] = {}
    for item in public:
        children.setdefault(str(item.get("parent_id") or ""), []).append(item)
    for row in drones:
        row["weapon_mounts"] = children.get(str(row.get("id") or "")) or []
    errors.extend(_finalize_vehicle_slots(drones))
    state.weapon_mounts = kept
    return public, nuyen, warnings, errors


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
        row["handling"] = _format_vehicle_stat(str(row.get("handling") or ""), int(stats.get("handling") or 0))
        row["speed"] = str(stats.get("speed") or row.get("speed") or "")
        row["accel"] = str(stats.get("accel") or row.get("accel") or "")
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
