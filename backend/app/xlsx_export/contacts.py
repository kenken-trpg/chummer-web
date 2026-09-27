"""The コンタクト／その他カルマ消費 sheet.

Nothing here needs translating: a contact is the player's own invention. The one
thing to get right is which column a rating goes in — the sheet keeps the total
apart from the part something else granted, and the import reads both, so a
granted point written into the total alone would be billed for.
"""

from __future__ import annotations

from ..models import CharacterState
from ..notices import ui
from ..xlsx_import.contacts import (
    COLUMN_CONNECTION,
    COLUMN_FREE_CONNECTION,
    COLUMN_FREE_LOYALTY,
    COLUMN_LOYALTY,
    CONTACT_NAME,
    CONTACT_ROWS,
)
from ._common import Limits
from ._workbook import Cells


def contacts_sheet(state: CharacterState, limits: Limits) -> Cells:
    """The コンタクト／その他カルマ消費 sheet for `state`.

    その他カルマ消費 is left empty: it is the template's place for karma this app
    has nothing to spend on, so there is never anything of ours to put there.
    """
    cells: Cells = {}
    contacts = list(state.contacts or [])
    for row, contact in zip(
        CONTACT_ROWS, limits.fit(contacts, len(CONTACT_ROWS), ui("engine.kind.contact")), strict=False
    ):
        cells[f"{CONTACT_NAME}{row}"] = contact.name
        cells[f"{COLUMN_CONNECTION}{row}"] = contact.connection
        cells[f"{COLUMN_LOYALTY}{row}"] = contact.loyalty
        if contact.free_connection:
            cells[f"{COLUMN_FREE_CONNECTION}{row}"] = contact.free_connection
        if contact.free_loyalty:
            cells[f"{COLUMN_FREE_LOYALTY}{row}"] = contact.free_loyalty
    return cells


__all__ = ["contacts_sheet"]
