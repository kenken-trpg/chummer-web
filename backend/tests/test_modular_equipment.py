"""Modular connectivity/effects; mount eligibility is a separate validation."""

from copy import deepcopy
from typing import Any
from xml.etree import ElementTree as ET

import pytest

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.engine import compute
from app.engine.ware.limbs import count_redliner_limbs, limb_attribute_replace
from app.engine.ware.modular import apply_modular_state
from app.engine.ware.pairs import apply_wireless_pairs, pair_bonus_sources
from app.models import CharacterState, CyberwareInstall, WeaponInstall
from tests.engine_support import _ware_id
from tests.test_centaur_grants import _centaur
from tests.test_centaur_modular_limbs import _connectors


def test_detach_reconnect_preserves_four_legs_cost_and_saved_ownership() -> None:
    state = compute(_centaur(cyberware=_connectors()))
    initial = deepcopy(state.derived)
    leg = next(inst for inst in state.cyberware if inst.id == "leg-0")
    leg.parent_id = None
    compute(state)
    rows = {row["id"]: row for row in state.derived["cyberware"]}
    assert rows["leg-0"]["modular_equipped"] is False
    assert rows["leg-0-Strength"]["modular_equipped"] is False
    assert rows["hip-0"]["modular_equipped"] is True
    assert rows["hip-0"]["limb_agi"] == rows["hip-0"]["limb_str"] == 0
    assert state.derived["condition_monitor"]["physical"] == initial["condition_monitor"]["physical"] - 1
    assert sum(row["nuyen"] for row in state.derived["cyberware"]) == sum(row["nuyen"] for row in initial["cyberware"])
    assert state.derived["totals"]["ESS"] == initial["totals"]["ESS"]
    # Web JSON and Chummer XML retain the detached subtree as owned ware.
    for _ in range(2):
        state = compute(CharacterState.model_validate_json(state.model_dump_json()))
        raw, warnings = chum5_to_state(state_to_chum5(state))
        assert not warnings
        state = compute(CharacterState.model_validate(raw))
        detached = next(
            inst
            for inst in state.cyberware
            if inst.ware_id == _ware_id("cyberware", "Obvious Full Leg, Modular") and inst.parent_id is None
        )
        assert detached.parent_id is None
        assert any(
            inst.parent_id == detached.id and inst.ware_id == _ware_id("cyberware", "Customized Strength")
            for inst in state.cyberware
        )
        assert next(row for row in state.derived["cyberware"] if row["id"] == detached.id)["modular_equipped"] is False
    empty_hip = next(row for row in state.derived["cyberware"] if row.get("limb_agi") == 0)
    detached.parent_id = empty_hip["id"]
    compute(state)
    for key in ("condition_monitor", "limb_replace", "movement", "totals"):
        assert state.derived[key] == initial[key]
    saved = ET.fromstring(state_to_chum5(state))
    assert len(saved.findall("./cyberwares/cyberware")) == 4


def test_detached_partial_limbs_do_not_complete_a_pair() -> None:
    installs = [
        CyberwareInstall(id=f"knee-{i}", ware_id=_ware_id("cyberware", "Modular Connector, Knee"), side=side)
        for i, side in enumerate(("Left", "Right"))
    ]
    installs += [
        CyberwareInstall(
            id=f"lower-{i}",
            ware_id=_ware_id("cyberware", "Obvious Lower Leg, Modular"),
            parent_id=f"knee-{i}",
            side=side,
        )
        for i, side in enumerate(("Left", "Right"))
    ]
    state = compute(_centaur(cyberware=installs))
    connected_boxes = state.derived["condition_monitor"]["physical"]
    installs[-1].parent_id = None
    compute(state)
    assert state.derived["condition_monitor"]["physical"] == connected_boxes - 1
    installs[-2].parent_id = None
    compute(state)
    assert state.derived["condition_monitor"]["physical"] == connected_boxes - 1


@pytest.mark.parametrize("outer_connected", [False, True])
def test_highest_ancestor_controls_nested_mounts_and_child_effects(outer_connected: bool) -> None:
    specs = {
        "socket": {"modular_mount": "hip"},
        "plug": {"mounts_to": "hip"},
        "nested": {"modular_mount": "knee", "mounts_to": "hip"},
        "normal": {},
    }
    rows: list[dict[str, Any]] = [
        {"id": "child", "ware_id": "normal", "parent_id": "inner", "bonus": [1]},
        {"id": "inner", "ware_id": "nested", "parent_id": "outer", "bonus": [1]},
        {"id": "outer", "ware_id": "plug", "parent_id": "root" if outer_connected else None, "bonus": [1]},
        {"id": "root", "ware_id": "socket", "bonus": [1]},
        {"id": "ordinary", "ware_id": "normal", "bonus": [1]},
    ]
    apply_modular_state(rows, specs)
    for row in rows[:3]:
        assert row["modular_equipped"] is outer_connected
        assert row["bonus"] == ([1] if outer_connected else [])
    assert "modular_equipped" not in rows[-1]


def test_inactive_subtree_is_excluded_from_average_but_redliner_keeps_xml_slot_count() -> None:
    rows = [
        {"id": "outer", "modular_equipped": False},
        {"id": "leg", "parent_id": "outer", "limbslot": "leg", "limb_agi": 8, "limb_str": 8},
    ]
    assert limb_attribute_replace(rows, 3, 3, {}, {"leg": 2}) is None
    # GetCyberlimbCount has no equipped guard, unlike CalculatedTotalValue.
    assert count_redliner_limbs(rows, {"leg": 4}) == 1


def test_disconnected_wireless_implant_cannot_supply_or_receive_pair_bonus() -> None:
    # Connectivity and pairing fixture, not a claim of legal mount fit.
    def rows() -> list[tuple[str, dict[str, Any]]]:
        return [
            (
                "cyberware",
                {"ware_id": _ware_id("cyberware", name), "name": name, "wireless": True, "bonus": [], "rating": 1},
            )
            for name in ("Wired Reflexes", "Reaction Enhancers")
        ]

    connected = rows()
    apply_wireless_pairs(connected)
    assert all(row.get("wireless_paired") for _, row in connected)
    for index in (0, 1):
        detached = rows()
        detached[index][1]["modular_equipped"] = False
        apply_wireless_pairs(detached)
        assert all(not row.get("wireless_paired") and row["bonus"] == [] for _, row in detached)
        assert not pair_bonus_sources(detached)


def test_cyclic_modular_ownership_terminates_with_effects_disabled() -> None:
    rows = [
        {"id": "a", "ware_id": "plain", "parent_id": "b", "bonus": [1]},
        {"id": "b", "ware_id": "plug", "parent_id": "a", "bonus": [1]},
    ]
    apply_modular_state(rows, {"plain": {}, "plug": {"mounts_to": "hip"}})
    assert all(row["modular_equipped"] is False and row["bonus"] == [] for row in rows)


def test_detached_children_keep_skill_choices_without_applying_them() -> None:
    # Effect-routing fixture; mount compatibility is not inferred from it.
    state = _centaur(
        cyberware=[
            CyberwareInstall(id="hip", ware_id=_ware_id("cyberware", "Modular Connector, Hip")),
            CyberwareInstall(id="leg", ware_id=_ware_id("cyberware", "Obvious Full Leg, Modular"), parent_id="hip"),
            CyberwareInstall(id="opt", ware_id=_ware_id("cyberware", "Cyberlimb Optimization"), parent_id="leg"),
            CyberwareInstall(id="hw", ware_id=_ware_id("cyberware", "Active Hardwires"), parent_id="leg", rating=4),
        ],
        skill_picks={"ware:opt:acc0": "Pistols", "ware:hw:0": "Archery"},
        weapons=[
            WeaponInstall(weapon_id=next(row["id"] for row in catalog()["weapons"] if row["name"] == "Ares Predator V"))
        ],
    )
    compute(state)
    connected_accuracy = next(row["accuracy"] for row in state.derived["weapons"] if row["name"] == "Ares Predator V")
    assert state.derived["skillsoft"]["Archery"] == 4
    picks = dict(state.skill_picks)
    next(inst for inst in state.cyberware if inst.id == "leg").parent_id = None
    compute(state)
    assert state.skill_picks == picks
    assert not state.derived["skill_pick_slots"]
    assert state.derived["skillsoft"].get("Archery", 0) == 0
    assert (
        int(next(row["accuracy"] for row in state.derived["weapons"] if row["name"] == "Ares Predator V"))
        == int(connected_accuracy) - 1
    )
    next(inst for inst in state.cyberware if inst.id == "leg").parent_id = "hip"
    compute(state)
    assert state.derived["skillsoft"]["Archery"] == 4
    assert (
        next(row["accuracy"] for row in state.derived["weapons"] if row["name"] == "Ares Predator V")
        == connected_accuracy
    )
