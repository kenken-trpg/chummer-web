"""Loss of Confidence: a learned exotic target and specialization effects."""

import pytest

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.engine import compute, selectskill_options
from app.models import CharacterState, ExoticSkillInstall
from tests.engine_support import _human, _quality_id
from tests.notice_asserts import has

QUALITY = "c9cd05ad-cd3c-451e-8285-e0fb1d95ebc1"
PICK = f"quality:{QUALITY}:0"
LASERS = "Exotic Ranged Weapon (Lasers)"
FLAME = "Exotic Ranged Weapon (Flamethrowers)"


def test_confidence_applies_only_to_the_selected_exotic_target() -> None:
    out = compute(
        _human(
            "confidence-exotic",
            quality_ids=[QUALITY],
            skill_picks={PICK: LASERS},
            exotic_skills=[
                ExoticSkillInstall(skill_name="Exotic Ranged Weapon", extra="Lasers", rating=4),
                ExoticSkillInstall(skill_name="Exotic Ranged Weapon", extra="Flamethrowers", rating=4),
                ExoticSkillInstall(skill_name="Exotic Melee Weapon", extra="Whip", rating=3),
                ExoticSkillInstall(skill_name="Exotic Melee Weapon", rating=4),
            ],
        )
    )
    slot = out.derived["skill_pick_slots"][0]
    assert slot["options"] == sorted([LASERS, FLAME])
    assert slot["picked"] == LASERS
    assert out.derived["skill_bonus"] == {LASERS: -2}
    assert out.derived["skill_specializations_disabled"] == [LASERS]
    assert not has(out.derived["warnings"], "engine.skills.pickInvalid")


@pytest.mark.parametrize("rating", [3, 4])
def test_exotic_minimum_rating_and_duplicate_handling(rating: int) -> None:
    out = compute(
        _human(
            "confidence-exotic-minimum",
            quality_ids=[QUALITY],
            skill_picks={PICK: LASERS},
            exotic_skills=[
                ExoticSkillInstall(skill_name="Exotic Ranged Weapon", extra="Lasers", rating=rating),
                ExoticSkillInstall(skill_name="Exotic Ranged Weapon", extra="Lasers", rating=6),
            ],
        )
    )
    assert out.derived["skill_totals"][LASERS] == rating
    assert out.derived["skill_pick_slots"][0]["options"] == ([LASERS] if rating == 4 else [])
    assert out.derived["skill_specializations_disabled"] == ([LASERS] if rating == 4 else [])
    assert has(out.derived["warnings"], "engine.skills.pickInvalid") == (rating < 4)


def test_exotic_choices_obey_category_attribute_and_name_filters() -> None:
    skills = catalog()["skills"]
    ratings = {LASERS: 4, FLAME: 3}
    assert selectskill_options({"limittoskill": "Exotic Ranged Weapon", "minimumrating": 4}, skills, ratings) == [
        LASERS
    ]
    assert selectskill_options({"limittoskill": LASERS}, skills, ratings) == [LASERS]
    assert LASERS not in selectskill_options({"limittoattribute": "LOG"}, skills, ratings)
    assert LASERS not in selectskill_options({"excludecategory": "Combat Active"}, skills, ratings)


def test_exotic_aptitude_caps_only_the_selected_weapon() -> None:
    aptitude = _quality_id("Aptitude")
    out = compute(
        _human(
            "aptitude-exotic",
            quality_ids=[aptitude],
            skill_picks={f"quality:{aptitude}:0": LASERS},
            exotic_skills=[
                ExoticSkillInstall(skill_name="Exotic Ranged Weapon", extra="Lasers", rating=7),
                ExoticSkillInstall(skill_name="Exotic Ranged Weapon", extra="Flamethrowers", rating=7),
            ],
        )
    )
    assert out.derived["skill_totals"][LASERS] == 7
    assert out.derived["skill_totals"][FLAME] == 6


def test_specialization_ownership_cost_and_recovery_survive_confidence() -> None:
    plain = compute(
        _human(
            "confidence-spec",
            skills={"Gymnastics": 4, "Pistols": 4},
            skill_specializations={"Gymnastics": "Parkour", "Pistols": "Revolvers"},
        )
    )
    affected = plain.model_copy(deep=True)
    affected.quality_ids = [QUALITY]
    affected.skill_picks = {PICK: "Gymnastics"}
    affected = compute(affected)
    assert affected.skill_specializations == plain.skill_specializations
    assert affected.derived["skill_specializations"] == plain.derived["skill_specializations"]
    assert affected.derived["points"]["skills"] == plain.derived["points"]["skills"]
    assert affected.derived["skill_specializations_disabled"] == ["Gymnastics"]
    affected.skill_picks[PICK] = "Pistols"
    assert compute(affected).derived["skill_specializations_disabled"] == ["Pistols"]
    affected.quality_ids = []
    recovered = compute(affected)
    assert recovered.derived["skill_specializations_disabled"] == []
    assert recovered.skill_specializations == plain.skill_specializations


def test_confidence_and_specializations_survive_a_chummer_roundtrip() -> None:
    original = compute(
        _human(
            "confidence-roundtrip",
            quality_ids=[QUALITY],
            skill_picks={PICK: LASERS},
            skills={"Gymnastics": 4},
            skill_specializations={"Gymnastics": "Parkour"},
            exotic_skills=[ExoticSkillInstall(skill_name="Exotic Ranged Weapon", extra="Lasers", rating=4)],
        )
    )
    imported, _warnings = chum5_to_state(state_to_chum5(original))
    restored = compute(CharacterState(**imported))
    assert restored.skill_picks[PICK] == LASERS
    assert restored.skill_specializations == original.skill_specializations
    assert restored.derived["skill_bonus"][LASERS] == -2
    assert restored.derived["skill_specializations_disabled"] == [LASERS]
