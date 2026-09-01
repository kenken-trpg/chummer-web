"""Core cyber/bioware resolution: subsystems, the resolved-row builder,
grade clamping and required-'ware warnings.

``resolve_ware`` is the workhorse ``compute`` calls once per kind; the
``ensure_*`` mutators inject forced subsystems and side assignments before
it runs, and the grade / warning helpers validate the picks.

Imports only ``catalog`` / ``eval_formula`` (``..data_loader``),
``substitute_rating`` (``..improvements``), ``_normalize_side``
(``..constants``), already-extracted engine modules and other ``ware/``
submodules / models — never back into ``app.engine``.
"""

from __future__ import annotations

from typing import Any

from ...data_loader import catalog, eval_formula
from ...improvements import substitute_rating
from ...models import CharacterState, CyberwareInstall
from ..constants import _normalize_side
from ..gear import _capacity_value, _device_rating_of
from ..lookups import _grade_by_name, _ware_by_id, _ware_by_name
from ._common import _cascade_orphans
from .limbs import _apply_limb_attributes
from .rating import _clamp_ware_rating, racial_formula_extras, ware_rating_bounds
from .sides import ensure_sides
from .vehicles import _vehicle_mod_hosts


def ensure_subsystems(state: CharacterState) -> CharacterState:
    extra = set(_vehicle_mod_hosts(state))
    state.cyberware = ensure_sides("cyberware", _ensure_kind_subsystems("cyberware", state.cyberware, extra))
    state.bioware = ensure_sides("bioware", _ensure_kind_subsystems("bioware", state.bioware))
    return state


def _ensure_kind_subsystems(
    kind: str,
    items: list[CyberwareInstall],
    extra_parent_ids: set[str] | None = None,
) -> list[CyberwareInstall]:
    items = _cascade_orphans(list(items), extra_parent_ids)
    existing = {(item.parent_id, item.ware_id) for item in items}
    extra: list[CyberwareInstall] = []
    for inst in items:
        if inst.parent_id:
            continue
        ware = _ware_by_id(kind, inst.ware_id)
        if not ware:
            continue
        for name in ware.get("subsystems") or []:
            sub = _ware_by_name(kind, name)
            if not sub or (inst.id, sub["id"]) in existing:
                continue
            extra.append(
                CyberwareInstall(
                    ware_id=sub["id"],
                    rating=_clamp_ware_rating(sub, int(sub.get("minrating") or 1)),
                    grade=ware.get("forcegrade") or inst.grade or "Standard",
                    wireless=inst.wireless,
                    parent_id=inst.id,
                    included=True,
                )
            )
            existing.add((inst.id, sub["id"]))
    return items + extra if extra else items


def resolve_ware(
    kind: str,
    installs: list[CyberwareInstall],
    attrs_spec: dict[str, dict[str, int | float]] | None = None,
) -> list[dict[str, Any]]:
    extras = racial_formula_extras(attrs_spec) if attrs_spec else {}
    resolved: list[dict[str, Any]] = []
    for inst in installs:
        ware = _ware_by_id(kind, inst.ware_id)
        if not ware:
            continue
        lo, hi = ware_rating_bounds(ware, extras)
        rating = max(lo, min(hi, int(inst.rating or lo)))
        grade_name = ware.get("forcegrade") or inst.grade or "Standard"
        grade = _grade_by_name(kind, grade_name)
        slotted = bool(inst.parent_id)
        included = bool(inst.included)
        plugin = bool(ware.get("plugin"))
        add_to_parent = bool(ware.get("addtoparentess")) and slotted and not included
        formula_extras = {**extras, "MinRating": lo}
        ess_base = round(eval_formula(ware.get("ess"), rating, extras=formula_extras) * float(grade.get("ess") or 1), 4)
        ess = 0.0 if included or (slotted and (plugin or add_to_parent)) else ess_base
        cost = (
            0
            if included
            else int(
                round(eval_formula(ware.get("cost"), rating, extras=formula_extras) * float(grade.get("cost") or 1))
            )
        )
        nodes = substitute_rating(ware.get("bonus") or [], rating)
        if inst.wireless:
            nodes = nodes + substitute_rating(ware.get("wirelessbonus") or [], rating)
        resolved.append(
            {
                "id": inst.id,
                "ware_id": ware["id"],
                "name": ware["name"],
                "category": ware["category"],
                "rating": rating,
                "rating_min": lo,
                "rating_max": hi,
                "grade": grade["name"],
                "wireless": bool(inst.wireless),
                "parent_id": inst.parent_id,
                "included": included,
                "plugin": plugin,
                "essence": ess,
                "nuyen": cost,
                "capacity_cost": _capacity_value(ware.get("capacity"), rating) if plugin else 0.0,
                "capacity_used": 0.0,
                "capacity_max": 0.0 if plugin else _capacity_value(ware.get("capacity"), rating),
                "allow_subsystems": list(ware.get("allow_subsystems") or []),
                "limbslot": ware.get("limbslot"),
                "limbslotcount": ware.get("limbslotcount") or "1",
                "selectside": bool(ware.get("selectside")),
                "side": _normalize_side(inst.side),
                "avail": ware.get("avail") or "",
                "source": ware.get("source"),
                "bonus": nodes,
                "ess_to_parent": ess_base if add_to_parent else 0.0,
                "add_weapon": ware.get("add_weapon") or "",
                "add_weapon_id": ware.get("add_weapon_id") or "",
                "device_rating": _device_rating_of(ware, rating),
            }
        )
    children: dict[str, list[dict[str, Any]]] = {}
    for item in resolved:
        if item["parent_id"]:
            children.setdefault(item["parent_id"], []).append(item)
    for item in resolved:
        kids = children.get(item["id"]) or []
        item["capacity_used"] = round(sum(float(kid["capacity_cost"]) for kid in kids), 4)
        extra_ess = sum(float(kid.get("ess_to_parent") or 0) for kid in kids)
        if extra_ess:
            item["essence"] = round(float(item["essence"]) + extra_ess, 4)
    if attrs_spec:
        _apply_limb_attributes(resolved, attrs_spec)
    return resolved


def _first_allowed_grade(kind: str, current: str, banned: set[str]) -> str:
    grades = catalog().get(kind, {}).get("grades") or []
    prefer_adapsin = "(Adapsin)" in (current or "")

    def ok(name: str) -> bool:
        return bool(name) and name != "None" and name not in banned

    for grade in grades:
        name = str(grade.get("name") or "")
        if ok(name) and ("(Adapsin)" in name) == prefer_adapsin:
            return name
    for grade in grades:
        name = str(grade.get("name") or "")
        if ok(name):
            return name
    return "Standard"


def _clamp_ware_grades(
    kind: str,
    items: list[CyberwareInstall],
    disabled_grades: set[str] | None = None,
) -> list[str]:
    warnings: list[str] = []
    quality_banned = set(disabled_grades or ())
    for inst in items:
        ware = _ware_by_id(kind, inst.ware_id)
        if not ware:
            continue
        force = ware.get("forcegrade")
        if force:
            inst.grade = force
            continue
        grade = inst.grade or "Standard"
        banned = set(ware.get("bannedgrades") or []) | quality_banned
        if grade in banned:
            fallback = _first_allowed_grade(kind, grade, banned)
            warnings.append(f"{ware['name']} は {grade} グレードを使えません（{fallback} に変更）")
            inst.grade = fallback
    return warnings


def _installed_ware_names(kind: str, items: list[CyberwareInstall]) -> set[str]:
    names: set[str] = set()
    for inst in items:
        ware = _ware_by_id(kind, inst.ware_id)
        if ware:
            names.add(ware["name"])
    return names


def _required_warnings(
    kind: str,
    items: list[CyberwareInstall],
    names: dict[str, set[str]],
    metatype: str,
    metavariant: str | None,
) -> list[str]:
    warnings: list[str] = []
    have_meta = {metatype}
    if metavariant:
        have_meta.add(metavariant)
    for inst in items:
        ware = _ware_by_id(kind, inst.ware_id)
        if not ware:
            continue
        req = ware.get("required") or {}
        for other in ("bioware", "cyberware"):
            needed = req.get(other) or []
            if needed and not any(name in names.get(other, set()) for name in needed):
                label = needed[0] if len(needed) == 1 else " / ".join(needed)
                warnings.append(f"{ware['name']} には {label} が必要です")
        needed_meta = req.get("metatype") or []
        if needed_meta and not any(name in have_meta for name in needed_meta):
            warnings.append(f"{ware['name']} は {' / '.join(needed_meta)} 専用です")
    return warnings
