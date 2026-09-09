"""The settings file, as far as it is ported: the books/preset loaders, the
`SettingsState` container and its `.chum5` round-trip.

Chummer's `<settings>` holds ~150 house-rule knobs; what lands here is the
book list and the build method. See docs/plans/settings-plan.md.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from app.characters import apply_patch, new_character
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.data_loader.loaders.books import load_books, load_settings_presets
from app.models import CharacterPatch, CharacterState


def test_books_carry_every_code_the_catalog_cites() -> None:
    """A `<source>` the settings screen cannot list is a book the user can
    never enable — the item would be unbuyable under any preset."""
    codes = {b["code"] for b in load_books()}
    assert {"SR5", "RG"} <= codes
    cited = {
        str(row.get("source"))
        for bucket in ("qualities", "spells", "weapons", "armor", "gear")
        for row in catalog()[bucket]  # type: ignore[literal-required]
        if row.get("source")
    }
    assert cited <= codes, f"cited but not in books.xml: {sorted(cited - codes)}"


def test_presets_only_offer_build_methods_the_engine_has() -> None:
    presets = load_settings_presets()
    assert presets, "settings.xml should ship presets"
    assert {p["build_method"] for p in presets} <= {"Priority", "SumToTen", "Karma"}
    standard = next(p for p in presets if p["name"] == "Standard")
    assert standard["books"] == ["SR5"]


def test_a_new_character_is_unrestricted() -> None:
    """Empty books means the whole catalog, not an empty one — a character
    built before settings existed must not lose its gear."""
    state = new_character(None)
    assert state.settings.name == ""
    assert state.settings.books == []


def test_patching_settings_merges_rather_than_replaces() -> None:
    """The name and the book list are edited from two different controls."""
    state = new_character(None)
    state = apply_patch(state, CharacterPatch(settings={"name": "Standard", "books": ["SR5"]}))
    assert state.settings.name == "Standard"

    state = apply_patch(state, CharacterPatch(settings={"books": ["SR5", "RG"]}))
    assert state.settings.books == ["SR5", "RG"]
    assert state.settings.name == "Standard"


def _export(state: CharacterState) -> ET.Element:
    return ET.fromstring(state_to_chum5(state))


def test_an_untouched_character_writes_no_settings_tag() -> None:
    assert _export(new_character(None)).find("settings") is None


def test_a_shipped_preset_round_trips_its_books() -> None:
    """Only the name survives a `.chum5` — Chummer keeps the books in the
    settings file, not in the character — so import recovers them by name."""
    state = apply_patch(
        new_character(None),
        CharacterPatch(settings={"name": "Sum-to-Ten", "books": ["SR5", "RF"]}),
    )
    assert _export(state).findtext("settings") == "Sum-to-Ten"

    back = chum5_to_state(state_to_chum5(state))[0]
    assert back["settings"] == {"name": "Sum-to-Ten", "books": ["SR5", "RF"]}


def test_an_unknown_settings_file_comes_back_unrestricted() -> None:
    """A GM's own settings file names books this app has never seen; guessing
    a restriction would hide gear the character legitimately owns."""
    xml = "<character><alias>X</alias><settings>日本_2021_SumTo10.xml</settings></character>"
    state = chum5_to_state(xml)[0]
    assert state["settings"] == {"name": "日本_2021_SumTo10", "books": []}


def test_a_settings_element_holding_house_rules_is_not_read_as_a_name() -> None:
    """Some builds write `<settings>` as a container, not a file name."""
    xml = "<character><alias>X</alias><settings><karmaattribute>5</karmaattribute></settings></character>"
    assert chum5_to_state(xml)[0]["settings"] == {}
