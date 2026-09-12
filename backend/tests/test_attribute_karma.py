"""Priority / Sum-to-Ten creation: attribute levels bought with karma.

Chummer keeps each attribute as `<base>` (attribute points) plus `<karma>`
(levels on top bought at the karma price). `attribute_karma` is that second
part; the levels leave the point pool and cost new-rating x 5 each.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from app.characters import apply_patch
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.engine import compute
from app.models import CharacterPatch, CharacterState, Priorities
from tests.test_engine import default_attributes, find_metatype


def _human(cid: str, **kw: object) -> CharacterState:
    attrs = default_attributes(find_metatype("Human", None))
    attrs.update({"BOD": 4, "AGI": 4, "LOG": 3})
    return CharacterState(id=cid, name=cid, metatype="Human", attributes=attrs, priorities=Priorities(), **kw)


def test_karma_levels_leave_the_point_pool_and_cost_the_raise_price() -> None:
    plain = compute(_human("ak-plain"))
    split = compute(_human("ak-split", attribute_karma={"AGI": 1, "LOG": 2}))
    points = plain.derived["points"]["attributes"]["used"]
    assert split.derived["points"]["attributes"]["used"] == points - 3
    # AGI 4 (the 4th level) = 20; LOG 3 (the 2nd and 3rd levels) = 10 + 15
    assert split.derived["attribute_karma"] == {
        "levels": {"AGI": 1, "LOG": 2},
        "floors": split.derived["attribute_karma"]["floors"],
        "karma": 45,
    }
    assert split.derived["karma"]["spent"] == plain.derived["karma"]["spent"] + 45


def test_levels_are_clamped_to_what_the_rating_has_above_its_floor() -> None:
    out = compute(_human("ak-clamp", attribute_karma={"BOD": 9, "CHA": 2, "ESS": 1}))
    # BOD 4 over a floor of 1 has three levels; CHA sits on its floor; ESS is not an attribute to buy
    assert out.attribute_karma == {"BOD": 3}
    assert out.derived["attribute_karma"]["levels"] == {"BOD": 3}


def test_a_karma_build_keeps_no_split() -> None:
    out = compute(_human("ak-karma", build_method="Karma", attribute_karma={"AGI": 1}))
    assert out.attribute_karma == {}
    assert out.derived["attribute_karma"]["karma"] == 0


def test_the_cost_stays_on_the_books_in_career() -> None:
    created = compute(_human("ak-career", attribute_karma={"AGI": 1}))
    career = apply_patch(created, CharacterPatch(career=True))
    assert career.derived["attribute_karma"]["karma"] == 20
    assert career.derived["karma"]["spent"] == created.derived["karma"]["spent"]


def test_changing_metatype_drops_the_split() -> None:
    state = compute(_human("ak-meta", attribute_karma={"AGI": 1}))
    out = apply_patch(state, CharacterPatch(metatype="Elf"))
    assert out.attribute_karma == {}


def test_the_split_round_trips_through_chum5_as_base_and_karma() -> None:
    state = compute(_human("ak-chum5", attribute_karma={"AGI": 1}))
    root = ET.fromstring(state_to_chum5(state))
    agi = next(a for a in root.findall("./attributes/attribute") if a.findtext("name") == "AGI")
    assert (agi.findtext("base"), agi.findtext("karma")) == ("2", "1")  # min 1 + 2 points + 1 karma = 4
    st, _ = chum5_to_state(ET.tostring(root))
    assert st["attributes"]["AGI"] == 4
    assert st["attribute_karma"] == {"AGI": 1}


def test_a_finished_characters_karma_is_not_read_as_a_creation_split() -> None:
    """After creation Chummer's <karma> also holds every career raise — those
    are billed from the career baseline, not again as creation levels."""
    state = compute(_human("ak-done", attribute_karma={"AGI": 1}))
    root = ET.fromstring(state_to_chum5(state))
    root.find("created").text = "True"  # type: ignore[union-attr]
    agi = next(a for a in root.findall("./attributes/attribute") if a.findtext("name") == "AGI")
    agi.find("karma").text = "2"  # type: ignore[union-attr]
    st, _ = chum5_to_state(ET.tostring(root))
    assert st["attribute_karma"] == {}
    assert st["attributes"]["AGI"] == 5
