"""Block accounting fixtures do not establish species equipment eligibility."""

from xml.etree import ElementTree as ET

import pytest

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.engine import compute, default_attributes, find_metatype
from app.engine.ware.mount_blocks import check_mount_blocks
from app.models import CharacterState, CyberwareInstall, SettingsState
from tests.engine_support import _ware_id
from tests.notice_asserts import has
from tests.test_centaur_grants import _centaur
from tests.test_centaur_modular_limbs import _connectors


def _ware(ident: str, name: str, side: str | None = None, parent: str | None = None) -> CyberwareInstall:
    return CyberwareInstall(id=ident, ware_id=_ware_id("cyberware", name), side=side, parent_id=parent)


def _blocked(state: CharacterState) -> list[dict]:
    return [row for row in state.derived["errors"] if row["key"] == "engine.ware.modularMountBlocked"]


@pytest.mark.parametrize("species", ["Human", "Centaur"])
def test_additional_legs_expand_same_side_mount_capacity(species: str) -> None:
    state = _centaur(
        cyberware=[
            _ware("leg", "Obvious Full Leg", "Left"),
            _ware("hip", "Modular Connector, Hip", "Left"),
        ]
    )
    state.metatype = species
    state.attributes = default_attributes(find_metatype(species, None))
    compute(state)
    assert bool(_blocked(state)) is (species == "Human")
    if species == "Centaur":
        state.cyberware.append(_ware("extra", "Modular Connector, Hip", "Left"))
        assert _blocked(compute(state))
    assert len(state.cyberware) == (3 if species == "Centaur" else 2)


def test_opposite_side_mount_does_not_conflict_with_full_leg() -> None:
    state = compute(
        _centaur(cyberware=[_ware("leg", "Obvious Full Leg", "Left"), _ware("hip", "Modular Connector, Hip", "Right")])
    )
    assert not _blocked(state)


def test_four_connectors_and_their_modular_children_do_not_double_count() -> None:
    assert not _blocked(compute(_centaur(cyberware=_connectors())))


def test_descendants_share_the_root_slot_and_nested_connectors_conflict_locally() -> None:
    state = _centaur(
        cyberware=[
            _ware("knee", "Modular Connector, Knee", parent="leg"),
            _ware("leg", "Obvious Full Leg", "Left"),
        ]
    )
    assert not _blocked(compute(state))
    state.cyberware.append(_ware("ankle", "Modular Connector, Ankle", parent="leg"))
    compute(state)
    assert has(state.derived["errors"], "engine.ware.modularMountBlocked", name="Obvious Full Leg", mount="ankle")
    # The conflict inside one leg is independent of the body's other 3 legs.
    assert all(row["params"]["max"] == 1 for row in _blocked(state))


def test_detached_subtree_does_not_reserve_body_mounts_but_retains_internal_validation() -> None:
    state = _centaur(
        cyberware=[
            _ware("leg", "Obvious Full Leg, Modular", "Left"),
            _ware("knee", "Modular Connector, Knee", parent="leg"),
            _ware("hip", "Modular Connector, Hip", "Left"),
            _ware("hip2", "Modular Connector, Hip", "Left"),
        ]
    )
    assert not _blocked(compute(state))
    state.cyberware.append(_ware("ankle", "Modular Connector, Ankle", parent="leg"))
    compute(state)
    assert _blocked(state)
    assert all(row["params"]["name"] == {"tr": "Obvious Full Leg, Modular"} for row in _blocked(state))


def test_all_leg_slots_block_an_extra_root_connector_and_survive_saves() -> None:
    state = compute(
        _centaur(
            cyberware=[_ware("tank", "Liminal Body, Tank (Full)"), _ware("hip", "Modular Connector, Hip", "Left")],
            settings=SettingsState(enforce_capacity=False),
        )
    )
    assert has(state.derived["errors"], "engine.ware.modularMountBlocked", mount="hip", used=5, max=4)
    expected_cost = sum(row["nuyen"] for row in state.derived["cyberware"])
    for _ in range(2):
        state = compute(CharacterState.model_validate_json(state.model_dump_json()))
        saved = ET.fromstring(state_to_chum5(state))
        for ware in saved.findall("./cyberwares/cyberware"):
            assert ware.findtext("blocksmounts") == "ankle,knee,hip"
        raw, warnings = chum5_to_state(ET.tostring(saved, encoding="unicode"))
        assert not warnings
        state = compute(CharacterState.model_validate(raw))
        assert has(state.derived["errors"], "engine.ware.modularMountBlocked", used=5, max=4)
        assert sum(row["nuyen"] for row in state.derived["cyberware"]) == expected_cost
    state.cyberware = [
        inst for inst in state.cyberware if inst.ware_id != _ware_id("cyberware", "Modular Connector, Hip")
    ]
    assert not _blocked(compute(state))


def test_catalog_blocks_are_loaded_without_inventing_them_for_modular_legs() -> None:
    items = {row["name"]: row for row in catalog()["cyberware"]["items"]}
    assert items["Obvious Full Leg"]["blocks_mounts"] == ["ankle", "knee", "hip"]
    assert items["Modular Connector, Hip"]["blocks_mounts"] == ["ankle", "knee", "hip"]
    assert items["Obvious Full Leg, Modular"]["blocks_mounts"] == []


def test_repeated_block_tags_inside_one_root_reserve_one_slot() -> None:
    rows = [
        {"id": "a", "ware_id": "block", "name": "A", "side": "Left"},
        {"id": "b", "ware_id": "block", "name": "B", "side": "Left", "parent_id": "a"},
        {"id": "c", "ware_id": "mount", "name": "C", "side": "Left"},
    ]
    specs = {"block": {"blocks_mounts": ["hip"]}, "mount": {"modular_mount": "hip"}}
    assert not check_mount_blocks(rows, specs, {"leg": 2})
    assert check_mount_blocks(rows, specs, {})


def test_mounts_and_blocks_for_different_limbs_do_not_conflict() -> None:
    state = compute(
        _centaur(
            cyberware=[
                _ware("arm", "Obvious Full Arm", "Left"),
                _ware("arm2", "Obvious Full Arm", "Left"),
                _ware("hip", "Modular Connector, Hip", "Left"),
            ]
        )
    )
    assert not _blocked(state)


def test_multi_limb_chassis_interior_is_not_assumed_to_be_one_leg() -> None:
    rows = [
        {"id": "body", "ware_id": "body", "name": "Body", "limbslot": "leg", "limbslotcount": "all"},
        *[{"id": f"knee-{i}", "ware_id": "knee", "name": "Knee", "parent_id": "body"} for i in range(4)],
    ]
    specs = {"body": {}, "knee": {"modular_mount": "knee", "blocks_mounts": ["knee"]}}
    assert not check_mount_blocks(rows, specs, {"leg": 2})
