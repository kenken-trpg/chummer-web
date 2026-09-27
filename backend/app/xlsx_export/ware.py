"""The 身体強化／電子機器 sheet: the implants, and the commlink or deck under them.

Cyberware and bioware are one table on the sheet — the player picks the grade,
not the book — so both go down the same thirty rows, a child implant written
under the one it is installed in with the box-drawing character the template
uses. Which side a paired implant went on is written into the name, because that
is the only place the sheet has for it and where the import looks.

What the engine adds by itself is left out. A cyberlimb comes with its own
capacity, a quality can grant an implant outright, and writing those rows would
have the import buy them a second time.
"""

from __future__ import annotations

from typing import Any

from ..data_loader import CatalogDict
from ..models import CharacterState
from ..notices import ui
from ..xlsx_import.ware import (
    DEVICE_NAME,
    DEVICE_RATING,
    DEVICES_COUNT,
    DEVICES_HEADING,
    DEVICES_OFFSET,
    GRADES,
    WARE_GRADE,
    WARE_NAME,
    WARE_RATING,
    WARE_ROWS,
)
from ._common import Limits, named, translator
from ._workbook import Cells

#: The grade dropdown, read backwards.
GRADE_NAMES = {english: japanese for japanese, english in GRADES.items()}

#: What the template puts in front of an implant installed in another.
NESTED_MARK = "└"

#: 右腕 / 左脚 — the side, which the import takes back out of the name.
SIDE_MARKS = {"Right": "右", "Left": "左"}

#: Where the device block goes. The import finds it by its heading, so this only
#: has to sit below the implant table.
DEVICES_HEADING_ROW = max(WARE_ROWS) + 2

#: The kind column of the device block, per state list.
DEVICE_KIND_NAMES = {"commlinks": "コムリンク", "cyberdecks": "サイバーデッキ"}
DEVICE_KIND_COLUMN = "A"


def _implant_name(row: dict[str, Any], names: dict[str, str]) -> str:
    """An implant as the sheet would have it written, side included."""
    name = named(names, str(row.get("name") or ""))
    side = SIDE_MARKS.get(str(row.get("side") or ""), "")
    return f"{side}{name}" if side else name


def _ordered(rows: list[dict[str, Any]]) -> list[tuple[dict[str, Any], bool]]:
    """`rows` as (row, nested), each child directly under its parent.

    The import attaches a nested row to the last row above it that was not
    nested, so the order is what says what is installed in what.
    """
    children: dict[str, list[dict[str, Any]]] = {}
    tops: list[dict[str, Any]] = []
    for row in rows:
        parent = str(row.get("parent_id") or "")
        if parent:
            children.setdefault(parent, []).append(row)
        else:
            tops.append(row)
    out: list[tuple[dict[str, Any], bool]] = []
    for row in tops:
        out.append((row, False))
        out += [(child, True) for child in children.get(str(row.get("id") or ""), [])]
    return out


def _bought(state: CharacterState, bucket: str) -> list[dict[str, Any]]:
    """The rows of `bucket` the character paid for.

    `included` is a piece that came with its parent and `granted_by` one a
    quality or a metatype handed over; the engine puts both back by itself.
    """
    return [
        row
        for row in ((state.derived or {}).get(bucket) or [])
        if not row.get("included") and not row.get("granted_by")
    ]


def _devices(state: CharacterState, names: dict[str, str], cells: Cells, limits: Limits) -> None:
    cells[f"{DEVICE_KIND_COLUMN}{DEVICES_HEADING_ROW}"] = DEVICES_HEADING
    entries: list[tuple[str, dict[str, Any]]] = [
        (kind, row) for bucket, kind in DEVICE_KIND_NAMES.items() for row in (state.derived or {}).get(bucket) or []
    ]
    first = DEVICES_HEADING_ROW + DEVICES_OFFSET
    for offset, (kind, row) in enumerate(limits.fit(entries, DEVICES_COUNT, ui("engine.kind.gear"))):
        cells[f"{DEVICE_KIND_COLUMN}{first + offset}"] = kind
        cells[f"{DEVICE_NAME}{first + offset}"] = named(names, str(row.get("name") or ""))
        cells[f"{DEVICE_RATING}{first + offset}"] = int(row.get("rating") or 1)


def ware_sheet(state: CharacterState, cat: CatalogDict, limits: Limits) -> Cells:
    """The 身体強化／電子機器 sheet for `state`."""
    ware_names = translator(cat, "cyberware")
    ware_names.update((cat.get("translations_by_kind") or {}).get("bioware") or {})
    implants = _ordered(_bought(state, "cyberware")) + _ordered(_bought(state, "bioware"))
    cells: Cells = {}
    for row, (implant, nested) in zip(
        WARE_ROWS, limits.fit(implants, len(WARE_ROWS), ui("engine.kind.cyberware")), strict=False
    ):
        mark = NESTED_MARK if nested else ""
        cells[f"{WARE_NAME}{row}"] = f"{mark}{_implant_name(implant, ware_names)}"
        cells[f"{WARE_GRADE}{row}"] = GRADE_NAMES.get(str(implant.get("grade") or "Standard"), "スタンダード")
        cells[f"{WARE_RATING}{row}"] = int(implant.get("rating") or 1)
    _devices(state, translator(cat, "gear"), cells, limits)
    return cells


__all__ = ["DEVICES_HEADING_ROW", "GRADE_NAMES", "NESTED_MARK", "SIDE_MARKS", "ware_sheet"]
