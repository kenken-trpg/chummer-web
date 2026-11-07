"""SR5 p.245: a running Decryption, Stealth, Toolbox or Encryption raises the
Attack, Sleaze, Data Processing or Firewall of the deck running it by 1.

Chummer leaves this to the player, so the .chum5 export keeps the deck's own
values; everything that reads the deck row here gets the raised ones."""

import xml.etree.ElementTree as ET

import pytest

from app.chummer_export import state_to_chum5
from app.data_loader import catalog
from app.engine import compute
from app.models import CharacterState, CyberwareInstall, GearInstall
from tests.engine_support import ERIKA_DECK, _human, _mundane, _ware_id

#: the Erika MCD-1 as it comes: Attack 4, Sleaze 3, Data Processing 2, Firewall 1
ERIKA = {"attack": 4, "sleaze": 3, "dataprocessing": 2, "firewall": 1}


def _program(name: str) -> str:
    return next(row["id"] for row in catalog()["programs"] if row["name"] == name)


def _deck_with(*programs: GearInstall, decks: int = 1) -> CharacterState:
    rows = [GearInstall(id=f"deck{i}", gear_id=ERIKA_DECK) for i in range(decks)]
    return compute(_mundane("decker", cyberdecks=rows, programs=list(programs)))


def _stats(state: CharacterState, index: int = 0) -> dict[str, int]:
    row = state.derived["cyberdecks"][index]
    return {key: row[key] for key in ERIKA}


@pytest.mark.parametrize(
    ("name", "key"),
    [("Decryption", "attack"), ("Stealth", "sleaze"), ("Toolbox", "dataprocessing"), ("Encryption", "firewall")],
)
def test_a_running_program_raises_its_attribute(name: str, key: str) -> None:
    running = _deck_with(GearInstall(gear_id=_program(name), parent_id="deck0", running=True))
    assert _stats(running) == {**ERIKA, key: ERIKA[key] + 1}
    assert running.derived["cyberdecks"][0]["program_bonus"] == {key: 1}
    assert running.derived["programs"][0]["attribute_bonus"] == key

    stopped = _deck_with(GearInstall(gear_id=_program(name), parent_id="deck0", running=False))
    assert _stats(stopped) == ERIKA
    assert stopped.derived["cyberdecks"][0]["program_bonus"] == {}
    # the row still says what it would raise, for the label beside the checkbox
    assert stopped.derived["programs"][0]["attribute_bonus"] == key


def test_other_programs_raise_nothing() -> None:
    state = _deck_with(GearInstall(gear_id=_program("Browse"), parent_id="deck0", running=True))
    assert _stats(state) == ERIKA
    assert state.derived["programs"][0]["attribute_bonus"] == ""


def test_toolbox_raises_the_vr_initiative_too() -> None:
    """VR initiative is Data Processing + Intuition (SR5 p.229)."""
    without = _deck_with().derived["matrix_initiative"]
    with_toolbox = _deck_with(GearInstall(gear_id=_program("Toolbox"), parent_id="deck0", running=True)).derived[
        "matrix_initiative"
    ]
    assert with_toolbox["dataprocessing"] == without["dataprocessing"] + 1
    assert with_toolbox["value"] == without["value"] + 1


def test_the_point_goes_where_the_array_put_the_attribute() -> None:
    """Data Processing moved to the first slot (4): Toolbox makes it 5."""
    deck = GearInstall(id="deck0", gear_id=ERIKA_DECK, array_order=["dataprocessing", "sleaze", "attack", "firewall"])
    state = compute(
        _mundane(
            "reordered",
            cyberdecks=[deck],
            programs=[GearInstall(gear_id=_program("Toolbox"), parent_id="deck0", running=True)],
        )
    )
    row = state.derived["cyberdecks"][0]
    assert (row["dataprocessing"], row["attack"]) == (5, 2)
    assert row["array"] == [4, 3, 2, 1]  # the slots themselves are unchanged


def test_only_the_deck_running_it_is_raised() -> None:
    state = _deck_with(
        GearInstall(gear_id=_program("Toolbox"), parent_id="deck1", running=True),
        GearInstall(gear_id=_program("Encryption"), running=True),  # loose: runs nowhere
        decks=2,
    )
    assert _stats(state, 0) == ERIKA
    assert _stats(state, 1) == {**ERIKA, "dataprocessing": 3}


def test_all_four_together() -> None:
    names = ("Decryption", "Stealth", "Toolbox", "Encryption")
    state = _deck_with(*(GearInstall(gear_id=_program(n), parent_id="deck0", running=True) for n in names))
    assert _stats(state) == {key: value + 1 for key, value in ERIKA.items()}


def test_a_program_stored_in_a_datajack_plus_raises_nothing() -> None:
    """KC p.65: the programs in it do not run there."""
    state = compute(
        _human(
            "dj",
            cyberware=[CyberwareInstall(id="dj", ware_id=_ware_id("cyberware", "Datajack Plus"), rating=2)],
            cyberdecks=[GearInstall(id="deck0", gear_id=ERIKA_DECK)],
            programs=[GearInstall(gear_id=_program("Toolbox"), parent_id="dj", running=True)],
        )
    )
    assert _stats(state) == ERIKA


def test_the_chum5_deck_is_the_same_running_or_not() -> None:
    """The save carries no raised value: Chummer works the deck out itself."""

    def deck_fields(running: bool) -> dict[str, str | None]:
        state = _deck_with(GearInstall(id="tb", gear_id=_program("Toolbox"), parent_id="deck0", running=running))
        root = ET.fromstring(state_to_chum5(state))
        deck = next(el for el in root.iter("gear") if el.findtext("name") == "Erika MCD-1")
        return {child.tag: child.text for child in deck if len(child) == 0}

    stopped = deck_fields(False)
    assert stopped.get("devicerating") == "1"
    assert deck_fields(True) == stopped
