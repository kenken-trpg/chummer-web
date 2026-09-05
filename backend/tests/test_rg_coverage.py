"""Phase 5 of docs/plans/translation-plan.md — the Run & Gun ledger.

The RG pass is a verification pass over ~493 catalog names, done a batch at a
time with the book open. These tests keep the record honest between batches:
every name is either checked (`RG`) or deliberately left in English
(`RG_UNVERIFIED`), never both, never invented, and the count only goes up.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.ja_curated_rg import RG, RG_UNVERIFIED
from scripts.make_rg_worksheet import rg_entries

# How many RG names have been decided. Raise it with each batch — a floor rather
# than an equality so a batch lands in one commit, and so re-running the
# generator can never quietly undo work.
DECIDED_FLOOR = 35


@pytest.fixture(scope="module")
def catalog_names() -> set[str]:
    names = set(rg_entries())
    assert names, "no RG entries found — is backend/vendor/chummer populated?"
    return names


def test_no_name_is_both_translated_and_skipped() -> None:
    both = sorted(set(RG) & set(RG_UNVERIFIED))
    assert not both, f"decide one way or the other: {both}"


def test_every_listed_name_exists_in_the_catalog(catalog_names: set[str]) -> None:
    """Guards against typos and against pinning a name the app never shows."""
    orphans = sorted((set(RG) | set(RG_UNVERIFIED)) - catalog_names)
    assert not orphans, "\n  " + "\n  ".join(orphans)


def test_translations_are_japanese() -> None:
    import re

    jp = re.compile(r"[぀-ヿ㐀-鿿]")
    latin = sorted(k for k, v in RG.items() if not jp.search(v))
    assert not latin, f"use RG_UNVERIFIED to leave a name in English: {latin}"


def test_worksheet_shorthands(tmp_path: Path) -> None:
    """'=' pins the `current` column, '-' skips, a term overrides — see the importer.

    The verification pass leans on '=' for most of its several hundred rows, so
    a silent change here would turn "checked against the book" into "copied
    whatever upstream said" without anything failing.
    """
    from scripts.import_rg_worksheet import _read_worksheet

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
    body = "".join(delimiter.join(r) + "\r\n" for r in rows)
    path.write_text(preamble + body, encoding="utf-8-sig")
    return path


def test_reads_a_worksheet_a_spreadsheet_handed_back(tmp_path: Path) -> None:
    """The real shape returned from the first batch: BOM, CRLF, ';', a title row.

    None of that is about the content, so none of it should stop an import.
    """
    from scripts.import_rg_worksheet import _read_worksheet

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
    from scripts.import_rg_worksheet import _read_worksheet

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


def test_worksheet_is_found_by_directory(tmp_path: Path) -> None:
    """The file comes back renamed, so a directory means "the newest one here"."""
    import os

    from scripts.import_rg_worksheet import resolve_worksheet

    assert resolve_worksheet(tmp_path)[0] is None  # nothing there yet
    old = _write(tmp_path / "rg-worksheet.tsv", [("english",)])
    new = _write(tmp_path / "done_rg-worksheet.csv", [("english",)])
    os.utime(old, (1, 1))

    found, note = resolve_worksheet(tmp_path)
    assert found == new
    assert "newest of 2" in note
    assert resolve_worksheet(old)[0] == old  # an explicit file still wins


def test_decided_count_does_not_regress(catalog_names: set[str]) -> None:
    decided = len(set(RG) | set(RG_UNVERIFIED))
    assert decided >= DECIDED_FLOOR, (
        f"{decided} names decided, floor is {DECIDED_FLOOR} — did a worksheet import drop entries?"
    )
    if decided > DECIDED_FLOOR:
        pytest.fail(
            f"{decided} of {len(catalog_names)} RG names decided; raise DECIDED_FLOOR to {decided} "
            "in this file so the progress is pinned"
        )
