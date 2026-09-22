"""`_match_by` answers from a per-list index once a list is long enough; it
must give exactly what the plain scan gives."""

from __future__ import annotations

from app.engine.lookups import _match_by


def test_indexed_lookup_matches_the_scan() -> None:
    rows = [{"id": str(i % 40), "n": i} for i in range(100)]
    assert _match_by(rows, "id", "3") is rows[3]  # the first of the repeats
    assert _match_by(rows, "id", "nope") is None
    assert _match_by(rows, "missing", None) is rows[0]
    assert _match_by(iter(rows), "id", "5") is rows[5]
    assert _match_by(None, "id", "5") is None


def test_a_new_list_gets_its_own_index() -> None:
    first = [{"id": str(i)} for i in range(50)]
    assert _match_by(first, "id", "7") is first[7]
    second = [{"id": str(i)} for i in range(50)]
    assert _match_by(second, "id", "7") is second[7]
