"""``apply_bonus_nodes``: the per-node loop + ordered domain dispatch.

Each ``nodes/<domain>.py`` owns a slice of the old ``if/elif tag`` chain as
``apply(tag, node, fields, effects, source) -> bool``; this module tries them
in order (no tag is claimed by two domains, so order across domains is
irrelevant). Completeness is guarded by
``tests/test_improvements_nodes.py``.
"""

from __future__ import annotations

from typing import Any, cast

from .._common import IMPLEMENTED, SILENT_TAGS
from ..effects import EffectsDict
from . import magic, skills, social, stats

_DOMAINS = (stats.apply, skills.apply, magic.apply, social.apply)


#: The values the sidebar explains term by term (`stat_sources`).
SOURCED_KEYS = (
    "limit_physical",
    "limit_mental",
    "limit_social",
    "cm_physical",
    "cm_stun",
    "initiative",
    "initiative_dice",
)


def _sourced_values(effects: EffectsDict) -> dict[str, int]:
    """Each sourced key as its plain bucket plus every value parked in a
    precedence group — what one source added, before stacking is resolved."""
    groups = effects.get("precedence_bonus") or {}
    plain = cast(dict[str, Any], effects)
    return {
        key: int(plain.get(key) or 0) + sum(sum(values) for values in (groups.get(key) or {}).values())
        for key in SOURCED_KEYS
    }


def apply_bonus_nodes(nodes: list[dict[str, Any]], effects: EffectsDict, source: str) -> None:
    before = _sourced_values(effects) if source else None
    _apply_nodes(nodes, effects, source)
    if before is None:
        return
    for key, value in _sourced_values(effects).items():
        delta = value - before[key]
        if not delta:
            continue
        rows = effects.setdefault("stat_sources", {}).setdefault(key, [])
        same = next((row for row in rows if row["source"] == source), None)
        if same:
            same["value"] += delta
        else:
            rows.append({"source": source, "value": delta})


def _apply_nodes(nodes: list[dict[str, Any]], effects: EffectsDict, source: str) -> None:
    for node in nodes:
        tag = node.get("tag", "")
        if tag not in IMPLEMENTED:
            if tag not in SILENT_TAGS:
                effects["unimplemented"].append({"source": source, "tag": tag})
            continue
        fields = node.get("fields") or {}
        for _domain in _DOMAINS:
            if _domain(tag, node, fields, effects, source):
                break
