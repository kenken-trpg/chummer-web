"""`_match_by` answers from a per-list index once a list is long enough; it
must give exactly what the plain scan gives."""

from __future__ import annotations

import pytest

from app.engine.lookups import _match_by, find_metatype
from app.notices import NoticeError


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


def test_metavariant_resolution_is_scoped_to_its_parent() -> None:
    assert find_metatype("Human", "Nartaki")["parent"] == "Human"
    assert find_metatype("Elf", "Nartaki")["name"] == "Elf"
    with pytest.raises(NoticeError):
        find_metatype("Missing species", "Nartaki")


def test_variant_of_nonpublic_metatype_can_be_resolved(monkeypatch: pytest.MonkeyPatch) -> None:
    variant = {"name": "Private variant", "parent": "Private species"}
    base = {"name": "Private species", "metavariants": [variant]}
    monkeypatch.setattr("app.engine.lookups.catalog", lambda: {"metatypes": [], "all_metatypes": {base["name"]: base}})
    assert find_metatype("Private species", "Private variant") is variant
