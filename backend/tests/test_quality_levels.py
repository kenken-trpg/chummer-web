"""Pinned Chummer SelectQuality level semantics, including supplements and nolevels exceptions."""

import pytest

from app.catalog_view import public_catalog
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.engine import compute
from tests.engine_support import _mundane

# Chummer d7e94f6a, Chummer/data/qualities.xml; inventory in docs/quality-levels.md.
LEVELS = {
    "Focused Concentration": 6,
    "High Pain Tolerance": 3,
    "Indomitable (Mental)": 3,
    "Indomitable (Physical)": 3,
    "Indomitable (Social)": 3,
    "Magic Resistance": 4,
    "Will to Live": 3,
    "Gremlins": 4,
    "Aged": 3,
    "Illness": 3,
    "Perceptive": 2,
    "Spike Resistance": 3,
    "Tough as Nails (Physical)": 3,
    "Tough as Nails (Stun)": 3,
    "Dimmer Bulb": 3,
    "In Debt": 15,
    "Infirm": 5,
    "Arcane Arrester": 2,
    "Shiva Arms (Pair)": 2,
    "Hello World!": 3,
    "Pilot Origins": 3,
    "Social Appearance Anxiety": 3,
    "Death Dealer": 3,
    "Flesh Sculpter": 3,
    "Illusionist": 3,
    "Puppet Master": 3,
    "Reckless Spell Master": 6,
    "Skinwalker": 3,
    "Busted Cyberware": 11,
    "Battle Hardened": 3,
    "Thousand-Yard Stare": 3,
    "Down the Rabbit Hole": 4,
    "Special Modifications": 2,
    "Stolen Gear": 20,
}


def test_all_chummer_leveled_qualities_reach_the_catalog() -> None:
    raw = {q["name"]: q["max_takes"] for q in catalog()["qualities"] if q["has_levels"]}
    public = {q["name"]: q["max_takes"] for q in public_catalog()["qualities"] if q["has_levels"]}
    assert raw == LEVELS
    assert public == LEVELS


@pytest.mark.parametrize(
    "name",
    [
        "Restricted Gear",
        "Records on File",
        "Dealer Connection",
        "Close Combat Mage",
        "Distinctive Style",
        "Ambidextrous",
    ],
)
def test_repeatability_and_single_takes_are_not_levels(name: str) -> None:
    assert not next(q for q in catalog()["qualities"] if q["name"] == name)["has_levels"]
    assert not next(q for q in public_catalog()["qualities"] if q["name"] == name)["has_levels"]


def test_three_levels_keep_karma_bonuses_and_chummer_roundtrip() -> None:
    ids = {q["name"]: q["id"] for q in catalog()["qualities"]}
    picked = [ids["Magic Resistance"]] * 3 + [ids["Gremlins"]] * 3
    base = compute(_mundane("level-base"))
    ch = compute(_mundane("levels", quality_ids=picked))
    assert ch.quality_ids == picked
    assert ch.derived["karma"]["spent"] - base.derived["karma"]["spent"] == 6
    assert ch.derived["spell_resistance"] == 3
    assert ch.derived["notoriety"] == 1
    assert all(q["has_levels"] for q in ch.derived["qualities"])
    imported, warnings = chum5_to_state(state_to_chum5(ch))
    assert not warnings
    back = compute(_mundane("level-back", quality_ids=imported["quality_ids"]))
    assert back.quality_ids == picked
    assert back.derived["karma"]["spent"] == ch.derived["karma"]["spent"]
    assert back.derived["spell_resistance"] == 3
    assert back.derived["notoriety"] == 1
