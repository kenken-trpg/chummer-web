"""Gear, routed to its buckets (commlinks, decks, sensors, programs, ...), and custom drugs.\n\nWare is in `ware`, armor and weapons in `combat`, vehicles in `vehicles`."""

from __future__ import annotations

import math
import uuid
import xml.etree.ElementTree as ET  # the Element type only — parsing goes through parse_untrusted
from typing import Any, cast

from ..data_loader import CatalogDict, catalog_list
from ..data_loader._xml import _int, _text, current_overlay_key
from ..notices import Notice, Phrase, notice, ui
from ._common import _chummer_added, _data_index, _discounted, _picked_cost, _Resolver


def _qty(node: ET.Element) -> float:
    """`<qty>` as Chummer writes it — a decimal ("100", "2.5")."""
    try:
        return max(0.0, float(_text(node.find("qty")) or 1))
    except ValueError:
        return 1.0


def _included(node: ET.Element) -> bool:
    """Whether Chummer says the entry came with its parent."""
    return any(_text(node.find(tag)).lower() == "true" for tag in ("included", "includedinparent"))


def _import_gear(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read gear, routed to whichever catalog bucket resolves it."""
    from ..engine.gear.misc import (
        _commlink_accessory_parent_spec,
        _matrix_device_parent_spec,
        _misc_child_fits,
    )

    #: what this app can fit inside a piece of armor or a vehicle
    HOST_BUCKETS = ("gear", "optics", "sensors")
    BUCKETS = ("commlinks", "cyberdecks", "rccs", "sensors", "optics", "programs", "apps", "drones")
    gear_res = {b: _Resolver(catalog_list(b)) for b in ("gear", *BUCKETS)}
    routed: dict[str, list[dict[str, Any]]] = {b: [] for b in ("gear", *BUCKETS)}
    # Chummer's `<qty>` counts single items (100 rounds); this app's `qty`
    # counts what the price is quoted for — `costfor` of them (a box of 10).
    cost_for = {str(row["id"]): int(row.get("costfor") or 0) for b in ("gear", *BUCKETS) for row in catalog_list(b)}

    rows_by_id = {str(row["id"]): row for b in ("gear", *BUCKETS) for row in catalog_list(b)}

    def stays(
        spec: dict[str, Any],
        parent_bucket: str | None,
        parent_gid: str,
        host: tuple[Phrase, str] | None,
        host_armor: bool,
        host_allow: list[str] | None = None,
    ) -> bool:
        """Whether the engine keeps a gear-bucket item where the save put it
        (`engine/gear/misc.py` runs the same tests)."""
        if host_allow is not None:
            # a piece of ware holds the categories its `<allowgear>` names;
            # ware that holds none is no host to the engine at all, which
            # would drop the piece without a word
            return str(spec.get("category") or "") in host_allow
        if spec.get("requireparent"):
            # it cannot be carried on its own either: left where it is, the
            # engine says it does not fit
            return True
        if host_armor:
            return bool(spec.get("armor_capacity"))
        if host is not None:
            return True  # a vehicle carries anything that needs no host
        parent = rows_by_id.get(parent_gid) or {}
        if parent_bucket == "gear":
            return _misc_child_fits(parent, spec)
        if parent_bucket == "commlinks":
            return _misc_child_fits(_commlink_accessory_parent_spec(parent), spec)
        if parent_bucket in ("cyberdecks", "rccs"):
            return _misc_child_fits(_matrix_device_parent_spec(parent), spec)
        return True

    def route_gear(
        g: ET.Element,
        parent_id: str | None,
        parent_bucket: str | None,
        host: tuple[Phrase, str] | None = None,
        parent_gid: str = "",
        host_armor: bool = False,
        host_allow: list[str] | None = None,
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
        if host is not None:
            # inside armor or a vehicle, an optic before a sensor function of
            # the same name (Vision Magnification is both)
            order = list(HOST_BUCKETS) + order
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
        # an autosoft runs on the drone or vehicle it is loaded into
        runs_there = (
            bucket == "programs"
            and host is not None
            and host[0] == ui("engine.kind.vehicle")
            and (rows_by_id.get(gid) or {}).get("program_host") == "rccs"
        )
        if (
            host is not None
            and (bucket not in HOST_BUCKETS or host_allow is not None and bucket != "gear")
            and not runs_there
        ):
            # a commlink stowed there (or an autosoft in armor): this app fits
            # those to other hosts only, so the piece is left out — but said so
            kind, host_name = host
            warn.append(notice("engine.import.hostGearSkipped", kind=kind, name=name, host=host_name))
            return
        row: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "gear_id": gid,
            "rating": max(1, _int(g.find("rating"), 1)),
            "discounted": _discounted(g),
        }
        spec = rows_by_id.get(gid) or {}
        if spec.get("cost_range"):
            row["cost"] = _picked_cost(g)
        if spec.get("category") == "Custom" and name and name != spec.get("name"):
            row["name"] = name
        if _text(g.find("extra")) and bucket != "commlinks":
            # what the item is for: an autosoft's model or weapon, a skillsoft's skill
            row["extra"] = _text(g.find("extra"))
        included = bool(parent_id) and (
            _included(g)
            # older saves do not say: what the parent's own entry
            # brings (a Nixdorf Sekretar's Agent) came with it
            or name.lower() in _data_index(current_overlay_key()).included.get(parent_gid, frozenset())
        )
        if (
            parent_id
            and bucket == "gear"
            and not included
            and not stays(spec, parent_bucket, parent_gid, host, host_armor, host_allow)
        ):
            # Chummer lets a player drag any gear into any other (ammo into a
            # Spare Clip, a reader into a commlink); this app would drop it
            # there, and what it holds with it, so it is carried on its own
            # instead — and said so.
            host_name = host[1] if host is not None else str((rows_by_id.get(parent_gid) or {}).get("name") or "")
            warn.append(notice("engine.import.gearMovedOut", name=name, host=host_name))
            parent_id = None
        if bucket == "commlinks":
            row["qty"] = max(1, math.ceil(_qty(g)))
        else:
            row["qty"] = max(1, math.ceil(_qty(g) / max(1, cost_for.get(gid, 0))))
            if parent_id:
                row["parent_id"] = parent_id
                row["included"] = included
        routed[bucket].append(row)
        for child in g.findall("./children/gear"):
            route_gear(child, row["id"], bucket, parent_gid=gid)

    for g in root.findall("./gears/gear"):
        # A bonded focus is gear too, but it belongs to `foci` / `qi_foci`
        # rather than to any gear bucket — `_import_foci` reads it there.
        if _text(g.find("category")) == "Foci":
            continue
        route_gear(g, None, None)
    armor_names = {str(a["id"]): str(a.get("name") or "") for a in catalog_list("armor")}
    armor_of = {str(a["id"]): armor_names.get(str(a["armor_id"]), "") for a in st.get("armor") or []}
    for armor_id, g in st.pop("_armor_gear", None) or []:
        route_gear(g, armor_id, None, (ui("engine.kind.armor"), armor_of.get(armor_id, "")), host_armor=True)
    vehicle_names = {
        str(v["id"]): next(
            (row["name"] for b in ("vehicles", "drones") for row in catalog_list(b) if row["id"] == v["gear_id"]),
            "",
        )
        for b in ("vehicles", "drones")
        for v in st.get(b) or []
    }
    for vehicle_id, g in st.pop("_vehicle_gear", None) or []:
        route_gear(g, vehicle_id, None, (ui("engine.kind.vehicle"), vehicle_names.get(vehicle_id, "")))
    ware_rows: dict[str, dict[str, Any]] = {
        str(row["id"]): row
        for kind in ("cyberware", "bioware")
        for row in (cast(dict[str, Any], cat.get(kind) or {}).get("items") or [])
    }
    for ware_inst, ware_id, kind, g in st.pop("_ware_gear", None) or []:
        ware = ware_rows.get(ware_id) or {}
        route_gear(
            g,
            ware_inst,
            None,
            (kind, str(ware.get("name") or "")),
            parent_gid=ware_id,
            host_allow=list(ware.get("allow_gear") or []),
        )
    for b, rows in routed.items():
        # vehicles import first: its drones are already in `st`
        st[b] = (st.get(b) or []) + rows


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
