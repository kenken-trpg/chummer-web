"""The pre-download round-trip check (app/chummer_export/check.py)."""

from __future__ import annotations

from typing import Any

import pytest
from starlette.testclient import TestClient

from app.characters import apply_patch, new_character
from app.chummer_export import check
from app.main import app
from app.models import CharacterCreate, CharacterPatch
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
        {"key": "engine.export.chum5CareerBaseline", "params": {"amount": 20}}
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
