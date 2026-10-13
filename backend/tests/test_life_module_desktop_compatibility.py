"""Desktop-written evidence and the settings required by Chummer 5.222.0."""

from __future__ import annotations

import io
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from app.characters import import_character
from app.chummer_export import state_to_chum5
from app.chummer_export.check import roundtrip_differences
from app.chummer_export.life_module_settings import life_module_bundle, life_module_settings
from app.chummer_import import chum5_to_state
from app.main import app
from app.notices import NoticeError
from app.settings_file import parse_settings_upload

FIXTURES = Path(__file__).resolve().parents[2] / "docs" / "fixtures"


def _state():
    return import_character(chum5_to_state((FIXTURES / "chummer-life-module-skill-overflow.chum5").read_bytes())[0])


@pytest.mark.parametrize("method", ["Karma", "Priority", "LifeModule", "SumtoTen", ""])
def test_desktop_module_grants_cannot_bypass_the_missing_choices_guard(method: str) -> None:
    root = ET.parse(FIXTURES / "EX_chummer-life-module-skill-overflow.chum5").getroot()
    root.find("buildmethod").text = method
    with pytest.raises(NoticeError) as error:
        chum5_to_state(ET.tostring(root))
    assert error.value.notice["key"] == "engine.life.chum5Unsupported"


def test_real_desktop_resave_is_rejected_by_the_http_import() -> None:
    response = TestClient(app).post(
        "/api/characters/import-chummer",
        content=(FIXTURES / "EX_chummer-life-module-skill-overflow.chum5").read_bytes(),
        headers={"content-type": "application/octet-stream"},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["key"] == "engine.life.chum5Unsupported"


def test_export_settings_use_the_desktop_custom_file_key_and_rf_policy() -> None:
    state = _state()
    key, xml = life_module_settings(state)
    root = ET.fromstring(xml)
    assert root.tag == "settings"
    assert root.findtext("id") == "00000000-0000-0000-0000-000000000000"
    assert root.findtext("buildmethod") == "LifeModule"
    assert root.findtext("buildpoints") == "750"
    assert root.findtext("maxskillratingcreate") == "7"
    assert root.findtext("maxknowledgeskillratingcreate") == "9"
    assert {x.text for x in root.findall("./books/book")} == {"SR5", "RF", "CF"}
    character = ET.fromstring(state_to_chum5(state))
    assert character.findtext("settings") == key
    assert character.findtext("buildmethod") == "LifeModule"
    restored = import_character(chum5_to_state(ET.tostring(character))[0])
    assert restored.derived["skill_totals"]["Perception"] == 7
    assert restored.derived["skill_totals"]["Navigation"] == 2
    assert restored.derived["karma"]["spent"] == 245
    assert restored.life_module_transfers == state.life_module_transfers


def test_settings_overrides_and_unrestricted_books_survive_the_settings_file() -> None:
    state = _state()
    state.settings.books = []
    state.settings.chargen_skill_max = 8
    state.settings.chargen_knowledge_skill_max = 10
    state.settings.karma_chargen_pool = 900
    state.settings.karma_attribute = 6
    state.settings.karma_to_nuyen = 3000
    state.settings.contact_free_mult = 4
    state.settings.ignore_art = True
    state.settings.customdata = ["Local Rules"]
    state.settings.banned_ware_grades = ["Used"]
    key, xml = life_module_settings(state)
    parsed, method = parse_settings_upload(xml)
    assert method == "LifeModule"
    assert parsed.chargen_skill_max == 8
    assert parsed.chargen_knowledge_skill_max == 10
    assert parsed.chargen_karma == 900
    assert parsed.karma_attribute == 6
    assert parsed.karma_to_nuyen == 3000
    assert parsed.contact_free_mult == 4
    assert parsed.ignore_art is True
    assert parsed.books
    assert parsed.customdata == ["Local Rules"]
    assert parsed.banned_ware_grades == ["Used"]
    assert key == life_module_settings(state)[0]
    state.settings.chargen_skill_max = 9
    assert key != life_module_settings(state)[0]


def test_bundle_contains_the_referenced_settings_and_installation_instructions() -> None:
    state = _state()
    with zipfile.ZipFile(io.BytesIO(life_module_bundle(state))) as archive:
        character = ET.fromstring(archive.read("character.chum5"))
        settings = ET.fromstring(archive.read("settings/" + character.findtext("settings")))
        assert settings.findtext("buildmethod") == character.findtext("buildmethod")
        assert "Life Modules" in archive.read("README.txt").decode()


def test_http_bundle_and_export_warning() -> None:
    state = _state()
    response = TestClient(app).post("/api/characters/chummer?bundle=true", json={"state": state.model_dump()})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert ".zip" in response.headers["content-disposition"]
    assert zipfile.is_zipfile(io.BytesIO(response.content))
    assert [n["key"] for n in roundtrip_differences(state)] == ["engine.export.chum5LifeModuleSetup"]
