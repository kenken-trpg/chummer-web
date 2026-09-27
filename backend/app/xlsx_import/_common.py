"""The bits the template's sheets share: their names, reading a number the way a
spreadsheet writes one, and looking a Japanese name back up in the catalog."""

from __future__ import annotations

from collections.abc import Iterable

from ..data_loader import CatalogDict

#: The sheets this import reads. The template's names carry a full-width slash.
SHEET_BASICS = "優先度／能力値／資質"
SHEET_SKILLS = "能動技能／技能グループ"
SHEET_KNOWLEDGE = "知識技能／言語技能"


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


def japanese_index(cat: CatalogDict, names: Iterable[str], kind: str = "") -> dict[str, str]:
    """``{japanese: english}`` for `names`, with the English name as a key too.

    Some of the catalog's Japanese names carry both readings, joined with a
    slash — ``隠密/ステルス``, ``真偽分析/アナライズ・トゥルース`` — and the
    template writes whichever of the two the player knows. So each side is a key
    of its own, alongside the joined name as written.

    `kind` names a `translations_by_kind` bucket to layer on top (``"skill"``
    for anything on the skill sheets), the way the catalog view does.
    """
    translations = dict(cat.get("translations") or {})
    if kind:
        translations.update((cat.get("translations_by_kind") or {}).get(kind) or {})
    index: dict[str, str] = {}
    for english in names:
        index.setdefault(english, english)
        japanese = translations.get(english)
        if not japanese:
            continue
        for part in [japanese, *japanese.split("/")]:
            part = part.strip()
            if part:
                index.setdefault(part, english)
    return index
