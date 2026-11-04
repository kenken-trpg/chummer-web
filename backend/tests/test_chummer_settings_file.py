"""The Chummer settings file written alongside a .chum5
(app/chummer_export/life_module_settings.py `chummer_settings_file`).

Chummer keeps the books, the availability limit and a preset's rules in its
settings file, not in the character, so a save it writes back carries only the
settings' own. A real Chummer 5.226 (2026-11-04) turned a Sum-to-Ten Prime
Runner into Sum-to-Ten and every character's books into the preset's."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from urllib.parse import unquote

from starlette.testclient import TestClient

from app.characters import apply_patch, import_character, new_character
from app.chummer_export import state_to_chum5
from app.chummer_export.check import _as_chummer_saves_it
from app.chummer_export.life_module_settings import chummer_settings_file
from app.chummer_import import chum5_to_state
from app.main import app
from app.models import CharacterCreate, CharacterPatch, CharacterState, SettingsState


def _prime_by_sum_to_ten() -> CharacterState:
    state = new_character(CharacterCreate())
    settings = SettingsState(
        name="Prime Runner",
        books=["SR5", "RG", "CF"],
        quality_karma_limit=35,
        priority_table="Prime Runner",
        priority_karma_nuyen_base=25,
        chargen_avail_max=15,
    )
    state = apply_patch(state, CharacterPatch(build_method="SumToTen", settings=settings, karma_nuyen=25))
    return import_character(state.model_dump())


def test_the_file_is_the_preset_built_by_the_characters_method() -> None:
    key, xml = chummer_settings_file(_prime_by_sum_to_ten())
    root = ET.fromstring(xml)
    assert root.tag == "settings"
    # a zero id is a settings file of the player's own, keyed by file name
    assert root.findtext("id") == "00000000-0000-0000-0000-000000000000"
    assert key.startswith("chummer-web-Prime Runner-") and key.endswith(".xml")
    fields = ("buildmethod", "qualitykarmalimit", "nuyenmaxbp", "prioritytable", "availability")
    assert [root.findtext(f) for f in fields] == ["SumtoTen", "35", "25", "Prime Runner", "15"]
    assert [b.text for b in root.findall("./books/book")] == ["CF", "RG", "SR5"]


def test_the_same_settings_share_one_file() -> None:
    assert chummer_settings_file(_prime_by_sum_to_ten())[0] == chummer_settings_file(_prime_by_sum_to_ten())[0]


def test_a_save_chummer_wrote_under_the_file_comes_back_whole() -> None:
    """What Chummer writes back under the file — its books, no
    `<gameplayoption>` or `<maxavail>`, `nuyenbp` within its cap — reads back
    as the settings the character left with, nuyen and all."""
    state = _prime_by_sum_to_ten()
    key, xml = chummer_settings_file(state)
    root = ET.fromstring(xml)
    as_chummer = {
        "books": [b.text for b in root.findall("./books/book")],
        "nuyen_max_bp": int(root.findtext("nuyenmaxbp") or 10),
    }
    saved = _as_chummer_saves_it(state_to_chum5(state, settings_key=key), as_chummer)
    assert ET.fromstring(saved).findtext("settings") == key
    back = import_character(chum5_to_state(saved)[0])
    s = back.settings
    assert (s.name, s.quality_karma_limit, s.priority_table, s.priority_karma_nuyen_base) == (
        "Prime Runner",
        35,
        "Prime Runner",
        25,
    )
    assert s.chargen_avail_max == 15
    assert sorted(s.books) == ["CF", "RG", "SR5"]
    assert back.karma_nuyen == 25
    assert back.derived["nuyen"] == state.derived["nuyen"]


def test_the_routes_hand_out_the_file_and_point_the_save_at_it() -> None:
    client = TestClient(app)
    body = {"state": _prime_by_sum_to_ten().model_dump()}
    settings = client.post("/api/characters/chummer/settings", json=body)
    assert settings.status_code == 200
    key = unquote(settings.headers["content-disposition"].split("filename*=UTF-8''")[1])
    assert key.startswith("chummer-web-Prime Runner-")
    save = client.post("/api/characters/chummer?settings_file=true", json=body)
    assert ET.fromstring(save.content).findtext("settings") == key
    plain = client.post("/api/characters/chummer", json=body)
    assert ET.fromstring(plain.content).findtext("settings") != key


def test_a_japanese_settings_name_downloads() -> None:
    """日本語環境, the default, is a file name Starlette cannot put in a bare
    `filename=`; it goes out as `filename*` and reads back as itself."""
    state = import_character(new_character(CharacterCreate()).model_dump())
    res = TestClient(app).post("/api/characters/chummer/settings", json={"state": state.model_dump()})
    assert res.status_code == 200
    key = unquote(res.headers["content-disposition"].split("filename*=UTF-8''")[1])
    assert key == chummer_settings_file(state)[0]
    assert key.startswith("chummer-web-日本語環境-")
    saved = state_to_chum5(state, settings_key=key)
    assert (
        chum5_to_state(saved.replace(b"<gameplayoption>", b"<x>").replace(b"</gameplayoption>", b"</x>"))[0][
            "settings"
        ]["name"]
        == "日本語環境"
    )
