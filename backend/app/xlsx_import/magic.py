"""The 呪文／複合体／アデプト・パワー sheet, and the mentor named on the quality sheet.

Three blocks share the sheet, and only the first two are a list of names the
book prints:

* **Spells** (rows 3–22, column C) and **complex forms** (the same rows, column
  V). The player types the name, but there is nothing else to type — the sheet
  fills the range, the drain and the duration in beside it — so the names come
  out clean and match the catalog as written. Rituals and alchemical
  preparations go in the same column, and the catalog holds them alongside the
  spells, so they resolve the same way.
* **Adept powers** (the twenty rows under the アデプト・パワー heading, column A,
  with the level in F). Here the player writes a target onto the name the way
  they do for qualities — ``潜在力強化　身体`` is the catalog's
  ``潜在力強化：(身体)`` — so a power goes through the same typed-name handling.

The block the sheet fills in for itself — power points spent, drain, the karma
totals — is the sheet's own arithmetic, which this app derives, so none of it is
read.
"""

from __future__ import annotations

import re
import uuid
from typing import Any

from ..data_loader import CatalogDict
from ..notices import Notice, Phrase, notice, ui
from ._common import cell_int, japanese_index, no_interpunct, resolve_typed, split_name

#: Spells and complex forms share rows 3–22, one list per half of the sheet.
NAMES_FROM_ROW = 3
SPELL_NAME = "C"
FORM_NAME = "V"

#: The heading that opens the adept-power block. Its own row and the two under
#: it are headings, and twenty rows of powers follow.
POWERS_HEADING = "アデプト・パワー"
POWERS_OFFSET = 3
POWERS_COUNT = 20
POWER_NAME = "A"
POWER_LEVEL = "F"

#: A power the player marked for themselves — 「※殺戮の手」 is Killing Hands with
#: a note that something else pays for it. The mark is not part of the name.
_MARKS = re.compile(r"^[※*＊]+\s*")

#: 竜 and 龍 are the same character; the catalog prints one and the template the
#: other, and nothing else in these lists turns on the difference.
_VARIANTS = {"竜": "龍"}

#: Mentors the template names differently from the catalog's Japanese.
MENTOR_ALIASES = {"鮫": "Shark"}


def _variant(text: str) -> str:
    for old, new in _VARIANTS.items():
        text = text.replace(old, new)
    return text


def _reading_stripped(text: str) -> str:
    """``龍殺しの英雄 (ドラゴンスレイヤー)`` -> ``龍殺しの英雄``.

    A handful of the catalog's Japanese names carry the loanword reading in
    parentheses beside the kanji, and the sheets write one or the other.
    """
    return re.sub(r"\s*[(（][^()（）]*[)）]\s*$", "", text).strip()


def mentor_index(cat: CatalogDict) -> dict[str, str]:
    """Japanese mentor or paragon name -> id, in every spelling seen."""
    translations = dict(cat.get("translations") or {})
    index: dict[str, str] = {}
    for row in list(cat["mentors"]) + list(cat["paragons"]):
        name, mentor_id = str(row["name"]), str(row["id"])
        index.setdefault(name, mentor_id)
        japanese = translations.get(name)
        for spelling in [japanese, _reading_stripped(japanese or "")] if japanese else []:
            for part in [spelling, *spelling.split("/")]:
                part = part.strip()
                if part:
                    index.setdefault(part, mentor_id)
                    index.setdefault(_variant(part), mentor_id)
    return index


def resolve_mentor(raw: str, cat: CatalogDict) -> str:
    """The mentor named in 導師精霊（…）, or "" if it is not one this app knows."""
    index = mentor_index(cat)
    name = split_name(raw)[0]
    aliased = MENTOR_ALIASES.get(name, "")
    return index.get(name) or index.get(_variant(name)) or index.get(no_interpunct(name)) or index.get(aliased) or ""


def _named_rows(cells: dict[str, str], column: str) -> list[tuple[int, str]]:
    """(row, name) for the filled rows of `column`, from `NAMES_FROM_ROW` down to
    the adept-power heading."""
    stop = _powers_heading(cells) or 10_000
    out = []
    for row in range(NAMES_FROM_ROW, stop):
        name = (cells.get(f"{column}{row}") or "").strip()
        if name:
            out.append((row, name))
    return out


def _powers_heading(cells: dict[str, str]) -> int | None:
    """The row of the アデプト・パワー heading, which is what separates the two
    halves of the sheet; a row inserted above it moves everything below."""
    for ref, text in cells.items():
        if re.fullmatch(r"A\d+", ref) and text.strip() == POWERS_HEADING:
            return int(ref[1:])
    return None


def _import_listed(
    cells: dict[str, str],
    column: str,
    key: str,
    id_key: str,
    rows: list[dict[str, Any]],
    kind: Phrase,
    cat: CatalogDict,
    st: dict[str, Any],
    warn: list[Notice],
) -> None:
    """Spells or complex forms: a column of names, nothing else to read."""
    ids = {str(row["name"]): str(row["id"]) for row in rows}
    index = japanese_index(cat, ids)
    out: list[dict[str, Any]] = []
    for _row, name in _named_rows(cells, column):
        found = index.get(name) or index.get(no_interpunct(name))
        if not found:
            warn.append(notice("engine.import.skippedUnknown", kind=kind, name=name))
            continue
        entry: dict[str, Any] = {"id": str(uuid.uuid4()), id_key: ids[found]}
        if id_key == "spell_id":
            # The sheet has no column for it: an alchemical preparation is a
            # name in the same list as the spells.
            entry["alchemical"] = False
        else:
            entry["level"] = None
            entry["extra"] = None
        out.append(entry)
    if out:
        st[key] = out


def _import_powers(cells: dict[str, str], cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    heading = _powers_heading(cells)
    if heading is None:
        return
    by_name = {str(row["name"]): row for row in cat["powers"]}
    index = japanese_index(cat, by_name, "power")
    powers: list[dict[str, Any]] = []
    for row in range(heading + POWERS_OFFSET, heading + POWERS_OFFSET + POWERS_COUNT):
        raw = _MARKS.sub("", (cells.get(f"{POWER_NAME}{row}") or "").strip())
        if not raw:
            continue
        resolved = resolve_typed(raw, index)
        if not resolved:
            warn.append(notice("engine.import.skippedUnknown", kind=ui("engine.kind.adeptPower"), name=raw))
            continue
        english, pick = resolved
        spec = by_name[english]
        level = cell_int(cells.get(f"{POWER_LEVEL}{row}"))
        # A power with levels starts at 1 when the column is empty. One without
        # them is a single purchase however the sheet counts it — the template
        # lets a level be typed in anyway (ララ's 潜在力強化 is at 2), and that
        # is the sheet charging power points the rules do not, so it is said.
        rating = max(1, level) if spec.get("levels") else 1
        if level > 1 and not spec.get("levels"):
            warn.append(notice("engine.import.xlsxPowerLevel", name=raw, level=level))
        if pick and not spec.get("select"):
            warn.append(notice("engine.import.xlsxPowerNote", name=raw, note=pick))
            pick = ""
        powers.append({"id": str(uuid.uuid4()), "power_id": spec["id"], "rating": rating, "extra": pick or None})
    if powers:
        st["adept_powers"] = powers


def import_magic(cells: dict[str, str], cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Fill the magic half of `st` from the 呪文／複合体／アデプト・パワー sheet."""
    _import_listed(cells, SPELL_NAME, "spells", "spell_id", list(cat["spells"]), ui("engine.kind.spell"), cat, st, warn)
    _import_listed(
        cells,
        FORM_NAME,
        "complex_forms",
        "form_id",
        list(cat["complex_forms"]),
        ui("engine.kind.complexForm"),
        cat,
        st,
        warn,
    )
    _import_powers(cells, cat, st, warn)


__all__ = ["MENTOR_ALIASES", "import_magic", "mentor_index", "resolve_mentor"]
