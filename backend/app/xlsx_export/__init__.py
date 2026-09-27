"""Write a character out as a .xlsx the キャラシテンプレート import reads back.

The template — 音の兔 様's 「［SR5］キャラシテンプレート」— is not ours to ship, and
the .xlsx it downloads as could not be filled in anyway: it is a Google Sheets
document, so every derived cell in it is a dead ``__xludf.DUMMYFUNCTION`` with
the last cached value beside it, and writing new inputs under those would leave
the sheet showing the previous character's numbers.

So this writes a workbook of its own with the template's sheet names and the
template's input addresses. A player can read it, and this app reads it back:
`state_to_xlsx` then `xlsx_to_state` is a round trip.

What the file does *not* carry is everything the template works out for itself —
the karma spent, the dice pools, the essence, the availability — because those
are this app's to derive and the sheet's own formulas are not ours to reproduce.
It is the character's inputs, in the template's shape.
"""

from __future__ import annotations

from ..data_loader import catalog
from ..models import CharacterState
from ..notices import Notice
from ..xlsx_import._common import (
    SHEET_BASICS,
    SHEET_CONTACTS,
    SHEET_GEAR,
    SHEET_KNOWLEDGE,
    SHEET_MAGIC,
    SHEET_SKILLS,
    SHEET_WARE,
)
from ._common import Limits
from ._workbook import Cells, write_workbook
from .basics import basics_sheet
from .contacts import contacts_sheet
from .gear import gear_sheet
from .magic import magic_sheet
from .skills import active_sheet, knowledge_sheet
from .ware import ware_sheet

__all__ = ["MARKER_SHEET", "state_to_xlsx", "xlsx_limits"]

#: The sheet the template keeps its own lookup tables on. The import requires it
#: by name to tell a character sheet apart from an unrelated spreadsheet, so a
#: file written here carries it — holding a line saying where the file came from
#: rather than a copy of the template's tables, which are not ours to reproduce.
MARKER_SHEET = "編集不可"
MARKER_CELL = "A1"
MARKER_TEXT = "chummer-web ([SR5] キャラシテンプレート 互換の書き出し)"


def _sheets(state: CharacterState, limits: Limits) -> tuple[list[tuple[str, Cells]], list[Notice]]:
    cat = catalog()
    gear, left = gear_sheet(state, cat, limits)
    return (
        [
            (SHEET_BASICS, basics_sheet(state, cat, limits)),
            (SHEET_SKILLS, active_sheet(state, cat)),
            (SHEET_KNOWLEDGE, knowledge_sheet(state, cat, limits)),
            (SHEET_MAGIC, magic_sheet(state, cat, limits)),
            (SHEET_WARE, ware_sheet(state, cat, limits)),
            (SHEET_GEAR, gear),
            (SHEET_CONTACTS, contacts_sheet(state, limits)),
            (MARKER_SHEET, {MARKER_CELL: MARKER_TEXT}),
        ],
        left,
    )


def state_to_xlsx(state: CharacterState) -> bytes:
    """`state` as a .xlsx in the template's shape."""
    limits = Limits()
    sheets, _left = _sheets(state, limits)
    return write_workbook(sheets)


def xlsx_limits(state: CharacterState) -> list[Notice]:
    """What the template has no room and no cell for.

    Half of what a round trip through this file costs, and the half only the
    writing knows: a row past the end of a fixed block, and a value no dropdown
    on the sheet can hold. `check.roundtrip_differences` reports it alongside
    what it finds by actually reading the file back.
    """
    limits = Limits()
    _written, left = _sheets(state, limits)
    return limits.notices + left
