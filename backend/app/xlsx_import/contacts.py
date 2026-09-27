"""The コンタクト／その他カルマ消費 sheet.

The easiest sheet in the template to read, and the only one that needs no name
matching at all: a contact is the player's own invention, so the name goes
through as written, the way the knowledge skills do.

What it does have is three columns per rating, because the sheet keeps track of
where each point came from: contact points (E/G), karma (I/K) and その他修正
(M/O) for what something else granted. The totals it adds up in Q/S are what
this app stores as the contact's ratings, with the granted part recorded
separately so it is not billed for.

Under the contacts is a small その他カルマ消費 block, for karma the sheet has no
other place for. This app has nothing to spend it on, so each row is reported
rather than folded into a number that would then be wrong.
"""

from __future__ import annotations

import re
import uuid
from typing import Any

from ..notices import Notice, notice
from ._common import cell_int

#: Rows 4–23 hold one contact each.
CONTACT_ROWS = range(4, 24)
CONTACT_NAME = "A"
#: The total the sheet adds up, and the part of it something else granted.
COLUMN_CONNECTION = "Q"
COLUMN_LOYALTY = "S"
COLUMN_FREE_CONNECTION = "M"
COLUMN_FREE_LOYALTY = "O"

#: The block under the contacts, and the rows of it: a name in A, karma in F.
KARMA_HEADING = "その他カルマ消費"
KARMA_OFFSET = 2
KARMA_COUNT = 10
KARMA_NAME = "A"
KARMA_SPENT = "F"


def _import_contacts(cells: dict[str, str], st: dict[str, Any]) -> None:
    contacts: list[dict[str, Any]] = []
    for row in CONTACT_ROWS:
        name = (cells.get(f"{CONTACT_NAME}{row}") or "").strip()
        if not name:
            continue
        free_connection = cell_int(cells.get(f"{COLUMN_FREE_CONNECTION}{row}"))
        free_loyalty = cell_int(cells.get(f"{COLUMN_FREE_LOYALTY}{row}"))
        contacts.append(
            {
                "id": str(uuid.uuid4()),
                "name": name,
                # A contact with nothing in any column but a name is still a
                # contact, at the 1/1 the rules start it at.
                "connection": max(1, cell_int(cells.get(f"{COLUMN_CONNECTION}{row}"))),
                "loyalty": max(1, cell_int(cells.get(f"{COLUMN_LOYALTY}{row}"))),
                "free_connection": free_connection,
                "free_loyalty": free_loyalty,
            }
        )
    if contacts:
        st["contacts"] = contacts


def _report_other_karma(cells: dict[str, str], warn: list[Notice]) -> None:
    """Karma the sheet spent on something this app does not keep."""
    heading = next(
        (int(ref[1:]) for ref, text in cells.items() if re.fullmatch(r"A\d+", ref) and text.strip() == KARMA_HEADING),
        None,
    )
    if heading is None:
        return
    for row in range(heading + KARMA_OFFSET, heading + KARMA_OFFSET + KARMA_COUNT):
        name = (cells.get(f"{KARMA_NAME}{row}") or "").strip()
        karma = cell_int(cells.get(f"{KARMA_SPENT}{row}"))
        if not name or name == "名称":
            continue
        warn.append(notice("engine.import.xlsxOtherKarma", name=name, karma=karma))


def import_contacts(cells: dict[str, str], st: dict[str, Any], warn: list[Notice]) -> None:
    """Fill the contacts from the コンタクト／その他カルマ消費 sheet."""
    _import_contacts(cells, st)
    _report_other_karma(cells, warn)


__all__ = ["CONTACT_ROWS", "KARMA_HEADING", "import_contacts"]
