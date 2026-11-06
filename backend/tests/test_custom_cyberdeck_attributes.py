"""A Fuchi Cyber-N / Cyber-Ex is bought at 0 in every attribute, and each
attribute on its own, as gear in the deck, up to the deck's rating (KC p.60)."""

import xml.etree.ElementTree as ET

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.engine import compute
from app.models import CharacterState, GearInstall
from tests.engine_support import _human


def _deck_id(name: str) -> str:
    return next(row["id"] for row in catalog()["cyberdecks"] if row["name"] == name)


def _attr_id(name: str, deck: str) -> str:
    return next(
        row["id"]
        for row in catalog()["gear"]
        if row["name"] == f"[Custom Cyberdeck] {name}" and deck in row["required_names"]
    )


def _state(deck: str = "Fuchi Cyber-Ex", rating: int = 4, **attrs: int) -> CharacterState:
    return compute(
        _human(
            "deck",
            cyberdecks=[GearInstall(id="deck", gear_id=_deck_id(deck), rating=rating)],
            gear=[
                GearInstall(id=f"a-{name}", gear_id=_attr_id(name, deck), parent_id="deck", rating=value)
                for name, value in attrs.items()
            ],
        )
    )


def _deck(state: CharacterState) -> dict:
    return next(row for row in state.derived["cyberdecks"] if row["id"] == "deck")


def test_each_attribute_is_bought_on_its_own():
    state = _state(Attack=3, Sleaze=2, **{"Data Processing": 4}, Firewall=1)
    deck = _deck(state)
    assert (deck["attack"], deck["sleaze"], deck["dataprocessing"], deck["firewall"]) == (3, 2, 4, 1)
    parts = {row["name"]: row for row in state.derived["gear"] if row.get("parent_id") == "deck"}
    # KC p.60: Attack and Firewall Rating³ × 500, Sleaze and Data Processing Rating² × 500
    assert parts["[Custom Cyberdeck] Attack"]["nuyen"] == 27 * 500
    assert parts["[Custom Cyberdeck] Sleaze"]["nuyen"] == 4 * 500
    assert parts["[Custom Cyberdeck] Data Processing"]["nuyen"] == 16 * 500
    assert parts["[Custom Cyberdeck] Firewall"]["nuyen"] == 1 * 500
    assert not [w for w in state.derived["warnings"] if "doesNotFit" in str(w)]


def test_no_attribute_goes_above_the_deck():
    state = _state(rating=3, Attack=6)
    part = next(row for row in state.derived["gear"] if row.get("parent_id") == "deck")
    assert part["rating"] == 3
    assert part["rating_max"] == 3
    assert _deck(state)["attack"] == 3


def test_the_cyber_n_takes_its_own_firewall():
    state = _state("Fuchi Cyber-N", rating=2, Firewall=2)
    assert _deck(state)["firewall"] == 2


def test_the_attributes_go_out_in_the_deck_and_come_back():
    state = _state(Attack=3, **{"Data Processing": 4})
    root = ET.fromstring(state_to_chum5(state))
    deck = next(el for el in root.iter("gear") if el.findtext("name") == "Fuchi Cyber-Ex")
    kids = {g.findtext("name"): g.findtext("rating") for g in deck.findall("./children/gear")}
    assert kids["[Custom Cyberdeck] Attack"] == "3"
    assert kids["[Custom Cyberdeck] Data Processing"] == "4"
    again = compute(CharacterState.model_validate(chum5_to_state(ET.tostring(root))[0]))
    row = next(r for r in again.derived["cyberdecks"] if r["name"] == "Fuchi Cyber-Ex")
    assert (row["attack"], row["dataprocessing"]) == (3, 4)
