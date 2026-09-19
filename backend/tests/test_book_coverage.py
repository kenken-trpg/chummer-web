"""Phase 5 of docs/plans/translation-plan.md — the per-book ledger.

A pass is a walk over one book's catalog names with its Japanese text open,
done a batch at a time. These tests keep the record honest between batches:
every name a pass has reached is either checked (the book's table) or
deliberately left in English (its `_UNVERIFIED` half), never both, never
invented, and the count only goes up.

The shape is the same for every book in `scripts/ja_books.py`, so the ledger
tests are parametrised over it. `DECIDED_FLOOR` is not: how far each pass has
got is a separate fact per book, and a book nobody has started sits at 0.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from scripts.ja_books import BOOKS, Book
from scripts.make_ja_worksheet import book_entries, decided

# How many names each pass has decided. Raise with each batch — a floor rather
# than an equality so a batch lands in one commit, and so re-running the
# generator can never quietly undo work.
DECIDED_FLOOR = {"RG": 35, "RF": 0, "SG": 0, "DT": 0}

BOOK_CODES = sorted(BOOKS)


@pytest.fixture(scope="module")
def names() -> dict[str, set[str]]:
    """Every catalog name per book — built once, the catalog walk is not cheap."""
    out = {code: set(book_entries(BOOKS[code])) for code in BOOK_CODES}
    empty = sorted(code for code, found in out.items() if not found)
    assert not empty, f"no entries found for {empty} — is backend/vendor/chummer populated?"
    return out


def test_every_registered_book_has_a_floor() -> None:
    """A book added to the registry without a floor would burn down unwatched."""
    assert sorted(DECIDED_FLOOR) == BOOK_CODES


@pytest.mark.parametrize("code", BOOK_CODES)
def test_no_name_is_both_translated_and_skipped(code: str) -> None:
    verified, skipped = decided(BOOKS[code])
    both = sorted(set(verified) & set(skipped))
    assert not both, f"decide one way or the other: {both}"


@pytest.mark.parametrize("code", BOOK_CODES)
def test_every_listed_name_exists_in_the_catalog(code: str, names: dict[str, set[str]]) -> None:
    """Guards against typos and against pinning a name the app never shows."""
    verified, skipped = decided(BOOKS[code])
    orphans = sorted((set(verified) | set(skipped)) - names[code])
    assert not orphans, "\n  " + "\n  ".join(orphans)


@pytest.mark.parametrize("code", BOOK_CODES)
def test_translations_are_japanese(code: str) -> None:
    jp = re.compile(r"[぀-ヿ㐀-鿿]")
    verified, _ = decided(BOOKS[code])
    latin = sorted(k for k, v in verified.items() if not jp.search(v))
    assert not latin, f"use {BOOKS[code].skipped_table} to leave a name in English: {latin}"


@pytest.mark.parametrize("code", BOOK_CODES)
def test_decided_count_does_not_regress(code: str, names: dict[str, set[str]]) -> None:
    book: Book = BOOKS[code]
    verified, skipped = decided(book)
    count = len(set(verified) | set(skipped))
    floor = DECIDED_FLOOR[code]
    assert count >= floor, f"{count} {code} names decided, floor is {floor} — did a worksheet import drop entries?"
    if count > floor:
        pytest.fail(
            f"{count} of {len(names[code])} {code} names decided; raise DECIDED_FLOOR[{code!r}] "
            f"to {count} in this file so the progress is pinned"
        )


def test_worksheet_shorthands(tmp_path: Path) -> None:
    """'=' pins the `current` column, '-' skips, a term overrides — see the importer.

    The verification pass leans on '=' for most of Run & Gun's several hundred
    rows, so a silent change here would turn "checked against the book" into
    "copied whatever upstream said" without anything failing.
    """
    from scripts.import_ja_worksheet import _read_worksheet

    rows = [
        ("english", "current", "official"),
        ("Aikido", "合気道", "="),  # agrees with upstream -> pinned as 合気道
        ("Bartitsu", "バリツ", "バーティツ"),  # the book differs -> the book wins
        ("AK-98", "", "-"),  # printed in Latin either way
        ("Krav Maga", "", "="),  # nothing to agree with -> a problem
    ]
    sheet = _write(tmp_path / "ws.tsv", rows)
    got = _read_worksheet(sheet)

    assert got.translations == {"Aikido": "合気道", "Bartitsu": "バーティツ"}
    assert got.skipped == {"AK-98"}
    assert got.problems == ["L5: 'Krav Maga' marked '=' but its `current` column is empty"]


def _write(path: Path, rows: list[tuple[str, ...]], delimiter: str = "\t", preamble: str = "") -> Path:
    r"""Write the worksheet with the CRLF a spreadsheet really emits.

    `write_text` would not do: it opens in text mode, where Windows translates
    every `\n` on the way out, so the `\r\n` written here lands as `\r\r\n` and
    the reader — correctly — sees a blank line that was never in the fixture.
    Bytes, so the file holds exactly what a spreadsheet would have put there on
    any platform.
    """
    body = "".join(delimiter.join(r) + "\r\n" for r in rows)
    path.write_bytes((preamble + body).encode("utf-8-sig"))
    return path


def test_reads_a_worksheet_a_spreadsheet_handed_back(tmp_path: Path) -> None:
    """The real shape returned from the first batch: BOM, CRLF, ';', a title row.

    None of that is about the content, so none of it should stop an import.
    """
    from scripts.import_ja_worksheet import _read_worksheet

    sheet = _write(
        tmp_path / "done_rg-worksheet.csv",
        [("status", "english", "current", "official"), ("pending", "Aikido", "合気道", "=")],
        delimiter=";",
        preamble="rg-worksheet\r\n",
    )
    got = _read_worksheet(sheet)

    assert got.translations == {"Aikido": "合気道"}
    assert not got.problems
    assert got.notes == ["skipped 1 line(s) above the header", "delimiter is ';', not tab"]


def test_an_answer_in_the_wrong_column_is_reported_not_harvested(tmp_path: Path) -> None:
    """The first batch's actual failure: answers typed into `current` and `note`.

    Importing `current` silently would be worse than dropping it — most rows
    carry an unverified upstream term there, and harvesting the column would
    record the community translation as if a human had checked it in the book.
    """
    from scripts.import_ja_worksheet import _read_worksheet

    rows = [
        ("english", "current", "official", "note"),
        ("Illuminating", "発光", "", ""),  # typed over an empty `current`
        ("Chainsaw", "", "", "チェーンソー"),  # typed into `note`
        ("Aikido", "合気道", "", ""),  # untouched: generator wrote this
    ]
    sheet = _write(tmp_path / "ws.tsv", rows)
    expected = {"Illuminating": "", "Chainsaw": "", "Aikido": "合気道"}

    got = _read_worksheet(sheet, expected_current=expected)
    assert got.translations == {}
    assert [p.split(" has ")[0] for p in got.problems] == ["L2: 'Illuminating'", "L3: 'Chainsaw'"]

    took = _read_worksheet(sheet, accept=("current", "note"), expected_current=expected)
    assert took.translations == {"Illuminating": "発光", "Chainsaw": "チェーンソー"}
    assert not took.problems


def test_worksheet_is_found_by_the_books_own_name(tmp_path: Path) -> None:
    """The file comes back renamed, so a directory means "the newest one here".

    Per book, though: two passes running side by side leave two worksheets in
    the same download folder, and importing RF's answers into RG's table would
    be silent — every name would be an orphan, but only after `--write`.
    """
    import os

    from scripts.import_ja_worksheet import resolve_worksheet

    rg, rf = BOOKS["RG"], BOOKS["RF"]
    assert resolve_worksheet(tmp_path, rg)[0] is None  # nothing there yet
    old = _write(tmp_path / "rg-worksheet.tsv", [("english",)])
    new = _write(tmp_path / "done_rg-worksheet.csv", [("english",)])
    other = _write(tmp_path / "rf-worksheet.tsv", [("english",)])
    os.utime(old, (1, 1))

    found, note = resolve_worksheet(tmp_path, rg)
    assert found == new
    assert "newest of 2" in note
    assert resolve_worksheet(tmp_path, rf)[0] == other
    assert resolve_worksheet(old, rg)[0] == old  # an explicit file still wins


def test_a_books_module_is_written_with_its_own_table_names(tmp_path: Path) -> None:
    """The generated half names the book, and a book with no module yet gets one.

    Registering a book in `ja_books.py` is meant to be the whole registration,
    so the first `--write` of a pass cannot require a file somebody remembered
    to create by hand — and what it creates has to be importable and already
    formatted the way `ruff format` wants it, or CI fails on generated output.
    """
    from scripts.import_ja_worksheet import _preserved_head, _render

    book = BOOKS["DT"]
    fresh = tmp_path / "ja_curated_dt.py"
    head = _preserved_head(fresh, book)
    assert head is not None
    body = head + _render({"AR Game": "ARゲーム"}, {"A.I."}, book)

    assert "DT: dict[str, str] = {" in body
    assert 'DT_UNVERIFIED: tuple[str, ...] = ("A.I.",)' in body
    assert "RG" not in body
    fresh.write_text(body, encoding="utf-8")
    compile(body, str(fresh), "exec")  # importable, not just plausible


def test_the_prose_above_the_marker_survives_a_rewrite(tmp_path: Path) -> None:
    """Everything a human wrote about a pass lives above the generated tables."""
    from scripts.import_ja_worksheet import _preserved_head, marker

    book = BOOKS["RG"]
    module = tmp_path / "ja_curated_rg.py"
    module.write_text(f'"""Why this pass exists."""\n\n{marker(book)}\n}}\n', encoding="utf-8")

    assert _preserved_head(module, book) == '"""Why this pass exists."""\n\n'
    module.write_text("no marker here\n", encoding="utf-8")
    assert _preserved_head(module, book) is None
