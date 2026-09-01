"""Bonus-node -> effects pipeline.

``apply_bonus_nodes`` folds a list of parsed ``<bonus>`` child nodes into an
``effects`` dict; ``collect_effects`` runs it over every (source, nodes) pair.
Split into ``improvements/`` submodules; this module is the public barrel.
"""

from __future__ import annotations

from typing import Any

from ._common import ATTR_ALIASES, _as_int, substitute_rating
from .effects import (
    compact_limit_modifiers,
    compact_special_armor,
    empty_effects,
    special_armor_totals,
)
from .nodes import apply_bonus_nodes

__all__ = [
    "ATTR_ALIASES",
    "_as_int",
    "apply_bonus_nodes",
    "collect_effects",
    "compact_limit_modifiers",
    "compact_special_armor",
    "empty_effects",
    "limit_modifiers_from_nodes",
    "special_armor_from_nodes",
    "special_armor_totals",
    "substitute_rating",
]


def special_armor_from_nodes(nodes: list[dict[str, Any]], rating: int = 1) -> dict[str, Any] | None:
    effects = empty_effects()
    apply_bonus_nodes(substitute_rating(nodes, rating), effects, "")
    return compact_special_armor(effects)


def limit_modifiers_from_nodes(nodes: list[dict[str, Any]], rating: int = 1) -> list[dict[str, Any]]:
    effects = empty_effects()
    apply_bonus_nodes(substitute_rating(nodes, rating), effects, "")
    return compact_limit_modifiers(effects)


def collect_effects(sources: list[tuple[str, list[dict[str, Any]]]]) -> dict[str, Any]:
    effects = empty_effects()
    for source, nodes in sources:
        apply_bonus_nodes(nodes, effects, source)
    effects["enabled_tabs"] = sorted(effects["enabled_tabs"])
    return effects
