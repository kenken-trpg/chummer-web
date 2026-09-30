"""The 成長ログ sheet: the reward ledger, back in the template's shape.

The import puts the date in front of the note because this app's ledger has one
label and no date field. Writing it back splits a leading date off again, so a
round trip through this app leaves the sheet's two columns where they were. A
label that does not start with a date goes into 備考 whole, which is what a row
typed here rather than imported looks like.

What is *not* written is 経過日数: the sheet keeps it for its own lifestyle
arithmetic, which this app does from the lifestyle instead.
"""

from __future__ import annotations

import re

from ..models import CharacterState
from ..notices import ui
from ..xlsx_import.growth import (
    LOG_FIRST_ROW,
    LOG_LAST_ROW,
    REWARD_DATE,
    REWARD_KARMA,
    REWARD_NOTE,
    REWARD_NUYEN,
)
from ._common import Limits
from ._workbook import Cells

#: A label the import wrote: an ISO date, then the note it was read with.
_DATED = re.compile(r"^(\d{4}-\d{2}-\d{2})(?:\s+(.*))?$")


def growth_sheet(state: CharacterState, limits: Limits) -> Cells:
    """The 成長ログ sheet for `state`, earnings first and write-offs after."""
    cells: Cells = {}
    rows = [*(state.reward_log or []), *(state.expense_log or [])]
    if not rows:
        return cells
    room = LOG_LAST_ROW - LOG_FIRST_ROW + 1
    for offset, entry in enumerate(limits.fit(rows, room, ui("sheet.rewardLog"))):
        row = LOG_FIRST_ROW + offset
        if entry.nuyen:
            cells[f"{REWARD_NUYEN}{row}"] = entry.nuyen
        if entry.karma:
            cells[f"{REWARD_KARMA}{row}"] = entry.karma
        dated = _DATED.match(entry.label or "")
        if dated:
            cells[f"{REWARD_DATE}{row}"] = dated.group(1)
            if dated.group(2):
                cells[f"{REWARD_NOTE}{row}"] = dated.group(2)
        elif entry.label:
            cells[f"{REWARD_NOTE}{row}"] = entry.label
    return cells


__all__ = ["growth_sheet"]
