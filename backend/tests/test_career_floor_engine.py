"""In career a rating cannot go under the one it had on entering career, from
any writer, not only the editors (`compute/_career.py: hold_career_floors`).

Chummer has no way to lower an attribute or a skill after creation; this app
prices karma from the ratings held, so a lower one gave chargen karma back.
"""

import json

from app.engine import compute, snapshot_career_baseline
from app.models import CharacterState, ExoticSkillInstall
from tests.engine_support import _mundane


def _career(state: CharacterState) -> CharacterState:
    state = compute(state)
    state.career = True
    state.career_baseline = snapshot_career_baseline(state)
    return compute(state)


def _again(state: CharacterState, **change: object) -> CharacterState:
    """The state as a client would send it back, with `change` written over."""
    data = json.loads(state.model_dump_json())
    data.update(change)
    return compute(CharacterState.model_validate(data))


def _left(state: CharacterState) -> int:
    return int(state.derived["karma"]["remaining"])


def _floor_notices(state: CharacterState) -> list[dict]:
    return [w for w in state.derived["warnings"] if "BelowChargen" in str(w.get("key"))]


def _built() -> CharacterState:
    return _career(
        _mundane(
            "floor",
            skills={"Pistols": 4, "Sneaking": 3},
            skill_groups={"Athletics": 2},
            knowledge_skills={"Seattle Gangs": 3},
            exotic_skills=[ExoticSkillInstall(id="ex", skill_name="Exotic Ranged Weapon", extra="Gyrojet", rating=2)],
        )
    )


def test_an_attribute_written_under_its_baseline_is_put_back():
    st = _built()
    left = _left(st)
    floor = st.career_baseline.attributes["AGI"]
    again = _again(st, attributes={**st.attributes, "AGI": floor - 1})
    assert again.attributes["AGI"] == floor
    assert _left(again) == left
    assert [w["key"] for w in _floor_notices(again)] == ["engine.career.attributeBelowChargen"]


def test_skills_groups_and_knowledge_are_held_at_their_baseline():
    st = _built()
    left = _left(st)
    again = _again(
        st,
        skills={**st.skills, "Pistols": 1},
        skill_groups={"Athletics": 0},
        knowledge_skills={},
    )
    assert again.skills["Pistols"] == 4
    assert again.skill_groups["Athletics"] == 2
    # a chargen knowledge skill deleted comes back
    assert again.knowledge_skills["Seattle Gangs"] == 3
    assert _left(again) == left
    assert len(_floor_notices(again)) == 3


def test_an_exotic_skill_row_keeps_its_rating():
    st = _built()
    left = _left(st)
    rows = [{**row.model_dump(), "rating": 0} for row in st.exotic_skills]
    again = _again(st, exotic_skills=rows)
    assert again.exotic_skills[0].rating == 2
    assert _left(again) == left


def test_raising_and_lowering_what_career_bought_is_free_to_undo():
    st = _built()
    left = _left(st)
    raised = _again(st, skills={**st.skills, "Pistols": 5})
    assert _left(raised) < left
    back = _again(raised, skills={**raised.skills, "Pistols": 4})
    assert _left(back) == left
    assert not _floor_notices(back)


def test_nothing_is_held_outside_career():
    st = compute(_mundane("chargen", skills={"Pistols": 4}))
    again = _again(st, skills={"Pistols": 1})
    assert again.skills["Pistols"] == 1
    assert not _floor_notices(again)
