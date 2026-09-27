"""Matching a name typed on the 装備 sheet against the catalog.

The same guessing is already exercised through the sheet in
`test_xlsx_import.py`, which is where the interesting cases are. This tries it
without a workbook around it: what a score means, what order a shortlist comes
back in, and which spellings `resolve` is willing to try.
"""

from __future__ import annotations

import pytest

from app.data_loader import catalog
from app.xlsx_import._match import (
    SUGGEST_LIMIT,
    SUGGEST_THRESHOLD,
    _likeness,
    _loose,
    build_index,
    resolve,
    suggest,
)


@pytest.fixture(scope="module")
def index() -> dict[str, list[tuple[str, str]]]:
    return build_index(catalog())


@pytest.fixture(scope="module")
def lifestyles() -> list[str]:
    cat = catalog()
    translations = dict(cat.get("translations") or {})
    return [translations.get(str(row["name"]), str(row["name"])) for row in cat["lifestyles"]]


# --- how alike two names are ----------------------------------------------


def test_the_same_name_is_a_perfect_score() -> None:
    assert _likeness("医療キット", "医療キット") == 1.0


def test_nothing_in_common_scores_zero() -> None:
    assert _likeness("医療キット", "アレス") == 0.0


def test_one_syllable_out_still_scores_well() -> None:
    """Which is the miss this is for: the sheets are typed from memory."""
    assert _likeness("サンダートラック", "サンダーストラック") > SUGGEST_THRESHOLD


def test_the_score_does_not_depend_on_the_order() -> None:
    assert _likeness("錠前キット", "錠前セット") == _likeness("錠前セット", "錠前キット")


def test_spacing_and_interpuncts_come_off_both_sides() -> None:
    assert _loose("アレス・プレデター V") == _loose("アレスプレデターV")


# --- the shortlist ---------------------------------------------------------


def test_the_closest_name_is_offered_first(index: dict[str, list[tuple[str, str]]]) -> None:
    """A name a character short of a real one puts that real one at the top,
    not merely somewhere in the list."""
    offered = suggest("医療キッ", index)
    assert offered[0] == index[_loose("医療キット")][0]


def test_a_name_like_nothing_in_the_book_is_offered_nothing(index: dict[str, list[tuple[str, str]]]) -> None:
    assert suggest("ぎゃqwertyほげほげ", index) == []


def test_an_empty_name_is_offered_nothing(index: dict[str, list[tuple[str, str]]]) -> None:
    assert suggest("", index) == []
    assert suggest("　 ", index) == []


def test_the_shortlist_is_capped_and_holds_no_duplicates(index: dict[str, list[tuple[str, str]]]) -> None:
    offered = suggest("キット", index)
    assert len(offered) <= SUGGEST_LIMIT
    assert len(set(offered)) == len(offered)


# --- the index and the answer ---------------------------------------------


def test_a_catalog_name_with_its_line_in_front_is_indexed_both_ways(
    index: dict[str, list[tuple[str, str]]],
) -> None:
    """弾薬: 通常弾 is how the book files it; 通常弾 is what a player writes."""
    assert index.get(_loose("弾薬: 通常弾"))
    assert index.get(_loose("通常弾"))


def test_a_name_in_two_catalogs_keeps_both(index: dict[str, list[tuple[str, str]]]) -> None:
    """予備クリップ is gear and a weapon accessory. Which one wins is `BUCKETS`
    order, which is `resolve`'s business — the index keeps both."""
    found = index[_loose("予備クリップ")]
    assert len(found) > 1
    assert found[0][0] == "gear", "gear comes first: on a row of its own it is what was bought"


def test_an_unknown_name_resolves_to_nothing(index: dict[str, list[tuple[str, str]]], lifestyles: list[str]) -> None:
    assert resolve(["そんな装備はない"], index, lifestyles) is None


def test_the_first_spelling_that_is_in_the_book_wins(
    index: dict[str, list[tuple[str, str]]], lifestyles: list[str]
) -> None:
    """`split_row` hands over the spellings in the order they are worth trying,
    and `resolve` takes the first that answers rather than the best."""
    found = resolve(["アレス・プレデター V", "メディキット"], index, lifestyles)
    assert found is not None
    bucket, item_id = found
    assert bucket == "weapons"
    assert index[_loose("アレス・プレデター V")][0][1] == item_id


def test_a_word_the_sheets_spell_differently_is_tried(
    index: dict[str, list[tuple[str, str]]], lifestyles: list[str]
) -> None:
    """偽装SIN for 偽造SIN — the same word, both spellings in use."""
    assert resolve(["偽装SIN"], index, lifestyles) == resolve(["偽造SIN"], index, lifestyles)
    assert resolve(["偽装SIN"], index, lifestyles) is not None


def test_a_lifestyle_is_found_inside_the_players_phrasing(
    index: dict[str, list[tuple[str, str]]], lifestyles: list[str]
) -> None:
    assert resolve(["ライフスタイル（下流）一か月分"], index, lifestyles) == resolve(["下流"], index, lifestyles)


def test_a_name_that_merely_contains_a_lifestyle_is_not_one(
    index: dict[str, list[tuple[str, str]]], lifestyles: list[str]
) -> None:
    """Only a name that says it is about a lifestyle is read that way, so this
    asks for the lifestyle word to be what makes the difference."""
    assert resolve(["下流ほげほげ"], index, lifestyles) is None
    assert resolve(["生活費下流ほげほげ"], index, lifestyles) is not None
