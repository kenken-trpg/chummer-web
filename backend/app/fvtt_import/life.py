"""Contacts, lifestyles and the tradition."""

from __future__ import annotations

import uuid
from typing import Any

from ..data_loader import CatalogDict
from ..notices import Notice, notice, ui
from ._common import _ATTRIBUTES, _d, _Matcher, _num

#: Foundry lifestyle `type` -> the catalog lifestyle it stands for
_LIFESTYLES = {
    "street": "Street",
    "squatter": "Squatter",
    "low": "Low",
    "medium": "Medium",
    "high": "High",
    "luxury": "Luxury",
}


def _import_life(
    system: dict[str, Any], items: list[dict[str, Any]], cat: CatalogDict, st: dict[str, Any], warn: list[Notice]
) -> None:
    """Contacts, lifestyles and the tradition."""
    st["contacts"] = [
        {
            "id": str(uuid.uuid4()),
            "name": str(i.get("name") or ""),
            "role": str(_d(i.get("system")).get("type") or "") or None,
            "connection": max(1, _num(_d(i.get("system")).get("connection"), 1)),
            "loyalty": max(1, _num(_d(i.get("system")).get("loyalty"), 1)),
            "group": bool(_d(i.get("system")).get("group")),
        }
        for i in items
        if i.get("type") == "contact"
    ]
    ls_m = _Matcher(cat["lifestyles"])
    lifestyles: list[dict[str, Any]] = []
    for i in items:
        if i.get("type") != "lifestyle":
            continue
        # a lifestyle is named by the player: the catalog one is its `type`
        lid = ls_m.find(i) or ls_m.by_name.get(_LIFESTYLES.get(str(_d(i.get("system")).get("type") or ""), "").lower())
        if lid:
            lifestyles.append({"id": str(uuid.uuid4()), "lifestyle_id": lid, "months": 1})
        else:
            warn.append(
                notice("engine.import.skippedUnknown", kind=ui("engine.kind.lifestyle"), name=str(i.get("name")))
            )
    st["lifestyles"] = lifestyles
    if st["talent"] in ("Magician", "Mystic Adept", "Aspected Magician"):
        # Foundry keeps only the drain attribute: the first tradition that
        # resists drain with it (Hermetic for LOG, Shamanic for CHA)
        drain = _ATTRIBUTES.get(str(_d(system.get("magic")).get("attribute") or ""))
        tid = next((str(t["id"]) for t in cat["traditions"] if (t.get("drain_attrs") or [])[-1:] == [drain]), None)
        if tid:
            st["tradition_id"] = tid
