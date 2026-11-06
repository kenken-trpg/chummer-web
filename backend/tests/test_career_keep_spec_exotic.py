"""A specialization or an exotic skill row held on entering career keeps what
chargen charged for it when it is deleted (`compute/_career_items.py`).

Chummer gives no karma back when something is deleted; this app prices karma
from what is held, so without a record a deleted one handed it back. The
editors cannot delete them in career; this is the stop for any other writer.
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
    data = json.loads(state.model_dump_json())
    data.update(change)
    return compute(CharacterState.model_validate(data))


def _left(state: CharacterState) -> int:
    return int(state.derived["karma"]["remaining"])


def _sheet(method: str = "Priority", **extra: object) -> CharacterState:
    state = _mundane(
        "keep",
        skills={"Pistols": 4, "Sneaking": 3},
        skill_specializations={"Pistols": "Semi-Automatics"},
        exotic_skills=[ExoticSkillInstall(id="ex", skill_name="Exotic Ranged Weapon", extra="Gyrojet", rating=2)],
        **extra,
    )
    state.build_method = method
    return state


def test_a_karma_build_keeps_a_deleted_chargen_specialization():
    st = _career(_sheet("Karma"))
    left = _left(st)
    assert _left(_again(st, skill_specializations={})) == left


def test_a_karma_build_keeps_a_deleted_chargen_exotic_row():
    st = _career(_sheet("Karma"))
    left = _left(st)
    assert _left(_again(st, exotic_skills=[])) == left


def test_a_karma_build_still_pays_for_what_career_adds_and_raises():
    st = _career(_sheet("Karma"))
    left = _left(st)
    spec = _again(st, skill_specializations={**st.skill_specializations, "Sneaking": "Urban"})
    assert _left(spec) == left - 7
    # taking back what career bought gives it back, as Chummer's undo does
    assert _left(_again(spec, skill_specializations=st.skill_specializations)) == left
    rows = [{**row.model_dump(), "rating": 3} for row in st.exotic_skills]
    raised = _again(st, exotic_skills=rows)
    assert _left(raised) == left - 6
    # the raise goes with the row, chargen's price stays
    assert _left(_again(raised, exotic_skills=[])) == left


def test_a_priority_specialization_bought_with_karma_stays_paid_in_career():
    sheet = _sheet(skill_specs_karma=["Pistols"])
    chargen = _left(compute(sheet.model_copy(deep=True)))
    st = _career(sheet)
    assert _left(st) == chargen
    assert _left(_again(st, skill_specializations={})) == chargen


def test_a_priority_specialization_bought_with_a_point_costs_no_karma_in_career():
    sheet = _sheet()
    chargen = _left(compute(sheet.model_copy(deep=True)))
    st = _career(sheet)
    assert _left(st) == chargen
    assert _left(_again(st, skill_specializations={})) == chargen
