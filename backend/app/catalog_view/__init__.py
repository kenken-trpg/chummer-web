"""The catalog as the frontend sees it.

`data_loader.catalog()` is the full, loader-shaped Chummer data. This package
projects it down to what the UI actually needs — dropping fields the client
never reads, flattening `<bonus>` nodes to tags, and pre-resolving the pick
lists. One `GET /api/catalog` serves the whole app, so the projection is done
once here rather than per request in the components.

It used to be one 615-line dict literal. Each domain now owns its own
`section(raw) -> dict`, so adding a field to weapons means opening `gear.py`
rather than scrolling to line 260 of a file that also knows about spirits. The
split is by domain, not by size: the modules line up with `engine/`'s, so the
projection for a rule and the rule itself are found in the same place.

Nothing here decides *what* the sections contain — they are pure functions of
`raw`, and this file only says which ones there are.
"""

from __future__ import annotations

from ..data_loader import catalog
from . import chargen, gear, magic, matrix, vehicles, ware
from .chargen import CORE_METATYPES

__all__ = ["CORE_METATYPES", "public_catalog"]

#: Every section, in the order they are merged. A key must come from exactly
#: one of these; a duplicate would be silently won by the last one, so
#: `test_catalog_view.py` asserts they stay disjoint.
_SECTIONS = (chargen, ware, magic, gear, matrix, vehicles)


def public_catalog() -> dict:
    raw = catalog()
    out: dict = {}
    for module in _SECTIONS:
        out.update(module.section(raw))
    # Not domain data: the raw passthroughs the UI needs alongside everything
    # else. `translations` and `ui_strings` are the two-layer i18n described in
    # docs/i18n.md; `weapon_ranges` is a lookup table the sheet reads directly.
    out["weapon_ranges"] = raw.get("weapon_ranges") or {}
    out["translations"] = raw["translations"]
    out["ui_strings"] = raw["ui_strings"]
    return out
