"""The backend is stateless: `store.py` functions are pure and the HTTP layer
forwards a client-owned `CharacterState` on every call. (Replaces the old
roster tests.)"""

from __future__ import annotations

from starlette.testclient import TestClient

from app.main import app
from app.models import CharacterCreate, CharacterPatch, CharacterState, Priorities, SpellInstall
from app.store import apply_patch, compute_state, import_character, new_character

client = TestClient(app)


def _human() -> CharacterState:
    return new_character(CharacterCreate(name="Runner"))


def _mage() -> CharacterState:
    st = new_character(
        CharacterCreate(
            name="Mage",
            priorities=Priorities(Heritage="C", Attributes="B", Talent="A", Skills="D", Resources="E"),
        )
    )
    return st.model_copy(update={"talent": "Magician", "spells": [SpellInstall(spell_id="x")]})


# --- pure functions ---------------------------------------------------------


def test_new_character_is_computed() -> None:
    st = new_character(CharacterCreate(name="Fresh"))
    assert st.id and st.name == "Fresh"
    assert st.derived and "totals" in st.derived


def test_apply_patch_merges_and_recomputes() -> None:
    st = _human()
    out = apply_patch(st, CharacterPatch(name="Renamed", notes="hi"))
    assert out.id == st.id
    assert out.name == "Renamed" and out.notes == "hi"
    assert out.derived and "totals" in out.derived


def test_apply_patch_talent_cascade_clears_awakened_lists() -> None:
    mage = _mage()
    assert mage.spells  # precondition
    out = apply_patch(mage, CharacterPatch(priorities=Priorities(Talent="E")))
    assert out.talent == "Mundane"
    assert out.spells == []
    assert out.attributes.get("MAG", 0) == 0


def test_apply_patch_career_toggle_snapshots_baseline() -> None:
    out = apply_patch(_human(), CharacterPatch(career=True))
    assert out.career is True
    assert out.career_baseline is not None


def test_import_character_regenerates_id() -> None:
    raw = _human().model_dump()
    raw["id"] = "attacker-controlled"
    out = import_character(raw)
    assert out.id != "attacker-controlled"
    assert out.derived


def test_compute_state_is_a_bare_recompute() -> None:
    st = _human().model_copy(update={"derived": {}})
    assert compute_state(st).derived


# --- HTTP surface ---------------------------------------------------------


def test_post_new_returns_computed_state() -> None:
    r = client.post("/api/characters/new", json={"name": "Web"})
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Web" and body["derived"]


def test_post_patch_with_and_without_patch() -> None:
    st = client.post("/api/characters/new", json={"name": "P"}).json()

    merged = client.post("/api/characters/patch", json={"state": st, "patch": {"name": "P2"}})
    assert merged.status_code == 200 and merged.json()["name"] == "P2"

    recomputed = client.post("/api/characters/patch", json={"state": st})
    assert recomputed.status_code == 200 and recomputed.json()["derived"]


def test_post_chummer_returns_xml_download() -> None:
    st = client.post("/api/characters/new", json={"name": "Export"}).json()
    r = client.post("/api/characters/chummer", json={"state": st})
    assert r.status_code == 200
    assert "xml" in r.headers["content-type"]
    cd = r.headers["content-disposition"]
    assert 'filename="Export.chum5"' in cd and "filename*=UTF-8''Export.chum5" in cd
    assert r.content.lstrip()[:16].lower().startswith((b"<?xml", b"<character"))


def test_post_import_regenerates_id() -> None:
    st = client.post("/api/characters/new", json={"name": "Imp"}).json()
    st["id"] = "nope"
    r = client.post("/api/characters/import", json=st)
    assert r.status_code == 200 and r.json()["id"] != "nope"
