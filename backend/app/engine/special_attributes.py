"""Free starting ratings, independent of the abilities a Talent permits."""

from __future__ import annotations

from typing import Any

from ..improvements import collect_effects
from .priority import talent_special


def special_attribute_floors(meta: dict[str, Any], talent: dict[str, Any], *, is_karma: bool = False) -> dict[str, int]:
    """Resolve species-enabled MAG/RES and replace a Talent's own starting rating.

    Chummer's SelectMetatypePriority assigns limits rather than adding its
    starting magic to the species minimum. Merely having a range in the XML
    does not enable an attribute; an explicit enableattribute bonus does.
    enabletab is deliberately excluded: showing a panel is not a grant.
    """
    nodes = [node for node in meta.get("bonus") or [] if node.get("tag") == "enableattribute"]
    enabled = collect_effects([(str(meta.get("name") or ""), nodes)])["enabled_tabs"]
    attrs = meta.get("attributes") or {}
    floors: dict[str, int] = {
        key: max(1, int((attrs.get(key) or {}).get("min") or 1)) for key in ("MAG", "RES") if key in enabled
    }
    key, start = talent_special(talent)
    if key:
        floors[key] = 1 if is_karma else max(1, start)
    return floors
