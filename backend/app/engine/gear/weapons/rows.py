"""The weapon row the UI reads, and the weapons a character never bought.

A `.chum5` character carries weapons it was granted rather than purchased: a
cyberspur is a `cyberware` install that *is* a weapon, a grenade in `gear`
becomes one when thrown, a drone's mounted gun belongs to the drone. They all
have to end up in the same shaped row as a bought weapon, and a cyberlimb's
weapon uses the *limb's* STR/AGI rather than the body's — which is what the
`_ware_weapon_attr_values` half of this module is for.
"""

from __future__ import annotations

from typing import Any

from ....improvements import EffectsDict, empty_effects
from ....models import CharacterState
from ...formulas import _eval_attr_stat
from ...lookups import _item_by_id
from .._common import _leading_vehicle_stat, _limb_attr_effect


def _public_weapon(
    spec: dict[str, Any],
    *,
    inst_id: str,
    qty: int,
    nuyen: int,
    loaded_ammo_id: str | None = None,
    from_gear: bool = False,
    source_gear_id: str | None = None,
    from_ware: bool = False,
    source_ware_id: str | None = None,
) -> dict[str, Any]:
    return {
        "id": inst_id,
        "weapon_id": spec["id"],
        "name": spec["name"],
        "category": spec.get("category") or "",
        "type": spec.get("type") or "",
        "weapon_type": spec.get("weapon_type") or "",
        "accuracy": spec.get("accuracy") or "",
        "reach": spec.get("reach") or "",
        "damage": spec.get("damage") or "",
        "ap": spec.get("ap") or "",
        "mode": spec.get("mode") or "",
        "rc": spec.get("rc") or "",
        "ammo": spec.get("ammo") or "",
        "conceal": spec.get("conceal") or "",
        "range": spec.get("range") or "",
        "alt_range": spec.get("alt_range") or "",
        "mounts": list(spec.get("mounts") or []),
        "qty": qty,
        "nuyen": nuyen,
        "accessories": [],
        "ammo_gear": [],
        "loaded_ammo_id": loaded_ammo_id or "",
        "from_gear": from_gear,
        "source_gear_id": source_gear_id or "",
        "from_ware": from_ware,
        "source_ware_id": source_ware_id or "",
        "useskill": spec.get("useskill") or "",
        "avail": spec.get("avail") or "",
        "source": spec.get("source") or "",
        "page": spec.get("page") or "",
        "limb_str": None,
        "limb_agi": None,
    }


def _append_gear_weapons(weapons: list[dict[str, Any]], gear_items: list[dict[str, Any]]) -> None:
    taken = {str(row.get("id") or "") for row in weapons}
    for item in gear_items:
        if item.get("parent_id"):
            continue
        spec_id = str(item.get("add_weapon_id") or "")
        if not spec_id:
            continue
        spec = _item_by_id("weapons", spec_id)
        if not spec:
            continue
        gear_id = str(item.get("id") or "")
        if not gear_id or gear_id in taken:
            continue
        weapons.append(
            _public_weapon(
                spec,
                inst_id=gear_id,
                qty=max(1, int(item.get("qty") or 1)),
                nuyen=int(item.get("nuyen") or 0),
                from_gear=True,
                source_gear_id=gear_id,
            )
        )
        taken.add(gear_id)


def _append_armor_weapons(weapons: list[dict[str, Any]], armor_items: list[dict[str, Any]]) -> None:
    """Rows for armour that is also a weapon — a shield you hit people with.

    Same shape as the gear-granted rows above: the armour was paid for as
    armour, so the weapon costs nothing more and is deleted by dropping the
    armour it belongs to.
    """
    taken = {str(row.get("id") or "") for row in weapons}
    for item in armor_items:
        armor_spec = _item_by_id("armor", str(item.get("armor_id") or ""))
        spec_id = str((armor_spec or {}).get("add_weapon_id") or "")
        if not spec_id:
            continue
        spec = _item_by_id("weapons", spec_id)
        if not spec:
            continue
        armor_id = str(item.get("id") or "")
        if not armor_id or armor_id in taken:
            continue
        weapon = _public_weapon(spec, inst_id=armor_id, qty=1, nuyen=int(item.get("nuyen") or 0))
        weapon["from_armor"] = True
        weapon["source_armor_id"] = armor_id
        weapons.append(weapon)
        taken.add(armor_id)


def _append_quality_weapons(weapons: list[dict[str, Any]], qualities: list[dict[str, Any]]) -> None:
    """Rows for the attacks a quality brings with it (`<addweapon>`).

    Claws, Fangs, Goring Horns and the rest of the metagenetic qualities
    (RF p.104) are weapons the character grew rather than bought, so they are
    marked `natural` exactly like a metatype's own attack: no cost, no
    accessories, and nothing to delete but the quality itself.
    """
    taken = {str(row.get("id") or "") for row in weapons}
    for index, quality in enumerate(qualities):
        spec_id = str(quality.get("add_weapon_id") or "")
        if not spec_id:
            continue
        spec = _item_by_id("weapons", spec_id)
        if not spec:
            continue
        # By position, not by quality id: a quality can be taken twice, and
        # each take is its own set of claws.
        inst_id = f"quality-{index}-{spec_id}"
        if inst_id in taken:
            continue
        weapon = _public_weapon(spec, inst_id=inst_id, qty=1, nuyen=0)
        weapon["natural"] = True
        weapon["natural_source"] = str(quality.get("name") or "")
        weapons.append(weapon)
        taken.add(inst_id)


def _append_natural_weapons(
    weapons: list[dict[str, Any]],
    effects: EffectsDict | None,
) -> None:
    """Rows for the attacks a metatype was born with (`<naturalweapon>`).

    A Shapeshifter's bite and claws are not in `weapons.xml` — the metavariant's
    bonus node carries the whole weapon (RF p.104) — so the row is built from
    the node instead of a spec. They cost nothing, take no accessories and are
    never in `state.weapons`, which is why the `.chum5` export never sees them.
    """
    rows = list((effects or empty_effects()).get("natural_weapons") or [])
    if not rows:
        return
    taken = {str(row.get("id") or "") for row in weapons}
    for index, row in enumerate(rows):
        inst_id = f"natural-{index}"
        if inst_id in taken:
            continue
        spec = {
            "id": "",
            "name": row["name"],
            "category": "Unarmed",
            "type": "Melee",
            "weapon_type": "Melee",
            "accuracy": row["accuracy"],
            "reach": row["reach"],
            "damage": row["damage"],
            "ap": row["ap"],
            "useskill": row["useskill"],
            "source": row["weapon_source"],
            "page": row["page"],
        }
        weapon = _public_weapon(spec, inst_id=inst_id, qty=1, nuyen=0)
        weapon["natural"] = True
        weapon["natural_source"] = row["source"]
        weapons.append(weapon)
        taken.add(inst_id)


def _drone_mod_limb_attrs(
    mod_id: str,
    ware_by_id: dict[str, dict[str, Any]],
    state: CharacterState,
) -> tuple[int, int]:
    inst = next((row for row in list(state.vehicle_mods or []) if row.id == mod_id), None)
    if not inst:
        return 0, 0
    spec = _item_by_id("vehicle_mods", inst.mod_id)
    if not spec:
        return 0, 0
    name = (spec.get("name") or "").lower()
    if "arm" not in name and "leg" not in name:
        return 0, 0
    body = 0
    pilot = 0
    parent_id = inst.parent_id or ""
    for kind in ("drones", "vehicles"):
        host = next((row for row in list(getattr(state, kind) or []) if row.id == parent_id), None)
        if not host:
            continue
        host_spec = _item_by_id(kind, host.gear_id)
        if not host_spec:
            continue
        body = _leading_vehicle_stat(host_spec.get("body"))
        pilot = _leading_vehicle_stat(host_spec.get("pilot"))
        break
    str_val = max(body, 0)
    agi_val = max(pilot, 0)
    str_bonus = 0
    agi_bonus = 0
    for kid in ware_by_id.values():
        if kid.get("parent_id") != mod_id:
            continue
        effect = _limb_attr_effect(kid.get("name") or "")
        if not effect:
            continue
        attr, mode = effect
        rating = int(kid.get("rating") or 1)
        if attr == "STR":
            if mode == "set":
                str_val = rating
            else:
                str_bonus = rating
        else:
            if mode == "set":
                agi_val = rating
            else:
                agi_bonus = rating
    return (
        min(str_val + str_bonus, max(body * 2, 1)),
        min(agi_val + agi_bonus, max(pilot * 2, 1)),
    )


def _ware_weapon_attr_values(
    ware: dict[str, Any],
    ware_by_id: dict[str, dict[str, Any]],
    state: CharacterState,
    attr_totals: dict[str, int] | None,
) -> tuple[int, int, bool]:
    node: dict[str, Any] | None = ware
    seen: set[str] = set()
    while node:
        nid = str(node.get("id") or "")
        if nid in seen:
            break
        seen.add(nid)
        if node.get("limb_str") is not None:
            return int(node.get("limb_str") or 0), int(node.get("limb_agi") or 0), True
        parent_id = str(node.get("parent_id") or "")
        if not parent_id:
            break
        nxt = ware_by_id.get(parent_id)
        if nxt:
            node = nxt
            continue
        str_val, agi_val = _drone_mod_limb_attrs(parent_id, ware_by_id, state)
        if str_val or agi_val:
            return str_val, agi_val, True
        break
    totals = attr_totals or {}
    raw = state.attributes or {}
    return (
        int(totals.get("STR") or raw.get("STR") or 1),
        int(totals.get("AGI") or raw.get("AGI") or 1),
        False,
    )


def _apply_ware_weapon_attrs(
    weapon: dict[str, Any],
    ware: dict[str, Any],
    ware_by_id: dict[str, dict[str, Any]],
    state: CharacterState,
    attr_totals: dict[str, int] | None,
) -> None:
    str_val, agi_val, from_limb = _ware_weapon_attr_values(ware, ware_by_id, state, attr_totals)
    attrs = {"STR": str_val, "AGI": agi_val}
    for key in ("damage", "ap", "accuracy", "reach"):
        raw = str(weapon.get(key) or "")
        # keep the formula beside the number, as `resolve_attr_formulas` does
        # for a weapon held in the hand
        if key in ("damage", "accuracy") and "{" in raw:
            weapon[f"{key}_formula"] = raw
        weapon[key] = _eval_attr_stat(raw, attrs)
    if from_limb:
        weapon["limb_str"] = str_val
        weapon["limb_agi"] = agi_val


def _append_ware_weapons(
    weapons: list[dict[str, Any]],
    ware_items: list[dict[str, Any]],
    state: CharacterState,
    attr_totals: dict[str, int] | None = None,
) -> None:
    taken = {str(row.get("id") or "") for row in weapons}
    ware_by_id = {str(item.get("id") or ""): item for item in ware_items if item.get("id")}
    for item in ware_items:
        spec_id = str(item.get("add_weapon_id") or "")
        if not spec_id:
            continue
        spec = _item_by_id("weapons", spec_id)
        if not spec:
            continue
        ware_id = str(item.get("id") or "")
        if not ware_id or ware_id in taken:
            continue
        row = _public_weapon(
            spec,
            inst_id=ware_id,
            qty=1,
            nuyen=int(item.get("nuyen") or 0),
            from_ware=True,
            source_ware_id=ware_id,
        )
        # Which tab owns it: bioware claws are deleted from `bioware`, a
        # cyberspur from `cyberware`.
        row["ware_kind"] = str(item.get("ware_kind") or "cyberware")
        _apply_ware_weapon_attrs(row, item, ware_by_id, state, attr_totals)
        weapons.append(row)
        taken.add(ware_id)
