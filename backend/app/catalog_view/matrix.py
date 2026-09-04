"""Matrix devices and the software that runs on them."""

from __future__ import annotations

from ..data_loader import CatalogDict
from ..engine import gear_extra_options


def section(raw: CatalogDict) -> dict:
    return {
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
    }
