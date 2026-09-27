"""The 能動技能／技能グループ and 知識技能／言語技能 sheets.

The template lists every skill in the book, one per row, and the player fills in
the numbers beside the ones they have. Writing all of them back would mean
carrying the book's whole skill list and its row order, which is the template's
business and not something worth pinning this export to. So only the skills the
character actually has are written, under the same headings the import cuts the
sheet at — a shorter sheet that reads back identically.

A rating is split back into the two columns the way the import adds them up:
`skills` is the finished rating and `skill_karma` the part of it karma paid for,
so the points column is the difference.
"""

from __future__ import annotations

from typing import Any

from ..data_loader import CatalogDict
from ..models import CharacterState
from ..notices import ui
from ..xlsx_import.skills import (
    COLUMN_KARMA,
    COLUMN_POINTS,
    COLUMN_SPEC_KARMA,
    COLUMN_SPEC_POINTS,
    GROUPS_HEADING,
    KNOWLEDGE_ROWS,
    NATIVE_CATEGORY,
)
from ._common import Limits, named, translator
from ._workbook import Cells

#: Where the two blocks of the active sheet start. The import finds them by
#: their headings, so these only have to be in the template's order.
GROUPS_HEADING_ROW = 3
SKILLS_HEADING = "能動技能"
NAME_COLUMN = "A"

#: The knowledge sheet: A the category, B the name, H the points, I the karma.
KNOWLEDGE_CATEGORY_COLUMN = "A"
KNOWLEDGE_NAME_COLUMN = "B"
KNOWLEDGE_POINTS = "H"
KNOWLEDGE_KARMA = "I"

#: Chummer's categories, read back into the ones the sheet offers. Several of
#: the sheet's answers mean the same category, so the first is used.
CATEGORY_NAMES = {
    "Street": "ストリート知識技能",
    "Academic": "学術知識技能",
    "Professional": "職業知識技能",
    "Interest": "趣味知識技能",
    "Language": "言語知識技能",
}


def _rated(cells: Cells, row: int, rating: int, karma: int) -> None:
    """I the points, J the karma — the two columns that add up to a rating."""
    if rating - karma:
        cells[f"{COLUMN_POINTS}{row}"] = rating - karma
    if karma:
        cells[f"{COLUMN_KARMA}{row}"] = karma


def _specialized(cells: Cells, row: int, spec: str, with_karma: bool, names: dict[str, str]) -> None:
    """E when points paid for the specialization, F when karma did.

    `names` holds only the specializations the skill itself offers, because the
    import can only translate those back: it looks a typed one up against the
    skill's own list and keeps anything else as written. Translating a
    specialization off that list — ``Tae Kwon Do`` is a martial art, not one of
    Unarmed Combat's four — would rename the player's own text instead.
    """
    if not spec:
        return
    column = COLUMN_SPEC_KARMA if with_karma else COLUMN_SPEC_POINTS
    cells[f"{column}{row}"] = names.get(spec) or spec


def _groups(state: CharacterState, names: dict[str, str], cells: Cells, row: int) -> int:
    cells[f"{NAME_COLUMN}{GROUPS_HEADING_ROW}"] = GROUPS_HEADING
    karma = state.skill_group_karma or {}
    for english, rating in (state.skill_groups or {}).items():
        cells[f"{NAME_COLUMN}{row}"] = named(names, english)
        _rated(cells, row, rating, karma.get(english) or 0)
        row += 1
    return row


def _spec_names(cat: CatalogDict, names: dict[str, str]) -> dict[str, dict[str, str]]:
    """``{skill: {specialization: japanese}}`` over the book's own lists."""
    return {
        str(skill["name"]): {
            str(option): names[str(option)] for option in skill.get("specs") or [] if str(option) in names
        }
        for skill in cat["skills"]["skills"]
    }


def _active(
    state: CharacterState, names: dict[str, str], specs_by_skill: dict[str, dict[str, str]], cells: Cells, row: int
) -> None:
    cells[f"{NAME_COLUMN}{row}"] = SKILLS_HEADING
    row += 1
    karma = state.skill_karma or {}
    specs = state.skill_specializations or {}
    with_karma = set(state.skill_specs_karma or [])
    for english, rating in (state.skills or {}).items():
        cells[f"{NAME_COLUMN}{row}"] = named(names, english)
        _rated(cells, row, rating, karma.get(english) or 0)
        _specialized(cells, row, specs.get(english) or "", english in with_karma, specs_by_skill.get(english, {}))
        row += 1
    for entry in state.exotic_skills or []:
        data: dict[str, Any] = entry.model_dump() if hasattr(entry, "model_dump") else dict(entry)
        # An exotic skill is one entry per weapon here and one row on the sheet,
        # whose only place for the weapon is the specialization column — which is
        # exactly where the import looks for it.
        cells[f"{NAME_COLUMN}{row}"] = named(names, str(data.get("skill_name") or ""))
        _rated(cells, row, int(data.get("rating") or 0), 0)
        _specialized(cells, row, str(data.get("extra") or ""), False, {})
        row += 1


def active_sheet(state: CharacterState, cat: CatalogDict) -> Cells:
    """The 能動技能／技能グループ sheet: the groups, then the skills."""
    names = translator(cat, "skill")
    cells: Cells = {}
    _active(state, names, _spec_names(cat, names), cells, _groups(state, names, cells, GROUPS_HEADING_ROW + 1))
    return cells


def knowledge_sheet(state: CharacterState, cat: CatalogDict, limits: Limits) -> Cells:
    """The 知識技能／言語技能 sheet.

    A knowledge skill's name *is* the skill — the sheet lets the player write
    anything, and this app stores whatever they wrote — so nothing here is
    translated, not even a name the book happens to print. Turning ``English``
    into ``英語`` on the way out would mean the character came back with a
    differently-named skill, which is a rename of the player's own data rather
    than a translation. Only the category is looked up, and it is a dropdown.
    """
    del cat
    karma = state.knowledge_karma or {}
    categories = state.knowledge_categories or {}
    specs = state.skill_specializations or {}
    with_karma = set(state.skill_specs_karma or [])
    entries: list[tuple[str, str, int, int]] = [
        (name, CATEGORY_NAMES.get(categories.get(name) or "Academic", "学術知識技能"), rating, karma.get(name) or 0)
        for name, rating in (state.knowledge_skills or {}).items()
    ]
    entries += [(name, NATIVE_CATEGORY, 0, 0) for name in state.native_languages or []]
    cells: Cells = {}
    for row, (name, category, rating, bought) in zip(
        KNOWLEDGE_ROWS, limits.fit(entries, len(KNOWLEDGE_ROWS), ui("engine.kind.knowledgeSkill")), strict=False
    ):
        cells[f"{KNOWLEDGE_CATEGORY_COLUMN}{row}"] = category
        cells[f"{KNOWLEDGE_NAME_COLUMN}{row}"] = name
        if rating - bought:
            cells[f"{KNOWLEDGE_POINTS}{row}"] = rating - bought
        if bought:
            cells[f"{KNOWLEDGE_KARMA}{row}"] = bought
        _specialized(cells, row, specs.get(name) or "", name in with_karma, {})
    return cells


__all__ = ["CATEGORY_NAMES", "active_sheet", "knowledge_sheet"]
