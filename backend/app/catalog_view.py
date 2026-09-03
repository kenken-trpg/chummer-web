"""The catalog as the frontend sees it.

`data_loader.catalog()` is the full, loader-shaped Chummer data. This module
projects it down to what the UI actually needs — dropping fields the client
never reads, flattening `<bonus>` nodes to tags, and pre-resolving the pick
lists. One `GET /api/catalog` serves the whole app, so the projection is done
once here rather than per request in the components.
"""

from __future__ import annotations

from .data_loader import catalog, drug_effect_summary
from .engine import (
    all_talent_options,
    gear_extra_options,
    is_way_quality,
    priority_value,
    talent_options,
)

CORE_METATYPES = {"Human", "Elf", "Dwarf", "Ork", "Troll"}


def public_catalog() -> dict:
    raw = catalog()
    qualities = [
        {
            "id": q["id"],
            "name": q["name"],
            "karma": q["karma"],
            "category": q["category"],
            "source": q["source"],
            "page": q["page"],
            "bonus_tags": [n["tag"] for n in q.get("bonus") or []],
            "forbidden_qualities": list((q.get("forbidden") or {}).get("quality") or []),
            "is_way": is_way_quality(q["name"]),
            "metagenic": bool(q.get("metagenic")),
            "needs_extra": bool(q.get("needs_extra")),
            "extra_kind": q.get("extra_kind") or "",
            "select_options": list(q.get("select_options") or []),
            "spirit_options": list(q.get("spirit_options") or []),
            "expertise_skill": q.get("expertise_skill") or "",
            "max_takes": q.get("max_takes"),
            "required_tree": q.get("required_tree") or [],
            "forbidden_tree": q.get("forbidden_tree") or [],
        }
        for q in raw["qualities"]
        if not q.get("onlyprioritygiven")
    ]
    table: dict[str, dict[str, dict]] = {}
    for cat in ("Heritage", "Attributes", "Talent", "Skills", "Resources"):
        table[cat] = {}
        for letter in "ABCDE":
            row = priority_value(cat, letter)
            mets = [m for m in (row.get("metatypes") or []) if m["name"] in CORE_METATYPES]
            table[cat][letter] = {
                "name": row.get("name"),
                "attribute_points": row.get("attribute_points"),
                "skill_points": row.get("skill_points"),
                "skill_group_points": row.get("skill_group_points"),
                "nuyen": row.get("nuyen"),
                "metatypes": mets,
                "talents": talent_options(letter) if cat == "Talent" else row.get("talents") or [],
            }
    return {
        "metatypes": raw["metatypes"],
        "skills": raw["skills"],
        "qualities": qualities,
        "cyberware": _public_ware(raw.get("cyberware") or {"grades": [], "items": []}),
        "bioware": _public_ware(raw.get("bioware") or {"grades": [], "items": []}),
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
        "armor": [
            {
                "id": a["id"],
                "name": a["name"],
                "category": a.get("category") or "Armor",
                "armor": a.get("armor") or "0",
                "armorcapacity": a.get("armorcapacity") or "",
                "avail": a.get("avail") or "",
                "cost": a.get("cost") or "0",
                "minrating": int(a.get("minrating") or 0),
                "maxrating": int(a.get("maxrating") or 0),
                "additive": bool(a.get("additive")),
                "addmodcategories": list(a.get("addmodcategories") or []),
                "has_wireless": bool(a.get("wirelessbonus")),
                "source": a.get("source") or "",
                "page": a.get("page") or "",
            }
            for a in raw.get("armor") or []
        ],
        "armor_mods": [
            {
                "id": a["id"],
                "name": a["name"],
                "category": a.get("category") or "General",
                "armor": a.get("armor") or "0",
                "armorcapacity": a.get("armorcapacity") or "",
                "avail": a.get("avail") or "",
                "cost": a.get("cost") or "0",
                "minrating": int(a.get("minrating") or 0),
                "maxrating": int(a.get("maxrating") or 0),
                "purchasable": bool(a.get("purchasable")),
                "unique": a.get("unique") or "",
                "required_names": list(a.get("required_names") or []),
                "required_mods": list(a.get("required_mods") or []),
                "has_wireless": bool(a.get("wirelessbonus")),
                "source": a.get("source") or "",
                "page": a.get("page") or "",
            }
            for a in raw.get("armor_mods") or []
            if a.get("purchasable")
        ],
        "weapons": [
            {
                "id": w["id"],
                "name": w["name"],
                "category": w.get("category") or "",
                "type": w.get("type") or "",
                "weapon_type": w.get("weapon_type") or "",
                "accuracy": w.get("accuracy") or "",
                "reach": w.get("reach") or "",
                "damage": w.get("damage") or "",
                "ap": w.get("ap") or "",
                "mode": w.get("mode") or "",
                "ammo": w.get("ammo") or "",
                "conceal": w.get("conceal") or "",
                "range": w.get("range") or "",
                "alt_range": w.get("alt_range") or "",
                "mounts": list(w.get("mounts") or []),
                "avail": w.get("avail") or "",
                "cost": w.get("cost") or "0",
                "source": w.get("source") or "",
                "page": w.get("page") or "",
                "from_gear": bool(w.get("from_gear")),
                "add_gear_id": w.get("add_gear_id") or "",
            }
            for w in raw.get("weapons") or []
            if not w.get("hidden")
        ],
        "weapon_accessories": [
            {
                "id": a["id"],
                "name": a["name"],
                "mounts": list(a.get("mounts") or []),
                "avail": a.get("avail") or "",
                "cost": a.get("cost") or "0",
                "purchasable": bool(a.get("purchasable")),
                "accuracy": a.get("accuracy") or "",
                "rc": a.get("rc") or "",
                "minrating": int(a.get("minrating") or 0),
                "maxrating": int(a.get("maxrating") or 0),
                "required": a.get("required") or {},
                "forbidden": a.get("forbidden") or {},
                "specialmodification": bool(a.get("specialmodification")),
                "special_modification_cost": int(a.get("special_modification_cost") or 0),
                "source": a.get("source") or "",
                "page": a.get("page") or "",
            }
            for a in raw.get("weapon_accessories") or []
        ],
        "commlinks": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "Commlinks",
                "cost": c.get("cost") or "0",
                "avail": c.get("avail") or "",
                "minrating": int(c.get("minrating") or 0),
                "maxrating": int(c.get("maxrating") or 0),
                "devicerating": c.get("devicerating") or "0",
                "dataprocessing": c.get("dataprocessing") or "0",
                "firewall": c.get("firewall") or "0",
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("commlinks") or []
        ],
        "cyberdecks": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "Cyberdecks",
                "cost": c.get("cost") or "0",
                "avail": c.get("avail") or "",
                "minrating": int(c.get("minrating") or 0),
                "maxrating": int(c.get("maxrating") or 0),
                "devicerating": c.get("devicerating") or "0",
                "attack": c.get("attack") or "0",
                "sleaze": c.get("sleaze") or "0",
                "dataprocessing": c.get("dataprocessing") or "0",
                "firewall": c.get("firewall") or "0",
                "attributearray": c.get("attributearray") or "",
                "programs": c.get("programs") or "0",
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("cyberdecks") or []
        ],
        "rccs": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "Rigger Command Consoles",
                "cost": c.get("cost") or "0",
                "avail": c.get("avail") or "",
                "minrating": int(c.get("minrating") or 0),
                "maxrating": int(c.get("maxrating") or 0),
                "devicerating": c.get("devicerating") or "0",
                "dataprocessing": c.get("dataprocessing") or "0",
                "firewall": c.get("firewall") or "0",
                "programs": c.get("programs") or "0",
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("rccs") or []
        ],
        "optics": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "",
                "cost": c.get("cost") or "0",
                "avail": c.get("avail") or "",
                "minrating": int(c.get("minrating") or 0),
                "maxrating": int(c.get("maxrating") or 0),
                "capacity": c.get("capacity") or "",
                "plugin": bool(c.get("plugin")),
                "requireparent": bool(c.get("requireparent")),
                "addoncategories": list(c.get("addoncategories") or []),
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("optics") or []
        ],
        "programs": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "",
                "cost": c.get("cost") or "0",
                "avail": c.get("avail") or "",
                "minrating": int(c.get("minrating") or 0),
                "maxrating": int(c.get("maxrating") or 0),
                "requireparent": True,
                "program_host": c.get("program_host") or "cyberdecks",
                "needs_extra": bool(c.get("needs_extra")),
                "extra_kind": c.get("extra_kind") or "",
                "extra_options": gear_extra_options(c, raw.get("skills")),
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("programs") or []
        ],
        "apps": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "",
                "cost": c.get("cost") or "0",
                "avail": c.get("avail") or "",
                "minrating": int(c.get("minrating") or 0),
                "maxrating": int(c.get("maxrating") or 0),
                "requireparent": True,
                "needs_extra": bool(c.get("needs_extra")),
                "extra_kind": c.get("extra_kind") or "",
                "extra_options": gear_extra_options(c, raw.get("skills")),
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("apps") or []
        ],
        "sensors": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "",
                "cost": c.get("cost") or "0",
                "avail": c.get("avail") or "",
                "minrating": int(c.get("minrating") or 0),
                "maxrating": int(c.get("maxrating") or 0),
                "capacity": c.get("capacity") or "",
                "plugin": bool(c.get("plugin")),
                "requireparent": bool(c.get("requireparent")),
                "addoncategories": list(c.get("addoncategories") or []),
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("sensors") or []
        ],
        "gear": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "",
                "cost": c.get("cost") or "0",
                "avail": c.get("avail") or "",
                "minrating": int(c.get("minrating") or 0),
                "maxrating": int(c.get("maxrating") or 0),
                "capacity": c.get("capacity") or "",
                "plugin": bool(c.get("plugin")),
                "requireparent": bool(c.get("requireparent")),
                "addoncategories": list(c.get("addoncategories") or []),
                "required_names": list(c.get("required_names") or []),
                "required_categories": list(c.get("required_categories") or []),
                "ammo_weapon_types": list(c.get("ammo_weapon_types") or []),
                "costfor": int(c.get("costfor") or 0),
                "weapon_details": c.get("weapon_details") or "",
                "add_weapon": c.get("add_weapon") or "",
                "add_weapon_id": c.get("add_weapon_id") or "",
                "needs_extra": bool(c.get("needs_extra")),
                "extra_kind": c.get("extra_kind") or "",
                "extra_options": gear_extra_options(c, raw.get("skills")),
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("gear") or []
        ],
        "drones": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "",
                "handling": c.get("handling") or "",
                "speed": c.get("speed") or "",
                "accel": c.get("accel") or "",
                "body": c.get("body") or "",
                "armor": c.get("armor") or "",
                "pilot": c.get("pilot") or "",
                "sensor": c.get("sensor") or "",
                "seats": c.get("seats") or "",
                "avail": c.get("avail") or "",
                "cost": c.get("cost") or "0",
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("drones") or []
        ],
        "vehicles": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "",
                "handling": c.get("handling") or "",
                "speed": c.get("speed") or "",
                "accel": c.get("accel") or "",
                "body": c.get("body") or "",
                "armor": c.get("armor") or "",
                "pilot": c.get("pilot") or "",
                "sensor": c.get("sensor") or "",
                "seats": c.get("seats") or "",
                "avail": c.get("avail") or "",
                "cost": c.get("cost") or "0",
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("vehicles") or []
        ],
        "vehicle_mods": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "",
                "cost": c.get("cost") or "0",
                "slots": c.get("slots") or "0",
                "avail": c.get("avail") or "",
                "minrating": int(c.get("minrating") or 0),
                "maxrating": int(c.get("maxrating") or 0),
                "purchasable": bool(c.get("purchasable")),
                "required": c.get("required") or {},
                "forbidden": c.get("forbidden") or {},
                "capacity": c.get("capacity") or "",
                "subsystems": list(c.get("subsystems") or []),
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("vehicle_mods") or []
            if c.get("purchasable")
        ],
        "weapon_mounts": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "",
                "cost": c.get("cost") or "0",
                "slots": c.get("slots") or "0",
                "avail": c.get("avail") or "",
                "required": c.get("required") or {},
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("weapon_mounts") or []
        ],
        "lifestyles": [
            {
                "id": ls["id"],
                "name": ls["name"],
                "cost": int(ls.get("cost") or 0),
                "dice": int(ls.get("dice") or 0),
                "lp": int(ls.get("lp") or 0),
                "multiplier": int(ls.get("multiplier") or 100),
                "increment": ls.get("increment") or "month",
                "freegrids": [
                    {"name": str(g.get("name") or ""), "select": str(g.get("select") or "")}
                    for g in (ls.get("freegrids") or [])
                ],
                "source": ls.get("source") or "",
                "page": ls.get("page") or "",
            }
            for ls in raw.get("lifestyles") or []
        ],
        "lifestyle_qualities": [
            {
                "id": q["id"],
                "name": q["name"],
                "category": q.get("category") or "",
                "lp": int(q.get("lp") or 0),
                "cost": int(q.get("cost") or 0),
                "multiplier": int(q.get("multiplier") or 0),
                "allowed": list(q.get("allowed") or []),
                "allow_multiple": bool(q.get("allow_multiple")),
                "needs_extra": bool(q.get("needs_extra")),
                "source": q.get("source") or "",
                "page": q.get("page") or "",
            }
            for q in raw.get("lifestyle_qualities") or []
        ],
        "drugs": [
            {
                "id": item["id"],
                "name": item["name"],
                "category": item.get("category") or "",
                "cost": item.get("cost") or "0",
                "avail": item.get("avail") or "",
                "addoncategories": list(item.get("addoncategories") or []),
                "speed": item.get("drug_speed") or "",
                "vectors": list(item.get("drug_vectors") or []),
                "duration": item.get("drug_duration") or "",
                "effect": drug_effect_summary(item.get("drug_bonus") or []),
                "source": item.get("source") or "",
                "page": item.get("page") or "",
            }
            for item in raw.get("drugs") or []
        ],
        "drug_grades": [
            {
                "id": item["id"],
                "name": item["name"],
                "cost": item.get("cost") or "0",
                "avail": item.get("avail") or "",
                "required_categories": list(item.get("required_categories") or []),
                "source": item.get("source") or "",
                "page": item.get("page") or "",
            }
            for item in raw.get("drug_grades") or []
        ],
        "martial_arts": [
            {
                "id": art["id"],
                "name": art["name"],
                "cost": int(art.get("cost") or 7),
                "techniques": list(art.get("techniques") or []),
                "source": art.get("source") or "",
                "page": art.get("page") or "",
                "is_quality": bool(art.get("is_quality")),
                "all_techniques": bool(art.get("all_techniques")),
                "spec_options": [
                    {"skill": skill, "spec": spec}
                    for node in (art.get("bonus") or [])
                    if node.get("tag") == "addskillspecializationoption"
                    for skill in [str((node.get("fields") or {}).get("skill") or "").strip()]
                    for spec in [str((node.get("fields") or {}).get("spec") or "").strip()]
                    if skill and spec
                ],
            }
            for art in raw.get("martial_arts") or []
            if not art.get("is_quality")
        ],
        "martial_art_techniques": [
            {
                "id": tech["id"],
                "name": tech["name"],
                "source": tech.get("source") or "",
                "page": tech.get("page") or "",
            }
            for tech in raw.get("martial_art_techniques") or []
        ],
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
        "priority_table": table,
        "karma_talents": [
            {
                "name": t["name"],
                "label": t.get("label") or t["name"],
                "magic": int(t.get("magic") or 0),
                "resonance": int(t.get("resonance") or 0),
            }
            for t in all_talent_options()
        ],
        "weapon_ranges": raw.get("weapon_ranges") or {},
        "translations": raw["translations"],
        "ui_strings": raw["ui_strings"],
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
