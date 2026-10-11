"""Slot and inherited-attribute accounting, not modular mount eligibility."""

from xml.etree import ElementTree as ET

import pytest

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.engine import compute
from app.engine.ware.limbs import _apply_limb_attributes, count_redliner_limbs, limb_attribute_replace
from app.models import CharacterState, CyberwareInstall, SettingsState
from app.rules import rules_for, using_rules
from tests.engine_support import _quality_id, _ware_id
from tests.test_centaur_grants import _centaur


def _connectors(with_children: bool = True) -> list[CyberwareInstall]:
    roots = [
        CyberwareInstall(id=f"hip-{i}", ware_id=_ware_id("cyberware", "Modular Connector, Hip"), side=side)
        for i, side in enumerate(["Left", "Right", "Left", "Right"])
    ]
    if not with_children:
        return roots
    kids = [
        CyberwareInstall(id=f"leg-{i}", ware_id=_ware_id("cyberware", "Obvious Full Leg, Modular"), parent_id=root.id)
        for i, root in enumerate(roots)
    ]
    mods = [
        CyberwareInstall(
            id=f"{kid.id}-{name}",
            ware_id=_ware_id("cyberware", f"Customized {name}"),
            rating=rating,
            parent_id=kid.id,
        )
        for i, kid in enumerate(kids)
        for name, rating in [("Agility", 3 + i), ("Strength", 4 + i)]
        if not (name == "Agility" and i == 0)  # base 3 needs no customization
    ]
    return [*reversed(mods), *reversed(kids), *roots]


@pytest.mark.parametrize("name", ["Obvious Foot", "Obvious Lower Leg", "Partial Cyberskull"])
def test_partial_limbs_have_local_attributes_but_no_whole_body_slot(name: str) -> None:
    spec = next(row for row in catalog()["cyberware"]["items"] if row["name"] == name)
    assert not spec["limbslot"]
    state = compute(_centaur(cyberware=[CyberwareInstall(ware_id=spec["id"])], quality_ids=[_quality_id("Redliner")]))
    assert state.derived["limb_replace"] is None
    assert state.derived["limb_quality"]["count"] == 0
    assert state.derived["cyberware"][0]["limb_agi"] == 3
    saved = ET.fromstring(state_to_chum5(state)).find("./cyberwares/cyberware")
    assert saved is not None and saved.findtext("category") == "Cyberlimb"
    assert not saved.findtext("limbslot")


@pytest.mark.parametrize("redliner", [False, True])
def test_four_connectors_inherit_individual_child_attributes_and_count_only_once(redliner: bool) -> None:
    state = compute(
        _centaur(
            cyberware=_connectors(),
            settings=SettingsState(cyberleg_movement=True),
            quality_ids=[_quality_id("Redliner")] if redliner else [],
        )
    )
    rows = {row["id"]: row for row in state.derived["cyberware"]}
    for i in range(4):
        root, child = rows[f"hip-{i}"], rows[f"leg-{i}"]
        assert root["limb_agi"] == child["limb_agi"] == 3 + i + (2 if redliner else 0)
        assert root["limb_str"] == child["limb_str"] == 4 + i + (2 if redliner else 0)
        assert root["side"] == child["side"]
    average = state.derived["limb_replace"]
    assert (average["count"], average["parts"], average["slots"]["leg"]) == (4, 8, 4)
    assert (average["agi"], average["str"]) == ((4, 6) if redliner else (3, 5))
    assert state.derived["movement"]["walk"] == ("5" if redliner else "3")
    assert state.derived["movement"]["modes"]["Swim"]["walk"] == ("5" if redliner else "4")
    if redliner:
        assert state.derived["limb_quality"]["count"] == 4
        assert state.derived["limb_quality"]["cm_physical"] == -6
    expected = (state.derived["limb_replace"], state.derived["movement"], state.derived["limb_quality"])
    for _ in range(2):
        state = compute(CharacterState.model_validate_json(state.model_dump_json()))
        root = ET.fromstring(state_to_chum5(state))
        hips = root.findall("./cyberwares/cyberware")
        assert len(hips) == 4
        for hip in hips:
            assert hip.findtext("limbslot") == "leg"
            assert hip.findtext("limbslotcount") == "1"
            assert hip.findtext("inheritattributes") == "True"
            assert hip.findtext("hasmodularmount") == "hip"
            child = hip.find("./children/cyberware")
            assert child is not None and child.findtext("plugsintomodularmount") == "hip"
        raw, warnings = chum5_to_state(ET.tostring(root, encoding="unicode"))
        assert not warnings
        state = compute(CharacterState.model_validate(raw))
        state.settings.cyberleg_movement = True  # separate Chummer settings file
        compute(state)
        assert (state.derived["limb_replace"], state.derived["movement"], state.derived["limb_quality"]) == expected


def test_empty_connectors_do_not_invent_base_three_or_reuse_meat_attributes() -> None:
    state = _centaur(cyberware=_connectors(False))
    state.attributes.update(STR=5, AGI=5)
    state = compute(state)
    assert all(row["limb_str"] == row["limb_agi"] == 0 for row in state.derived["cyberware"])
    assert (state.derived["limb_replace"]["count"], state.derived["limb_replace"]["parts"]) == (4, 8)
    assert (state.derived["totals"]["STR"], state.derived["totals"]["AGI"]) == (3, 3)


def test_inheritance_rounds_down_positive_children_and_ignores_enhancement_rows() -> None:
    # Arithmetic fixture with nested inheritance; this is not a claim that
    # multiple modular legs can legally attach to a single connector.
    rows = [
        {"id": "a", "parent_id": "inner", "name": "A", "category": "Cyberlimb"},
        {"id": "mod", "parent_id": "a", "name": "Customized Agility", "rating": 4},
        {"id": "b", "parent_id": "inner", "name": "B", "category": "Cyberlimb"},
        {"id": "inner", "parent_id": "outer", "inherit_attributes": True},
        {"id": "outer", "inherit_attributes": True},
        {"id": "ignored", "parent_id": "inner", "name": "Armor", "rating": 1},
    ]
    _apply_limb_attributes(rows, {"AGI": {"aug": 10}, "STR": {"aug": 12}})
    assert rows[0]["limb_agi"] == 4
    assert rows[2]["limb_agi"] == 3
    assert rows[3]["limb_agi"] == rows[4]["limb_agi"] == 3


def test_slot_metadata_and_parent_ownership_control_counting_instead_of_names() -> None:
    rows = [
        {"id": "outer", "name": "Container"},
        {
            "id": "root",
            "parent_id": "outer",
            "name": "Lower Foot Connector",
            "limbslot": "leg",
            "side": "Left",
            "limb_agi": 6,
            "limb_str": 6,
        },
        {"id": "kid", "parent_id": "root", "limbslot": "leg", "side": "Left", "limb_agi": 9, "limb_str": 9},
    ]
    assert count_redliner_limbs(rows, {"leg": 4}) == 1
    average = limb_attribute_replace(rows, 3, 3, {"AGI": {"aug": 10}, "STR": {"aug": 12}}, {"leg": 2})
    assert average is not None and average["count"] == 1
    assert average["agi"] == average["str"] == 4


def test_excluded_parent_is_skipped_for_average_but_redliner_visits_its_children() -> None:
    rows = [
        {"id": "torso", "limbslot": "torso", "limb_agi": 3, "limb_str": 3},
        {"id": "leg", "parent_id": "torso", "limbslot": "leg", "limb_agi": 6, "limb_str": 6},
    ]
    assert count_redliner_limbs(rows, {"leg": 4}) == 1
    with using_rules(rules_for(SettingsState(exclude_limb_slot="torso"))):
        assert limb_attribute_replace(rows, 3, 3, {}, {"leg": 2}) is None
