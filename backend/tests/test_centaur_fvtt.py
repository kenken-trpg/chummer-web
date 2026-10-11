"""Centaur's innate powers must not disappear from an external export silently."""

import pytest
from starlette.testclient import TestClient

from app.fvtt_export import state_to_fvtt
from app.fvtt_export.check import export_omissions
from app.main import app
from tests.test_centaur_data import KICK_SELECT
from tests.test_centaur_grants import _centaur


@pytest.mark.parametrize("cache", [{}, {"metatype_info": {"powers": []}}])
def test_missing_or_stale_cache_cannot_hide_omitted_powers(cache: dict) -> None:
    state = _centaur()
    state.derived = cache
    before = state.model_dump_json()
    rows = export_omissions(state)
    assert [row["params"]["name"] for row in rows] == [{"tr": "Search"}, {"tr": "Natural Weapon"}]
    assert all(row["key"] == "engine.export.fvttInnatePower" for row in rows)
    assert rows[0]["params"]["source"] == "SR5"
    assert rows[0]["params"]["page"] == "400"
    assert rows[1]["params"]["page"] == "399"
    assert rows[1]["params"]["selection"] == KICK_SELECT
    assert state.model_dump_json() == before


def test_core_metatype_has_no_innate_power_omission() -> None:
    state = _centaur()
    state.metatype = "Human"
    assert export_omissions(state) == []


def test_fvtt_check_route_reports_powers_while_kick_remains_a_weapon() -> None:
    state = _centaur()
    with TestClient(app) as client:
        response = client.post("/api/characters/fvtt/check", json={"state": state.model_dump()})
    assert response.status_code == 200
    assert response.json()["differences"] == export_omissions(state)
    char = state_to_fvtt(state, "en")["characters"]["character"]
    assert char["powers"]["power"] == []
    assert sum(row["name_english"] == "Kick (Centaur)" for row in char["weapons"]["weapon"]) == 1
    assert len(char["qualities"]["quality"]) == 4
