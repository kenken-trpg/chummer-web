from app.data_loader import catalog
from app.engine import compute, default_attributes, find_metatype, resolve_skill_mods, selectskill_options, spell_drain_value
from app.improvements import collect_effects
from app.models import AdeptPowerInstall, CharacterOptions, CharacterState, CyberwareInstall, Priorities, QiFocusInstall

DATAJACK = "47c48542-48c3-417e-91f0-b5a456183f05"
MUSCLE = "46f80a44-80ae-41d7-a7c8-a119c4cff70f"
WIRED = "bea0ded3-821f-449c-9507-815088f68b86"
EYES = "8e414ade-2764-4dc7-bdc4-83bb4a086034"
FLARE = "5921a6ac-1e20-483b-b210-dc84a14d3045"
ARM = "df01eed6-a019-4198-b88d-4ba8f9aaefdf"
LIMB_ARMOR = "8ea736c6-5a90-471c-9320-18432ec9aaf0"
OCULAR_DRONE = "fde2bfc3-c7a2-435e-a220-4896f49d8ca9"
ORTHOSKIN = "96e4809a-71e6-4b98-9740-c6c44bc33aa9"
TONER = "69ab0255-a76b-4190-a8be-0473fed231ef"
SYNAPTIC = "4a4e1079-5872-4f3f-a450-48c30a5504f3"
CEREBRAL = "81b40aa8-98d1-4a5d-89d6-9b6d438006da"
MNEMONIC = "b2289ebe-4bb0-49d0-a151-38fc1261bba8"
PHEROMONES = "2faac78a-ab32-4541-ad9c-3ef6c1b2cd84"
SYNTHACARDIUM = "109b0a32-320f-41c5-9acb-c49308525ce0"
GLAND = "abdbc210-c1fa-45f1-9840-4f78d9eb8867"
RESERVOIR = "d2064cf2-e9f7-479f-92cc-7da7c6024121"
WEBBING = "4a939488-bd12-42f9-847f-1034fc3b4154"
DRAGON_HIDE = "8aa2590f-1fc5-4706-a7b9-9eec3db4fab9"
CUSTOM_STR = "7d61f860-0637-4214-914d-c68022361d24"
CUSTOM_AGI = "7afb23c7-435f-450c-9d1c-f7a0e7e631a6"
ENHANCED_STR = "a9f4efd4-b86c-4e90-b0f7-aefa32c3b9de"
LEG = "c7b88f7e-4e3c-4c29-9f86-a4e244ec5066"
TORSO = "48e490fb-fe6a-482c-a47d-40cb04985897"
HAND = "cc503281-ff05-4e22-9121-09116a4a8306"
SKULL = "ea676290-1859-4a56-86f8-a3fb90decc32"


def test_human_derived_stats() -> None:
    state = CharacterState(
        id="test",
        name="Test",
        priorities=Priorities(Heritage="C", Attributes="A", Talent="E", Skills="B", Resources="D"),
        metatype="Human",
        attributes={
            "BOD": 3,
            "AGI": 5,
            "REA": 4,
            "STR": 3,
            "WIL": 3,
            "LOG": 3,
            "INT": 5,
            "CHA": 3,
            "EDG": 3,
            "MAG": 0,
            "RES": 0,
            "ESS": 6,
        },
    )
    out = compute(state)
    totals = out.derived["totals"]
    assert totals["BOD"] == 3
    assert out.derived["limits"]["physical"] == 6
    assert out.derived["condition_monitor"]["physical"] == 10
    assert out.derived["condition_monitor"]["stun"] == 10
    assert out.derived["initiative"]["value"] == 9
    assert out.derived["essence"] == 6
    assert out.derived["karma"]["remaining"] == 25


def test_elf_priority_does_not_charge_xml_karma() -> None:
    state = CharacterState(
        id="elf",
        name="Elf",
        priorities=Priorities(Heritage="C", Attributes="A", Talent="E", Skills="B", Resources="D"),
        metatype="Elf",
        attributes=default_attributes(find_metatype("Elf", None)),
    )
    out = compute(state)
    assert out.derived["karma"]["remaining"] == 25
    assert out.derived["errors"] == []


def test_magician_a_starts_at_magic_six_without_special_cost() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    attrs["MAG"] = 0
    state = CharacterState(
        id="mage",
        name="Mage",
        priorities=Priorities(Heritage="C", Attributes="B", Talent="A", Skills="D", Resources="E"),
        metatype="Human",
        talent="Magician",
        attributes=attrs,
    )
    out = compute(state)
    assert out.derived["totals"]["MAG"] == 6
    assert out.derived["totals"]["RES"] == 0
    assert out.derived["points"]["special"]["used"] == 0
    assert "MAG" in out.derived["enabled_tabs"]
    assert out.derived["errors"] == []


def test_technomancer_does_not_charge_resonance_baseline() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    state = CharacterState(
        id="techno",
        name="Techno",
        priorities=Priorities(Heritage="C", Attributes="B", Talent="C", Skills="A", Resources="E"),
        metatype="Human",
        talent="Technomancer",
        attributes=attrs,
    )
    out = compute(state)
    assert out.derived["totals"]["RES"] == 3
    assert out.derived["totals"]["MAG"] == 0
    assert out.derived["points"]["special"]["used"] == 0
    assert "RES" in out.derived["enabled_tabs"]


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


def test_essence_loss_reduces_magic() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    state = CharacterState(
        id="mageware",
        name="Mageware",
        priorities=Priorities(Heritage="C", Attributes="B", Talent="A", Skills="D", Resources="E"),
        metatype="Human",
        talent="Magician",
        attributes=attrs,
        cyberware=[CyberwareInstall(ware_id=DATAJACK)],
    )
    out = compute(state)
    assert out.derived["totals"]["MAG"] == 5
    assert out.derived["essence"] == 5.9


def test_unknown_bonus_does_not_crash() -> None:
    effects = collect_effects(
        [
            (
                "Dummy",
                [
                    {"tag": "notarealbonus", "value": "1"},
                    {"tag": "armor", "value": "2"},
                ],
            )
        ]
    )
    assert effects["armor"] == 2
    assert effects["unimplemented"][0]["tag"] == "notarealbonus"


def test_cybereyes_include_image_link() -> None:
    state = CharacterState(
        id="eyes",
        name="Eyes",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        cyberware=[CyberwareInstall(ware_id=EYES, rating=1)],
    )
    out = compute(state)
    names = {item["name"] for item in out.derived["cyberware"]}
    assert "Image Link" in names
    assert out.derived["essence"] == 5.8
    assert out.derived["nuyen_spent"] == 4000
    eyes = next(item for item in out.derived["cyberware"] if item["ware_id"] == EYES)
    assert eyes["capacity_used"] == 0
    assert eyes["capacity_max"] == 4
    link = next(item for item in out.derived["cyberware"] if item["name"] == "Image Link")
    assert link["included"]
    assert link["essence"] == 0
    assert link["nuyen"] == 0


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


def test_limb_armor_uses_arm_capacity() -> None:
    state = CharacterState(
        id="arm",
        name="Arm",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        cyberware=[
            CyberwareInstall(id="arm1", ware_id=ARM),
            CyberwareInstall(ware_id=LIMB_ARMOR, rating=2, parent_id="arm1"),
        ],
    )
    out = compute(state)
    assert out.derived["essence"] == 5.0
    assert out.derived["armor"] == 2
    assert out.derived["nuyen_spent"] == 21000
    arm = next(item for item in out.derived["cyberware"] if item["id"] == "arm1")
    assert arm["capacity_used"] == 2
    assert arm["capacity_max"] == 15
    assert out.derived["condition_monitor"]["physical"] == 10


def test_capacity_overflow_is_reported() -> None:
    state = CharacterState(
        id="overflow",
        name="Overflow",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        cyberware=[
            CyberwareInstall(id="eyes1", ware_id=EYES, rating=1),
            CyberwareInstall(ware_id=OCULAR_DRONE, parent_id="eyes1"),
        ],
    )
    out = compute(state)
    assert any("容量超過" in err for err in out.derived["errors"])


def test_orthoskin_adds_armor_and_essence() -> None:
    state = CharacterState(
        id="ortho",
        name="Ortho",
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        bioware=[CyberwareInstall(ware_id=ORTHOSKIN, rating=2)],
    )
    out = compute(state)
    assert out.derived["essence"] == 5.5
    assert out.derived["armor"] == 2
    assert out.derived["nuyen_spent"] == 12000
    assert out.derived["essence_lost_bio"] == 0.5


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


def test_human_customized_strength_uses_racial_min() -> None:
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
    assert custom["rating_min"] == 2
    assert custom["rating_max"] == 6
    assert custom["rating"] == 3
    assert custom["nuyen"] == 10000
    arm = next(item for item in out.derived["cyberware"] if item["id"] == "arm1")
    assert arm["limb_str"] == 3
    assert arm["limb_agi"] == 1
    assert out.derived["nuyen_spent"] == 25000
    assert out.derived["ware_ranges"][CUSTOM_STR] == {"min": 2, "max": 6}


def test_troll_customized_strength_starts_at_six() -> None:
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
    assert custom["rating_min"] == 6
    assert custom["rating_max"] == 10
    assert custom["rating"] == 6
    assert custom["nuyen"] == 5000
    arm = next(item for item in out.derived["cyberware"] if item["id"] == "arm1")
    assert arm["limb_str"] == 6
    assert arm["limb_agi"] == 1


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
    assert custom["nuyen"] == 15000
    arm = next(item for item in out.derived["cyberware"] if item["id"] == "arm1")
    assert arm["limb_str"] == 3
    assert arm["limb_agi"] == 4
    assert arm["capacity_used"] == 2


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
    assert out.derived["limb_replace"]["parts"] == 5
    assert out.derived["totals"]["STR"] == 2
    assert out.derived["limb_replace"]["meat_str"] == 1


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
    assert any("左の腕が重複" in err for err in out.derived["errors"])
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
    assert arm["limb_str"] == 3
    assert arm["limb_agi"] == 3


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
    assert any("Muscle Replacement" in warn for warn in out.derived["warnings"])
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
    assert any("Muscle Toner" in warn for warn in out.derived["warnings"])


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
    assert any("Used" in warn and "Synaptic Booster" in warn for warn in out.derived["warnings"])


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
    assert any("Orthoskin" in warn for warn in out.derived["warnings"])
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
    assert not any("Orthoskin が必要" in warn for warn in out.derived["warnings"])


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


def test_skill_group_exclude_is_honored() -> None:
    effects = collect_effects(
        [
            (
                "Dummy",
                [{"tag": "skillgroup", "fields": {"name": "Athletics", "bonus": "2", "exclude": "Running"}}],
            )
        ]
    )
    mods = resolve_skill_mods(catalog()["skills"], effects, {})
    assert mods["skill_bonus"]["Gymnastics"] == 2
    assert "Running" not in mods["skill_bonus"]


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
    assert out.derived["warnings"] == []


ENHANCED_ARTICULATION = "dfada66f-73f7-4648-aff4-6b6bce25f84c"
REFLEX_RECORDER = "17a6ba49-c21c-461b-9830-3beae8a237fc"
VOICE_MODULATOR = "ebc25387-655f-4a24-8ae7-81548c097dac"
APTITUDE = "58e3d62a-2073-4af5-b8e0-00c446b3a5ab"
CATLIKE = "84305e09-f8d5-4a82-8257-0119b8c3f926"
LOSS_OF_CONFIDENCE = "c9cd05ad-cd3c-451e-8285-e0fb1d95ebc1"


def _human(cid: str, **kwargs: object) -> CharacterState:
    return CharacterState(
        id=cid,
        name=cid,
        priorities=Priorities(),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        **kwargs,  # type: ignore[arg-type]
    )


def test_enhanced_articulation_adds_escape_artist() -> None:
    out = compute(_human("articulation", bioware=[CyberwareInstall(ware_id=ENHANCED_ARTICULATION)]))
    assert out.derived["skill_bonus"]["Escape Artist"] == 1
    assert out.derived["limits"]["physical"] == 3


def test_catlike_adds_sneaking() -> None:
    out = compute(_human("catlike", quality_ids=[CATLIKE]))
    assert out.derived["skill_bonus"]["Sneaking"] == 2
    assert out.derived["skill_pick_slots"] == []


def test_voice_modulator_rating_adds_impersonation() -> None:
    out = compute(_human("voice", cyberware=[CyberwareInstall(ware_id=VOICE_MODULATOR, rating=2)]))
    assert out.derived["skill_bonus"]["Impersonation"] == 2


def test_reflex_recorder_warns_until_skill_picked() -> None:
    out = compute(_human("recorder-empty", bioware=[CyberwareInstall(id="rec1", ware_id=REFLEX_RECORDER)]))
    assert any("Reflex Recorder のスキルを選んでください" in warn for warn in out.derived["warnings"])
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
    assert not any("スキルを選んでください" in warn for warn in out.derived["warnings"])
    assert out.derived["skill_pick_slots"][0]["picked"] == "Gymnastics"


def test_reflex_recorder_rejects_invalid_pick() -> None:
    out = compute(
        _human(
            "recorder-bad",
            bioware=[CyberwareInstall(id="rec1", ware_id=REFLEX_RECORDER)],
            skill_picks={"ware:rec1:0": "Software"},
        )
    )
    assert any("スキル指定が無効" in warn for warn in out.derived["warnings"])
    assert out.derived["skill_bonus"].get("Software", 0) == 0


def test_aptitude_raises_skill_max() -> None:
    out = compute(
        _human(
            "aptitude",
            quality_ids=[APTITUDE],
            skills={"Pistols": 7},
            skill_picks={"quality:58e3d62a-2073-4af5-b8e0-00c446b3a5ab:0": "Pistols"},
        )
    )
    assert out.derived["skill_max_bonus"]["Pistols"] == 1
    assert out.derived["skill_totals"]["Pistols"] == 7
    assert out.derived["skill_bonus"].get("Pistols", 0) == 0


def test_loss_of_confidence_requires_rating_four() -> None:
    out = compute(
        _human(
            "confidence",
            quality_ids=[LOSS_OF_CONFIDENCE],
            skills={"Gymnastics": 4},
            skill_picks={"quality:c9cd05ad-cd3c-451e-8285-e0fb1d95ebc1:0": "Gymnastics"},
        )
    )
    assert out.derived["skill_bonus"]["Gymnastics"] == -2
    blocked = compute(
        _human(
            "confidence-low",
            quality_ids=[LOSS_OF_CONFIDENCE],
            skills={"Gymnastics": 3},
            skill_picks={"quality:c9cd05ad-cd3c-451e-8285-e0fb1d95ebc1:0": "Gymnastics"},
        )
    )
    assert any("スキル指定が無効" in warn for warn in blocked.derived["warnings"])


def test_selectskill_options_limit_to_physical_attributes() -> None:
    spec = {
        "limittoattribute": "BOD,AGI,REA,STR",
        "knowledgeskills": False,
        "minimumrating": 0,
    }
    options = selectskill_options(spec, catalog()["skills"], {})
    assert "Gymnastics" in options
    assert "Pistols" in options
    assert "Software" not in options
    assert "Negotiation" not in options


IMPROVED_REFLEXES = "fea9e769-5f2c-4bae-9610-56c0825e145a"
IMPROVED_ABILITY = "75821fb7-a180-4012-aa16-daa92ac3bb63"
IMPROVED_PHYS = "901d2af5-246a-447a-a8e2-b2e8c10593df"


def _adept(cid: str, letter: str = "B", **kwargs: object) -> CharacterState:
    attrs = default_attributes(find_metatype("Human", None))
    return CharacterState(
        id=cid,
        name=cid,
        priorities=Priorities(
            Heritage="C",
            Attributes="A",
            Talent=letter,
            Skills="B" if letter == "D" else "D",
            Resources="E",
        ),
        metatype="Human",
        talent="Adept",
        attributes=attrs,
        **kwargs,  # type: ignore[arg-type]
    )


def test_adept_b_has_six_power_points() -> None:
    out = compute(_adept("adept-b"))
    assert out.derived["totals"]["MAG"] == 6
    assert out.derived["power_points"]["max"] == 6
    assert out.derived["power_points"]["used"] == 0
    assert "adept" in out.derived["enabled_tabs"]


def test_adept_essence_loss_reduces_power_points() -> None:
    out = compute(_adept("adept-ess", cyberware=[CyberwareInstall(ware_id=DATAJACK)]))
    assert out.derived["totals"]["MAG"] == 5
    assert out.derived["power_points"]["max"] == 5


def test_improved_reflexes_rating_two_costs_two_point_five() -> None:
    out = compute(
        _adept(
            "reflexes",
            adept_powers=[AdeptPowerInstall(power_id=IMPROVED_REFLEXES, rating=2)],
        )
    )
    assert out.derived["power_points"]["used"] == 2.5
    assert out.derived["totals"]["REA"] == 3
    assert out.derived["initiative"]["dice"] == 3


def test_improved_physical_attribute_raises_agility() -> None:
    out = compute(
        _adept(
            "ipa",
            adept_powers=[AdeptPowerInstall(power_id=IMPROVED_PHYS, rating=2, extra="AGI")],
        )
    )
    assert out.derived["totals"]["AGI"] == 3
    assert out.derived["power_points"]["used"] == 2


def test_improved_ability_adds_dice_not_rating() -> None:
    out = compute(
        _adept(
            "ability",
            adept_powers=[AdeptPowerInstall(power_id=IMPROVED_ABILITY, rating=2, extra="Gymnastics")],
        )
    )
    assert out.derived["skill_bonus"]["Gymnastics"] == 2
    assert out.derived["skill_totals"].get("Gymnastics", 0) == 0
    assert out.derived["power_points"]["used"] == 1


def test_adept_power_overspend_is_an_error() -> None:
    out = compute(
        _adept(
            "overspend",
            letter="D",
            adept_powers=[AdeptPowerInstall(power_id=IMPROVED_REFLEXES, rating=2)],
        )
    )
    assert out.derived["totals"]["MAG"] == 2
    assert any("パワー点" in err for err in out.derived["errors"])


def test_mystic_adept_buys_power_points_with_karma() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    out = compute(
        CharacterState(
            id="mystic",
            name="mystic",
            priorities=Priorities(Heritage="C", Attributes="A", Talent="C", Skills="B", Resources="E"),
            metatype="Human",
            talent="Mystic Adept",
            attributes=attrs,
            mystic_pp=2,
        )
    )
    assert out.derived["power_points"]["max"] == 2
    assert out.derived["karma"]["spent"] == 10
    assert out.derived["karma"]["remaining"] == 15
    assert "adept" in out.derived["enabled_tabs"]


COMBAT_SENSE = "76337564-7688-497f-84f9-302c6ece10fe"
WARRIOR_WAY = "32d0d753-9dad-4074-ab38-2d1ff5069a6a"
MAGICIAN_WAY = "64165b48-d67e-4bb8-b662-ca45fbf5b3c0"
ATHLETE_WAY = "3f536570-2f0c-40b1-a056-d310e29e983d"
BEAST_WAY = "2e7424d3-5d11-4c9d-ba92-f0431bb86786"
MENTOR_SPIRIT = "ced3fecf-2277-4b20-b1e0-894162ca9ae2"
BEAR = "136a3dc5-d9c4-45ad-bc24-705f54692590"
RAPID_HEALING = "4676b6f7-120d-4344-81ac-5922445a521b"
LIGHT_BODY = "ce7df757-792e-4fac-a86e-6b587586deb2"
AIR_WALKING = "8dc0a8e3-535a-4935-8c90-2079666e6a01"
ADEPT_SPELL = "87f0f97d-cbcf-4427-9259-baf376c9f55a"


def test_warrior_way_discounts_combat_sense() -> None:
    out = compute(
        _adept(
            "way-cs",
            quality_ids=[WARRIOR_WAY],
            adept_powers=[AdeptPowerInstall(power_id=COMBAT_SENSE, rating=1, discounted=True)],
        )
    )
    assert out.derived["power_points"]["used"] == 0.25
    assert out.derived["way_discount"]["used"] == 0.25
    assert out.derived["way_discount"]["max"] == 2
    assert out.derived["karma"]["spent"] == 20


def test_combat_sense_without_discount_is_half_point() -> None:
    out = compute(
        _adept(
            "cs-full",
            quality_ids=[WARRIOR_WAY],
            adept_powers=[AdeptPowerInstall(power_id=COMBAT_SENSE, rating=1, discounted=False)],
        )
    )
    assert out.derived["power_points"]["used"] == 0.5


def test_magician_way_can_discount_combat_sense() -> None:
    out = compute(
        _adept(
            "mage-way",
            quality_ids=[MAGICIAN_WAY],
            adept_powers=[AdeptPowerInstall(power_id=COMBAT_SENSE, rating=1, discounted=True)],
        )
    )
    assert out.derived["power_points"]["used"] == 0.25


def test_bear_mentor_gives_free_rapid_healing() -> None:
    out = compute(
        _adept(
            "bear",
            quality_ids=[MENTOR_SPIRIT],
            mentor_id=BEAR,
        )
    )
    assert out.derived["needs_mentor"] is True
    assert out.derived["mentor"]["name"] == "Bear"
    assert out.derived["damage_resistance"] == 2
    assert out.derived["power_points"]["used"] == 0
    names = {item["name"]: item for item in out.derived["adept_powers"]}
    assert names["Rapid Healing"]["free_levels"] == 1
    assert names["Rapid Healing"]["cost"] == 0
    assert out.derived["karma"]["spent"] == 5


def test_beasts_way_grants_free_mentor_spirit() -> None:
    out = compute(
        _adept(
            "beast-way",
            quality_ids=[BEAST_WAY],
            mentor_id=BEAR,
        )
    )
    assert out.derived["needs_mentor"] is True
    assert out.derived["karma"]["spent"] == 20
    assert any(q["id"] == MENTOR_SPIRIT for q in out.derived["qualities"])


def test_air_walking_costs_two_karma() -> None:
    out = compute(
        _adept(
            "air-walk",
            quality_ids=[ATHLETE_WAY],
            adept_powers=[AdeptPowerInstall(power_id=LIGHT_BODY, rating=1)],
            adept_enhancements=[AIR_WALKING],
        )
    )
    assert out.derived["karma"]["spent"] == 22
    assert any(item["name"] == "Air Walking" for item in out.derived["enhancements"])
    assert not any("Air Walking" in warn for warn in out.derived["warnings"])


def test_adept_spell_selects_stunbolt() -> None:
    out = compute(
        _adept(
            "spell",
            adept_powers=[AdeptPowerInstall(power_id=ADEPT_SPELL, extra="Stunbolt")],
        )
    )
    assert out.derived["power_points"]["used"] == 1
    row = next(item for item in out.derived["adept_powers"] if item["name"] == "Adept Spell")
    assert row["extra"] == "Stunbolt"
    assert row["select"] == "spell"
    assert "Spellcasting" in out.derived["unlock_skills"]
    assert row["spell"]["dv"] == "F-3"
    assert row["spell"]["force"] == 6
    assert row["spell"]["drain"] == 3
    assert row["spell"]["drain_code"] == "S"
    assert row["spell"]["resist_attrs"] == "WIL+INT"


def test_qi_focus_binds_combat_sense() -> None:
    out = compute(
        _adept(
            "qi-cs",
            qi_foci=[QiFocusInstall(power_id=COMBAT_SENSE, rating=2, power_rating=1)],
        )
    )
    focus = out.derived["qi_foci"][0]
    assert focus["rating"] == 2
    assert focus["nuyen"] == 6000
    assert focus["karma"] == 2
    assert out.derived["nuyen_spent"] == 6000
    assert out.derived["karma"]["spent"] == 2
    assert out.derived["power_points"]["used"] == 0
    names = {item["name"]: item for item in out.derived["adept_powers"]}
    assert names["Combat Sense"]["free_levels"] == 1


def test_athlete_way_reduces_qi_binding_karma() -> None:
    out = compute(
        _adept(
            "qi-way",
            quality_ids=[ATHLETE_WAY],
            qi_foci=[QiFocusInstall(power_id=IMPROVED_ABILITY, rating=2, power_rating=1, extra="Gymnastics")],
        )
    )
    focus = out.derived["qi_foci"][0]
    assert focus["karma"] == 0
    assert out.derived["skill_bonus"]["Gymnastics"] == 1


def test_later_way_replaces_earlier_way() -> None:
    out = compute(
        _adept(
            "swap-way",
            quality_ids=[BEAST_WAY, WARRIOR_WAY],
            mentor_id=BEAR,
            adept_enhancements=[AIR_WALKING],
        )
    )
    names = {q["name"] for q in out.derived["qualities"]}
    assert "The Warrior's Way" in names
    assert "The Beast's Way" not in names
    assert not out.derived["needs_mentor"]
    assert out.derived["karma"]["spent"] == 20
    assert any("The Beast's Way" in warn and "両立しない" in warn for warn in out.derived["warnings"])


def test_way_swap_drops_old_enhancement() -> None:
    out = compute(
        _adept(
            "swap-enh",
            quality_ids=[ATHLETE_WAY, WARRIOR_WAY],
            adept_powers=[AdeptPowerInstall(power_id=LIGHT_BODY, rating=1)],
            adept_enhancements=[AIR_WALKING],
        )
    )
    assert "The Warrior's Way" in {q["name"] for q in out.derived["qualities"]}
    assert out.adept_enhancements == []
    assert any("Air Walking" in warn for warn in out.derived["warnings"])


def test_spell_drain_formulas() -> None:
    assert spell_drain_value("F-3", 6) == 3
    assert spell_drain_value("F", 5) == 5
    assert spell_drain_value("F-6", 6) == 2
    assert spell_drain_value("F+1", 4) == 5
    assert spell_drain_value("Special", 6) is None
    assert spell_drain_value("0", 6) == 0


def test_adept_spell_overcast_is_physical() -> None:
    out = compute(
        _adept(
            "overcast",
            adept_powers=[AdeptPowerInstall(power_id=ADEPT_SPELL, extra="Stunbolt", force=7)],
        )
    )
    row = next(item for item in out.derived["adept_powers"] if item["name"] == "Adept Spell")
    assert row["spell"]["force"] == 7
    assert row["spell"]["drain"] == 4
    assert row["spell"]["drain_code"] == "P"
