"""Purchases above life-module free floors, including constrained group buys."""

from __future__ import annotations

from dataclasses import replace

import pytest

from app.engine.life_module_skill_purchases import resolve_life_skill_purchases
from app.engine.life_module_skills import LifeSkillResolution
from app.models.life_modules import LifeModuleSkillPolicy
from app.rules import DEFAULT_RULES, using_rules
from tests.notice_asserts import has


@pytest.fixture
def skills():
    return {
        "skills": [
            {"id": "perception", "name": "Perception", "attribute": "INT", "category": "Physical Active"},
            *[
                {"id": name, "name": name.title(), "skillgroup": "Outdoors", "category": "Physical Active"}
                for name in ["navigation", "tracking", "survival"]
            ],
            {"id": "exotic", "name": "Exotic Weapon", "exotic": True, "category": "Combat Active"},
        ]
    }


def free(**levels):
    return LifeSkillResolution(
        LifeModuleSkillPolicy(), free_active={f"skill:{key}": value for key, value in levels.items()}
    )


def test_individual_purchase_is_above_free_floor(skills):
    grants = free(perception=5)
    inputs = {"skill:perception": 1}
    result = resolve_life_skill_purchases(grants, skills, inputs, {})
    assert not result.errors
    assert result.totals["skill:perception"] == 6
    assert result.karma == 12
    assert inputs == {"skill:perception": 1} and grants.free_active == {"skill:perception": 5}


def test_uniform_group_purchase_and_individual_purchase_overlap_once(skills):
    grants = free(navigation=2, tracking=2, survival=2)
    group_only = resolve_life_skill_purchases(grants, skills, {}, {"Outdoors": 1})
    assert group_only.karma == 15
    assert set(group_only.totals.values()) == {3}
    result = resolve_life_skill_purchases(grants, skills, {"skill:navigation": 2}, {"Outdoors": 1})
    assert result.totals == {"skill:navigation": 4, "skill:tracking": 3, "skill:survival": 3}
    assert (result.group_karma, result.active_karma, result.karma) == (15, 8, 23)


def test_unequal_free_group_cannot_be_bought_at_group_price(skills):
    grants = free(navigation=3, tracking=2, survival=2)
    result = resolve_life_skill_purchases(grants, skills, {}, {"Outdoors": 1})
    assert has(result.errors, "engine.life.groupPurchaseUnequal", group="Outdoors")
    assert result.totals == grants.free_active
    assert result.karma == 0 and not result.group_totals


def test_individual_conversion_preserves_requested_unequal_group_ratings(skills):
    grants = free(navigation=3, tracking=2, survival=2)
    result = resolve_life_skill_purchases(
        grants, skills, {f"skill:{name}": 1 for name in ["navigation", "tracking", "survival"]}, {}
    )
    assert not result.errors
    assert result.totals == {"skill:navigation": 4, "skill:tracking": 3, "skill:survival": 3}
    assert result.karma == 8 + 6 + 6


def test_purchase_over_cap_is_retained_for_repair_and_cannot_create_credit(skills):
    result = resolve_life_skill_purchases(free(perception=7), skills, {"skill:perception": 1}, {})
    assert has(result.errors, "engine.life.purchaseCap", name="Perception", requested=8, cap=7)
    assert result.requested["skill:perception"] == 8
    assert result.totals["skill:perception"] == 7 and result.karma == 0


def test_aptitude_applies_to_purchases_without_changing_grant_floor(skills):
    grants = free(perception=7)
    result = resolve_life_skill_purchases(
        grants, skills, {"skill:perception": 1}, {}, skill_max_bonuses={"skill:perception": 1}
    )
    assert not result.errors and result.totals["skill:perception"] == 8
    assert result.karma == 16
    assert grants.policy.active_cap == 7


def test_group_cannot_buy_past_group_cap(skills):
    result = resolve_life_skill_purchases(free(navigation=7, tracking=7, survival=7), skills, {}, {"Outdoors": 1})
    assert has(result.errors, "engine.life.purchaseCap", name="Outdoors", requested=8, cap=7)
    assert result.karma == 0


def test_new_skill_house_price_is_only_charged_when_no_free_first_level(skills):
    with using_rules(replace(DEFAULT_RULES, karma_new_active_skill=9)):
        new = resolve_life_skill_purchases(free(), skills, {"skill:perception": 1}, {})
        above_free = resolve_life_skill_purchases(free(perception=1), skills, {"skill:perception": 1}, {})
    assert new.karma == 9 and above_free.karma == 4


def test_new_group_house_price_and_category_multiplier(skills):
    with using_rules(replace(DEFAULT_RULES, karma_new_skill_group=13)):
        result = resolve_life_skill_purchases(free(), skills, {}, {"Outdoors": 1})
    assert result.karma == 13
    result = resolve_life_skill_purchases(
        free(perception=5), skills, {"skill:perception": 1}, {}, active_karma_mults={"Physical Active": 50}
    )
    assert result.karma == 6


def test_group_compensation_never_refunds_free_levels(skills):
    grants = free(navigation=3, tracking=2, survival=2)
    with using_rules(replace(DEFAULT_RULES, compensate_skill_group_karma_difference=True)):
        no_buys = resolve_life_skill_purchases(grants, skills, {}, {})
        one_each = resolve_life_skill_purchases(
            grants, skills, {f"skill:{name}": 1 for name in ["navigation", "tracking", "survival"]}, {}
        )
        paid_common_level = resolve_life_skill_purchases(
            grants, skills, {"skill:navigation": 1, "skill:tracking": 2, "skill:survival": 2}, {}
        )
    assert no_buys.karma == 0
    assert one_each.compensation == 0 and one_each.karma == 20
    assert paid_common_level.compensation == 20 - 24
    assert paid_common_level.karma == (8 + 6 + 8 + 6 + 8) - 4


def test_exotic_purchase_above_free_concrete_target(skills):
    grants = LifeSkillResolution(LifeModuleSkillPolicy(), free_active={"exotic:exotic:laser": 2})
    result = resolve_life_skill_purchases(grants, skills, {"exotic:exotic:laser": 1}, {})
    assert not result.errors
    assert result.totals["exotic:exotic:laser"] == 3 and result.karma == 6


@pytest.mark.parametrize("invalid", [-1, True, 1.0, 10**400])
def test_invalid_purchase_counts_are_not_used_in_price_ranges(skills, invalid):
    result = resolve_life_skill_purchases(free(), skills, {"skill:perception": invalid}, {})
    assert has(result.errors, "engine.life.purchaseInvalid")
    assert result.karma == 0


def test_huge_but_bounded_input_has_a_bounded_preview(skills):
    result = resolve_life_skill_purchases(free(), skills, {"skill:perception": 10**12}, {})
    assert result.requested["skill:perception"] == 10**12
    assert result.totals["skill:perception"] == 7
    assert has(result.errors, "engine.life.purchaseCap")


def test_unknown_purchase_ids_and_groups_are_reported(skills):
    result = resolve_life_skill_purchases(free(), skills, {"skill:missing": 1}, {"Missing": 1})
    assert has(result.errors, "engine.life.purchaseInvalid")
    assert result.karma == 0
