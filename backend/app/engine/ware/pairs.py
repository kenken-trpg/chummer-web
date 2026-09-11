"""`<pairbonus>`: what a piece of ware adds once it has a partner.

Two lower cyberlimbs give +1 physical box, fins on both hands give +1
Swimming, callus on hands and feet stack their DV — none of it is on either
item's own `<bonus>`. Chummer (``Cyberware.Create``) decides it at install
time: counting the earlier ware this one pairs with (its own name plus
`<pairinclude>`, with the same Extra), an odd count means this item completes
a pair and brings the bonus. Replayed over the install order that is one
bonus per pair, which is what this module hands back as extra bonus sources.
"""

from __future__ import annotations

from typing import Any

from ...improvements import substitute_rating
from ..lookups import _ware_by_id


def _pair_nodes(nodes: list[dict[str, Any]], extra: str) -> list[dict[str, Any]]:
    """Cyberlimb Optimization pairs on its picked skill, and its pair bonus is
    a `<selectskill>` that upstream means as *that* skill (CF p.87) — so it is
    rewritten into the fixed `<specificskill>` the effects pass understands."""
    out: list[dict[str, Any]] = []
    for node in nodes:
        if node.get("tag") != "selectskill":
            out.append(node)
            continue
        if not extra:
            continue
        fields = node.get("fields") or {}
        out.append(
            {
                "tag": "specificskill",
                "fields": {"name": extra, "bonus": fields.get("val") or fields.get("bonus") or node.get("value")},
            }
        )
    return out


def pair_bonus_sources(
    installed: list[tuple[str, dict[str, Any]]],
    extras: dict[str, str] | None = None,
) -> list[tuple[str, list[dict[str, Any]]]]:
    """``(name, nodes)`` bonus sources for every completed pair.

    `installed` is ``(kind, item)`` in install order — the character's own
    ware only, never what sits in a vehicle mod. `extras` overrides an item's
    Extra by install id (the skill a Cyberlimb Optimization was pointed at).
    """
    extras = extras or {}
    seen: list[tuple[dict[str, Any], dict[str, Any]]] = []
    sources: list[tuple[str, list[dict[str, Any]]]] = []
    for kind, item in installed:
        spec = _ware_by_id(kind, str(item.get("ware_id") or ""))
        if not spec:
            continue
        item = {**item, "extra": extras.get(str(item.get("id") or ""), item.get("extra") or "")}
        pair_nodes = list(spec.get("pairbonus") or [])
        if pair_nodes:
            name = str(spec.get("name") or "")
            include = {name, *(spec.get("pairinclude") or [])}
            partners = [
                other for other, _ in seen if other.get("name") in include and other.get("extra") == item["extra"]
            ]
            side = str(item.get("side") or "")
            if side and include == {name}:
                # a left pairs only with a right: same-side partners cancel out
                count = sum(1 if str(other.get("side") or "") != side else -1 for other in partners)
            else:
                count = len(partners)
            if count > 0 and count % 2 == 1:
                nodes = _pair_nodes(pair_nodes, str(item["extra"] or ""))
                if nodes:
                    sources.append((name, nodes))
        seen.append((item, spec))
    return sources


def apply_wireless_pairs(installed: list[tuple[str, dict[str, Any]]]) -> None:
    """`<wirelesspairbonus>`: what two wireless implants do together.

    Wired Reflexes and Reaction Enhancers (SR5 p.459/461) name each other in
    `<wirelesspairinclude>`; with both installed and both wireless, each one's
    bonus is *replaced* (``mode="replace"``) by a version whose REA (and
    initiative) moves from precedence 0 — only the best counts — to 1, which
    stacks. Rewrites ``item["bonus"]`` in place so every later reader (the
    effects pass, the chargen cap) sees the paired version.
    """
    wireless = [(kind, item) for kind, item in installed if item.get("wireless")]
    for kind, item in wireless:
        spec = _ware_by_id(kind, str(item.get("ware_id") or ""))
        if not spec or not spec.get("wirelesspairbonus"):
            continue
        partners = set(spec.get("wirelesspairinclude") or [])
        if not any(other is not item and other.get("name") in partners for _, other in wireless):
            continue
        rating = int(item.get("rating") or 1)
        paired = substitute_rating(list(spec["wirelesspairbonus"]), rating)
        if spec.get("wirelesspairmode") == "replace":
            item["bonus"] = paired + substitute_rating(list(spec.get("wirelessbonus") or []), rating)
        else:
            item["bonus"] = list(item.get("bonus") or []) + paired
        item["wireless_paired"] = True
