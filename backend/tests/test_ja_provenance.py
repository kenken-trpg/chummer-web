"""scripts/ja_provenance.py — where the translation report says a name comes from."""

from __future__ import annotations

from scripts.ja_provenance import carriers, ja_books, layer_of, per_book

BOOKS = [
    {"code": "SR5", "name": "Shadowrun 5th Edition", "name_ja": "シャドウラン 第5版"},
    {"code": "DT", "name": "Data Trails", "name_ja": "Data Trails"},
    {"code": "KC", "name": "Kill Code", "name_ja": "Kill Code"},
    {"code": "SRCX", "name": "Shadowrun Codex", "name_ja": "シャドウラン・コデックス"},
]
PRINTED = ja_books(BOOKS)

PUBLIC = {
    "books": BOOKS,  # not rows: never walked
    "translations": {"Redundancy": "冗長化"},
    "complex_forms": [{"name": "Redundancy", "source": "DT"}],
    "qualities": [
        {"name": "Redundancy", "source": "DT", "category": "Positive"},
        {"name": "Data Anomaly", "source": "DT", "also_in": [{"source": "SRCX", "page": "199"}]},
        {"name": "Ambidextrous", "source": "SR5"},
    ],
    "gear": [{"name": "Kit", "source": "KC", "options": [{"name": "Nested Part"}]}],
}


def test_a_book_has_a_japanese_edition_when_its_title_is_japanese() -> None:
    assert PRINTED == {"SR5", "SRCX"}


def test_every_kind_and_book_carrying_a_name_is_listed() -> None:
    found = carriers(PUBLIC, PRINTED)
    assert found["Redundancy"].render() == "complex_forms: DT / qualities: DT"
    assert found["Positive"].render() == "category: DT"
    assert "Data Trails" not in found  # book titles are not rows


def test_a_nested_row_inherits_its_parents_book() -> None:
    assert carriers(PUBLIC, PRINTED)["Nested Part"].books() == {"KC"}


def test_printed_in_japanese_by_its_own_book_or_a_codex_reprint() -> None:
    found = carriers(PUBLIC, PRINTED)
    assert found["Ambidextrous"].printed_ja
    assert found["Data Anomaly"].printed_ja  # DT, but the Codex reprints it
    assert not found["Redundancy"].printed_ja


def test_the_layer_is_the_first_that_changes_the_name() -> None:
    overlay = {"Redundancy": "冗長化", "Kit": "Kit"}
    upstream = {"Ambidextrous": "両手利き", "Redundancy": "Redundancy"}
    shown = {"Data Anomaly": "特異なデータ", "Ambidextrous": "両手利き", "Redundancy": "冗長化"}
    assert layer_of("Redundancy", overlay, upstream, shown) == "overlay"
    assert layer_of("Ambidextrous", overlay, upstream, shown) == "upstream"
    assert layer_of("Data Anomaly", overlay, upstream, shown) == "codex"
    assert layer_of("Kit", overlay, upstream, shown) == "english"  # an overlay entry equal to the English


def test_per_book_counts_a_name_once_in_each_of_its_books() -> None:
    found = carriers(PUBLIC, PRINTED)
    counts = per_book(found, {"Redundancy": "冗長化"}, {}, {"Data Anomaly": "特異なデータ"})
    assert counts["DT"] == {"upstream": 0, "overlay": 1, "codex": 1, "english": 1}  # + Positive
    assert counts["KC"]["english"] == 2
