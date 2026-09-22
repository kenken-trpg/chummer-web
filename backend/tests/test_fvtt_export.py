"""Foundry VTT shadowrun5e (0.34.5) export: Chummer's JSON export, as the
system's Chummer importer reads it (backend/app/fvtt_export)."""

from __future__ import annotations

import json
from typing import Any

from starlette.testclient import TestClient

from app.characters import compute_state
from app.data_loader import catalog
from app.fvtt_export import state_to_fvtt
from app.main import app
from app.models import CharacterState, CyberwareInstall, Priorities


def _state() -> CharacterState:
    c = catalog()
    trad = next(r["id"] for r in c["traditions"] if r["name"] == "Hermetic")
    wire = next(r["id"] for r in c["cyberware"]["items"] if r["name"] == "Wired Reflexes")
    quals = [r["id"] for r in c["qualities"] if r["name"] in ("Ambidextrous", "Distinctive Style")]
    return compute_state(
        CharacterState(
            id="fvtt",
            name="夜叉",
            priorities=Priorities(Heritage="C", Attributes="B", Talent="A", Skills="D", Resources="E"),
            metatype="Elf",
            talent="Magician",
            tradition_id=trad,
            attributes={"BOD": 3, "AGI": 4, "REA": 3, "STR": 2, "CHA": 5, "INT": 4, "LOG": 4, "WIL": 4, "MAG": 5},
            skills={"Spellcasting": 5, "Pistols": 3},
            skill_groups={"Athletics": 2},
            skill_specializations={"Spellcasting": "Combat"},
            knowledge_skills={"Magical Theory": 3},
            knowledge_categories={"Magical Theory": "Academic"},
            native_languages=["Sperethiel"],
            quality_ids=quals,
            cyberware=[CyberwareInstall(ware_id=wire, rating=1, grade="Standard")],
            appearance="銀髪 & <細身>\n左頬に傷",
            background="元企業の内勤。\n\n今はフリー。",
        )
    )


def _char(state: CharacterState, locale: str = "ja") -> dict[str, Any]:
    out = state_to_fvtt(state, locale)
    # the importer takes the first character of `characters.character`
    assert set(out) == {"?xml", "characters"}
    char = out["characters"]["character"]
    assert isinstance(char, dict)
    return char


def _skill(char: dict[str, Any], english: str) -> dict[str, Any]:
    return next(s for s in char["skills"]["skill"] if s["name_english"] == english)


def test_the_fields_the_importer_dereferences_without_a_guard_are_there() -> None:
    char = _char(_state())
    # `nuyen.replace(...)`, `attributes[1].attribute`, `skills.skill` and
    # `metatype_english.toLowerCase()` throw when missing
    assert isinstance(char["nuyen"], str)
    assert char["attributes"][0] is None
    assert isinstance(char["attributes"][1]["attribute"], list)
    assert isinstance(char["skills"]["skill"], list)
    assert char["metatype_english"] == "Elf"


def test_every_value_is_a_string_or_a_container_the_way_chummer_prints_it() -> None:
    def walk(v: Any) -> None:
        if isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        else:
            assert v is None or isinstance(v, str), v

    walk(state_to_fvtt(_state()))


def test_attributes_carry_the_unaugmented_base_and_the_finished_total() -> None:
    state = _state()
    rows = {a["name_english"]: a for a in _char(state)["attributes"][1]["attribute"]}
    totals = state.derived["totals"]
    # Wired Reflexes 1 lifts REA by one; the importer covers base -> total
    # with an ActiveEffect
    assert int(rows["REA"]["total"]) == totals["REA"] == int(rows["REA"]["base"]) + 1
    # the essence the ware cost comes off MAG in the total only
    assert int(rows["MAG"]["total"]) == totals["MAG"] < int(rows["MAG"]["base"])
    # a mundane special attribute and ESS are not written (no Foundry field)
    assert "RES" not in rows and "ESS" not in rows


def test_initiative_is_written_as_the_parts_the_importer_subtracts_from() -> None:
    state = _state()
    char = _char(state)
    d = state.derived
    assert int(char["initbonus"]) == d["initiative"]["value"] - d["totals"]["REA"] - d["totals"]["INT"]
    assert int(char["initdice"]) == d["initiative"]["dice"] == 2
    assert int(char["astralinitdice"]) == d["astral_initiative"]["dice"]


def test_magic_flags_tradition_and_reputation() -> None:
    state = _state()
    char = _char(state)
    assert (char["magician"], char["adept"], char["technomancer"]) == ("True", "False", "False")
    # the attribute that is not WIL becomes Foundry's drain attribute
    assert char["tradition"]["drainattributes"] == "WIL + LOG"
    assert char["initiationgrade"] is None
    assert char["calculatedstreetcred"] == str(state.derived["street_cred"])
    assert char["calculatednotoriety"] == str(state.derived["notoriety"])


def test_active_skills_are_matched_by_english_name_and_include_the_group_rating() -> None:
    char = _char(_state())
    pistols = _skill(char, "Pistols")
    assert pistols["rating"] == "3"
    assert pistols["knowledge"] == "False"
    assert pistols["name"] == catalog()["translations"]["Pistols"] != "Pistols"
    # a skill rated only through its group prints at the group's rating
    assert _skill(char, "Running")["rating"] == "2"
    spell = _skill(char, "Spellcasting")
    assert spell["skillspecializations"]["skillspecialization"][0]["name_english"] == "Combat"
    # unrated skills stay out: the importer lays the default skill set down first
    assert all(int(s["rating"]) > 0 or s["isnativelanguage"] == "True" for s in char["skills"]["skill"])
    assert char["skills"]["skillgroup"] == [
        {
            "name": catalog()["translations"].get("Athletics", "Athletics"),
            "name_english": "Athletics",
            "rating": "2",
            "isbroken": "False",
        }
    ]


def test_knowledge_and_native_language_skills() -> None:
    char = _char(_state())
    theory = _skill(char, "Magical Theory")
    assert (theory["knowledge"], theory["islanguage"], theory["rating"]) == ("True", "False", "3")
    assert theory["skillcategory_english"] == "Academic"
    native = _skill(char, "Sperethiel")
    assert (native["islanguage"], native["isnativelanguage"]) == ("True", "True")


def test_qualities_carry_the_guid_the_importer_matches_on_first() -> None:
    state = _state()
    rows = {q["name_english"]: q for q in _char(state)["qualities"]["quality"]}
    ambi = next(r for r in catalog()["qualities"] if r["name"] == "Ambidextrous")
    assert rows["Ambidextrous"]["sourceid"] == ambi["id"]
    assert rows["Ambidextrous"]["qualitytype_english"] == "Positive"
    assert rows["Ambidextrous"]["bp"] == str(ambi["karma"])
    assert rows["Distinctive Style"]["qualitytype_english"] == "Negative"


def test_english_locale_keeps_the_data_names() -> None:
    char = _char(_state(), "en")
    assert _skill(char, "Pistols")["name"] == "Pistols"
    assert char["metatype"] == "Elf"


def test_bio_text_is_escaped_html() -> None:
    char = _char(_state())
    assert char["description"] == "<p>銀髪 &amp; &lt;細身&gt;<br/>左頬に傷</p>"
    assert char["background"] == "<p>元企業の内勤。</p><p>今はフリー。</p>"
    assert char["concept"] is None


def test_fvtt_download_route() -> None:
    client = TestClient(app)
    ip = {"cf-connecting-ip": "203.0.113.57"}
    state = client.post("/api/characters/new", json={"name": "夜叉"}, headers=ip).json()
    r = client.post("/api/characters/fvtt", json={"state": state, "locale": "ja"}, headers=ip)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/json")
    assert "filename*=UTF-8''%E5%A4%9C%E5%8F%89.json" in r.headers["content-disposition"]
    body = json.loads(r.content)
    assert body["characters"]["character"]["name"] == "夜叉"
