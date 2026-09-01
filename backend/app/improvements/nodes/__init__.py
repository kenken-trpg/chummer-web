"""``apply_bonus_nodes``: the per-node loop + ordered domain dispatch.

Each ``nodes/<domain>.py`` owns a slice of the old ``if/elif tag`` chain as
``apply(tag, node, fields, effects, source) -> bool``; this module tries them
in order (no tag is claimed by two domains, so order across domains is
irrelevant). Completeness is guarded by
``tests/test_improvements_nodes.py``.
"""

from __future__ import annotations

from typing import Any

from .._common import IMPLEMENTED, SILENT_TAGS
from . import magic, skills, social, stats

_DOMAINS = (stats.apply, skills.apply, magic.apply, social.apply)


def apply_bonus_nodes(nodes: list[dict[str, Any]], effects: dict[str, Any], source: str) -> None:
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
