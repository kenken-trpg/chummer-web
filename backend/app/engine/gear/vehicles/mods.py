"""Vehicle mods and weapon mounts installed on a vehicle or drone."""

from __future__ import annotations

from typing import Any

from ....data_loader import catalog, eval_formula
from ....models import CharacterState, VehicleModInstall, WeaponMountInstall
from ....notices import Notice, notice, term
from .._common import (
    _capacity_value,
    _default_mount_parts,
)
from .slots import _add_vehicle_slot_use, _finalize_vehicle_slots
from .stats import _apply_vehicle_bonus, _clamp_vehicle_rating, _vehicle_extras, mod_fits_vehicle, vehicle_matches


def _resolve_vehicle_mods(
    state: CharacterState,
    drones: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int, list[Notice], list[Notice]]:
    warnings: list[Notice] = []
    errors: list[Notice] = []
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
                warnings.append(notice("engine.gear.mountOnVehicle", name=term(str(spec["name"]))))
            continue
        if not inst.included and not mod_fits_vehicle(spec, parent):
            warnings.append(
                notice("engine.gear.doesNotFit", name=term(str(spec["name"])), host=term(str(parent["name"])))
            )
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
        _add_vehicle_slot_use(
            parent,
            slots,
            str(spec.get("category") or ""),
            bool(inst.included),
            downgrade=bool(spec.get("downgrade")),
        )
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
) -> tuple[list[dict[str, Any]], int, list[Notice], list[Notice]]:
    warnings: list[Notice] = []
    errors: list[Notice] = []
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
                warnings.append(notice("engine.gear.mountOnVehicle", name=term(str(size["name"]))))
            continue
        if not inst.included and not vehicle_matches(parent, size.get("required")):
            warnings.append(
                notice("engine.gear.doesNotFit", name=term(str(size["name"])), host=term(str(parent["name"])))
            )
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
            warnings.append(notice("engine.gear.weaponMountEmpty", name=term(str(parent["name"]))))
            inst.weapon_install_id = None
        elif weapon and weapon["id"] in used_weapons:
            warnings.append(notice("engine.gear.weaponAlreadyMounted", name=term(str(weapon["name"]))))
            weapon = None
            inst.weapon_install_id = None
        elif weapon:
            allowed = (inst.allowedweapons or "").strip()
            if allowed and weapon["name"] not in {part.strip() for part in allowed.split(",") if part.strip()}:
                warnings.append(
                    notice(
                        "engine.gear.weaponNotOnMount",
                        name=term(str(weapon["name"])),
                        host=term(str(parent["name"])),
                    )
                )
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
