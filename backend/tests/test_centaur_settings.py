"""Disabling RF restricts new choices; it must not erase an imported Centaur."""

import pytest

from app.catalog_view import public_catalog
from app.characters import apply_patch, import_character
from app.engine import compute
from app.models import CharacterPatch, SettingsState
from tests.notice_asserts import find, unwrap
from tests.test_centaur_grants import _centaur


@pytest.mark.parametrize("method", ["Priority", "SumToTen", "Karma"])
def test_book_toggle_and_json_reload_keep_centaur_and_its_grants(method: str) -> None:
    state = compute(_centaur(build_method=method, settings=SettingsState(books=["SR5", "RF"])))
    state = apply_patch(state, CharacterPatch(attributes={**state.attributes, "MAG": 3}))
    expected = {key: state.derived[key] for key in ("totals", "qualities", "weapons", "movement", "metatype_info")}
    assert not find(state.derived["warnings"], "engine.settings.outOfBooks")
    for books in (["SR5"], ["SR5", "RF"], []):
        state = apply_patch(state, CharacterPatch(settings=SettingsState(books=books)))
        for _ in range(2):
            assert state.metatype == "Centaur"
            assert {key: state.derived[key] for key in expected} == expected
            assert state.quality_ids == [] and state.weapons == []
            warnings = find(state.derived["warnings"], "engine.settings.outOfBooks")
            if books == ["SR5"]:
                assert len(warnings) == 1
                assert "Centaur" in unwrap(warnings[0]["params"]["names"])
                assert warnings[0]["params"]["books"] == "RF"
            else:
                assert warnings == []
            state = import_character(state.model_dump())


def test_centaur_stays_hidden_in_both_catalog_and_priority_choices() -> None:
    cat = public_catalog()
    assert "Centaur" not in {row["name"] for row in cat["metatypes"]}
    for cell in cat["priority_table"]["Heritage"].values():
        assert "Centaur" not in {row["name"] for row in cell["metatypes"]}
