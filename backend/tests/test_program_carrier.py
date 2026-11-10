"""A Program Carrier (DT p.65) holds the one program picked when it is made
(its `extra`, Chummer's `<selecttext>`): an extra program the deck runs
permanently, outside its slots, and paid for in the module's own price."""

from app.data_loader import catalog
from app.engine import compute
from app.engine.gear.deck_modules import PROGRAM_CARRIER
from app.models import CharacterState, GearInstall
from tests.engine_support import _human

ERIKA = "b6d1476d-a08c-43fc-be0e-68ca9330a43e"  # Erika MCD-1: 1 program, DP 2


def _program(name: str) -> str:
    return next(row["id"] for row in catalog()["programs"] if row["name"] == name)


def _state(
    held: str = "Toolbox", *, equipped: bool = True, programs: list[GearInstall] | None = None
) -> CharacterState:
    return compute(
        _human(
            "carrier",
            cyberdecks=[GearInstall(id="deck", gear_id=ERIKA)],
            programs=programs or [],
            gear=[GearInstall(id="pc", gear_id=PROGRAM_CARRIER, parent_id="deck", extra=held, equipped=equipped)],
        )
    )


def _deck(state: CharacterState) -> dict:
    return next(row for row in state.derived["cyberdecks"] if row["id"] == "deck")


def _bare_dp() -> int:
    return int(_deck(compute(_human("bare", cyberdecks=[GearInstall(id="deck", gear_id=ERIKA)])))["dataprocessing"])


def test_the_held_program_runs_outside_the_slots():
    state = _state(programs=[GearInstall(id="br", gear_id=_program("Browse"), parent_id="deck")])
    deck = _deck(state)
    assert deck["carrier_programs"] == ["Toolbox"]
    # the deck's one slot still holds Browse, with nothing over
    assert deck["program_used"] == 1
    assert not [w for w in state.derived["warnings"] if "runningProgramsOver" in str(w)]
    # a running Toolbox raises Data Processing by 1 (SR5 p.245)
    assert deck["program_bonus"] == {"dataprocessing": 1}
    assert int(deck["dataprocessing"]) == _bare_dp() + 1
    assert next(r for r in state.derived["gear"] if r["id"] == "pc")["module_effect_supported"]


def test_the_price_includes_the_program():
    state = _state()
    assert next(r for r in state.derived["gear"] if r["id"] == "pc")["nuyen"] == 900
    assert state.derived["programs"] == []


def test_a_disabled_carrier_runs_nothing():
    deck = _deck(_state(equipped=False))
    assert deck["carrier_programs"] == []
    assert deck["program_bonus"] == {}


def test_the_same_program_in_a_slot_does_not_raise_it_twice():
    state = _state(programs=[GearInstall(id="tb", gear_id=_program("Toolbox"), parent_id="deck")])
    assert _deck(state)["program_bonus"] == {"dataprocessing": 1}
