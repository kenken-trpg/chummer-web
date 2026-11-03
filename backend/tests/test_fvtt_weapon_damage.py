"""Weapon damage for both importers (0.34.5 reads `damage_noammo_english`;
0.36.3 on read `rawdamage`, then `damage_english`), and the Unarmed Attack
Chummer gives every character (a vehicle gets none: see the drone in
`test_fvtt_export`, whose only weapon is its gun)."""

from __future__ import annotations

from typing import Any

from app.characters import compute_state
from app.data_loader import catalog
from app.fvtt_export import state_to_fvtt
from app.models import CharacterState, WeaponInstall
from tests.test_fvtt_export import _state
from tests.test_quality_natural_weapons import _infected


def _weapons(state: CharacterState) -> dict[str, dict[str, Any]]:
    char = state_to_fvtt(state, "en")["characters"]["character"]
    return {w["name_english"]: w for w in char["weapons"]["weapon"]}


def test_every_weapon_carries_its_damage_where_both_importers_look() -> None:
    state = _state()
    gun = next(r["id"] for r in catalog()["weapons"] if r["name"] == "Ares Predator V")
    state.weapons = [WeaponInstall(id="gun", weapon_id=gun)]
    row = _weapons(compute_state(state))["Ares Predator V"]
    assert row["damage_noammo_english"] == row["damage_english"] == "8P"
    # a gun's figure is finished; no formula to take over from it
    assert row["rawdamage"] is None


def test_unarmed_attack_runs_on_strength_and_the_physical_limit() -> None:
    state = _state()  # STR 2
    row = _weapons(state)["Unarmed Attack"]
    assert {k: row[k] for k in ("category_english", "type", "skill", "rawaccuracy", "rawap", "rawreach")} == {
        "category_english": "Unarmed",
        "type": "Melee",
        "skill": "Unarmed Combat",
        "rawaccuracy": "Physical",
        "rawap": "-",
        "rawreach": "0",
    }
    assert (row["rawdamage"], row["damage_english"]) == ("({STR})S", "2S")


def test_unarmed_attack_takes_the_bonuses() -> None:
    state = _state()
    state.derived = {**state.derived, "unarmed_dv": 2, "unarmed_physical": True, "unarmed_ap": -1, "unarmed_reach": 1}
    row = _weapons(state)["Unarmed Attack"]
    assert (row["rawdamage"], row["damage_english"], row["rawap"], row["rawreach"]) == ("({STR}+2)P", "4P", "-1", "1")


def test_a_natural_weapon_runs_on_strength_and_keeps_what_is_added() -> None:
    state = _infected("Infected: Vampire (Non-Human)")  # STR 4
    bite = _weapons(state)["Infected Bite"]
    assert (bite["rawdamage"], bite["damage_english"], bite["rawaccuracy"]) == ("({STR}+1)P", "5P", "Physical")
    # a bonus on the finished figure stays in the formula
    rows = state.derived["weapons"]
    state.derived = {**state.derived, "weapons": [{**rows[0], "damage": "7P"}]}
    assert _weapons(state)["Infected Bite"]["rawdamage"] == "({STR}+3)P"
