"""Vehicle-hosted cyberware.

Cyberware can be installed into a vehicle mod's subsystem slots rather than
the character's body. These helpers validate those installs
(``_drop_invalid_vehicle_ware``), zero the essence they would otherwise
charge the character (``_zero_vehicle_hosted_essence``), and attach the
resolved rows onto their host mod (``_attach_ware_to_vehicle_mods``).

Imports only ``catalog`` (``..data_loader``), ``_iter_vehicle_hosts`` /
``mod_fits_vehicle`` (``.gear``), ``_ware_by_id`` (``.lookups``),
``_cascade_orphans`` / ``_public_installed`` (``._common``) and models —
never back into ``app.engine``.
"""

from __future__ import annotations

from typing import Any

from ...data_loader import catalog
from ...models import CharacterState, CyberwareInstall
from ..gear import _iter_vehicle_hosts, mod_fits_vehicle
from ..lookups import _ware_by_id
from ._common import _cascade_orphans, _public_installed


def _vehicle_mod_hosts(state: CharacterState) -> dict[str, dict[str, Any]]:
    specs = {item["id"]: item for item in catalog().get("vehicle_mods") or []}
    parents = {inst.id: spec for inst, spec in _iter_vehicle_hosts(state)}
    hosts: dict[str, dict[str, Any]] = {}
    for inst in state.vehicle_mods or []:
        spec = specs.get(inst.mod_id)
        parent = parents.get(inst.parent_id or "")
        if not spec or not spec.get("subsystems") or not parent:
            continue
        if not inst.included and not mod_fits_vehicle(spec, parent):
            continue
        hosts[inst.id] = spec
    return hosts


def _ware_fits_vehicle_mod(ware: dict[str, Any], spec: dict[str, Any]) -> bool:
    if ware.get("category") not in (spec.get("subsystems") or []):
        return False
    if not (ware.get("plugin") or ware.get("requireparent")):
        return False
    names = ware.get("required_parent_names") or []
    if not names:
        return True
    parent_name = spec.get("name") or ""
    return any(name in parent_name for name in names)


def _drop_invalid_vehicle_ware(state: CharacterState) -> list[str]:
    hosts = _vehicle_mod_hosts(state)
    cyber_ids = {item.id for item in state.cyberware}
    warnings: list[str] = []
    kept: list[CyberwareInstall] = []
    for inst in state.cyberware:
        parent_id = inst.parent_id
        if not parent_id or parent_id in cyber_ids:
            kept.append(inst)
            continue
        spec = hosts.get(parent_id)
        ware = _ware_by_id("cyberware", inst.ware_id)
        if not spec or not ware:
            continue
        if not _ware_fits_vehicle_mod(ware, spec):
            warnings.append(f"{ware['name']} は {spec['name']} に装着できません")
            continue
        kept.append(inst)
    state.cyberware = _cascade_orphans(kept, set(hosts))
    return warnings


def _vehicle_hosted_ware_ids(resolved: list[dict[str, Any]], vehicle_hosts: set[str]) -> set[str]:
    hosted: set[str] = set()
    by_id = {str(item.get("id") or ""): item for item in resolved}

    def is_hosted(item: dict[str, Any]) -> bool:
        parent_id = item.get("parent_id") or ""
        seen: set[str] = set()
        while parent_id:
            if parent_id in vehicle_hosts:
                return True
            if parent_id in seen:
                return False
            seen.add(parent_id)
            parent = by_id.get(parent_id)
            if not parent:
                return False
            parent_id = parent.get("parent_id") or ""
        return False

    for item in resolved:
        if is_hosted(item):
            hosted.add(str(item.get("id") or ""))
    return hosted


def _zero_vehicle_hosted_essence(resolved: list[dict[str, Any]], vehicle_hosts: set[str]) -> None:
    hosted = _vehicle_hosted_ware_ids(resolved, vehicle_hosts)
    for item in resolved:
        if item.get("id") in hosted:
            item["essence"] = 0.0
            item["ess_to_parent"] = 0.0


def _attach_ware_to_vehicle_mods(mods: list[dict[str, Any]], ware: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    by_id = {str(mod.get("id") or ""): mod for mod in mods}
    for mod in mods:
        mod["cyberware"] = []
        mod["capacity_used"] = 0.0
    for item in ware:
        parent = by_id.get(str(item.get("parent_id") or ""))
        if not parent:
            continue
        parent["cyberware"].append(_public_installed(item))
        parent["capacity_used"] = round(
            float(parent.get("capacity_used") or 0) + float(item.get("capacity_cost") or 0),
            4,
        )
    for mod in mods:
        cap_max = float(mod.get("capacity_max") or 0)
        used = float(mod.get("capacity_used") or 0)
        if cap_max > 0 and used > cap_max + 1e-9:
            errors.append(f"{mod['name']} の容量超過（{used:g}/{cap_max:g}）")
    return errors
