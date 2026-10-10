"""Four distinct leg installs using Chummer's existing Left/Right locations."""

from xml.etree import ElementTree as ET

import pytest

from app.characters import apply_patch
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.engine import compute
from app.engine.ware.sides import ensure_sides
from app.models import CharacterPatch, CharacterState, CyberwareInstall
from tests.engine_support import _quality_id, _ware_id
from tests.notice_asserts import has
from tests.test_centaur_grants import _centaur


def _legs(sides: list[str | None]) -> list[CyberwareInstall]:
    return [
        CyberwareInstall(id=f"leg-{i}", ware_id=_ware_id("cyberware", "Obvious Full Leg"), side=side)
        for i, side in enumerate(sides)
    ]


def test_four_legs_auto_assign_balanced_sides_and_count_each_install() -> None:
    state = compute(_centaur(cyberware=_legs([None] * 4), quality_ids=[_quality_id("Redliner")]))
    assert [row.side for row in state.cyberware] == ["Left", "Right", "Left", "Right"]
    assert not has(state.derived["errors"], "engine.ware.sideDuplicate")
    assert state.derived["body_limb_slots"] == {"arm": 2, "leg": 4, "torso": 1, "skull": 1}
    assert state.derived["limb_replace"]["count"] == 4
    assert state.derived["limb_quality"]["count"] == 4
    assert state.derived["limb_quality"]["limb_bonus"] == 2
    assert compute(state).derived["limb_replace"] == state.derived["limb_replace"]


def test_four_individually_customized_legs_keep_children_and_averages_across_saves() -> None:
    legs = _legs(["Left", "Right", "Left", "Right"])
    mods = [
        CyberwareInstall(
            id=f"{leg.id}-{attr}",
            ware_id=_ware_id("cyberware", f"Customized {name}"),
            rating=rating,
            parent_id=leg.id,
        )
        for leg, agi, strength in zip(legs, [3, 4, 5, 6], [4, 5, 6, 7], strict=True)
        for attr, name, rating in [("AGI", "Agility", agi), ("STR", "Strength", strength)]
    ]
    state = _centaur(cyberware=[*reversed(mods), *legs])  # children before parents
    state.attributes.update(AGI=1, STR=3)
    state = compute(state)
    assert not has(state.derived["errors"], "engine.ware.sideDuplicate")
    expected = state.derived["limb_replace"]
    assert (expected["count"], expected["parts"], expected["agi"], expected["str"]) == (4, 8, 3, 5)

    def signatures(st: CharacterState) -> list[tuple[str, int, str, tuple[tuple[str, int, str], ...]]]:
        return sorted(
            (
                leg.ware_id,
                leg.rating,
                leg.side or "",
                tuple(sorted((m.ware_id, m.rating, m.side or "") for m in st.cyberware if m.parent_id == leg.id)),
            )
            for leg in st.cyberware
            if not leg.parent_id
        )

    installs = signatures(state)
    for _ in range(2):
        state = compute(CharacterState.model_validate_json(state.model_dump_json()))
        xml = state_to_chum5(state)
        root = ET.fromstring(xml)
        saved_legs = root.findall("./cyberwares/cyberware")
        assert len(saved_legs) == 4
        assert [leg.findtext("location") for leg in saved_legs].count("Left") == 2
        assert [leg.findtext("location") for leg in saved_legs].count("Right") == 2
        assert len({leg.findtext("guid") for leg in saved_legs}) == 4
        raw, warnings = chum5_to_state(xml)
        assert not warnings
        state = compute(CharacterState.model_validate(raw))
        assert state.derived["limb_replace"] == expected
        assert signatures(state) == installs


@pytest.mark.parametrize("sides", [["Left", "Left", "Left", "Right"], ["Left", "Right", "Left", "Right", "Left"]])
def test_overflow_is_reported_and_excluded_from_averaging_and_redliner(sides: list[str]) -> None:
    state = compute(_centaur(cyberware=_legs(sides), quality_ids=[_quality_id("Redliner")]))
    assert has(state.derived["errors"], "engine.ware.sideDuplicate", side="engine.side.Left", slot="engine.slot.leg")
    expected = min(sides.count("Left"), 2) + min(sides.count("Right"), 2)
    assert state.derived["limb_replace"]["count"] == expected
    assert state.derived["limb_quality"]["count"] == expected


def test_species_change_and_removal_revalidate_without_dropping_installs() -> None:
    state = compute(_centaur(cyberware=_legs(["Left", "Right", "Left", "Right"])))
    human = apply_patch(state, CharacterPatch(metatype="Human"))
    assert human.derived["body_limb_slots"]["leg"] == 2
    assert has(human.derived["errors"], "engine.ware.sideDuplicate")
    assert human.derived["limb_replace"]["count"] == 2
    assert len(human.cyberware) == 4
    back = apply_patch(human, CharacterPatch(metatype="Centaur"))
    assert not has(back.derived["errors"], "engine.ware.sideDuplicate")
    assert back.derived["limb_replace"]["count"] == 4
    removed = apply_patch(back, CharacterPatch(cyberware=[row for row in back.cyberware if row.id != "leg-2"]))
    assert removed.derived["limb_replace"]["count"] == 3
    added = apply_patch(
        removed,
        CharacterPatch(
            cyberware=[*removed.cyberware, CyberwareInstall(ware_id=_ware_id("cyberware", "Obvious Full Leg"))]
        ),
    )
    assert added.cyberware[-1].side == "Left"
    assert added.derived["limb_replace"]["count"] == 4


@pytest.mark.parametrize("count,conflicts", [(1, False), (2, True)])
def test_quality_can_claim_a_free_extra_leg_but_not_a_full_side(count: int, conflicts: bool) -> None:
    quality = _quality_id("Crystal Limb (Leg)")
    state = compute(
        _centaur(cyberware=_legs(["Left"] * count), quality_ids=[quality], quality_extras={quality: "Left"})
    )
    assert has(state.derived["errors"], "engine.qualities.sideDuplicate") is conflicts


def test_centaur_does_not_gain_extra_arm_sides() -> None:
    state = compute(
        _centaur(
            cyberware=[
                CyberwareInstall(ware_id=_ware_id("cyberware", "Obvious Full Arm"), side="Left") for _ in range(2)
            ]
        )
    )
    assert has(state.derived["errors"], "engine.ware.sideDuplicate", side="engine.side.Left", slot="engine.slot.arm")
    assert state.derived["limb_replace"]["count"] == 1


@pytest.mark.parametrize("root_side,expected", [(None, "Left"), ("Right", "Right")])
def test_nested_children_inherit_sides_independent_of_list_order(root_side: str | None, expected: str) -> None:
    root = CyberwareInstall(
        id="root",
        ware_id=_ware_id("cyberware", "Obvious Full Leg" if root_side else "Liminal Body, Tank (Full)"),
        side=root_side,
    )
    subsystem = CyberwareInstall(
        id="subsystem", ware_id=_ware_id("cyberware", "Obvious Full Leg"), parent_id="root", side="Left"
    )
    enhancement = CyberwareInstall(
        id="enhancement", ware_id=_ware_id("cyberware", "Customized Agility"), parent_id="subsystem"
    )
    ensure_sides("cyberware", [enhancement, subsystem, root], {"leg": 2})
    assert subsystem.side == enhancement.side == expected
