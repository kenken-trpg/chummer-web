"""Quality karma after chargen (SR5 p.107).

A positive quality taken in play costs twice its karma; buying a negative one
off costs twice the karma it gave. A negative quality picked up in play gives
nothing, and a positive one dropped is not refunded. `<doublecareer>False`
(the Ways, metagenic qualities, ...) takes the single price instead.

Chargen already sums every held quality at its table karma (`karma_from_q`);
this works out only the difference, measured against the qualities held when
the character entered career mode.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from ..lookups import _quality_by_id

CAREER_MULT = 2


def _mult(spec: dict[str, Any]) -> int:
    return CAREER_MULT if spec.get("double_career", True) is not False else 1


def career_quality_karma(
    qualities: list[dict[str, Any]],
    free_ids: list[str],
    baseline_ids: list[str],
) -> tuple[int, list[int | None], list[dict[str, Any]]]:
    """Return (extra karma, per-row career cost aligned to `qualities`, dropped rows).

    A row's career cost is None for a quality held since chargen (or free).
    """
    free = set(free_ids)
    base = Counter(baseline_ids)
    seen: Counter[str] = Counter()
    delta = 0
    costs: list[int | None] = []
    for spec in qualities:
        qid = spec["id"]
        if spec.get("onlyprioritygiven") or qid in free:
            costs.append(None)
            continue
        seen[qid] += 1
        if seen[qid] <= base[qid]:
            costs.append(None)
            continue
        karma = int(spec["karma"])
        if karma > 0:
            cost = karma * _mult(spec)
            delta += cost - karma
        else:
            # no karma for a negative picked up in play: undo the table gain
            cost = 0
            delta += -karma
        costs.append(cost)
    removed: list[dict[str, Any]] = []
    for qid, held in base.items():
        gone = held - seen[qid]
        if gone <= 0:
            continue
        gone_spec = _quality_by_id(qid)
        if not gone_spec:
            continue
        karma = int(gone_spec["karma"])
        if karma < 0:
            # the chargen gain stays; the buy-off is paid on top
            cost = -karma * _mult(gone_spec)
            delta += (cost + karma) * gone
        else:
            # spent karma stays spent
            cost = 0
            delta += karma * gone
        removed.extend(
            {"id": qid, "name": gone_spec["name"], "category": gone_spec.get("category") or "", "karma": cost}
            for _ in range(gone)
        )
    return delta, costs, removed
