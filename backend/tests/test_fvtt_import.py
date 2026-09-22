"""Foundry VTT shadowrun5e actor import (see backend/app/fvtt_import/)."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.characters import import_character
from app.data_loader import catalog
from app.fvtt_import import fvtt_to_state
from app.main import app
from app.notices import NoticeError
from tests.notice_asserts import has


def _id(kind: str, name: str) -> str:
    return next(str(r["id"]) for r in catalog()[kind] if r["name"] == name)


def _item(kind: str, name: str, sourceid: str = "", english: str = "", **system: Any) -> dict[str, Any]:
    flags = {"isFreshImport": True, "sourceid": sourceid, "name": english or name, "category": ""}
    return {"name": name, "type": kind, "system": {"importFlags": flags, **system}}


def _skill(name: str, rating: int, category: str = "active", **skill: Any) -> dict[str, Any]:
    return {
        "name": name,
        "type": "skill",
        "system": {"type": "skill", "skill": {"category": category, "rating": rating, **skill}},
    }


def _actor(**system: Any) -> dict[str, Any]:
    attrs = {
        "body": 3,
        "agility": 5,
        "reaction": 4,
        "strength": 2,
        "charisma": 3,
        "intuition": 4,
        "logic": 3,
        "willpower": 4,
        "edge": 2,
        "magic": 6,
        "resonance": 0,
    }
    return {
        "name": "Kagero",
        "type": "character",
        "system": {
            "metatype": "elf",
            "special": "magic",
            "attributes": {k: {"base": v, "value": v + 1} for k, v in attrs.items()},
            "karma": {"value": 7, "max": 40},
            "nuyen": 1234,
            "magic": {"attribute": "willpower", "initiation": 1},
            "description": {"value": "<p>Runs &amp; hides</p><p>Seattle</p>"},
            **system,
        },
        "items": [
            _skill("Pistols", 4, specializations=[{"name": "Revolvers"}]),
            _skill("Sneaking", 0),
            {"name": "Firearms", "type": "skill", "system": {"type": "group", "group": {"rating": 2}}},
            _skill("English", 0, "language", language={"isNative": True}),
            _skill("Japanese", 3, "language", language={"isNative": False}),
            _skill("Seattle Gangs", 2, "knowledge", knowledgeType="street"),
            # a display name that is not the catalog's: matched on the GUID
            _item("quality", "両利き", _id("qualities", "Ambidextrous")),
            _item("spell", "Manabolt"),
            _item("adept_power", "Improved Ability (skill) (Pistols)", english="Improved Ability (skill)", level=2),
            _item("quality", "Homebrew Quirk"),
        ],
    }


def test_an_actor_comes_back_as_a_karma_career_character_with_its_balance() -> None:
    state, warnings = fvtt_to_state(_actor())
    char = import_character(state)
    assert (char.name, char.metatype, char.build_method, char.career) == ("Kagero", "Elf", "Karma", True)
    # `base`, not the value Foundry works out with its effects on top
    assert state["attributes"]["AGI"] == 5 and state["attributes"]["MAG"] == 6 and "RES" not in state["attributes"]
    assert char.talent == "Mystic Adept" and char.initiate_grade == 1
    assert char.background == "Runs & hides\nSeattle"
    assert char.derived["karma"]["remaining"] == 7
    assert char.derived["nuyen"] == 1234
    assert has(warnings, "engine.import.skippedUnknown", name="Homebrew Quirk")


def test_skills_languages_and_groups() -> None:
    state, _ = fvtt_to_state(_actor())
    assert state["skills"] == {"Pistols": 4}
    assert state["skill_specializations"] == {"Pistols": "Revolvers"}
    assert state["skill_groups"] == {"Firearms": 2}
    assert state["native_languages"] == ["English"]
    assert state["knowledge_skills"] == {"Japanese": 3, "Seattle Gangs": 2}
    assert state["knowledge_categories"] == {"Japanese": "Language", "Seattle Gangs": "Street"}


def test_items_are_matched_on_the_guid_then_the_english_name() -> None:
    state, _ = fvtt_to_state(_actor())
    assert state["quality_ids"] == [_id("qualities", "Ambidextrous")]
    assert [s["spell_id"] for s in state["spells"]] == [_id("spells", "Manabolt")]
    [power] = state["adept_powers"]
    assert (power["power_id"], power["rating"], power["extra"]) == (
        _id("powers", "Improved Ability (skill)"),
        2,
        "Pistols",
    )


def test_something_else_is_refused_with_a_message() -> None:
    with pytest.raises(NoticeError) as caught:
        fvtt_to_state({"name": "x", "type": "vehicle", "system": {}, "items": []})
    assert caught.value.notice["key"] == "api.notAnFvttActor"


def test_the_endpoint_returns_the_character_and_the_warnings() -> None:
    r = TestClient(app).post("/api/characters/import-fvtt", json=_actor(), headers={"cf-connecting-ip": "203.0.113.40"})
    assert r.status_code == 200
    body = r.json()
    assert body["character"]["name"] == "Kagero"
    assert has(body["warnings"], "engine.import.skippedUnknown", name="Homebrew Quirk")
