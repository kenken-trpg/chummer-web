"""The 装備 sheet: one flat table holding everything the character owns.

The sheet has three columns that matter — the name, the price and the count —
and no column for a rating, so a rating is written into the name the way the
players do (``偽造 SIN-R4``). A price is what tells the import that a row is an
item rather than a heading, so every row written here carries one.

What is fitted to something else goes directly under it with the template's own
box-drawing character. A commlink and a deck are not here at all: the template
puts them on the 身体強化／電子機器 sheet, and writing them twice would buy them
twice.
"""

from __future__ import annotations

from typing import Any

from ..data_loader import CatalogDict
from ..models import CharacterState
from ..notices import Notice, notice, term
from ..xlsx_import.gear import FIRST_ROW, GEAR_BOUGHT, GEAR_NAME, GEAR_PRICE
from ._common import Limits, named, translator
from ._workbook import Cells

#: What marks a row as fitted to the one above it.
NESTED_MARK = "└"

#: The derived lists this sheet holds, and the translation bucket each uses.
#: `commlinks` and `cyberdecks` are deliberately absent — they belong to the
#: 身体強化／電子機器 sheet — and so are the two plugin lists, which are written
#: under whatever they are fitted to rather than in a block of their own.
BLOCKS: tuple[tuple[str, str], ...] = (
    ("weapons", ""),
    ("armor_items", "armor"),
    ("vehicles", ""),
    ("drones", ""),
    ("lifestyles", ""),
    ("gear", "gear"),
)

#: The lists whose rows are fitted to something above them.
PLUGIN_BLOCKS: tuple[tuple[str, str], ...] = (
    ("armor_mods", "armor"),
    ("weapon_accessories", ""),
)


def _count(row: dict[str, Any]) -> int:
    """What column E holds: the count, or for a lifestyle the months."""
    return int(row.get("months") or row.get("qty") or 1)


def _name(row: dict[str, Any], names: dict[str, str]) -> str:
    """An item as the sheet would have it written, rating included.

    The sheet has no rating column, so a rating above 1 is written onto the name
    with the hyphen-R spelling — one of the four the import reads, and the only
    one that cannot be mistaken for part of a name.
    """
    name = named(names, "Electronic Parts" if "parts_remaining_units" in row else str(row.get("name") or ""))
    rating = int(row.get("rating") or 0)
    return f"{name}-R{rating}" if rating > 1 else name


def _bought(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The rows that were paid for.

    What came with a parent, what a quality granted, and what the engine made
    out of something else — a Hand Blade is the weapon side of an implant, and a
    grenade is the weapon side of a piece of gear — are all put back when the
    character is computed again, so writing them would buy them twice.
    """
    return [
        row
        for row in rows
        if (not row.get("included") or row.get("parts_supply"))
        and row.get("parts_remaining_units") != 0
        and ("parts_remaining_units" not in row or int(row["parts_remaining_units"]) % 4 == 0)
        and row.get("modification_status") != "pending"
        and (not row.get("granted_by") or row.get("parts_supply"))
        and not row.get("from_gear")
        and not row.get("from_ware")
    ]


def _fitted(
    state: CharacterState, translators: dict[str, dict[str, str]]
) -> dict[str, list[tuple[str, int, int, str]]]:
    """``{parent id: [(name, price, count, english), …]}`` for everything fitted to
    something else: the two plugin lists, and the gear held inside other gear."""
    out: dict[str, list[tuple[str, int, int, str]]] = {}
    blocks = PLUGIN_BLOCKS + (("gear", "gear"),)
    for bucket, kind in blocks:
        names = translators[kind]
        for row in _bought((state.derived or {}).get(bucket) or []):
            parent = str(row.get("parent_id") or "")
            if parent and "parts_remaining_units" not in row:
                out.setdefault(parent, []).append(
                    (_name(row, names), int(row.get("nuyen") or 0), _count(row), str(row.get("name") or ""))
                )
    return out


def gear_sheet(state: CharacterState, cat: CatalogDict, limits: Limits) -> tuple[Cells, list[Notice]]:
    """The 装備 sheet for `state`, and what would not fit on it.

    A row whose parent is not on this sheet — a program inside a commlink, which
    the template keeps on another sheet entirely — has nowhere to go: written
    loose it would be a different thing from what it is. So it is reported
    rather than written. `limits` is taken for the sake of the same signature
    the other sheets have; this one is the only sheet the template does not cap.
    """
    del limits
    translators = {kind: translator(cat, kind) for _bucket, kind in BLOCKS + PLUGIN_BLOCKS}
    fitted = _fitted(state, translators)
    lines: list[tuple[str, int, int]] = []
    for bucket, kind in BLOCKS:
        for row in _bought((state.derived or {}).get(bucket) or []):
            if str(row.get("parent_id") or "") and "parts_remaining_units" not in row:
                continue  # written under its parent, or reported below
            children = fitted.pop(str(row.get("id") or ""), [])
            # A weapon's or an item's derived price is the whole assembly, and
            # each child writes its own price on its own row — so the parent's
            # row shows what is left, and the column adds up to what was paid.
            own = int(row.get("nuyen") or 0) - sum(price for _n, price, _c, _e in children)
            lines.append((_name(row, translators[kind]), max(0, own), _count(row)))
            for name, price, count, _english in children:
                lines.append((f"{NESTED_MARK}{name}", price, count))

    cells: Cells = {}
    for offset, (name, price, count) in enumerate(lines):
        at = FIRST_ROW + offset
        cells[f"{GEAR_NAME}{at}"] = name
        # The price is what tells the import this row is an item at all, so a
        # thing that costs nothing is still written as costing 0.
        cells[f"{GEAR_PRICE}{at}"] = price
        cells[f"{GEAR_BOUGHT}{at}"] = count
    # Whatever is still held was fitted to something this sheet does not write.
    left = sorted({english for rows in fitted.values() for _n, _p, _c, english in rows})
    fractional_parts = [
        str(r["name"]) for r in (state.derived or {}).get("gear") or [] if r.get("parts_remaining_units", 0) % 4
    ]
    return cells, [notice("engine.export.xlsxNoPlace", name=term(english)) for english in [*left, *fractional_parts]]


__all__ = ["BLOCKS", "NESTED_MARK", "PLUGIN_BLOCKS", "gear_sheet"]
