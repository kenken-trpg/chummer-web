"""Character roster: list / open / delete (backend/app/store.py)."""

from __future__ import annotations

from app.models import CharacterCreate
from app.store import (
    SAVE_DIR,
    create_character,
    delete_character,
    get_character,
    list_characters,
)


def _mk(name: str) -> str:
    return create_character(CharacterCreate(name=name)).id


def test_created_character_appears_in_roster() -> None:
    cid = _mk("RosterTestA")
    try:
        rows = list_characters()
        row = next((r for r in rows if r["id"] == cid), None)
        assert row is not None
        assert row["name"] == "RosterTestA"
        assert set(row) >= {"id", "name", "metatype", "career", "updated"}
    finally:
        delete_character(cid)


def test_roster_is_newest_first() -> None:
    a = _mk("RosterOrderOld")
    b = _mk("RosterOrderNew")
    try:
        rows = [r for r in list_characters() if r["id"] in (a, b)]
        assert [r["id"] for r in rows] == [b, a]
    finally:
        delete_character(a)
        delete_character(b)


def test_delete_removes_file_and_roster_entry() -> None:
    cid = _mk("RosterTestDelete")
    assert (SAVE_DIR / f"{cid}.json").exists()
    delete_character(cid)
    assert not (SAVE_DIR / f"{cid}.json").exists()
    assert all(r["id"] != cid for r in list_characters())


def test_get_character_reloads_from_disk_after_memory_evicted() -> None:
    cid = _mk("RosterTestReload")
    try:
        import app.store as store

        store._MEMORY.pop(cid, None)
        again = get_character(cid)
        assert again.id == cid and again.name == "RosterTestReload"
    finally:
        delete_character(cid)


def test_list_characters_respects_limit() -> None:
    ids = [_mk(f"RosterLimit{i}") for i in range(4)]
    try:
        assert len(list_characters(limit=2)) == 2
    finally:
        for cid in ids:
            delete_character(cid)
