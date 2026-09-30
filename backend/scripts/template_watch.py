#!/usr/bin/env python3
"""Watch シャドウラン_キャラシテンプレート for the changes that break its import.

The template (音の兔 様) is a living Google Sheets document: it is revised
whenever the community finds something to fix, and a revision can move a cell,
rename a sheet, widen a block or add a dropdown entry. The .xlsx import reads it
by fixed address in places, so a revision can quietly drop half a character
without anything failing — which is exactly the kind of breakage a test suite
built on a fixture never sees.

So this script does what a test cannot: it fetches the live sheet, reduces it to
the handful of facts the import actually leans on, and diffs those against a
baseline checked in beside it. Every difference is printed with the code that has
to move with it, so the output is a work list rather than a diff.

What is watched, and why each one matters:

* **the sheet names** — `_common.SHEET_*` and `REQUIRED_SHEETS`. A renamed sheet
  is either a skipped section or a refused upload.
* **the dropdowns** (the sheet's own data validations) — both their *ranges*,
  which are where the row blocks the import walks come from (`QUALITY_ROWS`,
  `WARE_ROWS`, `KNOWLEDGE_ROWS`, …), and their *entries*, which the mapping
  tables have to cover (`METATYPES`, `TALENTS`, `GRADES`,
  `KNOWLEDGE_CATEGORIES`).
* **the header-row labels** — the column letters (`COLUMN_POINTS`, `WARE_GRADE`,
  `GEAR_PRICE`, …) are only right for as long as each label stays in its column.
* **the anchor cells** — the labels sitting beside the fixed addresses
  (`PRIORITY_CELLS`, `KARMA_NUYEN_CELL`, `ATTRIBUTE_ROWS`). A row inserted above
  them moves every one.
* **the section headings** and how far each block runs — `DEVICES_OFFSET`
  / `DEVICES_COUNT`, `POWERS_*`, `KARMA_*`.
* **the skill list**, resolved through the same index the import builds, so a
  renamed or added skill shows up as a name nothing matches rather than as a
  warning in somebody's import.

Usage::

    ./.venv/bin/python scripts/template_watch.py            # check against the baseline
    ./.venv/bin/python scripts/template_watch.py --json      # the same, as JSON
    ./.venv/bin/python scripts/template_watch.py --update    # adopt what is live now
    ./.venv/bin/python scripts/template_watch.py --file a.xlsx  # a local download

Exit code 1 means there is something to do — so this can be run from a cron and
looked at only when it says so. A network failure exits 2, which is not a finding
about the template.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import zipfile
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.data_loader import catalog  # noqa: E402
from app.notices import NoticeError  # noqa: E402
from app.sheets_url import fetch_sheet  # noqa: E402
from app.xlsx_import import REQUIRED_SHEETS  # noqa: E402
from app.xlsx_import._common import (  # noqa: E402
    SHEET_BASICS,
    SHEET_CONTACTS,
    SHEET_GEAR,
    SHEET_KNOWLEDGE,
    SHEET_MAGIC,
    SHEET_SKILLS,
    SHEET_WARE,
    japanese_index,
)
from app.xlsx_import._sheet import NotAWorkbook, Workbook  # noqa: E402
from app.xlsx_import.basics import METATYPES, TALENTS  # noqa: E402
from app.xlsx_import.contacts import KARMA_COUNT, KARMA_HEADING, KARMA_OFFSET  # noqa: E402
from app.xlsx_import.magic import POWERS_COUNT, POWERS_HEADING, POWERS_OFFSET  # noqa: E402
from app.xlsx_import.skills import (  # noqa: E402
    GROUP_ALIASES,
    GROUPS_HEADING,
    KNOWLEDGE_CATEGORIES,
    SKILL_ALIASES,
    SKILLS_HEADING,
    _sections,
)
from app.xlsx_import.ware import DEVICES_COUNT, DEVICES_HEADING, DEVICES_OFFSET, GRADES  # noqa: E402

#: The template this watches. The document the wiki points at, not a copy: a
#: player's own copy has their character in it and is revised by nobody.
SHEET_ID = "1s_kEWwXbTKxbfnU7wc9-z2xkS_1MOzQvKi9asXCQ1rg"

BASELINE = Path(__file__).with_name("template_baseline.json")

#: The shape of a snapshot. Bumped whenever what is recorded changes, so a
#: baseline written by an older version of this script is refused rather than
#: diffed field by field against a shape it never had.
FORMAT = 1

_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
#: A range in another sheet, the way a validation writes one:
#: ``'編集不可'!$A$2:$F$7``.
_REFERENCE = re.compile(r"^'?([^'!]+)'?!\$?([A-Z]+)\$?(\d+)(?::\$?([A-Z]+)\$?(\d+))?$")
#: A literal list: ``"A,B,C,D,E"``.
_LITERAL = re.compile(r'^"(.*)"$')
#: One cell of an sqref, for reading a block's first and last row out of it.
_CELL = re.compile(r"^([A-Z]+)(\d+)(?::([A-Z]+)(\d+))?$")


# ── what is watched ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Header:
    """A header row whose labels pin the column letters under them."""

    sheet: str
    row: int
    owns: str


#: Every row of column labels the import counts on. The devices block has its
#: own, further down the same sheet.
HEADERS = (
    Header(SHEET_SKILLS, 2, "skills.COLUMN_POINTS / COLUMN_KARMA / COLUMN_SPEC_*"),
    Header(SHEET_KNOWLEDGE, 2, "skills knowledge columns (A/B/E/F/H/I)"),
    Header(SHEET_MAGIC, 2, "magic.SPELL_NAME / FORM_NAME"),
    Header(SHEET_WARE, 2, "ware.WARE_NAME / WARE_GRADE / WARE_RATING"),
    Header(SHEET_WARE, 36, "ware.DEVICE_NAME / DEVICE_RATING"),
    Header(SHEET_GEAR, 2, "gear.GEAR_NAME / GEAR_PRICE / GEAR_BOUGHT / GEAR_NOTE"),
    Header(SHEET_CONTACTS, 3, "contacts.COLUMN_CONNECTION / COLUMN_LOYALTY / COLUMN_FREE_*"),
    Header(SHEET_CONTACTS, 26, "contacts.KARMA_NAME / KARMA_SPENT"),
)

#: The cells read by address, each recorded through the label that sits with it.
#: The expected text is not written here: it is whatever the baseline holds, so
#: adopting a revision is one `--update` rather than an edit in two places.
ANCHORS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (SHEET_BASICS, ("A3", "A7", "A8", "A12", "A13"), "basics.PRIORITY_CELLS"),
    (SHEET_BASICS, ("A16", "A17"), "basics.METATYPES / TALENTS cells (C16/C17)"),
    (SHEET_BASICS, ("AC3",), "basics.KARMA_NUYEN_CELL (AC4)"),
    (SHEET_BASICS, tuple(f"D{row}" for row in range(19, 30)), "basics.ATTRIBUTE_ROWS"),
    (SHEET_BASICS, ("A48", "A49"), "qualities.QUALITY_ROWS"),
)


@dataclass(frozen=True)
class Block:
    """A block found by its heading, and the column its rows are named in.

    The heading is searched for by text, so moving it is harmless — but how many
    rows follow it is a constant, and that is what this measures.
    """

    sheet: str
    heading: str
    column: str
    owns: str
    #: The window the import reads, as the code's own offset and count.
    offset: int
    count: int
    #: Which of the two measures says where this block ends: `filled` for a block
    #: whose rows are labelled in advance, `styled` for one a player types into.
    measure: str


BLOCKS = (
    Block(
        SHEET_MAGIC, POWERS_HEADING, "A", "magic.POWERS_OFFSET / POWERS_COUNT", POWERS_OFFSET, POWERS_COUNT, "styled"
    ),
    Block(
        SHEET_WARE,
        DEVICES_HEADING,
        "A",
        "ware.DEVICES_OFFSET / DEVICES_COUNT",
        DEVICES_OFFSET,
        DEVICES_COUNT,
        "filled",
    ),
    Block(
        SHEET_CONTACTS, KARMA_HEADING, "A", "contacts.KARMA_OFFSET / KARMA_COUNT", KARMA_OFFSET, KARMA_COUNT, "styled"
    ),
)


@dataclass(frozen=True)
class Covered:
    """A dropdown whose entries a mapping table has to know.

    `tolerated` is the entries deliberately left unhandled: the import warns
    about them rather than guessing, and they are listed so that a *new* entry
    still stands out.
    """

    sheet: str
    sqref: str
    known: frozenset[str]
    tolerated: frozenset[str]
    owns: str


COVERED = (
    # カスタム is the sheet's escape hatch for a metatype it does not list; there
    # is nothing to map it to.
    Covered(SHEET_BASICS, "C16", frozenset(METATYPES), frozenset({"カスタム"}), "basics.METATYPES"),
    Covered(SHEET_BASICS, "C17", frozenset(TALENTS), frozenset(), "basics.TALENTS"),
    # The two other play levels are the priority method under a different table,
    # which this app does not offer — `import_basics` says so and carries on.
    Covered(
        SHEET_BASICS,
        "W1",
        frozenset({"通常のプレイレベル", "800カルマ割り振り"}),
        frozenset({"ストリートレベル", "プライム・ランナーレベル"}),
        "basics.LEVEL_NORMAL / LEVEL_KARMA",
    ),
    Covered(SHEET_KNOWLEDGE, "A3:A27", frozenset(KNOWLEDGE_CATEGORIES), frozenset(), "skills.KNOWLEDGE_CATEGORIES"),
    Covered(SHEET_WARE, "N4:N33", frozenset(GRADES), frozenset(), "ware.GRADES"),
)

#: The row blocks that come from a dropdown's range, and the constant each is.
RANGES = {
    (SHEET_BASICS, "C3 C7:C8 C12:C13"): "basics.PRIORITY_CELLS",
    (SHEET_BASICS, "A50:A59"): "qualities.QUALITY_ROWS",
    (SHEET_KNOWLEDGE, "A3:A27"): "skills.KNOWLEDGE_ROWS",
    (SHEET_MAGIC, "A3:A22"): "magic.NAMES_FROM_ROW and the spell/form row span",
    (SHEET_WARE, "N4:N33"): "ware.WARE_ROWS",
}


# ── reading the workbook ────────────────────────────────────────────────────


def _validations(body: bytes, workbook: Workbook) -> dict[str, dict[str, list[str]]]:
    """``{sheet: {sqref: [entry, …]}}`` for every list validation in the book.

    `Workbook` reads values and nothing else, on purpose, so the validations are
    parsed here rather than there: they are a development question, not something
    an import needs.
    """
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        parts = {name for name in archive.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", name)}
        # `Workbook` already worked out which part each sheet is; matching on
        # the part name keeps this from depending on the order they happen to be
        # zipped. Reaching into it is the price of leaving the reader alone: the
        # import has no use for a validation.
        by_part = {part: name for name, part in workbook.sheet_parts.items() if part in parts}
        out: dict[str, dict[str, list[str]]] = {}
        for part, sheet in sorted(by_part.items()):
            found: dict[str, list[str]] = {}
            text = archive.read(part).decode("utf-8", "replace")
            for match in re.finditer(r"<dataValidation\b([^>]*)>(.*?)</dataValidation>", text, re.S):
                sqref = re.search(r'sqref="([^"]*)"', match.group(1))
                formula = re.search(r"<formula1>(.*?)</formula1>", match.group(2), re.S)
                if not sqref or not formula:
                    continue
                found[sqref.group(1)] = _entries(formula.group(1), workbook)
            if found:
                out[sheet] = found
    return out


def _styles(body: bytes, workbook: Workbook, sheets: Iterable[str]) -> dict[str, dict[str, str]]:
    """``{sheet: {ref: format id}}`` — how a cell is formatted, not what it holds.

    The only reason to look: an empty cell a player is meant to type into is
    still a formatted cell, so this is what says how far a block of them runs
    when the template is blank. `Workbook` reads values and skips this on
    purpose; see `_validations` for why that stays true.
    """
    wanted = {name: part for name, part in workbook.sheet_parts.items() if name in set(sheets)}
    out: dict[str, dict[str, str]] = {}
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        for sheet, part in wanted.items():
            text = archive.read(part).decode("utf-8", "replace")
            out[sheet] = {
                match.group(1): match.group(2) for match in re.finditer(r'<c r="([A-Z]+\d+)"[^>]*?\bs="(\d+)"', text)
            }
    return out


def _entries(formula: str, workbook: Workbook) -> list[str]:
    """A validation's entries, whether written out or held in another sheet."""
    written = formula.strip().replace("&quot;", '"')
    literal = _LITERAL.match(written)
    if literal:
        return [part.strip() for part in literal.group(1).split(",") if part.strip()]
    reference = _REFERENCE.match(written)
    if not reference:
        return []
    sheet, first_col, first_row, last_col, last_row = reference.groups()
    try:
        cells = workbook.cells(sheet)
    except NotAWorkbook:
        return []
    rows = range(int(first_row), int(last_row or first_row) + 1)
    columns = _columns(first_col, last_col or first_col)
    # Read down each column and then across: the lists in 編集不可 are one column
    # wide with the rest of the range left empty, and an empty cell is not an
    # entry.
    return [text for column in columns for row in rows if (text := cells.get(f"{column}{row}"))]


def _columns(first: str, last: str) -> list[str]:
    """The column letters from `first` to `last`, inclusive."""
    return [_letters(index) for index in range(_index(first), _index(last) + 1)]


def _index(letters: str) -> int:
    value = 0
    for char in letters:
        value = value * 26 + (ord(char) - 64)
    return value


def _letters(index: int) -> str:
    out = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        out = chr(65 + remainder) + out
    return out


def _row(ref: str) -> int:
    return int(re.sub(r"\D", "", ref))


def _column(ref: str) -> str:
    return re.sub(r"\d", "", ref)


def _header(cells: dict[str, str], row: int) -> dict[str, str]:
    """``{column: label}`` for one header row."""
    return {_column(ref): text for ref, text in cells.items() if _row(ref) == row}


def _block_span(cells: dict[str, str], styles: dict[str, str], heading: str, column: str) -> dict[str, int] | None:
    """Where a heading's block starts and how far it runs.

    A blank template is the only version there is to read — nobody publishes a
    filled-in one — so the rows a player types into are empty, and counting
    filled cells would measure nothing. Two things are measured instead, because
    the sheets delimit a block both ways:

    * `filled`, the last of the contiguous rows that already hold text. The
      device block is like this: its rows are labelled コムリンク / サイバーデッキ
      in advance.
    * `styled`, the end of the run of rows sharing one cell format. The blocks a
      player fills in are like this: twenty identically bordered empty cells.

    Neither is exact on its own, and neither has to be: what they are for is
    being the same number next time, so that a block that grew says so.
    """
    labelled = sorted((_row(ref), text) for ref, text in cells.items() if _column(ref) == column)
    at = next((row for row, text in labelled if text.strip() == heading), None)
    if at is None:
        return None
    filled = at
    for row, _text in labelled:
        if row <= at:
            continue
        # Up to two rows of column headings, and the empty row some sheets put
        # between them and the block, sit between the heading and its rows.
        if row - filled > (3 if filled == at else 1):
            break
        filled = row
    return {"heading": at, "filled": filled, "styled": _styled_run(styles, column, at)}


#: How many rows of one format make a block rather than a coincidence. Two rows
#: of heading under a heading share a format often enough.
_RUN_MINIMUM = 3


def _styled_run(styles: dict[str, str], column: str, heading: int) -> int:
    """The last row of the first run of ≥3 identically formatted rows below
    `heading`, or the heading's own row if there is none."""
    below = sorted(
        (_row(ref), style) for ref, style in styles.items() if _column(ref) == column and _row(ref) > heading
    )
    run_style, run_first, run_last = "", 0, 0
    for row, style in below:
        if style == run_style and row == run_last + 1:
            run_last = row
            continue
        if run_last - run_first + 1 >= _RUN_MINIMUM:
            break
        run_style, run_first, run_last = style, row, row
    return run_last if run_last - run_first + 1 >= _RUN_MINIMUM else heading


def _sections_of(cells: dict[str, str]) -> list[list[Any]]:
    """The skill sheet's own section headings, as ``[[row, text], …]``.

    `skills._sections` cuts the sheet at these rather than trusting a row
    number, so a new section is not a break — but it is a section nobody has
    looked at, and a renamed one takes its whole block of skills with it.
    """
    return [
        [row, text]
        for ref, text in sorted(cells.items(), key=lambda kv: _row(kv[0]))
        if _column(ref) == "A"
        and ((row := _row(ref)) or True)
        and (text == GROUPS_HEADING or SKILLS_HEADING.search(text))
    ]


def _skill_names(cells: dict[str, str]) -> dict[str, list[str]]:
    """The group and skill names the active sheet lists, in its own order."""
    groups, skills = _sections(cells)
    return {
        "groups": [text for row in groups if (text := (cells.get(f"A{row}") or "").strip())],
        "skills": [text for row in skills if (text := (cells.get(f"A{row}") or "").strip())],
    }


def snapshot(body: bytes) -> dict[str, Any]:
    """The template reduced to what the import leans on."""
    workbook = Workbook(body)
    names = workbook.sheet_names
    cells = {name: workbook.cells(name) for name in names if name in _WATCHED_SHEETS}
    styles = _styles(body, workbook, {block.sheet for block in BLOCKS})
    return {
        "format": FORMAT,
        "taken": date.today().isoformat(),
        "sheets": names,
        "validations": _validations(body, workbook),
        "headers": {
            f"{header.sheet}!{header.row}": _header(cells.get(header.sheet, {}), header.row) for header in HEADERS
        },
        "anchors": {
            f"{sheet}!{ref}": cells.get(sheet, {}).get(ref, "") for sheet, refs, _owns in ANCHORS for ref in refs
        },
        "blocks": {
            f"{block.sheet}!{block.heading}": _block_span(
                cells.get(block.sheet, {}), styles.get(block.sheet, {}), block.heading, block.column
            )
            for block in BLOCKS
        },
        "sections": _sections_of(cells.get(SHEET_SKILLS, {})),
        "skills": _skill_names(cells.get(SHEET_SKILLS, {})),
    }


_WATCHED_SHEETS = {
    SHEET_BASICS,
    SHEET_SKILLS,
    SHEET_KNOWLEDGE,
    SHEET_MAGIC,
    SHEET_WARE,
    SHEET_GEAR,
    SHEET_CONTACTS,
}


# ── turning a difference into something to do ───────────────────────────────


@dataclass
class Finding:
    """One thing to do, and the code it is about."""

    kind: str
    what: str
    owns: str

    def line(self) -> str:
        return f"  [{self.kind}] {self.what}\n      → {self.owns}"


def _owner_of(sheet: str, sqref: str, *, about: str) -> str:
    """The code a change to one dropdown is about.

    Which code depends on what changed: a dropdown's *range* is where a row
    block's bounds come from, while its *entries* are what a mapping table has
    to cover. The same dropdown usually has one of each.
    """
    mapping = next((c.owns for c in COVERED if c.sheet == sheet and c.sqref == sqref), "")
    rows = RANGES.get((sheet, sqref), "")
    first, second = (mapping, rows) if about == "entries" else (rows, mapping)
    return first or second or "no code reads this one yet — check whether it should"


def compare(old: dict[str, Any], new: dict[str, Any]) -> list[Finding]:
    """What changed between two snapshots, as work rather than as a diff."""
    if old.get("format") != new["format"]:
        return [
            Finding(
                "baseline stale",
                f"the baseline was written in format {old.get('format', 0)}, this script writes {new['format']}",
                "re-run with --update, then diff the baseline by hand this once",
            )
        ]
    out: list[Finding] = []
    out += _compare_sheets(old, new)
    out += _compare_validations(old, new)
    out += _compare_mapping(old.get("headers", {}), new.get("headers", {}), "header", HEADER_OWNERS)
    out += _compare_mapping(old.get("anchors", {}), new.get("anchors", {}), "anchor", ANCHOR_OWNERS)
    out += _compare_blocks(old, new)
    out += _compare_sections(old, new)
    out += _compare_skills(old, new)
    return out


def _compare_sheets(old: dict[str, Any], new: dict[str, Any]) -> list[Finding]:
    before, after = old.get("sheets") or [], new.get("sheets") or []
    out: list[Finding] = []
    for name in before:
        if name in after:
            continue
        owns = "xlsx_import.REQUIRED_SHEETS" if name in REQUIRED_SHEETS else "_common.SHEET_* and its importer"
        out.append(Finding("sheet gone", f"「{name}」 is no longer in the book", owns))
    for name in after:
        if name not in before:
            out.append(Finding("sheet new", f"「{name}」 was added", "decide whether anything in it is worth reading"))
    if before and after and before != after and set(before) == set(after):
        out.append(Finding("sheet order", "the sheets are in a different order", "nothing — order is not read"))
    return out


def _compare_validations(old: dict[str, Any], new: dict[str, Any]) -> list[Finding]:
    before, after = old.get("validations") or {}, new.get("validations") or {}
    out: list[Finding] = []
    for sheet in sorted(set(before) | set(after)):
        was, now = before.get(sheet, {}), after.get(sheet, {})
        for sqref in sorted(set(was) - set(now)):
            out.append(
                Finding(
                    "range gone", f"{sheet}!{sqref} has no dropdown any more", _owner_of(sheet, sqref, about="range")
                )
            )
        for sqref in sorted(set(now) - set(was)):
            # A block that grew is written as a new range rather than a changed
            # one, because the sqref is the key.
            out.append(
                Finding("range new", f"{sheet}!{sqref} is a dropdown now", _owner_of(sheet, sqref, about="range"))
            )
        for sqref in sorted(set(was) & set(now)):
            gone = [entry for entry in was[sqref] if entry not in now[sqref]]
            added = [entry for entry in now[sqref] if entry not in was[sqref]]
            if gone:
                out.append(
                    Finding(
                        "entry gone",
                        f"{sheet}!{sqref} dropped {'、'.join(gone)}",
                        _owner_of(sheet, sqref, about="entries"),
                    )
                )
            if added:
                out.append(
                    Finding(
                        "entry new",
                        f"{sheet}!{sqref} offers {'、'.join(added)}",
                        _owner_of(sheet, sqref, about="entries"),
                    )
                )
    return out


HEADER_OWNERS = {f"{header.sheet}!{header.row}": header.owns for header in HEADERS}
ANCHOR_OWNERS = {f"{sheet}!{ref}": owns for sheet, refs, owns in ANCHORS for ref in refs}


def _compare_mapping(before: dict[str, Any], after: dict[str, Any], kind: str, owners: dict[str, str]) -> list[Finding]:
    """Header rows and anchor cells, which differ the same way.

    A header row is compared column by column rather than label by label,
    because the labels repeat — 「コネ値」 sits over four columns of the contact
    sheet — and a label that occurs twice cannot be said to have moved.
    """
    out: list[Finding] = []
    for key in sorted(set(before) | set(after)):
        was, now = before.get(key), after.get(key)
        if was == now:
            continue
        owns = owners.get(key, "unclaimed")
        if isinstance(was, dict) and isinstance(now, dict):
            for column in sorted(set(was) | set(now), key=_index):
                if was.get(column) == now.get(column):
                    continue
                out.append(
                    Finding(
                        f"{kind} changed",
                        f"{key} column {column}: 「{was.get(column, '')}」 → 「{now.get(column, '')}」",
                        owns,
                    )
                )
            continue
        out.append(Finding(f"{kind} changed", f"{key}: 「{was}」 → 「{now}」", owns))
    return out


def _compare_blocks(old: dict[str, Any], new: dict[str, Any]) -> list[Finding]:
    before, after = old.get("blocks") or {}, new.get("blocks") or {}
    owners = {f"{block.sheet}!{block.heading}": block.owns for block in BLOCKS}
    out: list[Finding] = []
    for key in sorted(set(before) | set(after)):
        was, now = before.get(key), after.get(key)
        owns = owners.get(key, "unclaimed")
        if now is None:
            # The heading is how the importer finds the block at all: without it
            # the section is silently skipped rather than read wrongly.
            out.append(Finding("heading gone", f"{key} is not on its sheet any more", owns))
            continue
        if was is None or was == now:
            continue
        for measure in ("filled", "styled"):
            rows_before = was[measure] - was["heading"]
            rows_after = now[measure] - now["heading"]
            if rows_before != rows_after:
                out.append(
                    Finding("block resized", f"{key}: {rows_before} {measure} rows under it → {rows_after}", owns)
                )
        if was["heading"] != now["heading"] and was["filled"] - was["heading"] == now["filled"] - now["heading"]:
            out.append(
                Finding("block moved", f"{key}: row {was['heading']} → {now['heading']}", "nothing — found by text")
            )
    return out


def _compare_sections(old: dict[str, Any], new: dict[str, Any]) -> list[Finding]:
    before = {text for _row, text in old.get("sections") or []}
    after = {text for _row, text in new.get("sections") or []}
    owns = "skills.GROUPS_HEADING / SKILLS_HEADING"
    return [Finding("section gone", f"「{t}」 is not a heading any more", owns) for t in sorted(before - after)] + [
        Finding("section new", f"「{t}」 is a new section", owns) for t in sorted(after - before)
    ]


def _compare_skills(old: dict[str, Any], new: dict[str, Any]) -> list[Finding]:
    before, after = old.get("skills") or {}, new.get("skills") or {}
    out: list[Finding] = []
    for part, owns in (("groups", "skills.GROUP_ALIASES"), ("skills", "skills.SKILL_ALIASES")):
        was, now = before.get(part) or [], after.get(part) or []
        for name in [n for n in was if n not in now]:
            out.append(Finding("skill gone", f"「{name}」 is no longer listed", owns))
        for name in [n for n in now if n not in was]:
            out.append(Finding("skill new", f"「{name}」 was added", owns))
    return out


def unmatched(current: dict[str, Any]) -> list[Finding]:
    """What the code cannot make sense of in the template as it stands now.

    Independent of the baseline: this is true of the live sheet whether or not it
    changed, so a dropdown entry nobody ever handled is reported on the first run
    rather than never.
    """
    out: list[Finding] = []
    for covered in COVERED:
        entries = (current.get("validations") or {}).get(covered.sheet, {}).get(covered.sqref)
        if entries is None:
            out.append(
                Finding(
                    "dropdown gone",
                    f"{covered.sheet}!{covered.sqref} is not a dropdown any more",
                    covered.owns,
                )
            )
            continue
        unknown = [e for e in entries if e not in covered.known and e not in covered.tolerated]
        if unknown:
            out.append(
                Finding("unmapped entry", f"{covered.sheet}!{covered.sqref}: {'、'.join(unknown)}", covered.owns)
            )
    out += _shortfall(current)
    out += _unmatched_skills(current)
    return out


def _shortfall(current: dict[str, Any]) -> list[Finding]:
    """Blocks the template offers more rows of than the import reads.

    One-sided on purpose. Reading past the end of a block costs nothing — the
    rows are empty — but stopping short of it drops whatever the player wrote
    there without a word, which is the failure this whole script is about.
    """
    out: list[Finding] = []
    for block in BLOCKS:
        span = (current.get("blocks") or {}).get(f"{block.sheet}!{block.heading}")
        if not span:
            continue
        last_read = span["heading"] + block.offset + block.count - 1
        last_there = span[block.measure]
        if last_there > last_read:
            out.append(
                Finding(
                    "block under-read",
                    f"{block.sheet}!{block.heading}: rows {last_read + 1}-{last_there} are not read"
                    f" (reads {block.count} from row {span['heading'] + block.offset})",
                    block.owns,
                )
            )
    return out


def _unmatched_skills(current: dict[str, Any]) -> list[Finding]:
    """Listed skills the catalog has no Japanese name for.

    Resolved through the same index `import_skills` builds, so this answers the
    question the import will be asked rather than a similar one.
    """
    try:
        cat = catalog()
    except Exception as exc:  # the vendored data is not there; not a template finding
        return [Finding("skipped", f"skill names not checked: {exc}", "run 'make data' first")]
    listed = current.get("skills") or {}
    out: list[Finding] = []
    for part, names, aliases, owns in (
        ("group", cat["skills"]["group_names"], GROUP_ALIASES, "skills.GROUP_ALIASES"),
        ("skill", [row["name"] for row in cat["skills"]["skills"]], SKILL_ALIASES, "skills.SKILL_ALIASES"),
    ):
        index = japanese_index(cat, [str(name) for name in names], "skill")
        missing = [
            name
            for name in (listed.get("groups" if part == "group" else "skills") or [])
            if not index.get(name) and not index.get(aliases.get(name, "")) and not aliases.get(name)
        ]
        if missing:
            out.append(Finding("unmatched name", f"{part}: {'、'.join(missing)}", owns))
    return out


# ── cli ─────────────────────────────────────────────────────────────────────


def _load(args: argparse.Namespace) -> bytes:
    if args.file:
        return Path(args.file).read_bytes()
    return fetch_sheet(f"https://docs.google.com/spreadsheets/d/{args.id}/edit")


def _print(findings: Iterable[Finding], current: dict[str, Any], baseline: dict[str, Any] | None) -> None:
    findings = list(findings)
    if baseline is None:
        print("no baseline yet — run with --update to write one")
    else:
        print(f"baseline taken {baseline.get('taken', '?')}, sheet read {current['taken']}")
    if not findings:
        print("nothing to do: the template still matches what the import expects")
        return
    print(f"\n{len(findings)} thing(s) to look at:")
    for finding in findings:
        print(finding.line())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--id", default=SHEET_ID, help="the Google Sheets document id")
    ap.add_argument("--file", help="read a downloaded .xlsx instead of fetching")
    ap.add_argument("--update", action="store_true", help="write what is live now as the new baseline")
    ap.add_argument("--json", action="store_true", dest="as_json", help="print the findings as JSON")
    args = ap.parse_args()

    try:
        body = _load(args)
    except (NoticeError, OSError) as exc:
        print(f"could not read the template: {exc}", file=sys.stderr)
        return 2
    try:
        current = snapshot(body)
    except NotAWorkbook as exc:
        print(f"not a readable workbook: {exc}", file=sys.stderr)
        return 2

    baseline = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.exists() else None
    findings = (compare(baseline, current) if baseline else []) + unmatched(current)

    if args.as_json:
        print(
            json.dumps(
                {
                    "taken": current["taken"],
                    "baseline": (baseline or {}).get("taken"),
                    "findings": [vars(f) for f in findings],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        _print(findings, current, baseline)

    if args.update:
        BASELINE.write_text(json.dumps(current, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if not args.as_json:
            print(
                f"\nbaseline written: {BASELINE.relative_to(Path.cwd()) if BASELINE.is_relative_to(Path.cwd()) else BASELINE}"
            )
        return 0
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
