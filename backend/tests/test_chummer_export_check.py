"""The pre-download round-trip check (app/chummer_export/check.py)."""

from __future__ import annotations

from typing import Any

import pytest
from starlette.testclient import TestClient

from app.characters import apply_patch, import_character, new_character
from app.chummer_export import check
from app.data_loader import catalog
from app.main import app
from app.models import CharacterCreate, CharacterPatch, CharacterState, SettingsState
from app.notices import has_key
from tests.notice_asserts import has
from tests.test_chummer_export import _rich_state


def test_a_character_that_survives_the_round_trip_has_nothing_to_report() -> None:
    assert check.roundtrip_differences(_rich_state()) == []


def test_rows_the_importer_drops_are_reported_by_section(monkeypatch: pytest.MonkeyPatch) -> None:
    real = check.chum5_to_state

    def lossy(xml: bytes) -> tuple[dict[str, Any], list[Any]]:
        state, warnings = real(xml)
        state["weapons"] = []
        state["weapon_accessories"] = []
        return state, warnings

    monkeypatch.setattr(check, "chum5_to_state", lossy)
    out = check.roundtrip_differences(_rich_state())
    lost: dict[str, Any] = {}
    for n in out:
        if n["key"] == "engine.export.lost":
            kind: Any = n["params"]["kind"]
            lost[kind["ui"]] = n["params"]["count"]
    assert lost["engine.kind.weapon"] == 1
    assert set(lost) == {"engine.kind.weapon", "engine.kind.weaponAccessory"}, "nothing else is reported"
    assert has_key(out, "engine.export.nuyen"), "the dropped pistol's price comes back as nuyen left"


def test_the_endpoint_returns_the_differences() -> None:
    res = TestClient(app).post("/api/characters/chummer/check", json={"state": _rich_state().model_dump()})
    assert res.status_code == 200
    assert res.json() == {"differences": []}


def test_core_species_career_conversion_is_also_explained() -> None:
    state = new_character(CharacterCreate())
    state = apply_patch(state, CharacterPatch(attributes={**state.attributes, "BOD": 3}))
    state = apply_patch(state, CharacterPatch(career=True))
    state = apply_patch(state, CharacterPatch(attributes={**state.attributes, "BOD": 4}))
    assert check.roundtrip_differences(state) == [
        {"key": "engine.export.chum5CareerBaseline", "params": {"amount": 20}},
        # 日本語環境 opens as Standard, which enables SR5 alone
        {"key": "engine.export.chum5Books", "params": {"lost": "RG, SRCX", "books": "SR5"}},
    ]


def test_actual_balance_loss_is_not_hidden_by_career_conversion(monkeypatch: pytest.MonkeyPatch) -> None:
    state = new_character(CharacterCreate())
    state = apply_patch(state, CharacterPatch(attributes={**state.attributes, "BOD": 3}))
    state = apply_patch(state, CharacterPatch(career=True))
    state = apply_patch(state, CharacterPatch(attributes={**state.attributes, "BOD": 4}))
    real = check.chum5_to_state

    def lossy(xml: bytes) -> tuple[dict[str, Any], list[Any]]:
        raw, warnings = real(xml)
        raw["karma_adjust"] += 1
        return raw, warnings

    monkeypatch.setattr(check, "chum5_to_state", lossy)
    out = check.roundtrip_differences(state)
    assert not has(out, "engine.export.chum5CareerBaseline")
    assert has(out, "engine.export.karma")
    assert has(out, "engine.export.changed", kind="engine.kind.other")


def _built(build_method: str, settings: SettingsState, **fields: Any) -> CharacterState:
    state = new_character(CharacterCreate())
    return apply_patch(state, CharacterPatch(build_method=build_method, settings=settings, **fields))


def test_a_sum_to_ten_prime_runner_is_told_what_chummer_takes() -> None:
    """Chummer ships Prime Runner for Priority only. A Sum-to-Ten Prime Runner
    is exported under Sum-to-Ten, and Chummer holds it to that: on a real
    Chummer (2026-11-04) the save came back with Standard's caps and
    `nuyenbp` cut from 25 to 10, 30,000 nuyen gone."""
    prime = next(p for p in catalog()["settings_presets"] if p["name"] == "Prime Runner")
    settings = SettingsState(
        name="Prime Runner",
        books=["SR5", "RG"],
        quality_karma_limit=35,
        priority_table="Prime Runner",
        priority_karma_nuyen_base=25,
        chargen_avail_max=15,
    )
    assert prime["build_method"] == "Priority"
    out = check.chummer_settings_losses(import_character(_built("SumToTen", settings, karma_nuyen=25).model_dump()))
    params = {n["key"].removeprefix("engine.export."): n["params"] for n in out}
    assert params["chum5SettingsAs"] == {"before": "Prime Runner", "after": "Sum-to-Ten"}
    assert params["chum5QualityCap"] == {"before": 35, "after": 25}
    assert params["chum5AvailMax"] == {"before": 15, "after": 12}
    assert params["chum5NuyenCap"] == {"before": 25, "after": 10}
    assert params["chum5PriorityTable"] == {"before": "Prime Runner", "after": "Standard"}
    assert params["chum5Books"] == {"lost": "RG", "books": "SR5, RF"}
    assert params["chum5Nuyen"]["after"] < params["chum5Nuyen"]["before"]


def test_a_priority_prime_runner_keeps_its_rules() -> None:
    """Built by Priority, Prime Runner opens as itself (MikoPR on a real
    Chummer), so only the books it does not ship with are lost — and with
    the preset's own books, nothing is."""
    prime = next(p for p in catalog()["settings_presets"] if p["name"] == "Prime Runner")
    settings = SettingsState(
        name="Prime Runner",
        books=list(prime["books"]),
        quality_karma_limit=35,
        priority_table="Prime Runner",
        priority_karma_nuyen_base=25,
        chargen_avail_max=15,
    )
    assert check.chummer_settings_losses(import_character(_built("Priority", settings).model_dump())) == []


def test_standard_by_sum_to_ten_is_not_called_a_change_of_rules() -> None:
    """Standard built by Sum-to-Ten opens as the Sum-to-Ten preset, which
    plays the same; only its books are worth a word."""
    stt = next(p for p in catalog()["settings_presets"] if p["name"] == "Sum-to-Ten")
    out = check.chummer_settings_losses(
        import_character(_built("SumToTen", SettingsState(name="Standard", books=list(stt["books"]))).model_dump())
    )
    assert out == []
