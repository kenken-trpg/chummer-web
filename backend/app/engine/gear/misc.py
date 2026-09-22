"""Miscellaneous gear resolution: the catch-all ``gear`` list that hangs off
commlinks, vehicles, weapons or other gear. Where a row may go lives in
``misc_hosts``; this owns capacity accounting and the ``_ensure_misc_gear`` / ``_resolve_misc_gear`` pair that
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
from ...rules import current_rules
from ..selects import gear_extra_options, gear_extra_skill_kind
from ._common import (
    _cascade_optics,
    _clamp_rating,
    _device_rating_of,
    _program_label,
    armor_capacity_of,
    chosen_cost,
)
from .ammo import _apply_loaded_ammo, _pick_loaded_ammo, ammo_fits_weapon
from .misc_hosts import (
    _misc_child_fits,
    _misc_external_hosts,
    _misc_slot_stats,
)

#: the most of one gear item a row holds (a box of 2,000 datachips is 200 lots)
MAX_QTY = 999


def _held_multiplier(inst: GearInstall, by_id: dict[str, GearInstall], specs: dict[str, dict[str, Any]]) -> int:
    """How many of each gear ancestor there are, multiplied up the chain."""
    out = 1
    seen: set[str] = set()
    parent = by_id.get(inst.parent_id or "")
    while parent is not None and parent.id not in seen:
        seen.add(parent.id)
        per_lot = max(1, int((specs.get(parent.gear_id) or {}).get("costfor") or 0))
        out *= max(1, int(parent.qty or 1)) * per_lot
        parent = by_id.get(parent.parent_id or "")
    return out


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
                # what the parent's entry brings (a Survival Kit's Matches)
                # is there whatever its category says
                fits = bool(inst.included) or _misc_child_fits(parent_spec, spec)
                host_name = str(parent_spec.get("name") or "")
            elif host:
                kind, host_spec = host
                if kind == "weapon":
                    fits = ammo_fits_weapon(spec, host_spec)
                elif kind == "vehicle":
                    # a vehicle is a container: a medkit or a camera rides in
                    # it as it is. Only what plugs into a host of its own
                    # (`requireparent`) has to match the interior categories.
                    fits = bool(inst.included) or not spec.get("requireparent") or _misc_child_fits(host_spec, spec)
                elif kind == "ware":
                    fits = bool(inst.included) or (spec.get("category") or "") in host_spec["allow_gear"]
                elif kind == "armor":
                    # armor carries gear that says what capacity it takes
                    # there (`<armorcapacity>`: a Holster, a Medkit, Trodes)
                    fits = bool(inst.included) or bool(spec.get("armor_capacity"))
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
        qty = max(1, min(MAX_QTY, int(inst.qty or 1)))
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
        picked = chosen_cost(spec, inst.cost)
        inst.cost = picked
        if (spec.get("category") or "") != "Custom":
            inst.name = None
        unit = 0 if inst.included else picked if picked is not None else int(eval_formula(cost_expr, rating, 0, extras))
        unit_costs[inst.id] = unit
        # Chummer's `Gear.TotalCost`: what is inside a gear item is bought
        # once for each of it — three gas grenades, three loads of CS/Tear
        # Gas — counting single items, not the lots a price is quoted for
        cost = unit * qty * _held_multiplier(inst, by_id, specs)
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
                "label": inst.name or _program_label(spec, extra),
                "custom_name": inst.name or "",
                "cost_range": spec.get("cost_range"),
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
                "extra_skill_kind": gear_extra_skill_kind(spec),
                "nuyen": cost,
                "capacity_cost": cap_cost,
                "capacity_used": 0.0,
                "capacity_max": cap_max,
                "armor_capacity": armor_capacity_of(spec, inst, rating),
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
        if current_rules().enforce_capacity and cap_max > 0 and float(item["capacity_used"]) > cap_max + 1e-9:
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
        # before the loaded round changes them (the FVTT export's base values)
        for key in ("damage", "ap", "mode"):
            row[f"{key}_noammo"] = row.get(key)
        loaded = _pick_loaded_ammo(kids, str(row.get("loaded_ammo_id") or "") or None)
        if loaded:
            loaded["loaded"] = True
            row["loaded_ammo_id"] = loaded["id"]
            _apply_loaded_ammo(row, loaded)
        else:
            row["loaded_ammo_id"] = ""
    state.gear = kept
    return public, nuyen, warnings, errors, bonus_sources
