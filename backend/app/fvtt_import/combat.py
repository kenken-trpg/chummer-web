"""Armor and its mods, weapons and their accessories, cyber- and bioware."""

from __future__ import annotations

import uuid
from typing import Any, cast

from ..data_loader import CatalogDict
from ..notices import Notice
from ._common import _MAX_QTY, _d, _embedded, _extra, _flags, _Matcher, _num, _rating, _tech

#: Foundry cyberware grade -> this app's
_GRADES = {
    "standard": "Standard",
    "alpha": "Alphaware",
    "beta": "Betaware",
    "delta": "Deltaware",
    "gamma": "Gammaware",
    "grey": "Greyware",
    "used": "Used",
}


def _import_combat(items: list[dict[str, Any]], cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Armor and its mods, weapons and their accessories, cyber- and bioware."""
    armor_m = _Matcher(cat["armor"])
    amod_m = _Matcher(cat["armor_mods"])
    variable_armor = {str(r["id"]) for r in cat["armor"] if r.get("cost_range")}
    armor: list[dict[str, Any]] = []
    armor_mods: list[dict[str, Any]] = []
    for i in items:
        if i.get("type") != "armor" or not (aid := armor_m.match(i, warn, "engine.kind.armor")):
            continue
        row: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "armor_id": aid,
            "rating": _rating(i),
            "equipped": bool(_tech(i).get("equipped", True)),
        }
        if aid in variable_armor:
            row["cost"] = _num(_tech(i).get("cost"))
        armor.append(row)
        for m in _embedded(i):
            if m.get("type") == "modification" and (mid := amod_m.match(m, warn, "engine.kind.armorMod")):
                armor_mods.append(
                    {"id": str(uuid.uuid4()), "mod_id": mid, "parent_id": row["id"], "rating": _rating(m)}
                )

    weapons_by_id = {str(r["id"]): r for r in cat["weapons"]}
    weap_m = _Matcher(cat["weapons"])
    wacc_m = _Matcher(cat["weapon_accessories"])
    weapons: list[dict[str, Any]] = []
    accessories: list[dict[str, Any]] = []
    for i in items:
        if i.get("type") != "weapon" or not (wid := weap_m.match(i, warn, "engine.kind.weapon")):
            continue
        spec = weapons_by_id[wid]
        if not spec.get("purchasable", True):
            # a cyberspur, bioware claws: the ware that grants it brings it back
            continue
        row = {
            "id": str(uuid.uuid4()),
            "weapon_id": wid,
            "qty": min(_MAX_QTY, max(1, _num(_tech(i).get("quantity"), 1))),
        }
        weapons.append(row)
        built_in = {str(n).lower() for n in spec.get("included") or []}
        for acc in _embedded(i):
            if acc.get("type") != "modification":
                continue
            english = str(_flags(acc).get("name") or acc.get("name") or "").lower()
            if english in built_in:
                continue  # comes with the weapon
            if acid := wacc_m.match(acc, warn, "engine.kind.weaponAccessory"):
                mount = str(_d(_d(acc.get("system")).get("mod_weapon")).get("mount_point") or "")
                accessories.append(
                    {
                        "id": str(uuid.uuid4()),
                        "accessory_id": acid,
                        "parent_id": row["id"],
                        "mount": mount.capitalize(),
                        "rating": _rating(acc),
                    }
                )

    ware_ids: dict[str, set[str]] = {}
    ware_rows: list[dict[str, Any]] = []
    for kind in ("cyberware", "bioware"):
        rows = cast(dict[str, Any], cat.get(kind) or {}).get("items") or []
        ware_ids[kind] = {str(r["id"]) for r in rows}
        ware_rows += rows
    ware_m = _Matcher(ware_rows)
    variable_ware = {str(r["id"]) for r in ware_rows if r.get("cost_range")}
    ware: dict[str, list[dict[str, Any]]] = {"cyberware": [], "bioware": []}
    for i in items:
        kind = str(i.get("type") or "")
        if kind not in ware or not (wid := ware_m.match(i, warn, f"engine.kind.{kind}")):
            continue
        row = {
            "id": str(uuid.uuid4()),
            "ware_id": wid,
            "rating": _rating(i),
            "grade": _GRADES.get(str(_d(i.get("system")).get("grade") or ""), "Standard"),
            "extra": _extra(i),
        }
        if wid in variable_ware:
            row["cost"] = _num(_tech(i).get("cost"))
        # the bucket the catalog has it in, whatever Foundry called it
        ware["bioware" if wid in ware_ids["bioware"] else "cyberware"].append(row)
    st.update(armor=armor, armor_mods=armor_mods, weapons=weapons, weapon_accessories=accessories, **ware)
