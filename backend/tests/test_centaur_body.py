"""Movement and costs against the pinned Character/Lifestyle implementations."""

import pytest

from app.characters import apply_patch
from app.data_loader import catalog
from app.engine import compute
from app.engine.compute.finalize import resolve_movement
from app.engine.ware.limbs import body_limb_slots, limb_attribute_replace
from app.improvements import collect_effects
from app.models import CharacterPatch, CharacterState, CyberwareInstall, LifestyleInstall, SettingsState
from tests.engine_support import LOW_LIFESTYLE, _quality_id, _ware_id
from tests.test_centaur_grants import _centaur


def test_centaur_movement_preserves_all_three_media() -> None:
    state = _centaur()
    state.attributes.update(AGI=3, STR=3)
    movement = compute(state).derived["movement"]
    assert (movement["walk"], movement["run"], movement["sprint"]) == ("3", "12", "4")
    ground, swim, fly = (movement["modes"][key] for key in ("Ground", "Swim", "Fly"))
    assert ground["rates"] == {"walk": 1, "run": 4, "sprint": 4}
    assert swim["rates"] == {"walk": 1, "run": 0, "sprint": 1}
    assert (swim["walk"], swim["run"], swim["sprint"]) == ("3", "0", "1")
    assert swim["available"]
    assert fly["rates"] == {"walk": 0, "run": 0, "sprint": 0}
    assert not fly["available"]
    reloaded = compute(CharacterState.model_validate_json(state.model_dump_json()))
    assert reloaded.derived["movement"] == movement


def test_swim_uses_limb_inclusive_strength_and_agility_not_ground_cyberlegs() -> None:
    state = _centaur(settings=SettingsState(cyberleg_movement=True))
    state.attributes.update(AGI=1, STR=5)
    state.cyberware = [
        CyberwareInstall(id="left-leg", ware_id=_ware_id("cyberware", "Obvious Full Leg"), side="Left"),
        CyberwareInstall(id="right-leg", ware_id=_ware_id("cyberware", "Obvious Full Leg"), side="Right"),
    ]
    out = compute(state).derived
    assert out["limb_replace"]["parts"] == 8
    assert out["limb_replace"]["slots"]["leg"] == 2
    assert out["totals"]["AGI"] == 2  # ceil((3+3+1*6)/8)
    assert out["totals"]["STR"] == 5  # ceil((3+3+5*6)/8)
    # The pinned C# threshold is >=2 cyberleg slots, also for a four-legged body.
    assert out["movement"]["walk"] == "3"
    assert out["movement"]["modes"]["Swim"]["walk"] == "3.5"
    state.settings.cyberleg_movement = False
    off = compute(state).derived["movement"]
    assert off["walk"] == "1"
    assert off["modes"]["Swim"]["walk"] == "3.5"


def test_extra_legs_reach_body_slots_and_all_slot_averaging() -> None:
    meta = catalog()["all_metatypes"]["Centaur"]
    effects = collect_effects([("Centaur", meta["bonus"])])
    extra = effects["extra_limbs"]
    assert body_limb_slots(extra) == {"arm": 2, "leg": 4, "torso": 1, "skull": 1}
    result = limb_attribute_replace(
        [
            {
                "id": "all-legs",
                "name": "All legs",
                "category": "Cyberlimb",
                "limbslot": "leg",
                "limbslotcount": "all",
                "limb_agi": 5,
                "limb_str": 5,
            }
        ],
        3,
        3,
        meta["attributes"],
        extra,
    )
    assert result is not None
    assert (result["count"], result["parts"], result["agi"], result["str"]) == (4, 8, 4, 4)


def test_movement_bonuses_are_scoped_to_their_medium_and_keep_fractional_rates() -> None:
    effects = collect_effects(
        [
            (
                "test",
                [
                    {"tag": "walkmultiplier", "fields": {"category": "Swim", "percent": "50"}},
                    {"tag": "sprintbonus", "fields": {"category": "Swim", "val": "50"}},
                ],
            )
        ]
    )
    meta = {"walk": "1/1/0.5", "run": "4/0/1", "sprint": "4/1/0.25"}
    movement = resolve_movement(meta, effects, 3, swim_agi=3, swim_str=4, ground_agi=6)
    assert movement["walk"] == "6"
    assert movement["modes"]["Swim"]["walk"] == "5.25"
    assert movement["modes"]["Swim"]["sprint"] == "1.5"
    assert movement["modes"]["Fly"]["walk"] == "1.5"  # meat AGI, not cyberleg AGI
    assert movement["modes"]["Fly"]["sprint"] == "0.25"


@pytest.mark.parametrize("months", [1, 3])
def test_centaur_lifestyle_multiplier_is_applied_once_and_included_in_spending(months: int) -> None:
    state = _centaur(lifestyles=[LifestyleInstall(lifestyle_id=LOW_LIFESTYLE, months=months)])
    out = compute(state)
    assert out.derived["lifestyle_cost_mod"] == 150
    assert out.derived["lifestyles"][0]["monthly"] == 5000
    assert out.derived["lifestyles"][0]["nuyen"] == 5000 * months
    assert out.derived["nuyen_spent"] == 5000 * months
    assert sum(row["amount"] for row in out.derived["nuyen_spend_breakdown"]) == 5000 * months
    assert compute(out).derived["nuyen_spent"] == 5000 * months
    human = apply_patch(out, CharacterPatch(metatype="Human"))
    assert human.derived["nuyen_spent"] == 2000 * months
    assert human.derived["lifestyle_cost_mod"] == 0


def test_centaur_lifestyle_compounds_modifiers_but_does_not_scale_outings_or_contracts() -> None:
    quality_ids = [_quality_id("Bad Credit"), _quality_id("Dependent (Nuisance)")]
    lifestyle_qualities = {row["name"]: row["id"] for row in catalog()["lifestyle_qualities"]}
    state = _centaur(
        quality_ids=quality_ids,
        lifestyles=[
            LifestyleInstall(
                lifestyle_id=LOW_LIFESTYLE,
                months=2,
                quality_ids=[
                    lifestyle_qualities["Subsistence Hunting/Gathering II"],
                    lifestyle_qualities["Datahost Subscription"],
                ],
            ),
            LifestyleInstall(lifestyle_id=LOW_LIFESTYLE),
        ],
    )
    out = compute(state).derived
    # Base x dependents(+10%) x Centaur(+150%) x Bad Credit(+10%), then +30/+250.
    assert [row["monthly"] for row in out["lifestyles"]] == [6330, 6050]
    assert out["nuyen_spent"] == 6330 * 2 + 6050
    assert sum(row["amount"] for row in out["nuyen_spend_breakdown"]) == out["nuyen_spent"]
