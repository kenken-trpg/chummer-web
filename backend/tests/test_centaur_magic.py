"""Species-enabled MAG across purchase, mutation, loss and save paths.

These exercise the pinned Chummer starting limits and existing attribute
economy. RF/errata and GUI save fixtures remain separate release gates.
"""

from xml.etree import ElementTree as ET

import pytest

from app.characters import apply_patch, new_character
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.engine import compute, find_metatype, resolve_talent_for_method
from app.engine.qualities import quality_requirement_context
from app.engine.special_attributes import special_attribute_floors
from app.models import CharacterCreate, CharacterPatch, CharacterState, CyberwareInstall, SettingsState
from tests.engine_support import _ware_id
from tests.test_centaur_grants import _centaur


@pytest.mark.parametrize("method", ["Priority", "SumToTen", "Karma"])
def test_mundane_native_magic_is_free_and_survives_recompute(method: str) -> None:
    state = new_character(CharacterCreate(metatype="Centaur", build_method=method))
    assert state.talent == "Mundane"
    assert state.attributes["MAG"] == state.derived["totals"]["MAG"] == 1
    assert state.attributes["RES"] == state.derived["totals"]["RES"] == 0
    assert state.derived["attribute_karma"]["floors"]["MAG"] == 1
    assert state.derived["metatype_info"]["attributes"]["MAG"]["min"] == 1
    assert state.derived["metatype_info"]["attributes"]["MAG"]["max"] == 6
    assert state.derived["points"]["special"]["used"] == 0
    assert state.derived["karma_chargen"]["attributes"] == 0
    assert "MAG" in state.derived["enabled_tabs"]
    assert not set(state.derived["enabled_tabs"]) & {"adept", "spells", "spirits", "foci", "complexforms", "sprites"}
    expected = state.derived
    for _ in range(2):
        state = compute(CharacterState.model_validate_json(state.model_dump_json()))
        assert state.derived == expected


@pytest.mark.parametrize("method", ["Priority", "SumToTen", "Karma"])
def test_native_magic_purchases_charge_only_levels_above_the_free_start(method: str) -> None:
    state = compute(_centaur(build_method=method))
    state = apply_patch(state, CharacterPatch(attributes={**state.attributes, "MAG": 3}))
    assert state.attributes["MAG"] == state.derived["totals"]["MAG"] == 3
    if method == "Karma":
        assert state.derived["karma_chargen"]["attributes"] == 25  # (2+3)*5
    else:
        assert state.derived["points"]["special"]["used"] == 2
        state = apply_patch(state, CharacterPatch(attribute_karma={"MAG": 1}))
        assert state.derived["points"]["special"]["used"] == 1
        assert state.derived["attribute_karma"]["karma"] == 15  # top level 3*5
    for _ in range(2):
        raw, warnings = chum5_to_state(state_to_chum5(state))
        assert not warnings
        loaded = compute(CharacterState.model_validate(raw))
        assert loaded.attributes["MAG"] == 3
        assert loaded.derived["attribute_karma"] == state.derived["attribute_karma"]
        assert loaded.derived["karma_chargen"]["attributes"] == state.derived["karma_chargen"]["attributes"]
        state = loaded


def test_species_and_talent_patches_replace_the_start_without_double_granting() -> None:
    state = compute(_centaur())
    state = apply_patch(state, CharacterPatch(metatype="Human"))
    assert state.attributes["MAG"] == state.derived["totals"]["MAG"] == 0
    state = apply_patch(state, CharacterPatch(metatype="Centaur"))
    assert state.attributes["MAG"] == 1
    priorities = state.priorities.model_copy(update={"Talent": "A"})
    state = apply_patch(state, CharacterPatch(priorities=priorities, talent="Magician"))
    assert state.attributes["MAG"] == state.derived["totals"]["MAG"] == 6
    assert state.derived["attribute_karma"]["floors"]["MAG"] == 6
    assert state.derived["points"]["special"]["used"] == 0
    assert "spells" in state.derived["enabled_tabs"]
    state = apply_patch(state, CharacterPatch(build_method="Karma"))
    assert state.attributes["MAG"] == 1
    assert state.derived["karma_chargen"]["attributes"] == 0
    state = apply_patch(state, CharacterPatch(talent="Mundane"))
    assert state.attributes["MAG"] == 1
    assert "spells" not in state.derived["enabled_tabs"]


@pytest.mark.parametrize(
    "letter,talent,start",
    [
        ("A", "Magician", 6),
        ("B", "Magician", 4),
        ("C", "Magician", 3),
        ("B", "Adept", 6),
        ("C", "Adept", 4),
        ("D", "Adept", 2),
    ],
)
def test_magical_talent_start_replaces_native_magic(letter: str, talent: str, start: int) -> None:
    state = _centaur()
    state.priorities.Talent = letter
    state.talent = talent
    resolved = resolve_talent_for_method(letter, talent, state.build_method)
    assert resolved["name"] == talent and resolved["magic"] == start
    state = compute(state)
    assert state.attributes["MAG"] == start
    assert state.derived["attribute_karma"]["floors"]["MAG"] == start
    assert state.derived["points"]["special"]["used"] == 0
    assert state.derived["karma_chargen"]["attributes"] == 0
    priorities = state.priorities.model_copy(update={"Talent": "E"})
    state = apply_patch(state, CharacterPatch(priorities=priorities, talent="Mundane"))
    assert state.attributes["MAG"] == state.derived["totals"]["MAG"] == 1


@pytest.mark.parametrize("requested,expected", [(0, 1), (99, 6)])
def test_native_magic_purchase_is_clamped_to_its_species_range(requested: int, expected: int) -> None:
    state = compute(_centaur())
    state = apply_patch(state, CharacterPatch(attributes={**state.attributes, "MAG": requested}))
    assert state.attributes["MAG"] == state.derived["totals"]["MAG"] == expected
    assert state.derived["points"]["special"]["used"] == expected - 1


@pytest.mark.parametrize("maximum_only,expected", [(False, 0), (True, 1)])
def test_native_magic_uses_existing_essence_loss_settings(maximum_only: bool, expected: int) -> None:
    state = _centaur(settings=SettingsState(ess_loss_reduces_maximum_only=maximum_only))
    state.cyberware = [CyberwareInstall(ware_id=_ware_id("cyberware", "Datajack"))]
    state = compute(state)
    assert state.derived["essence"] == 5.9
    assert state.attributes["MAG"] == 1  # save the purchase, not its reduced result
    assert state.derived["totals"]["MAG"] == expected
    assert state.derived["points"]["special"]["used"] == 0
    assert len(state.derived["metatype_info"]["powers"]) == 2
    assert len(state.derived["weapons"]) == 1
    assert compute(state).derived["totals"]["MAG"] == expected
    root = ET.fromstring(state_to_chum5(state))
    assert root.findtext("magenabled") == "True"
    mag = root.find("./attributes/attribute[name='MAG']")
    assert mag is not None
    assert (mag.findtext("metatypemin"), mag.findtext("base"), mag.findtext("karma")) == ("1", "0", "0")
    state = apply_patch(state, CharacterPatch(cyberware=[]))
    assert state.derived["totals"]["MAG"] == 1


def test_native_magic_career_baseline_does_not_charge_its_free_start() -> None:
    state = apply_patch(compute(_centaur()), CharacterPatch(career=True))
    assert state.career_baseline is not None
    assert state.career_baseline.attributes["MAG"] == 1
    assert state.derived["career_advancement_karma"] == 0
    state = apply_patch(state, CharacterPatch(attributes={**state.attributes, "MAG": 2}))
    assert state.derived["career_advancement_karma"] == 10
    assert compute(state).derived["career_advancement_karma"] == 10


def test_attribute_range_or_tab_alone_does_not_enable_native_magic() -> None:
    talent = resolve_talent_for_method("E", "Mundane", "Priority")
    centaur = find_metatype("Centaur", None)
    assert special_attribute_floors(centaur, talent) == {"MAG": 1}
    assert (
        special_attribute_floors({**centaur, "bonus": [{"tag": "enabletab", "fields": {"name": "MAG"}}]}, talent) == {}
    )
    for name in ("Human", "Elf", "Dwarf", "Ork", "Troll"):
        assert special_attribute_floors(find_metatype(name, None), talent) == {}
    ctx = quality_requirement_context(_centaur(), talent, [], centaur, 6, 0, {}, set(), set(), "", set(), set())
    assert ctx["magenabled"] and not ctx["resenabled"]
