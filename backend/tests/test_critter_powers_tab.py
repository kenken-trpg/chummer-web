"""The Critter Powers tab: an Infected's or a drake's powers, bought with karma.

Chummer: a quality opens the tab (`<enabletab>critter`) and names what it
sells (`<limitcritterpowercategory>`); SelectCritterPower lists the powers in
those categories whose requirements are met; CharacterCreate subtracts each
bought power's `<karma>`; CritterPower.Create runs its bonus at the rating.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.engine import compute
from app.engine.critter_powers import resolve_critter_powers
from app.models import CharacterState, CritterPowerInstall
from tests.engine_support import _human, _quality_id

STOCK = {str(p["name"]): p for p in catalog()["buyable_critter_powers"]}


def _bought(*names: str, rating: int | None = None) -> list[CritterPowerInstall]:
    return [CritterPowerInstall(power_id=STOCK[n]["id"], rating=rating) for n in names]


def _infected(quality: str, *powers: str, rating: int | None = None) -> CharacterState:
    return _human("cp", quality_ids=[_quality_id(quality)], critter_powers=_bought(*powers, rating=rating))


def _keys(out: dict, prefix: str) -> list[tuple[str, str]]:
    return [
        (e["key"], e["params"]["name"]["tr"]) for e in out["errors"] + out["warnings"] if e["key"].startswith(prefix)
    ]


def test_the_stock_is_the_categories_a_quality_opens_the_tab_to() -> None:
    assert {p["category"] for p in STOCK.values()} == {"Infected", "Drake"}
    assert len(STOCK) == 58


def test_an_infected_is_offered_its_own_powers_and_pays_their_karma() -> None:
    out = compute(_infected("Infected: Bandersnatch", "Evolved Reflexes")).derived
    assert out["critter_power_categories"] == ["Infected"]
    offered = {p["name"] for p in STOCK.values() if p["id"] in out["critter_power_offer"]}
    assert offered == {"Evolved Reflexes", "Mimicry", "Pounce (Infected)"}  # Mimicry has no requirement
    assert [(r["name"], r["karma"]) for r in out["critter_powers"]] == [("Evolved Reflexes", 12)]
    lines = [(line["notice"]["key"], line["amount"]) for line in out["karma_spend_breakdown"]]
    assert ("engine.spend.critterPowers", 12) in lines


def test_a_bought_power_does_what_its_bonus_says() -> None:
    before = compute(_infected("Infected: Bandersnatch")).derived
    after = compute(_infected("Infected: Bandersnatch", "Evolved Reflexes")).derived
    assert after["initiative"]["dice"] == before["initiative"]["dice"] + 1  # <initiativedice>1


def test_a_power_on_a_granted_power_is_offered() -> None:
    # Calcified Hide needs Fomoraig and the Armor power Fomoraig is granted
    out = compute(_infected("Infected: Fomoraig")).derived
    assert STOCK["Calcified Hide"]["id"] in out["critter_power_offer"]


def test_creation_checks_requirements_and_category_but_career_does_not() -> None:
    out = compute(_infected("Infected: Bandersnatch", "Silence", "Dragonspeech")).derived
    assert ("engine.critterPowers.prereq", "Silence") in _keys(out, "engine.critterPowers")  # a Banshee's
    assert ("engine.critterPowers.category", "Dragonspeech") in _keys(out, "engine.critterPowers")  # a drake's
    state = _infected("Infected: Bandersnatch", "Silence")
    career = resolve_critter_powers(state, {"critter"}, {"Infected"}, {"qualities": set()}, career=True)
    assert not career["errors"]


def test_a_pick_and_a_rating_are_asked_for() -> None:
    out = compute(
        _human("cp", quality_ids=[_quality_id("Dracoform (Western Drake)")], critter_powers=_bought("Animal Control"))
    ).derived
    assert ("engine.critterPowers.pickExtra", "Animal Control") in _keys(out, "engine.critterPowers")
    out = compute(_infected("Infected: Nosferatu", "Mystic Armor (Infected)")).derived
    assert ("engine.critterPowers.pickRating", "Mystic Armor (Infected)") in _keys(out, "engine.critterPowers")


def test_without_the_quality_the_purchases_go() -> None:
    state = _human("cp", critter_powers=_bought("Mimicry"))
    out = compute(state)
    assert out.critter_powers == []
    assert out.derived["critter_powers"] == []


def test_bought_powers_survive_the_round_trip() -> None:
    state = _infected("Infected: Nosferatu", "Mystic Armor (Infected)", rating=3)
    root = ET.fromstring(state_to_chum5(state))
    written = [p for p in root.findall("./critterpowers/critterpower") if p.findtext("grade") == "0"]
    assert [(p.findtext("name"), p.findtext("rating"), p.findtext("karma")) for p in written] == [
        ("Mystic Armor (Infected)", "3", "6")
    ]
    back = CharacterState(**chum5_to_state(state_to_chum5(state))[0])
    assert [(p.power_id, p.rating) for p in back.critter_powers] == [(STOCK["Mystic Armor (Infected)"]["id"], 3)]
    assert compute(back).derived["karma"]["spent"] == compute(state).derived["karma"]["spent"]
