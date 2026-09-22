"""Foundry VTT shadowrun5e actor import (see backend/app/fvtt_import/)."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.characters import import_character
from app.data_loader import catalog, catalog_list
from app.fvtt_import import _base_name, _paren, fvtt_to_state
from app.main import app
from app.models._common import MAX_INPUT_INT
from app.models.character import MAX_GRADE
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


def _gear(
    kind: str, name: str, rating: int = 1, quantity: int = 1, embedded: Any = (), **system: Any
) -> dict[str, Any]:
    item = _item(kind, name, technology={"rating": rating, "quantity": quantity, "equipped": True}, **system)
    item["flags"] = {"shadowrun5e": {"embeddedItems": list(embedded)}}
    return item


def _geared(**system: Any) -> dict[str, Any]:
    actor = _actor(**system)
    actor["system"]["magic"]["attribute"] = "logic"
    actor["system"].update(street_cred=5, notoriety=2, public_awareness=1)
    actor["items"] += [
        _gear("armor", "Lined Coat", embedded=[_gear("modification", "Chemical Protection", 3, type="armor")]),
        _gear(
            "weapon",
            "Ares Predator V",
            embedded=[
                _gear("modification", "Smartgun System, Internal", type="weapon"),
                _gear("modification", "Silencer/Suppressor", type="weapon", mod_weapon={"mount_point": "barrel"}),
                _gear("ammo", "Regular Ammo"),
            ],
        ),
        _gear("cyberware", "Wired Reflexes", 2, grade="alpha"),
        # Foundry has it as cyberware; the catalog says bioware
        _gear("cyberware", "Muscle Toner", 1),
        _gear("device", "Hermes Ikon", category="commlink"),
        _gear("sin", "Fake SIN", 4),
        _gear("equipment", "Medkit", 3),
        _item("contact", "Fixer Bob", type="Fixer", connection=4, loyalty=3),
        _item("lifestyle", "My Flat", type="low"),
    ]
    return actor


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


def test_armor_weapons_and_ware() -> None:
    state, warnings = fvtt_to_state(_geared())
    [coat] = state["armor"]
    assert coat["armor_id"] == _id("armor", "Lined Coat")
    [mod] = state["armor_mods"]
    assert (mod["mod_id"], mod["parent_id"], mod["rating"]) == (_id("armor_mods", "Chemical Protection"), coat["id"], 3)
    [gun] = state["weapons"]
    # the internal smartgun comes with the gun; the ammo is not an accessory
    [acc] = state["weapon_accessories"]
    assert (acc["accessory_id"], acc["parent_id"], acc["mount"]) == (
        _id("weapon_accessories", "Silencer/Suppressor"),
        gun["id"],
        "Barrel",
    )
    [wired] = state["cyberware"]
    assert (wired["rating"], wired["grade"]) == (2, "Alphaware")
    assert [b["ware_id"] for b in state["bioware"]] == [
        next(str(r["id"]) for r in catalog()["bioware"]["items"] if r["name"] == "Muscle Toner")
    ]
    assert not warnings[1:]  # only the homebrew quality


def test_gear_goes_to_its_bucket() -> None:
    state, _ = fvtt_to_state(_geared())
    assert [c["gear_id"] for c in state["commlinks"]] == [
        next(str(r["id"]) for r in catalog_list("commlinks") if r["name"] == "Hermes Ikon")
    ]
    names = {str(r["id"]): r["name"] for r in catalog_list("gear")}
    assert sorted((names[g["gear_id"]], g["rating"]) for g in state["gear"]) == [("Fake SIN", 4), ("Medkit", 3)]


def test_contacts_lifestyles_tradition_and_reputation() -> None:
    state, _ = fvtt_to_state(_geared())
    [bob] = state["contacts"]
    assert (bob["name"], bob["role"], bob["connection"], bob["loyalty"]) == ("Fixer Bob", "Fixer", 4, 3)
    assert [ls["lifestyle_id"] for ls in state["lifestyles"]] == [_id("lifestyles", "Low")]
    assert state["tradition_id"] == _id("traditions", "Hermetic")
    char = import_character(state)
    assert (char.derived["street_cred"], char.derived["notoriety"], char.derived["public_awareness"]) == (5, 2, 1)
    assert char.derived["nuyen"] == 1234 and char.derived["karma"]["remaining"] == 7


def test_hostile_names_and_descriptions_do_not_stall() -> None:
    # these went polynomial under the regexes they replaced (CodeQL py/polynomial-redos)
    actor = _actor(description={"value": "<p>" + "<" * 50_000})
    actor["items"].append(_item("quality", "(" + " " * 50_000 + "x"))
    fvtt_to_state(actor)


def test_only_the_last_parenthesis_comes_off() -> None:
    assert _paren("Improved Ability (skill) (Pistols) ") == ("Improved Ability (skill)", "Pistols")
    assert _base_name("Ares Predator V") == "Ares Predator V"
    assert _paren("odd (a) b)") is None


def test_a_huge_grade_or_quantity_is_capped_not_walked() -> None:
    # the engine walks every grade; 10**12 would never come back
    actor = _geared(magic={"attribute": "logic", "initiation": 10**12})
    commlink = next(i for i in actor["items"] if i["name"] == "Hermes Ikon")
    commlink["system"]["technology"]["quantity"] = 10**12
    state, _ = fvtt_to_state(actor)
    assert state["initiate_grade"] == MAX_GRADE
    assert state["commlinks"][0]["qty"] == 999
    import_character(state)


def test_a_json_character_with_a_huge_grade_fails_validation() -> None:
    state, _ = fvtt_to_state(_actor())
    state["initiate_grade"] = 10**12
    with pytest.raises(ValidationError):
        import_character(state)


def test_a_number_past_the_input_cap_is_clamped_by_the_read() -> None:
    """A hand-edited actor must still come back as a state that validates.

    The models refuse an int past `MAX_INPUT_INT`, so a base of 10**26 read
    through unchanged would fail validation after the read said it was fine —
    the fuzz contract asks for a state or a `NoticeError`, not either of those.
    """
    actor = _geared()
    actor["system"]["attributes"]["body"]["base"] = "99999999999999999999999999"
    state, _ = fvtt_to_state(actor)
    assert state["attributes"]["BOD"] == MAX_INPUT_INT
    import_character(state)
