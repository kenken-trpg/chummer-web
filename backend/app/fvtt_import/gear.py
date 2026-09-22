"""Gear, routed to the bucket it belongs in: Foundry keeps it flat."""

from __future__ import annotations

import math
import uuid
from typing import Any

from ..data_loader import catalog_list
from ..notices import Notice, notice, ui
from ._common import _MAX_QTY, _extra, _Matcher, _num, _rating, _tech

#: gear buckets tried before plain gear, as the .chum5 import does
_GEAR_BUCKETS = ("commlinks", "cyberdecks", "rccs", "programs", "apps", "sensors", "optics")

#: Foundry item types that are gear of some kind
_GEAR_TYPES = ("equipment", "device", "program", "sin", "ammo")


def _import_gear(items: list[dict[str, Any]], st: dict[str, Any], warn: list[Notice]) -> None:
    """Gear, into whichever bucket matches it. Foundry keeps it flat."""
    matchers = {b: _Matcher(catalog_list(b)) for b in (*_GEAR_BUCKETS, "gear")}
    rows_by_id = {str(r["id"]): r for b in matchers for r in catalog_list(b)}
    routed: dict[str, list[dict[str, Any]]] = {b: [] for b in matchers}
    for i in items:
        if i.get("type") not in _GEAR_TYPES:
            continue
        got = next(((b, gid) for b, m in matchers.items() if (gid := m.find(i))), None)
        if not got:
            warn.append(notice("engine.import.skippedUnknown", kind=ui("engine.kind.gear"), name=str(i.get("name"))))
            continue
        bucket, gid = got
        spec = rows_by_id[gid]
        qty = max(1, _num(_tech(i).get("quantity"), 1))
        row: dict[str, Any] = {"id": str(uuid.uuid4()), "gear_id": gid, "rating": _rating(i)}
        # Foundry counts single items (100 rounds); this app counts what the
        # price is quoted for (a box of 10)
        row["qty"] = min(
            _MAX_QTY, qty if bucket == "commlinks" else max(1, math.ceil(qty / max(1, _num(spec.get("costfor")))))
        )
        if spec.get("cost_range"):
            row["cost"] = _num(_tech(i).get("cost"))
        if extra := _extra(i):
            row["extra"] = extra
        routed[bucket].append(row)
    st.update(routed)
