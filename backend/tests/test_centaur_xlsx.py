"""Template fallback must report free grants without turning them into purchases."""

import pytest
from starlette.testclient import TestClient

from app.characters import import_character, new_character
from app.main import app
from app.models import CharacterCreate, WeaponInstall
from app.xlsx_export import state_to_xlsx
from app.xlsx_export.check import roundtrip_differences
from app.xlsx_import import xlsx_to_state
from tests.notice_asserts import find, has
from tests.test_centaur_data import KICK_SELECT, QUALITY_IDS
from tests.test_centaur_grants import _centaur

KICK_ID = "e4124dde-69f2-4322-884a-620ba7792b82"


@pytest.mark.parametrize("method", ["Priority", "SumToTen", "Karma"])
@pytest.mark.parametrize("cache", [{}, {"qualities": [], "metatype_info": {"powers": []}, "weapons": []}])
def test_xlsx_reports_all_lost_grants_from_inputs_without_mutation(method: str, cache: dict) -> None:
    state = _centaur(build_method=method)
    state.derived = cache
    before = state.model_dump_json()
    rows = roundtrip_differences(state)
    lost = find(rows, "engine.export.xlsxInnateGrant")
    assert [row["params"]["name"]["tr"] for row in lost] == [
        *QUALITY_IDS,
        "Search",
        "Natural Weapon",
        "Kick (Centaur)",
    ]
    assert has(lost, "engine.export.xlsxInnateGrant", name="Search", source="SR5", page="400")
    assert has(
        lost,
        "engine.export.xlsxInnateGrant",
        name="Natural Weapon",
        selection=KICK_SELECT,
        source="SR5",
        page="399",
    )
    assert has(rows, "engine.export.xlsxNoCell", name="Centaur", instead="Human")
    assert state.model_dump_json() == before


@pytest.mark.parametrize("manual_kick", [False, True])
def test_xlsx_does_not_convert_free_kick_to_a_purchased_weapon(manual_kick: bool) -> None:
    state = _centaur()
    if manual_kick:
        state.weapons = [WeaponInstall(weapon_id=KICK_ID)]
    first = import_character(state.model_dump())
    again = import_character(xlsx_to_state(state_to_xlsx(first))[0])
    assert again.metatype == "Human"
    assert again.quality_ids == []
    assert again.derived["qualities"] == []
    assert not again.derived["metatype_info"].get("powers")
    assert [row.weapon_id for row in again.weapons] == ([KICK_ID] if manual_kick else [])
    assert len(again.derived["weapons"]) == int(manual_kick)


@pytest.mark.parametrize("metatype", ["Human", "Elf", "Dwarf", "Ork", "Troll"])
def test_supported_species_regrant_without_false_loss_reports(metatype: str) -> None:
    state = new_character(CharacterCreate(metatype=metatype))
    assert not find(roundtrip_differences(state), "engine.export.xlsxInnateGrant")


def test_xlsx_check_route_reports_innate_losses() -> None:
    state = _centaur()
    with TestClient(app) as client:
        response = client.post("/api/characters/xlsx/check", json={"state": state.model_dump()})
    assert response.status_code == 200
    assert len(find(response.json()["differences"], "engine.export.xlsxInnateGrant")) == 7
