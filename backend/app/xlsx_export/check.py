"""What a character loses on the way through the キャラシテンプレート .xlsx.

The template is lossier than a .chum5 by a wide margin, and for reasons worth
saying out loud rather than listing as rules:

* **It is a fixed grid.** Ten qualities, twenty spells, twenty adept powers,
  thirty implants, seven devices, twenty contacts, twenty-five knowledge skills.
* **Several of its dropdowns are shorter than the book.** Five metatypes, six
  kinds of magic user, five implant grades, two build methods.
* **All the equipment shares one free-text column.** A name that two of the
  book's lists both hold comes back under whichever the import tries first, so a
  grenade kept as gear can come back as a weapon.

Rather than a rule per case, this writes the file, reads it back and compares —
so the report is right by construction, and stays right as the sheets change.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from ..characters import import_character
from ..export_check import differences
from ..models import CharacterState
from ..notices import Notice, notice, term
from ..xlsx_import import xlsx_to_state
from . import state_to_xlsx, xlsx_limits

__all__ = ["roundtrip_differences"]

#: Said in its own words below rather than counted with the character's own
#: contents. The template is a character-creation sheet: it has no cell for
#: which rulebooks are in play or which house rules are on, so this is lost on
#: every export and would otherwise report 「その他が変わります」 every time.
_OWN_WORDS = frozenset({"settings"})


def _grant_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("weapon_id") or row.get("id") or ""),
        str(row.get("name") or ""),
        str(row.get("select") or row.get("extra") or ""),
        str(row.get("rating") or ""),
    )


def _innate_losses(first: CharacterState, again: CharacterState) -> list[Notice]:
    """State fields omit free grants. Compare their recomputed rows as well.

    A supported species can re-grant its qualities without a sheet cell. Only
    actual losses count, including repeated grants with distinct fixed picks.
    """
    out: list[Notice] = []
    for before, after in (
        (first.derived.get("qualities"), again.derived.get("qualities")),
        (
            (first.derived.get("metatype_info") or {}).get("powers"),
            (again.derived.get("metatype_info") or {}).get("powers"),
        ),
        (first.derived.get("weapons"), again.derived.get("weapons")),
    ):
        kept = Counter(_grant_key(row) for row in after or [] if row.get("origin") == "Metatype")
        for row in before or []:
            if row.get("origin") != "Metatype":
                continue
            key = _grant_key(row)
            if kept[key]:
                kept[key] -= 1
                continue
            out.append(
                notice(
                    "engine.export.xlsxInnateGrant",
                    name=term(str(row.get("name") or "")),
                    selection=str(row.get("select") or row.get("extra") or ""),
                    source=str(row.get("source") or ""),
                    page=str(row.get("page") or ""),
                )
            )
    return out


def roundtrip_differences(state: CharacterState) -> list[Notice]:
    """What the character would look like after being written to the template's
    .xlsx and read back, as notices. Empty when it comes back the same.

    The equipment rows the re-import could not match are counted among the
    losses rather than offered for confirmation: this is asked before the
    download, and what it answers is "how much of this character does the file
    carry", not "what should it have been".
    """
    first = import_character(state.model_dump())
    again = import_character(xlsx_to_state(state_to_xlsx(first))[0])
    out = xlsx_limits(first)
    if first.settings != again.settings:
        out.append(notice("engine.export.xlsxNoSettings", name=(first.settings.name or "")))
    return out + _innate_losses(first, again) + differences(first, again, skip=_OWN_WORDS)
