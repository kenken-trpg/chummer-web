"""`<critterpower>` in a requirement tree, and the powers a quality grants
surviving a `.chum5` round trip.

The loader kept `<critterpower>` in `required_tree` / `forbidden_tree`, but the
evaluator did not know the tag and answered "not met" — so Soul Swallower
could never be taken (DTR p.164: it needs Essence Drain), and an Infected
optional power never forbade one the character already had (RF p.126).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.engine import compute, default_attributes, find_metatype
from app.engine.constants import quality_optional_power_extra_key
from app.engine.requirements import requirement_tree_met
from app.models import CharacterState, Priorities
from tests.engine_support import _human, _quality_id


def _quality(name: str) -> dict:
    return next(q for q in catalog()["qualities"] if q["name"] == name)


def _flagged(out: dict, key: str) -> list[str]:
    return [e["params"]["name"]["tr"] for e in out["errors"] if e["key"] == key]


def test_soul_swallower_needs_essence_drain() -> None:
    alone = compute(_human("cp", quality_ids=[_quality_id("Soul Swallower")])).derived
    assert _flagged(alone, "engine.qualities.prereq") == ["Soul Swallower"]
    # Nosferatu's own powers include Essence Drain
    ids = [_quality_id("Infected: Nosferatu"), _quality_id("Soul Swallower")]
    assert "Soul Swallower" not in _flagged(compute(_human("cp", quality_ids=ids)).derived, "engine.qualities.prereq")


def test_an_optional_power_quality_is_forbidden_by_the_same_power_picked_elsewhere() -> None:
    mutaqua = _quality("Infected: Mutaqua")
    ids = [mutaqua["id"], _quality_id("Infected Optional Power: Fear")]
    unpicked = compute(_human("cp", quality_ids=ids)).derived
    assert "Infected Optional Power: Fear" not in _flagged(unpicked, "engine.qualities.forbidden")
    picked = compute(
        _human("cp", quality_ids=ids, quality_extras={quality_optional_power_extra_key(mutaqua["id"]): "Fear"})
    ).derived
    assert "Infected Optional Power: Fear" in _flagged(picked, "engine.qualities.forbidden")


def test_a_quality_is_checked_as_before_it_was_taken() -> None:
    """Chummer checks `<forbidden>` when a quality is added, so neither the
    quality nor the powers it brings are there yet."""
    # Infected Optional Power: Compulsion gives Compulsion and forbids it
    ids = [_quality_id("Infected: Nosferatu"), _quality_id("Infected Optional Power: Compulsion")]
    out = compute(_human("cp", quality_ids=ids)).derived
    assert "Infected Optional Power: Compulsion" not in _flagged(out, "engine.qualities.forbidden")
    # Mutaqua's forbidden list names Mutaqua
    troll = CharacterState(
        id="cp",
        name="cp",
        priorities=Priorities(),
        metatype="Troll",
        attributes=default_attributes(find_metatype("Troll", None)),
        quality_ids=[_quality_id("Infected: Mutaqua")],
    )
    assert "Infected: Mutaqua" not in _flagged(compute(troll).derived, "engine.qualities.forbidden")


def test_enhanced_mist_form_needs_the_mist_form_power() -> None:
    tree = next(m for m in catalog()["metamagics"] if m["name"] == "Enhanced Mist Form")["required_tree"]
    assert not requirement_tree_met(tree, {"critter_powers": set()})
    assert requirement_tree_met(tree, {"critter_powers": {"Mist Form"}})


def test_a_drakes_and_an_insect_spirits_powers_survive_the_round_trip() -> None:
    for name in ("Dracoform (Western Drake)", "Free Insect Spirit: Black Widow"):
        state = _human("rt", quality_ids=[_quality_id(name)])
        before = compute(state).derived
        xml = state_to_chum5(state)
        written = len(ET.fromstring(xml).findall("./critterpowers/critterpower"))
        for _ in range(2):
            back, _notes = chum5_to_state(xml)
            xml = state_to_chum5(CharacterState(**back))
        assert len(ET.fromstring(xml).findall("./critterpowers/critterpower")) == written, name
        after = compute(CharacterState(**chum5_to_state(xml)[0])).derived
        assert [q["name"] for q in after["qualities"]] == [q["name"] for q in before["qualities"]], name
        powers = [[p["name"] for p in q.get("critter_powers") or []] for q in before["qualities"]]
        assert [[p["name"] for p in q.get("critter_powers") or []] for q in after["qualities"]] == powers, name
        assert after["armor"] == before["armor"], name
