"""Import シャドウラン_キャラシテンプレート — the Japanese community character
sheet (音の兔 様, v2.3.2) — into this app's ``CharacterState``.

The template is a Google Sheets document that players fill in and download as
.xlsx. What comes over so far: the build method, the five priorities, the metatype, the
kind of magic user, the attributes and the qualities (優先度／能力値／資質), the
active skills and skill groups (能動技能／技能グループ), the knowledge and
language skills (知識技能／言語技能) and the spells, complex forms and adept
powers (呪文／複合体／アデプト・パワー) and the implants, commlinks and decks
(身体強化／電子機器), the equipment (装備) and the contacts
(コンタクト／その他カルマ消費). A character with nothing in 成長ログ arrives as a
priority build still in creation, so the rest can be filled in here; one with
rows there has been played, and arrives as a career character carrying its
reward ledger.

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
from ._common import (
    SHEET_BASICS,
    SHEET_CONTACTS,
    SHEET_GEAR,
    SHEET_GROWTH,
    SHEET_KNOWLEDGE,
    SHEET_MAGIC,
    SHEET_SKILLS,
    SHEET_WARE,
)
from ._sheet import NotAWorkbook, Workbook
from .basics import import_basics
from .contacts import import_contacts
from .gear import import_gear
from .growth import import_growth
from .magic import import_magic
from .qualities import import_qualities
from .skills import import_skills
from .ware import import_ware

__all__ = ["NotAWorkbook", "is_template_workbook", "xlsx_to_state"]

#: Sheets every version of the template has. Enough to tell it apart from an
#: unrelated spreadsheet without pinning the import to one revision.
REQUIRED_SHEETS = (SHEET_BASICS, SHEET_SKILLS, "編集不可")


def is_template_workbook(body: bytes) -> bool:
    """Whether the upload is a character-sheet template this can read."""
    try:
        names = set(Workbook(body).sheet_names)
    except NotAWorkbook:
        return False
    return all(sheet in names for sheet in REQUIRED_SHEETS)


def xlsx_to_state(body: bytes) -> tuple[dict[str, Any], list[Notice], list[dict[str, Any]]]:
    """A filled-in template in; a `CharacterState` dict, warnings, and the
    equipment rows that need a person to confirm them.

    The third of those is why the 装備 sheet is worth importing at all: it is
    written freely enough that a good deal of it cannot be matched, and a row
    that comes back with a shortlist of what it looks like is a row someone can
    settle in one click.
    """
    try:
        workbook = Workbook(body)
    except NotAWorkbook as exc:
        raise NoticeError(notice("api.notACharacterTemplate")) from exc
    if not all(sheet in workbook.sheet_names for sheet in REQUIRED_SHEETS):
        raise NoticeError(notice("api.notACharacterTemplate"))
    try:
        basics = workbook.cells(SHEET_BASICS)
        active = workbook.cells(SHEET_SKILLS)
        # 知識技能／言語技能 is not in REQUIRED_SHEETS: a revision that renamed it
        # should still bring the rest of the character over.
        knowledge = workbook.cells(SHEET_KNOWLEDGE) if SHEET_KNOWLEDGE in workbook.sheet_names else {}
        magic = workbook.cells(SHEET_MAGIC) if SHEET_MAGIC in workbook.sheet_names else {}
        ware = workbook.cells(SHEET_WARE) if SHEET_WARE in workbook.sheet_names else {}
        gear = workbook.cells(SHEET_GEAR) if SHEET_GEAR in workbook.sheet_names else {}
        contacts = workbook.cells(SHEET_CONTACTS) if SHEET_CONTACTS in workbook.sheet_names else {}
        growth = workbook.cells(SHEET_GROWTH) if SHEET_GROWTH in workbook.sheet_names else {}
    except NotAWorkbook as exc:
        raise NoticeError(notice("api.notACharacterTemplate")) from exc

    cat = catalog()
    warn: list[Notice] = []
    pending: list[dict[str, Any]] = []
    st: dict[str, Any] = {"id": str(uuid.uuid4()), "name": "Imported Runner"}
    import_basics(basics, st, warn)
    import_qualities(basics, cat, st, warn)
    import_skills(active, knowledge, cat, st, warn)
    import_magic(magic, cat, st, warn)
    import_ware(ware, cat, st, warn)
    import_gear(gear, cat, st, warn, pending)
    import_contacts(contacts, st, warn)
    import_growth(growth, st, warn)

    seen: set[str] = set()
    unique: list[Notice] = []
    for item in warn:
        marker = json.dumps(item, sort_keys=True, ensure_ascii=False)
        if marker not in seen:
            seen.add(marker)
            unique.append(item)
    # as the .chum5 and Foundry reads do: a hand-typed number comes through
    # composed into a rating, and the models refuse one past the cap.
    return cast(dict[str, Any], clamp_input_ints(st)), unique, pending
