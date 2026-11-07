"""Overclocker (RF p.148) raises the Matrix attribute the player picks on a deck.

Chummer keeps the pick per deck as `<overclocked>` (`Gear.Overclocked`: None,
Attack, Sleaze, Data Processing or Firewall) and adds it by name. With no pick
anywhere, this app goes on giving the highest-rated deck's Attack the point."""

import xml.etree.ElementTree as ET

import pytest

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.engine import compute
from app.models import CharacterState, GearInstall
from tests.engine_support import ERIKA_DECK, _mundane

OVERCLOCKER = "554ca59c-22e6-46ef-9b05-250ec8abd728"
#: the Erika MCD-1 as it comes: Attack 4, Sleaze 3, Data Processing 2, Firewall 1
ERIKA = {"attack": 4, "sleaze": 3, "dataprocessing": 2, "firewall": 1}


def _deck(name: str) -> str:
    return next(row["id"] for row in catalog()["cyberdecks"] if row["name"] == name)


def _with(*decks: GearInstall, overclocker: bool = True) -> CharacterState:
    return compute(_mundane("oc", quality_ids=[OVERCLOCKER] if overclocker else [], cyberdecks=list(decks)))


def _stats(state: CharacterState, index: int = 0) -> dict[str, int]:
    row = state.derived["cyberdecks"][index]
    return {key: row[key] for key in ERIKA}


@pytest.mark.parametrize("key", ["attack", "sleaze", "dataprocessing", "firewall"])
def test_the_picked_attribute_is_raised(key: str) -> None:
    state = _with(GearInstall(id="d", gear_id=ERIKA_DECK, overclocked=key))
    assert _stats(state) == {**ERIKA, key: ERIKA[key] + 1}
    assert state.derived["cyberdecks"][0]["overclocker"] == key
    assert state.derived["cyberdecks"][0]["overclocked"] == key


def test_none_raises_nothing() -> None:
    state = _with(GearInstall(id="d", gear_id=ERIKA_DECK, overclocked="none"))
    assert _stats(state) == ERIKA
    assert "overclocker" not in state.derived["cyberdecks"][0]


def test_with_no_pick_the_attack_of_the_best_deck_is_raised() -> None:
    """What every character with Overclocker had before there was a pick."""
    state = _with(GearInstall(id="d", gear_id=ERIKA_DECK))
    assert _stats(state) == {**ERIKA, "attack": 5}
    assert state.derived["cyberdecks"][0]["overclocker"] == "attack"
    assert state.derived["cyberdecks"][0]["overclocked"] is None


def test_without_the_quality_a_pick_does_nothing() -> None:
    state = _with(GearInstall(id="d", gear_id=ERIKA_DECK, overclocked="firewall"), overclocker=False)
    assert _stats(state) == ERIKA


def test_a_pick_on_one_deck_takes_it_off_the_fallback() -> None:
    """Picking on the lesser deck: the better one no longer gets the Attack."""
    state = _with(
        GearInstall(id="best", gear_id=_deck("Shiawase Cyber-5")),
        GearInstall(id="erika", gear_id=ERIKA_DECK, overclocked="firewall"),
    )
    best, erika = state.derived["cyberdecks"]
    assert "overclocker" not in best
    assert erika["overclocker"] == "firewall"
    assert _stats(state, 1) == {**ERIKA, "firewall": 2}


def test_the_point_follows_the_attribute_through_the_array() -> None:
    """Data Processing moved to the first slot (4): Overclocker makes it 5."""
    deck = GearInstall(
        id="d",
        gear_id=ERIKA_DECK,
        array_order=["dataprocessing", "sleaze", "attack", "firewall"],
        overclocked="dataprocessing",
    )
    row = _with(deck).derived["cyberdecks"][0]
    assert (row["dataprocessing"], row["attack"]) == (5, 2)


def test_the_vr_initiative_takes_an_overclocked_data_processing() -> None:
    plain = _with(GearInstall(id="d", gear_id=ERIKA_DECK, overclocked="attack")).derived["matrix_initiative"]
    dp = _with(GearInstall(id="d", gear_id=ERIKA_DECK, overclocked="dataprocessing")).derived["matrix_initiative"]
    assert dp["dataprocessing"] == plain["dataprocessing"] + 1


def _overclocked(state: CharacterState) -> str | None:
    root = ET.fromstring(state_to_chum5(state))
    deck = next(el for el in root.iter("gear") if el.findtext("name") == "Erika MCD-1")
    return deck.findtext("overclocked")


@pytest.mark.parametrize(
    ("pick", "written"),
    [
        ("dataprocessing", "Data Processing"),
        ("sleaze", "Sleaze"),
        ("none", "None"),
        # no pick: the deck that got the Attack says so, so Chummer adds it too
        (None, "Attack"),
    ],
)
def test_the_chum5_says_what_the_deck_got(pick: str | None, written: str) -> None:
    assert _overclocked(_with(GearInstall(id="d", gear_id=ERIKA_DECK, overclocked=pick))) == written


def test_without_the_quality_the_chum5_says_none() -> None:
    assert _overclocked(_with(GearInstall(id="d", gear_id=ERIKA_DECK, overclocked="sleaze"), overclocker=False)) == (
        "None"
    )


def _reimport(state: CharacterState) -> CharacterState:
    return CharacterState.model_validate(chum5_to_state(state_to_chum5(state))[0])


@pytest.mark.parametrize("pick", ["attack", "sleaze", "dataprocessing", "firewall"])
def test_the_pick_comes_back_from_the_chum5(pick: str) -> None:
    state = _with(GearInstall(id="d", gear_id=ERIKA_DECK, overclocked=pick))
    back = compute(_reimport(state))
    assert back.cyberdecks[0].overclocked == pick
    assert _stats(back) == _stats(state)


def test_a_chummer_none_is_read_as_no_pick() -> None:
    """Chummer writes None on every deck it was never asked about."""
    state = _with(GearInstall(id="d", gear_id=ERIKA_DECK, overclocked="none"))
    assert _reimport(state).cyberdecks[0].overclocked is None
