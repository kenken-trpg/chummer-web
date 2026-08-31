"""Sensors and sensor-housing plugins.

A sensor array (standalone, on a commlink, or mounted on a drone/vehicle host)
carries individual sensor functions up to its capacity. ``_plugin_capacity_expr``
picks the right capacity expression for where a plugin sits; ``_resolve_sensors``
prices the tree, collects ``<bonus>`` nodes, and checks capacity.
"""

from __future__ import annotations

from typing import Any

from ...data_loader import catalog, eval_formula, parse_capacity
from ...improvements import substitute_rating
from ...models import CharacterState, GearInstall
from ._common import _capacity_value, _cascade_optics, _clamp_rating, _device_rating_of


def _ensure_sensors(state: CharacterState) -> list[str]:
    warnings: list[str] = []
    specs = {item["id"]: item for item in catalog().get("sensors") or []}
    by_name = {(item["name"], item.get("category") or ""): item for item in specs.values()}
    drone_ids = {row.id for row in state.drones or []}
    vehicle_ids = {row.id for row in state.vehicles or []}
    host_ids = drone_ids | vehicle_ids
    items = _cascade_optics(list(state.sensors or []), host_ids)
    kept: list[GearInstall] = []
    for inst in items:
        spec = specs.get(inst.gear_id)
        if not spec:
            continue
        if spec.get("requireparent") and not inst.parent_id:
            warnings.append(f"{spec['name']} は本体に装着してください")
            continue
        if inst.parent_id:
            parent = next((row for row in items if row.id == inst.parent_id), None)
            if parent:
                parent_spec = specs.get(parent.gear_id) if parent else None
                allowed = set(parent_spec.get("addoncategories") or []) if parent_spec else set()
                if allowed and spec.get("category") not in allowed:
                    warnings.append(
                        f"{spec['name']} は {parent_spec.get('name') if parent_spec else '本体'} に装着できません"
                    )
                    continue
            elif inst.parent_id in host_ids:
                if spec.get("category") not in {"Sensors", "Sensor Housings"}:
                    warnings.append(f"{spec['name']} は車両に装着できません")
                    continue
            else:
                warnings.append(f"{spec['name']} は本体に装着してください")
                continue
        kept.append(inst)
    have = {(row.parent_id, (specs.get(row.gear_id) or {}).get("name")) for row in kept}
    extra: list[GearInstall] = []
    for inst in kept:
        if inst.parent_id:
            continue
        spec = specs.get(inst.gear_id) or {}
        for gift in spec.get("included") or []:
            child = by_name.get((gift.get("name"), gift.get("category") or "")) or next(
                (item for item in specs.values() if item["name"] == gift.get("name")),
                None,
            )
            if not child or (inst.id, child["name"]) in have:
                continue
            override = str(gift.get("capacity") or "").strip()
            _plugin, expr = parse_capacity(override) if override else (False, "")
            extra.append(
                GearInstall(
                    gear_id=child["id"],
                    parent_id=inst.id,
                    included=True,
                    rating=int(gift.get("rating") or 1),
                    capacity_override=expr if override else None,
                )
            )
            have.add((inst.id, child["name"]))
    state.sensors = kept + extra
    return warnings


def _plugin_capacity_expr(
    spec: dict[str, Any], inst: GearInstall, host_ids: set[str] | None = None
) -> tuple[bool, str, float]:
    rating = int(inst.rating or 1)
    if inst.capacity_override is not None:
        return True, str(inst.capacity_override), _capacity_value(inst.capacity_override, rating)
    if inst.parent_id and inst.parent_id in (host_ids or set()):
        expr = str(spec.get("host_capacity") or spec.get("capacity") or "")
        return False, expr, _capacity_value(expr, rating)
    if inst.parent_id:
        expr = str(spec.get("plugin_capacity") or spec.get("capacity") or "")
        return True, expr, _capacity_value(expr, rating)
    if spec.get("plugin"):
        expr = str(spec.get("capacity") or "")
        return True, expr, _capacity_value(expr, rating)
    expr = str(spec.get("host_capacity") or spec.get("capacity") or "")
    return False, expr, _capacity_value(expr, rating)


def _resolve_sensors(
    state: CharacterState,
) -> tuple[list[dict[str, Any]], int, list[str], list[str], list[tuple[str, list[dict[str, Any]]]]]:
    warnings = _ensure_sensors(state)
    errors: list[str] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    specs = {item["id"]: item for item in catalog().get("sensors") or []}
    public: list[dict[str, Any]] = []
    kept: list[GearInstall] = []
    nuyen = 0
    for inst in state.sensors:
        spec = specs.get(inst.gear_id)
        if not spec:
            continue
        rating = _clamp_rating(spec, inst.rating)
        inst.rating = rating
        cost = 0 if inst.included else int(eval_formula(str(spec.get("cost") or "0"), rating, 0))
        nuyen += cost
        plugin, _expr, cap_value = _plugin_capacity_expr(
            spec,
            inst,
            {row.id for row in list(state.drones or []) + list(state.vehicles or [])},
        )
        cap_cost = cap_value if plugin else 0.0
        cap_max = 0.0 if plugin else cap_value
        nodes = substitute_rating(list(spec.get("bonus") or []), rating)
        if nodes:
            bonus_sources.append((spec["name"], nodes))
        kept.append(inst)
        public.append(
            {
                "id": inst.id,
                "gear_id": spec["id"],
                "name": spec["name"],
                "category": spec.get("category") or "",
                "rating": rating,
                "rating_max": int(spec.get("maxrating") or 0),
                "parent_id": inst.parent_id,
                "included": bool(inst.included),
                "plugin": plugin,
                "nuyen": cost,
                "capacity_cost": cap_cost,
                "capacity_used": 0.0,
                "capacity_max": cap_max,
                "addoncategories": list(spec.get("addoncategories") or []),
                "requireparent": bool(spec.get("requireparent")),
                "device_rating": _device_rating_of(spec, rating),
                "avail": spec.get("avail") or "",
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
    children: dict[str, list[dict[str, Any]]] = {}
    for item in public:
        if item["parent_id"]:
            children.setdefault(item["parent_id"], []).append(item)
    for item in public:
        kids = children.get(item["id"]) or []
        used = round(sum(float(kid.get("capacity_cost") or 0) for kid in kids), 4)
        item["capacity_used"] = int(used) if used == int(used) else used
        cap_max = float(item.get("capacity_max") or 0)
        if cap_max == int(cap_max):
            item["capacity_max"] = int(cap_max)
        if cap_max > 0 and float(item["capacity_used"]) > cap_max + 1e-9:
            errors.append(f"{item['name']} の容量超過（{item['capacity_used']:g}/{cap_max:g}）")
    state.sensors = kept
    return public, nuyen, warnings, errors, bonus_sources
