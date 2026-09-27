"""Import シャドウラン_キャラシテンプレート — the Japanese community character
sheet (音の兔 様, v2.3.2) — into this app's ``CharacterState``.

The template is a Google Sheets document that players fill in and download as
.xlsx. What comes over so far is what its 優先度／能力値／資質 sheet holds: the
build method, the five priorities, the metatype, the kind of magic user, the
attributes and the qualities. Its other sheets (skills, knowledge, spells, ware,
gear, contacts) are not read yet, and the character arrives as a priority build
still in creation, so the rest can be filled in here.

Names are matched against the catalog's Japanese, because the template has the
player type them: a name that matches nothing becomes a warning rather than
failing the import.
"""

from __future__ import annotations

import json
import uuid
from typing import Any, cast

from ..data_loader import catalog
from ..models._common import clamp_input_ints
from ..notices import Notice, NoticeError, notice
from ._common import SHEET_BASICS
from ._sheet import NotAWorkbook, Workbook
from .basics import import_basics
from .qualities import import_qualities

__all__ = ["NotAWorkbook", "is_template_workbook", "xlsx_to_state"]

#: Sheets every version of the template has. Enough to tell it apart from an
#: unrelated spreadsheet without pinning the import to one revision.
REQUIRED_SHEETS = (SHEET_BASICS, "能動技能／技能グループ", "編集不可")


def is_template_workbook(body: bytes) -> bool:
    """Whether the upload is a character-sheet template this can read."""
    try:
        names = set(Workbook(body).sheet_names)
    except NotAWorkbook:
        return False
    return all(sheet in names for sheet in REQUIRED_SHEETS)


def xlsx_to_state(body: bytes) -> tuple[dict[str, Any], list[Notice]]:
    """A filled-in template in, a `CharacterState` dict plus warnings out."""
    try:
        workbook = Workbook(body)
    except NotAWorkbook as exc:
        raise NoticeError(notice("api.notACharacterTemplate")) from exc
    if not all(sheet in workbook.sheet_names for sheet in REQUIRED_SHEETS):
        raise NoticeError(notice("api.notACharacterTemplate"))
    try:
        cells = workbook.cells(SHEET_BASICS)
    except NotAWorkbook as exc:
        raise NoticeError(notice("api.notACharacterTemplate")) from exc

    cat = catalog()
    warn: list[Notice] = []
    st: dict[str, Any] = {"id": str(uuid.uuid4()), "name": "Imported Runner"}
    import_basics(cells, st, warn)
    import_qualities(cells, cat, st, warn)

    seen: set[str] = set()
    unique: list[Notice] = []
    for item in warn:
        marker = json.dumps(item, sort_keys=True, ensure_ascii=False)
        if marker not in seen:
            seen.add(marker)
            unique.append(item)
    # as the .chum5 and Foundry reads do: a hand-typed number comes through
    # composed into a rating, and the models refuse one past the cap.
    return cast(dict[str, Any], clamp_input_ints(st)), unique
