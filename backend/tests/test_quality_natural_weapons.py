"""A quality's own `<naturalweapons>` — the Infected's bite and claws (RF p.137) —
become weapons, as Chummer's `Quality.Create` runs the node as a bonus."""

from __future__ import annotations

from app.characters import compute_state
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.fvtt_export import state_to_fvtt
from app.models import CharacterState, Priorities


def _infected(quality: str, *, strength: int = 4) -> CharacterState:
    qid = next(r["id"] for r in catalog()["qualities"] if r["name"] == quality)
    return compute_state(
        CharacterState(
            id="infected",
            name="infected",
            priorities=Priorities(Heritage="C", Attributes="B", Talent="A", Skills="D", Resources="E"),
            metatype="Dwarf",
            attributes={"BOD": 3, "AGI": 3, "REA": 3, "STR": strength, "CHA": 3, "INT": 3, "LOG": 3, "WIL": 3},
            quality_ids=[qid],
        )
    )


def _natural(state: CharacterState) -> list[tuple[str, str, str, str]]:
    return [
        (w["name"], w["damage"], str(w["ap"]), str(w["reach"])) for w in state.derived["weapons"] if w.get("natural")
    ]


def test_a_vampire_bites() -> None:
    state = _infected("Infected: Vampire (Non-Human)")
    # ({STR}+1)P, AP -1, reach -1 (RF p.137)
    assert _natural(state) == [("Infected Bite", "5P", "-1", "-1")]
    bite = next(w for w in state.derived["weapons"] if w.get("natural"))
    assert bite["natural_source"] == "Infected: Vampire (Non-Human)"
    assert bite["useskill"] == "Unarmed Combat"


def test_a_ghoul_has_claws_and_a_bite() -> None:
    assert _natural(_infected("Infected: Ghoul (Dwarf)", strength=5)) == [
        ("Infected Claws", "7P", "-1", "0"),
        ("Infected Bite", "6P", "-1", "-1"),
    ]


def test_without_the_quality_there_is_none() -> None:
    state = _infected("Infected: Vampire (Non-Human)")
    state.quality_ids = []
    assert _natural(compute_state(state)) == []


def test_the_fvtt_export_carries_the_bite() -> None:
    char = state_to_fvtt(_infected("Infected: Vampire (Non-Human)"))["characters"]["character"]
    weapons = char["weapons"]["weapon"]
    assert [(w["name_english"], w["category_english"], w["damage_noammo_english"]) for w in weapons] == [
        ("Infected Bite", "Unarmed", "5P"),
        ("Unarmed Attack", "Unarmed", "4S"),
    ]


def test_the_bite_chummer_saved_is_not_imported_twice() -> None:
    """Chummer saves the weapon its improvement made, with no data id behind
    it; the quality brings it back, so the save's copy is not imported."""
    xml = b"""<character><metatype>Dwarf</metatype><buildmethod>Priority</buildmethod>
      <qualities><quality><name>Infected: Vampire (Non-Human)</name>
        <qualitysource>Selected</qualitysource></quality></qualities>
      <weapons><weapon><sourceid>00000000-0000-0000-0000-000000000000</sourceid>
        <name>Infected Bite</name><category>Unarmed</category></weapon></weapons>
    </character>"""
    st, _ = chum5_to_state(xml)
    assert st["weapons"] == []
    assert [name for name, *_ in _natural(compute_state(CharacterState(**st)))] == ["Infected Bite"]
