"""Kick modifiers through real grants, equipment, martial arts and saves."""

import xml.etree.ElementTree as ET

import pytest

from app.characters import apply_patch
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.engine import compute
from app.engine.gear.weapons.bonuses import apply_unarmed_bonuses
from app.models import (
    AdeptPowerInstall,
    CharacterPatch,
    CharacterState,
    CyberwareInstall,
    MartialArtInstall,
    SettingsState,
)
from app.rules import rules_for, using_rules
from app.settings_file import parse_settings_xml
from tests.engine_support import _quality_id
from tests.test_centaur_grants import _centaur


def _fighter(enabled: bool | None) -> CharacterState:
    karate = next(a["id"] for a in catalog()["martial_arts"] if a["name"] == "Karate")
    state = _centaur(
        talent="Adept",
        settings=SettingsState(unarmed_improvements_apply_to_weapons=enabled),
        quality_ids=[_quality_id("Razor Claws"), _quality_id("Death Dealer (Adept)")],
        quality_extras={_quality_id("Death Dealer (Adept)"): "Unarmed Combat"},
        bioware=[CyberwareInstall(ware_id="b04871a1-6b7b-4a78-89fc-af8ec69bdd3d", rating=2)],
        adept_powers=[
            AdeptPowerInstall(power_id="70311f5c-a019-47b9-be21-e9a8d270e32e", rating=2),
            AdeptPowerInstall(power_id="dbf16604-164c-485c-96c8-fe3136cd5caa", extra="Unarmed Combat"),
        ],
        martial_arts=[MartialArtInstall(art_id=karate, techniques=["Kick Attack"])],
    )
    state.priorities.Talent = "B"
    state.attributes["MAG"] = 6
    return compute(state)


def _attacks(state: CharacterState) -> dict[str, tuple[str, str, str]]:
    return {w["name"]: (w["damage"], w["ap"], w["reach"]) for w in state.derived["weapons"]}


@pytest.mark.parametrize("enabled", [None, False, True])
def test_kick_and_claws_distinguish_category_dv_from_optional_unarmed_modifiers(enabled: bool | None) -> None:
    state = _fighter(enabled)
    # Death Dealer's category DV always applies. Bone Density's unarmed
    # DV, Penetrating Strike and Kick Attack need the optional weapon rule.
    assert state.derived["unarmed_dv"] == 1
    assert state.derived["unarmed_ap"] == -2
    assert state.derived["unarmed_reach"] == 1
    assert _attacks(state) == {
        "Kick (Centaur)": ("7P", "-1", "2") if enabled else ("6P", "+1", "1"),
        "Razor Claws": ("6P", "-3", "1") if enabled else ("5P", "-1", "0"),
    }
    assert state.weapons == []
    assert len(state.derived["weapons"]) == 2
    for weapon in state.derived["weapons"]:
        assert weapon["natural"] and weapon["nuyen"] == 0
        assert int(weapon["accuracy"]) == state.derived["limits"]["physical"]
    expected = _attacks(state)
    assert _attacks(compute(state)) == expected
    assert _attacks(compute(CharacterState.model_validate_json(state.model_dump_json()))) == expected


def test_settings_upload_and_patch_toggle_modifiers_without_baking_them_into_grants() -> None:
    state = _fighter(False)
    parsed = parse_settings_xml(
        "<settings><unarmedimprovementsapplytoweapons>True</unarmedimprovementsapplytoweapons></settings>"
    )
    assert parsed.unarmed_improvements_apply_to_weapons is True
    assert "unarmedimprovementsapplytoweapons" not in parsed.unsupported
    state = apply_patch(state, CharacterPatch(settings=parsed.model_dump(exclude_unset=True)))
    assert _attacks(state)["Kick (Centaur)"] == ("7P", "-1", "2")
    state = apply_patch(state, CharacterPatch(attributes={**state.attributes, "STR": 5}))
    assert _attacks(state)["Kick (Centaur)"] == ("9P", "-1", "2")
    assert _attacks(state)["Razor Claws"] == ("8P", "-3", "1")
    state = apply_patch(state, CharacterPatch(settings={"unarmed_improvements_apply_to_weapons": False}))
    assert _attacks(state)["Kick (Centaur)"] == ("8P", "+1", "1")
    state = apply_patch(state, CharacterPatch(metatype="Human"))
    assert set(_attacks(state)) == {"Razor Claws"}
    state = apply_patch(state, CharacterPatch(metatype="Centaur"))
    assert set(_attacks(state)) == {"Kick (Centaur)", "Razor Claws"}
    assert state.quality_ids == [_quality_id("Razor Claws"), _quality_id("Death Dealer (Adept)")]


def test_export_keeps_raw_kick_formula_and_chum5_uses_separate_house_settings() -> None:
    state = _fighter(True)
    for _ in range(2):
        xml = state_to_chum5(state)
        kick = next(w for w in ET.fromstring(xml).findall("./weapons/weapon") if w.findtext("name") == "Kick (Centaur)")
        assert (kick.findtext("damage"), kick.findtext("ap"), kick.findtext("reach")) == ("({STR}+2)P", "+1", "1")
        raw, _ = chum5_to_state(xml)
        loaded = compute(CharacterState.model_validate(raw))
        # A .chum5 references a separate settings file; per-character house
        # overrides are not embedded. Reapply the same settings for comparison.
        loaded = apply_patch(loaded, CharacterPatch(settings=state.settings.model_dump()))
        assert _attacks(loaded) == _attacks(state)
        assert loaded.weapons == []
        state = loaded


@pytest.mark.parametrize("enabled", [False, True])
def test_base_unarmed_attack_always_benefits_and_other_stun_weapons_keep_their_type(enabled: bool) -> None:
    rows = [
        {"name": "Unarmed Attack", "damage": "3S", "reach": "0", "ap": "0"},
        {"name": "Shock Glove", "useskill": "Unarmed Combat", "damage": "8S", "reach": "0", "ap": "-5"},
        {"name": "Sword", "category": "Blades", "damage": "6P", "reach": "1", "ap": "-2"},
    ]
    with using_rules(rules_for(SettingsState(unarmed_improvements_apply_to_weapons=enabled))):
        apply_unarmed_bonuses(rows, 1, -2, 1, True)
    assert (rows[0]["damage"], rows[0]["reach"], rows[0]["ap"]) == ("4P", "1", "-2")
    assert (rows[1]["damage"], rows[1]["reach"], rows[1]["ap"]) == (("9S", "1", "-7") if enabled else ("8S", "0", "-5"))
    assert (rows[2]["damage"], rows[2]["reach"], rows[2]["ap"]) == ("6P", "1", "-2")
