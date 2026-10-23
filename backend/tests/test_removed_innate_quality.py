"""Taking a metatype's `removable="True"` quality off at chargen.

Chummer's CharacterCreate lets the player delete such a grant — a
Shapeshifter's Uneducated, a Wakyambi's Celerity — and leaves a
`MetatypeRemovedAtChargen` row in its place that costs the quality's value the
other way round. The rest of a metatype's grants stay where they are.
"""

import xml.etree.ElementTree as ET

from app.characters import apply_patch
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.engine import compute, default_attributes, find_metatype
from app.models import CharacterPatch, CharacterState, Priorities

VULPINE = "Shapeshifter: Vulpine"


def _character(metatype: str = VULPINE, metavariant: str | None = None, removed: list[str] | None = None):
    return CharacterState(
        id="removed-innate",
        name="Mittens",
        metatype=metatype,
        metavariant=metavariant,
        priorities=Priorities(Heritage="C", Attributes="A", Talent="E", Skills="B", Resources="D"),
        attributes=default_attributes(find_metatype(metatype, metavariant)),
        removed_innate_qualities=removed or [],
    )


def _grant_id(metatype: str, metavariant: str | None, name: str) -> str:
    grants = find_metatype(metatype, metavariant)["quality_grants"]
    return next(g["id"] for g in grants if g["name"] == name)


def _spent_on_qualities(state: CharacterState) -> int:
    rows = state.derived["karma_spend_breakdown"]
    return next((row["amount"] for row in rows if row["notice"]["key"] == "engine.spend.qualities"), 0)


UNEDUCATED = _grant_id(VULPINE, "Human", "Uneducated")


def test_a_removable_negative_grant_is_bought_off_for_its_value() -> None:
    kept = compute(_character())
    gone = compute(_character(removed=[UNEDUCATED]))
    assert "Uneducated" in {q["name"] for q in kept.derived["qualities"]}
    assert "Uneducated" not in {q["name"] for q in gone.derived["qualities"]}
    assert gone.derived["removed_innate_qualities"] == [
        {"id": UNEDUCATED, "name": "Uneducated", "category": "Negative", "karma": 8, "origin_name": "Human"}
    ]
    assert _spent_on_qualities(gone) == _spent_on_qualities(kept) + 8
    # its bonus goes with it: Uneducated is a point of Notoriety
    assert gone.derived["notoriety_quality"] == kept.derived["notoriety_quality"] - 1


def test_a_removable_positive_grant_gives_its_value_back() -> None:
    celerity = _grant_id("Elf", "Wakyambi", "Celerity")
    kept = compute(_character("Elf", "Wakyambi"))
    gone = compute(_character("Elf", "Wakyambi", removed=[celerity]))
    assert gone.derived["removed_innate_qualities"][0]["karma"] == -6
    assert _spent_on_qualities(gone) == _spent_on_qualities(kept) - 6


def test_only_a_removable_grant_of_this_metatype_can_go() -> None:
    fixed = _grant_id(VULPINE, "Human", "Low-Light Vision")
    out = compute(_character(removed=[fixed, "not-a-quality"]))
    assert "Low-Light Vision" in {q["name"] for q in out.derived["qualities"]}
    assert out.removed_innate_qualities == []
    assert out.derived["removed_innate_qualities"] == []


def test_a_new_metatype_brings_its_grants_back() -> None:
    state = compute(_character(removed=[UNEDUCATED]))
    switched = apply_patch(state, CharacterPatch(metavariant="Elf"))
    assert switched.removed_innate_qualities == []
    assert "Uneducated" in {q["name"] for q in switched.derived["qualities"]}


def test_the_removal_survives_a_chum5_round_trip() -> None:
    state = compute(_character(removed=[UNEDUCATED]))
    root = ET.fromstring(state_to_chum5(state))
    rows = [q for q in root.findall("./qualities/quality") if q.findtext("name") == "Uneducated"]
    assert len(rows) == 1
    row = rows[0]
    # the replacement CharacterCreate leaves: turned around and kept off the sheet
    assert row.findtext("qualitysource") == "MetatypeRemovedAtChargen"
    assert row.findtext("qualitytype") == "Positive"
    assert row.findtext("bp") == "8"
    assert row.findtext("contributetolimit") == "False"
    assert row.findtext("print") == "False"
    assert row.find("bonus") is None
    again, _ = chum5_to_state(state_to_chum5(state))
    assert again["removed_innate_qualities"] == [UNEDUCATED]
    assert UNEDUCATED not in again["quality_ids"]
