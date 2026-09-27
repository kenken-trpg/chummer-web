"""The 呪文／複合体／アデプト・パワー sheet.

Three lists down one sheet: the spells in column C from row 3, the complex forms
in column V of the same rows, and the adept powers under their own heading. The
sheet works the drain, the range and the power points out for itself, so a name
and — for a power — a level is the whole of what is written.
"""

from __future__ import annotations

from typing import Any

from ..data_loader import CatalogDict
from ..models import CharacterState
from ..notices import ui
from ..xlsx_import.magic import (
    FORM_NAME,
    NAMES_FROM_ROW,
    POWER_LEVEL,
    POWER_NAME,
    POWERS_COUNT,
    POWERS_HEADING,
    POWERS_OFFSET,
    SPELL_NAME,
)
from ._common import Limits, named, translator
from ._workbook import Cells

#: The rows the two name columns share, and where the power block goes. The
#: import finds the powers by their heading, so this only has to leave the
#: spells room above it.
NAMES_COUNT = 20
POWERS_HEADING_ROW = NAMES_FROM_ROW + NAMES_COUNT + 1


def _listed(rows: list[dict[str, Any]], key: str, by_id: dict[str, str], names: dict[str, str]) -> list[str]:
    """The Japanese names of `rows`, which hold an id rather than a name."""
    out = []
    for row in rows:
        english = by_id.get(str(row.get(key) or ""))
        if english:
            out.append(named(names, english))
    return out


def _power_name(row: dict[str, Any], by_id: dict[str, str], names: dict[str, str]) -> str:
    """A power as the sheet would have it written: the name, and what it was
    taken for in parentheses — which is the first shape the import tries."""
    name = named(names, by_id.get(str(row.get("power_id") or ""), ""))
    extra = str(row.get("extra") or "").strip()
    return f"{name}（{extra}）" if extra else name


def magic_sheet(state: CharacterState, cat: CatalogDict, limits: Limits) -> Cells:
    """The 呪文／複合体／アデプト・パワー sheet for `state`."""
    names = translator(cat)
    cells: Cells = {}
    for column, key, bucket, what in (
        (SPELL_NAME, "spell_id", "spells", ui("engine.kind.spell")),
        (FORM_NAME, "form_id", "complex_forms", ui("engine.kind.complexForm")),
    ):
        by_id = {str(row["id"]): str(row["name"]) for row in cat[bucket]}  # type: ignore[literal-required]
        held = [entry.model_dump() for entry in getattr(state, bucket, None) or []]
        for offset, name in enumerate(limits.fit(_listed(held, key, by_id, names), NAMES_COUNT, what)):
            cells[f"{column}{NAMES_FROM_ROW + offset}"] = name

    cells[f"{POWER_NAME}{POWERS_HEADING_ROW}"] = POWERS_HEADING
    power_names = translator(cat, "power")
    powers_by_id = {str(row["id"]): str(row["name"]) for row in cat["powers"]}
    powers = [entry.model_dump() for entry in state.adept_powers or []]
    first = POWERS_HEADING_ROW + POWERS_OFFSET
    for offset, row in enumerate(limits.fit(powers, POWERS_COUNT, ui("engine.kind.adeptPower"))):
        cells[f"{POWER_NAME}{first + offset}"] = _power_name(row, powers_by_id, power_names)
        # A power with no levels sits at 1 and the sheet's level column means
        # nothing for it; writing the rating regardless keeps the two agreeing.
        cells[f"{POWER_LEVEL}{first + offset}"] = int(row.get("rating") or 1)
    return cells


__all__ = ["NAMES_COUNT", "POWERS_HEADING_ROW", "magic_sheet"]
