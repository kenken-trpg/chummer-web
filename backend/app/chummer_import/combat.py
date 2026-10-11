"""Armor with its mods, and weapons with their accessories."""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET  # the Element type only — parsing goes through parse_untrusted
from typing import Any

from ..data_loader import CatalogDict, catalog_list
from ..data_loader._xml import _int, _text
from ..notices import Notice, ui
from ._common import _discounted, _picked_cost, _Resolver, _unexpected_children


def _is_gear_not_mod(node: ET.Element, mods: _Resolver, gear: _Resolver) -> bool:
    sid = _text(node.find("sourceid")) or _text(node.find("guid"))
    name = _text(node.find("name")).lower()
    if (sid and sid in mods.ids) or name in mods.by_name:
        return False
    return bool(sid and sid in gear.ids) or name in gear.by_name


def _import_armor(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read armor and the mods bolted to it.

    The gear carried in it (a Holster, a Medkit) is left for `_import_gear`,
    which knows the gear buckets, as (armor row id, gear node) pairs."""
    armor_r = _Resolver(cat["armor"])
    amod_r = _Resolver(cat["armor_mods"])
    variable_armor = {str(row["id"]) for row in cat["armor"] if row.get("cost_range")}
    gear_r = _Resolver(catalog_list("gear"))
    st_armor: list[dict[str, Any]] = []
    st_amods: list[dict[str, Any]] = []
    carried: list[tuple[str, ET.Element]] = []
    for a in root.findall("./armors/armor"):
        aid = armor_r.resolve(a, warn, ui("engine.kind.armor"))
        if not aid:
            continue
        row = {
            "id": str(uuid.uuid4()),
            "armor_id": aid,
            "rating": max(1, _int(a.find("rating"), 1)),
            "equipped": _text(a.find("equipped")).lower() != "false",
            "discounted": _discounted(a),
        }
        if aid in variable_armor:
            row["cost"] = _picked_cost(a)
        st_armor.append(row)
        # what the armor's own entry brings is not modelled apart from it
        armor_id = str(row["id"])
        carried += [(armor_id, g) for g in _unexpected_children(aid, a.findall("./gears/gear"))]
        for m in a.findall("./armormods/armormod"):
            if _is_gear_not_mod(m, amod_r, gear_r):
                # older saves list a Personal Drone Rack with the mods; the
                # data has it as gear that takes the armor's capacity
                carried.append((armor_id, m))
                continue
            mid = amod_r.resolve(m, warn, ui("engine.kind.armorMod"))
            if mid:
                st_amods.append(
                    {
                        "id": str(uuid.uuid4()),
                        "mod_id": mid,
                        "parent_id": row["id"],
                        "rating": max(1, _int(m.find("rating"), 1)),
                        "included": _text(m.find("included")).lower() == "true",
                        # Custom Fit (Stack): the armor it was tailored to
                        "stack_with": _text(m.find("extra")),
                    }
                )
    st["armor"] = st_armor
    st["armor_mods"] = st_amods
    st["_armor_gear"] = carried


def _import_weapons(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read weapons and their accessories."""
    weap_r, wacc_r = weapon_resolvers(cat)
    st_weap: list[dict[str, Any]] = []
    st_wacc: list[dict[str, Any]] = []
    hosts = st.pop("_ware_weapon_hosts", {})
    ware = {row["id"]: row for kind in ("cyberware", "bioware") for row in st.get(kind) or []}
    ware_specs = {row["id"]: row for kind in ("cyberware", "bioware") for row in cat[kind]["items"]}
    carried: list[tuple[str, ET.Element]] = []
    loaded: dict[str, str] = {}
    for w in root.findall("./weapons/weapon"):
        parent_id = hosts.get(_text(w.find("parentid"))) or hosts.get(_text(w.find("guid")))
        if parent_id:
            expected = ware_specs[ware[parent_id]["ware_id"]].get("add_weapon_id")
            if _text(w.find("sourceid")) != expected:
                continue
            _read_accessories(w, parent_id, wacc_r, st_wacc, warn)
            row_id = parent_id
        elif _text(w.find("parentid")):
            # made by Chummer from what brought it — a grenade bought as gear,
            # a Survival Kit's knife, a shield — and not bought again: this
            # app makes those rows from the same gear, armor or ware
            continue
        else:
            row_id = _read_weapon(w, weap_r, wacc_r, st_weap, st_wacc, warn)
        if row_id:
            carried.extend((row_id, g) for g in w.findall("./gears/gear"))
            if _text(w.find("loadedammoguid")):
                loaded[row_id] = _text(w.find("loadedammoguid"))
    st["_weapon_gear"] = carried
    st["_weapon_loaded"] = loaded
    st["weapons"] = st_weap
    st["weapon_accessories"] = st_wacc


def _read_weapon(
    w: ET.Element,
    weap_r: _Resolver,
    wacc_r: _Resolver,
    st_weap: list[dict[str, Any]],
    st_wacc: list[dict[str, Any]],
    warn: list[Notice],
) -> str | None:
    """Append one weapon row and its accessories; return the new row's id.

    Shared with the vehicle importer, which reads the guns bolted into a
    weapon mount: those are weapon rows of the character here, and the mount
    links to one by id.
    """
    if _text(w.find("cyberware")).lower() == "true":
        return None
    wid = weap_r.resolve(w, warn, ui("engine.kind.weapon"))
    if not wid:
        return None
    row = {
        "id": str(uuid.uuid4()),
        "weapon_id": wid,
        "qty": max(1, _int(w.find("qty"), 1)),
        "discounted": _discounted(w),
    }
    st_weap.append(row)
    _read_accessories(w, str(row["id"]), wacc_r, st_wacc, warn)
    return str(row["id"])


def _read_accessories(
    w: ET.Element, parent_id: str, wacc_r: _Resolver, st_wacc: list[dict[str, Any]], warn: list[Notice]
) -> None:
    for acc in w.findall("./accessories/accessory"):
        acid = wacc_r.resolve(acc, warn, ui("engine.kind.weaponAccessory"))
        if acid:
            st_wacc.append(
                {
                    "id": str(uuid.uuid4()),
                    "accessory_id": acid,
                    "parent_id": parent_id,
                    "mount": _text(acc.find("mount")),
                    "rating": max(1, _int(acc.find("rating"), 1)),
                    "included": _text(acc.find("included")).lower() == "true",
                }
            )


def weapon_resolvers(cat: CatalogDict) -> tuple[_Resolver, _Resolver]:
    """The two resolvers `_read_weapon` takes.

    Only weapons a character could have bought: the granted ones (a cyberspur,
    bioware claws) come back with the ware that grants them, and matching them
    here as well would give the character the weapon twice.
    """
    return (
        _Resolver([w for w in cat["weapons"] if w.get("purchasable")]),
        _Resolver(cat["weapon_accessories"]),
    )
