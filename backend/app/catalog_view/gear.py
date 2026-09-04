"""Things bought with nuyen: armor, weapons, general gear, drugs, lifestyles."""

from __future__ import annotations

from ..data_loader import CatalogDict, drug_effect_summary
from ..engine import gear_extra_options


def section(raw: CatalogDict) -> dict:
    return {
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
    }
