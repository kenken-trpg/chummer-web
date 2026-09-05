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
    sheet = tmp_path / "ws.tsv"
    sheet.write_text("".join("\t".join(r) + "\n" for r in rows), encoding="utf-8")
    translations, skipped, problems = _read_worksheet(sheet)

    assert translations == {"Aikido": "合気道", "Bartitsu": "バーティツ"}
    assert skipped == {"AK-98"}
    assert problems == ["L5: 'Krav Maga' marked '=' but its `current` column is empty"]


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
