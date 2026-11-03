"""Centaur's innate powers reach the Foundry export as critter powers, and the
pre-export check no longer lists them as left out."""

from starlette.testclient import TestClient

from app.fvtt_export import state_to_fvtt
from app.fvtt_export.check import export_omissions
from app.main import app
from tests.test_centaur_data import KICK_SELECT
from tests.test_centaur_grants import _centaur


def test_the_innate_powers_go_out_as_critter_powers() -> None:
    state = _centaur()
    state.derived = {}  # worked out again, as for every other section
    before = state.model_dump_json()
    powers = state_to_fvtt(state, "en")["characters"]["character"]["critterpowers"]["critterpower"]
    assert [(p["name_english"], p["source"], p["page"]) for p in powers] == [
        ("Search", "SR5", "400"),
        ("Natural Weapon", "SR5", "399"),
    ]
    # the kick's text is a pick, not a rating: the importer parses `extra_english` as one
    assert (powers[1]["extra"], powers[1]["extra_english"]) == (KICK_SELECT, None)
    assert state.model_dump_json() == before


def test_the_check_reports_nothing_for_a_centaur() -> None:
    assert export_omissions(_centaur()) == []


def test_fvtt_check_route_and_the_kick_stays_a_weapon() -> None:
    state = _centaur()
    with TestClient(app) as client:
        response = client.post("/api/characters/fvtt/check", json={"state": state.model_dump()})
    assert response.status_code == 200
    assert response.json()["differences"] == []
    char = state_to_fvtt(state, "en")["characters"]["character"]
    assert char["powers"]["power"] == []
    assert sum(row["name_english"] == "Kick (Centaur)" for row in char["weapons"]["weapon"]) == 1
    assert len(char["qualities"]["quality"]) == 4
