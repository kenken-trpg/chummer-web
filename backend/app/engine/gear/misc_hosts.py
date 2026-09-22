"""Where miscellaneous gear can go: every host a ``gear`` row can hang off
(commlinks, decks, vehicles, armor, weapons, ware), the parent/child fit rule,
the capacity a row takes or offers, and what the gear inside ware costs.

Split from ``misc.py`` so the chum5 importer can ask "does this fit there"
without pulling in gear resolution.
"""

from __future__ import annotations

from typing import Any

from ...data_loader import eval_formula
from ...models import CharacterState, GearInstall
from ..lookups import _item_by_id, _ware_by_id
from ._common import _capacity_value, chosen_cost
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
    addons = ["Commlink Accessories", "Electronic Modification"]
    if spec.get("category") == "PI-Tac":
        addons.append("PI-Tac Programs")
    return {
        "name": spec.get("name") or "",
        "category": "Commlinks",
        "addoncategories": addons,
    }


def _matrix_device_parent_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """A cyberdeck or an RCC as a host. It takes the same dongles a commlink
    does, plus the Electronic Modifications of DT p.66 that are soldered into
    a device rather than plugged into one."""
    return {
        "name": spec.get("name") or "",
        "category": "Commlinks",
        "addoncategories": ["Commlink Accessories", "Electronic Modification"],
    }


def _misc_external_hosts(state: CharacterState) -> dict[str, tuple[str, dict[str, Any]]]:
    hosts: dict[str, tuple[str, dict[str, Any]]] = {}
    for link_inst in list(state.commlinks or []):
        spec = _item_by_id("commlinks", link_inst.gear_id)
        if spec:
            hosts[link_inst.id] = ("commlink", _commlink_accessory_parent_spec(spec))
    for kind in ("cyberdecks", "rccs"):
        for inst in list(getattr(state, kind) or []):
            spec = _item_by_id(kind, inst.gear_id)
            if spec:
                hosts[inst.id] = ("commlink", _matrix_device_parent_spec(spec))
    for veh_inst, spec in _iter_vehicle_hosts(state):
        hosts[veh_inst.id] = ("vehicle", _vehicle_interior_parent_spec(spec))
    for armor_inst in list(state.armor or []):
        spec = _item_by_id("armor", armor_inst.armor_id)
        if spec:
            hosts[armor_inst.id] = ("armor", {"name": spec.get("name") or "", "category": "Armor"})
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
    hosts.update(_ware_hosts(state))
    return hosts


def _ware_hosts(state: CharacterState) -> dict[str, tuple[str, dict[str, Any]]]:
    """Cyber- and bioware that holds gear (`<allowgear>`): a Chemical Gland's
    chemical, an Auto Injector's drug, a grenade cyberfinger's grenade."""
    hosts: dict[str, tuple[str, dict[str, Any]]] = {}
    for kind in ("cyberware", "bioware"):
        for inst in list(getattr(state, kind) or []):
            spec = _ware_by_id(kind, inst.ware_id)
            if spec and spec.get("allow_gear"):
                hosts[inst.id] = (
                    "ware",
                    {"name": spec.get("name") or "", "category": "", "allow_gear": list(spec["allow_gear"])},
                )
    return hosts


def ware_gear_costs(state: CharacterState) -> dict[str, int]:
    """What the gear inside each piece of ware cost, by the ware's install id —
    Chummer's `Gear Cost` in a ware price."""
    hosts = _ware_hosts(state)
    out: dict[str, int] = {}
    for inst in state.gear or []:
        if not inst.parent_id or inst.parent_id not in hosts or inst.included:
            continue
        spec = _item_by_id("gear", inst.gear_id)
        if not spec:
            continue
        picked = chosen_cost(spec, inst.cost)
        unit = (
            picked if picked is not None else int(eval_formula(str(spec.get("cost") or "0"), int(inst.rating or 1), 0))
        )
        out[inst.parent_id] = out.get(inst.parent_id, 0) + unit * max(1, int(inst.qty or 1))
    return out


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
