"""Direct modular mount fit, grade and occupancy; not body-wide mount blocking."""

from app.characters import apply_patch
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.engine import compute
from app.models import CharacterPatch, CharacterState, CyberwareInstall, SettingsState
from tests.engine_support import _ware_id
from tests.notice_asserts import has
from tests.test_centaur_grants import _centaur
from tests.test_centaur_modular_limbs import _connectors


def _modular_errors(state: CharacterState) -> list[dict]:
    return [row for row in state.derived["errors"] if row["key"].startswith("engine.ware.modular")]


def test_four_same_named_connectors_have_independent_occupancy_and_allow_enhancements() -> None:
    state = compute(_centaur(cyberware=_connectors()))
    assert not _modular_errors(state)
    for _ in range(2):
        state = compute(CharacterState.model_validate_json(state.model_dump_json()))
        raw, warnings = chum5_to_state(state_to_chum5(state))
        assert not warnings
        state = compute(CharacterState.model_validate(raw))
        assert not _modular_errors(state)


def test_wrong_mount_type_is_an_error_without_deleting_or_reparenting_purchases() -> None:
    state = _centaur(cyberware=_connectors())
    leg = next(inst for inst in state.cyberware if inst.id == "leg-0")
    leg.ware_id = _ware_id("cyberware", "Obvious Lower Leg, Modular")  # knee, not hip
    original = [(inst.id, inst.ware_id, inst.parent_id) for inst in state.cyberware]
    compute(state)
    assert has(
        state.derived["errors"],
        "engine.ware.modularMountMismatch",
        name="Obvious Lower Leg, Modular",
        parent="Modular Connector, Hip",
        mount="knee",
    )
    assert [(inst.id, inst.ware_id, inst.parent_id) for inst in state.cyberware] == original
    assert len(_modular_errors(compute(state))) == 1
    leg.parent_id = None  # owned detached pieces need no connector
    assert not _modular_errors(compute(state))


def test_ordinary_parent_cannot_replace_a_modular_connector() -> None:
    state = compute(
        _centaur(
            cyberware=[
                CyberwareInstall(id="parent", ware_id=_ware_id("cyberware", "Obvious Full Leg")),
                CyberwareInstall(
                    id="plug", ware_id=_ware_id("cyberware", "Obvious Full Leg, Modular"), parent_id="parent"
                ),
            ]
        )
    )
    assert has(state.derived["errors"], "engine.ware.modularMountMismatch", mount="hip")


def test_double_connection_counts_by_parent_id_even_if_capacity_is_disabled() -> None:
    state = _centaur(cyberware=_connectors(), settings=SettingsState(enforce_capacity=False))
    state.cyberware.append(
        CyberwareInstall(
            id="extra-leg", ware_id=_ware_id("cyberware", "Synthetic Full Leg, Modular"), parent_id="hip-0"
        )
    )
    state = apply_patch(state, CharacterPatch(cyberware=state.cyberware))
    assert has(state.derived["errors"], "engine.ware.modularMountOccupied", count=2)
    assert len(_modular_errors(state)) == 1
    assert any(inst.id == "extra-leg" and inst.parent_id == "hip-0" for inst in state.cyberware)
    expected_cost = sum(row["nuyen"] for row in state.derived["cyberware"])
    raw, warnings = chum5_to_state(state_to_chum5(state))
    assert not warnings
    state = compute(CharacterState.model_validate(raw))
    assert has(state.derived["errors"], "engine.ware.modularMountOccupied", count=2)
    assert sum(row["nuyen"] for row in state.derived["cyberware"]) == expected_cost
    extra = next(
        inst for inst in state.cyberware if inst.ware_id == _ware_id("cyberware", "Synthetic Full Leg, Modular")
    )
    extra.parent_id = None
    assert not _modular_errors(compute(state))


def test_same_grade_required_but_other_child_parts_do_not_occupy_modular_mount() -> None:
    state = _centaur(cyberware=_connectors())
    leg = next(inst for inst in state.cyberware if inst.id == "leg-0")
    leg.grade = "Alphaware"
    compute(state)
    assert has(
        state.derived["errors"],
        "engine.ware.modularGradeMismatch",
        name="Obvious Full Leg, Modular",
        grade="Alphaware",
        parent_grade="Standard",
    )
    assert not has(state.derived["errors"], "engine.ware.modularMountOccupied")
    next(inst for inst in state.cyberware if inst.id == "hip-0").grade = "Alphaware"
    assert not _modular_errors(compute(state))


def test_wrong_type_does_not_also_report_occupancy_of_the_hosts_mount() -> None:
    state = _centaur(cyberware=_connectors())
    state.cyberware.append(
        CyberwareInstall(id="wrong", ware_id=_ware_id("cyberware", "Obvious Lower Leg, Modular"), parent_id="hip-0")
    )
    compute(state)
    assert has(state.derived["errors"], "engine.ware.modularMountMismatch")
    assert not has(state.derived["errors"], "engine.ware.modularMountOccupied")


def test_nested_connectors_validate_against_direct_parent_even_when_detached() -> None:
    state = _centaur(
        cyberware=[
            CyberwareInstall(id="lower", ware_id=_ware_id("cyberware", "Obvious Lower Leg, Modular"), parent_id="knee"),
            CyberwareInstall(id="knee", ware_id=_ware_id("cyberware", "Modular Connector, Knee"), parent_id="leg"),
            CyberwareInstall(id="leg", ware_id=_ware_id("cyberware", "Obvious Full Leg, Modular")),
        ]
    )
    assert not _modular_errors(compute(state))
    next(inst for inst in state.cyberware if inst.id == "lower").parent_id = "leg"
    assert has(compute(state).derived["errors"], "engine.ware.modularMountMismatch", mount="knee")
