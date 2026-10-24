"""Chummer 5.226.177 (Nightly, the vendored commit) against the critter
powers a quality grants — files written by the desktop app, kept in
docs/fixtures/critter-powers (see its README)."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.engine import compute
from app.models import CharacterState, Priorities

FIXTURES = Path(__file__).resolve().parents[2] / "docs" / "fixtures" / "critter-powers"


def _qid(name: str) -> str:
    return next(q["id"] for q in catalog()["qualities"] if q["name"] == name)


def _read(name: str) -> tuple[list[str], dict[str, str], int]:
    raw, _ = chum5_to_state((FIXTURES / name).read_bytes())
    names = {q["id"]: q["name"] for q in catalog()["qualities"]}
    armor = compute(CharacterState(**raw)).derived["armor"]
    return [names[q] for q in raw["quality_ids"]], raw["quality_extras"], armor


def _power_improvements(root: ET.Element) -> list[tuple[str, str, str, str, str]]:
    """(power, type, improved name, target, value) for every improvement a
    power's bonus made — guids differ between files, the power's name does not."""
    powers = {p.findtext("guid"): p.findtext("name") or "" for p in root.findall("./critterpowers/critterpower")}
    return sorted(
        (
            powers.get(imp.findtext("sourcename"), "?"),
            imp.findtext("improvementttype") or "",
            imp.findtext("improvedname") or "",
            imp.findtext("target") or "",
            imp.findtext("val") or "0",
        )
        for imp in root.findall("./improvements/improvement")
        if imp.findtext("improvementsource") == "CritterPower"
    )


def test_a_drakes_powers_leave_the_improvements_chummer_itself_writes() -> None:
    """Chummer never runs a bonus on load, so these are what make Hardened
    Armor count there at all — written as the desktop app wrote them."""
    qid = _qid("Dracoform (Western Drake)")
    state = CharacterState(
        id="d", name="d", priorities=Priorities(), metatype="Human", attributes={}, quality_ids=[qid]
    )
    ours = _power_improvements(ET.fromstring(state_to_chum5(state)))
    theirs = _power_improvements(ET.parse(FIXTURES / "chummer-western-drake.chum5").getroot())
    assert ours == theirs
    assert ("Hardened Armor", "Armor", "", "", "2") in ours


def test_a_rated_power_carries_its_rating_as_the_extra_too() -> None:
    qid = _qid("Dracoform (Western Drake)")
    state = CharacterState(
        id="d", name="d", priorities=Priorities(), metatype="Human", attributes={}, quality_ids=[qid]
    )
    ours = {p.findtext("name"): p.findtext("extra") for p in ET.fromstring(state_to_chum5(state)).iter("critterpower")}
    theirs = {
        p.findtext("name"): p.findtext("extra")
        for p in ET.parse(FIXTURES / "chummer-western-drake.chum5").getroot().iter("critterpower")
    }
    assert ours == theirs


@pytest.mark.parametrize(
    "name",
    ["chummer-western-drake.chum5", "RT-WesternDrake-resave.chum5", "RT-WesternDrake-reapplied.chum5"],
)
def test_a_drake_reads_back_with_its_armor_whatever_chummer_saved(name: str) -> None:
    """Chummer's resave drops each power's rating (CritterPower.Load never
    reads it) and its Re-apply Improvements doubles the armor; the powers
    come from the quality here, so neither reaches the sheet."""
    qualities, _, armor = _read(name)
    assert qualities == ["Dracoform (Western Drake)"]
    assert armor == 2


def test_an_infecteds_pick_survives_chummers_resave() -> None:
    qualities, extras, _ = _read("RT-Banshee-resave.chum5")
    assert qualities == ["Infected: Banshee"]
    assert extras == {f"{_qid('Infected: Banshee')}:optionalpower": "Immunity (Toxins)"}


@pytest.mark.parametrize("name", ["RT-Banshee-removed.chum5", "RT-WesternDrake-removed.chum5"])
def test_removing_the_quality_in_chummer_takes_its_powers_with_it(name: str) -> None:
    root = ET.parse(FIXTURES / name).getroot()
    assert root.find("./critterpowers/critterpower") is None
    assert not [i for i in root.iter("improvement") if i.findtext("improvementttype") == "CritterPower"]
    qualities, extras, armor = _read(name)
    assert qualities == [] and extras == {} and armor == 0
