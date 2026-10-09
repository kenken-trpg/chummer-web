"""Physical module pools and device-scoped effects (DT pp.64–66, KC p.76)."""

from __future__ import annotations

from typing import Any

from ...models import CharacterState
from ...notices import Notice, notice, term

ADD_MODULE = "d6802ad9-5dca-434a-bc92-bf8a17a8c5dc"
DECK_BUILDER = "d85c6437-7611-47d3-b4c7-4e581e5349a4"
COPROCESSOR = "8706c98d-b53b-4a29-b21b-a921030ae801"


def resolve_deck_modules(
    state: CharacterState,
    decks: list[dict[str, Any]],
    devices: list[dict[str, Any]],
    gear: list[dict[str, Any]],
) -> list[Notice]:
    warnings: list[Notice] = []
    by_id = {str(row["id"]): row for row in gear}
    hosts = {str(row["id"]): row for row in devices}
    deck_ids = {str(row["id"]) for row in decks}
    builder = state.deck_builder_deck_id
    if DECK_BUILDER in state.quality_ids and not builder and len(decks) == 1:
        builder = str(decks[0]["id"])
    if DECK_BUILDER in state.quality_ids and builder not in deck_ids:
        warnings.append(notice("engine.gear.deckBuilderTarget"))
    pools: dict[tuple[str, str], list[dict[str, Any]]] = {}
    mods = [r for r in gear if r.get("gear_id") == ADD_MODULE and r.get("modification_valid", True)]
    for host in devices:
        hid = str(host["id"])
        host["module_used"] = 0
        host["module_max"] = (1 + int(DECK_BUILDER in state.quality_ids and hid == builder)) if hid in deck_ids else 0
        host["hardwired_module_used"] = 0
        host["hardwired_module_max"] = int(sum(r.get("parent_id") == hid for r in mods) == 1)
        host["module_initiative_dice"] = 0
    for row in gear:
        if row.get("category") != "Cyberdeck Modules":
            continue
        parent = str(row.get("parent_id") or "")
        method = "normal" if parent in deck_ids else ""
        host_id = parent if method else ""
        mod = by_id.get(parent)
        if mod and mod.get("gear_id") == ADD_MODULE and str(mod.get("parent_id")) in hosts:
            method, host_id = "hardwired", str(mod["parent_id"])
        row.update(
            module_host_id=host_id or None,
            module_method=method,
            module_valid=False,
            module_reason="uninstalled" if not parent else "invalidHost",
            module_effect_supported=row["gear_id"] == COPROCESSOR,
        )
        if not method:
            # Containers hold spare modules; invalid chains never grant an effect.
            if parent and (not mod or mod.get("category") in ("Electronic Modification", "Cyberdeck Modules")):
                warnings.append(notice("engine.gear.moduleInvalid", name=term(str(row["name"]))))
            continue
        pools.setdefault((host_id, method), []).append(row)
    for (hid, method), rows in pools.items():
        host = hosts[hid]
        prefix = "hardwired_module" if method == "hardwired" else "module"
        used = sum(int(r.get("qty") or 1) for r in rows)
        maximum = int(host[f"{prefix}_max"])
        host[f"{prefix}_used"] = used
        valid = used <= maximum and all(
            by_id.get(str(r.get("parent_id")), {}).get("modification_valid", True) for r in rows
        )
        if not valid:
            warnings.append(
                notice("engine.gear.modulesOver", name=term(str(host["name"])), pool=method, used=used, max=maximum)
            )
        for row in rows:
            row["module_valid"] = valid
            row["module_reason"] = "" if valid else "overLimit"
            if valid and row.get("equipped", True) and row["gear_id"] == COPROCESSOR:
                # Identical modules do not stack their same initiative effect.
                host["module_initiative_dice"] = 1
    return warnings
