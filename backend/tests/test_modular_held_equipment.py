"""Ownership survives; detached storage cannot supply passive effects or attacks."""

from copy import deepcopy

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.engine import compute
from app.fvtt_export import state_to_fvtt
from app.models import CharacterState, CyberwareInstall, GearInstall
from tests.engine_support import _ware_id
from tests.test_centaur_grants import _centaur
from tests.test_centaur_modular_limbs import _connectors


def _gear(name: str) -> str:
    return next(row["id"] for row in catalog()["gear"] if row["name"] == name)


def _state() -> CharacterState:
    ware = _connectors()
    ware.extend(
        [
            CyberwareInstall(id="blade", ware_id=_ware_id("cyberware", "Foot Blade"), parent_id="leg-0"),
            CyberwareInstall(id="wires", ware_id=_ware_id("cyberware", "Skillwires"), rating=4),
            CyberwareInstall(id="jack", ware_id=_ware_id("cyberware", "Skilljack"), rating=4),
        ]
    )
    # A Custom container is allowed by the limb's real allowgear. Its arbitrary
    # contents test transitive storage, not equipment fit for centaurs.
    gear = [
        GearInstall(id="mask", gear_id=_gear("Respirator"), rating=4, parent_id="box", equipped=True),
        GearInstall(id="soft", gear_id=_gear("Activesoft"), rating=4, parent_id="inner", extra="Archery"),
        GearInstall(id="inner", gear_id=_gear("Custom Item"), parent_id="box"),
        GearInstall(id="box", gear_id=_gear("Custom Item"), parent_id="leg-0", cost=25),
        GearInstall(id="ordinary", gear_id=_gear("Respirator"), rating=1),
    ]
    return compute(_centaur(cyberware=ware, gear=gear))


def test_detach_suppresses_nested_gear_effects_and_skillsofts_without_mutating_ownership() -> None:
    state = _state()
    initial = deepcopy(state.derived)
    assert initial["skillsoft"]["Archery"] == 4
    assert all(row["modular_equipped"] for row in initial["gear"] if row["id"] != "ordinary")
    saved_gear = [row.model_dump() for row in state.gear]
    next(row for row in state.cyberware if row.id == "leg-0").parent_id = None
    compute(state)
    assert state.derived["skillsoft"].get("Archery", 0) == 0
    assert all(row["modular_equipped"] is False for row in state.derived["gear"] if row["id"] != "ordinary")
    assert "modular_equipped" not in next(row for row in state.derived["gear"] if row["id"] == "ordinary")
    assert [row.model_dump() for row in state.gear] == saved_gear
    assert state.derived["nuyen_spent"] == initial["nuyen_spent"]
    assert state.derived["special_armor"]["toxin_inhalation"] == 1
    assert initial["special_armor"]["toxin_inhalation"] > 1
    next(row for row in state.cyberware if row.id == "leg-0").parent_id = "hip-0"
    compute(state)
    for key in ("gear", "skillsoft", "special_armor", "nuyen_spent"):
        assert state.derived[key] == initial[key]


def test_implanted_weapon_stays_in_inventory_with_derived_connection_state() -> None:
    state = _state()
    weapon = next(row for row in state.derived["weapons"] if row.get("source_ware_id") == "blade")
    assert weapon["modular_equipped"] is True
    initial = deepcopy(weapon)
    next(row for row in state.cyberware if row.id == "leg-0").parent_id = None
    compute(state)
    weapon = next(row for row in state.derived["weapons"] if row.get("source_ware_id") == "blade")
    assert weapon == {**initial, "modular_equipped": False}
    assert any(row.id == "blade" and row.parent_id == "leg-0" for row in state.cyberware)


def test_detached_subtree_survives_json_and_chum5_and_reconnects() -> None:
    state = _state()
    cost = state.derived["nuyen_spent"]
    next(row for row in state.cyberware if row.id == "leg-0").parent_id = None
    for _ in range(2):
        state = compute(CharacterState.model_validate_json(state.model_dump_json()))
        raw, warnings = chum5_to_state(state_to_chum5(state))
        assert not warnings
        state = compute(CharacterState.model_validate(raw))
        detached = next(
            row
            for row in state.cyberware
            if row.ware_id == _ware_id("cyberware", "Obvious Full Leg, Modular") and not row.parent_id
        )
        weapon = next(row for row in state.derived["weapons"] if row["name"] == "Foot Blade")
        assert weapon["modular_equipped"] is False
        assert state.derived["skillsoft"].get("Archery", 0) == 0
        assert len(state.gear) == 5
        assert state.derived["nuyen_spent"] == cost
        assert next(row for row in state.gear if row.gear_id == _gear("Respirator") and row.rating == 4).equipped
    # IDs are normalized on Chummer import: use the now-empty connector.
    hip = next(
        row
        for row in state.derived["cyberware"]
        if row["name"] == "Modular Connector, Hip" and row.get("limb_agi") == 0
    )
    detached.parent_id = hip["id"]
    compute(state)
    assert state.derived["skillsoft"]["Archery"] == 4
    assert next(row for row in state.derived["weapons"] if row["name"] == "Foot Blade")["modular_equipped"] is True


def test_foundry_export_keeps_detached_inventory_but_marks_it_unequipped() -> None:
    state = _state()
    for connected in (True, False, True):
        next(row for row in state.cyberware if row.id == "leg-0").parent_id = "hip-0" if connected else None
        compute(state)
        char = state_to_fvtt(state, "en")["characters"]["character"]
        blade = next(row for row in char["weapons"]["weapon"] if row["name_english"] == "Foot Blade")
        mask = next(row for row in char["gears"]["gear"] if row["guid"] == "mask")
        assert blade["equipped"] == mask["equipped"] == ("True" if connected else "False")
