"""The 優先度／能力値／資質 sheet: the build, the metatype, the attributes and
the qualities.

Every address here is the one the import reads, and the tables are the import's
own tables read backwards. Where the import folds several of the sheet's answers
onto one value — 魔法使い（メイジ） and 魔法使い（シャーマン） are both
``Magician`` — the export has to pick one, and picks the first the sheet offers.
"""

from __future__ import annotations

import re
from typing import Any

from ..data_loader import CatalogDict
from ..models import CharacterState
from ..notices import ui
from ..xlsx_import.basics import ATTRIBUTE_ROWS, KARMA_NUYEN_CELL, LEVEL_KARMA, LEVEL_NORMAL, METATYPES, PRIORITY_CELLS
from ..xlsx_import.qualities import QUALITY_ROWS
from ._common import Limits, named, translator
from ._workbook import Cells

#: The metatype and awakened dropdowns, read backwards. `TALENTS` has several
#: answers per value, so the first one wins: メイジ over シャーマン, and the
#: 魔術 field for an aspected magician. The tradition and the field are kept
#: elsewhere in this app and the sheet has nowhere else to put them, so the
#: choice is arbitrary and the round trip reports it.
METATYPE_NAMES = {english: japanese for japanese, english in METATYPES.items()}
TALENT_NAMES = {
    "Mundane": "－",
    "Technomancer": "テクノマンサー",
    "Adept": "アデプト",
    "Magician": "魔法使い（メイジ）",
    "Mystic Adept": "ミスティック・アデプト（メイジ）",
    "Aspected Magician": "偏位魔法使い（メイジ、魔術）",
}

#: The kinds of magic user the dropdown has no answer for, and the nearest one
#: it does. Apprentice, Aware, Enchanter and Explorer are all the book's limited
#: magicians, which is what 偏位魔法使い is; an A.I. is nothing the sheet knows.
NEAREST_TALENT = {
    "Apprentice": "Aspected Magician",
    "Aware": "Aspected Magician",
    "Enchanter": "Aspected Magician",
    "Explorer": "Aspected Magician",
    "A.I.": "Mundane",
}

#: The build methods the sheet has no setting for, and the one it is written as.
#: A SumToTen build still chose priority letters — they add up to ten instead of
#: being one of each — so the letters survive and only the method changes.
NEAREST_METHOD = {"SumToTen": "Priority", "LifeModule": "Karma"}

#: Rows 50–59: A the kind, C the name.
QUALITY_KIND = {"Positive": "有利", "Negative": "不利"}
QUALITY_KIND_COLUMN = "A"
QUALITY_NAME_COLUMN = "C"


def _priorities(state: CharacterState, cells: Cells, limits: Limits) -> None:
    method = state.build_method or "Priority"
    if method in NEAREST_METHOD:
        limits.no_cell(ui("engine.kind.other"), method, NEAREST_METHOD[method])
        method = NEAREST_METHOD[method]
    if method == "Karma":
        # The priority letters mean nothing under the karma method, and the
        # sheet says so with this dropdown rather than by blanking them.
        cells["W1"] = LEVEL_KARMA
        return
    cells["W1"] = LEVEL_NORMAL
    chosen = state.priorities.model_dump() if state.priorities else {}
    for field, ref in PRIORITY_CELLS.items():
        cells[ref] = chosen.get(field) or "C"


def _attributes(state: CharacterState, cells: Cells) -> None:
    """H the racial minimum, J what was bought with points, L with karma.

    The import adds H and J back together, so the split is free to be whatever
    reads best on the sheet — and the racial minimum is what the template puts
    in H, so a player opening the file sees their own numbers in the columns
    they filled in.
    """
    minimums = ((state.derived or {}).get("metatype_info") or {}).get("attributes") or {}
    for row, key in ATTRIBUTE_ROWS.items():
        rating = (state.attributes or {}).get(key)
        karma = (state.attribute_karma or {}).get(key) or 0
        if not rating and not karma:
            # MAG / RES on a mundane character: left blank, not written as 0.
            continue
        base = min(int((minimums.get(key) or {}).get("min") or 0), rating or 0)
        if base:
            cells[f"H{row}"] = base
        if (rating or 0) - base:
            cells[f"J{row}"] = (rating or 0) - base
        if karma:
            cells[f"L{row}"] = karma


#: A catalog name that ends in a degree — ``依存症 (中度)``. A pick cannot simply
#: be appended to one of those: the sheet's reader takes the *first* parenthesis
#: as the pick, so 「依存症 (中度)（クラム）」 would come back as 中度 with クラム
#: read as a note. The template's own spelling for both at once is 依存症／中度／クラム.
_DEGREE = re.compile(r"^(.+?)\s*[(（]([^()（）]+)[)）]$")


def _quality_name(row: dict[str, Any], names: dict[str, str]) -> str:
    """The quality as the sheet would have it written.

    A pick goes in parentheses, which is the shape the import tries first — and
    for a quality whose own name already carries it (``SIN持ち：国家SIN``) the
    catalog name is left to speak for itself.
    """
    name = named(names, str(row.get("name") or ""))
    extra = str(row.get("extra") or "").strip()
    if not extra:
        return name
    degree = _DEGREE.match(name)
    if degree:
        return f"{degree.group(1)}／{degree.group(2)}／{extra}"
    return f"{name}（{extra}）"


#: The quality a mentor is taken as, per kind of awakened character. A
#: technomancer's is a paragon; everyone else's is a mentor spirit.
MENTOR_QUALITIES = {"Technomancer": "Paragon", "": "Mentor Spirit"}


#: 「龍殺しの英雄 (ドラゴンスレイヤー)」 — the catalog puts the reading after the
#: name, and the sheet's reader takes the first parenthesis it finds as the pick,
#: so a mentor written with its reading would leave the reading as the mentor.
#: The import adds the reading back when it looks the name up.
_READING = re.compile(r"\s*[(（][^()（）]*[)）]\s*$")


def _mentor(state: CharacterState, cat: CatalogDict, names: dict[str, str]) -> tuple[str, str]:
    """(the quality a mentor is taken as, the mentor's name), or ("", "").

    The import lifts a mentor out of the quality list and into `mentor_id` — the
    sheet has nowhere else to put one, and writes it as the quality's pick — so
    the export has to put it back. Without this the mentor is the one thing a
    character from the template loses on the way back out.
    """
    if not state.mentor_id:
        return "", ""
    quality = MENTOR_QUALITIES.get(state.talent or "", MENTOR_QUALITIES[""])
    kinds = {"Paragon": cat["paragons"], "Mentor Spirit": cat["mentors"]}
    found = next((row for row in kinds[quality] if str(row["id"]) == state.mentor_id), None)
    if not found:
        return "", ""
    return quality, _READING.sub("", named(names, str(found["name"])))


def _qualities(state: CharacterState, cat: CatalogDict, cells: Cells, limits: Limits) -> None:
    names = translator(cat, "qualities")
    rows: list[dict[str, Any]] = [row for row in ((state.derived or {}).get("qualities") or []) if not row.get("free")]
    quality, mentor = _mentor(state, cat, names)
    held = {str(row.get("name") or "") for row in rows}
    if mentor and quality not in held:
        # the mentor's quality was taken off the list on the way in; it goes back
        rows.append({"name": quality, "category": "Positive"})
    pairs = [
        (
            QUALITY_KIND.get(str(row.get("category") or ""), "有利"),
            # the mentor is that quality's pick, whichever row it ended up on
            _quality_name({**row, "extra": mentor}, names)
            if mentor and str(row.get("name") or "") == quality
            else _quality_name(row, names),
        )
        for row in rows
    ]
    for ref, (kind, name) in zip(
        QUALITY_ROWS, limits.fit(pairs, len(QUALITY_ROWS), ui("engine.kind.quality")), strict=False
    ):
        cells[f"{QUALITY_KIND_COLUMN}{ref}"] = kind
        cells[f"{QUALITY_NAME_COLUMN}{ref}"] = name


def basics_sheet(state: CharacterState, cat: CatalogDict, limits: Limits) -> Cells:
    """The 優先度／能力値／資質 sheet for `state`."""
    cells: Cells = {}
    _priorities(state, cells, limits)
    metatype = state.metatype or "Human"
    if metatype not in METATYPE_NAMES:
        # The dropdown has the five core metatypes and カスタム, which the import
        # cannot read back as anything, so a Pixie is written as what it was
        # closest to and said out loud rather than quietly turned into a human.
        limits.no_cell(ui("engine.kind.other"), metatype, "Human")
    cells["C16"] = METATYPE_NAMES.get(metatype, "ヒューマン")
    talent = state.talent or "Mundane"
    if talent in NEAREST_TALENT:
        limits.no_cell(ui("engine.kind.other"), talent, NEAREST_TALENT[talent])
        talent = NEAREST_TALENT[talent]
    cells["C17"] = TALENT_NAMES.get(talent, "－")
    _attributes(state, cells)
    _qualities(state, cat, cells, limits)
    if state.karma_nuyen:
        cells[KARMA_NUYEN_CELL] = state.karma_nuyen
    return cells


__all__ = ["METATYPE_NAMES", "TALENT_NAMES", "basics_sheet"]
