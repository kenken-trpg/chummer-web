"""Desktop-written evidence and the settings required by Chummer 5.222.0."""

from __future__ import annotations

import io
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from app.characters import apply_patch, import_character
from app.chummer_export import state_to_chum5
from app.chummer_export.check import roundtrip_differences
from app.chummer_export.life_module_settings import life_module_bundle, life_module_settings
from app.chummer_import import chum5_to_state
from app.main import app
from app.models import CharacterPatch
from app.notices import NoticeError
from app.settings_file import parse_settings_upload

FIXTURES = Path(__file__).resolve().parents[2] / "docs" / "fixtures"


def _state():
    return import_character(chum5_to_state((FIXTURES / "chummer-life-module-skill-overflow.chum5").read_bytes())[0])


def test_real_desktop_resave_becomes_a_career_snapshot_without_losing_ratings() -> None:
    raw, warnings = chum5_to_state((FIXTURES / "EX_chummer-life-module-skill-overflow.chum5").read_bytes())
    char = import_character(raw)
    assert char.build_method == "Karma"
    assert char.career
    assert char.life_modules == []
    assert len(char.life_module_archive) == 5
    assert char.derived["skill_totals"]["Perception"] == 7
    assert char.derived["skill_totals"]["Navigation"] == 2
    assert char.career_baseline is not None
    assert char.career_baseline.skills["Perception"] == 7
    assert [warning["key"] for warning in warnings] == ["engine.life.chum5Snapshot"]

    # The archived module names are informational on export. They must not
    # grant skills a second time when the app reads its own Chummer file.
    exported = state_to_chum5(char)
    restored_raw, restored_warnings = chum5_to_state(exported)
    restored = import_character(restored_raw)
    assert restored.derived["skill_totals"]["Perception"] == 7
    assert restored.derived["skill_totals"]["Navigation"] == 2
    assert restored.life_module_archive == char.life_module_archive
    assert [warning["key"] for warning in restored_warnings] == ["engine.life.chum5Snapshot"]


def test_career_growth_after_desktop_snapshot_is_charged_from_saved_rating() -> None:
    raw, _ = chum5_to_state((FIXTURES / "EX_chummer-life-module-skill-overflow.chum5").read_bytes())
    char = import_character(raw)
    grown = apply_patch(char, CharacterPatch(skills={**char.skills, "Perception": 8}))
    assert grown.derived["skill_totals"]["Perception"] == 8
    assert grown.derived["karma"]["spent"] == char.derived["karma"]["spent"] + 16
    assert grown.derived["karma"]["remaining"] == char.derived["karma"]["remaining"] - 16


def test_life_module_build_method_without_modules_or_choices_still_stops() -> None:
    root = ET.parse(FIXTURES / "EX_chummer-life-module-skill-overflow.chum5").getroot()
    root.find("buildmethod").text = "LifeModule"
    for quality in list(root.findall("./qualities/quality")):
        if (quality.findtext("qualitytype") or "").lower() == "lifemodule":
            root.find("./qualities").remove(quality)
    with pytest.raises(NoticeError) as error:
        chum5_to_state(ET.tostring(root))
    assert error.value.notice["key"] == "engine.life.chum5Unsupported"


def test_real_desktop_resave_imports_with_a_snapshot_notice() -> None:
    response = TestClient(app).post(
        "/api/characters/import-chummer",
        content=(FIXTURES / "EX_chummer-life-module-skill-overflow.chum5").read_bytes(),
        headers={"content-type": "application/octet-stream"},
    )
    assert response.status_code == 200
    assert response.json()["warnings"][0]["key"] == "engine.life.chum5Snapshot"
    character = import_character(response.json()["character"])
    assert character.derived["skill_totals"]["Perception"] == 7
    assert character.derived["skill_totals"]["Navigation"] == 2


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
