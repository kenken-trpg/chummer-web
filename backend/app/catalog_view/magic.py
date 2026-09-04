"""Magic and resonance: powers, spells, spirits, foci, and their echoes."""

from __future__ import annotations

from ..data_loader import CatalogDict


def section(raw: CatalogDict) -> dict:
    return {
        "powers": [
            {
                "id": p["id"],
                "name": p["name"],
                "points": p["points"],
                "levels": p["levels"],
                "maxlevels": p["maxlevels"],
                "extrapointcost": p["extrapointcost"],
                "source": p["source"],
                "page": p["page"],
                "select": p.get("select"),
                "required": list(p.get("required") or []),
                "adeptway": p.get("adeptway") or 0,
                "adeptwayrequires": list(p.get("adeptwayrequires") or []),
            }
            for p in raw.get("powers") or []
            if not p.get("hidden")
        ],
        "enhancements": [
            {
                "id": e["id"],
                "name": e["name"],
                "power": e.get("power"),
                "source": e.get("source"),
                "page": e.get("page"),
                "required": e.get("required") or {},
            }
            for e in raw.get("enhancements") or []
        ],
        "mentors": [
            {
                "id": m["id"],
                "name": m["name"],
                "source": m.get("source"),
                "page": m.get("page"),
                "advantage": m.get("advantage") or "",
            }
            for m in raw.get("mentors") or []
        ],
        "spells": [
            {
                "id": s["id"],
                "name": s["name"],
                "category": s.get("category"),
                "dv": s.get("dv"),
                "type": s.get("type"),
                "range": s.get("range"),
                "duration": s.get("duration"),
                "descriptor": s.get("descriptor"),
                "kind": s.get("kind") or "spell",
                "useskill": s.get("useskill") or "Spellcasting",
                "learnable": bool(s.get("learnable")),
                "required": [name for names in (s.get("required") or {}).values() for name in names],
                "source": s.get("source"),
                "page": s.get("page"),
            }
            for s in raw.get("spells") or []
        ],
        "traditions": [
            {
                "id": t["id"],
                "name": t["name"],
                "drain": t.get("drain") or "",
                "drain_attrs": list(t.get("drain_attrs") or []),
                "spirits": dict(t.get("spirits") or {}),
                "source": t.get("source"),
                "page": t.get("page"),
            }
            for t in raw.get("traditions") or []
        ],
        "spirits": [
            {
                "id": s["id"],
                "name": s["name"],
                "attributes": dict(s.get("attributes") or {}),
                "powers": list(s.get("powers") or []),
                "optionalpowers": list(s.get("optionalpowers") or []),
                "skills": list(s.get("skills") or []),
                "weaknesses": list(s.get("weaknesses") or []),
                "source": s.get("source"),
                "page": s.get("page"),
            }
            for s in raw.get("spirits") or []
        ],
        "complex_forms": [
            {
                "id": f["id"],
                "name": f["name"],
                "target": f.get("target") or "",
                "duration": f.get("duration") or "",
                "fv": f.get("fv") or "",
                "needs_extra": bool(f.get("needs_extra")),
                "required": [name for names in (f.get("required") or {}).values() for name in names],
                "source": f.get("source"),
                "page": f.get("page"),
            }
            for f in raw.get("complex_forms") or []
        ],
        "streams": [
            {
                "id": s["id"],
                "name": s["name"],
                "drain": s.get("drain") or "",
                "drain_attrs": list(s.get("drain_attrs") or []),
                "sprites": list(s.get("sprites") or []),
                "source": s.get("source"),
                "page": s.get("page"),
            }
            for s in raw.get("streams") or []
        ],
        "sprites": [
            {
                "id": s["id"],
                "name": s["name"],
                "attributes": dict(s.get("attributes") or {}),
                "powers": list(s.get("powers") or []),
                "skills": list(s.get("skills") or []),
                "source": s.get("source"),
                "page": s.get("page"),
            }
            for s in raw.get("sprites") or []
        ],
        "foci": [
            {
                "id": f["id"],
                "name": f["name"],
                "maxrating": f.get("maxrating") or 6,
                "cost": f.get("cost") or "",
                "effect": f.get("effect") or "",
                "formula": (
                    {
                        "id": (f.get("formula") or {}).get("id"),
                        "name": (f.get("formula") or {}).get("name"),
                        "cost": (f.get("formula") or {}).get("cost") or "",
                    }
                    if f.get("formula")
                    else None
                ),
                "source": f.get("source"),
                "page": f.get("page"),
            }
            for f in raw.get("foci") or []
        ],
        "qi_focus": raw.get("qi_focus"),
        "metamagics": [
            {
                "id": item["id"],
                "name": item["name"],
                "adept": bool(item.get("adept")),
                "magician": bool(item.get("magician")),
                "repeatable": bool(item.get("repeatable")),
                "required": [name for names in (item.get("required") or {}).values() for name in names],
                "source": item.get("source") or "",
                "page": item.get("page") or "",
            }
            for item in raw.get("metamagics") or []
        ],
        "magic_arts": [
            {
                "id": item["id"],
                "name": item["name"],
                "source": item.get("source") or "",
                "page": item.get("page") or "",
            }
            for item in raw.get("magic_arts") or []
        ],
        "echoes": [
            {
                "id": item["id"],
                "name": item["name"],
                "max_takes": item.get("max_takes"),
                "needs_extra": bool(item.get("needs_extra")),
                "source": item.get("source") or "",
                "page": item.get("page") or "",
            }
            for item in raw.get("echoes") or []
        ],
    }
