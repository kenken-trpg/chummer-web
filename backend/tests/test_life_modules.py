"""Life-module free ratings and persistence, using the pinned Chummer data."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from app.characters import apply_patch, import_character, new_character
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.data_loader.loaders import life_modules as life_loader
from app.engine import compute
from app.models import CharacterCreate, CharacterPatch
from app.notices import NoticeError
from tests.notice_asserts import has


def module(name: str, stage: str | None = None) -> dict:
    return next(m for m in catalog()["life_modules"] if m["name"] == name and (stage is None or m["stage"] == stage))


def runner():
    return new_character(CharacterCreate(name="History", build_method="LifeModule"))


@pytest.mark.parametrize("metatype,allowed", [("Human", False), ("Ork", True), ("Troll", True)])
def test_module_metatype_requirements_reject_effects_until_matched(metatype, allowed):
    base = runner()
    spec = module("Trog Ganger")
    state = apply_patch(base, CharacterPatch(metatype=metatype, life_modules=[spec["id"]]))
    assert has(state.derived["errors"], "engine.life.requirement") is not allowed
    baseline = apply_patch(base, CharacterPatch(metatype=metatype))
    assert state.derived["karma"]["spent"] - baseline.derived["karma"]["spent"] == (spec["karma"] if allowed else 0)


@pytest.mark.parametrize("talent,allowed", [("Mundane", False), ("Magician", True)])
def test_module_quality_requirements_include_selected_talent(talent, allowed):
    base = runner()
    spec = module("Magical Education (Magician)")
    state = apply_patch(base, CharacterPatch(talent=talent, life_modules=[spec["id"]]))
    assert has(state.derived["errors"], "engine.life.requirement") is not allowed


def test_pool_and_method_do_not_inherit_priority_or_karma_defaults():
    state = runner()
    assert state.build_method == "LifeModule"
    assert state.derived["karma"]["pool"] == 750
    assert state.derived["karma_chargen"]["enabled"]
    assert not has(state.derived["errors"], "engine.priority.oneEach")
    assert has(state.derived["errors"], "engine.life.missingStage", stage="life.stage.Nationality")


def test_grants_are_paid_once_and_remove_without_leaving_ratings():
    base = runner()
    spec = module("Bounty Hunter")
    state = apply_patch(base, CharacterPatch(life_modules=[spec["id"]]))
    assert state.derived["totals"]["BOD"] == 2
    assert state.derived["karma"]["spent"] == 100
    assert state.derived["karma_chargen"]["skills"] == 0
    assert state.attributes == base.attributes
    assert state.skills == base.skills
    assert compute(state).model_dump() == state.model_dump()
    assert import_character(state.model_dump()).derived == state.derived
    removed = apply_patch(state, CharacterPatch(life_modules=[]))
    assert removed.derived == base.derived


def test_purchased_attribute_is_priced_above_the_free_module_rating():
    base = runner()
    state = apply_patch(
        base, CharacterPatch(life_modules=[module("Bounty Hunter")["id"]], attributes={**base.attributes, "BOD": 2})
    )
    assert state.derived["totals"]["BOD"] == 3
    assert state.derived["karma_chargen"]["attributes"] == 15
    assert state.derived["karma"]["spent"] == 115
    assert state.attributes["BOD"] == 2


def test_repeated_adult_modules_stack_without_double_charging_skills():
    mid = module("Bounty Hunter")["id"]
    state = apply_patch(runner(), CharacterPatch(life_modules=[mid, mid]))
    assert state.derived["totals"]["BOD"] == 3
    assert state.derived["karma"]["spent"] == 200
    assert state.derived["karma_chargen"]["skills"] == 0


def test_choice_and_native_language_are_derived_and_not_added_to_purchases():
    spec = module("SINless")
    picks = {
        f"0:{choice['key']}": choice["options"][0] if choice["options"] else "Seattle" for choice in spec["choices"]
    }
    state = apply_patch(runner(), CharacterPatch(life_modules=[spec["id"]], life_module_choices=picks))
    assert not has(state.derived["errors"], "engine.life.choice")
    assert not state.native_languages
    assert any(row["name"] == "English" and row["native"] for row in state.derived["knowledge_skills"])
    assert state.derived["karma"]["spent"] == 15
    assert state.knowledge_skills == {}


def test_missing_or_invalid_choices_are_reported_and_not_applied():
    spec = module("SINless")
    state = apply_patch(runner(), CharacterPatch(life_modules=[spec["id"]], life_module_choices={"0:4": "invalid"}))
    assert has(state.derived["errors"], "engine.life.choice")
    assert not any(row["name"] == "invalid" for row in state.derived["knowledge_skills"])


def test_unknown_and_unsupported_modules_never_grant_partial_benefits():
    bad = module("Pit Fighter")
    state = apply_patch(runner(), CharacterPatch(life_modules=["unknown", bad["id"]]))
    assert has(state.derived["errors"], "engine.life.unknown")
    assert has(state.derived["errors"], "engine.life.unsupported")
    assert state.derived["karma"]["spent"] == 0
    assert state.derived["totals"]["BOD"] == 1


def test_childhood_cannot_repeat():
    spec = module("Corp Drone")
    picks = {f"0:{c['key']}": c["options"][0] if c["options"] else "Seattle" for c in spec["choices"]}
    state = apply_patch(runner(), CharacterPatch(life_modules=[spec["id"], spec["id"]], life_module_choices=picks))
    assert has(state.derived["errors"], "engine.life.duplicateStage", stage="life.stage.Formative Years")
    assert state.derived["karma"]["spent"] == 40


def test_disabled_modules_are_still_listed_for_visibility():
    rows = catalog()["life_modules"]
    assert {row["stage"] for row in rows} == {
        "Nationality",
        "Formative Years",
        "Teen Years",
        "Further Education",
        "Real Life",
    }
    assert any(row["unsupported"] for row in rows)
    assert any(not row["unsupported"] for row in rows)


def test_chum5_does_not_silently_drop_the_history():
    with pytest.raises(NoticeError, match="engine.life.chum5Unsupported"):
        state_to_chum5(runner())
    with pytest.raises(NoticeError, match="engine.life.chum5Unsupported"):
        chum5_to_state(b"<character><buildmethod>LifeModule</buildmethod></character>")


def test_knowledge_purchases_are_priced_above_module_grants():
    base = runner()
    state = apply_patch(
        base,
        CharacterPatch(
            life_modules=[module("Bounty Hunter")["id"]],
            knowledge_skills={"Crook Hangouts": 1},
            settings={"knowledge_points_expression": "0"},
        ),
    )
    assert state.derived["karma_chargen"]["knowledge"] == 4


def test_custom_pool_is_honored():
    state = apply_patch(runner(), CharacterPatch(settings={"karma_chargen_pool": 900}))
    assert state.derived["karma"]["pool"] == 900


def test_excess_free_ratings_are_explicitly_rejected():
    state = apply_patch(runner(), CharacterPatch(life_modules=[module("Bounty Hunter")["id"]] * 7))
    assert has(state.derived["errors"], "engine.life.ratingCap", name="BOD", rating=8, cap=6)


@pytest.mark.parametrize(
    "name,level",
    [
        ("Fugitive", 2),
        ("Gang Warfare", 2),
        ("Ganger", 2),
        ("Organized Crime", 2),
        ("Political Activist", 2),
        ("Terrorist", 2),
        ("Framed", 2),
        ("Corp Silver Spooner", 3),
    ],
)
def test_nested_quality_levels_unlock_modules_and_apply_the_quality(name, level):
    spec = module(name)
    assert not spec["unsupported"]
    assert spec["quality_levels"] == [{"group": "SINner", "level": level}]
    state = apply_patch(runner(), CharacterPatch(life_modules=[spec["id"]]))
    expected = catalog()["quality_levels"]["SINner"][level]
    assert [q["name"] for q in state.derived["qualities"] if q["name"].startswith("SINner")] == [expected]
    assert state.quality_ids == []
    assert compute(state).model_dump() == state.model_dump()
    restored = import_character(state.model_dump())

    # Import intentionally creates a new character ID. Generated contact IDs
    # follow that identity, but their contents and all other results agree.
    def without_contact_ids(derived):
        return {**derived, "contacts": [{**contact, "id": None} for contact in derived["contacts"]]}

    assert without_contact_ids(restored.derived) == without_contact_ids(state.derived)
    assert compute(restored).model_dump() == restored.model_dump()
    assert apply_patch(state, CharacterPatch(life_modules=[])).derived == runner().derived


def test_nested_quality_levels_take_highest_and_restore_purchased_quality_on_removal():
    levels = catalog()["quality_levels"]["SINner"]
    purchased = next(q["id"] for q in catalog()["qualities"] if q["name"] == levels[1])
    base = apply_patch(runner(), CharacterPatch(quality_ids=[purchased]))
    low, high = module("Framed")["id"], module("Corp Silver Spooner")["id"]
    state = apply_patch(base, CharacterPatch(life_modules=[low, high]))
    assert [q["name"] for q in state.derived["qualities"] if q["name"].startswith("SINner")] == [levels[3]]
    assert state.quality_ids == [purchased]
    assert import_character(state.model_dump()).derived == state.derived
    downgraded = apply_patch(state, CharacterPatch(life_modules=[low]))
    assert [q["name"] for q in downgraded.derived["qualities"] if q["name"].startswith("SINner")] == [levels[2]]
    assert apply_patch(downgraded, CharacterPatch(life_modules=[])).derived == base.derived


@pytest.mark.parametrize("group,level", [("Unknown", 1), ("SINner", 99)])
def test_unknown_nested_quality_levels_still_block_the_whole_module(monkeypatch, group, level):
    root = ET.fromstring(
        f"<chummer><modules><module><id>nested</id><name>Nested</name><bonus>"
        f'<addqualities><qualitylevel group="{group}">{level}</qualitylevel></addqualities>'
        "</bonus></module></modules></chummer>"
    )
    monkeypatch.setattr(life_loader, "data_root", lambda _: root)
    row = life_loader.load_life_modules()[0]
    assert row["unsupported"] == ["qualitylevel:unknown"]
    assert row["quality_levels"] == []


@pytest.mark.parametrize(
    "spec",
    [r for r in catalog()["life_modules"] if r["quality_choice_grants"] and not r["unsupported"]],
    ids=lambda r: r["id"],
)
def test_quality_extra_modules_preserve_choices_and_remove_grants(spec):
    base = runner()
    if spec["required"]:
        base = apply_patch(base, CharacterPatch(metatype="Ork"))
    picks = {f"0:{c['key']}": c["options"][0] if c["options"] else "Seattle" for c in spec["choices"]}
    state = apply_patch(base, CharacterPatch(life_modules=[spec["id"]], life_module_choices=picks))
    assert not has(state.derived["errors"], "engine.life.choice")
    assert not has(state.derived["errors"], "engine.life.requirement")
    for grant in spec["quality_choice_grants"]:
        quality = next(q for q in state.derived["qualities"] if q["id"] == grant["quality_id"])
        assert quality["extra"] == (grant["value"] or picks[f"0:{grant['choice']}"])
        assert quality["free"]
    assert state.quality_extras == base.quality_extras
    assert state.life_module_choices == picks
    assert compute(state).model_dump() == state.model_dump()
    restored = import_character(state.model_dump())
    assert restored.life_module_choices == picks
    assert restored.derived["qualities"] == state.derived["qualities"]
    assert apply_patch(state, CharacterPatch(life_modules=[], life_module_choices={})).derived == base.derived


def test_missing_and_invalid_quality_choices_are_not_granted():
    spec = module("Decker", "Real Life")
    grant = next(g for g in spec["quality_choice_grants"] if g["quality_id"] == "41cc3e26-ae55-4e28-bd6a-b08866c21424")
    for picked in ("", "not a matrix action"):
        state = apply_patch(
            runner(), CharacterPatch(life_modules=[spec["id"]], life_module_choices={f"0:{grant['choice']}": picked})
        )
        assert has(state.derived["errors"], "engine.life.choice")
        assert not any(q["id"] == grant["quality_id"] for q in state.derived["qualities"])


def test_quality_extra_conflicts_do_not_overwrite_purchased_extras():
    spec = module("Street Urchin")
    grant = spec["quality_choice_grants"][0]
    base = apply_patch(
        runner(), CharacterPatch(quality_ids=[grant["quality_id"]], quality_extras={grant["quality_id"]: "Original"})
    )
    state = apply_patch(
        base, CharacterPatch(life_modules=[spec["id"]], life_module_choices={f"0:{grant['choice']}": "Different"})
    )
    assert has(state.derived["errors"], "engine.life.qualityChoiceConflict")
    assert state.quality_extras == base.quality_extras
    assert next(q for q in state.derived["qualities"] if q["id"] == grant["quality_id"])["extra"] == "Original"


def test_mr_johnson_contacts_are_free_distinct_and_not_persisted_as_purchases():
    spec = module("Mr. Johnson")
    state = apply_patch(runner(), CharacterPatch(life_modules=[spec["id"]], life_module_choices={"0:q0": "Ares"}))
    contacts = state.derived["contacts"]
    assert len(contacts) == len({c["id"] for c in contacts}) == 3
    assert all(c["connection"] == 4 and c["loyalty"] == 3 and c["billable"] == 0 for c in contacts)
    assert state.contacts == []
    assert compute(state).derived["contacts"] == contacts
