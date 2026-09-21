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
from app.engine import compute, default_attributes, find_metatype
from app.engine.karma import alternate_attribute_shift
from app.models import CharacterPatch, CharacterState, Priorities, SettingsState
from app.rules import Rules, using_rules


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


# --- <alternatemetatypeattributekarma> ------------------------------------ #


def _troll(cid: str, settings: SettingsState, **kw: object) -> CharacterState:
    attrs = default_attributes(find_metatype("Troll", None))
    attrs["BOD"] = attrs["BOD"] + 2
    return CharacterState(
        id=cid, name=cid, metatype="Troll", attributes=attrs, priorities=Priorities(), settings=settings, **kw
    )


def test_alternate_metatype_attribute_karma_prices_from_one_in_a_karma_build() -> None:
    """Troll BOD minimum 5, raised two levels to 7: 6 x 5 + 7 x 5 = 65 by
    the book, 2 x 5 + 3 x 5 = 25 under the house rule — what a metatype with a
    minimum of 1 pays for its first two levels (`TotalKarmaCost`)."""
    plain = compute(_troll("alt-off", SettingsState(), build_method="Karma")).derived["karma"]["spent"]
    alt = compute(
        _troll("alt-on", SettingsState(alternate_metatype_attribute_karma=True), build_method="Karma")
    ).derived["karma"]["spent"]
    assert plain - alt == 65 - 25


def test_alternate_metatype_attribute_karma_prices_priority_karma_levels_from_one() -> None:
    """The karma levels on a Priority sheet shift the same way: BOD 7 with
    one level bought with karma pays for level 3, not level 7."""
    on = SettingsState(alternate_metatype_attribute_karma=True)
    out = compute(_troll("alt-prio", on, attribute_karma={"BOD": 1}))
    assert out.derived["attribute_karma"]["karma"] == 3 * 5
    assert (
        compute(_troll("alt-prio-off", SettingsState(), attribute_karma={"BOD": 1})).derived["attribute_karma"]["karma"]
        == 7 * 5
    )


def test_alternate_metatype_attribute_karma_leaves_magic_alone() -> None:
    with using_rules(Rules(alternate_metatype_attribute_karma=True)):
        assert alternate_attribute_shift("MAG", 3) == 0
        assert alternate_attribute_shift("BOD", 5) == 4
    assert alternate_attribute_shift("BOD", 5) == 0
