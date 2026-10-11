"""Pinned Character.RedlinerBonus/RefreshRedlinerImprovements accounting.

Liminal body cases verify slot arithmetic, not RF equipment eligibility.
Individual four-leg placement and Chummer GUI saves remain release gates.
"""

import pytest

from app.characters import apply_patch
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.engine import compute
from app.engine.ware.limbs import count_redliner_limbs, redliner_slot_caps
from app.models import CharacterOptions, CharacterPatch, CharacterState, CyberwareInstall
from tests.engine_support import _quality_id, _ware_id
from tests.test_centaur_grants import _centaur


def test_redliner_all_slots_use_the_extra_legs_and_respect_empty_exclusions() -> None:
    all_legs = [{"id": "legs", "name": "All legs", "category": "Cyberlimb", "limbslot": "leg", "limbslotcount": "all"}]
    assert redliner_slot_caps(extra_limbs={"leg": 2}) == {"arm": 2, "leg": 4}
    assert count_redliner_limbs(all_legs) == 2
    assert count_redliner_limbs(all_legs, redliner_slot_caps(extra_limbs={"leg": 2})) == 4
    assert count_redliner_limbs(all_legs, {}) == 0


@pytest.mark.parametrize("quality", ["Redliner", "Cyber-Singularity Seeker"])
def test_centaur_six_limb_count_caps_bonuses_and_survives_save_and_species_change(quality: str) -> None:
    state = _centaur(
        quality_ids=[_quality_id(quality)],
        cyberware=[
            CyberwareInstall(id="arm-left", ware_id=_ware_id("cyberware", "Obvious Full Arm"), side="Left"),
            CyberwareInstall(id="arm-right", ware_id=_ware_id("cyberware", "Obvious Full Arm"), side="Right"),
            CyberwareInstall(id="all-legs", ware_id=_ware_id("cyberware", "Liminal Body, Tank (Full)")),
        ],
    )
    out = compute(state)
    expected = out.derived["limb_quality"]
    installs = sorted((row.ware_id, row.side or "") for row in out.cyberware)
    assert expected["count"] == 6
    assert expected["pairs"] == 2
    assert out.derived["limb_replace"]["slots"]["leg"] == 4
    assert out.derived["limb_replace"]["parts"] == 8
    if quality == "Redliner":
        assert expected["attribute_bonus"] == {"STR": 2, "AGI": 2}
        assert expected["limb_bonus"] == 2
        assert expected["cm_physical"] == -6
        assert all(row["limb_str"] == row["limb_agi"] == 5 for row in out.derived["cyberware"])
    else:
        assert expected["attribute_bonus"] == {"WIL": 2}
        assert expected["limb_bonus"] == expected["cm_physical"] == 0
    for _ in range(2):
        out = compute(CharacterState.model_validate_json(out.model_dump_json()))
        assert out.derived["limb_quality"] == expected
        raw, warnings = chum5_to_state(state_to_chum5(out))
        assert not warnings
        out = compute(CharacterState.model_validate(raw))
        assert out.derived["limb_quality"] == expected
        assert sorted((row.ware_id, row.side or "") for row in out.cyberware) == installs
    human = apply_patch(out, CharacterPatch(metatype="Human"))
    assert human.derived["limb_quality"]["count"] == 4
    assert human.derived["limb_quality"]["pairs"] == 2
    assert human.derived["limb_replace"]["parts"] == 6
    back = apply_patch(human, CharacterPatch(metatype="Centaur"))
    assert back.derived["limb_quality"] == expected


def test_six_conventional_limbs_also_cap_redliner_without_all_slot_ware() -> None:
    state = _centaur(
        quality_ids=[_quality_id("Redliner")],
        options=CharacterOptions(redliner_torso=True, redliner_skull=True),
        cyberware=[
            CyberwareInstall(id=f"{slot}-{side}", ware_id=_ware_id("cyberware", f"Obvious Full {slot}"), side=side)
            for slot in ("Arm", "Leg")
            for side in ("Left", "Right")
        ]
        + [
            CyberwareInstall(id="torso", ware_id=_ware_id("cyberware", "Obvious Torso")),
            CyberwareInstall(id="skull", ware_id=_ware_id("cyberware", "Obvious Skull")),
        ],
    )
    out = compute(state)
    assert out.derived["limb_quality"]["count"] == 6
    assert out.derived["limb_quality"]["limb_bonus"] == 2
    assert out.derived["limb_quality"]["cm_physical"] == -6
