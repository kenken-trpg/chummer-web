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
        # the Codex's stamps only: a Role&Roll issue reprints some rows too
        if any(a.get("source") == codex.CODE for a in node.get("also_in") or []):
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
    # the Codex is stamped first, so it leads any Role&Roll issue
    assert all(row["also_in"][0]["source"] == codex.CODE for row in found.values())


def test_codex_names_fill_only_missing_translations():
    tr = public_catalog()["translations"]
    assert tr["Wanted"] == "賞金首"
    assert tr["Bulk Modification (Full Arm/Full Leg)"] == "大容量化改造（腕/脚）"
    # an existing translation is kept
    assert codex.fill_translations({"Quiet": "静寂"}, {"Quiet": "クワイエット"}) == {"Quiet": "静寂"}


def test_dongles_cite_page_202():
    # the dongles follow the weapon mods (p.201) and share p.202 with the
    # partial cyberskull; they were once stamped p.200
    found = _stamped(public_catalog(), {})
    dongle = found["d66c8cfa-2d00-4f5f-ac7a-eed5f5f7dde7"]
    assert dongle["also_in"][0] == {"source": codex.CODE, "page": "202"}
