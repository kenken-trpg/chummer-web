"""Cyberware and bioware: essence, grades, capacity, limbs and implant picks."""

from app.data_loader import catalog
from app.engine import (
    compute,
    default_attributes,
    find_metatype,
)
from app.models import (
    AdeptPowerInstall,
    CharacterOptions,
    CharacterState,
    CyberwareInstall,
    GearInstall,
    Priorities,
    SettingsState,
    VehicleModInstall,
)
from tests.engine_support import (
    ARM,
    CUSTOM_STR,
    CYBERLIMB_OPTIMIZATION,
    DATAJACK,
    DEAD_SIN,
    EYES,
    FORD_AMERICAR,
    HAND_BLADE,
    MECHANICAL_ARM,
    MUSCLE,
    ORTHOSKIN,
    QUALIA,
    REFLEX_RECORDER_OPTIMIZATION,
    SUPRATHYROID,
    TONER,
    WIRED,
    _adept,
    _career_quality,
    _human,
    _mundane,
    _optimized_arm,
    _quality_row,
    _ware_id,
    _ware_named,
)
from tests.notice_asserts import has

FLARE = "5921a6ac-1e20-483b-b210-dc84a14d3045"
SYNAPTIC = "4a4e1079-5872-4f3f-a450-48c30a5504f3"
CEREBRAL = "81b40aa8-98d1-4a5d-89d6-9b6d438006da"
MNEMONIC = "b2289ebe-4bb0-49d0-a151-38fc1261bba8"
PHEROMONES = "2faac78a-ab32-4541-ad9c-3ef6c1b2cd84"
SYNTHACARDIUM = "109b0a32-320f-41c5-9acb-c49308525ce0"
GLAND = "abdbc210-c1fa-45f1-9840-4f78d9eb8867"
RESERVOIR = "d2064cf2-e9f7-479f-92cc-7da7c6024121"
WEBBING = "4a939488-bd12-42f9-847f-1034fc3b4154"
DRAGON_HIDE = "8aa2590f-1fc5-4706-a7b9-9eec3db4fab9"
PUSHED = "2c988cbe-e6e6-4c22-ae3c-14ad6e1fff1f"
CYCLOPEAN_EYE = "acd06d4f-7f09-4d80-8bab-006b680392a2"
DAMPER = "3785a2cf-c3df-476a-b7cd-6e224ea77ab0"
ADAPSIN = "3f8b9030-662e-4212-8f30-5aa394a41568"
CUSTOM_AGI = "7afb23c7-435f-450c-9d1c-f7a0e7e631a6"
ENHANCED_STR = "a9f4efd4-b86c-4e90-b0f7-aefa32c3b9de"
LEG = "c7b88f7e-4e3c-4c29-9f86-a4e244ec5066"
TORSO = "48e490fb-fe6a-482c-a47d-40cb04985897"
HAND = "cc503281-ff05-4e22-9121-09116a4a8306"
SKULL = "ea676290-1859-4a56-86f8-a3fb90decc32"


def test_datajack_costs_essence_and_nuyen() -> None:
    state = CharacterState(
        id="jack",
        name="Jack",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        cyberware=[CyberwareInstall(ware_id=DATAJACK, rating=1, grade="Standard")],
    )
    out = compute(state)
    assert out.derived["essence"] == 5.9
    assert out.derived["nuyen_spent"] == 1000
    assert out.derived["nuyen"] == 49000


def test_alphaware_reduces_essence() -> None:
    state = CharacterState(
        id="alpha",
        name="Alpha",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        cyberware=[CyberwareInstall(ware_id=DATAJACK, grade="Alphaware")],
    )
    out = compute(state)
    assert out.derived["essence"] == 5.92
    assert out.derived["nuyen_spent"] == 1200


def test_muscle_replacement_adds_attributes() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    state = CharacterState(
        id="muscle",
        name="Muscle",
        priorities=Priorities(),
        metatype="Human",
        attributes=attrs,
        cyberware=[CyberwareInstall(ware_id=MUSCLE, rating=2)],
    )
    out = compute(state)
    assert out.derived["totals"]["AGI"] == 3
    assert out.derived["totals"]["STR"] == 3
    assert out.derived["essence"] == 4.0
    assert out.derived["nuyen_spent"] == 50000


def test_wired_reflexes_add_initiative_dice() -> None:
    state = CharacterState(
        id="wired",
        name="Wired",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        cyberware=[CyberwareInstall(ware_id=WIRED, rating=1)],
    )
    out = compute(state)
    assert out.derived["totals"]["REA"] == 2
    assert out.derived["initiative"]["dice"] == 2
    assert out.derived["essence"] == 4.0


def test_flare_compensation_in_eyes_uses_capacity_not_essence() -> None:
    state = CharacterState(
        id="flare-slot",
        name="FlareSlot",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        cyberware=[
            CyberwareInstall(id="eyes1", ware_id=EYES, rating=1),
            CyberwareInstall(ware_id=FLARE, parent_id="eyes1"),
        ],
    )
    out = compute(state)
    assert out.derived["essence"] == 5.8
    assert out.derived["nuyen_spent"] == 5000
    eyes = next(item for item in out.derived["cyberware"] if item["id"] == "eyes1")
    assert eyes["capacity_used"] == 1
    assert eyes["capacity_max"] == 4


def test_flare_compensation_standalone_costs_essence() -> None:
    state = CharacterState(
        id="flare-solo",
        name="FlareSolo",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        cyberware=[CyberwareInstall(ware_id=FLARE)],
    )
    out = compute(state)
    assert out.derived["essence"] == 5.9
    assert out.derived["nuyen_spent"] == 1000


def test_muscle_toner_raises_agility() -> None:
    state = CharacterState(
        id="toner",
        name="Toner",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        bioware=[CyberwareInstall(ware_id=TONER, rating=2)],
    )
    out = compute(state)
    assert out.derived["totals"]["AGI"] == 3
    assert out.derived["essence"] == 5.6
    assert out.derived["ware_attr_bonus"]["AGI"] == 2
    assert out.derived["ware_attr_limit"] == 4
    assert not has(out.derived["errors"], "engine.ware.attrBonusOver")


def test_muscle_replacement_four_is_at_ware_attr_cap() -> None:
    out = compute(
        _mundane(
            "ware-cap-ok",
            priorities=Priorities(Heritage="C", Attributes="B", Talent="E", Skills="D", Resources="A"),
            cyberware=[CyberwareInstall(ware_id=MUSCLE, rating=4)],
        )
    )
    assert out.derived["ware_attr_bonus"]["AGI"] == 4
    assert out.derived["ware_attr_bonus"]["STR"] == 4
    assert out.derived["totals"]["AGI"] == 5
    assert not has(out.derived["errors"], "engine.ware.attrBonusOver")


def test_muscle_replacement_and_toner_exceed_ware_attr_cap() -> None:
    out = compute(
        _mundane(
            "ware-cap-over",
            priorities=Priorities(Heritage="C", Attributes="B", Talent="E", Skills="D", Resources="A"),
            cyberware=[CyberwareInstall(ware_id=MUSCLE, rating=4)],
            bioware=[CyberwareInstall(ware_id=TONER, rating=2)],
        )
    )
    assert out.derived["ware_attr_bonus"]["AGI"] == 6
    assert out.derived["ware_attr_bonus"]["STR"] == 4
    assert has(out.derived["errors"], "engine.ware.attrBonusOver", attr="AGI", value=6)
    assert not has(out.derived["errors"], "engine.ware.attrBonusOver", attr="STR")


def test_toner_and_suprathyroid_exceed_ware_attr_cap() -> None:
    out = compute(
        _mundane(
            "ware-cap-gland",
            priorities=Priorities(Heritage="C", Attributes="B", Talent="E", Skills="D", Resources="A"),
            bioware=[
                CyberwareInstall(ware_id=TONER, rating=4),
                CyberwareInstall(ware_id=SUPRATHYROID),
            ],
        )
    )
    assert out.derived["ware_attr_bonus"]["AGI"] == 5
    assert out.derived["ware_attr_bonus"]["STR"] == 1
    assert has(out.derived["errors"], "engine.ware.attrBonusOver", attr="AGI", value=5)


def test_cyberlimb_custom_strength_does_not_count_as_ware_attr_bonus() -> None:
    out = compute(
        _mundane(
            "ware-cap-limb",
            cyberware=[
                CyberwareInstall(id="arm1", ware_id=ARM),
                CyberwareInstall(ware_id=CUSTOM_STR, rating=6, parent_id="arm1"),
            ],
        )
    )
    assert out.derived.get("ware_attr_bonus") in ({}, None) or "STR" not in (out.derived.get("ware_attr_bonus") or {})
    assert not has(out.derived["errors"], "engine.ware.attrBonusOver")
    arm = next(item for item in out.derived["cyberware"] if item["id"] == "arm1")
    assert arm["limb_str"] == 6


def test_customized_strength_starts_above_the_limbs_base_of_three() -> None:
    """Inside a limb `{STRMinimum}` is the limb's own base (3), not the
    character's: Chummer's `Cyberware.ProcessAttributesInXPath` walks up to the
    cyberlimb. Reading the racial 1 priced every Customized point 5,000¥ high,
    which left four of Chummer's own test characters 30-60,000¥ in debt."""
    state = CharacterState(
        id="custom-human",
        name="CustomHuman",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        cyberware=[
            CyberwareInstall(id="arm1", ware_id=ARM),
            CyberwareInstall(ware_id=CUSTOM_STR, rating=3, parent_id="arm1"),
        ],
    )
    out = compute(state)
    custom = next(item for item in out.derived["cyberware"] if item["ware_id"] == CUSTOM_STR)
    assert custom["rating_min"] == 4
    assert custom["rating_max"] == 6
    assert custom["rating"] == 4  # a stored 3 is below the floor
    assert custom["nuyen"] == 5000
    arm = next(item for item in out.derived["cyberware"] if item["id"] == "arm1")
    assert arm["limb_str"] == 4
    assert arm["limb_agi"] == 3  # empty cyberlimb attribute base is 3 (SR5 p.456)
    assert out.derived["nuyen_spent"] == 20000
    assert out.derived["ware_ranges"][CUSTOM_STR] == {"min": 4, "max": 6}


def test_troll_customized_strength_keeps_the_troll_maximum() -> None:
    """The floor is the limb's 3 for a troll too; only the ceiling is racial."""
    state = CharacterState(
        id="custom-troll",
        name="CustomTroll",
        priorities=Priorities(Heritage="A", Attributes="C", Talent="E", Skills="B", Resources="D"),
        metatype="Troll",
        attributes=default_attributes(find_metatype("Troll", None)),
        cyberware=[
            CyberwareInstall(id="arm1", ware_id=ARM),
            CyberwareInstall(ware_id=CUSTOM_STR, rating=5, parent_id="arm1"),
        ],
    )
    out = compute(state)
    custom = next(item for item in out.derived["cyberware"] if item["ware_id"] == CUSTOM_STR)
    assert custom["rating_min"] == 4
    assert custom["rating_max"] == 10
    assert custom["rating"] == 5
    assert custom["nuyen"] == 10000
    arm = next(item for item in out.derived["cyberware"] if item["id"] == "arm1")
    assert arm["limb_str"] == 5
    assert arm["limb_agi"] == 3


def test_customized_and_enhanced_stack_on_limb() -> None:
    state = CharacterState(
        id="limb-stack",
        name="LimbStack",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        cyberware=[
            CyberwareInstall(id="arm1", ware_id=ARM),
            CyberwareInstall(ware_id=CUSTOM_AGI, rating=4, parent_id="arm1"),
            CyberwareInstall(ware_id=ENHANCED_STR, rating=2, parent_id="arm1"),
        ],
    )
    out = compute(state)
    custom = next(item for item in out.derived["cyberware"] if item["ware_id"] == CUSTOM_AGI)
    assert custom["nuyen"] == 5000  # the first point above the limb's 3
    arm = next(item for item in out.derived["cyberware"] if item["id"] == "arm1")
    assert arm["limb_str"] == 5  # base 3 + Enhanced Strength 2
    assert arm["limb_agi"] == 4  # Customized Agility sets the base
    assert arm["capacity_used"] == 2


ENHANCED_AGI = "2c50d5c1-f2ff-4c7b-bf5e-46925e808648"
CYBERLIMB_ARMOR = "8ea736c6-5a90-471c-9320-18432ec9aaf0"


def test_empty_cyberlimb_has_attribute_base_three() -> None:
    out = compute(
        _mundane(
            "bare-limb",
            cyberware=[CyberwareInstall(id="arm1", ware_id=ARM, side="Left")],
        )
    )
    arm = next(item for item in out.derived["cyberware"] if item["id"] == "arm1")
    assert arm["limb_str"] == 3 and arm["limb_agi"] == 3
    assert arm["limb_armor"] == 0


def test_cyberlimb_attribute_capped_at_augmented_maximum() -> None:
    # Customized 6 + Enhanced 3 = 9, which is exactly the Human AGI aug max
    state = CharacterState(
        id="limb-cap",
        name="LimbCap",
        career=True,
        nuyen_earned=10_000_000,
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        cyberware=[
            CyberwareInstall(id="arm1", ware_id=ARM, side="Left"),
            CyberwareInstall(ware_id=CUSTOM_AGI, rating=6, parent_id="arm1"),
            CyberwareInstall(ware_id=ENHANCED_AGI, rating=3, parent_id="arm1"),
            CyberwareInstall(ware_id=CYBERLIMB_ARMOR, rating=3, parent_id="arm1"),
        ],
    )
    out = compute(state)
    arm = next(item for item in out.derived["cyberware"] if item["id"] == "arm1")
    assert arm["limb_agi"] == 9
    assert arm["limb_armor"] == 3
    assert out.derived["armor"] == 3  # cyberlimb Armor mod adds to the armor rating


def test_one_customized_arm_pulls_body_strength() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    attrs["STR"] = 1
    state = CharacterState(
        id="one-arm",
        name="OneArm",
        priorities=Priorities(),
        metatype="Human",
        attributes=attrs,
        cyberware=[
            CyberwareInstall(id="arm1", ware_id=ARM),
            CyberwareInstall(ware_id=CUSTOM_STR, rating=6, parent_id="arm1"),
        ],
    )
    out = compute(state)
    assert out.derived["limb_replace"]["count"] == 1
    # Chummer's six limbs, skull included: (6 + 1×5) / 6, rounded up
    assert out.derived["limb_replace"]["parts"] == 6
    assert out.derived["totals"]["STR"] == 2
    assert out.derived["limb_replace"]["meat_str"] == 1


SHIVA_ARMS = "51ba5e67-f2fd-4149-b24c-9b502ed0e7c7"
BUSTED_CYBERWARE = "ab862f1f-5ed3-4976-a781-bf63565faf26"


def test_busted_cyberware_costs_half_a_point_of_essence() -> None:
    """`addware`: somebody left junk in you (TSG p.30). The implant is hidden
    in Chummer's catalog, so it is nobody's to buy — it arrives with the
    quality, at the grade the quality forces, and takes its Essence."""
    plain = compute(_mundane("clean"))
    out = compute(_mundane("busted", quality_ids=[BUSTED_CYBERWARE]))
    row = next(item for item in out.derived["cyberware"] if item["name"] == "Busted Ware")
    assert row["granted_by"] == "Busted Cyberware"
    assert row["grade"] == "None"
    assert row["nuyen"] == 0
    assert out.derived["essence"] == plain.derived["essence"] - 0.5
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "addware" not in tags


def test_hidden_ware_stays_out_of_the_picker() -> None:
    """It is in the catalog so `<addware>` has something to name, and out of
    the picker so nobody buys half a point of junk on purpose."""
    from app.catalog_view import public_catalog

    assert any(item["name"] == "Busted Ware" for item in catalog()["cyberware"]["items"])
    names = {item["name"] for item in public_catalog()["cyberware"]["items"]}
    assert "Busted Ware" not in names
    assert "Wired Reflexes" in names


def test_dead_sin_comes_with_a_fake_sin_and_four_licenses() -> None:
    """`addgear` hands the gear over free (BTB p.162). The rows live in the
    derived output only — the quality carries them, so they cost no nuyen, ask
    for nothing, and go when it goes."""
    out = compute(_mundane("dead-sin", quality_ids=[DEAD_SIN]))
    rows = [row for row in out.derived["gear"] if row.get("granted_by")]
    sin = next(row for row in rows if row["name"] == "Fake SIN")
    licenses = [row for row in rows if row["name"] == "Fake License"]
    assert sin["rating"] == 3 and sin["nuyen"] == 0 and sin["granted_by"] == "Dead SIN"
    assert len(licenses) == 4
    assert all(row["parent_id"] == sin["id"] and row["rating"] == 3 for row in licenses)
    assert out.derived["nuyen_spent"] == 0
    # Nothing in the gear tab can fill these in, so nothing asks.
    keys = [item["key"] for item in out.derived["warnings"]]
    assert "engine.gear.pickExtra" not in keys
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "addgear" not in tags


def test_shiva_arms_average_a_cyberlimb_over_eight_parts() -> None:
    """`addlimb`: a second pair of arms (RF p.118) is two more body parts to
    average a cyberlimb's STR/AGI over (SR5 p.456), so the same two cyberarms
    move the total less."""
    attrs = default_attributes(find_metatype("Human", None))
    attrs["STR"] = 2
    limbs = [
        CyberwareInstall(id="arm1", ware_id=ARM),
        CyberwareInstall(ware_id=CUSTOM_STR, rating=6, parent_id="arm1"),
        CyberwareInstall(id="arm2", ware_id=ARM),
        CyberwareInstall(ware_id=CUSTOM_STR, rating=6, parent_id="arm2"),
    ]

    def build(quality_ids: list[str]) -> CharacterState:
        return CharacterState(
            id="shiva",
            name="Shiva",
            priorities=Priorities(),
            metatype="Human",
            attributes=attrs,
            quality_ids=quality_ids,
            cyberware=[item.model_copy(deep=True) for item in limbs],
        )

    plain = compute(build([]))
    shiva = compute(build([SHIVA_ARMS]))
    # six limbs (skull included) and two more arms: 4 = ⌈20/6⌉, 3 = ⌈24/8⌉
    assert plain.derived["limb_replace"]["parts"] == 6
    assert shiva.derived["limb_replace"]["parts"] == 8
    assert shiva.derived["limb_replace"]["count"] == 2
    assert shiva.derived["totals"]["STR"] < plain.derived["totals"]["STR"]
    tags = [item["tag"] for item in shiva.derived["unimplemented_bonuses"]]
    assert "addlimb" not in tags


def test_two_arms_average_with_meat() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    attrs["STR"] = 3
    state = CharacterState(
        id="two-arm",
        name="TwoArm",
        priorities=Priorities(),
        metatype="Human",
        attributes=attrs,
        cyberware=[
            CyberwareInstall(id="arm1", ware_id=ARM),
            CyberwareInstall(ware_id=CUSTOM_STR, rating=6, parent_id="arm1"),
            CyberwareInstall(id="arm2", ware_id=ARM),
            CyberwareInstall(ware_id=CUSTOM_STR, rating=6, parent_id="arm2"),
        ],
    )
    out = compute(state)
    assert out.derived["limb_replace"]["count"] == 2
    assert out.derived["limb_replace"]["slots"]["arm"] == 2
    assert out.derived["totals"]["STR"] == 4
    assert out.derived["limits"]["physical"] >= 3


def test_full_body_limbs_replace_strength() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    state = CharacterState(
        id="full-body",
        name="FullBody",
        priorities=Priorities(),
        metatype="Human",
        attributes=attrs,
        cyberware=[
            CyberwareInstall(id="arm1", ware_id=ARM),
            CyberwareInstall(ware_id=CUSTOM_STR, rating=6, parent_id="arm1"),
            CyberwareInstall(id="arm2", ware_id=ARM),
            CyberwareInstall(ware_id=CUSTOM_STR, rating=6, parent_id="arm2"),
            CyberwareInstall(id="leg1", ware_id=LEG),
            CyberwareInstall(ware_id=CUSTOM_STR, rating=6, parent_id="leg1"),
            CyberwareInstall(id="leg2", ware_id=LEG),
            CyberwareInstall(ware_id=CUSTOM_STR, rating=6, parent_id="leg2"),
            CyberwareInstall(id="torso1", ware_id=TORSO),
            CyberwareInstall(ware_id=CUSTOM_STR, rating=6, parent_id="torso1"),
        ],
    )
    out = compute(state)
    assert out.derived["limb_replace"]["count"] == 5
    assert out.derived["totals"]["STR"] == 6
    assert out.derived["limb_replace"]["meat_str"] == 1


def test_cyberhand_does_not_count_as_body_limb() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    attrs["STR"] = 3
    state = CharacterState(
        id="hand-only",
        name="HandOnly",
        priorities=Priorities(),
        metatype="Human",
        attributes=attrs,
        cyberware=[CyberwareInstall(ware_id=HAND)],
    )
    out = compute(state)
    assert out.derived["limb_replace"] is None
    assert out.derived["totals"]["STR"] == 3


REDLINER = "38deea18-76f0-49a3-95ba-50006e4e7f90"
SEEKER = "b47319f5-372d-4e23-9fd9-a8e4aecd4c85"


def test_two_arms_without_side_are_assigned_left_and_right() -> None:
    state = CharacterState(
        id="auto-side",
        name="AutoSide",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        cyberware=[
            CyberwareInstall(id="arm1", ware_id=ARM),
            CyberwareInstall(id="arm2", ware_id=ARM),
        ],
    )
    out = compute(state)
    sides = {item["id"]: item["side"] for item in out.derived["cyberware"] if item["ware_id"] == ARM}
    assert set(sides.values()) == {"Left", "Right"}
    assert out.derived["limb_replace"]["count"] == 2
    assert out.derived["errors"] == []


def test_duplicate_left_arms_are_an_error_and_count_once() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    attrs["STR"] = 1
    state = CharacterState(
        id="dup-left",
        name="DupLeft",
        priorities=Priorities(),
        metatype="Human",
        attributes=attrs,
        cyberware=[
            CyberwareInstall(id="arm1", ware_id=ARM, side="Left"),
            CyberwareInstall(ware_id=CUSTOM_STR, rating=6, parent_id="arm1"),
            CyberwareInstall(id="arm2", ware_id=ARM, side="Left"),
            CyberwareInstall(ware_id=CUSTOM_STR, rating=6, parent_id="arm2"),
        ],
    )
    out = compute(state)
    assert has(out.derived["errors"], "engine.ware.sideDuplicate", side="engine.side.Left", slot="engine.slot.arm")
    assert out.derived["limb_replace"]["count"] == 1
    assert out.derived["totals"]["STR"] == 2


def test_redliner_adds_limb_attributes_and_cuts_physical_cm() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    attrs["STR"] = 1
    attrs["BOD"] = 1
    state = CharacterState(
        id="redliner-two",
        name="RedlinerTwo",
        priorities=Priorities(Heritage="C", Attributes="B", Talent="E", Skills="D", Resources="A"),
        metatype="Human",
        attributes=attrs,
        quality_ids=[REDLINER],
        cyberware=[
            CyberwareInstall(id="arm1", ware_id=ARM, side="Left"),
            CyberwareInstall(ware_id=CUSTOM_STR, rating=6, parent_id="arm1"),
            CyberwareInstall(id="arm2", ware_id=ARM, side="Right"),
            CyberwareInstall(ware_id=CUSTOM_STR, rating=6, parent_id="arm2"),
        ],
    )
    out = compute(state)
    assert out.derived["limb_quality"]["count"] == 2
    assert out.derived["limb_quality"]["pairs"] == 1
    assert out.derived["limb_quality"]["limb_bonus"] == 1
    arms = [item for item in out.derived["cyberware"] if item["ware_id"] == ARM]
    assert all(item["limb_str"] == 7 for item in arms)
    assert out.derived["totals"]["STR"] == 3
    assert out.derived["condition_monitor"]["physical"] == 10
    assert out.derived["karma"]["remaining"] == 15


def test_redliner_four_limbs_is_plus_two() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    state = CharacterState(
        id="redliner-four",
        name="RedlinerFour",
        priorities=Priorities(Heritage="C", Attributes="B", Talent="E", Skills="D", Resources="A"),
        metatype="Human",
        attributes=attrs,
        quality_ids=[REDLINER],
        cyberware=[
            CyberwareInstall(id="arm1", ware_id=ARM, side="Left"),
            CyberwareInstall(id="arm2", ware_id=ARM, side="Right"),
            CyberwareInstall(id="leg1", ware_id=LEG, side="Left"),
            CyberwareInstall(id="leg2", ware_id=LEG, side="Right"),
        ],
    )
    out = compute(state)
    assert out.derived["limb_quality"]["count"] == 4
    assert out.derived["limb_quality"]["pairs"] == 2
    assert out.derived["limb_quality"]["cm_physical"] == -2
    arm = next(item for item in out.derived["cyberware"] if item["id"] == "arm1")
    assert arm["limb_str"] == 5  # base 3 + Redliner +2
    assert arm["limb_agi"] == 5


def test_cyber_singularity_seeker_adds_willpower() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    state = CharacterState(
        id="seeker",
        name="Seeker",
        priorities=Priorities(),
        metatype="Human",
        attributes=attrs,
        quality_ids=[SEEKER],
        cyberware=[
            CyberwareInstall(id="arm1", ware_id=ARM, side="Left"),
            CyberwareInstall(id="arm2", ware_id=ARM, side="Right"),
        ],
    )
    out = compute(state)
    assert out.derived["totals"]["WIL"] == 2
    assert out.derived["limb_quality"]["pairs"] == 1
    assert out.derived["limb_quality"]["limb_bonus"] == 0
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "cyberseeker" not in tags


def test_torso_and_hand_do_not_count_for_redliner() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    state = CharacterState(
        id="redliner-torso",
        name="RedlinerTorso",
        priorities=Priorities(),
        metatype="Human",
        attributes=attrs,
        quality_ids=[REDLINER],
        cyberware=[
            CyberwareInstall(id="arm1", ware_id=ARM, side="Left"),
            CyberwareInstall(id="torso1", ware_id=TORSO),
            CyberwareInstall(ware_id=HAND, side="Right"),
        ],
    )
    out = compute(state)
    assert out.derived["limb_quality"]["count"] == 1
    assert out.derived["limb_quality"]["pairs"] == 0
    assert out.derived["limb_replace"]["count"] == 2
    assert out.derived["limb_quality"]["cm_physical"] == 0
    assert out.derived["limb_quality"]["include"] == ["arm", "leg"]


def test_redliner_option_counts_torso() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    state = CharacterState(
        id="redliner-torso-on",
        name="RedlinerTorsoOn",
        priorities=Priorities(),
        metatype="Human",
        attributes=attrs,
        quality_ids=[REDLINER],
        options=CharacterOptions(redliner_torso=True),
        cyberware=[
            CyberwareInstall(id="arm1", ware_id=ARM, side="Left"),
            CyberwareInstall(id="torso1", ware_id=TORSO),
        ],
    )
    out = compute(state)
    assert out.derived["limb_quality"]["count"] == 2
    assert out.derived["limb_quality"]["pairs"] == 1
    assert out.derived["limb_quality"]["limb_bonus"] == 1
    assert out.derived["limb_quality"]["include"] == ["arm", "leg", "torso"]


def test_redliner_option_counts_skull() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    state = CharacterState(
        id="redliner-skull-on",
        name="RedlinerSkullOn",
        priorities=Priorities(),
        metatype="Human",
        attributes=attrs,
        quality_ids=[REDLINER],
        options=CharacterOptions(redliner_skull=True),
        cyberware=[
            CyberwareInstall(id="arm1", ware_id=ARM, side="Left"),
            CyberwareInstall(id="skull1", ware_id=SKULL),
        ],
    )
    out = compute(state)
    assert out.derived["limb_quality"]["count"] == 2
    assert out.derived["limb_quality"]["pairs"] == 1
    assert "skull" in out.derived["limb_quality"]["include"]


def test_redliner_warns_against_muscle_replacement() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    state = CharacterState(
        id="redliner-muscle",
        name="RedlinerMuscle",
        priorities=Priorities(Heritage="C", Attributes="B", Talent="E", Skills="D", Resources="A"),
        metatype="Human",
        attributes=attrs,
        quality_ids=[REDLINER],
        cyberware=[
            CyberwareInstall(id="arm1", ware_id=ARM, side="Left"),
            CyberwareInstall(id="arm2", ware_id=ARM, side="Right"),
            CyberwareInstall(ware_id=MUSCLE, rating=1),
        ],
    )
    out = compute(state)
    assert has(out.derived["warnings"], "engine.ware.redlinerIncompatible", needed=["Muscle Replacement"])
    assert out.derived["limb_quality"]["pairs"] == 1


def test_redliner_warns_against_muscle_toner() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    state = CharacterState(
        id="redliner-toner",
        name="RedlinerToner",
        priorities=Priorities(),
        metatype="Human",
        attributes=attrs,
        quality_ids=[REDLINER],
        cyberware=[CyberwareInstall(id="arm1", ware_id=ARM, side="Left")],
        bioware=[CyberwareInstall(ware_id=TONER, rating=1)],
    )
    out = compute(state)
    assert has(out.derived["warnings"], "engine.ware.redlinerIncompatible", needed=["Muscle Toner"])


def test_synaptic_booster_raises_reaction_and_initiative() -> None:
    state = CharacterState(
        id="synaptic",
        name="Synaptic",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        bioware=[CyberwareInstall(ware_id=SYNAPTIC, rating=1)],
    )
    out = compute(state)
    assert out.derived["totals"]["REA"] == 2
    assert out.derived["initiative"]["dice"] == 2
    assert out.derived["essence"] == 5.5
    assert out.derived["nuyen_spent"] == 95000
    assert out.derived["essence_lost_bio"] == 0.5


def test_cerebral_booster_raises_logic() -> None:
    state = CharacterState(
        id="cerebral",
        name="Cerebral",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        bioware=[CyberwareInstall(ware_id=CEREBRAL, rating=2)],
    )
    out = compute(state)
    assert out.derived["totals"]["LOG"] == 3
    assert out.derived["essence"] == 5.6
    assert out.derived["nuyen_spent"] == 63000


def test_cultured_used_grade_falls_back_to_standard() -> None:
    state = CharacterState(
        id="cultured-used",
        name="CulturedUsed",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        bioware=[CyberwareInstall(ware_id=SYNAPTIC, rating=1, grade="Used")],
    )
    out = compute(state)
    item = next(row for row in out.derived["bioware"] if row["ware_id"] == SYNAPTIC)
    assert item["grade"] == "Standard"
    assert item["essence"] == 0.5
    assert has(out.derived["warnings"], "engine.ware.gradeBanned", name="Synaptic Booster", grade="Used")


def test_chemical_gland_expanded_reservoir_adds_parent_essence() -> None:
    state = CharacterState(
        id="gland",
        name="Gland",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        bioware=[
            CyberwareInstall(id="gland1", ware_id=GLAND),
            CyberwareInstall(ware_id=RESERVOIR, parent_id="gland1"),
        ],
    )
    out = compute(state)
    parent = next(row for row in out.derived["bioware"] if row["id"] == "gland1")
    child = next(row for row in out.derived["bioware"] if row["ware_id"] == RESERVOIR)
    assert parent["essence"] == 0.2
    assert child["essence"] == 0
    assert child["parent_id"] == "gland1"
    assert out.derived["essence_lost_bio"] == 0.2


def test_hand_webbing_assigns_left_side() -> None:
    state = CharacterState(
        id="webbing",
        name="Webbing",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        bioware=[CyberwareInstall(ware_id=WEBBING)],
    )
    out = compute(state)
    item = next(row for row in out.derived["bioware"] if row["ware_id"] == WEBBING)
    assert item["selectside"]
    assert item["side"] == "Left"


def test_orthoskin_upgrade_warns_without_orthoskin() -> None:
    state = CharacterState(
        id="dragon-alone",
        name="DragonAlone",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        bioware=[CyberwareInstall(ware_id=DRAGON_HIDE)],
    )
    out = compute(state)
    assert has(out.derived["warnings"], "engine.ware.requires", needed=["Orthoskin"])
    assert out.derived["essence_lost_bio"] == 0.1


def test_orthoskin_upgrade_nested_pays_own_essence() -> None:
    state = CharacterState(
        id="dragon-nested",
        name="DragonNested",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        bioware=[
            CyberwareInstall(id="skin1", ware_id=ORTHOSKIN, rating=1),
            CyberwareInstall(ware_id=DRAGON_HIDE, parent_id="skin1"),
        ],
    )
    out = compute(state)
    skin = next(row for row in out.derived["bioware"] if row["id"] == "skin1")
    hide = next(row for row in out.derived["bioware"] if row["ware_id"] == DRAGON_HIDE)
    assert skin["essence"] == 0.25
    assert hide["essence"] == 0.1
    assert hide["parent_id"] == "skin1"
    assert out.derived["essence_lost_bio"] == 0.35
    assert not has(out.derived["warnings"], "engine.ware.requires", needed=["Orthoskin"])


def test_mnemonic_enhancer_raises_mental_limit() -> None:
    state = CharacterState(
        id="mnemonic",
        name="Mnemonic",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        bioware=[CyberwareInstall(ware_id=MNEMONIC, rating=2)],
    )
    out = compute(state)
    assert out.derived["limits"]["mental"] == 4
    assert out.derived["essence"] == 5.8


def test_tailored_pheromones_raise_social_limit() -> None:
    state = CharacterState(
        id="pheromones",
        name="Pheromones",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        bioware=[CyberwareInstall(ware_id=PHEROMONES, rating=1)],
    )
    out = compute(state)
    assert out.derived["limits"]["social"] == 4
    assert out.derived["essence"] == 5.8
    assert out.derived["skill_group_bonus"]["Acting"] == 1
    assert out.derived["skill_group_bonus"]["Influence"] == 1
    assert out.derived["skill_bonus"]["Con"] == 1
    assert out.derived["skill_bonus"]["Negotiation"] == 1
    assert "People who can smell you" in out.derived["skill_bonus_notes"]["Con"]


def test_synthacardium_adds_athletics_dice() -> None:
    state = CharacterState(
        id="synth",
        name="Synth",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        bioware=[CyberwareInstall(ware_id=SYNTHACARDIUM, rating=2)],
    )
    out = compute(state)
    assert out.derived["skill_group_bonus"]["Athletics"] == 2
    assert out.derived["skill_bonus"]["Gymnastics"] == 2
    assert out.derived["skill_bonus"]["Running"] == 2
    assert out.derived["skill_bonus"]["Swimming"] == 2
    assert out.derived["skill_totals"].get("Gymnastics", 0) == 0
    assert out.derived["essence"] == 5.8


def test_mnemonic_enhancer_adds_knowledge_category_dice() -> None:
    state = CharacterState(
        id="mnemonic-know",
        name="MnemonicKnow",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        knowledge_skills={"Alcohol": 3},
        bioware=[CyberwareInstall(ware_id=MNEMONIC, rating=2)],
    )
    out = compute(state)
    assert out.derived["skill_category_bonus"]["Interest"] == 2
    assert out.derived["skill_category_bonus"]["Academic"] == 2
    assert out.derived["skill_bonus"]["Alcohol"] == 2
    assert "Administration" not in out.derived["skill_bonus"]


def test_custom_knowledge_keeps_category_and_mnemonic_bonus() -> None:
    out = compute(
        _human(
            "know-custom",
            knowledge_skills={"Seattle Gangs": 2},
            knowledge_categories={"Seattle Gangs": "Street"},
            bioware=[CyberwareInstall(ware_id=MNEMONIC, rating=2)],
        )
    )
    row = next(item for item in out.derived["knowledge_skills"] if item["name"] == "Seattle Gangs")
    assert row["category"] == "Street"
    assert row["attribute"] == "INT"
    assert out.knowledge_categories == {"Seattle Gangs": "Street"}
    assert out.derived["skill_bonus"]["Seattle Gangs"] == 2


def test_seeker_alone_does_not_warn_for_muscle() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    state = CharacterState(
        id="seeker-muscle",
        name="SeekerMuscle",
        priorities=Priorities(Heritage="C", Attributes="B", Talent="E", Skills="D", Resources="A"),
        metatype="Human",
        attributes=attrs,
        quality_ids=[SEEKER],
        cyberware=[
            CyberwareInstall(id="arm1", ware_id=ARM, side="Left"),
            CyberwareInstall(ware_id=MUSCLE, rating=1),
        ],
    )
    out = compute(state)
    # ignore the unrelated leftover-nuyen / leftover-karma carryover notices
    carry = {"engine.nuyen.chargenCarryOver", "engine.karma.chargenCarryOver"}
    assert [w for w in out.derived["warnings"] if w["key"] not in carry] == []


ENHANCED_ARTICULATION = "dfada66f-73f7-4648-aff4-6b6bce25f84c"
REFLEX_RECORDER = "17a6ba49-c21c-461b-9830-3beae8a237fc"
ACTIVE_HARDWIRES = "b330ed31-20d4-4e5a-823b-4ef6d6270685"
KNOWLEDGE_HARDWIRES = "56a5fcc1-5da7-4728-aae9-073c92f67c2b"
CATLIKE = "84305e09-f8d5-4a82-8257-0119b8c3f926"


def test_enhanced_articulation_adds_escape_artist() -> None:
    out = compute(_human("articulation", bioware=[CyberwareInstall(ware_id=ENHANCED_ARTICULATION)]))
    assert out.derived["skill_bonus"]["Escape Artist"] == 1
    assert out.derived["limits"]["physical"] == 3


def test_catlike_adds_sneaking() -> None:
    out = compute(_human("catlike", quality_ids=[CATLIKE]))
    assert out.derived["skill_bonus"]["Sneaking"] == 2
    assert out.derived["skill_pick_slots"] == []


NANOHIVE_SOFT = "52d76c1a-2918-4531-b6ad-5ea732a1e6ea"  # <selectcyberware><category>Soft Nanoware
IMPLANT_MEDIC = "e709cb79-e351-41ce-b305-58720993d2c1"  # <selectcyberware /> — any implant


def _keyed(cid: str, ware_id: str, extra: str | None) -> CharacterState:
    return _human(cid, cyberware=[CyberwareInstall(id="w1", ware_id=ware_id, rating=2, extra=extra)])


def _ware_row(out: CharacterState) -> dict[str, object]:
    return next(row for row in out.derived["cyberware"] if row["id"] == "w1")


def test_a_keyed_implant_asks_for_its_target() -> None:
    out = compute(_keyed("nanohive-empty", NANOHIVE_SOFT, None))
    row = _ware_row(out)
    assert (row["select_ware"], row["select_ware_category"], row["extra"]) == (True, "Soft Nanoware", "")
    assert has(out.derived["warnings"], "engine.ware.pickTarget", name="Nanohive, Soft")


def test_a_keyed_implant_keeps_a_target_from_its_category() -> None:
    out = compute(_keyed("nanohive-ok", NANOHIVE_SOFT, "Nanotattoos"))
    assert _ware_row(out)["extra"] == "Nanotattoos"
    assert not has(out.derived["warnings"], "engine.ware.pickTarget")
    # A label only: no bonus, no essence or nuyen of its own.
    assert out.derived["unimplemented_bonuses"] == []


def test_a_target_outside_the_category_is_stripped_from_the_character() -> None:
    out = compute(_keyed("nanohive-bad", NANOHIVE_SOFT, "Cyberears"))
    assert has(out.derived["warnings"], "engine.ware.targetInvalid", picked="Cyberears")
    assert _ware_row(out)["extra"] == ""
    # the state itself, not only the payload
    assert out.cyberware[0].extra is None


def test_an_unfiltered_keyed_implant_takes_any_implant() -> None:
    out = compute(_keyed("medic", IMPLANT_MEDIC, "Cyberears"))
    row = _ware_row(out)
    assert (row["select_ware"], row["select_ware_category"]) == (True, "")
    assert row["extra"] == "Cyberears"
    assert not has(out.derived["warnings"], "engine.ware.targetInvalid")


def test_ware_that_is_not_keyed_carries_no_target() -> None:
    out = compute(_human("plain-ware", cyberware=[CyberwareInstall(id="w1", ware_id=DATAJACK)]))
    row = _ware_row(out)
    assert (row["select_ware"], row["extra"]) == (False, "")


def test_reflex_recorder_warns_until_skill_picked() -> None:
    out = compute(_human("recorder-empty", bioware=[CyberwareInstall(id="rec1", ware_id=REFLEX_RECORDER)]))
    assert has(out.derived["warnings"], "engine.skills.pickSkill", source="Reflex Recorder")
    assert out.derived["skill_bonus"].get("Gymnastics", 0) == 0
    slots = out.derived["skill_pick_slots"]
    assert len(slots) == 1
    assert slots[0]["key"] == "ware:rec1:0"
    assert "Gymnastics" in slots[0]["options"]
    assert "Software" not in slots[0]["options"]


def test_reflex_recorder_adds_picked_skill() -> None:
    out = compute(
        _human(
            "recorder-gym",
            bioware=[CyberwareInstall(id="rec1", ware_id=REFLEX_RECORDER)],
            skill_picks={"ware:rec1:0": "Gymnastics"},
        )
    )
    assert out.derived["skill_bonus"]["Gymnastics"] == 1
    assert not has(out.derived["warnings"], "engine.skills.pickSkill")
    assert out.derived["skill_pick_slots"][0]["picked"] == "Gymnastics"


def test_active_hardwires_offers_a_rated_pick() -> None:
    out = compute(_human("hw-empty", cyberware=[CyberwareInstall(id="hw1", ware_id=ACTIVE_HARDWIRES, rating=4)]))
    assert has(out.derived["warnings"], "engine.skills.pickSkill", source="Active Hardwires")
    slot = out.derived["skill_pick_slots"][0]
    assert slot["key"] == "ware:hw1:0"
    # The value is a rating, never a dice bonus.
    assert (slot["rating"], slot["bonus"], slot["max"]) == (4, 0, 0)
    assert "Archery" in slot["options"]
    assert "Spellcasting" not in slot["options"]  # excludecategory="Magical Active,..."


def test_active_hardwires_sets_the_picked_skill_rating() -> None:
    out = compute(
        _human(
            "hw-archery",
            cyberware=[CyberwareInstall(id="hw1", ware_id=ACTIVE_HARDWIRES, rating=4)],
            skill_picks={"ware:hw1:0": "Archery"},
        )
    )
    # The rating rides the skillsoft channel: bought nothing, still at 4.
    assert out.derived["skillsoft"]["Archery"] == 4
    assert out.derived["skill_totals"].get("Archery", 0) == 0
    assert not has(out.derived["warnings"], "engine.skills.pickSkill")


def test_hardwires_needs_no_skillwires_and_does_not_pay_karma() -> None:
    plain = compute(_human("hw-cost-off"))
    out = compute(
        _human(
            "hw-cost-on",
            cyberware=[CyberwareInstall(id="hw1", ware_id=ACTIVE_HARDWIRES, rating=6)],
            skill_picks={"ware:hw1:0": "Archery"},
        )
    )
    assert out.derived["skillwires"] == 0
    assert not has(out.derived["warnings"], "engine.skills.needsSkillwires")
    assert out.derived["skillsoft"]["Archery"] == 6
    assert out.derived["points"]["skills"] == plain.derived["points"]["skills"]


def test_knowledge_hardwires_picks_a_knowledge_skill() -> None:
    out = compute(
        _human(
            "hw-know",
            cyberware=[CyberwareInstall(id="hw1", ware_id=KNOWLEDGE_HARDWIRES, rating=3)],
            skill_picks={"ware:hw1:0": "Anatomy"},
        )
    )
    slot = out.derived["skill_pick_slots"][0]
    assert slot["knowledgeskills"] is True  # <hardwires knowledgeskill="True">
    assert "Archery" not in slot["options"]
    assert out.derived["skillsoft"]["Anatomy"] == 3
    row = next(r for r in out.derived["knowledge_skills"] if r["name"] == "Anatomy")
    assert (row["rating"], row["skillsoft"]) == (0, 3)


def test_reflex_recorder_rejects_invalid_pick() -> None:
    out = compute(
        _human(
            "recorder-bad",
            bioware=[CyberwareInstall(id="rec1", ware_id=REFLEX_RECORDER)],
            skill_picks={"ware:rec1:0": "Software"},
        )
    )
    assert has(out.derived["warnings"], "engine.skills.pickInvalid")
    assert out.derived["skill_bonus"].get("Software", 0) == 0


def test_adapsin_discounts_cyberware_essence_but_not_its_own() -> None:
    plain = compute(_mundane("plain", cyberware=[CyberwareInstall(ware_id=WIRED, rating=1)]))
    assert plain.derived["cyberware"][0]["essence"] == 2.0

    out = compute(
        _mundane(
            "adapsin",
            cyberware=[CyberwareInstall(ware_id=WIRED, rating=1)],
            bioware=[CyberwareInstall(ware_id=ADAPSIN)],
        )
    )
    # Standard grade drops 1.0 -> 0.9 for cyberware only; the Adapsin bioware
    # itself still costs its listed 0.2, because bioware has no Adapsin grades.
    assert out.derived["cyberware"][0]["essence"] == 1.8
    assert out.derived["bioware"][0]["essence"] == 0.2
    assert out.derived["essence"] == 4.0
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "adapsin" not in tags


def test_adapsin_discount_is_per_grade_not_a_flat_ten_percent() -> None:
    """Alphaware goes 0.8 -> 0.7, which is a tenth off the multiplier, not a
    tenth off the result (that would be 0.72). The numbers come from the grade
    table, so this pins that they are being read rather than computed."""
    out = compute(
        _mundane(
            "adapsin-alpha",
            cyberware=[CyberwareInstall(ware_id=WIRED, rating=1, grade="Alphaware")],
            bioware=[CyberwareInstall(ware_id=ADAPSIN)],
        )
    )
    assert out.derived["cyberware"][0]["essence"] == 1.4


def test_the_adapsin_grade_twins_are_not_offered_in_the_picker() -> None:
    """Chummer models Adapsin by swapping in a parallel grade; those are an
    implementation detail, not something a player picks."""
    names = [grade["name"] for grade in catalog()["cyberware"]["grades"]]
    assert not [name for name in names if "(Adapsin)" in name]
    standard = next(grade for grade in catalog()["cyberware"]["grades"] if grade["name"] == "Standard")
    assert (standard["ess"], standard["ess_adapsin"]) == (1.0, 0.9)


def test_damper_adds_sonic_resistance() -> None:
    out = compute(_mundane("damper", cyberware=[CyberwareInstall(ware_id=DAMPER)]))
    assert out.derived["special_armor"]["sonic"] == 2
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "sonicresist" not in tags


def test_pushed_adds_dice_to_every_log_linked_skill() -> None:
    """`skilllinkedattribute` reads like `skillattribute`: every skill hanging
    off that attribute gets the dice, and nothing else does."""
    out = compute(_mundane("pushed", bioware=[CyberwareInstall(ware_id=PUSHED)]))
    bonus = out.derived["skill_bonus"]
    assert bonus["Computer"] == 1  # LOG
    # "Medicine" is both an active skill and a knowledge skill; the bonus is
    # keyed by name, so it must land once, not once per list.
    assert bonus["Medicine"] == 1  # LOG
    assert bonus.get("Gymnastics", 0) == 0  # AGI
    assert bonus.get("Con", 0) == 0  # CHA
    # A knowledge skill nobody bought stays out of the sheet entirely.
    assert bonus.get("Corporation: Evo", 0) == 0
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "skilllinkedattribute" not in tags


def test_qualia_and_pushed_stack_on_a_skill_linked_to_both() -> None:
    out = compute(
        _mundane(
            "qualia-pushed",
            bioware=[CyberwareInstall(ware_id=QUALIA), CyberwareInstall(ware_id=PUSHED)],
        )
    )
    # Qualia is INT, PuSHed is LOG, so no single skill takes both.
    assert out.derived["skill_bonus"]["Perception"] == 1
    assert out.derived["skill_bonus"]["Computer"] == 1


def test_cyclopean_eye_costs_a_die_on_defense_tests() -> None:
    """`defensetest` lands in the same pool as `dodge` — one eye, no depth
    perception (RF p.154)."""
    out = compute(_mundane("one-eye", quality_ids=[CYCLOPEAN_EYE]))
    assert out.derived["test_mods"]["dodge"] == -1
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "defensetest" not in tags


def test_wired_reflexes_rating_three_exceeds_chargen_avail() -> None:
    out = compute(
        _mundane(
            "avail-wired3",
            priorities=Priorities(Heritage="C", Attributes="B", Talent="E", Skills="D", Resources="A"),
            cyberware=[CyberwareInstall(ware_id=WIRED, rating=3)],
        )
    )
    ware = out.derived["cyberware"][0]
    assert ware["avail"] == "20R"
    assert has(out.derived["errors"], "engine.gear.availOver", shown="20R")


def test_betaware_adds_four_avail() -> None:
    ok = compute(
        _mundane(
            "avail-beta-ok",
            cyberware=[CyberwareInstall(ware_id=WIRED, rating=1, grade="Betaware")],
        )
    )
    over = compute(
        _mundane(
            "avail-beta-over",
            priorities=Priorities(Heritage="C", Attributes="B", Talent="E", Skills="D", Resources="A"),
            cyberware=[CyberwareInstall(ware_id=WIRED, rating=2, grade="Betaware")],
        )
    )
    assert ok.derived["cyberware"][0]["avail"] == "12R"
    assert not has(ok.derived["errors"], "engine.gear.availOver")
    assert over.derived["cyberware"][0]["avail"] == "16R"
    assert has(over.derived["errors"], "engine.gear.availOver", shown="16R")


def test_mechanical_arm_does_not_host_ware() -> None:
    car = GearInstall(gear_id=FORD_AMERICAR)
    arm = VehicleModInstall(id="mech1", mod_id=MECHANICAL_ARM, parent_id=car.id)
    out = compute(
        _mundane(
            "car-mech",
            vehicles=[car],
            vehicle_mods=[arm],
            cyberware=[CyberwareInstall(ware_id=HAND_BLADE, parent_id=arm.id)],
        )
    )
    assert all(item["name"] != "Hand Blade" for item in out.derived["cyberware"])
    mech = next(item for item in out.derived["vehicle_mods"] if item["id"] == "mech1")
    assert mech["cyberware"] == []
    assert not mech.get("subsystems")


MUZZLE = "605b82f9-9f12-4a14-b567-091dd5fcde80"


def test_muzzle_does_not_report_an_unimplemented_bonus() -> None:
    """`weaponaccuracy` sharpens the `Fangs` natural weapon, and natural
    weapons belong to critters we do not build — nothing to report to the
    player about it."""
    out = compute(_mundane("muzzle", bioware=[CyberwareInstall(ware_id=MUZZLE)]))
    assert out.derived["unimplemented_bonuses"] == []


def _recorder(cid: str, *, optimized: bool, picked: str = "Automatics") -> CharacterState:
    ware = [CyberwareInstall(id="rr", ware_id=REFLEX_RECORDER, rating=1)]
    if optimized:
        ware.append(CyberwareInstall(id="opt", ware_id=REFLEX_RECORDER_OPTIMIZATION, rating=1))
    return _mundane(cid, bioware=ware, skill_picks={"ware:rr:0": picked})


def test_reflex_recorder_optimization_covers_the_picks_group() -> None:
    """The recorded skill and the rest of its group default without the −1."""
    out = compute(_recorder("rr-opt", optimized=True))
    assert out.derived["no_default_penalty_skills"] == ["Automatics", "Longarms", "Pistols"]
    assert out.derived["skill_pick_slots"][0]["default_free"] is True
    assert "reflexrecorderoptimization" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


def test_a_reflex_recorder_alone_covers_nothing() -> None:
    out = compute(_recorder("rr-plain", optimized=False))
    assert out.derived["no_default_penalty_skills"] == []
    assert out.derived["skill_pick_slots"][0]["default_free"] is False


def test_cyberlimb_optimization_asks_for_its_skill() -> None:
    """Upstream writes the pick as `<weaponskillaccuracy><selectskill/>`, not a
    bare `<selectskill>`, so it used to get no picker and do nothing, silently."""
    out = compute(_optimized_arm()).derived
    (slot,) = out["skill_pick_slots"]
    assert slot["key"] == "ware:opt:acc0"
    assert slot["source"] == "Cyberlimb Optimization"
    assert slot["accuracy"] == 1
    # Accuracy, not dice: nothing on the pool
    assert slot["bonus"] == 0
    assert "Pistols" in slot["options"]
    assert any(w["key"] == "engine.skills.pickSkill" for w in out["warnings"])
    assert out["weapons"][0]["accuracy"] == "5"


def test_two_lower_cyberlimbs_add_a_box_between_them() -> None:
    """`<pairbonus>` (Obvious Lower Arm, CF p.87): +1 physical box once a
    second lower limb is in — any lower limb, via `<pairinclude>`."""
    arm = _ware_id("cyberware", "Obvious Lower Arm")
    leg = _ware_id("cyberware", "Obvious Lower Leg")

    def physical(*rows: CyberwareInstall) -> int:
        return int(compute(_human("pair", cyberware=list(rows))).derived["condition_monitor"]["physical"])

    alone = physical(CyberwareInstall(id="a", ware_id=arm, side="Left"))
    assert (
        physical(
            CyberwareInstall(id="a", ware_id=arm, side="Left"), CyberwareInstall(id="b", ware_id=arm, side="Right")
        )
        == alone + 1
    )
    assert (
        physical(CyberwareInstall(id="a", ware_id=arm, side="Left"), CyberwareInstall(id="b", ware_id=leg, side="Left"))
        == alone + 1
    )
    # one bonus per pair, not per partner
    four = [
        CyberwareInstall(id="a", ware_id=arm, side="Left"),
        CyberwareInstall(id="b", ware_id=arm, side="Right"),
        CyberwareInstall(id="c", ware_id=leg, side="Left"),
        CyberwareInstall(id="d", ware_id=leg, side="Right"),
    ]
    assert physical(*four) == alone + 2


def test_a_pair_of_fins_swims() -> None:
    fin = _ware_id("cyberware", "Cyberfins (Hands)")
    one = compute(_human("fin", cyberware=[CyberwareInstall(id="a", ware_id=fin)])).derived
    two = compute(
        _human("fins", cyberware=[CyberwareInstall(id="a", ware_id=fin), CyberwareInstall(id="b", ware_id=fin)])
    ).derived
    assert one["skill_bonus"].get("Swimming", 0) == 0
    assert two["skill_bonus"]["Swimming"] == 1


def test_two_cyberlimb_optimizations_on_one_skill_add_a_die() -> None:
    """Upstream's pair bonus is a `<selectskill>` that means the skill the
    pair was optimized for (CF p.87) — and only a matching pair pairs."""
    full = _ware_id("cyberware", "Obvious Full Arm")
    rows = [
        CyberwareInstall(id="L", ware_id=full, side="Left"),
        CyberwareInstall(id="R", ware_id=full, side="Right"),
        CyberwareInstall(id="o1", ware_id=CYBERLIMB_OPTIMIZATION, parent_id="L"),
        CyberwareInstall(id="o2", ware_id=CYBERLIMB_OPTIMIZATION, parent_id="R"),
    ]
    same = compute(
        _human("co", cyberware=rows, skill_picks={"ware:o1:acc0": "Pistols", "ware:o2:acc0": "Pistols"})
    ).derived
    assert same["skill_bonus"]["Pistols"] == 1
    split = compute(
        _human("co2", cyberware=rows, skill_picks={"ware:o1:acc0": "Pistols", "ware:o2:acc0": "Longarms"})
    ).derived
    assert split["skill_bonus"].get("Pistols", 0) == 0
    assert split["skill_bonus"].get("Longarms", 0) == 0


def test_muzzle_sharpens_every_fang() -> None:
    """`<weaponaccuracy><name>[contains]Fangs` (Muzzle, CF p.121): +2 Accuracy
    on any weapon whose name holds "Fangs"."""
    fangs = _ware_id("bioware", "Fangs")
    muzzle = _ware_id("bioware", "Muzzle")

    def fang_accuracy(*ids: str) -> str:
        out = compute(_human("muzzle", bioware=[CyberwareInstall(ware_id=i) for i in ids])).derived
        return next(str(w["accuracy"]) for w in out["weapons"] if "Fangs" in w["name"])

    assert fang_accuracy(fangs) == "3"
    assert fang_accuracy(fangs, muzzle) == "5"


def test_paired_digigrade_legs_steady_the_raptor_foot() -> None:
    """Digigrade Legs' pair bonus (CF p.87) gives the Raptor Foot +1 on an
    Accuracy that is a limit formula — the offset moves, the limit stays."""
    leg = _ware_id("cyberware", "Obvious Full Leg")
    digi = _ware_id("cyberware", "Digigrade Legs")
    foot = _ware_id("cyberware", "Raptor Foot")
    rows = [
        CyberwareInstall(id="L", ware_id=leg, side="Left"),
        CyberwareInstall(id="R", ware_id=leg, side="Right"),
        CyberwareInstall(id="rf", ware_id=foot, parent_id="L", side="Left"),
        CyberwareInstall(id="d1", ware_id=digi, parent_id="L"),
    ]

    def raptor(cyber: list[CyberwareInstall]) -> tuple[str, str, int]:
        out = compute(_human("digi", cyberware=cyber)).derived
        weapon = next(w for w in out["weapons"] if w["name"] == "Raptor Foot")
        return str(weapon["accuracy_formula"]), str(weapon["accuracy"]), int(out["limits"]["physical"])

    formula, accuracy, physical = raptor(rows)
    assert formula == "Physical-1"
    assert accuracy == str(physical - 1)
    formula, accuracy, physical = raptor([*rows, CyberwareInstall(id="d2", ware_id=digi, parent_id="R")])
    assert formula == "Physical"
    assert accuracy == str(physical)


def _reflexes(wireless: bool, **kwargs: object) -> dict:
    wired = _ware_id("cyberware", "Wired Reflexes")
    enhancers = _ware_id("cyberware", "Reaction Enhancers")
    rows = [
        CyberwareInstall(ware_id=wired, rating=3, wireless=wireless),
        CyberwareInstall(ware_id=enhancers, rating=3, wireless=wireless),
    ]
    return compute(_human("reflexes", cyberware=rows, **kwargs)).derived


def test_reflex_augmentations_do_not_stack_on_their_own() -> None:
    """Wired Reflexes and Reaction Enhancers both give REA at precedence 0:
    only the better one counts (Chummer `precedence`, SR5 p.459)."""
    base = compute(_human("plain")).derived["totals"]["REA"]
    out = _reflexes(wireless=False)
    assert out["totals"]["REA"] == base + 3
    assert out["ware_attr_bonus"]["REA"] == 3


def test_a_wireless_pair_of_reflex_augmentations_stacks() -> None:
    """`<wirelesspairbonus mode="replace">`: both wireless, each bonus moves to
    precedence 1, and those stack — REA +6, with `<aug>` lifting the chargen
    cap by one each at Rating 3 so the build is legal."""
    base = compute(_human("plain")).derived["totals"]["REA"]
    out = _reflexes(wireless=True)
    assert out["totals"]["REA"] == base + 6
    assert out["ware_attr_bonus"]["REA"] == 6
    assert not any(e["key"] == "engine.ware.attrBonusOver" for e in out["errors"])
    # the initiative dice are Wired Reflexes' alone either way
    assert out["initiative"]["dice"] == 1 + 3


def test_initiative_dice_from_ware_and_power_take_the_best() -> None:
    """Improved Reflexes (power) and Wired Reflexes (ware) both add dice at
    precedence 0 — across the two sources, only the better one counts."""
    power = next(p["id"] for p in catalog()["powers"] if p["name"] == "Improved Reflexes")
    wired = _ware_id("cyberware", "Wired Reflexes")
    out = compute(
        _adept(
            "ir-wr",
            adept_powers=[AdeptPowerInstall(power_id=power, rating=2)],
            cyberware=[CyberwareInstall(ware_id=wired, rating=1)],
        )
    ).derived
    assert out["initiative"]["dice"] == 1 + 2


def test_wired_reflexes_switch_lightning_reflexes_off() -> None:
    """`<disablequality>` (RF p.148): Lightning Reflexes stops working once
    Wired Reflexes does its job — its initiative bonus goes, Wired's stays."""
    lr = _career_quality("Lightning Reflexes")["id"]
    alone = compute(_mundane("lr", quality_ids=[lr])).derived
    wired = compute(_mundane("wr", cyberware=[CyberwareInstall(ware_id=WIRED, rating=1)])).derived
    both = compute(_mundane("lr-wr", quality_ids=[lr], cyberware=[CyberwareInstall(ware_id=WIRED, rating=1)])).derived
    plain = compute(_mundane("none")).derived
    assert alone["initiative"] != plain["initiative"]
    assert both["initiative"] == wired["initiative"]
    assert _quality_row(both, "Lightning Reflexes")["disabled_by"] == "Wired Reflexes"
    assert "disabled_by" not in _quality_row(alone, "Lightning Reflexes")


def test_muscle_replacement_switches_celerity_off() -> None:
    celerity = _career_quality("Celerity")["id"]
    muscle = CyberwareInstall(ware_id=_ware_named("Muscle Replacement"), rating=1)
    alone = compute(_mundane("cel", quality_ids=[celerity])).derived
    both = compute(_mundane("cel-mr", quality_ids=[celerity], cyberware=[muscle])).derived
    plain = compute(_mundane("cel-none")).derived
    # movement is metres now, so Muscle Replacement's AGI moves it too:
    # compare with the ware on its own, not with a bare runner
    muscle_only = compute(_mundane("cel-mr-only", cyberware=[muscle])).derived
    assert alone["movement"] != plain["movement"]
    assert both["movement"] == muscle_only["movement"]
    assert _quality_row(both, "Celerity")["disabled_by"] == "Muscle Replacement"


def _legged(cid: str, legs: int, settings: SettingsState) -> CharacterState:
    ware = [
        CyberwareInstall(id="leg1", ware_id=LEG, side="Left"),
        CyberwareInstall(ware_id=CUSTOM_AGI, rating=5, parent_id="leg1"),
        CyberwareInstall(id="leg2", ware_id=LEG, side="Right"),
    ][: 2 if legs == 1 else 3]
    return _human(cid, cyberware=ware, settings=settings)


def test_two_cyberlegs_set_movement_under_the_house_rule() -> None:
    """`<cyberlegmovement>` (Chummer's `CalculatedMovement`): with both legs
    chrome, movement runs off the lower leg AGI (3, the plain leg) instead
    of the runner's own AGI 1."""
    on = SettingsState(cyberleg_movement=True)
    both = compute(_legged("legs-on", 2, on)).derived
    assert (both["movement"]["walk"], both["movement"]["run"]) == ("6", "12")

    off = compute(_legged("legs-off", 2, SettingsState())).derived
    assert (off["movement"]["walk"], off["movement"]["run"]) == ("2", "4")

    one = compute(_legged("leg-one", 1, on)).derived
    assert one["movement"]["walk"] == "2", "a single cyberleg does not count"


def test_a_cyberarm_averages_over_six_limbs_rounding_up() -> None:
    """Chummer's `CalculatedTotalValue`: AGI 3 with one AGI 5 arm is
    ⌈(5 + 3×5) / 6⌉ = 4, where five parts rounded down gave 3."""
    state = _human(
        "arm-avg",
        cyberware=[
            CyberwareInstall(id="a1", ware_id=ARM, side="Left"),
            CyberwareInstall(ware_id=CUSTOM_AGI, rating=5, parent_id="a1"),
        ],
    )
    state.attributes["AGI"] = 3
    assert compute(state).derived["totals"]["AGI"] == 4


def test_a_cyberskull_is_one_of_the_limbs() -> None:
    """A skull has STR 3 like any cyberlimb, so on a STR 1 body it lifts the
    average to ⌈(3 + 1×5) / 6⌉ = 2 — unless the settings leave the skull
    out, as Neon Anarchy's `<excludelimbslot>skull` does."""
    plain = compute(_human("skull", cyberware=[CyberwareInstall(ware_id=SKULL)])).derived
    assert plain["limb_replace"]["count"] == 1
    assert plain["totals"]["STR"] == 2

    anarchy = SettingsState(limb_count=5, exclude_limb_slot="skull")
    out = compute(_human("skull-na", cyberware=[CyberwareInstall(ware_id=SKULL)], settings=anarchy))
    assert out.derived["limb_replace"] is None
    assert out.derived["totals"]["STR"] == 1


def test_an_empty_chemical_gland_still_costs_its_base_price() -> None:
    """`20000 + (99 * Gear Cost)` — Chummer's `Gear Cost` is the chemicals
    inside, 0 for an empty gland. The unknown words used to zero the whole
    price, so Ghile Mear's two glands were free."""
    gland = _ware_id("bioware", "Chemical Gland (Internal Release or Gradual Release)")
    reservoir = _ware_id("bioware", "Chemical Gland (Weapon Reservoir)")
    out = compute(_human("gland", bioware=[CyberwareInstall(ware_id=gland), CyberwareInstall(ware_id=reservoir)]))
    prices = {row["name"]: row["nuyen"] for row in out.derived["bioware"]}
    assert prices["Chemical Gland (Internal Release or Gradual Release)"] == 20000
    assert prices["Chemical Gland (Weapon Reservoir)"] == 24000


def _limb_arm(settings: SettingsState | None = None, str_rating: int = 3) -> CharacterState:
    return CharacterState(
        id="limb-bonus-cap",
        name="LimbBonusCap",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        cyberware=[
            CyberwareInstall(id="arm1", ware_id=ARM),
            CyberwareInstall(ware_id=ENHANCED_STR, rating=str_rating, parent_id="arm1"),
        ],
        settings=settings or SettingsState(),
    )


def test_cyberlimb_enhancement_is_held_to_the_settings_bonus_cap() -> None:
    def arm_str(settings: SettingsState | None) -> int:
        out = compute(_limb_arm(settings))
        return int(next(item for item in out.derived["cyberware"] if item["id"] == "arm1")["limb_str"])

    assert arm_str(None) == 6  # base 3 + Enhanced 3, under Chummer's cap of 4
    assert arm_str(SettingsState(cyberlimb_attribute_bonus_cap=1)) == 4


def test_redliner_shares_the_cyberlimb_bonus_cap() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    state = CharacterState(
        id="redliner-cap",
        name="RedlinerCap",
        priorities=Priorities(Heritage="C", Attributes="B", Talent="E", Skills="D", Resources="A"),
        metatype="Human",
        attributes=attrs,
        quality_ids=[REDLINER],
        cyberware=[
            CyberwareInstall(id="arm1", ware_id=ARM, side="Left"),
            CyberwareInstall(ware_id=CUSTOM_STR, rating=6, parent_id="arm1"),
            CyberwareInstall(id="arm2", ware_id=ARM, side="Right"),
            CyberwareInstall(ware_id=CUSTOM_STR, rating=6, parent_id="arm2"),
        ],
        settings=SettingsState(cyberlimb_attribute_bonus_cap=0),
    )
    out = compute(state)
    arms = [item for item in out.derived["cyberware"] if item["ware_id"] == ARM]
    assert all(item["limb_str"] == 6 for item in arms)


def test_dont_use_cyberlimb_calculation_keeps_the_meat_strength() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    ware = []
    for i, limb in enumerate((ARM, ARM, LEG, LEG, TORSO)):
        ware.append(CyberwareInstall(id=f"limb{i}", ware_id=limb))
        ware.append(CyberwareInstall(ware_id=CUSTOM_STR, rating=6, parent_id=f"limb{i}"))
    state = CharacterState(
        id="no-limb-calc",
        name="NoLimbCalc",
        priorities=Priorities(),
        metatype="Human",
        attributes=attrs,
        cyberware=ware,
        settings=SettingsState(dont_use_cyberlimb_calculation=True),
    )
    out = compute(state)
    assert out.derived["limb_replace"] is None
    assert out.derived["totals"]["STR"] == 1
