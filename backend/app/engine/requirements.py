"""Chummer ``<required>`` / ``<forbidden>`` requirement-tree evaluation.

``requirement_tree_met`` walks a parsed requirement tree against a context dict
(qualities, metatypes, powers, skills, essence, ...) that each caller builds for
its own subsystem. Depends on nothing else in the engine, so qualities, martial
arts and initiation can all import from here.
"""

from __future__ import annotations

from typing import Any


def _pool_rating(pool: dict[str, int], name: str) -> int:
    best = int(pool.get(name) or 0)
    prefix = f"{name} ("
    for key, value in pool.items():
        if str(key).startswith(prefix):
            best = max(best, int(value or 0))
    return best


#: tags met when the node's name is in the context set every caller builds
_IN_CONTEXT = {
    "quality": "qualities",
    "metatype": "metatypes",
    "metatypecategory": "metatype_categories",
    "power": "powers",
    "cyberware": "cyberware",
    "bioware": "bioware",
    "spell": "spells",
}
#: the same, for sets only some callers build; a missing one is empty.
#: `critterpower`: Soul Swallower needs Essence Drain (DTR p.164); an Infected
#: optional power is forbidden to whoever has it already (RF p.126)
_IN_OPTIONAL_CONTEXT = {
    "critterpower": "critter_powers",
    "metamagic": "metamagics",
}


def _requirement_item_met(node: dict[str, Any], ctx: dict[str, Any]) -> bool:
    tag = node.get("tag") or ""
    children = list(node.get("children") or [])
    if tag == "oneof":
        return any(_requirement_item_met(child, ctx) for child in children) if children else True
    if tag in {"allof", "group"}:
        return all(_requirement_item_met(child, ctx) for child in children) if children else True
    name = str(node.get("name") or "")
    if tag in _IN_CONTEXT:
        return name in ctx[_IN_CONTEXT[tag]]
    if tag in _IN_OPTIONAL_CONTEXT:
        return name in (ctx.get(_IN_OPTIONAL_CONTEXT[tag]) or set())
    if tag in {"magenabled", "resenabled"}:
        return bool(ctx[tag])
    if tag == "art":
        return bool(ctx.get("ignore_art")) or name in (ctx.get("arts") or set())
    if tag == "tradition":
        return bool(name == ctx["tradition"])
    if tag == "skill":
        rating = int(node.get("val") or 1)
        pool = ctx["knowledge"] if str(node.get("type") or "").lower() == "knowledge" else ctx["skills"]
        return _pool_rating(pool, name) >= rating
    if tag == "ess":
        value = float(node.get("value") or 0)
        if value < 0:
            return float(ctx["ess_lost"]) + 1e-9 >= abs(value)
        return float(ctx["essence"]) + 1e-9 >= value
    # `gameplayoption` and anything unknown: not met
    return False


def requirement_tree_met(tree: list[dict[str, Any]] | None, ctx: dict[str, Any]) -> bool:
    nodes = list(tree or [])
    if not nodes:
        return True
    return all(_requirement_item_met(node, ctx) for node in nodes)
