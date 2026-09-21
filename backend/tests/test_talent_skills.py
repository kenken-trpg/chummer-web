"""The skills a priority talent hands out at a fixed rating (SR5 p.65)."""

import xml.etree.ElementTree as ET

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.engine import compute, default_attributes, find_metatype
from app.models import CharacterState, Priorities
from tests.engine_support import _techno


def test_technomancer_b_picks_are_raised_to_4_for_no_points() -> None:
    out = compute(_techno("tb", "B", talent_skills=["Compiling", "Hacking"]))
    d = out.derived
    assert d["talent_skills"]["qty"] == 3
    assert d["talent_skills"]["rating"] == 4
    assert d["talent_skills"]["picked"] == ["Compiling", "Hacking"]
    assert out.skills["Compiling"] == 4
    assert out.skills["Hacking"] == 4
    assert d["points"]["skills"]["used"] == 0


def test_points_and_karma_go_on_top_of_the_free_levels() -> None:
    # Yeti's Compiling: 4 free, 1 point, 1 karma level — the karma level is
    # rating 6, so it costs 12 (Chummer's `RangeCost(Base + FreeBase, total)`)
    free_only = compute(_techno("f", "B", talent_skills=["Compiling"]))
    bought = compute(
        _techno("b", "B", talent_skills=["Compiling"], skills={"Compiling": 6}, skill_karma={"Compiling": 1})
    )
    assert bought.derived["points"]["skills"]["used"] == 1
    assert free_only.derived["karma"]["remaining"] - bought.derived["karma"]["remaining"] == 12


def test_picks_the_talent_does_not_offer_are_dropped() -> None:
    out = compute(
        _techno("x", "B", talent_skills=["Pistols", "Compiling", "Compiling", "Hacking", "Software", "Computer"])
    )
    # Pistols is no resonance / Cracking / Electronics skill; a repeat and the
    # fourth pick go too
    assert out.talent_skills == ["Compiling", "Hacking", "Software"]
    assert "Pistols" not in out.skills


def test_an_aspected_magician_picks_a_group() -> None:
    state = CharacterState(
        id="asp",
        name="asp",
        priorities=Priorities(Heritage="C", Attributes="A", Talent="B", Skills="D", Resources="E"),
        metatype="Human",
        talent="Aspected Magician",
        talent_skills=["Sorcery"],
        attributes=default_attributes(find_metatype("Human", None)),
    )
    out = compute(state)
    assert out.derived["talent_skills"]["group"] is True
    assert out.skill_groups["Sorcery"] == 4
    assert out.derived["points"]["skill_groups"]["used"] == 0
    assert out.derived["skill_totals"]["Spellcasting"] == 4


def test_a_karma_build_has_no_free_skills() -> None:
    state = _techno("k", "B", talent_skills=["Compiling"])
    state.build_method = "Karma"
    out = compute(state)
    assert out.derived["talent_skills"]["qty"] == 0
    assert out.talent_skills == []


def test_the_free_levels_go_out_as_heritage_improvements_and_come_back() -> None:
    before = compute(
        _techno("rt", "B", talent_skills=["Compiling"], skills={"Compiling": 6}, skill_karma={"Compiling": 1})
    )
    xml = state_to_chum5(before)
    root = ET.fromstring(xml)
    imps = [
        (i.findtext("improvedname"), i.findtext("val"))
        for i in root.iter("improvement")
        if i.findtext("improvementsource") == "Heritage" and i.findtext("improvementttype") == "SkillBase"
    ]
    assert imps == [("Compiling", "4")]
    assert [e.text for e in root.iter("priorityskill")] == ["Compiling"]
    compiling = next(
        s for s in root.iter("skill") if s.findtext("isknowledge") == "False" and s.findtext("base") == "1"
    )
    assert compiling.findtext("karma") == "1"
    assert len(root.findall("improvements")) <= 1
    state, _ = chum5_to_state(xml)
    after = compute(CharacterState.model_validate({k: v for k, v in state.items() if k != "_warnings"}))
    assert after.talent_skills == ["Compiling"]
    assert after.skills["Compiling"] == 6
    assert after.derived["karma"]["remaining"] == before.derived["karma"]["remaining"]
