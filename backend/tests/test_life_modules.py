"""Life-module free ratings and persistence, using the pinned Chummer data."""

from __future__ import annotations

import pytest

from app.characters import apply_patch, import_character, new_character
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
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
    assert state.derived["karma"]["spent"] - baseline.derived["karma"]["spent"] == (
        spec["karma"] if allowed else 0
    )


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
    bad = module("Street Urchin")
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
