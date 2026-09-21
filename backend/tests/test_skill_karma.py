"""Priority / Sum-to-Ten creation: skill levels bought with karma.

The skill side of `test_attribute_karma.py`. Chummer keeps each skill as
`<base>` (skill or knowledge points) plus `<karma>` (levels on top at the
karma price — `Skill.RangeCost`). `skill_karma` / `knowledge_karma` are that
second part: the levels leave the point pool and cost new-rating x 2 (x 1 for
a knowledge skill) each.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from app.characters import apply_patch
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.engine import compute, default_attributes, find_metatype
from app.models import CharacterPatch, CharacterState, Priorities, SettingsState
from tests.notice_asserts import has


def _human(cid: str, **kw: object) -> CharacterState:
    attrs = default_attributes(find_metatype("Human", None))
    attrs.update({"INT": 3, "LOG": 3})
    return CharacterState(
        id=cid,
        name=cid,
        metatype="Human",
        attributes=attrs,
        priorities=Priorities(),
        **{
            "skills": {"Pistols": 5, "Sneaking": 2},
            "knowledge_skills": {"Seattle Gangs": 3},
            "knowledge_categories": {"Seattle Gangs": "Street"},
            **kw,
        },
    )


def test_skill_karma_levels_leave_the_point_pool_and_cost_the_raise_price() -> None:
    plain = compute(_human("sk-plain"))
    split = compute(_human("sk-split", skill_karma={"Pistols": 2}, knowledge_karma={"Seattle Gangs": 1}))
    assert split.derived["points"]["skills"]["used"] == plain.derived["points"]["skills"]["used"] - 2
    assert split.derived["points"]["knowledge"]["used"] == plain.derived["points"]["knowledge"]["used"] - 1
    # Pistols 5: the 4th and 5th levels = 4×2 + 5×2; Seattle Gangs 3: the 3rd = 3×1
    assert split.derived["skill_karma"] == {
        "levels": {"Pistols": 2},
        "knowledge_levels": {"Seattle Gangs": 1},
        "group_levels": {},
        "karma": 18,
        "knowledge_karma": 3,
    }
    assert split.derived["karma"]["spent"] == plain.derived["karma"]["spent"] + 21


def test_levels_are_clamped_to_the_rating_and_dropped_for_unknown_skills() -> None:
    out = compute(_human("sk-clamp", skill_karma={"Sneaking": 9, "Pistols": 0, "Nothing": 2}))
    assert out.skill_karma == {"Sneaking": 2}


def test_levels_under_a_skill_group_stay_with_the_group() -> None:
    """A grouped skill's floor is the group rating: only what sits above it
    was bought on its own, so only that can be karma."""
    out = compute(_human("sk-group", skill_groups={"Stealth": 2}, skills={"Sneaking": 4}, skill_karma={"Sneaking": 3}))
    assert out.skill_karma == {"Sneaking": 2}


def test_a_karma_build_keeps_no_skill_split() -> None:
    out = compute(_human("sk-karma", build_method="Karma", skill_karma={"Pistols": 1}))
    assert out.skill_karma == {}
    assert out.derived["skill_karma"]["karma"] == 0


def test_the_skill_cost_stays_on_the_books_in_career() -> None:
    created = compute(_human("sk-career", skill_karma={"Pistols": 1}))
    career = apply_patch(created, CharacterPatch(career=True))
    assert career.derived["skill_karma"]["karma"] == 10
    assert career.derived["karma"]["spent"] == created.derived["karma"]["spent"]


def test_the_skill_split_round_trips_through_chum5_as_base_and_karma() -> None:
    state = compute(_human("sk-chum5", skill_karma={"Pistols": 2}, knowledge_karma={"Seattle Gangs": 1}))
    root = ET.fromstring(state_to_chum5(state))
    pistols_id = next(row["id"] for row in catalog()["skills"]["skills"] if row["name"] == "Pistols")
    pistols = next(s for s in root.iter("skill") if s.findtext("suid") == pistols_id)
    assert (pistols.findtext("base"), pistols.findtext("karma")) == ("3", "2")
    st, _ = chum5_to_state(ET.tostring(root))
    assert st["skills"]["Pistols"] == 5
    assert st["skill_karma"] == {"Pistols": 2}
    assert st["knowledge_karma"] == {"Seattle Gangs": 1}


def test_a_finished_characters_skill_karma_is_not_read_as_a_creation_split() -> None:
    state = compute(_human("sk-done", skill_karma={"Pistols": 1}))
    root = ET.fromstring(state_to_chum5(state))
    root.find("created").text = "True"  # type: ignore[union-attr]
    st, _ = chum5_to_state(ET.tostring(root))
    assert st["skill_karma"] == {}
    assert st["skills"]["Pistols"] == 5


def test_a_skill_bought_only_with_karma_pays_its_specialization_in_karma() -> None:
    """Chummer's `Skill.ForcedBuyWithKarma`: karma levels and no points of its
    own, so the specialization is 7 karma rather than a skill point. Yeti in
    Chummer's test saves is the case: Computer 1 from karma, with a spec."""
    base = _human("bwk-base", skills={"Computer": 1})
    plain = compute(base).derived
    state = _human(
        "bwk-spec",
        skills={"Computer": 1},
        skill_karma={"Computer": 1},
        skill_specializations={"Computer": "Matrix Perception"},
    )
    out = compute(state).derived
    assert out["points"]["skills"]["used"] == plain["points"]["skills"]["used"] - 1
    assert out["karma"]["spent"] == plain["karma"]["spent"] + 2 + 7


def test_a_settings_file_can_let_that_specialization_take_a_point() -> None:
    state = _human(
        "bwk-allowed",
        skills={"Computer": 1},
        skill_karma={"Computer": 1},
        skill_specializations={"Computer": "Matrix Perception"},
    )
    state.settings = SettingsState(allow_point_buy_specializations_on_karma_skills=True)
    out = compute(state).derived
    assert out["points"]["skills"]["used"] == 1


def test_a_skill_with_points_keeps_paying_its_specialization_in_points() -> None:
    state = _human(
        "points-spec",
        skills={"Computer": 3},
        skill_karma={"Computer": 1},
        skill_specializations={"Computer": "Matrix Perception"},
    )
    out = compute(state).derived
    assert out["points"]["skills"]["used"] == 2 + 1


def test_group_levels_bought_with_karma_leave_the_group_points() -> None:
    """Rez0luti0n2.0 in Chummer's test saves: Acting 1 from karma, no group
    points to spend. The level costs 5 × 1 karma instead."""
    plain = compute(_human("grp-plain", skill_groups={"Acting": 1})).derived
    split = compute(_human("grp-karma", skill_groups={"Acting": 1}, skill_group_karma={"Acting": 1})).derived
    assert split["points"]["skill_groups"]["used"] == plain["points"]["skill_groups"]["used"] - 1
    assert split["skill_karma"]["group_levels"] == {"Acting": 1}
    assert split["karma"]["spent"] == plain["karma"]["spent"] + 5


def test_group_karma_survives_a_chummer_round_trip() -> None:
    state = _human("grp-trip", skill_groups={"Acting": 2}, skill_group_karma={"Acting": 1})
    xml = state_to_chum5(compute(state))
    group = next(g for g in ET.fromstring(xml).iter("group") if g.findtext("name") == "Acting")
    assert (group.findtext("base"), group.findtext("karma")) == ("1", "1")
    back, _ = chum5_to_state(xml)
    assert back["skill_groups"] == {"Acting": 2}
    assert back["skill_group_karma"] == {"Acting": 1}


def test_skill_points_on_a_grouped_skill_need_the_setting() -> None:
    """Chummer's `Skill.BaseUnlocked`: while Stealth holds group points,
    Sneaking may rise above it with karma but not with skill points, unless
    `<usepointsonbrokengroups>` allows it."""
    points = compute(_human("grp-points", skill_groups={"Stealth": 2}, skills={"Sneaking": 3}))
    assert has(points.derived["errors"], "engine.skills.pointsOnGroupedSkill", name="Sneaking", group="Stealth")
    karma = compute(
        _human("grp-karma-ok", skill_groups={"Stealth": 2}, skills={"Sneaking": 3}, skill_karma={"Sneaking": 1})
    )
    assert not has(karma.derived["errors"], "engine.skills.pointsOnGroupedSkill")
    allowed = compute(
        _human(
            "grp-points-ok",
            skill_groups={"Stealth": 2},
            skills={"Sneaking": 3},
            settings=SettingsState(use_points_on_broken_groups=True),
        )
    )
    assert not has(allowed.derived["errors"], "engine.skills.pointsOnGroupedSkill")


def test_a_group_bought_with_karma_leaves_skill_points_free() -> None:
    out = compute(
        _human("grp-karma-group", skill_groups={"Stealth": 1}, skill_group_karma={"Stealth": 1}, skills={"Sneaking": 3})
    )
    assert not has(out.derived["errors"], "engine.skills.pointsOnGroupedSkill")


def test_strict_groups_forbid_any_own_level_at_chargen() -> None:
    strict = SettingsState(strict_skill_groups_in_create_mode=True, use_points_on_broken_groups=True)
    out = compute(
        _human(
            "grp-strict",
            skill_groups={"Stealth": 2},
            skills={"Sneaking": 3},
            skill_karma={"Sneaking": 1},
            settings=strict,
        )
    )
    assert has(out.derived["errors"], "engine.skills.groupedSkillLocked", name="Sneaking", group="Stealth")
    career = apply_patch(
        compute(_human("grp-strict-c", skill_groups={"Stealth": 2}, settings=strict)), CharacterPatch(career=True)
    )
    career = apply_patch(career, CharacterPatch(skills={"Sneaking": 3}))
    assert not has(career.derived["errors"], "engine.skills.groupedSkillLocked")


def test_the_player_can_pay_a_point_skills_specialization_with_karma() -> None:
    """Chummer's `<buywithkarma>` ticked by hand: the skill keeps its points,
    the specialization moves to 7 karma. Bastion in Chummer's test saves."""
    kw: dict[str, object] = {"skills": {"Computer": 3}, "skill_specializations": {"Computer": "Matrix Perception"}}
    points = compute(_human("spec-points", **kw)).derived
    karma = compute(_human("spec-karma", skill_specs_karma=["Computer"], **kw)).derived
    assert karma["points"]["skills"]["used"] == points["points"]["skills"]["used"] - 1
    assert karma["karma"]["spent"] == points["karma"]["spent"] + 7


def test_the_karma_specialization_tick_survives_a_chum5_round_trip() -> None:
    state = _human(
        "spec-karma-rt",
        skills={"Computer": 3},
        skill_specializations={"Computer": "Matrix Perception"},
        skill_specs_karma=["Computer"],
    )
    root = ET.fromstring(state_to_chum5(state))
    assert [el.text for el in root.iter("buywithkarma")].count("True") == 1
    st, _ = chum5_to_state(ET.tostring(root))
    assert st["skill_specs_karma"] == ["Computer"]
