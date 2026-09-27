"""The bits the template's sheets share: sheet names, and reading a number the
way a spreadsheet writes one."""

from __future__ import annotations

#: The sheet this import reads. The template's names carry a full-width slash.
SHEET_BASICS = "優先度／能力値／資質"


def cell_int(text: str | None) -> int:
    """A sheet's number as an int.

    Everything arrives as a decimal string — a 5 typed into a cell is written
    ``5.0`` — and a cell that holds a label where a number belongs is worth 0
    rather than an error.
    """
    if not text:
        return 0
    try:
        value = float(text)
    except ValueError:
        return 0
    if value != value or value in (float("inf"), float("-inf")):  # NaN / ±inf from a hand edit
        return 0
    return int(round(value))
