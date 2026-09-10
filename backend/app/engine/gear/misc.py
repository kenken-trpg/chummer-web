"""Miscellaneous gear resolution: the catch-all ``gear`` list that hangs off
commlinks, vehicles, weapons or other gear. Owns host discovery
(``_misc_external_hosts``), the parent/child fit rules, capacity accounting
and the ``_ensure_misc_gear`` / ``_resolve_misc_gear`` pair that
``resolve_gear`` drives.

Imports only ``catalog`` / ``eval_formula`` / already-extracted engine modules
/ models — never back into ``app.engine``.
"""

from __future__ import annotations

from typing import Any

from ...data_loader import DRUG_CATEGORIES, catalog, drug_effect_summary, eval_formula, parse_capacity
from ...improvements import substitute_rating
from ...improvements.effect_rows import GrantGearRow
from ...models import CharacterState, GearInstall
from ...notices import Notice, notice, term, ui
from ..lookups import _item_by_id
from ..selects import gear_extra_options
from ._common import (
    _capacity_value,
    _cascade_optics,
    _clamp_rating,
    _device_rating_of,
    _program_label,
)
from .ammo import _apply_loaded_ammo, _pick_loaded_ammo, ammo_fits_weapon
from .vehicles import _iter_vehicle_hosts

VEHICLE_INTERIOR_CATEGORIES = [
    "Commlink Accessories",
    "Electronics Accessories",
    "Communications and Countermeasures",
]


def _vehicle_interior_parent_spec(spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": spec.get("name") or "",
        "category": "Commlinks",
        "addoncategories": list(VEHICLE_INTERIOR_CATEGORIES),
    }


def _commlink_accessory_parent_spec(spec: dict[str, Any]) -> dict[str, Any]:
    addons = ["Commlink Accessories"]
    if spec.get("category") == "PI-Tac":
        addons.append("PI-Tac Programs")
    return {
        "name": spec.get("name") or "",
        "category": "Commlinks",
        "addoncategories": addons,
    }


def _misc_external_hosts(state: CharacterState) -> dict[str, tuple[str, dict[str, Any]]]:
    hosts: dict[str, tuple[str, dict[str, Any]]] = {}
    for link_inst in list(state.commlinks or []):
        spec = _item_by_id("commlinks", link_inst.gear_id)
        if spec:
            hosts[link_inst.id] = ("commlink", _commlink_accessory_parent_spec(spec))
    for veh_inst, spec in _iter_vehicle_hosts(state):
        hosts[veh_inst.id] = ("vehicle", _vehicle_interior_parent_spec(spec))
    for weapon_inst in list(state.weapons or []):
        spec = _item_by_id("weapons", weapon_inst.weapon_id)
        if spec:
            hosts[weapon_inst.id] = (
                "weapon",
                {
                    "name": spec.get("name") or "",
                    "category": spec.get("category") or "",
                    "ammo": spec.get("ammo") or "",
                    "weapon_type": spec.get("weapon_type") or "",
                    "type": spec.get("type") or "",
                },
            )
    return hosts


def _misc_child_fits(parent_spec: dict[str, Any], child_spec: dict[str, Any]) -> bool:
    parent_name = parent_spec.get("name") or ""
    parent_cat = parent_spec.get("category") or ""
    child_cat = child_spec.get("category") or ""
    allowed = [c for c in (parent_spec.get("addoncategories") or []) if c and c != "Custom"]
    req_names = [n for n in (child_spec.get("required_names") or []) if n]
    req_cats = [c for c in (child_spec.get("required_categories") or []) if c and c != "Custom"]
    if req_names or req_cats:
        return parent_name in req_names or parent_cat in req_cats
    if allowed:
        return child_cat in allowed
    if child_spec.get("requireparent"):
        return child_cat == parent_cat
    return False


def _misc_slot_stats(spec: dict[str, Any], inst: GearInstall, rating: int) -> tuple[bool, float, float]:
    if inst.capacity_override is not None:
        return True, _capacity_value(inst.capacity_override, rating), 0.0
    if spec.get("plugin"):
        expr = str(spec.get("plugin_capacity") or spec.get("capacity") or "")
        return True, _capacity_value(expr, rating), 0.0
    plugin_expr = str(spec.get("plugin_capacity") or "")
    host_expr = str(spec.get("host_capacity") or spec.get("capacity") or "")
    if plugin_expr:
        return False, 0.0, _capacity_value(host_expr, rating)
    return False, 0.0, 0.0


def _ensure_misc_gear(state: CharacterState) -> list[Notice]:
    warnings: list[Notice] = []
    specs = {item["id"]: item for item in catalog().get("gear") or []}
    by_name = {(item["name"], item.get("category") or ""): item for item in specs.values()}
    external = _misc_external_hosts(state)
    items = _cascade_optics(list(state.gear or []), set(external))
    kept: list[GearInstall] = []
    for inst in items:
        spec = specs.get(inst.gear_id)
        if not spec:
            continue
        if spec.get("requireparent") and not inst.parent_id:
            warnings.append(notice("engine.gear.needsHost", name=term(str(spec["name"]))))
            continue
        if inst.parent_id:
            parent = next((row for row in items if row.id == inst.parent_id), None)
            parent_spec = specs.get(parent.gear_id) if parent else None
            host = external.get(inst.parent_id)
            host_name = ""
            if parent_spec:
                fits = _misc_child_fits(parent_spec, spec)
                host_name = str(parent_spec.get("name") or "")
            elif host:
                kind, host_spec = host
                if kind == "weapon":
                    fits = ammo_fits_weapon(spec, host_spec)
                else:
                    fits = bool(inst.included) or _misc_child_fits(host_spec, spec)
                host_name = str(host_spec.get("name") or "")
            else:
                fits = False
            if not fits:
                warnings.append(
                    notice(
                        "engine.gear.doesNotFit",
                        name=term(str(spec["name"])),
                        host=term(host_name) if host_name else ui("engine.term.host"),
                    )
                )
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
    state.gear = kept + extra
    return warnings


def _granted_gear_installs(
    grants: list[GrantGearRow],
    specs: dict[str, dict[str, Any]],
) -> tuple[list[GearInstall], dict[str, str]]:
    """``<addgear>`` grants as installs, parents first.

    They stay out of ``state.gear``: the quality is what carries them, so they
    come and go with it and nothing in the gear tab can edit or delete them.
    The ids are derived from the row's place in the grant, so a recompute hands
    the client back the same rows. Returns the installs and, per install id,
    the source that granted it.
    """
    by_name = {(item["name"], item.get("category") or ""): item for item in specs.values()}

    def find(name: str, category: str) -> dict[str, Any] | None:
        return by_name.get((name, category)) or next((item for item in specs.values() if item["name"] == name), None)

    out: list[GearInstall] = []
    sources: dict[str, str] = {}
    for index, grant in enumerate(grants or []):
        spec = find(str(grant.get("name") or ""), str(grant.get("category") or ""))
        if not spec:
            continue
        source = str(grant.get("source") or "")
        parent_id = f"granted:{index}"
        sources[parent_id] = source
        out.append(
            GearInstall(
                id=parent_id,
                gear_id=spec["id"],
                rating=max(1, int(grant.get("rating") or 1)),
                included=True,
            )
        )
        for kid_index, kid in enumerate(grant.get("children") or []):
            kid_spec = find(str(kid.get("name") or ""), str(kid.get("category") or ""))
            if not kid_spec:
                continue
            sources[f"{parent_id}:{kid_index}"] = source
            out.append(
                GearInstall(
                    id=f"{parent_id}:{kid_index}",
                    gear_id=kid_spec["id"],
                    parent_id=parent_id,
                    rating=max(1, int(kid.get("rating") or 1)),
                    included=True,
                )
            )
    return out, sources


def _resolve_misc_gear(
    state: CharacterState,
    vehicles: list[dict[str, Any]] | None = None,
    weapons: list[dict[str, Any]] | None = None,
    granted: list[GrantGearRow] | None = None,
) -> tuple[list[dict[str, Any]], int, list[Notice], list[Notice], list[tuple[str, list[dict[str, Any]]]]]:
    warnings = _ensure_misc_gear(state)
    errors: list[Notice] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    specs = {item["id"]: item for item in catalog().get("gear") or []}
    public: list[dict[str, Any]] = []
    kept: list[GearInstall] = []
    nuyen = 0
    # The row names the quality that brought it, so the gear tab can label it
    # and leave its controls out.
    granted_installs, granted_by = _granted_gear_installs(granted or [], specs)
    granted_ids = set(granted_by)
    rows = [*state.gear, *granted_installs]
    by_id = {row.id: row for row in rows}
    unit_costs: dict[str, int] = {}
    # Parents first so children can reference Parent Cost.
    ordered = sorted(rows, key=lambda row: 1 if row.parent_id else 0)
    for inst in ordered:
        spec = specs.get(inst.gear_id)
        if not spec:
            continue
        extra_kind = str(spec.get("extra_kind") or "")
        extra = (inst.extra or "").strip()
        options = gear_extra_options(spec)
        if extra_kind == "skill":
            if extra and extra not in options:
                warnings.append(notice("engine.gear.skillInvalid", name=term(str(spec["name"])), picked=term(extra)))
                extra = ""
            if not extra:
                warnings.append(notice("engine.gear.pickSkill", name=term(str(spec["name"]))))
        elif extra_kind == "group":
            if extra and extra not in options:
                warnings.append(notice("engine.gear.groupInvalid", name=term(str(spec["name"])), picked=term(extra)))
                extra = ""
            if not extra:
                warnings.append(notice("engine.gear.pickGroup", name=term(str(spec["name"]))))
        elif extra_kind == "text" and not extra and inst.id not in granted_ids:
            # A granted row has no editor behind it — asking for a name would
            # be a warning nobody can clear.
            warnings.append(notice("engine.gear.pickExtra", name=term(str(spec["name"]))))
        inst.extra = extra or None
        rating = _clamp_rating(spec, inst.rating)
        inst.rating = rating
        qty = max(1, min(99, int(inst.qty or 1)))
        inst.qty = qty
        cost_expr = str(spec.get("cost") or "0")
        extras: dict[str, int | float] = {}
        if inst.parent_id and "Parent Cost" in cost_expr:
            parent_unit = unit_costs.get(inst.parent_id)
            if parent_unit is None:
                parent = by_id.get(inst.parent_id)
                parent_spec = specs.get(parent.gear_id) if parent else None
                parent_unit = (
                    0
                    if not parent or not parent_spec or parent.included
                    else int(eval_formula(str(parent_spec.get("cost") or "0"), int(parent.rating or 1), 0))
                )
            extras["Parent Cost"] = int(parent_unit)
            extras["ParentCost"] = int(parent_unit)
        unit = 0 if inst.included else int(eval_formula(cost_expr, rating, 0, extras))
        unit_costs[inst.id] = unit
        cost = unit * qty
        nuyen += cost
        plugin, cap_cost, cap_max = _misc_slot_stats(spec, inst, rating)
        nodes = substitute_rating(list(spec.get("bonus") or []), rating)
        if nodes:
            bonus_sources.append((_program_label(spec, extra), nodes))
        is_drug = (spec.get("category") or "") in DRUG_CATEGORIES
        drug_bonus = list(spec.get("drug_bonus") or []) if is_drug else []
        inst.active = bool(inst.active) and (is_drug and bool(drug_bonus))
        if inst.id not in granted_ids:
            kept.append(inst)
        public.append(
            {
                "id": inst.id,
                "gear_id": spec["id"],
                "name": spec["name"],
                "label": _program_label(spec, extra),
                "category": spec.get("category") or "",
                "is_drug": is_drug,
                "active": inst.active,
                "drug_speed": spec.get("drug_speed") or "" if is_drug else "",
                "drug_vectors": list(spec.get("drug_vectors") or []) if is_drug else [],
                "drug_duration": spec.get("drug_duration") or "" if is_drug else "",
                "drug_effect": drug_effect_summary(drug_bonus) if drug_bonus else [],
                "rating": rating,
                "rating_max": int(spec.get("maxrating") or 0),
                "qty": qty,
                "parent_id": inst.parent_id,
                "included": bool(inst.included),
                "granted_by": granted_by.get(inst.id, ""),
                "plugin": plugin,
                "extra": extra,
                "needs_extra": bool(extra_kind),
                "extra_kind": extra_kind,
                "extra_options": options,
                "nuyen": cost,
                "capacity_cost": cap_cost,
                "capacity_used": 0.0,
                "capacity_max": cap_max,
                "addoncategories": list(spec.get("addoncategories") or []),
                "requireparent": bool(spec.get("requireparent")),
                "required_names": list(spec.get("required_names") or []),
                "required_categories": list(spec.get("required_categories") or []),
                "ammo_weapon_types": list(spec.get("ammo_weapon_types") or []),
                "costfor": int(spec.get("costfor") or 0),
                "add_weapon": spec.get("add_weapon") or "",
                "add_weapon_id": spec.get("add_weapon_id") or "",
                "weaponbonus": dict(spec.get("weaponbonus") or {}),
                "loaded": False,
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
            errors.append(
                notice(
                    "engine.gear.capacityOver",
                    name=term(str(item["name"])),
                    used=f"{item['capacity_used']:g}",
                    max=f"{cap_max:g}",
                )
            )
    for row in vehicles or []:
        kids = children.get(str(row.get("id") or "")) or []
        row["gear"] = kids
        extra_cost = sum(int(kid.get("nuyen") or 0) for kid in kids)
        row["nuyen"] = int(row.get("nuyen") or 0) + extra_cost
    for row in weapons or []:
        kids = children.get(str(row.get("id") or "")) or []
        row["ammo_gear"] = kids
        extra_cost = sum(int(kid.get("nuyen") or 0) for kid in kids)
        row["nuyen"] = int(row.get("nuyen") or 0) + extra_cost
        loaded = _pick_loaded_ammo(kids, str(row.get("loaded_ammo_id") or "") or None)
        if loaded:
            loaded["loaded"] = True
            row["loaded_ammo_id"] = loaded["id"]
            _apply_loaded_ammo(row, loaded)
        else:
            row["loaded_ammo_id"] = ""
    state.gear = kept
    return public, nuyen, warnings, errors, bonus_sources
