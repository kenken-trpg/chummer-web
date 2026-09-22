"""The Shadowrun Codex: a Japanese book Chummer lacks, reprinting English-
supplement items (backend/app/data_loader/codex.py)."""

from __future__ import annotations

from app.catalog_view import public_catalog
from app.data_loader import codex


def _stamped(node, found):
    if isinstance(node, list):
        for child in node:
            _stamped(child, found)
    elif isinstance(node, dict):
        if node.get("also_in"):
            found[node.get("id")] = node
        for child in node.values():
            _stamped(child, found)
    return found


def test_codex_is_a_book_to_tick():
    assert codex.BOOK in public_catalog()["books"]


def test_every_listed_item_is_found_in_the_catalog():
    # an id typo, or a Chummer data update renaming an entry, would silently
    # drop the item from the Codex — so each one must turn up
    found = _stamped(public_catalog(), {})
    assert set(codex.ITEMS) <= set(found)
    assert {row["name"] for row in found.values()} >= set(codex.NAMED)
    assert all(row["also_in"][0]["source"] == codex.CODE for row in found.values())


def test_codex_names_fill_only_missing_translations():
    tr = public_catalog()["translations"]
    assert tr["Wanted"] == "賞金首"
    assert tr["Bulk Modification (Full Arm/Full Leg)"] == "大容量化改造（腕/脚）"
    # an existing translation is kept
    assert codex.fill_translations({"Quiet": "静寂"}, {"Quiet": "クワイエット"}) == {"Quiet": "静寂"}
