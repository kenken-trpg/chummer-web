"""Cyber- and bioware, which share a shape (`grades` + `items`)."""

from __future__ import annotations

from ..data_loader import CatalogDict

_EMPTY: dict = {"grades": [], "items": []}


def section(raw: CatalogDict) -> dict:
    return {
        "cyberware": _public_ware(raw.get("cyberware") or _EMPTY),
        "bioware": _public_ware(raw.get("bioware") or _EMPTY),
    }


def _public_ware(block: dict) -> dict:
    grades = [g for g in block.get("grades") or [] if g.get("core")]
    items = []
    for w in block.get("items") or []:
        items.append(
            {
                "id": w["id"],
                "name": w["name"],
                "category": w["category"],
                "ess": w["ess"],
                "cost": w["cost"],
                "capacity": w.get("capacity") or "",
                "minrating": w["minrating"],
                "maxrating": w["maxrating"],
                "minrating_expr": w.get("minrating_expr") or str(w["minrating"]),
                "maxrating_expr": w.get("maxrating_expr") or str(w["maxrating"]),
                "forcegrade": w.get("forcegrade"),
                "plugin": w.get("plugin", False),
                "requireparent": bool(w.get("requireparent")),
                "addtoparentess": bool(w.get("addtoparentess")),
                "formula_rating": bool(w.get("formula_rating")),
                "allow_subsystems": list(w.get("allow_subsystems") or []),
                "has_wireless": bool(w.get("wirelessbonus")),
                "bannedgrades": list(w.get("bannedgrades") or []),
                "required": w.get("required") or {"bioware": [], "cyberware": [], "metatype": [], "quality": []},
                "required_parent_names": list(w.get("required_parent_names") or []),
                "limbslot": w.get("limbslot"),
                "selectside": bool(w.get("selectside")),
                "source": w.get("source"),
                "page": w.get("page"),
            }
        )
    return {"grades": grades, "items": items}
