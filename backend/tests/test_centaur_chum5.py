"""Innate grants in Chummer-shaped XML and the web import/export loop.

These are generated fixtures checked against the fixed C# Save/Create fields,
not saves produced by running the Chummer GUI.
"""

import xml.etree.ElementTree as ET

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.engine import compute
from app.models import CharacterState, WeaponInstall
from tests.test_centaur_data import KICK_SELECT, NATURAL_WEAPON_ID, QUALITY_IDS, SEARCH_ID
from tests.test_centaur_grants import _centaur


def test_chum5_writes_metatype_owned_qualities_powers_and_one_linked_kick() -> None:
    state = compute(_centaur())
    xml = state_to_chum5(state)
    assert state_to_chum5(state) == xml
    root = ET.fromstring(xml)
    qualities = root.findall("./qualities/quality")
    assert {q.findtext("sourceid") for q in qualities} == set(QUALITY_IDS.values())
    assert len(qualities) == 4
    for quality in qualities:
        assert quality.findtext("qualitysource") == "Metatype"
        assert quality.findtext("contributetobp") == "False"
        assert quality.findtext("contributetolimit") == "False"
    kick_quality = next(q for q in qualities if q.findtext("sourceid") == QUALITY_IDS["Natural Weapon: Kick (Centaur)"])
    (kick,) = root.findall("./weapons/weapon")
    assert kick.findtext("guid") == kick_quality.findtext("weaponguid")
    assert kick.findtext("parentid") == kick_quality.findtext("guid")
    assert kick.findtext("damage") == "({STR}+2)P"
    assert kick.findtext("accuracy") == "Physical"
    assert kick.findtext("ap") == "+1" and kick.findtext("reach") == "1"
    assert kick.findtext("cost") == "0" and kick.findtext("allowaccessory") == "False"
    powers = root.findall("./critterpowers/critterpower")
    assert [p.findtext("sourceid") for p in powers] == [SEARCH_ID, NATURAL_WEAPON_ID]
    assert powers[1].findtext("extra") == KICK_SELECT
    assert all(p.findtext("counttowardslimit") == "False" and p.findtext("grade") == "0" for p in powers)
    assert powers[1].find("./bonus/selecttext") is not None
    links = root.findall("./improvements/improvement[improvementttype='CritterPower']")
    assert {link.findtext("improvedname") for link in links} == {p.findtext("guid") for p in powers}
    assert all(link.findtext("improvementsource") == "Metatype" for link in links)


def test_chum5_reimports_grants_by_species_without_creating_purchases() -> None:
    state = compute(_centaur())
    expected_qualities = state.derived["qualities"]
    expected_powers = state.derived["metatype_info"]["powers"]
    expected_weapon = state.derived["weapons"][0]
    for _ in range(3):
        raw, warnings = chum5_to_state(state_to_chum5(state))
        assert not warnings
        state = compute(CharacterState.model_validate(raw))
        assert state.quality_ids == [] and state.weapons == []
        assert state.derived["qualities"] == expected_qualities
        assert state.derived["metatype_info"]["powers"] == expected_powers
        assert state.derived["weapons"][0] == expected_weapon
        assert len(state.derived["weapons"]) == 1
        assert state.derived["karma_chargen"]["qualities"] == 0


def test_chum5_keeps_purchased_overlap_and_purchased_weapons_separate() -> None:
    magic = QUALITY_IDS["Magic Sense"]
    pistol = next(w["id"] for w in catalog()["weapons"] if w["name"] == "Ares Predator V")
    state = compute(_centaur(quality_ids=[magic], weapons=[WeaponInstall(weapon_id=pistol)]))
    raw, warnings = chum5_to_state(state_to_chum5(state))
    assert not warnings
    loaded = compute(CharacterState.model_validate(raw))
    assert loaded.quality_ids == [magic]
    assert [w.weapon_id for w in loaded.weapons] == [pistol]
    assert len(loaded.derived["qualities"]) == 4
    assert len(loaded.derived["weapons"]) == 2
