"""A Program Carrier (DT p.65) holds one program, bought on the deck it is
installed in, that the deck runs permanently: it cannot be stopped, it still
takes one of the deck's slots, and its name is the carrier's `<extra>`."""

import xml.etree.ElementTree as ET

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.engine import compute
from app.engine.gear.deck_modules import PROGRAM_CARRIER
from app.models import CharacterState, GearInstall
from tests.engine_support import _human

HERMES = "785179f5-1500-46b6-b04f-063effa3a457"  # Hermes Chariot: 2 programs
ERIKA = "b6d1476d-a08c-43fc-be0e-68ca9330a43e"  # Erika MCD-1: 1 program


def _program(name: str) -> str:
    return next(row["id"] for row in catalog()["programs"] if row["name"] == name)


def _state(*, equipped: bool = True, deck: str = HERMES, extra: list[GearInstall] | None = None) -> CharacterState:
    return compute(
        _human(
            "carrier",
            cyberdecks=[GearInstall(id="deck", gear_id=deck), GearInstall(id="other", gear_id=HERMES)],
            programs=[
                GearInstall(id="tb", gear_id=_program("Toolbox"), parent_id="deck", running=False),
                *(extra or []),
            ],
            gear=[
                GearInstall(id="pc", gear_id=PROGRAM_CARRIER, parent_id="deck", held_program_id="tb", equipped=equipped)
            ],
        )
    )


def _deck(state: CharacterState, deck_id: str = "deck") -> dict:
    return next(row for row in state.derived["cyberdecks"] if row["id"] == deck_id)


def _prog(state: CharacterState, prog_id: str = "tb") -> dict:
    return next(row for row in state.derived["programs"] if row["id"] == prog_id)


def _carrier(state: CharacterState) -> dict:
    return next(row for row in state.derived["gear"] if row["id"] == "pc")


def test_the_held_program_runs_and_takes_a_slot():
    state = _state()
    assert _prog(state)["running"] and _prog(state)["carried_by"] == "pc"
    assert _deck(state)["program_used"] == 1
    # Toolbox running raises Data Processing by 1 (SR5 p.245)
    assert _deck(state)["program_bonus"] == {"dataprocessing": 1}
    assert _carrier(state)["module_effect_supported"]
    assert next(g for g in state.gear if g.id == "pc").extra == "Toolbox"


def test_a_disabled_carrier_runs_nothing():
    state = _state(equipped=False)
    assert not _prog(state)["running"] and _prog(state)["carried_by"] == ""
    assert _deck(state)["program_used"] == 0


def test_the_held_program_counts_toward_the_limit():
    state = _state(deck=ERIKA, extra=[GearInstall(id="br", gear_id=_program("Browse"), parent_id="deck")])
    assert _deck(state)["program_used"] == 2
    assert any("runningProgramsOver" in str(w) for w in state.derived["warnings"])


def test_a_program_moved_to_another_deck_is_not_carried():
    raw = _state().model_copy(deep=True)
    raw.programs[0].parent_id = "other"
    state = compute(raw)
    assert not _prog(state)["running"] and _prog(state)["carried_by"] == ""
    assert any("carrierProgramElsewhere" in str(w) for w in state.derived["warnings"])


def test_a_deleted_program_lets_go_and_keeps_the_name():
    raw = _state().model_copy(deep=True)
    raw.programs = []
    state = compute(raw)
    carrier = next(g for g in state.gear if g.id == "pc")
    assert carrier.held_program_id is None and carrier.extra == "Toolbox"


def test_the_carrier_goes_out_by_name_and_comes_back_holding_it():
    root = ET.fromstring(state_to_chum5(_state()))
    carrier = next(el for el in root.iter("gear") if el.findtext("name") == "Program Carrier")
    assert carrier.findtext("extra") == "Toolbox"
    toolbox = next(el for el in root.iter("gear") if el.findtext("name") == "Toolbox")
    # it runs, whatever its own switch said
    assert toolbox.findtext("equipped") == "True"
    again = compute(CharacterState.model_validate(chum5_to_state(ET.tostring(root))[0]))
    held = next(g for g in again.gear if g.gear_id == PROGRAM_CARRIER).held_program_id
    assert held == next(p.id for p in again.programs if p.gear_id == _program("Toolbox"))
    assert next(p for p in again.derived["programs"] if p["id"] == held)["running"]
