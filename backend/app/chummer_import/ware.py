"""Cyberware and bioware."""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET  # the Element type only — parsing goes through parse_untrusted
from typing import Any

from ..data_loader import CatalogDict
from ..data_loader._xml import _int, _text
from ..notices import Notice, Phrase, ui
from ._common import _discounted, _picked_cost, _Resolver, _unexpected_children


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
    ware_by_id = {str(row["id"]): row for row in ware_rows}
    picks: dict[str, str] = {}
    #: gear held in a piece of ware: (install id, ware id, kind, node)
    carried: list[tuple[str, str, Phrase, ET.Element]] = []

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
                "discounted": _discounted(w),
            }
            if (ware_by_id.get(wid) or {}).get("cost_range"):
                row["cost"] = _picked_cost(w)
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
            held = _unexpected_children(wid, w.findall("./gears/gear"))
            if held:
                # routed with the rest of the gear, which knows the buckets
                carried.extend((str(row["id"]), wid, kind, g) for g in held)
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
    # A drone's arm or leg holds implants too (a Shock Hand, a smuggling
    # compartment). Read here with the rest; `_import_vehicles` hangs each on
    # the mod row it makes for that `<mod>`.
    in_mods: dict[int, list[dict[str, Any]]] = {}
    for mod in root.findall("./vehicles/vehicle/mods/mod"):
        rows_in = load_ware(mod.findall("./cyberwares/cyberware"), ui("engine.kind.cyberware"))
        if rows_in:
            in_mods[id(mod)] = rows_in
            st["cyberware"].extend(rows_in)
    st["skill_picks"] = {**(st.get("skill_picks") or {}), **picks}
    st["_ware_gear"] = carried
    st["_vehicle_mod_ware"] = in_mods
