"""What a quality costs and whether it counts against a cap.

`<costdiscount>` moves the karma; `<metageniclimit>` and
`Quality.ContributeToLimit` decide which of the two 25-karma limits — and the
SURGE limit that replaces one of them — a quality answers to.
"""

from __future__ import annotations

from typing import Any

from ...improvements import _as_int
from ..requirements import requirement_tree_met


def apply_cost_discounts(qualities: list[dict[str, Any]], req_ctx: dict[str, Any]) -> list[dict[str, Any]]:
    """`<costdiscount>`: a quality's karma moves by `value` when its tree is
    met. As Chummer reads it, `value` is added to a positive quality's cost
    and taken from a negative one's: The Beast's Way 20 → 17 with an Animal
    Familiar (SG p.176), Blind −15 → −5 for the astrally aware (RF p.153),
    Astral Hazing −5 → −15 for the Awakened (RF p.119). Returns copies — the
    specs are the catalog's own dicts — with the table value on `karma_base`."""
    out: list[dict[str, Any]] = []
    for spec in qualities:
        discount = spec.get("cost_discount") or {}
        value = int(discount.get("value") or 0)
        if value and requirement_tree_met(discount.get("required_tree"), req_ctx):
            karma = int(spec["karma"])
            spec = {**spec, "karma_base": karma, "karma": karma + value if karma > 0 else karma - value}
        out.append(spec)
    return out


def surge_metagenic_limit(qualities: list[dict[str, Any]]) -> int:
    """The karma a SURGE Changeling may put into metagenic qualities (RF p.106),
    or 0 for anyone else — the largest `<metageniclimit>` among `qualities`."""
    limit = 0
    for spec in qualities:
        for node in spec.get("bonus") or []:
            if node.get("tag") == "metageniclimit":
                limit = max(limit, _as_int(node.get("value") or (node.get("fields") or {}).get("value")))
    return limit


def counts_toward_quality_limit(spec: dict[str, Any], surge: bool) -> bool:
    """Chummer's `Quality.ContributeToLimit`, for the 25-karma limits both ways.

    `<contributetolimit>False` keeps a quality out (Infected, the talents).
    So does being metagenic on a SURGE Changeling: those answer to the SURGE
    limit instead ("Positive Metagenic Qualities are free if you're a
    Changeling"), and counting them twice would refuse a legal 30-karma build.
    """
    if not spec.get("contributes_to_limit", True):
        return False
    return not (surge and spec.get("metagenic"))
