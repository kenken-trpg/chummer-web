"""The build method, the metatype, the kind of magic user and the attributes —
everything the template's 優先度／能力値／資質 sheet holds above the qualities.

Every input on that sheet sits at a fixed address, so this is a table of cells
rather than a search. The addresses come from the sheet's own data validations
(the dropdowns name the cells they are attached to).
"""

from __future__ import annotations

from typing import Any

from ..notices import Notice, notice, ui
from ._common import SHEET_BASICS, cell_int

#: The five priorities, and the cell each is chosen in.
#: 換金したカルマ — karma turned into starting nuyen, which the sheet spends out
#: of the same equipment budget. Without it every character who used it looks
#: over budget by 2,000 nuyen a point.
KARMA_NUYEN_CELL = "AC4"

PRIORITY_CELLS = {
    "Heritage": "C3",
    "Attributes": "C7",
    "Talent": "C8",
    "Skills": "C12",
    "Resources": "C13",
}

#: W1 — which of the book's starting levels the sheet is set up for. Only the
#: first is a priority build; 800 カルマ割り振り is the Karma method, and the
#: other two are the priority method under a different table.
LEVEL_NORMAL = "通常のプレイレベル"
LEVEL_KARMA = "800カルマ割り振り"

#: C16, the metatype dropdown. The sheet offers only the five core metatypes
#: plus カスタム, an escape hatch it leaves to the player to sort out.
METATYPES = {
    "ヒューマン": "Human",
    "エルフ": "Elf",
    "ドワーフ": "Dwarf",
    "オーク": "Ork",
    "トロール": "Troll",
}

#: C17, the awakened dropdown. The sheet splits a magician by tradition
#: (メイジ / シャーマン) and an aspected one by field, distinctions this app
#: keeps in the tradition and in a quality rather than in `talent` — so several
#: of these fold onto one value and the lost half becomes a warning.
TALENTS = {
    "－": "Mundane",
    "テクノマンサー": "Technomancer",
    "アデプト": "Adept",
    "魔法使い（メイジ）": "Magician",
    "魔法使い（シャーマン）": "Magician",
    "ミスティック・アデプト（メイジ）": "Mystic Adept",
    "ミスティック・アデプト（シャーマン）": "Mystic Adept",
    "偏位魔法使い（メイジ、魔術）": "Aspected Magician",
    "偏位魔法使い（メイジ、召喚術）": "Aspected Magician",
    "偏位魔法使い（メイジ、錬金術）": "Aspected Magician",
    "偏位魔法使い（シャーマン、魔術）": "Aspected Magician",
    "偏位魔法使い（シャーマン、召喚術）": "Aspected Magician",
    "偏位魔法使い（シャーマン、錬金術）": "Aspected Magician",
}

#: The attribute rows, in the order the sheet lists them.
ATTRIBUTE_ROWS = {
    19: "BOD",
    20: "AGI",
    21: "REA",
    22: "STR",
    23: "CHA",
    24: "INT",
    25: "LOG",
    26: "WIL",
    27: "EDG",
    28: "MAG",
    29: "RES",
}


def _import_priorities(cells: dict[str, str], st: dict[str, Any], warn: list[Notice]) -> None:
    level = cells.get("W1") or LEVEL_NORMAL
    if level == LEVEL_KARMA:
        # A different build method altogether: the priority letters on the sheet
        # are left over from before the switch and mean nothing.
        st["build_method"] = "Karma"
        st["priorities"] = {}
        return
    st["build_method"] = "Priority"
    st["priorities"] = {field: (cells.get(ref) or "C") for field, ref in PRIORITY_CELLS.items()}
    if level != LEVEL_NORMAL:
        warn.append(notice("engine.import.xlsxPlayLevel", level=level))


def _import_metatype(cells: dict[str, str], st: dict[str, Any], warn: list[Notice]) -> None:
    name = cells.get("C16") or ""
    metatype = METATYPES.get(name)
    if not metatype:
        warn.append(notice("engine.import.skippedUnknown", kind=ui("engine.kind.other"), name=name))
    st["metatype"] = metatype or "Human"


def _import_talent(cells: dict[str, str], st: dict[str, Any], warn: list[Notice]) -> None:
    name = cells.get("C17") or ""
    talent = TALENTS.get(name)
    if talent is None:
        warn.append(notice("engine.import.skippedUnknown", kind=ui("engine.kind.other"), name=name))
    st["talent"] = talent or "Mundane"
    # メイジ／シャーマン and the aspected fields are a tradition and a quality
    # here, neither of which the sheet records anywhere this can read.
    if talent in ("Magician", "Mystic Adept", "Aspected Magician"):
        warn.append(notice("engine.import.xlsxMagicStyle", name=name))


def _import_attributes(cells: dict[str, str], st: dict[str, Any]) -> None:
    """H + J is the attribute as bought, L is what karma raised it by.

    P holds the finished number, but reading it would count the karma twice and
    fold in the bonuses from qualities and ware that this app derives for itself.
    """
    attributes: dict[str, int] = {}
    karma: dict[str, int] = {}
    for row, key in ATTRIBUTE_ROWS.items():
        base = cell_int(cells.get(f"H{row}"))
        points = cell_int(cells.get(f"J{row}"))
        bought = cell_int(cells.get(f"L{row}"))
        # MAG / RES stay absent for a mundane character rather than sitting at 0.
        if base or points:
            attributes[key] = base + points
        if bought:
            karma[key] = bought
    if attributes:
        st["attributes"] = attributes
    if karma:
        st["attribute_karma"] = karma


def import_basics(cells: dict[str, str], st: dict[str, Any], warn: list[Notice]) -> None:
    """Fill `st` from the 優先度／能力値／資質 sheet's upper half."""
    _import_priorities(cells, st, warn)
    _import_metatype(cells, st, warn)
    _import_talent(cells, st, warn)
    _import_attributes(cells, st)
    karma_nuyen = cell_int(cells.get(KARMA_NUYEN_CELL))
    if karma_nuyen > 0:
        st["karma_nuyen"] = karma_nuyen


__all__ = [
    "ATTRIBUTE_ROWS",
    "KARMA_NUYEN_CELL",
    "METATYPES",
    "PRIORITY_CELLS",
    "SHEET_BASICS",
    "TALENTS",
    "import_basics",
]
