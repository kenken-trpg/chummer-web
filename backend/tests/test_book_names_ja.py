"""Book titles come from the lang file by id, not the flat name table."""

from __future__ import annotations

import pytest

from app.data_loader.loaders.books import load_books
from app.data_loader.loaders.translations import load_translations

BOOKS = {book["code"]: book for book in load_books()}

pytestmark = pytest.mark.skipif(not BOOKS, reason="vendored Chummer data not fetched")


def test_lockdown_keeps_its_english_title():
    # "Lockdown" is also the core-rulebook program, which the flat table
    # translates as ロックダウン — that must not leak onto the book
    assert load_translations().get("Lockdown") == "ロックダウン"
    assert BOOKS["LCD"]["name_ja"] == "Lockdown"


def test_books_with_a_japanese_edition_are_translated():
    assert BOOKS["SR5"]["name_ja"] == "シャドウラン 第5版"
    assert BOOKS["RG"]["name_ja"] == "ラン＆ガン"


def test_every_book_has_a_title():
    assert all(book["name_ja"] for book in BOOKS.values())
