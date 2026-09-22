"""A new character starts under 日本語環境 (app/ja_default.py)."""

from __future__ import annotations

from app import ja_default
from app.catalog_view import public_catalog
from app.characters import new_character
from app.data_loader import catalog


def test_new_character_starts_with_the_japanese_books():
    settings = new_character().settings
    assert settings.name == "日本語環境"
    assert settings.books == ["SR5", "RG", "SRCX"]


def test_the_preset_is_offered_first_but_is_not_one_of_chummers():
    assert public_catalog()["settings_presets"][0] == ja_default.PRESET
    # import/export look Chummer's preset ids up here; ours has none
    assert all(p["name"] != ja_default.NAME for p in catalog()["settings_presets"])


def test_it_exports_as_standard_and_imports_back():
    from app.chummer_export import state_to_chum5
    from app.chummer_import import chum5_to_state

    xml = state_to_chum5(new_character())
    xml = xml.decode() if isinstance(xml, bytes) else xml
    assert "<gameplayoption>日本語環境</gameplayoption>" in xml
    standard = next(p for p in catalog()["settings_presets"] if p["name"] == "Standard")
    assert f"<settings>{standard['id']}</settings>" in xml
    assert chum5_to_state(xml)[0]["settings"]["books"] == ["SR5", "RG", "SRCX"]
