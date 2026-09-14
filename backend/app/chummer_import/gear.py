"""Everything bought: ware, armor, weapons, gear, vehicles and custom drugs."""

from __future__ import annotations

import math
import uuid
import xml.etree.ElementTree as ET  # the Element type only — parsing goes through parse_untrusted
from typing import Any

from ..data_loader import CatalogDict, catalog_list
from ..data_loader._xml import _int, _text
from ..notices import Notice, Phrase, notice, ui
from ._common import _chummer_added, _Resolver, _unexpected_children


def _came_with_parent(node: ET.Element) -> bool:
    """Whether a piece of ware came with the one it sits in, rather than being
    bought for it.

    Chummer sets `<parentid>` to the parent's guid on what the parent's own
    data added (a cybereye's Image Link, a subsystem) and leaves it empty on
    what the player put in — that is paid for, Customized Agility in a
    cyberlimb or a Biomonitor in its capacity. This app's older exports mark
    the former with `<included>True`.
    """
    if node.find("parentid") is not None:
        return bool(_text(node.find("parentid")))
    return _text(node.find("included")).lower() == "true"


def _import_ware(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read cyber- and bioware, nested to any depth."""
    ware_rows = (cat.get("cyberware") or {}).get("items") or []
    ware_rows = ware_rows + ((cat.get("bioware") or {}).get("items") or [])
    ware_r = _Resolver(ware_rows)
    picks: dict[str, str] = {}

    def load_ware(nodes: list[ET.Element], kind: Phrase) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for w in nodes:
            wid = ware_r.resolve(w, warn, kind)
            if not wid:
                continue
            row = {
                "id": str(uuid.uuid4()),
                "ware_id": wid,
                "rating": max(1, _int(w.find("rating"), 1)),
                "grade": _text(w.find("grade")) or "Standard",
                "side": _text(w.find("location")) or None,
                "extra": _text(w.find("extra")) or None,
                "included": _came_with_parent(w),
            }
            out.append(row)
            for pick in w.findall("./skillpicks/pick"):
                skill = _text(pick.find("skill"))
                if skill:
                    picks[f"ware:{row['id']}:{_text(pick.find('index'))}"] = skill
            kids = w.findall("./children/cyberware") + w.findall("./children/bioware")
            for child in load_ware(kids, kind):
                # `load_ware` returns the whole subtree flat: only the direct
                # children are this row's, a grandchild keeps its own parent
                child.setdefault("parent_id", row["id"])
                out.append(child)
            if _unexpected_children(wid, w.findall("./gears/gear")):
                warn.append(notice("engine.import.nestedGearSkipped", kind=kind, name=_text(w.find("name"))))
        return out

    # Chummer keeps bioware in `<cyberwares>` too, as `<cyberware>` rows told
    # apart only by `<improvementsource>Bioware</improvementsource>`. Left in
    # with the cyberware they resolved to a bioware id the cyberware side
    # cannot price, and every piece of bioware in a Chummer save was dropped.
    rows = root.findall("./cyberwares/cyberware")
    bio_rows = [w for w in rows if _text(w.find("improvementsource")).lower() == "bioware"]
    st["cyberware"] = load_ware([w for w in rows if w not in bio_rows], ui("engine.kind.cyberware"))
    st["bioware"] = load_ware(
        bio_rows + root.findall("./biowares/bioware") + root.findall("./cyberwares/bioware"), ui("engine.kind.bioware")
    )
    st["skill_picks"] = {**(st.get("skill_picks") or {}), **picks}


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
    # Only weapons a character could have bought: the granted ones (a cyberspur,
    # bioware claws) come back with the ware that grants them, and matching them
    # here as well would give the character the weapon twice.
    weap_r = _Resolver([w for w in cat["weapons"] if w.get("purchasable")])
    wacc_r = _Resolver(cat["weapon_accessories"])
    st_weap: list[dict[str, Any]] = []
    st_wacc: list[dict[str, Any]] = []
    for w in root.findall("./weapons/weapon"):
        if _text(w.find("cyberware")).lower() == "true":
            continue
        wid = weap_r.resolve(w, warn, ui("engine.kind.weapon"))
        if not wid:
            continue
        row = {"id": str(uuid.uuid4()), "weapon_id": wid, "qty": max(1, _int(w.find("qty"), 1))}
        st_weap.append(row)
        for acc in w.findall("./accessories/accessory"):
            acid = wacc_r.resolve(acc, warn, ui("engine.kind.weaponAccessory"))
            if acid:
                st_wacc.append(
                    {
                        "id": str(uuid.uuid4()),
                        "accessory_id": acid,
                        "parent_id": row["id"],
                        "mount": _text(acc.find("mount")),
                        "rating": max(1, _int(acc.find("rating"), 1)),
                        "included": _text(acc.find("included")).lower() == "true",
                    }
                )
    st["weapons"] = st_weap
    st["weapon_accessories"] = st_wacc


def _picked_cost(node: ET.Element) -> int | None:
    """`<cost>` of an item Chummer let the player price — the number picked."""
    try:
        return max(0, int(round(float(_text(node.find("cost"))))))
    except ValueError:
        return None


def _qty(node: ET.Element) -> float:
    """`<qty>` as Chummer writes it — a decimal ("100", "2.5")."""
    try:
        return max(0.0, float(_text(node.find("qty")) or 1))
    except ValueError:
        return 1.0


def _import_gear(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read gear, routed to whichever catalog bucket resolves it."""
    BUCKETS = ("commlinks", "cyberdecks", "rccs", "sensors", "optics", "programs", "apps", "drones")
    gear_res = {b: _Resolver(catalog_list(b)) for b in ("gear", *BUCKETS)}
    routed: dict[str, list[dict[str, Any]]] = {b: [] for b in ("gear", *BUCKETS)}
    # Chummer's `<qty>` counts single items (100 rounds); this app's `qty`
    # counts what the price is quoted for — `costfor` of them (a box of 10).
    cost_for = {str(row["id"]): int(row.get("costfor") or 0) for b in ("gear", *BUCKETS) for row in catalog_list(b)}

    rows_by_id = {str(row["id"]): row for b in ("gear", *BUCKETS) for row in catalog_list(b)}

    def route_gear(
        g: ET.Element, parent_id: str | None, parent_bucket: str | None, armor_name: str | None = None
    ) -> None:
        # Chummer names a gear entry by `<id>` too — a Custom Item's `<name>`
        # is whatever the player called it
        sid = _text(g.find("sourceid")) or (_text(g.find("id")) if _text(g.find("id")) in rows_by_id else "")
        sid = sid or _text(g.find("guid"))
        name = _text(g.find("name"))
        bucket = "gear"
        gid: str | None = None
        # a child stays with its parent's bucket if it resolves there
        order = ([parent_bucket] if parent_bucket else []) + list(BUCKETS) + ["gear"]
        for b in order:
            if not b:
                continue
            r = gear_res[b]
            cand = sid if sid in r.ids else r.by_name.get(name.lower())
            if cand:
                gid, bucket = cand, b
                break
        if not gid:
            if name and not _chummer_added(g):
                warn.append(notice("engine.import.skippedUnknown", kind=ui("engine.kind.gear"), name=name))
            return
        if armor_name is not None and bucket != "gear":
            # a sensor or an optic in armor: this app fits those to other
            # hosts only, so the piece is left out — but said so
            warn.append(notice("engine.import.armorGearSkipped", name=name, armor=armor_name))
            return
        row: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "gear_id": gid,
            "rating": max(1, _int(g.find("rating"), 1)),
        }
        spec = rows_by_id.get(gid) or {}
        if spec.get("cost_range"):
            row["cost"] = _picked_cost(g)
        if spec.get("category") == "Custom" and name and name != spec.get("name"):
            row["name"] = name
        if bucket == "commlinks":
            row.pop("rating", None)
            row["rating"] = max(1, _int(g.find("rating"), 1))
        else:
            row["qty"] = max(1, math.ceil(_qty(g) / max(1, cost_for.get(gid, 0))))
            if parent_id:
                row["parent_id"] = parent_id
                row["included"] = _text(g.find("included")).lower() == "true"
        routed[bucket].append(row)
        for child in g.findall("./children/gear"):
            route_gear(child, row["id"], bucket)

    for g in root.findall("./gears/gear"):
        # A bonded focus is gear too, but it belongs to `foci` / `qi_foci`
        # rather than to any gear bucket — `_import_foci` reads it there.
        if _text(g.find("category")) == "Foci":
            continue
        route_gear(g, None, None)
    armor_names = {str(a["id"]): str(a.get("name") or "") for a in catalog_list("armor")}
    armor_of = {str(a["id"]): armor_names.get(str(a["armor_id"]), "") for a in st.get("armor") or []}
    for armor_id, g in st.pop("_armor_gear", None) or []:
        route_gear(g, armor_id, "gear", armor_of.get(armor_id, ""))
    for b, rows in routed.items():
        st[b] = rows


def _import_vehicles(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read vehicles, drones and vehicle mods."""
    veh_r = _Resolver(cat["vehicles"])
    drone_r = _Resolver(cat["drones"])
    vmod_r = _Resolver(cat["vehicle_mods"])
    mount_r = _Resolver(cat["weapon_mounts"])
    mount_categories = {row["id"]: row.get("category") or "" for row in cat["weapon_mounts"]}
    # A mount points at a weapon row by name: ids are regenerated on import.
    weapon_ids: dict[str, str] = {}
    for wrow in st.get("weapons") or []:
        wname = next((w["name"] for w in cat["weapons"] if w["id"] == wrow.get("weapon_id")), "")
        weapon_ids.setdefault(wname.lower(), wrow["id"])
    st_mounts: list[dict[str, Any]] = []
    st_veh: list[dict[str, Any]] = list(st.get("drones") or [])
    st_veh_only: list[dict[str, Any]] = []
    st_vmods: list[dict[str, Any]] = []
    for v in root.findall("./vehicles/vehicle"):
        is_drone = veh_r.resolve(v, [], ui("engine.kind.vehicle")) is None
        vid = (
            drone_r.resolve(v, [], ui("engine.kind.drone"))
            if is_drone
            else veh_r.resolve(v, warn, ui("engine.kind.vehicle"))
        )
        if not vid:
            vid = veh_r.resolve(v, [], ui("engine.kind.vehicle")) or drone_r.resolve(v, warn, ui("engine.kind.drone"))
        if not vid:
            continue
        row = {"id": str(uuid.uuid4()), "gear_id": vid, "rating": 1, "qty": 1}
        (st_veh if is_drone else st_veh_only).append(row)
        for m in v.findall("./mods/mod") + v.findall("./vehiclemods/vehiclemod"):
            mid = vmod_r.resolve(m, warn, ui("engine.kind.vehicleMod"))
            if mid:
                st_vmods.append(
                    {
                        "id": str(uuid.uuid4()),
                        "mod_id": mid,
                        "parent_id": row["id"],
                        "rating": max(1, _int(m.find("rating"), 1)),
                        "included": _text(m.find("included")).lower() == "true",
                    }
                )
        for m in v.findall("./weaponmounts/weaponmount"):
            size_id = mount_r.resolve(m, warn, ui("engine.kind.weaponMount"))
            if not size_id:
                continue
            parts = {"Visibility": "", "Flexibility": "", "Control": ""}
            for opt in m.findall("./weaponmountoptions/weaponmountoption"):
                part_id = mount_r.resolve(opt, warn, ui("engine.kind.weaponMount"))
                if part_id and mount_categories.get(part_id) in parts:
                    parts[mount_categories[part_id]] = part_id
            st_mounts.append(
                {
                    "id": str(uuid.uuid4()),
                    "parent_id": row["id"],
                    "size_id": size_id,
                    "visibility_id": parts["Visibility"],
                    "flexibility_id": parts["Flexibility"],
                    "control_id": parts["Control"],
                    "included": _text(m.find("included")).lower() == "true",
                    "weapon_install_id": weapon_ids.get(_text(m.find("mountedweaponname")).lower()),
                    "allowedweapons": _text(m.find("weaponmountcategories")),
                }
            )
        if _unexpected_children(vid, v.findall("./weapons/weapon") + v.findall("./gears/gear")):
            warn.append(notice("engine.import.vehicleLoadSkipped", name=_text(v.find("name"))))
    st["drones"] = st_veh
    st["vehicles"] = st_veh_only
    st["vehicle_mods"] = st_vmods
    st["weapon_mounts"] = st_mounts


def _import_custom_drugs(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read mixed drugs back out of `<drugs><drug>`.

    A custom drug is its components: cost, availability, addiction and onset
    are recomputed from them, so nothing Chummer wrote about the totals is
    read back. `<active>` is this app's own element (see the export) and is
    simply absent on a file Chummer wrote.
    """
    comp_r = _Resolver(cat.get("drug_components") or [])
    drugs = []
    for d in root.findall("./drugs/drug"):
        parts = []
        for c in d.findall("./drugcomponents/drugcomponent"):
            cid = comp_r.resolve(c, warn, ui("engine.kind.drugComponent"))
            if cid:
                parts.append({"component_id": cid, "level": max(0, _int(c.find("level"), 0))})
        if not parts:
            continue
        drugs.append(
            {
                "id": str(uuid.uuid4()),
                "name": _text(d.find("name")),
                "grade": _text(d.find("grade")) or "Standard",
                "qty": max(1, _int(d.find("quantity"), 1)),
                "active": _text(d.find("active")).lower() == "true",
                "parts": parts,
            }
        )
    st["custom_drugs"] = drugs
