"""A shapeshifter in creation, as Chummer's `Character.Create` builds one.

The metatype is the animal and the metavariant the metahuman form it takes.
Chummer reads the attributes from the metatype and everything else (karma,
qualities, powers, bonus) from the metavariant, and picks Human when no
metavariant was chosen.
"""

import xml.etree.ElementTree as ET

import pytest

from app.catalog_view import public_catalog
from app.characters import apply_patch
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.engine import compute, default_attributes, find_metatype
from app.models import CharacterPatch, CharacterState, Priorities
from tests.notice_asserts import has

VULPINE = "Shapeshifter: Vulpine"
ANIMALS = {
    "Bovine",
    "Canine",
    "Equine",
    "Falconine",
    "Leonine",
    "Lupine",
    "Pantherine",
    "Phocine",
    "Tigrine",
    "Ursine",
    "Vulpine",
}


def _vulpine(method: str = "Priority", **kwargs: object) -> CharacterState:
    return CharacterState(
        id="shapeshifter",
        name="Mittens",
        metatype=VULPINE,
        build_method=method,
        priorities=Priorities(Heritage="C", Attributes="A", Talent="E", Skills="B", Resources="D"),
        attributes=default_attributes(find_metatype(VULPINE, None)),
        **kwargs,  # type: ignore[arg-type]
    )


def test_a_form_keeps_the_animal_attributes_and_its_own_grants() -> None:
    animal = find_metatype(VULPINE, None)
    human = find_metatype(VULPINE, "Human")
    assert human["attributes"] == animal["attributes"]
    # Vulpine, not the Human form's 1-6: what `Mittens Chargen` saved.
    assert (human["attributes"]["AGI"]["min"], human["attributes"]["AGI"]["max"]) == (2, 7)
    assert (human["attributes"]["BOD"]["min"], human["attributes"]["BOD"]["max"]) == (1, 4)
    assert [p["name"] for p in human["powers"]] == ["Shift (Metahuman Form)"]
    assert not animal["powers"]


def test_a_metavariant_outside_a_shapeshifter_is_unchanged() -> None:
    nocturna = find_metatype("Elf", "Nocturna")
    assert nocturna["attributes"] != find_metatype("Elf", None)["attributes"]


@pytest.mark.parametrize(("method", "cost"), [("Priority", 5), ("SumToTen", 5), ("Karma", 100)])
def test_no_form_chosen_is_the_human_form(method: str, cost: int) -> None:
    out = compute(_vulpine(method))
    assert out.metavariant == "Human"
    assert not has(out.derived["warnings"], "engine.meta.invalidVariant")
    breakdown = {row["notice"]["key"]: row["amount"] for row in out.derived["karma_spend_breakdown"]}
    assert breakdown["engine.spend.metatype"] == cost
    assert {"MAG", "critter"} <= set(out.derived["enabled_tabs"])
    assert out.derived["totals"]["MAG"] >= 1
    grants = {q["name"]: q for q in out.derived["qualities"] if q.get("origin") == "Metatype"}
    assert set(grants) == {
        "Broadened Auditory System (Ultrasound)",
        "Keen-Eared",
        "Low-Light Vision",
        "Vomeronasal Organ",
        "Uneducated",
    }
    assert grants["Uneducated"]["removable"] is True
    assert all(q["free"] and q["karma"] == 0 for q in grants.values())
    bite = [w for w in out.derived["weapons"] if w.get("natural")]
    assert [(w["name"], w["damage"]) for w in bite] == [("Bite (Vulpine Form)", "2P")]


def test_attributes_are_checked_against_the_animal_range() -> None:
    state = _vulpine()
    state.attributes = {**state.attributes, "AGI": 7, "BOD": 5}
    out = compute(state)
    errors = out.derived["errors"]
    assert not has(errors, "engine.attrs.overMax", attr="AGI")
    assert out.derived["metatype_info"]["attributes"]["BOD"]["max"] == 4


def test_leaving_for_a_metahuman_drops_the_form() -> None:
    out = apply_patch(compute(_vulpine()), CharacterPatch(metatype="Human", metavariant=None))
    assert out.metatype == "Human" and out.metavariant is None
    assert not [q for q in out.derived["qualities"] if q.get("origin") == "Metatype"]
    assert not [w for w in out.derived["weapons"] if w.get("natural")]


def test_the_export_marks_the_removable_grant_as_chummer_does() -> None:
    root = ET.fromstring(state_to_chum5(compute(_vulpine())))
    sources = {q.findtext("name"): q.findtext("qualitysource") for q in root.iter("quality")}
    assert sources["Uneducated"] == "MetatypeRemovable"
    assert sources["Low-Light Vision"] == "Metatype"


def test_a_round_trip_keeps_the_form_and_its_grants_once() -> None:
    first = compute(_vulpine("SumToTen"))
    state, _ = chum5_to_state(state_to_chum5(first))
    back = compute(CharacterState(**state))
    assert (back.metatype, back.metavariant) == (VULPINE, "Human")
    assert back.quality_ids == first.quality_ids
    assert len([q for q in back.derived["qualities"] if q.get("origin") == "Metatype"]) == 5
    assert len([w for w in back.derived["weapons"] if w.get("natural")]) == 1


def test_every_shapeshifter_is_a_creation_candidate() -> None:
    cat = public_catalog()
    offered = {m["name"]: m for m in cat["metatypes"] if m["category"] == "Shapeshifter"}
    assert set(offered) == {f"Shapeshifter: {animal}" for animal in ANIMALS}
    for name, row in offered.items():
        # Phocine is the one from Sail Away, Sweet Sister.
        assert row["source"] == ("SAG" if name.endswith("Phocine") else "RF")
        assert "Human" in {v["name"] for v in row["metavariants"]}
    vulpine = offered[VULPINE]
    assert vulpine["karma"] == 100


def test_the_heritage_rows_offer_them_at_a_b_c_for_five_karma() -> None:
    table = public_catalog()["priority_table"]["Heritage"]
    for letter, cell in table.items():
        rows = [m for m in cell["metatypes"] if m["name"].startswith("Shapeshifter: ")]
        if letter in "ABC":
            assert {m["name"] for m in rows} == {f"Shapeshifter: {animal}" for animal in ANIMALS}
            vulpine = next(m for m in rows if m["name"] == VULPINE)
            assert (vulpine["special"], vulpine["karma"]) == ({"A": 8, "B": 6, "C": 4}[letter], 5)
        else:
            assert rows == []
    # The other metasapients stay out of creation.
    names = {m["name"] for cell in table.values() for m in cell["metatypes"]}
    assert not {"Naga", "Pixie", "Sasquatch"} & names
