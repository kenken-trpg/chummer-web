"""Foci, critter powers and metamagics in the Foundry export: the three
sections the system's ItemsParser reads (`gears` with category Foci,
`critterpowers`, `metamagics`) that the export used to leave out."""

from __future__ import annotations

from typing import Any

from app.characters import compute_state
from app.data_loader import catalog
from app.engine import compute
from app.engine.constants import quality_optional_power_extra_key
from app.fvtt_export import state_to_fvtt
from app.models import CharacterState, CritterPowerInstall, FocusInstall, InitiationChoice, Priorities, QiFocusInstall
from tests.test_chummer_report_regressions import _initiate
from tests.test_fvtt_export import _state
from tests.test_quality_natural_weapons import _infected


def _char(state: CharacterState, locale: str = "en") -> dict[str, Any]:
    return state_to_fvtt(state, locale)["characters"]["character"]


def _gid(kind: str, name: str) -> str:
    return next(str(row["id"]) for row in catalog()[kind] if row["name"] == name)


def _foci(char: dict[str, Any]) -> list[dict[str, Any]]:
    return [g for g in char["gears"]["gear"] if g["category_english"] == "Foci"]


def test_a_focus_is_gear_at_its_force() -> None:
    state = _state()
    state.foci = [FocusInstall(id="fx", gear_id=_gid("foci", "Alchemical Focus"), force=2, bonded=False)]
    [focus] = _foci(_char(compute_state(state)))
    assert {k: focus[k] for k in ("guid", "sourceid", "name_english", "rating", "qty", "bonded", "equipped")} == {
        "guid": "fx",
        "sourceid": _gid("foci", "Alchemical Focus"),
        "name_english": "Alchemical Focus",
        "rating": "2",
        "qty": "1",
        "bonded": "False",
        "equipped": "True",
    }
    # the importer files anything not flagged a device, SIN or ammo as equipment
    assert (focus["iscommlink"], focus["issin"], focus["isammo"]) == ("False", "False", "False")
    assert int(focus["owncost"]) > 0 and focus["source"] == "SR5"


def test_a_qi_focus_is_the_qi_focus_holding_its_power() -> None:
    state = CharacterState(
        id="adept",
        name="adept",
        priorities=Priorities(Heritage="D", Attributes="A", Talent="B", Skills="C", Resources="E"),
        metatype="Human",
        attributes={},
        talent="Adept",
        qi_foci=[QiFocusInstall(id="qi", rating=4, power_id=_gid("powers", "Astral Perception"))],
    )
    [focus] = _foci(_char(compute_state(state)))
    assert (focus["name_english"], focus["fullname_english"], focus["rating"]) == (
        "Qi Focus",
        "Qi Focus (Astral Perception)",
        "4",
    )
    assert focus["sourceid"] == catalog()["qi_focus"]["id"]


def test_a_vampire_carries_its_powers_with_the_fields_the_importer_reads() -> None:
    char = _char(_infected("Infected: Vampire (Non-Human)"))
    powers = {p["fullname_english"]: p for p in char["critterpowers"]["critterpower"]}
    assert "Essence Drain" in powers and "Infection" in powers
    drain = powers["Essence Drain"]
    assert (drain["type_english"], drain["range_english"], drain["duration_english"]) == ("P", "Touch", "P")
    # a pick is not a rating: `extra_english` is parsed as one
    immunity = powers["Immunity (Age)"]
    assert (immunity["name_english"], immunity["extra"], immunity["extra_english"]) == ("Immunity", "Age", None)


def test_the_optional_power_picked_goes_too() -> None:
    state = _infected("Infected: Vampire (Non-Human)")
    qid = state.quality_ids[0]
    state.quality_extras = {quality_optional_power_extra_key(qid): "Enhanced Senses (Smell)"}
    names = [p["fullname_english"] for p in _char(compute_state(state))["critterpowers"]["critterpower"]]
    assert "Enhanced Senses (Smell)" in names
    assert "Enhanced Senses (Hearing)" not in names


def test_a_bought_power_keeps_its_karma_and_guid() -> None:
    stock = {str(p["name"]): p for p in catalog()["buyable_critter_powers"]}
    state = _infected("Infected: Ghoul (Dwarf)")
    state.critter_powers = [CritterPowerInstall(id="cp1", power_id=stock["Tunneling Claws"]["id"])]
    bought = [p for p in _char(compute(state))["critterpowers"]["critterpower"] if p["guid"] == "cp1"]
    assert [(p["name_english"], p["sourceid"], int(p["karma"]) > 0) for p in bought] == [
        ("Tunneling Claws", stock["Tunneling Claws"]["id"], True)
    ]


def test_durations_are_the_letters_the_importer_keys_off() -> None:
    char = _char(_infected("Infected: Vampire (Non-Human)"))
    durations = {p["duration_english"] for p in char["critterpowers"]["critterpower"]}
    assert not durations & {"Instant", "Sustained", "Permanent"}


def test_power_names_are_translated_for_display_only() -> None:
    [drain] = [
        p
        for p in _char(_infected("Infected: Vampire (Non-Human)"), "ja")["critterpowers"]["critterpower"]
        if p["name_english"] == "Essence Drain"
    ]
    assert drain["name"] != "Essence Drain" and drain["type_english"] == "P"


def test_a_metamagic_carries_its_grade_and_kind() -> None:
    pid = _gid("metamagics", "Masking")
    char = _char(compute(_initiate("Magician", "art-gates", [InitiationChoice(grade=1, option_id=pid)])))
    [masking] = char["metamagics"]["metamagic"]
    assert {k: masking[k] for k in ("sourceid", "name_english", "grade", "improvementsource")} == {
        "sourceid": pid,
        "name_english": "Masking",
        "grade": "1",
        "improvementsource": "Metamagic",
    }


def test_nothing_to_write_writes_empty_lists() -> None:
    char = _char(_state())
    assert char["critterpowers"] == {"critterpower": []}
    assert char["metamagics"] == {"metamagic": []}
    assert _foci(char) == []
