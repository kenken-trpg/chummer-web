"""Karma paid at chargen stays paid in career.

Chummer spends karma when something is bought and never gives it back when
the thing is deleted (`CharacterShared.RemoveSelectedObject` only removes
it; karma comes back only through a spending record's undo). This app works
karma out again from what is held on every pass, so without a record a
spirit dismissed in play, or a contact dropped, handed its chargen karma
back.

On the first career pass each kind of thing records what every row held
then cost (`CareerBaseline.chargen_karma`). From then on the kind costs what
was recorded, held or not, plus what the rows bought since cost in career.
A kind the record does not hold yet (a baseline from before it was kept, or
from before this kind was) is recorded the first time it is priced.
"""

from __future__ import annotations

from collections.abc import Iterable

from .context import Ctx


def kept_karma(ctx: Ctx, kind: str, rows: Iterable[tuple[str, int, int]]) -> int:
    """What `kind` costs in all: `rows` are (id, karma as priced now, karma
    it costs bought in career)."""
    rows = list(rows)
    baseline = ctx.state.career_baseline if ctx.career else None
    if baseline is None:
        return sum(now for _, now, _ in rows)
    if baseline.chargen_karma is None:
        baseline.chargen_karma = {}
    recorded = baseline.chargen_karma.get(kind)
    if recorded is None:
        baseline.chargen_karma[kind] = {row_id: int(now) for row_id, now, _ in rows}
        return sum(now for _, now, _ in rows)
    return sum(recorded.values()) + sum(career for row_id, _, career in rows if row_id not in recorded)


def bought_in_career(ctx: Ctx, kind: str, rows: list[dict]) -> list[dict]:
    """The rows of `kind` the record does not hold: bought in career."""
    baseline = ctx.state.career_baseline if ctx.career else None
    recorded = (baseline.chargen_karma or {}).get(kind) if baseline is not None else None
    if recorded is None:
        return []
    return [row for row in rows if str(row.get("id") or "") not in recorded]
