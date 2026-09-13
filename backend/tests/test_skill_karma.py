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
from app.engine import compute, default_attributes, find_metatype
from app.models import CharacterPatch, CharacterState, Priorities


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
    pistols = next(s for s in root.iter("skill") if s.findtext("name") == "Pistols")
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
