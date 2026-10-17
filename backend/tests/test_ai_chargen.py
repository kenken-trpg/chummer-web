"""An A.I. in creation (DT p.135), as the pinned Chummer source builds one.

No test save of Chummer's has an A.I. player character, so each rule here is
pinned against the source instead (`docs/ai-chargen.md`):
SelectMetatypePriority halves the attribute points and starts Depth at the
talent's `<depth>`, `Character.IsAI` caps Edge at Depth, the talents'
`<forbidden>` / `<required>` keep the A.I. and everyone else apart, and
SelectQuality offers an A.I. only its `<qualityrestriction>`.
"""

import xml.etree.ElementTree as ET

import pytest

from app.catalog_view import public_catalog
from app.characters import apply_patch
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.engine import compute, default_attributes, find_metatype, talent_allowed, talent_options
from app.models import CharacterPatch, CharacterState, Priorities
from tests.notice_asserts import has

AI = "A.I."
VARIANTS = ("E-Ghost", "Xenosapient", "Protosapient")


def _ai(
    metavariant: str | None = None,
    method: str = "Priority",
    *,
    attributes: str = "B",
    talent_letter: str = "C",
    **kwargs: object,
) -> CharacterState:
    # Heritage A or C (B is the A.I.'s too); the letters left go to the rest.
    heritage = "C" if "A" in {attributes, talent_letter} else "A"
    rest = [letter for letter in "ABCDE" if letter not in {heritage, attributes, talent_letter}]
    kwargs.setdefault("talent", AI)
    return CharacterState(
        id="ai",
        name="Ghost",
        metatype=AI,
        metavariant=metavariant,
        build_method=method,
        priorities=Priorities(
            Heritage=heritage, Attributes=attributes, Talent=talent_letter, Skills=rest[0], Resources=rest[1]
        ),
        attributes=default_attributes(find_metatype(AI, metavariant)),
        **kwargs,  # type: ignore[arg-type]
    )


def _human(**kwargs: object) -> CharacterState:
    return CharacterState(
        id="human",
        name="Joe",
        metatype="Human",
        priorities=Priorities(Heritage="E", Attributes="B", Talent="C", Skills="A", Resources="D"),
        attributes=default_attributes(find_metatype("Human", None)),
        **kwargs,  # type: ignore[arg-type]
    )


def _quality_id(name: str) -> str:
    from app.data_loader import catalog

    return next(q["id"] for q in catalog()["qualities"] if q["name"] == name)


# --- the data -----------------------------------------------------------------


@pytest.mark.parametrize("metavariant", [None, *VARIANTS])
def test_an_ai_has_depth_and_no_body(metavariant: str | None) -> None:
    meta = find_metatype(AI, metavariant)
    attrs = meta["attributes"]
    assert (attrs["DEP"]["min"], attrs["DEP"]["max"]) == (1, 6)
    for key in ("BOD", "AGI", "REA", "STR"):
        assert (attrs[key]["min"], attrs[key]["max"]) == (0, 0)
    assert meta["halve_attribute_points"] is True
    restriction = meta["quality_restriction"]
    assert len(restriction["Positive"]) == 63
    assert len(restriction["Negative"]) == 43


def test_a_metavariant_keeps_its_own_ranges() -> None:
    # Unlike a shapeshifter's, an A.I.'s metavariant is a different mind.
    assert find_metatype(AI, "Xenosapient")["attributes"]["LOG"]["max"] == 8
    assert find_metatype(AI, None)["attributes"]["LOG"]["max"] == 7


def test_a_metahuman_has_no_depth_and_no_restriction() -> None:
    human = find_metatype("Human", None)
    assert human["attributes"]["DEP"] == {"min": 0, "max": 0, "aug": 0}
    assert human["halve_attribute_points"] is False
    assert human["quality_restriction"] is None


# --- the talent ---------------------------------------------------------------


@pytest.mark.parametrize(("letter", "depth"), [("A", 6), ("B", 4), ("C", 3), ("D", 2), ("E", 1)])
def test_every_talent_row_offers_the_ai_its_depth(letter: str, depth: int) -> None:
    talent = next(t for t in talent_options(letter) if t["name"] == AI)
    assert talent["depth"] == depth
    assert talent_allowed(talent, AI)
    assert not talent_allowed(talent, "Human")
    # An A.I. may take nothing else, not even Mundane.
    others = [t for t in talent_options(letter) if t["name"] != AI]
    assert others
    assert not any(talent_allowed(t, AI) for t in others)


def test_a_technomancer_must_be_a_metahuman() -> None:
    techno = next(t for t in talent_options("A") if t["name"] == "Technomancer")
    assert talent_allowed(techno, "Human")
    # The base metatype's category: a Nocturna is a Metahuman Elf.
    assert talent_allowed(techno, "Elf")
    assert not talent_allowed(techno, "Centaur")
    assert not talent_allowed(techno, "Shapeshifter: Vulpine")


# --- creation -----------------------------------------------------------------


@pytest.mark.parametrize(("letter", "depth"), [("A", 6), ("B", 4), ("C", 3), ("D", 2), ("E", 1)])
def test_depth_starts_at_the_talent(letter: str, depth: int) -> None:
    # An E-Ghost: the bare A.I.'s Codeslinger wants a Matrix action picked.
    out = compute(_ai("E-Ghost", talent_letter=letter, attributes="B" if letter != "B" else "C"))
    assert out.talent == AI
    assert out.attributes["DEP"] == depth
    assert out.derived["metatype_info"]["attributes"]["DEP"]["min"] == depth
    assert {"DEP", "advanced programs"} <= set(out.derived["enabled_tabs"])
    assert not out.derived["errors"]


@pytest.mark.parametrize(
    ("method", "letter", "points"), [("Priority", "B", 10), ("SumToTen", "B", 10), ("Priority", "D", 7)]
)
def test_the_attribute_points_are_halved(method: str, letter: str, points: int) -> None:
    out = compute(_ai(method=method, attributes=letter))
    assert out.derived["points"]["attributes"]["max"] == points


def test_the_body_stays_at_zero() -> None:
    state = _ai()
    state.attributes = {**state.attributes, "BOD": 4, "AGI": 3}
    out = compute(state)
    assert all(out.derived["totals"][key] == 0 for key in ("BOD", "AGI", "REA", "STR"))
    assert out.derived["points"]["attributes"]["used"] == 0


def test_depth_above_the_talent_spends_special_points() -> None:
    state = _ai()
    state.attributes = {**state.attributes, "DEP": 5}
    out = compute(state)
    assert out.derived["totals"]["DEP"] == 5
    assert out.derived["points"]["special"] == {"used": 2, "max": 4}


def test_edge_is_capped_by_depth() -> None:
    state = _ai(talent_letter="D")
    state.attributes = {**state.attributes, "EDG": 6}
    out = compute(state)
    assert out.derived["metatype_info"]["attributes"]["EDG"]["max"] == 2
    assert out.derived["totals"]["EDG"] == 2


def test_an_e_ghosts_luck_raises_the_edge_cap_above_depth() -> None:
    out = compute(_ai("E-Ghost", talent_letter="D"))
    assert out.derived["metatype_info"]["attributes"]["EDG"]["max"] == 3


def test_a_karma_ai_starts_depth_at_one() -> None:
    out = compute(_ai(method="Karma"))
    assert out.attributes["DEP"] == 1
    breakdown = {row["notice"]["key"]: row["amount"] for row in out.derived["karma_spend_breakdown"]}
    assert breakdown["engine.spend.metatype"] == 180


def test_a_karma_ai_may_buy_no_talent() -> None:
    # A Karma build has no Talent priority: Mundane only means none was
    # bought, and the metatype still enables Depth.
    out = compute(_ai(method="Karma", talent="Mundane"))
    assert out.talent == "Mundane"
    assert out.attributes["DEP"] == 1
    assert not has(out.derived["errors"], "engine.priority.talentNotAllowed")


def test_a_new_karma_ai_takes_its_talent_rather_than_mundane() -> None:
    human = compute(_human(build_method="Karma"))
    ai = apply_patch(human, CharacterPatch(metatype=AI, metavariant=None))
    assert ai.talent == AI


def test_an_e_ghost_is_born_saying_hello_three_times() -> None:
    out = compute(_ai("E-Ghost"))
    names = [q["name"] for q in out.derived["qualities"] if q.get("origin") == "Metatype"]
    assert names.count("Hello World!") == 3
    assert not out.derived["errors"]


def test_a_gnome_is_born_with_arcane_arrester_twice() -> None:
    # The same rule as Hello World!: one quality per `<quality>` line.
    state = CharacterState(
        id="gnome",
        name="Gnome",
        metatype="Dwarf",
        metavariant="Gnome",
        priorities=Priorities(Heritage="A", Attributes="B", Talent="C", Skills="D", Resources="E"),
        attributes=default_attributes(find_metatype("Dwarf", "Gnome")),
    )
    out = compute(state)
    names = [q["name"] for q in out.derived["qualities"]]
    assert names.count("Arcane Arrester") == 2
    assert out.derived["spell_resistance"] == 4


# --- what an A.I. may not take ------------------------------------------------


def test_an_ai_may_not_take_a_magic_talent() -> None:
    out = compute(_ai(talent="Adept"))
    assert out.talent == "Adept"
    assert has(out.derived["errors"], "engine.priority.talentNotAllowed")


def test_a_human_may_not_take_the_ai_talent() -> None:
    out = compute(_human(talent=AI))
    assert has(out.derived["errors"], "engine.priority.talentNotAllowed")


def test_becoming_an_ai_switches_to_its_talent_and_back() -> None:
    human = compute(_human(talent="Adept"))
    ai = apply_patch(human, CharacterPatch(metatype=AI, metavariant=None))
    assert ai.talent == AI
    assert ai.attributes["DEP"] == 3
    assert not has(ai.derived["errors"], "engine.priority.talentNotAllowed")
    back = apply_patch(ai, CharacterPatch(metatype="Human", metavariant=None))
    assert back.talent != AI
    assert not has(back.derived["errors"], "engine.priority.talentNotAllowed")


def test_an_ai_may_take_only_the_qualities_on_its_list() -> None:
    allowed = compute(_ai(quality_ids=[_quality_id("Guts")]))
    assert not has(allowed.derived["errors"], "engine.qualities.forbidden")
    refused = compute(_ai(quality_ids=[_quality_id("Ambidextrous")]))
    assert has(refused.derived["errors"], "engine.qualities.forbidden")


def test_the_list_does_not_bind_a_metahuman() -> None:
    out = compute(_human(quality_ids=[_quality_id("Ambidextrous")]))
    assert not has(out.derived["errors"], "engine.qualities.forbidden")


def test_creation_offers_the_ai_and_its_talent() -> None:
    cat = public_catalog()
    offered = {m["name"]: m for m in cat["metatypes"]}
    assert {v["name"] for v in offered[AI]["metavariants"]} == set(VARIANTS)
    assert offered[AI]["quality_restriction"]["Positive"]
    heritage = cat["priority_table"]["Heritage"]
    for letter, cell in heritage.items():
        assert (AI in {m["name"] for m in cell["metatypes"]}) == (letter in "ABC")
    for cell in cat["priority_table"]["Talent"].values():
        rows = {t["name"]: t for t in cell["talents"]}
        assert rows[AI]["required"] == [{"kind": "metatype", "name": AI}]
    karma = {t["name"]: t for t in cat["karma_talents"]}
    assert AI in karma


# --- .chum5 -------------------------------------------------------------------


def test_the_export_says_depth_is_enabled_and_where_it_starts() -> None:
    state = _ai("E-Ghost")
    state.attributes = {**state.attributes, "DEP": 5}
    root = ET.fromstring(state_to_chum5(compute(state)))
    assert root.findtext("metatypecategory") == "Metasapient"
    assert root.findtext("depenabled") == "True"
    dep = next(a for a in root.iter("attribute") if a.findtext("name") == "DEP")
    # The talent's Depth is Chummer's minimum; only the two above it are bought.
    assert (dep.findtext("metatypemin"), dep.findtext("base")) == ("3", "2")


def test_an_ai_is_a_fixed_point_of_export_and_import() -> None:
    state = _ai("Xenosapient")
    state.attributes = {**state.attributes, "DEP": 4, "LOG": 6}
    first = compute(state)
    again, _ = chum5_to_state(state_to_chum5(first))
    second = compute(CharacterState(**again))
    assert second.metatype == AI
    assert second.metavariant == "Xenosapient"
    assert second.talent == AI
    assert second.attributes["DEP"] == 4
    assert second.attributes["LOG"] == 6
    assert second.derived["points"] == first.derived["points"]
