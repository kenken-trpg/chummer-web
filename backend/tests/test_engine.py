from app.data_loader import catalog, parse_avail
from app.engine import compute, default_attributes, find_metatype, resolve_skill_mods, selectskill_options, spell_drain_value, tradition_resist
from app.improvements import collect_effects
from app.models import AdeptPowerInstall, ArmorInstall, ArmorModInstall, CharacterOptions, CharacterState, CommlinkInstall, ComplexFormInstall, ContactInstall, CyberwareInstall, ExoticSkillInstall, FocusInstall, GearInstall, LifestyleInstall, InitiationChoice, MartialArtInstall, Priorities, QiFocusInstall, SpellInstall, SpiritInstall, SpriteInstall, SubmersionChoice, VehicleModInstall, WeaponAccessoryInstall, WeaponInstall, WeaponMountInstall

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
SUPRATHYROID = "d1a314d9-3b83-4d62-854d-90e3788eea83"
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


def test_priority_rejects_duplicate_letters() -> None:
    state = CharacterState(
        id="dup-pri",
        name="Dup",
        build_method="Priority",
        priorities=Priorities(Heritage="A", Attributes="A", Talent="E", Skills="B", Resources="D"),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
    )
    out = compute(state)
    assert any("各カテゴリに1つずつ" in err for err in out.derived["errors"])


def test_sum_to_ten_allows_duplicate_a() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    state = CharacterState(
        id="sum10-aa",
        name="Rich Mage",
        build_method="SumToTen",
        priorities=Priorities(Heritage="E", Attributes="C", Talent="A", Skills="E", Resources="A"),
        metatype="Human",
        talent="Magician",
        attributes=attrs,
        tradition_id="19320625-bc1a-492f-8904-da6a847e5700",
    )
    out = compute(state)
    assert out.build_method == "SumToTen"
    assert out.derived["sum_to_ten"]["used"] == 10
    assert out.derived["totals"]["MAG"] == 6
    assert out.derived["nuyen"] == 450_000
    assert not any("Sum to Ten" in err for err in out.derived["errors"])
    assert not any("各カテゴリに1つずつ" in err for err in out.derived["errors"])


def test_sum_to_ten_requires_exact_budget() -> None:
    state = CharacterState(
        id="sum10-low",
        name="Under",
        build_method="SumToTen",
        priorities=Priorities(Heritage="E", Attributes="E", Talent="E", Skills="E", Resources="E"),
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
    )
    out = compute(state)
    assert out.derived["sum_to_ten"]["used"] == 0
    assert any("Sum to Ten" in err and "0" in err for err in out.derived["errors"])


def test_karma_chargen_human_baseline_is_800() -> None:
    out = compute(
        CharacterState(
            id="karma-base",
            name="Karma Base",
            build_method="Karma",
            priorities=Priorities(),
            metatype="Human",
            attributes=default_attributes(find_metatype("Human", None)),
        )
    )
    assert out.build_method == "Karma"
    assert out.derived["karma"]["pool"] == 800
    assert out.derived["karma"]["spent"] == 0
    assert out.derived["karma_chargen"]["enabled"] is True
    assert out.derived["points"]["attributes"]["max"] == 0
    assert out.derived["errors"] == []


def test_karma_chargen_attributes_and_metatype_cost() -> None:
    attrs = default_attributes(find_metatype("Elf", None))
    attrs["BOD"] = 3  # racial min 1 → 2*5 + 3*5 = 25
    out = compute(
        CharacterState(
            id="karma-elf",
            name="Karma Elf",
            build_method="Karma",
            priorities=Priorities(),
            metatype="Elf",
            attributes=attrs,
        )
    )
    assert out.derived["karma_chargen"]["metatype"] == 40
    assert out.derived["karma_chargen"]["attributes"] == 25
    assert out.derived["karma"]["spent"] == 65


def test_karma_chargen_nuyen_conversion() -> None:
    out = compute(
        CharacterState(
            id="karma-yen",
            name="Karma Yen",
            build_method="Karma",
            priorities=Priorities(),
            metatype="Human",
            attributes=default_attributes(find_metatype("Human", None)),
            karma_nuyen=10,
        )
    )
    assert out.derived["nuyen"] == 20_000
    assert out.derived["karma_chargen"]["nuyen_karma"] == 10
    assert out.derived["karma"]["spent"] == 10


def test_karma_chargen_magician_starts_at_magic_one_without_free_spells() -> None:
    out = compute(
        CharacterState(
            id="karma-mage",
            name="Karma Mage",
            build_method="Karma",
            priorities=Priorities(),
            metatype="Human",
            talent="Magician",
            attributes=default_attributes(find_metatype("Human", None)),
            tradition_id="19320625-bc1a-492f-8904-da6a847e5700",
        )
    )
    assert out.derived["totals"]["MAG"] == 1
    assert out.derived["spell_points"]["free"] == 0
    assert "spells" in out.derived["enabled_tabs"]
    assert out.attributes["MAG"] == 1


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
    assert "spells" in out.derived["enabled_tabs"]
    assert out.derived["spell_points"]["free"] == 10
    assert any("伝統" in warn for warn in out.derived["warnings"])
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
    assert "complexforms" in out.derived["enabled_tabs"]
    assert "sprites" in out.derived["enabled_tabs"]
    assert out.derived["complex_form_points"]["free"] == 3
    assert out.derived["living_persona"]["device_rating"] == 3
    assert out.derived["fade_resist"]["attrs"] == "WIL+RES"


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
    assert out.derived["ware_attr_bonus"]["AGI"] == 2
    assert out.derived["ware_attr_limit"] == 4
    assert all("ウェア強化" not in err for err in out.derived["errors"])


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
    assert all("ウェア強化" not in err for err in out.derived["errors"])


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
    assert any("AGI" in err and "ウェア強化超過" in err and "+6" in err for err in out.derived["errors"])
    assert all("STR" not in err or "ウェア強化" not in err for err in out.derived["errors"])


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
    assert any("AGI" in err and "ウェア強化超過" in err and "+5" in err for err in out.derived["errors"])


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
    assert all("ウェア強化" not in err for err in out.derived["errors"])
    arm = next(item for item in out.derived["cyberware"] if item["id"] == "arm1")
    assert arm["limb_str"] == 6


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


def test_knowledge_points_are_intuition_plus_logic_times_two() -> None:
    out = compute(_human("know-pool"))
    assert out.derived["points"]["knowledge"] == {"used": 0, "max": 4}
    high_state = _human("know-pool-high")
    high_state.attributes["INT"] = 5
    high_state.attributes["LOG"] = 4
    high = compute(high_state)
    assert high.derived["points"]["knowledge"] == {"used": 0, "max": 18}


def test_knowledge_skills_spend_free_points_and_keep_native_free() -> None:
    state = _human(
        "know-spend",
        knowledge_skills={"Alcohol": 3, "English": 2},
        native_languages=["Japanese"],
    )
    state.attributes["INT"] = 3
    state.attributes["LOG"] = 3
    out = compute(state)
    points = out.derived["points"]["knowledge"]
    assert points == {"used": 5, "max": 12}
    assert out.derived["errors"] == []
    public = {row["name"]: row for row in out.derived["knowledge_skills"]}
    assert public["Japanese"] == {
        "name": "Japanese",
        "category": "Language",
        "attribute": "INT",
        "rating": 0,
        "native": True,
    }
    assert public["Alcohol"]["category"] == "Interest"
    assert public["Alcohol"]["rating"] == 3
    assert public["English"]["native"] is False
    assert "Japanese" not in out.knowledge_skills
    assert out.native_languages == ["Japanese"]


def test_knowledge_overspend_is_an_error() -> None:
    out = compute(_human("know-over", knowledge_skills={"Alcohol": 6, "Biology": 6, "Chemistry": 1}))
    assert out.derived["points"]["knowledge"]["used"] == 13
    assert any("知識スキル点が不足しています" in err for err in out.derived["errors"])


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


def test_second_native_language_is_warned() -> None:
    out = compute(_human("know-natives", native_languages=["Japanese", "English"]))
    assert out.native_languages == ["Japanese"]
    assert any("母語は1つまで" in warn for warn in out.derived["warnings"])
    assert out.derived["points"]["knowledge"]["used"] == 0


def test_skill_specialization_costs_one_skill_point() -> None:
    out = compute(_human("spec-pistols", skills={"Pistols": 4}, skill_specializations={"Pistols": "Semi-Automatics"}))
    assert out.derived["skill_totals"]["Pistols"] == 4
    assert out.skill_specializations["Pistols"] == "Semi-Automatics"
    assert out.derived["skill_specializations"]["Pistols"] == "Semi-Automatics"
    assert out.derived["points"]["skills"]["used"] == 5
    assert out.derived["errors"] == []
    pistols = next(item for item in catalog()["skills"]["skills"] if item["name"] == "Pistols")
    assert "Semi-Automatics" in pistols["specs"]


def test_skill_specialization_requires_the_skill() -> None:
    out = compute(_human("spec-none", skill_specializations={"Pistols": "Semi-Automatics"}))
    assert "Pistols" not in out.skill_specializations
    assert any("Pistols の専門化にはスキルが必要です" in warn for warn in out.derived["warnings"])
    assert out.derived["points"]["skills"]["used"] == 0


def test_skill_specialization_works_with_skill_group() -> None:
    out = compute(
        _human("spec-group", skill_groups={"Firearms": 2}, skill_specializations={"Pistols": "Revolvers"})
    )
    assert out.derived["skill_totals"]["Pistols"] == 2
    assert out.skill_specializations["Pistols"] == "Revolvers"
    assert out.derived["points"]["skill_groups"]["used"] == 2
    assert out.derived["points"]["skills"]["used"] == 1


def test_knowledge_specialization_costs_one_knowledge_point() -> None:
    state = _human(
        "spec-know",
        knowledge_skills={"Alcohol": 2},
        skill_specializations={"Alcohol": "Wines"},
    )
    state.attributes["INT"] = 3
    state.attributes["LOG"] = 3
    out = compute(state)
    assert out.derived["points"]["knowledge"] == {"used": 3, "max": 12}
    row = next(item for item in out.derived["knowledge_skills"] if item["name"] == "Alcohol")
    assert row["spec"] == "Wines"
    assert row["rating"] == 2
    assert out.derived["errors"] == []


def test_native_language_specialization_costs_knowledge_point() -> None:
    state = _human(
        "spec-native",
        native_languages=["Japanese"],
        skill_specializations={"Japanese": "Speak"},
    )
    state.attributes["INT"] = 3
    state.attributes["LOG"] = 3
    out = compute(state)
    assert out.derived["points"]["knowledge"] == {"used": 1, "max": 12}
    row = next(item for item in out.derived["knowledge_skills"] if item["name"] == "Japanese")
    assert row["native"] is True
    assert row["spec"] == "Speak"


def test_custom_knowledge_specialization_is_kept() -> None:
    out = compute(
        _human(
            "spec-custom",
            knowledge_skills={"Seattle Gangs": 1},
            knowledge_categories={"Seattle Gangs": "Street"},
            skill_specializations={"Seattle Gangs": "Halloweeners"},
        )
    )
    row = next(item for item in out.derived["knowledge_skills"] if item["name"] == "Seattle Gangs")
    assert row["spec"] == "Halloweeners"
    assert out.derived["points"]["knowledge"]["used"] == 2


SKILLWIRES = "60485c4e-042f-44f6-ad89-324003223f73"
ACTIVESOFT = "c4da5448-0069-447c-b3e4-4147e6bf4ca7"


def test_activesoft_can_take_a_specialization() -> None:
    out = compute(
        _mundane(
            "soft-spec",
            cyberware=[CyberwareInstall(ware_id=SKILLWIRES, rating=1)],
            gear=[GearInstall(gear_id=ACTIVESOFT, rating=1, extra="Pistols")],
            skill_specializations={"Pistols": "Semi-Automatics"},
        )
    )
    assert out.derived["skill_totals"].get("Pistols", 0) == 0
    assert out.derived["skillsoft"]["Pistols"] == 1
    assert out.skill_specializations["Pistols"] == "Semi-Automatics"
    assert out.derived["points"]["skills"]["used"] == 1
    assert out.derived["errors"] == []


def test_exotic_ranged_costs_rating_points() -> None:
    out = compute(
        _human(
            "exotic-lasers",
            exotic_skills=[ExoticSkillInstall(skill_name="Exotic Ranged Weapon", extra="Lasers", rating=4)],
        )
    )
    assert out.derived["skill_totals"]["Exotic Ranged Weapon (Lasers)"] == 4
    assert "Exotic Ranged Weapon" not in out.derived["skill_totals"]
    assert out.derived["points"]["skills"]["used"] == 4
    assert out.derived["errors"] == []
    row = out.derived["exotic_skills"][0]
    assert row["label"] == "Exotic Ranged Weapon (Lasers)"
    assert row["rating"] == 4
    assert "Lasers" in row["options"]


def test_exotic_skill_requires_target() -> None:
    out = compute(
        _human(
            "exotic-empty",
            exotic_skills=[ExoticSkillInstall(skill_name="Exotic Ranged Weapon", extra="", rating=2)],
        )
    )
    assert any("Exotic Ranged Weapon の対象を選んでください" in warn for warn in out.derived["warnings"])
    assert "Exotic Ranged Weapon" not in out.derived["skill_totals"]
    assert out.derived["points"]["skills"]["used"] == 2


def test_exotic_skill_allows_multiple_targets() -> None:
    out = compute(
        _human(
            "exotic-two",
            exotic_skills=[
                ExoticSkillInstall(skill_name="Exotic Ranged Weapon", extra="Lasers", rating=4),
                ExoticSkillInstall(skill_name="Exotic Ranged Weapon", extra="Flamethrowers", rating=2),
            ],
        )
    )
    totals = out.derived["skill_totals"]
    assert totals["Exotic Ranged Weapon (Lasers)"] == 4
    assert totals["Exotic Ranged Weapon (Flamethrowers)"] == 2
    assert out.derived["points"]["skills"]["used"] == 6
    assert out.derived["errors"] == []


def test_exotic_skill_duplicate_target_is_dropped() -> None:
    out = compute(
        _human(
            "exotic-dup",
            exotic_skills=[
                ExoticSkillInstall(skill_name="Exotic Ranged Weapon", extra="Lasers", rating=4),
                ExoticSkillInstall(skill_name="Exotic Ranged Weapon", extra="Lasers", rating=2),
            ],
        )
    )
    assert any("Exotic Ranged Weapon (Lasers) が重複しています" in warn for warn in out.derived["warnings"])
    assert out.derived["skill_totals"]["Exotic Ranged Weapon (Lasers)"] == 4
    assert len(out.derived["exotic_skills"]) == 1
    assert out.derived["points"]["skills"]["used"] == 4


def test_exotic_and_normal_skill_share_rating_six_limit() -> None:
    out = compute(
        _human(
            "exotic-six",
            skills={"Pistols": 6},
            exotic_skills=[ExoticSkillInstall(skill_name="Exotic Ranged Weapon", extra="Lasers", rating=6)],
        )
    )
    assert any("作成時にレーティング6のスキルは1つまでです" in err for err in out.derived["errors"])


def test_exotic_does_not_charge_specialization_point() -> None:
    out = compute(
        _human(
            "exotic-spec-mix",
            skills={"Pistols": 4},
            skill_specializations={"Pistols": "Semi-Automatics"},
            exotic_skills=[ExoticSkillInstall(skill_name="Exotic Ranged Weapon", extra="Lasers", rating=3)],
        )
    )
    assert out.derived["points"]["skills"]["used"] == 8
    assert out.derived["skill_totals"]["Pistols"] == 4
    assert out.derived["skill_totals"]["Exotic Ranged Weapon (Lasers)"] == 3
    assert out.skill_specializations["Pistols"] == "Semi-Automatics"
    assert out.derived["errors"] == []


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


ALLERGY_MILD = "b7841930-0c7b-4be4-b1cf-86debc41aa95"
ALLERGY_EXTREME = "8a40007a-9876-4998-a7c9-047248cfbc52"
HUMAN_LOOKING = "2844e64e-f271-4ca7-bd58-0860b2db56c9"
ASTRAL_CHAMELEON = "7d81f676-e523-4ec6-ae98-8d801f90b031"


def test_allergy_requires_target_text() -> None:
    missing = compute(_human("allergy-empty", quality_ids=[ALLERGY_MILD]))
    assert any("対象を入力してください" in err for err in missing.derived["errors"])
    filled = compute(
        _human("allergy-sun", quality_ids=[ALLERGY_MILD], quality_extras={ALLERGY_MILD: "Sunlight"})
    )
    assert filled.derived["errors"] == []
    assert filled.derived["karma"]["negative"] == {"used": 5, "max": 25}
    assert filled.derived["karma"]["remaining"] == 30


def test_negative_quality_karma_is_capped_at_25() -> None:
    out = compute(
        _human(
            "neg-cap",
            quality_ids=[ALLERGY_EXTREME, ALLERGY_MILD],
            quality_extras={ALLERGY_EXTREME: "Bees", ALLERGY_MILD: "Sunlight"},
        )
    )
    assert out.derived["karma"]["negative"]["used"] == 30
    assert any("不利クオリティから得られるカルマが上限を超えています" in err for err in out.derived["errors"])


def test_human_looking_requires_nonhuman_metatype() -> None:
    human = compute(_human("looking-human", quality_ids=[HUMAN_LOOKING]))
    assert any("Human-Looking の前提を満たしていません" in err for err in human.derived["errors"])
    elf = compute(
        CharacterState(
            id="looking-elf",
            name="looking-elf",
            priorities=Priorities(),
            metatype="Elf",
            attributes=default_attributes(find_metatype("Elf", None)),
            quality_ids=[HUMAN_LOOKING],
        )
    )
    assert elf.derived["errors"] == []


def test_astral_chameleon_requires_magic() -> None:
    mundane = compute(_human("astral-mundane", quality_ids=[ASTRAL_CHAMELEON]))
    assert any("Astral Chameleon の前提を満たしていません" in err for err in mundane.derived["errors"])
    attrs = default_attributes(find_metatype("Human", None))
    mage = compute(
        CharacterState(
            id="astral-mage",
            name="astral-mage",
            priorities=Priorities(Heritage="C", Attributes="B", Talent="A", Skills="D", Resources="E"),
            metatype="Human",
            talent="Magician",
            attributes=attrs,
            quality_ids=[ASTRAL_CHAMELEON],
        )
    )
    assert not any("前提を満たしていません" in err for err in mage.derived["errors"])


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


HERMETIC = "19320625-bc1a-492f-8904-da6a847e5700"
SHAMANIC = "8d185e0e-5f49-4992-babd-d1ac9c848f68"
STUNBOLT = "47423962-6b73-4cc3-ad4e-e8d037cf9507"


def _mage(cid: str, letter: str = "A", **kwargs: object) -> CharacterState:
    attrs = kwargs.pop("attributes", None) or default_attributes(find_metatype("Human", None))
    return CharacterState(
        id=cid,
        name=cid,
        priorities=Priorities(
            Heritage="C",
            Attributes="B" if letter == "A" else "A",
            Talent=letter,
            Skills="D",
            Resources="E",
        ),
        metatype="Human",
        talent="Magician",
        attributes=attrs,  # type: ignore[arg-type]
        **kwargs,  # type: ignore[arg-type]
    )


def _learnable_ids(count: int) -> list[str]:
    return [item["id"] for item in catalog()["spells"] if item.get("learnable")][:count]


def test_tradition_resist_hermetic() -> None:
    spec = next(item for item in catalog()["traditions"] if item["id"] == HERMETIC)
    pool, label = tradition_resist(spec, {"WIL": 5, "LOG": 6, "INT": 2, "CHA": 1})
    assert pool == 11
    assert label == "WIL+LOG"


def test_mage_stunbolt_uses_hermetic_drain() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    attrs["WIL"] = 5
    attrs["LOG"] = 4
    attrs["INT"] = 2
    out = compute(
        _mage(
            "hermetic-drain",
            attributes=attrs,
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=STUNBOLT)],
        )
    )
    row = out.derived["spells"][0]
    assert row["name"] == "Stunbolt"
    assert row["free"] is True
    assert row["karma"] == 0
    assert row["spell"]["dv"] == "F-3"
    assert row["spell"]["force"] == 6
    assert row["spell"]["drain"] == 3
    assert row["spell"]["drain_code"] == "S"
    assert row["spell"]["resist"] == 9
    assert row["spell"]["resist_attrs"] == "WIL+LOG"
    assert out.derived["tradition"]["name"] == "Hermetic"
    assert out.derived["karma"]["spent"] == 0
    assert not any("伝統" in warn for warn in out.derived["warnings"])


def test_mage_overcast_is_physical() -> None:
    out = compute(
        _mage(
            "mage-overcast",
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=STUNBOLT, force=7)],
        )
    )
    row = out.derived["spells"][0]
    assert row["spell"]["force"] == 7
    assert row["spell"]["drain"] == 4
    assert row["spell"]["drain_code"] == "P"


def test_eleventh_spell_costs_five_karma() -> None:
    ids = _learnable_ids(11)
    assert len(ids) == 11
    out = compute(
        _mage(
            "eleven",
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=sid) for sid in ids],
        )
    )
    assert out.derived["spell_points"]["used"] == 11
    assert out.derived["spell_points"]["paid"] == 1
    assert out.derived["spells"][-1]["free"] is False
    assert out.derived["spells"][-1]["karma"] == 5
    assert out.derived["karma"]["spent"] == 5
    assert out.derived["errors"] == []


def test_duplicate_spell_is_dropped() -> None:
    out = compute(
        _mage(
            "dup",
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=STUNBOLT), SpellInstall(spell_id=STUNBOLT)],
        )
    )
    assert len(out.derived["spells"]) == 1
    assert any("重複" in warn for warn in out.derived["warnings"])


def test_aspected_magician_buys_spells() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    out = compute(
        CharacterState(
            id="aspected",
            name="aspected",
            priorities=Priorities(Heritage="C", Attributes="A", Talent="B", Skills="D", Resources="E"),
            metatype="Human",
            talent="Aspected Magician",
            attributes=attrs,
            tradition_id=SHAMANIC,
            spells=[SpellInstall(spell_id=STUNBOLT)],
        )
    )
    assert out.derived["spell_points"]["free"] == 0
    assert out.derived["spells"][0]["karma"] == 5
    assert out.derived["karma"]["spent"] == 5
    assert out.derived["spells"][0]["spell"]["resist_attrs"] == "WIL+CHA"


def test_adept_has_no_spell_tab() -> None:
    out = compute(_adept("no-spells"))
    assert "spells" not in out.derived["enabled_tabs"]
    assert out.derived["spell_points"]["free"] == 0


def test_mystic_adept_spell_uses_tradition() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    attrs["WIL"] = 4
    attrs["LOG"] = 5
    out = compute(
        CharacterState(
            id="mystic",
            name="mystic",
            priorities=Priorities(Heritage="C", Attributes="B", Talent="A", Skills="D", Resources="E"),
            metatype="Human",
            talent="Mystic Adept",
            attributes=attrs,
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=STUNBOLT)],
            adept_powers=[AdeptPowerInstall(power_id=ADEPT_SPELL, extra="Stunbolt")],
        )
    )
    assert "spells" in out.derived["enabled_tabs"]
    assert "adept" in out.derived["enabled_tabs"]
    assert out.derived["spells"][0]["spell"]["resist_attrs"] == "WIL+LOG"
    adept_row = next(item for item in out.derived["adept_powers"] if item["name"] == "Adept Spell")
    assert adept_row["spell"]["resist_attrs"] == "WIL+LOG"
    assert adept_row["spell"]["resist"] == 9


WARD = "3cea53a2-7628-4009-9bc4-af2f141fc28d"
RECHARGE_REAGENTS = "e45f4b5d-8969-4e03-ae55-583beee464fc"


def test_ward_ritual_uses_free_slot() -> None:
    out = compute(
        _mage(
            "ward",
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=WARD)],
        )
    )
    row = out.derived["spells"][0]
    assert row["name"] == "Ward"
    assert row["kind"] == "ritual"
    assert row["useskill"] == "Ritual Spellcasting"
    assert row["has_force"] is True
    assert row["free"] is True
    assert row["spell"]["drain"] is None
    assert row["spell"]["dv"] == "Special"
    assert out.derived["spell_points"]["used"] == 1
    assert out.derived["karma"]["spent"] == 0


def test_enchantment_warns_for_metamagic() -> None:
    out = compute(
        _mage(
            "reagents",
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=RECHARGE_REAGENTS)],
        )
    )
    row = out.derived["spells"][0]
    assert row["name"] == "Recharge Reagents"
    assert row["kind"] == "enchantment"
    assert row["useskill"] == "Artificing"
    assert row["has_force"] is False
    assert row["spell"] is None
    assert row["free"] is True
    assert any("Geomancy" in warn for warn in out.derived["warnings"])


GEOMANCY_ART = "5b922bcf-4114-4c49-a4f3-0f3dcb45dd2f"
QUICKENING_META = "4ea558ed-0fe8-4b9e-b2fa-afffb3eb2476"
POWER_POINT_META = "406f096a-c093-4a02-b60f-002eb01a20b9"


def test_initiation_grade_one_costs_thirteen_karma() -> None:
    out = compute(
        _mage(
            "init1",
            initiate_grade=1,
            initiations=[InitiationChoice(grade=1, kind="metamagic", option_id=QUICKENING_META)],
        )
    )
    assert "initiation" in out.derived["enabled_tabs"]
    assert out.derived["initiation"]["grade"] == 1
    assert out.derived["initiation"]["karma"] == 13
    assert out.derived["karma"]["spent"] == 13
    assert out.derived["initiation"]["metamagics"][0]["name"] == "Quickening"


def test_initiation_raises_mag_max() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    attrs["MAG"] = 7
    out = compute(
        _mage(
            "init-mag",
            attributes=attrs,
            initiate_grade=1,
            initiations=[InitiationChoice(grade=1, kind="metamagic", option_id=QUICKENING_META)],
        )
    )
    assert out.derived["metatype_info"]["attributes"]["MAG"]["max"] == 7
    assert out.attributes["MAG"] == 7
    assert out.derived["totals"]["MAG"] == 7


def test_geomancy_art_clears_recharge_warning() -> None:
    out = compute(
        _mage(
            "geomancy",
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=RECHARGE_REAGENTS)],
            initiate_grade=1,
            initiations=[InitiationChoice(grade=1, kind="art", option_id=GEOMANCY_ART)],
        )
    )
    assert out.derived["initiation"]["arts"][0]["name"] == "Geomancy"
    assert not any("Geomancy" in warn for warn in out.derived["warnings"])


def test_power_point_metamagic_adds_pp() -> None:
    base = compute(_adept("pp-base"))
    out = compute(
        _adept(
            "pp-meta",
            initiate_grade=1,
            initiations=[InitiationChoice(grade=1, kind="metamagic", option_id=POWER_POINT_META)],
        )
    )
    assert out.derived["initiation"]["metamagics"][0]["name"] == "Power Point"
    assert out.derived["power_points"]["max"] == float(base.derived["power_points"]["max"]) + 1
    assert out.derived["karma"]["spent"] == 13


def test_initiation_grade_above_mag_errors() -> None:
    out = compute(_mage("init-over", initiate_grade=7))
    assert any("イニシエーション等級は魔力以下" in err for err in out.derived["errors"])


def test_ritual_and_spell_share_free_pool() -> None:
    out = compute(
        _mage(
            "mix",
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=STUNBOLT), SpellInstall(spell_id=WARD)],
        )
    )
    kinds = {item["name"]: item["kind"] for item in out.derived["spells"]}
    assert kinds["Stunbolt"] == "spell"
    assert kinds["Ward"] == "ritual"
    assert out.derived["spell_points"]["used"] == 2
    assert out.derived["karma"]["spent"] == 0


def test_enchanter_can_buy_enchantments() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    out = compute(
        CharacterState(
            id="enchanter",
            name="enchanter",
            priorities=Priorities(Heritage="C", Attributes="A", Talent="C", Skills="B", Resources="E"),
            metatype="Human",
            talent="Enchanter",
            attributes=attrs,
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=RECHARGE_REAGENTS)],
        )
    )
    assert "spells" in out.derived["enabled_tabs"]
    assert out.derived["spell_points"]["free"] == 0
    assert out.derived["spells"][0]["karma"] == 5
    assert out.derived["karma"]["spent"] == 5


def test_adept_spell_rejects_ritual() -> None:
    out = compute(
        _adept(
            "no-ritual",
            adept_powers=[AdeptPowerInstall(power_id=ADEPT_SPELL, extra="Ward")],
        )
    )
    row = next(item for item in out.derived["adept_powers"] if item["name"] == "Adept Spell")
    assert row["extra"] != "Ward"
    assert any("無効" in warn for warn in out.derived["warnings"])


SPIRIT_FIRE = "c0178bf8-1fc5-4c56-9ce1-92a3ae1adc45"
SPIRIT_BEASTS = "c5e35ac9-5737-4003-8c9e-eb016d2bccd2"
POWER_FOCUS = "62bfb38d-5515-440b-83ed-289ed926d27e"
WEAPON_FOCUS = "25b0168d-7052-4f76-b8e5-162d67b8ab6e"
SPELLCASTING_COMBAT = "2f485376-54c1-41be-8678-79cc98e04ebc"


def _mage_rich(cid: str, **kwargs: object) -> CharacterState:
    attrs = kwargs.pop("attributes", None) or default_attributes(find_metatype("Human", None))
    return CharacterState(
        id=cid,
        name=cid,
        priorities=Priorities(Heritage="E", Attributes="C", Talent="A", Skills="D", Resources="B"),
        metatype="Human",
        talent="Magician",
        attributes=attrs,  # type: ignore[arg-type]
        **kwargs,  # type: ignore[arg-type]
    )


def test_hermetic_binds_fire_spirit() -> None:
    out = compute(
        _mage(
            "bind-fire",
            tradition_id=HERMETIC,
            spirits=[SpiritInstall(spirit_id=SPIRIT_FIRE, force=3, services=2)],
        )
    )
    row = out.derived["spirits"][0]
    assert row["name"] == "Spirit of Fire"
    assert row["role"] == "combat"
    assert row["force"] == 3
    assert row["services"] == 2
    assert row["nuyen"] == 60
    assert row["attributes"]["BOD"] == 4
    assert row["attributes"]["AGI"] == 5
    assert row["attributes"]["REA"] == 6
    assert row["attributes"]["STR"] == 1
    assert row["attributes"]["INI"] == 9
    assert "Elemental Attack" in row["powers"]
    assert out.derived["nuyen_spent"] == 60
    assert "spirits" in out.derived["enabled_tabs"]


def test_shaman_rejects_fire_spirit() -> None:
    out = compute(
        _mage(
            "wrong-spirit",
            tradition_id=SHAMANIC,
            spirits=[SpiritInstall(spirit_id=SPIRIT_FIRE, force=3, services=1)],
        )
    )
    assert out.derived["spirits"] == []
    assert any("召喚できません" in warn for warn in out.derived["warnings"])


def test_spirit_force_clamps_to_magic() -> None:
    out = compute(
        _mage(
            "spirit-cap",
            tradition_id=HERMETIC,
            spirits=[SpiritInstall(spirit_id=SPIRIT_FIRE, force=12, services=9)],
        )
    )
    row = out.derived["spirits"][0]
    assert row["force"] == 6
    assert row["services"] == 6
    assert row["nuyen"] == 120


def test_enchanter_cannot_bind_spirits() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    out = compute(
        CharacterState(
            id="no-summon",
            name="no-summon",
            priorities=Priorities(Heritage="C", Attributes="A", Talent="C", Skills="B", Resources="E"),
            metatype="Human",
            talent="Enchanter",
            attributes=attrs,
            tradition_id=HERMETIC,
            spirits=[SpiritInstall(spirit_id=SPIRIT_FIRE, force=2, services=1)],
        )
    )
    assert out.derived["spirits"] == []
    assert "spirits" not in out.derived["enabled_tabs"]
    assert "foci" in out.derived["enabled_tabs"]


def test_power_focus_costs_and_boosts_magic_skills() -> None:
    out = compute(
        _mage_rich(
            "power-focus",
            tradition_id=HERMETIC,
            foci=[FocusInstall(gear_id=POWER_FOCUS, force=2)],
        )
    )
    row = out.derived["foci"][0]
    assert row["name"] == "Power Focus"
    assert row["force"] == 2
    assert row["nuyen"] == 36000
    assert row["karma"] == 2
    assert out.derived["nuyen_spent"] == 36000
    assert out.derived["karma"]["spent"] == 2
    assert out.derived["skill_bonus"]["Spellcasting"] == 2
    assert out.derived["skill_bonus"]["Summoning"] == 2
    assert out.derived["focus_limits"]["count"] == 1
    assert out.derived["focus_limits"]["force"] == 2


KATANA = "8f266b4c-4035-4ba3-aa89-3289d0f42ce1"


def test_weapon_focus_requires_target_weapon() -> None:
    out = compute(
        _mage_rich(
            "wf-empty",
            tradition_id=HERMETIC,
            foci=[FocusInstall(gear_id=WEAPON_FOCUS, force=2)],
        )
    )
    row = out.derived["foci"][0]
    assert row["needs_weapon"] is True
    assert row["weapon_type"] == "Melee"
    assert row["weapon_dice"] == 2
    assert any("対象武器を選んでください" in warn for warn in out.derived["warnings"])


def test_weapon_focus_adds_dice_to_melee_weapon() -> None:
    weapon = WeaponInstall(weapon_id=KATANA)
    out = compute(
        _mage_rich(
            "wf-katana",
            tradition_id=HERMETIC,
            weapons=[weapon],
            foci=[FocusInstall(gear_id=WEAPON_FOCUS, force=2, extra=weapon.id)],
        )
    )
    focus = out.derived["foci"][0]
    assert focus["weapon_id"] == weapon.id
    assert focus["weapon_name"] == "Katana"
    assert focus["weapon_dice"] == 2
    assert any(opt["id"] == weapon.id for opt in focus["weapon_options"])
    blade = next(item for item in out.derived["weapons"] if item["id"] == weapon.id)
    assert blade["focus_dice"] == 2
    assert out.derived["errors"] == []
    assert not any("対象武器" in warn for warn in out.derived["warnings"])


def test_weapon_focus_rejects_ranged_weapon() -> None:
    predator_id = next(item["id"] for item in catalog()["weapons"] if item["name"] == "Ares Predator V")
    weapon = WeaponInstall(weapon_id=predator_id)
    out = compute(
        _mage_rich(
            "wf-ranged",
            tradition_id=HERMETIC,
            weapons=[weapon],
            foci=[FocusInstall(gear_id=WEAPON_FOCUS, force=1, extra=weapon.id)],
        )
    )
    focus = out.derived["foci"][0]
    assert focus["weapon_id"] == ""
    assert any("Melee武器専用" in warn for warn in out.derived["warnings"])
    gun = next(item for item in out.derived["weapons"] if item["id"] == weapon.id)
    assert gun.get("focus_dice", 0) == 0


def test_spellcasting_focus_marks_combat_spells() -> None:
    out = compute(
        _mage_rich(
            "spell-focus",
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=STUNBOLT)],
            foci=[FocusInstall(gear_id=SPELLCASTING_COMBAT, force=3)],
        )
    )
    assert out.derived["foci"][0]["nuyen"] == 12000
    assert out.derived["foci"][0]["karma"] == 3
    assert out.derived["spells"][0]["focus_bonus"] == 3


def test_bound_focus_count_cannot_exceed_magic() -> None:
    out = compute(
        _mage_rich(
            "too-many-foci",
            foci=[FocusInstall(gear_id=WEAPON_FOCUS, force=1) for _ in range(7)],
        )
    )
    assert out.derived["focus_limits"]["count"] == 7
    assert any("魔力まで" in err for err in out.derived["errors"])


def test_bound_focus_force_total_cannot_exceed_magic_times_five() -> None:
    out = compute(
        _mage_rich(
            "too-much-force",
            foci=[FocusInstall(gear_id=WEAPON_FOCUS, force=6) for _ in range(6)],
        )
    )
    assert out.derived["focus_limits"]["force"] == 36
    assert any("Force合計" in err for err in out.derived["errors"])


def test_summoned_spirit_uses_summoning_test() -> None:
    out = compute(
        _mage(
            "summon-fire",
            tradition_id=HERMETIC,
            skills={"Summoning": 4},
            spirits=[SpiritInstall(spirit_id=SPIRIT_FIRE, force=3, bound=False, hits=5, opposed_hits=2)],
        )
    )
    row = out.derived["spirits"][0]
    assert row["bound"] is False
    assert row["nuyen"] == 0
    assert row["services"] == 3
    assert row["force"] == 3
    assert out.derived["nuyen_spent"] == 0
    test = row["test"]
    assert test["skill"] == "Summoning"
    assert test["pool"] == 10
    assert test["vs"] == 3
    assert test["limit"] == 3
    assert test["drain"] == 4
    assert test["drain_code"] == "S"
    assert test["net"] == 3
    assert test["missing"] is False


def test_summoned_overcast_is_physical() -> None:
    out = compute(
        _mage(
            "summon-over",
            tradition_id=HERMETIC,
            skills={"Summoning": 6},
            spirits=[SpiritInstall(spirit_id=SPIRIT_FIRE, force=7, bound=False, hits=4, opposed_hits=3)],
        )
    )
    row = out.derived["spirits"][0]
    assert row["force"] == 7
    assert row["test"]["vs"] == 7
    assert row["test"]["physical"] is True
    assert row["test"]["drain"] == 6
    assert row["test"]["drain_code"] == "P"
    assert row["services"] == 1


def test_bound_spirit_uses_binding_test() -> None:
    out = compute(
        _mage(
            "bind-test",
            tradition_id=HERMETIC,
            skills={"Binding": 3},
            spirits=[SpiritInstall(spirit_id=SPIRIT_FIRE, force=3, bound=True, hits=6, opposed_hits=2)],
        )
    )
    row = out.derived["spirits"][0]
    assert row["bound"] is True
    assert row["nuyen"] == 60
    assert row["services"] == 4
    assert row["test"]["skill"] == "Binding"
    assert row["test"]["pool"] == 9
    assert row["test"]["vs"] == 6
    assert row["test"]["drain"] == 4


def test_summon_without_skill_warns() -> None:
    out = compute(
        _mage(
            "no-summon-skill",
            tradition_id=HERMETIC,
            spirits=[SpiritInstall(spirit_id=SPIRIT_FIRE, force=1, bound=False)],
        )
    )
    assert out.derived["spirits"][0]["test"]["missing"] is True
    assert any("Summoning" in warn for warn in out.derived["warnings"])


def test_crafted_power_focus_uses_formula_and_artificing() -> None:
    out = compute(
        _mage_rich(
            "craft-power",
            skills={"Artificing": 5},
            foci=[FocusInstall(gear_id=POWER_FOCUS, force=2, crafted=True, formula_bought=True, hits=5, opposed_hits=2)],
        )
    )
    row = out.derived["foci"][0]
    assert row["crafted"] is True
    assert row["formula_nuyen"] == 9000
    assert row["reagent_nuyen"] == 40
    assert row["nuyen"] == 9040
    assert row["retail_nuyen"] == 36000
    assert row["karma"] == 2
    test = row["test"]
    assert test["skill"] == "Artificing"
    assert test["pool"] == 11
    assert test["vs"] == 4
    assert test["days"] == 2
    assert test["drain"] == 4
    assert test["net"] == 3
    assert test["missing"] is False


def test_designed_formula_skips_formula_price() -> None:
    out = compute(
        _mage_rich(
            "design-formula",
            skills={"Artificing": 4, "Arcana": 3},
            foci=[FocusInstall(gear_id=POWER_FOCUS, force=1, crafted=True, formula_bought=False)],
        )
    )
    row = out.derived["foci"][0]
    assert row["nuyen"] == 20
    assert row["formula_nuyen"] == 0
    assert row["formula_test"]["skill"] == "Arcana"
    assert row["formula_test"]["vs"] == 2
    assert row["formula_test"]["limit_name"] == "Mental"
    assert row["formula_test"]["missing"] is False


def test_craft_without_artificing_warns() -> None:
    out = compute(
        _mage_rich(
            "no-artifice",
            foci=[FocusInstall(gear_id=POWER_FOCUS, force=1, crafted=True, hits=1, opposed_hits=1)],
        )
    )
    assert out.derived["foci"][0]["test"]["missing"] is True
    assert any("Artificing" in warn for warn in out.derived["warnings"])
    assert any("失敗" in warn for warn in out.derived["warnings"])


ARMOR_JACKET = "36a4cd30-c32c-44d0-847a-0c15fb51072a"
ARMOR_VEST = "4ad1eeab-daf3-4495-a73d-fbb0ce89be5b"
HELMET = "fd6e194b-89ea-4030-9203-87341442eadb"
CHEM_PROT = "480b7c5d-758b-4833-8bfd-9487e2455f7d"
FIRE_RES = "dd246520-7306-40fb-88b4-c9cb031208fc"
INSULATION = "497b5d6b-df0c-401d-91de-42a224b1fa87"
NONCONDUCT = "0cfb049a-a1bd-4daa-96be-9468c37d9c3c"
CHEM_SEAL = "1e002d2e-cd93-4cef-a666-b6c6449f4e9f"
THERMAL_DAMPING = "ba32a6e9-4e6f-47fe-8fd7-c3194a5174d6"
RESTRICTED_GEAR = "ce939b04-5fc6-49e9-a747-9c9d1254449e"
SHOCK_FRILLS = "dbdaf817-9bfa-4938-a195-b53c63b53e7c"
SOFTWEAVE = "cf8accf5-4117-4419-ab73-957489038ab9"
GEL_PACKS = "ed43ded4-1b2f-410a-9322-166c39306d03"
FULL_BODY = "9ee80c97-9197-4dd5-baed-f77cfd2cee17"
FBA_HELMET = "71c20b15-de11-49eb-93fe-f4d7491283e3"
URBAN_EXPLORER = "d8d9154d-c8d3-4593-a408-9f5b259f0363"
UE_HELMET = "812a7926-3980-4c26-9935-5f1b66abacda"
DIVING_ARMOR = "f2aab6fa-645a-4d39-a612-91d3ee9e6bce"
META_LINK = "89a0f3c9-5ef6-41cd-981f-4ac690ee2ab3"
CUSTOM_LINK = "d63eb841-7b15-4539-9026-b90a4924aeeb"
FAIRLIGHT_CALIBAN = "1522dd91-99d9-42f9-ab19-b43e8e3c7322"
TRANSYS_AVALON = "01077e2d-4f67-428a-850d-250faad2007c"
PI_TAC_I = "b77b4cf8-8bdc-40bf-acca-f2afcca4965c"
PI_TAC_COPILOT = "d900aa9c-5914-4e5b-baa4-b4e0c0625123"
LOW_LIFESTYLE = "451eef87-d18e-4bee-a972-1ee165b08522"
LUXURY_LIFESTYLE = "4b513ac9-9eb3-471b-931b-839a04873b84"
PREDATOR = "971c711b-db32-4339-9203-865ef38f350e"
LIGHT_FIRE_70 = "67474de7-d29b-4b31-a6ae-1e2e981fa5d2"
KNIFE = "eb16de72-e646-4880-aa5b-21a5a0a2b342"
INTERNAL_SMARTGUN = "d57d2c64-1f61-4f5f-a465-8ce0dfacec6a"
APDS = "ef9c8aae-26df-4fe6-88b3-79fbb5eb77c5"
REGULAR_AMMO = "b2a0b340-c793-4322-8422-8b03d18a6fae"
GEL_ROUNDS = "0c8d16cb-6e96-4d95-8454-104a36091cf9"
SPARE_CLIP = "75ccb148-e774-429c-b854-a27816439626"
SPEED_LOADER = "f87701a0-4ea2-47db-bcac-f5b8396c369e"
SUPER_WARHAWK = "61c59a89-3c51-46b7-880a-933b29394315"
FLASH_BANG = "f4b92e14-fe1f-4be4-ad73-aed10e1f73b4"
THROWING_KNIFE_GEAR = "d9bf2003-1911-4e65-b6a1-8babb761dd85"
ANTIOCH = "504cba24-2141-4879-8062-782332e83386"
MINI_HE = "daecdfc8-15d5-4864-9e20-13e4a0dca88e"
MINI_FLASH = "f092fca8-46a9-4351-a06a-362846e6546a"
ERIKA_DECK = "b6d1476d-a08c-43fc-be0e-68ca9330a43e"
RADIO_SHACK_RCC = "9d410862-89ae-408c-8342-82f7e6c1ae8f"
GLASSES = "b218dbd1-5706-4d9e-a6a7-ab9b658c3acd"
BINOCULARS = "1c6db3ed-a360-40b4-8118-9aca9d96001c"
FLARE_COMP = "7fc23c2f-b41a-46b0-9ed7-9dc93986fab3"
IMAGE_LINK = "2886d77a-1321-4a29-aec8-8040b9c5776f"
EARBUDS = "5d69d002-c33d-4d0f-9c4d-d78db4d78e5d"
SPATIAL = "3f086e04-8de6-4d4e-a503-a19cba8295f5"
BROWSE = "b3c0a6bd-e086-4971-be77-dc9a9cb2e174"
ARMOR_PROG = "a1e4b783-0751-43eb-b5bd-ee00f84b7bb3"
EXPLOIT = "67ea7c0c-1703-412b-80d3-9c23cc6d8291"
CLEARSIGHT = "149a8dd2-dfef-473f-94a4-1bdd77e4f855"
SENSOR_ARRAY = "2ca81a10-d0f7-4b39-ac93-a84f2f69f9d9"
SINGLE_SENSOR = "2d4edef2-2891-4383-83f6-81f05cfbd046"
HANDHELD_HOUSING = "49bbc9d3-860d-47db-b4bc-8417f5b6ab65"
ATMOSPHERE = "5c3b9966-ad7e-42e3-b0e0-f656021784cf"
MOTION_SENSOR = "e853967a-a2b8-4d89-9a97-773034489a16"


def _mundane(cid: str, **kwargs: object) -> CharacterState:
    return CharacterState(
        id=cid,
        name=cid,
        metatype="Human",
        attributes=default_attributes(find_metatype("Human", None)),
        **{"priorities": Priorities(), **kwargs},
    )


def test_armor_jacket_adds_armor_and_nuyen() -> None:
    out = compute(_mundane("jacket", armor=[ArmorInstall(armor_id=ARMOR_JACKET)]))
    assert out.derived["armor"] == 12
    assert out.derived["nuyen_spent"] == 1000
    assert out.derived["worn_armor"] == "Armor Jacket"
    assert out.derived["errors"] == []


def test_helmet_stacks_on_jacket() -> None:
    out = compute(
        _mundane(
            "helm",
            armor=[ArmorInstall(armor_id=ARMOR_JACKET), ArmorInstall(armor_id=HELMET)],
        )
    )
    assert out.derived["armor"] == 14
    assert out.derived["nuyen_spent"] == 1100


def test_two_armor_suits_use_highest() -> None:
    out = compute(
        _mundane(
            "stack",
            armor=[ArmorInstall(armor_id=ARMOR_JACKET), ArmorInstall(armor_id=ARMOR_VEST)],
        )
    )
    assert out.derived["armor"] == 12
    assert out.derived["nuyen_spent"] == 1500
    assert any("一番高い" in warn for warn in out.derived["warnings"])


def test_orthoskin_stacks_with_jacket() -> None:
    out = compute(
        _mundane(
            "skin-jacket",
            armor=[ArmorInstall(armor_id=ARMOR_JACKET)],
            bioware=[CyberwareInstall(ware_id=ORTHOSKIN, rating=2)],
        )
    )
    assert out.derived["armor"] == 14
    assert out.derived["nuyen_spent"] == 13000


def test_chemical_protection_on_jacket() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "chem-jacket",
            armor=[jacket],
            armor_mods=[ArmorModInstall(mod_id=CHEM_PROT, parent_id=jacket.id, rating=2)],
        )
    )
    row = out.derived["armor_items"][0]
    assert out.derived["armor"] == 12
    assert out.derived["nuyen_spent"] == 1500
    assert row["capacity_used"] == 2
    assert row["capacity_max"] == 12
    assert row["mods"][0]["nuyen"] == 500
    assert row["mods"][0]["special_armor"]["toxin_contact"] == 2
    assert row["mods"][0]["special_armor"]["pathogen_contact"] == 2
    assert out.derived["special_armor"]["toxin_contact"] == 2
    assert out.derived["special_armor"]["pathogen_contact"] == 2
    assert out.derived["errors"] == []


def test_fire_resistance_adds_special_armor() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "fire-jacket",
            armor=[jacket],
            armor_mods=[ArmorModInstall(mod_id=FIRE_RES, parent_id=jacket.id, rating=2)],
        )
    )
    assert out.derived["armor"] == 12
    assert out.derived["special_armor"]["fire"] == 2
    assert out.derived["armor_items"][0]["mods"][0]["special_armor"]["fire"] == 2
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "firearmor" not in tags


def test_insulation_and_nonconductivity_add_special_armor() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "insul-jacket",
            armor=[jacket],
            armor_mods=[
                ArmorModInstall(mod_id=INSULATION, parent_id=jacket.id, rating=3),
                ArmorModInstall(mod_id=NONCONDUCT, parent_id=jacket.id, rating=1),
            ],
        )
    )
    assert out.derived["armor"] == 12
    assert out.derived["special_armor"]["cold"] == 3
    assert out.derived["special_armor"]["electricity"] == 1


def test_chemical_seal_grants_contact_and_inhalation_immunity() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "seal-jacket",
            armor=[jacket],
            armor_mods=[ArmorModInstall(mod_id=CHEM_SEAL, parent_id=jacket.id)],
        )
    )
    immunities = out.derived["special_armor"]["immunities"]
    assert immunities["toxin_contact"] is True
    assert immunities["toxin_inhalation"] is True
    assert immunities["pathogen_contact"] is True
    assert immunities["pathogen_inhalation"] is True
    assert out.derived["armor_items"][0]["mods"][0]["special_armor"]["immunities"]["toxin_contact"] is True


def test_thermal_damping_adds_sneaking_physical_limit() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    baseline = compute(_mundane("damp-base", armor=[jacket]))
    out = compute(
        _mundane(
            "damp-jacket",
            armor=[jacket],
            armor_mods=[ArmorModInstall(mod_id=THERMAL_DAMPING, parent_id=jacket.id, rating=2)],
        )
    )
    row = out.derived["armor_items"][0]["mods"][0]
    assert out.derived["armor"] == 12
    assert out.derived["nuyen_spent"] == 2000
    assert row["nuyen"] == 1000
    assert row["capacity_cost"] == 2
    assert row["limit_modifiers"] == [
        {
            "limit": "physical",
            "value": 2,
            "condition": "LimitCondition_TestSneakingThermal",
            "condition_label": "熱視覚／熱センサーに対する潜伏",
            "source": "",
        }
    ]
    assert out.derived["limit_modifiers"] == [
        {
            "limit": "physical",
            "value": 2,
            "condition": "LimitCondition_TestSneakingThermal",
            "condition_label": "熱視覚／熱センサーに対する潜伏",
            "source": "Thermal Damping",
        }
    ]
    assert out.derived["limits"]["physical"] == baseline.derived["limits"]["physical"]
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "limitmodifier" not in tags
    assert out.derived["errors"] == []


def test_unequipped_armor_drops_thermal_damping_limit() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET, equipped=False)
    out = compute(
        _mundane(
            "unequip-damp",
            armor=[jacket],
            armor_mods=[ArmorModInstall(mod_id=THERMAL_DAMPING, parent_id=jacket.id, rating=2)],
        )
    )
    assert out.derived["limit_modifiers"] == []
    assert out.derived["armor_items"][0]["mods"][0]["limit_modifiers"][0]["value"] == 2


def test_unequipped_armor_drops_special_armor() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET, equipped=False)
    out = compute(
        _mundane(
            "unequip-fire",
            armor=[jacket],
            armor_mods=[ArmorModInstall(mod_id=FIRE_RES, parent_id=jacket.id, rating=2)],
        )
    )
    assert out.derived["special_armor"]["fire"] == 0
    assert out.derived["armor_items"][0]["mods"][0]["special_armor"]["fire"] == 2


def test_shock_frills_uses_capacity() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "shock-jacket",
            armor=[jacket],
            armor_mods=[ArmorModInstall(mod_id=SHOCK_FRILLS, parent_id=jacket.id)],
        )
    )
    row = out.derived["armor_items"][0]
    assert out.derived["nuyen_spent"] == 1250
    assert row["capacity_used"] == 2
    assert out.derived["errors"] == []


def test_ynt_softweave_doubles_jacket_cost_and_capacity() -> None:
    spec = next(item for item in catalog()["armor_mods"] if item["id"] == SOFTWEAVE)
    assert spec["purchasable"] is True
    assert spec["cost"] == "Armor Cost"
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "softweave-jacket",
            armor=[jacket],
            armor_mods=[ArmorModInstall(mod_id=SOFTWEAVE, parent_id=jacket.id)],
        )
    )
    row = out.derived["armor_items"][0]
    weave = row["mods"][0]
    assert weave["name"] == "YNT Softweave Armor"
    assert weave["nuyen"] == 1000
    assert weave["capacity_cost"] == -6
    assert row["nuyen"] == 2000
    assert row["capacity_used"] == 0
    assert row["capacity_max"] == 18
    assert out.derived["nuyen_spent"] == 2000
    assert out.derived["errors"] == []


def test_ynt_softweave_rounds_odd_capacity_up() -> None:
    vest = ArmorInstall(armor_id=ARMOR_VEST)
    out = compute(
        _mundane(
            "softweave-vest",
            armor=[vest],
            armor_mods=[ArmorModInstall(mod_id=SOFTWEAVE, parent_id=vest.id)],
        )
    )
    row = out.derived["armor_items"][0]
    assert row["nuyen"] == 1000
    assert row["capacity_used"] == 0
    assert row["capacity_max"] == 14
    assert out.derived["nuyen_spent"] == 1000
    assert out.derived["errors"] == []


def test_ynt_softweave_keeps_chem_prot_inside_expanded_capacity() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "softweave-chem",
            armor=[jacket],
            armor_mods=[
                ArmorModInstall(mod_id=CHEM_PROT, parent_id=jacket.id, rating=2),
                ArmorModInstall(mod_id=SOFTWEAVE, parent_id=jacket.id),
            ],
        )
    )
    row = out.derived["armor_items"][0]
    assert out.derived["nuyen_spent"] == 2500
    assert row["capacity_used"] == 2
    assert row["capacity_max"] == 18
    assert out.derived["errors"] == []


def test_armor_mod_capacity_overflow() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "overflow",
            armor=[jacket],
            armor_mods=[
                ArmorModInstall(mod_id=FIRE_RES, parent_id=jacket.id, rating=6),
                ArmorModInstall(mod_id=CHEM_PROT, parent_id=jacket.id, rating=6),
                ArmorModInstall(mod_id=SHOCK_FRILLS, parent_id=jacket.id),
            ],
        )
    )
    row = out.derived["armor_items"][0]
    assert row["capacity_used"] == 14
    assert any("容量超過" in err for err in out.derived["errors"])


def test_full_body_armor_helmet_adds_armor() -> None:
    suit = ArmorInstall(armor_id=FULL_BODY)
    out = compute(
        _mundane(
            "fba",
            armor=[suit],
            armor_mods=[ArmorModInstall(mod_id=FBA_HELMET, parent_id=suit.id)],
        )
    )
    assert out.derived["armor"] == 18
    assert out.derived["nuyen_spent"] == 2500
    assert out.derived["armor_items"][0]["mods"][0]["capacity_cost"] == 0


def test_urban_explorer_helmet_fits_only_jumpsuit() -> None:
    suit = ArmorInstall(armor_id=URBAN_EXPLORER)
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    ok = compute(
        _mundane(
            "ue-helm",
            armor=[suit],
            armor_mods=[ArmorModInstall(mod_id=UE_HELMET, parent_id=suit.id)],
        )
    )
    bad = compute(
        _mundane(
            "ue-on-jacket",
            armor=[jacket],
            armor_mods=[ArmorModInstall(mod_id=UE_HELMET, parent_id=jacket.id)],
        )
    )
    assert ok.derived["armor"] == 11
    assert ok.derived["nuyen_spent"] == 750
    assert any("装着できません" in warn for warn in bad.derived["warnings"])
    assert bad.derived["nuyen_spent"] == 1000


def test_fba_helmet_rejected_on_jacket() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "fba-on-jacket",
            armor=[jacket],
            armor_mods=[ArmorModInstall(mod_id=FBA_HELMET, parent_id=jacket.id)],
        )
    )
    assert any("装着できません" in warn for warn in out.derived["warnings"])
    assert out.derived["armor"] == 12
    assert out.derived["nuyen_spent"] == 1000


def test_armor_mod_without_parent_is_dropped() -> None:
    out = compute(_mundane("orphan-mod", armor_mods=[ArmorModInstall(mod_id=CHEM_PROT, rating=1)]))
    assert any("防具に装着" in warn for warn in out.derived["warnings"])
    assert out.derived["nuyen_spent"] == 0


def test_gel_packs_add_armor() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "gel",
            armor=[jacket],
            armor_mods=[ArmorModInstall(mod_id=GEL_PACKS, parent_id=jacket.id)],
        )
    )
    assert out.derived["armor"] == 14
    assert out.derived["nuyen_spent"] == 2500
    assert out.derived["armor_items"][0]["capacity_used"] == 0


def test_diving_armor_includes_chemical_protection() -> None:
    out = compute(_mundane("dive", armor=[ArmorInstall(armor_id=DIVING_ARMOR)]))
    row = out.derived["armor_items"][0]
    names = [mod["name"] for mod in row["mods"]]
    assert "Chemical Protection" in names
    assert row["mods"][0]["included"] is True
    assert row["mods"][0]["rating"] == 4
    assert row["mods"][0]["nuyen"] == 0
    assert row["mods"][0]["special_armor"]["toxin_contact"] == 4
    assert row["mods"][0]["special_armor"]["pathogen_contact"] == 4
    assert out.derived["special_armor"]["toxin_contact"] == 4
    assert out.derived["special_armor"]["pathogen_contact"] == 4
    assert row["capacity_used"] == 0
    assert out.derived["nuyen_spent"] == 1750


def test_duplicate_chemical_protection_is_rejected() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "dup-chem",
            armor=[jacket],
            armor_mods=[
                ArmorModInstall(mod_id=CHEM_PROT, parent_id=jacket.id, rating=2),
                ArmorModInstall(mod_id=CHEM_PROT, parent_id=jacket.id, rating=3),
            ],
        )
    )
    assert len(out.derived["armor_items"][0]["mods"]) == 1
    assert any("重複" in warn for warn in out.derived["warnings"])
    assert out.derived["nuyen_spent"] == 1500


def test_parse_avail_reads_rating_suffix_and_additive() -> None:
    assert parse_avail("12R") == (12, "R", False)
    assert parse_avail("+4") == (4, "", True)
    assert parse_avail("+2R") == (2, "R", True)
    assert parse_avail("FixedValues(8R,12R,20R)", 1) == (8, "R", False)
    assert parse_avail("FixedValues(8R,12R,20R)", 2) == (12, "R", False)
    assert parse_avail("FixedValues(8R,12R,20R)", 3) == (20, "R", False)
    assert parse_avail("(Rating * 5)R", 2) == (10, "R", False)
    assert parse_avail("+Rating - MinRating + 1", 3, {"MinRating": 1}) == (3, "", True)


def test_softweave_adds_four_to_jacket_avail() -> None:
    jacket = ArmorInstall(armor_id=ARMOR_JACKET)
    out = compute(
        _mundane(
            "avail-softweave",
            armor=[jacket],
            armor_mods=[ArmorModInstall(mod_id=SOFTWEAVE, parent_id=jacket.id)],
        )
    )
    row = out.derived["armor_items"][0]
    weave = row["mods"][0]
    assert row["avail"] == "6"
    assert row["avail_value"] == 6
    assert weave["avail"] == "4"
    assert weave["avail_additive"] is True
    assert weave["avail_folded"] is True
    assert out.derived["avail_limit"] == 12
    assert out.derived["errors"] == []


def test_internal_smartgun_adds_restricted_avail_to_predator() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "avail-smartgun",
            weapons=[weapon],
            weapon_accessories=[WeaponAccessoryInstall(accessory_id=INTERNAL_SMARTGUN, parent_id=weapon.id)],
        )
    )
    row = out.derived["weapons"][0]
    smart = next(acc for acc in row["accessories"] if acc["name"] == "Smartgun System, Internal")
    assert row["avail"] == "7R"
    assert smart["avail"] == "2R"
    assert smart["avail_additive"] is True
    assert out.derived["errors"] == []


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
    assert any("入手制限超過" in err and "20R" in err for err in out.derived["errors"])


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
    assert all("入手制限" not in err for err in ok.derived["errors"])
    assert over.derived["cyberware"][0]["avail"] == "16R"
    assert any("入手制限超過" in err and "16R" in err for err in over.derived["errors"])


def test_restricted_gear_allows_one_item_over_avail_twelve() -> None:
    out = compute(
        _mundane(
            "avail-restricted",
            priorities=Priorities(Heritage="C", Attributes="B", Talent="E", Skills="D", Resources="A"),
            quality_ids=[RESTRICTED_GEAR],
            cyberware=[CyberwareInstall(ware_id=WIRED, rating=3)],
        )
    )
    assert out.derived["cyberware"][0]["avail"] == "20R"
    assert out.derived["cyberware"][0].get("restricted_gear") is True
    assert all("入手制限" not in err for err in out.derived["errors"])
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "restrictedgear" not in tags


def test_custom_commlink_rating_six_is_at_device_limit() -> None:
    out = compute(_mundane("dr-custom-6", commlinks=[CommlinkInstall(gear_id=CUSTOM_LINK, rating=6)]))
    row = out.derived["commlinks"][0]
    assert row["device_rating"] == 6
    assert row["avail"] == "12"
    assert out.derived["device_rating_limit"] == 6
    assert all("デバイスレーティング" not in err for err in out.derived["errors"])
    assert all("入手制限" not in err for err in out.derived["errors"])


def test_custom_commlink_rating_seven_exceeds_device_rating() -> None:
    out = compute(_mundane("dr-custom-7", commlinks=[CommlinkInstall(gear_id=CUSTOM_LINK, rating=7)]))
    row = out.derived["commlinks"][0]
    assert row["device_rating"] == 7
    assert any("デバイスレーティング超過" in err and "7" in err for err in out.derived["errors"])


def test_fairlight_caliban_exceeds_device_rating_even_with_restricted_gear() -> None:
    out = compute(
        _mundane(
            "dr-caliban",
            quality_ids=[RESTRICTED_GEAR],
            commlinks=[CommlinkInstall(gear_id=FAIRLIGHT_CALIBAN)],
        )
    )
    row = out.derived["commlinks"][0]
    assert row["device_rating"] == 7
    assert row["avail"] == "14"
    assert row.get("restricted_gear") is True
    assert all("入手制限" not in err for err in out.derived["errors"])
    assert any("Fairlight Caliban" in err and "デバイスレーティング超過" in err for err in out.derived["errors"])


def test_transys_avalon_is_at_device_limit() -> None:
    out = compute(_mundane("dr-avalon", commlinks=[CommlinkInstall(gear_id=TRANSYS_AVALON)]))
    row = out.derived["commlinks"][0]
    assert row["device_rating"] == 6
    assert row["avail"] == "12"
    assert out.derived["errors"] == []


def test_sensor_array_rating_seven_exceeds_device_rating() -> None:
    ok = compute(_mundane("dr-array-6", sensors=[GearInstall(gear_id=SENSOR_ARRAY, rating=6)]))
    over = compute(_mundane("dr-array-7", sensors=[GearInstall(gear_id=SENSOR_ARRAY, rating=7)]))
    assert ok.derived["sensors"][0]["device_rating"] == 6
    assert all("デバイスレーティング" not in err for err in ok.derived["errors"])
    assert over.derived["sensors"][0]["device_rating"] == 7
    assert over.derived["sensors"][0]["avail"] == "7"
    assert any("Sensor Array" in err and "デバイスレーティング超過" in err for err in over.derived["errors"])
    assert all("入手制限" not in err for err in over.derived["errors"])


def test_meta_link_costs_nuyen() -> None:
    out = compute(_mundane("metalink", commlinks=[CommlinkInstall(gear_id=META_LINK)]))
    row = out.derived["commlinks"][0]
    assert row["nuyen"] == 100
    assert row["device_rating"] == 1
    assert row["dataprocessing"] == 1
    assert row["firewall"] == 1
    assert out.derived["nuyen_spent"] == 100


def test_custom_commlink_rating_four() -> None:
    out = compute(_mundane("custom-link", commlinks=[CommlinkInstall(gear_id=CUSTOM_LINK, rating=4)]))
    row = out.derived["commlinks"][0]
    assert row["nuyen"] == 2500
    assert row["device_rating"] == 4


def test_pi_tac_is_treated_as_commlink() -> None:
    spec = next(item for item in catalog()["commlinks"] if item["id"] == PI_TAC_I)
    assert spec["category"] == "PI-Tac"
    assert spec["devicerating"] == "4"
    assert spec["dataprocessing"] == "4"
    assert spec["firewall"] == "4"
    assert all(item["id"] != PI_TAC_I for item in catalog()["gear"])
    out = compute(
        _mundane(
            "pitac",
            priorities=Priorities(Heritage="C", Attributes="B", Talent="E", Skills="D", Resources="A"),
            commlinks=[CommlinkInstall(gear_id=PI_TAC_I)],
        )
    )
    row = out.derived["commlinks"][0]
    assert row["name"].startswith("PI-Tac Level I")
    assert row["category"] == "PI-Tac"
    assert row["nuyen"] == 115000
    assert row["device_rating"] == 4
    assert row["dataprocessing"] == 4
    assert row["firewall"] == 4
    assert out.derived["commlink"]["gear_id"] == PI_TAC_I
    assert out.derived["nuyen_spent"] == 115000
    assert out.derived["errors"] == []


def test_pi_tac_hosts_apps() -> None:
    link = CommlinkInstall(gear_id=PI_TAC_I)
    out = compute(
        _mundane(
            "pitac-app",
            priorities=Priorities(Heritage="C", Attributes="B", Talent="E", Skills="D", Resources="A"),
            commlinks=[link],
            apps=[GearInstall(gear_id=DATASOFT, parent_id=link.id, extra="Security Companies")],
        )
    )
    app = out.derived["apps"][0]
    assert app["label"] == "Datasoft (Security Companies)"
    assert app["parent_id"] == link.id
    assert out.derived["nuyen_spent"] == 115120
    assert out.derived["errors"] == []


def test_pi_tac_programs_only_fit_pi_tac() -> None:
    tac = CommlinkInstall(gear_id=PI_TAC_I)
    link = CommlinkInstall(gear_id=META_LINK)
    ok = compute(
        _mundane(
            "pitac-prog",
            priorities=Priorities(Heritage="C", Attributes="B", Talent="E", Skills="D", Resources="A"),
            commlinks=[tac],
            gear=[GearInstall(gear_id=PI_TAC_COPILOT, parent_id=tac.id)],
        )
    )
    kids = [row for row in ok.derived["gear"] if row.get("parent_id") == tac.id]
    assert kids[0]["name"] == 'Pantheon Industries "Co-Pilot" Mk I'
    assert kids[0]["nuyen"] == 400
    assert ok.derived["nuyen_spent"] == 115400
    assert ok.derived["errors"] == []
    denied = compute(
        _mundane(
            "pitac-prog-meta",
            commlinks=[link],
            gear=[GearInstall(gear_id=PI_TAC_COPILOT, parent_id=link.id)],
        )
    )
    assert denied.derived["gear"] == []
    assert any("装着できません" in warn for warn in denied.derived["warnings"])


def test_low_lifestyle_one_month() -> None:
    out = compute(_mundane("low-life", lifestyles=[LifestyleInstall(lifestyle_id=LOW_LIFESTYLE, months=1)]))
    assert out.derived["nuyen_spent"] == 2000
    assert out.derived["lifestyle"]["name"] == "Low"
    assert out.derived["errors"] == []


def test_low_lifestyle_two_months() -> None:
    out = compute(_mundane("low-life-2", lifestyles=[LifestyleInstall(lifestyle_id=LOW_LIFESTYLE, months=2)]))
    assert out.derived["nuyen_spent"] == 4000


def test_luxury_lifestyle_exceeds_resources() -> None:
    out = compute(_mundane("luxury", lifestyles=[LifestyleInstall(lifestyle_id=LUXURY_LIFESTYLE, months=1)]))
    assert out.derived["nuyen_spent"] == 100000
    assert any("ニューエンが不足" in err for err in out.derived["errors"])


def test_predator_purchase() -> None:
    out = compute(_mundane("predator", weapons=[WeaponInstall(weapon_id=PREDATOR, qty=1)]))
    row = out.derived["weapons"][0]
    assert row["nuyen"] == 725
    assert row["damage"] == "8P"
    assert row["ap"] == "-1"
    assert row["accuracy"] == "7"
    assert any(acc["name"] == "Smartgun System, Internal" and acc["included"] for acc in row["accessories"])
    assert out.derived["errors"] == []


def test_erika_cyberdeck_matrix_array() -> None:
    out = compute(_mundane("erika", cyberdecks=[GearInstall(gear_id=ERIKA_DECK)]))
    row = out.derived["cyberdecks"][0]
    assert row["nuyen"] == 49500
    assert row["device_rating"] == 1
    assert row["attack"] == 4
    assert row["sleaze"] == 3
    assert row["dataprocessing"] == 2
    assert row["firewall"] == 1
    assert row["programs"] == 1
    assert row["array"] == [4, 3, 2, 1]
    assert row["array_order"] == ["attack", "sleaze", "dataprocessing", "firewall"]
    assert row["can_reorder"] is True
    assert out.derived["cyberdeck"]["name"] == "Erika MCD-1"
    assert out.derived["nuyen_spent"] == 49500


def test_erika_cyberdeck_array_reorder() -> None:
    out = compute(
        _mundane(
            "erika-reorder",
            cyberdecks=[
                GearInstall(
                    gear_id=ERIKA_DECK,
                    array_order=["firewall", "dataprocessing", "sleaze", "attack"],
                )
            ],
        )
    )
    row = out.derived["cyberdecks"][0]
    assert row["attack"] == 1
    assert row["sleaze"] == 2
    assert row["dataprocessing"] == 3
    assert row["firewall"] == 4
    assert row["array"] == [4, 3, 2, 1]
    assert row["array_order"] == ["firewall", "dataprocessing", "sleaze", "attack"]
    assert out.derived["cyberdeck"]["attack"] == 1
    assert out.derived["nuyen_spent"] == 49500


def test_erika_cyberdeck_invalid_array_order_is_normalized() -> None:
    out = compute(
        _mundane(
            "erika-bad-order",
            cyberdecks=[GearInstall(gear_id=ERIKA_DECK, array_order=["attack", "attack", "nope"])],
        )
    )
    row = out.derived["cyberdecks"][0]
    assert row["array_order"] == ["attack", "sleaze", "dataprocessing", "firewall"]
    assert row["attack"] == 4
    assert row["sleaze"] == 3
    assert row["dataprocessing"] == 2
    assert row["firewall"] == 1


def test_radio_shack_rcc() -> None:
    out = compute(_mundane("rcc", rccs=[GearInstall(gear_id=RADIO_SHACK_RCC)]))
    row = out.derived["rccs"][0]
    assert row["nuyen"] == 8000
    assert row["device_rating"] == 2
    assert row["dataprocessing"] == 3
    assert row["firewall"] == 3
    assert row["programs"] == 2
    assert row["can_reorder"] is False
    assert out.derived["rcc"]["name"] == "Radio Shack Remote Controller"


def test_rcc_ignores_array_order() -> None:
    out = compute(
        _mundane(
            "rcc-order",
            rccs=[
                GearInstall(
                    gear_id=RADIO_SHACK_RCC,
                    array_order=["firewall", "dataprocessing", "attack", "sleaze"],
                )
            ],
        )
    )
    row = out.derived["rccs"][0]
    assert row["dataprocessing"] == 3
    assert row["firewall"] == 3
    assert row["can_reorder"] is False


def test_glasses_with_vision_enhancements() -> None:
    glasses = GearInstall(gear_id=GLASSES, rating=2)
    out = compute(
        _mundane(
            "glasses",
            optics=[
                glasses,
                GearInstall(gear_id=FLARE_COMP, parent_id=glasses.id),
                GearInstall(gear_id=IMAGE_LINK, parent_id=glasses.id),
            ],
        )
    )
    parent = next(item for item in out.derived["optics"] if item["gear_id"] == GLASSES)
    assert parent["nuyen"] == 200
    assert parent["capacity_used"] == 2
    assert parent["capacity_max"] == 2
    assert out.derived["nuyen_spent"] == 475
    assert out.derived["errors"] == []


def test_glasses_capacity_overflow() -> None:
    glasses = GearInstall(gear_id=GLASSES, rating=1)
    out = compute(
        _mundane(
            "glasses-over",
            optics=[
                glasses,
                GearInstall(gear_id=FLARE_COMP, parent_id=glasses.id),
                GearInstall(gear_id=IMAGE_LINK, parent_id=glasses.id),
            ],
        )
    )
    assert any("容量超過" in err for err in out.derived["errors"])


def test_binoculars_include_magnification() -> None:
    out = compute(_mundane("binocs", optics=[GearInstall(gear_id=BINOCULARS, rating=1)]))
    names = {item["name"] for item in out.derived["optics"]}
    assert "Binoculars" in names
    mag = next(item for item in out.derived["optics"] if item["name"] == "Vision Magnification")
    assert mag["included"] is True
    assert mag["nuyen"] == 0
    parent = next(item for item in out.derived["optics"] if item["name"] == "Binoculars")
    assert parent["capacity_used"] == 0
    assert out.derived["nuyen_spent"] == 50


def test_vision_mod_without_parent_is_dropped() -> None:
    out = compute(_mundane("flare-loose", optics=[GearInstall(gear_id=FLARE_COMP)]))
    assert out.derived["optics"] == []
    assert any("本体に装着" in warn for warn in out.derived["warnings"])


def test_earbuds_spatial_recognizer() -> None:
    buds = GearInstall(gear_id=EARBUDS, rating=2)
    out = compute(
        _mundane(
            "earbuds",
            optics=[buds, GearInstall(gear_id=SPATIAL, parent_id=buds.id)],
        )
    )
    parent = next(item for item in out.derived["optics"] if item["gear_id"] == EARBUDS)
    assert parent["nuyen"] == 100
    assert parent["capacity_used"] == 2
    assert parent["capacity_max"] == 2
    assert out.derived["nuyen_spent"] == 1100
    assert out.derived["errors"] == []


def test_erika_can_buy_one_program() -> None:
    deck = GearInstall(gear_id=ERIKA_DECK)
    out = compute(
        _mundane(
            "erika-armor-prog",
            cyberdecks=[deck],
            programs=[GearInstall(gear_id=ARMOR_PROG, parent_id=deck.id)],
        )
    )
    row = out.derived["cyberdecks"][0]
    assert row["program_used"] == 1
    assert row["program_max"] == 1
    assert out.derived["programs"][0]["name"] == "Armor"
    assert out.derived["nuyen_spent"] == 49750
    assert out.derived["errors"] == []
    assert not any("プログラムが上限超過" in warn for warn in out.derived["warnings"])


def test_erika_program_slot_overflow_warns() -> None:
    deck = GearInstall(gear_id=ERIKA_DECK)
    out = compute(
        _mundane(
            "erika-two-progs",
            cyberdecks=[deck],
            programs=[
                GearInstall(gear_id=ARMOR_PROG, parent_id=deck.id),
                GearInstall(gear_id=BROWSE, parent_id=deck.id),
            ],
        )
    )
    assert out.derived["cyberdecks"][0]["program_used"] == 2
    assert out.derived["nuyen_spent"] == 49830
    assert any("プログラムが上限超過（2/1）" in warn for warn in out.derived["warnings"])


def test_program_without_parent_is_dropped() -> None:
    out = compute(_mundane("loose-browse", programs=[GearInstall(gear_id=BROWSE)]))
    assert out.derived["programs"] == []
    assert any("本体に装着" in warn for warn in out.derived["warnings"])
    assert out.derived["nuyen_spent"] == 0


def test_autosoft_on_rcc() -> None:
    rcc = GearInstall(gear_id=RADIO_SHACK_RCC)
    out = compute(
        _mundane(
            "rcc-soft",
            rccs=[rcc],
            programs=[GearInstall(gear_id=CLEARSIGHT, rating=3, parent_id=rcc.id)],
        )
    )
    assert out.derived["rccs"][0]["program_used"] == 1
    assert out.derived["rccs"][0]["program_max"] == 2
    assert out.derived["programs"][0]["nuyen"] == 1500
    assert out.derived["nuyen_spent"] == 9500
    assert out.derived["errors"] == []


def test_hacking_program_rejected_on_rcc() -> None:
    rcc = GearInstall(gear_id=RADIO_SHACK_RCC)
    out = compute(
        _mundane(
            "rcc-hack",
            rccs=[rcc],
            programs=[GearInstall(gear_id=EXPLOIT, parent_id=rcc.id)],
        )
    )
    assert out.derived["programs"] == []
    assert any("サイバーデッキに装着" in warn for warn in out.derived["warnings"])
    assert out.derived["nuyen_spent"] == 8000


def test_sensor_array_with_functions() -> None:
    array = GearInstall(gear_id=SENSOR_ARRAY, rating=2)
    out = compute(
        _mundane(
            "array",
            sensors=[
                array,
                GearInstall(gear_id=ATMOSPHERE, parent_id=array.id),
                GearInstall(gear_id=MOTION_SENSOR, parent_id=array.id),
            ],
        )
    )
    parent = next(item for item in out.derived["sensors"] if item["gear_id"] == SENSOR_ARRAY)
    assert parent["nuyen"] == 2000
    assert parent["capacity_used"] == 2
    assert parent["capacity_max"] == 8
    assert out.derived["nuyen_spent"] == 2000
    assert out.derived["errors"] == []


def test_handheld_housing_takes_single_sensor() -> None:
    house = GearInstall(gear_id=HANDHELD_HOUSING, rating=2)
    sensor = GearInstall(gear_id=SINGLE_SENSOR, rating=3, parent_id=house.id)
    out = compute(_mundane("housing", sensors=[house, sensor]))
    parent = next(item for item in out.derived["sensors"] if item["gear_id"] == HANDHELD_HOUSING)
    child = next(item for item in out.derived["sensors"] if item["gear_id"] == SINGLE_SENSOR)
    assert parent["nuyen"] == 200
    assert parent["capacity_max"] == 2
    assert parent["capacity_used"] == 1
    assert child["nuyen"] == 300
    assert child["capacity_cost"] == 1
    assert out.derived["nuyen_spent"] == 500
    assert out.derived["errors"] == []


def test_sensor_array_does_not_fit_handheld() -> None:
    house = GearInstall(gear_id=HANDHELD_HOUSING, rating=3)
    array = GearInstall(gear_id=SENSOR_ARRAY, rating=2, parent_id=house.id)
    out = compute(_mundane("array-in-hand", sensors=[house, array]))
    parent = next(item for item in out.derived["sensors"] if item["gear_id"] == HANDHELD_HOUSING)
    assert parent["capacity_used"] == 6
    assert parent["capacity_max"] == 3
    assert any("容量超過" in err for err in out.derived["errors"])


def test_sensor_function_without_parent_is_dropped() -> None:
    out = compute(_mundane("loose-atmo", sensors=[GearInstall(gear_id=ATMOSPHERE)]))
    assert out.derived["sensors"] == []
    assert any("本体に装着" in warn for warn in out.derived["warnings"])


SKILL_AUTOSOFT = "87d24cff-e63b-4f73-a115-7aa5e29ea467"
DATASOFT = "1a55fbe3-b3c1-4568-882f-abe4dedb8572"
AGENT_APP = "2d8396ff-a4a9-4382-ab69-70d198856e7f"
LASER_SIGHT = "521f9c2e-dfb2-42a6-b707-9808ae4885de"
GAS_VENT_2 = "b3827611-f631-461e-8660-e744593ba2d2"
SILENCER = "0da6149e-982f-4051-825b-52c1b79c7e52"
DOBERMAN = "9186a0a7-635f-4242-a0e8-238f48b17ca2"


def test_skill_autosoft_needs_skill() -> None:
    rcc = GearInstall(gear_id=RADIO_SHACK_RCC)
    out = compute(
        _mundane(
            "skill-auto",
            rccs=[rcc],
            programs=[GearInstall(gear_id=SKILL_AUTOSOFT, rating=3, parent_id=rcc.id)],
        )
    )
    assert out.derived["programs"][0]["nuyen"] == 1500
    assert out.derived["nuyen_spent"] == 9500
    assert any("スキルを選んでください" in warn for warn in out.derived["warnings"])
    assert "First Aid" in out.derived["programs"][0]["extra_options"]


def test_skill_autosoft_with_skill() -> None:
    rcc = GearInstall(gear_id=RADIO_SHACK_RCC)
    out = compute(
        _mundane(
            "skill-auto-pick",
            rccs=[rcc],
            programs=[GearInstall(gear_id=SKILL_AUTOSOFT, rating=2, parent_id=rcc.id, extra="Hardware")],
        )
    )
    row = out.derived["programs"][0]
    assert row["extra"] == "Hardware"
    assert row["label"] == "Skill Autosoft (Hardware)"
    assert row["nuyen"] == 1000
    assert out.derived["nuyen_spent"] == 9000
    assert not any("スキルを選んでください" in warn for warn in out.derived["warnings"])


def test_predator_laser_sight() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "pred-laser",
            weapons=[weapon],
            weapon_accessories=[WeaponAccessoryInstall(accessory_id=LASER_SIGHT, parent_id=weapon.id)],
        )
    )
    row = out.derived["weapons"][0]
    assert row["accuracy"] == "8"
    assert row["nuyen"] == 850
    assert out.derived["nuyen_spent"] == 850
    names = {acc["name"] for acc in row["accessories"]}
    assert "Laser Sight" in names
    assert "Smartgun System, Internal" in names
    assert out.derived["errors"] == []


def test_internal_smartgun_retrofit_costs_weapon_price() -> None:
    spec = next(item for item in catalog()["weapon_accessories"] if item["id"] == INTERNAL_SMARTGUN)
    assert spec["purchasable"] is True
    assert spec["cost"] == "Weapon Cost"
    weapon = WeaponInstall(weapon_id=LIGHT_FIRE_70)
    out = compute(
        _mundane(
            "smartgun-retrofit",
            weapons=[weapon],
            weapon_accessories=[WeaponAccessoryInstall(accessory_id=INTERNAL_SMARTGUN, parent_id=weapon.id)],
        )
    )
    row = out.derived["weapons"][0]
    smart = next(acc for acc in row["accessories"] if acc["name"] == "Smartgun System, Internal")
    assert smart["included"] is False
    assert smart["nuyen"] == 200
    assert row["accuracy"] == "9"
    assert row["nuyen"] == 400
    assert out.derived["nuyen_spent"] == 400
    assert out.derived["errors"] == []


def test_internal_smartgun_qty_scales() -> None:
    weapon = WeaponInstall(weapon_id=LIGHT_FIRE_70, qty=2)
    out = compute(
        _mundane(
            "smartgun-qty",
            weapons=[weapon],
            weapon_accessories=[WeaponAccessoryInstall(accessory_id=INTERNAL_SMARTGUN, parent_id=weapon.id)],
        )
    )
    assert out.derived["weapons"][0]["nuyen"] == 800
    assert out.derived["nuyen_spent"] == 800


def test_internal_smartgun_forbidden_on_melee() -> None:
    weapon = WeaponInstall(weapon_id=KNIFE)
    out = compute(
        _mundane(
            "smartgun-knife",
            weapons=[weapon],
            weapon_accessories=[WeaponAccessoryInstall(accessory_id=INTERNAL_SMARTGUN, parent_id=weapon.id)],
        )
    )
    assert out.derived["nuyen_spent"] == 10
    assert out.derived["weapons"][0]["accessories"] == []
    assert any("装着できません" in warn for warn in out.derived["warnings"])


def test_predator_keeps_included_internal_smartgun() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "pred-dup-smart",
            weapons=[weapon],
            weapon_accessories=[WeaponAccessoryInstall(accessory_id=INTERNAL_SMARTGUN, parent_id=weapon.id)],
        )
    )
    row = out.derived["weapons"][0]
    smarts = [acc for acc in row["accessories"] if acc["name"] == "Smartgun System, Internal"]
    assert len(smarts) == 1
    assert smarts[0]["included"] is True
    assert smarts[0]["nuyen"] == 0
    assert row["nuyen"] == 725
    assert row["accuracy"] == "7"


def test_predator_apds_changes_ap() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "pred-apds",
            weapons=[weapon],
            gear=[GearInstall(gear_id=APDS, parent_id=weapon.id)],
        )
    )
    row = out.derived["weapons"][0]
    ammo = row["ammo_gear"][0]
    assert ammo["name"] == "Ammo: APDS"
    assert ammo["loaded"] is True
    assert ammo["nuyen"] == 120
    assert ammo["costfor"] == 10
    assert row["ap"] == "-5"
    assert row["damage"] == "8P"
    assert row["nuyen"] == 845
    assert out.derived["nuyen_spent"] == 845
    assert out.derived["errors"] == []


def test_predator_apds_qty_two() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "pred-apds-2",
            weapons=[weapon],
            gear=[GearInstall(gear_id=APDS, parent_id=weapon.id, qty=2)],
        )
    )
    assert out.derived["weapons"][0]["nuyen"] == 965
    assert out.derived["nuyen_spent"] == 965


def test_predator_regular_ammo_keeps_stats() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "pred-regular",
            weapons=[weapon],
            gear=[GearInstall(gear_id=REGULAR_AMMO, parent_id=weapon.id)],
        )
    )
    row = out.derived["weapons"][0]
    assert row["ap"] == "-1"
    assert row["damage"] == "8P"
    assert row["nuyen"] == 745


def test_predator_gel_rounds_stun() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "pred-gel",
            weapons=[weapon],
            gear=[GearInstall(gear_id=GEL_ROUNDS, parent_id=weapon.id)],
        )
    )
    row = out.derived["weapons"][0]
    assert row["damage"] == "8S"
    assert row["ap"] == "0"
    assert row["nuyen"] == 750


def test_predator_spare_clip() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "pred-clip",
            weapons=[weapon],
            gear=[GearInstall(gear_id=SPARE_CLIP, parent_id=weapon.id)],
        )
    )
    row = out.derived["weapons"][0]
    clip = row["ammo_gear"][0]
    assert clip["name"] == "Spare Clip"
    assert clip["loaded"] is False
    assert row["ap"] == "-1"
    assert row["nuyen"] == 730


def test_speed_loader_needs_cylinder() -> None:
    pistol = WeaponInstall(weapon_id=LIGHT_FIRE_70)
    revolver = WeaponInstall(weapon_id=SUPER_WARHAWK)
    rejected = compute(
        _mundane(
            "speed-clip",
            weapons=[pistol],
            gear=[GearInstall(gear_id=SPEED_LOADER, parent_id=pistol.id)],
        )
    )
    assert rejected.derived["weapons"][0]["ammo_gear"] == []
    assert any("装着できません" in warn for warn in rejected.derived["warnings"])
    accepted = compute(
        _mundane(
            "speed-cy",
            weapons=[revolver],
            gear=[GearInstall(gear_id=SPEED_LOADER, parent_id=revolver.id)],
        )
    )
    assert accepted.derived["weapons"][0]["ammo_gear"][0]["name"] == "Speed Loader"
    assert accepted.derived["nuyen_spent"] == 425


def test_apds_forbidden_on_melee() -> None:
    weapon = WeaponInstall(weapon_id=KNIFE)
    out = compute(
        _mundane(
            "knife-apds",
            weapons=[weapon],
            gear=[GearInstall(gear_id=APDS, parent_id=weapon.id)],
        )
    )
    assert out.derived["weapons"][0]["ammo_gear"] == []
    assert out.derived["nuyen_spent"] == 10
    assert any("装着できません" in warn for warn in out.derived["warnings"])


def test_predator_ammo_switch() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    apds = GearInstall(gear_id=APDS, parent_id=weapon.id)
    gel = GearInstall(gear_id=GEL_ROUNDS, parent_id=weapon.id)
    first = compute(_mundane("pred-switch", weapons=[weapon], gear=[apds, gel]))
    row = first.derived["weapons"][0]
    assert row["ap"] == "-5"
    assert row["damage"] == "8P"
    assert row["ammo_gear"][0]["loaded"] is True
    assert row["ammo_gear"][1]["loaded"] is False
    weapon.loaded_ammo_id = gel.id
    switched = compute(_mundane("pred-switch-gel", weapons=[weapon], gear=[apds, gel]))
    row = switched.derived["weapons"][0]
    assert row["damage"] == "8S"
    assert row["ap"] == "0"
    assert row["ammo_gear"][0]["loaded"] is False
    assert row["ammo_gear"][1]["loaded"] is True
    assert switched.derived["nuyen_spent"] == 870


def test_flash_bang_becomes_weapon() -> None:
    grenade = GearInstall(gear_id=FLASH_BANG, qty=2)
    out = compute(_mundane("flash-bang", gear=[grenade]))
    assert out.derived["nuyen_spent"] == 200
    assert len(out.derived["weapons"]) == 1
    row = out.derived["weapons"][0]
    assert row["name"] == "Grenade: Flash-Bang"
    assert row["from_gear"] is True
    assert row["source_gear_id"] == grenade.id
    assert row["id"] == grenade.id
    assert row["qty"] == 2
    assert row["nuyen"] == 200
    assert row["damage"].startswith("10S")
    assert row["ap"] == "-4"
    assert out.derived["gear"][0]["add_weapon"] == "Grenade: Flash-Bang"


def test_throwing_knife_gear_is_weapon() -> None:
    knife = GearInstall(gear_id=THROWING_KNIFE_GEAR)
    out = compute(_mundane("throw-knife", gear=[knife]))
    assert out.derived["nuyen_spent"] == 25
    row = out.derived["weapons"][0]
    assert row["name"] == "Throwing Knife"
    assert row["from_gear"] is True
    assert "({STR}+1)P" in row["damage"]


def test_minigrenade_loads_into_launcher() -> None:
    launcher = WeaponInstall(weapon_id=ANTIOCH)
    he = GearInstall(gear_id=MINI_HE, parent_id=launcher.id)
    flash = GearInstall(gear_id=MINI_FLASH, parent_id=launcher.id)
    first = compute(_mundane("antioch-he", weapons=[launcher], gear=[he, flash]))
    assert first.derived["nuyen_spent"] == 3400
    assert len(first.derived["weapons"]) == 1
    row = first.derived["weapons"][0]
    assert row["name"] == "Ares Antioch-2"
    assert row["damage"] == "16P (-2/m)"
    assert row["ap"] == "-2"
    assert row["ammo_gear"][0]["loaded"] is True
    launcher.loaded_ammo_id = flash.id
    switched = compute(_mundane("antioch-flash", weapons=[launcher], gear=[he, flash]))
    row = switched.derived["weapons"][0]
    assert row["damage"] == "10S (10m Radius)"
    assert row["ap"] == "-4"
    assert row["ammo_gear"][1]["loaded"] is True
    assert switched.derived["nuyen_spent"] == 3400


def test_barrel_accessories_conflict() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "barrel-full",
            weapons=[weapon],
            weapon_accessories=[
                WeaponAccessoryInstall(accessory_id=GAS_VENT_2, parent_id=weapon.id),
                WeaponAccessoryInstall(accessory_id=SILENCER, parent_id=weapon.id),
            ],
        )
    )
    assert any("マウントが足りません" in err for err in out.derived["errors"])


def test_datasoft_on_commlink() -> None:
    link = CommlinkInstall(gear_id=META_LINK)
    out = compute(
        _mundane(
            "data-app",
            commlinks=[link],
            apps=[GearInstall(gear_id=DATASOFT, parent_id=link.id, extra="Security Companies")],
        )
    )
    app = out.derived["apps"][0]
    assert app["label"] == "Datasoft (Security Companies)"
    assert app["nuyen"] == 120
    assert out.derived["nuyen_spent"] == 220
    assert out.derived["errors"] == []


def test_agent_rating_cost() -> None:
    link = CommlinkInstall(gear_id=META_LINK)
    out = compute(
        _mundane(
            "agent-app",
            commlinks=[link],
            apps=[GearInstall(gear_id=AGENT_APP, rating=4, parent_id=link.id)],
        )
    )
    assert out.derived["apps"][0]["nuyen"] == 8000
    assert out.derived["nuyen_spent"] == 8100


def test_app_without_commlink_is_dropped() -> None:
    out = compute(_mundane("loose-app", apps=[GearInstall(gear_id=DATASOFT, extra="Maps")]))
    assert out.derived["apps"] == []
    assert any("通信機に装着" in warn for warn in out.derived["warnings"])


def test_doberman_drone() -> None:
    out = compute(_mundane("doberman", drones=[GearInstall(gear_id=DOBERMAN)]))
    row = out.derived["drones"][0]
    assert row["name"] == "GM-Nissan Doberman (Medium)"
    assert row["pilot"] == "3"
    assert row["body"] == "4"
    assert row["nuyen"] == 5000
    assert out.derived["nuyen_spent"] == 5000
    assert out.derived["errors"] == []
    assert {mod["name"] for mod in row["mods"]} == {"Rigger Interface"}
    assert any(acc["name"] == "Sensor Array" for acc in row["sensors"])
    assert row["weapon_mounts"]
    assert row["slots_used"] == 0
    assert row["slots_max"] == 4


HONDA_SPIRIT = "79046746-a3fb-4eb2-a78a-82ebdeecdacc"
FORD_AMERICAR = "898906ec-f2b9-43a4-98ad-6f79230b9a0c"
DODGE_SCOOT = "c0d3e7fd-d5fd-48c4-b49d-0c7dea26895d"
SUZUKI_MIRAGE = "86374792-b881-4d9b-915a-d0e6652bbf4d"
RIGGER_INTERFACE = "354bd92f-dafc-42a4-979c-e3631be6cf45"


def test_honda_spirit_costs_nuyen_and_includes_sensor() -> None:
    out = compute(_mundane("spirit", vehicles=[GearInstall(gear_id=HONDA_SPIRIT)]))
    row = out.derived["vehicles"][0]
    assert row["name"] == "Honda Spirit (Subcompact)"
    assert row["seats"] == "2"
    assert row["body"] == "8"
    assert row["armor"] == "6"
    assert row["nuyen"] == 12000
    assert row["slots_max"] == 8
    tracks = {item["category"]: item for item in row["slot_tracks"]}
    assert tracks["Powertrain"]["max"] == 8
    assert tracks["Weapons"]["used"] == 0
    assert any(acc["name"] == "Sensor Array" and acc["included"] and acc["rating"] == 2 for acc in row["sensors"])
    assert out.derived["nuyen_spent"] == 12000
    assert out.derived["errors"] == []


def test_dodge_scoot_includes_improved_economy() -> None:
    out = compute(_mundane("scoot", vehicles=[GearInstall(gear_id=DODGE_SCOOT)]))
    row = out.derived["vehicles"][0]
    assert row["nuyen"] == 3000
    assert {mod["name"] for mod in row["mods"]} == {"Improved Economy"}
    assert row["mods"][0]["included"] is True
    assert row["mods"][0]["nuyen"] == 0
    tracks = {item["category"]: item for item in row["slot_tracks"]}
    assert tracks["Powertrain"]["used"] == 0
    assert tracks["Powertrain"]["max"] == 4
    assert row["slots_used"] == 0
    assert out.derived["nuyen_spent"] == 3000


def test_rigger_interface_on_spirit() -> None:
    car = GearInstall(gear_id=HONDA_SPIRIT)
    out = compute(
        _mundane(
            "spirit-ri",
            vehicles=[car],
            vehicle_mods=[VehicleModInstall(mod_id=RIGGER_INTERFACE, parent_id=car.id)],
        )
    )
    row = out.derived["vehicles"][0]
    assert out.derived["nuyen_spent"] == 13000
    assert any(mod["name"] == "Rigger Interface" and mod["nuyen"] == 1000 for mod in row["mods"])
    tracks = {item["category"]: item for item in row["slot_tracks"]}
    assert tracks["Cosmetic"]["used"] == 0
    assert tracks["Cosmetic"]["max"] == 8
    assert out.derived["errors"] == []


GRIDLINK = "831a60c3-f57b-40c7-9b4d-92906897ee90"
MECHANICAL_ARM = "3154f81c-f85c-414d-abe4-8289aa6e9766"
HYUNDAI_SHIN = "72a204fc-e4f7-4e00-9d14-7f338fb86817"
ROTO_DRONE = "1291ab59-2483-42ca-b7a9-503b2c354cee"
IMPROVED_ECONOMY = "20083c34-5008-4647-9d9e-9ed230e4efe1"


def test_gridlink_uses_electromagnetic_slots() -> None:
    car = GearInstall(gear_id=HONDA_SPIRIT)
    out = compute(
        _mundane(
            "spirit-grid",
            vehicles=[car],
            vehicle_mods=[VehicleModInstall(mod_id=GRIDLINK, parent_id=car.id)],
        )
    )
    row = out.derived["vehicles"][0]
    tracks = {item["category"]: item for item in row["slot_tracks"]}
    assert tracks["Electromagnetic"]["used"] == 2
    assert tracks["Electromagnetic"]["max"] == 8
    assert tracks["Powertrain"]["used"] == 0
    assert out.derived["nuyen_spent"] == 12750
    assert out.derived["errors"] == []


def test_powertrain_slot_overflow_on_spirit() -> None:
    car = GearInstall(gear_id=HONDA_SPIRIT)
    out = compute(
        _mundane(
            "spirit-hnd-over",
            vehicles=[car],
            vehicle_mods=[VehicleModInstall(mod_id=HANDLING_ENH, parent_id=car.id, rating=2)],
        )
    )
    tracks = {item["category"]: item for item in out.derived["vehicles"][0]["slot_tracks"]}
    assert tracks["Powertrain"]["used"] == 10
    assert tracks["Powertrain"]["max"] == 8
    assert any("パワートレインスロット超過" in err for err in out.derived["errors"])


def test_shin_hyung_extra_body_slots() -> None:
    car = GearInstall(gear_id=HYUNDAI_SHIN)
    out = compute(
        _mundane(
            "shin-arm",
            vehicles=[car],
            vehicle_mods=[VehicleModInstall(mod_id=MECHANICAL_ARM, parent_id=car.id)],
        )
    )
    tracks = {item["category"]: item for item in out.derived["vehicles"][0]["slot_tracks"]}
    assert tracks["Body"]["max"] == 14
    assert tracks["Body"]["used"] == 3
    assert tracks["Powertrain"]["max"] == 10
    assert out.derived["errors"] == []


def test_roto_drone_uses_listed_modslots() -> None:
    out = compute(_mundane("roto", drones=[GearInstall(gear_id=ROTO_DRONE)]))
    row = out.derived["drones"][0]
    assert row["slots_max"] == 7
    assert row["slot_tracks"] == []
    assert out.derived["errors"] == []


def test_purchased_improved_economy_uses_powertrain() -> None:
    car = GearInstall(gear_id=HONDA_SPIRIT)
    out = compute(
        _mundane(
            "spirit-econ",
            vehicles=[car],
            vehicle_mods=[VehicleModInstall(mod_id=IMPROVED_ECONOMY, parent_id=car.id)],
        )
    )
    tracks = {item["category"]: item for item in out.derived["vehicles"][0]["slot_tracks"]}
    assert tracks["Powertrain"]["used"] == 2
    assert tracks["Powertrain"]["max"] == 8
    assert out.derived["nuyen_spent"] == 19500
    assert out.derived["errors"] == []


def test_gecko_tips_rejected_on_spirit() -> None:
    car = GearInstall(gear_id=HONDA_SPIRIT)
    out = compute(
        _mundane(
            "spirit-gecko",
            vehicles=[car],
            vehicle_mods=[VehicleModInstall(mod_id=GECKO_TIPS, parent_id=car.id)],
        )
    )
    assert any("装着できません" in warn for warn in out.derived["warnings"])
    assert out.derived["nuyen_spent"] == 12000


def test_gecko_tips_on_mirage() -> None:
    bike = GearInstall(gear_id=SUZUKI_MIRAGE)
    out = compute(
        _mundane(
            "mirage-gecko",
            vehicles=[bike],
            vehicle_mods=[VehicleModInstall(mod_id=GECKO_TIPS, parent_id=bike.id)],
        )
    )
    row = out.derived["vehicles"][0]
    gecko = next(mod for mod in row["mods"] if mod["mod_id"] == GECKO_TIPS)
    assert gecko["nuyen"] == 5000
    assert gecko["slots"] == 4
    assert out.derived["nuyen_spent"] == 13500
    assert out.derived["errors"] == []


def test_vehicle_mod_without_parent_is_dropped() -> None:
    out = compute(_mundane("orphan-vmod", vehicle_mods=[VehicleModInstall(mod_id=RIGGER_INTERFACE)]))
    assert any("車両に装着" in warn for warn in out.derived["warnings"])
    assert out.derived["nuyen_spent"] == 0


def test_ford_americar_and_spirit_stack_nuyen() -> None:
    out = compute(
        _mundane(
            "two-cars",
            vehicles=[GearInstall(gear_id=HONDA_SPIRIT), GearInstall(gear_id=FORD_AMERICAR)],
        )
    )
    assert out.derived["nuyen_spent"] == 28000
    assert {row["name"] for row in out.derived["vehicles"]} == {
        "Honda Spirit (Subcompact)",
        "Ford Americar (Sedan)",
    }


SIM_MODULE = "d589142e-a71f-4cd9-b916-967168721eea"
SIM_MODULE_HOT = "b7da0596-da6e-4122-adc3-21d7f3f9e3f1"
TRODES = "418d5ba1-dd19-4179-add8-074be445a7b2"
TOOL_KIT = "64fa5212-1d58-4e94-9cc1-9e3eb10773ed"


def test_sim_module_installs_in_spirit() -> None:
    car = GearInstall(gear_id=HONDA_SPIRIT)
    out = compute(
        _mundane(
            "spirit-sim",
            vehicles=[car],
            gear=[GearInstall(gear_id=SIM_MODULE, parent_id=car.id)],
        )
    )
    row = out.derived["vehicles"][0]
    assert any(acc["name"] == "Sim Module" and acc["nuyen"] == 100 for acc in row["gear"])
    assert row["nuyen"] == 12100
    assert out.derived["nuyen_spent"] == 12100
    assert out.derived["errors"] == []


def test_sim_module_hot_and_trodes_in_spirit() -> None:
    car = GearInstall(gear_id=HONDA_SPIRIT)
    out = compute(
        _mundane(
            "spirit-interior",
            vehicles=[car],
            gear=[
                GearInstall(gear_id=SIM_MODULE_HOT, parent_id=car.id),
                GearInstall(gear_id=TRODES, parent_id=car.id),
            ],
        )
    )
    names = {acc["name"] for acc in out.derived["vehicles"][0]["gear"]}
    assert names == {"Sim Module, Hot", "Trodes"}
    assert out.derived["nuyen_spent"] == 12000 + 250 + 70


def test_sim_module_without_parent_is_dropped() -> None:
    out = compute(_mundane("loose-sim", gear=[GearInstall(gear_id=SIM_MODULE)]))
    assert out.derived["gear"] == []
    assert any("装着" in warn for warn in out.derived["warnings"])


def test_sim_module_on_meta_link() -> None:
    link = CommlinkInstall(gear_id=META_LINK)
    out = compute(
        _mundane(
            "link-sim",
            commlinks=[link],
            gear=[GearInstall(gear_id=SIM_MODULE, parent_id=link.id)],
        )
    )
    assert out.derived["gear"][0]["name"] == "Sim Module"
    assert out.derived["nuyen_spent"] == 200
    assert out.derived["errors"] == []


def test_tool_kit_does_not_install_in_spirit() -> None:
    car = GearInstall(gear_id=HONDA_SPIRIT)
    out = compute(
        _mundane(
            "spirit-kit",
            vehicles=[car],
            gear=[GearInstall(gear_id=TOOL_KIT, parent_id=car.id, extra="Hardware")],
        )
    )
    assert out.derived["vehicles"][0]["gear"] == []
    assert any("装着できません" in warn for warn in out.derived["warnings"])
    assert out.derived["nuyen_spent"] == 12000


GROUP_AUTOSOFT = "25235dcf-089a-4c17-bc8f-6a1f5b2fb0b6"
MANEUVERING = "9d81218f-ee70-4304-9a09-ac865d84b8e0"
TARGETING = "0949997a-acb7-49d9-9905-5ae2cd35626f"
SIGNATURE_MASKING = "a249d87f-ec07-4716-9c62-e26061e80eac"
HANDLING_ENH = "956a20f7-64f3-4160-88a0-d6d6b29b0bd1"
GECKO_TIPS = "06940788-ad0b-453c-bc8a-e54e6221c185"
STANDARD_SR5_MOUNT = "079a5c61-aee6-4383-81b7-32540f7a0a0b"


def test_group_autosoft_needs_group() -> None:
    rcc = GearInstall(gear_id=RADIO_SHACK_RCC)
    out = compute(
        _mundane(
            "group-auto",
            rccs=[rcc],
            programs=[GearInstall(gear_id=GROUP_AUTOSOFT, rating=2, parent_id=rcc.id)],
        )
    )
    assert out.derived["programs"][0]["nuyen"] == 1000
    assert "Electronics" in out.derived["programs"][0]["extra_options"]
    assert any("スキルグループを選んでください" in warn for warn in out.derived["warnings"])


def test_group_autosoft_with_group() -> None:
    rcc = GearInstall(gear_id=RADIO_SHACK_RCC)
    out = compute(
        _mundane(
            "group-auto-pick",
            rccs=[rcc],
            programs=[GearInstall(gear_id=GROUP_AUTOSOFT, rating=2, parent_id=rcc.id, extra="Electronics")],
        )
    )
    row = out.derived["programs"][0]
    assert row["label"] == "Group Autosoft (Electronics)"
    assert row["nuyen"] == 1000
    assert not any("スキルグループを選んでください" in warn for warn in out.derived["warnings"])


def test_model_maneuvering_autosoft() -> None:
    rcc = GearInstall(gear_id=RADIO_SHACK_RCC)
    out = compute(
        _mundane(
            "model-auto",
            rccs=[rcc],
            programs=[GearInstall(gear_id=MANEUVERING, rating=2, parent_id=rcc.id, extra="GM-Nissan Doberman (Medium)")],
        )
    )
    row = out.derived["programs"][0]
    assert row["label"] == "Maneuvering Autosoft (GM-Nissan Doberman (Medium))"
    assert row["nuyen"] == 1000
    assert "GM-Nissan Doberman (Medium)" in row["extra_options"]
    assert not any("対象を入力" in warn for warn in out.derived["warnings"])


def test_weapon_targeting_autosoft_free_text() -> None:
    rcc = GearInstall(gear_id=RADIO_SHACK_RCC)
    out = compute(
        _mundane(
            "weapon-auto",
            rccs=[rcc],
            programs=[GearInstall(gear_id=TARGETING, rating=1, parent_id=rcc.id, extra="Custom Rifle")],
        )
    )
    row = out.derived["programs"][0]
    assert row["label"] == "Targeting Autosoft (Custom Rifle)"
    assert row["nuyen"] == 500


def test_doberman_sensor_function() -> None:
    drone = GearInstall(gear_id=DOBERMAN)
    array = GearInstall(gear_id=SENSOR_ARRAY, parent_id=drone.id, included=True, rating=3)
    out = compute(
        _mundane(
            "dob-atmo",
            drones=[drone],
            sensors=[array, GearInstall(gear_id=ATMOSPHERE, parent_id=array.id)],
        )
    )
    parent = next(item for item in out.derived["sensors"] if item["name"] == "Sensor Array")
    assert parent["included"] is True
    assert parent["nuyen"] == 0
    assert parent["capacity_max"] == 8
    assert parent["capacity_used"] == 1
    assert out.derived["nuyen_spent"] == 5000
    assert out.derived["errors"] == []


def test_doberman_signature_masking() -> None:
    drone = GearInstall(gear_id=DOBERMAN)
    out = compute(
        _mundane(
            "dob-mask",
            drones=[drone],
            vehicle_mods=[VehicleModInstall(mod_id=SIGNATURE_MASKING, parent_id=drone.id, rating=1)],
        )
    )
    row = out.derived["drones"][0]
    assert any(mod["name"] == "Signature Masking" for mod in row["mods"])
    assert out.derived["nuyen_spent"] == 7000
    assert row["slots_used"] <= row["slots_max"]
    assert any("Signature Masking" in err and "入手制限超過" in err for err in out.derived["errors"])


def test_doberman_handling_enhancement_slots() -> None:
    drone = GearInstall(gear_id=DOBERMAN)
    out = compute(
        _mundane(
            "dob-hnd",
            drones=[drone],
            vehicle_mods=[VehicleModInstall(mod_id=HANDLING_ENH, parent_id=drone.id, rating=1)],
        )
    )
    row = out.derived["drones"][0]
    assert row["handling"].startswith("6")
    assert out.derived["nuyen_spent"] == 15000
    assert row["slots_used"] == 4
    assert row["slots_max"] == 4
    assert out.derived["errors"] == []
    over = compute(
        _mundane(
            "dob-hnd-over",
            drones=[drone],
            vehicle_mods=[VehicleModInstall(mod_id=HANDLING_ENH, parent_id=drone.id, rating=2)],
        )
    )
    assert any("改造スロット超過" in err for err in over.derived["errors"])


def test_gecko_tips_body_formula() -> None:
    drone = GearInstall(gear_id=DOBERMAN)
    out = compute(
        _mundane(
            "dob-gecko",
            drones=[drone],
            vehicle_mods=[VehicleModInstall(mod_id=GECKO_TIPS, parent_id=drone.id)],
        )
    )
    mod = next(item for item in out.derived["vehicle_mods"] if item["mod_id"] == GECKO_TIPS)
    assert mod["nuyen"] == 5000
    assert mod["slots"] == 4


DRONE_ARM = "af87f3e0-aca3-4459-9d40-1573c758d137"
SYNTHETIC_DRONE_ARM = "a51d3e74-3e94-493e-b477-fd30511853b1"
HAND_BLADE = "ba93ab8d-fd7f-4fc4-bfa3-5f987fd15d77"
GYROMOUNT = "816fbe31-0bfb-455f-a939-fca85b968bd2"


def test_drone_arm_hosts_hand_blade() -> None:
    drone = GearInstall(gear_id=DOBERMAN)
    arm = VehicleModInstall(id="arm1", mod_id=DRONE_ARM, parent_id=drone.id)
    out = compute(
        _mundane(
            "dob-blade",
            drones=[drone],
            vehicle_mods=[arm],
            cyberware=[CyberwareInstall(ware_id=HAND_BLADE, parent_id=arm.id)],
        )
    )
    row = next(item for item in out.derived["vehicle_mods"] if item["id"] == "arm1")
    assert row["capacity_max"] == 15
    assert row["capacity_used"] == 2
    assert {item["name"] for item in row["cyberware"]} == {"Hand Blade"}
    blade = next(item for item in out.derived["cyberware"] if item["name"] == "Hand Blade")
    assert blade["essence"] == 0
    assert blade["nuyen"] == 2500
    assert out.derived["essence"] == 6
    assert out.derived["nuyen_spent"] == 15000
    assert out.derived["errors"] == []
    weapon = next(item for item in out.derived["weapons"] if item["name"] == "Hand Blade")
    assert weapon["from_ware"] is True
    assert weapon["nuyen"] == 2500
    assert weapon["useskill"] == "Unarmed Combat"
    assert weapon["damage"] == "6P"
    assert weapon["limb_str"] == 4


def test_hand_blade_on_cyberarm_is_weapon() -> None:
    arm = CyberwareInstall(id="arm1", ware_id=ARM)
    blade = CyberwareInstall(id="blade1", ware_id=HAND_BLADE, parent_id=arm.id)
    out = compute(_mundane("arm-blade", cyberware=[arm, blade]))
    row = next(item for item in out.derived["weapons"] if item["from_ware"])
    assert row["name"] == "Hand Blade"
    assert row["id"] == "blade1"
    assert row["source_ware_id"] == "blade1"
    assert row["weapon_id"] == "5ec246dc-c129-4e61-a27a-c4d82b223bea"
    assert row["nuyen"] == 2500
    assert row["ap"] == "-2"
    assert row["damage"] == "3P"
    assert row["limb_str"] == 1
    assert out.derived["nuyen_spent"] == 17500
    assert out.derived["essence"] == 5.0
    assert out.derived["errors"] == []


def test_hand_blade_uses_customized_limb_str() -> None:
    arm = CyberwareInstall(id="arm1", ware_id=ARM)
    custom = CyberwareInstall(ware_id=CUSTOM_STR, rating=3, parent_id="arm1")
    blade = CyberwareInstall(id="blade1", ware_id=HAND_BLADE, parent_id="arm1")
    out = compute(_mundane("arm-blade-str", cyberware=[arm, custom, blade]))
    row = next(item for item in out.derived["weapons"] if item["from_ware"])
    assert row["damage"] == "5P"
    assert row["limb_str"] == 3
    arm_row = next(item for item in out.derived["cyberware"] if item["id"] == "arm1")
    assert arm_row["limb_str"] == 3


def test_meat_hand_blade_uses_character_str() -> None:
    blade = CyberwareInstall(id="blade1", ware_id=HAND_BLADE)
    out = compute(_mundane("meat-blade", cyberware=[blade]))
    row = next(item for item in out.derived["weapons"] if item["from_ware"])
    assert row["damage"] == "3P"
    assert row.get("limb_str") in (None, 0)
    assert out.derived["essence"] == 5.75


def test_implant_weapon_is_hidden_from_catalog() -> None:
    hidden = next(item for item in catalog()["weapons"] if item["name"] == "Hand Blade" and item.get("from_cyberware"))
    assert hidden["hidden"] is True
    from app.store import public_catalog

    names = {item["name"] for item in public_catalog()["weapons"]}
    assert "Hand Blade" not in names
    ware = next(item for item in catalog()["cyberware"]["items"] if item["id"] == HAND_BLADE)
    assert ware["add_weapon"] == "Hand Blade"
    assert ware["add_weapon_id"] == hidden["id"]


def test_synthetic_drone_arm_fits_hand_blade() -> None:
    drone = GearInstall(gear_id=DOBERMAN)
    arm = VehicleModInstall(id="arm1", mod_id=SYNTHETIC_DRONE_ARM, parent_id=drone.id)
    out = compute(
        _mundane(
            "dob-synth",
            drones=[drone],
            vehicle_mods=[arm],
            cyberware=[CyberwareInstall(ware_id=HAND_BLADE, parent_id=arm.id)],
        )
    )
    row = next(item for item in out.derived["vehicle_mods"] if item["id"] == "arm1")
    assert row["nuyen"] == 10000
    assert row["capacity_used"] == 2
    assert out.derived["nuyen_spent"] == 17500
    assert out.derived["errors"] == []


def test_drone_arm_gyromount_capacity() -> None:
    drone = GearInstall(gear_id=DOBERMAN)
    arm = VehicleModInstall(id="arm1", mod_id=DRONE_ARM, parent_id=drone.id)
    out = compute(
        _mundane(
            "dob-gyro",
            drones=[drone],
            vehicle_mods=[arm],
            cyberware=[CyberwareInstall(ware_id=GYROMOUNT, parent_id=arm.id)],
        )
    )
    row = next(item for item in out.derived["vehicle_mods"] if item["id"] == "arm1")
    assert row["capacity_used"] == 8
    assert out.derived["nuyen_spent"] == 18500
    stacked = compute(
        _mundane(
            "dob-gyro-blade",
            drones=[drone],
            vehicle_mods=[arm],
            cyberware=[
                CyberwareInstall(ware_id=GYROMOUNT, parent_id=arm.id),
                CyberwareInstall(ware_id=HAND_BLADE, parent_id=arm.id),
            ],
        )
    )
    stacked_arm = next(item for item in stacked.derived["vehicle_mods"] if item["id"] == "arm1")
    assert stacked_arm["capacity_used"] == 10
    assert stacked.derived["errors"] == []


def test_drone_arm_capacity_overflow() -> None:
    drone = GearInstall(gear_id=DOBERMAN)
    arm = VehicleModInstall(id="arm1", mod_id=DRONE_ARM, parent_id=drone.id)
    out = compute(
        _mundane(
            "dob-over",
            drones=[drone],
            vehicle_mods=[arm],
            cyberware=[
                CyberwareInstall(ware_id=GYROMOUNT, parent_id=arm.id),
                CyberwareInstall(id="gyro2", ware_id=GYROMOUNT, parent_id=arm.id),
            ],
        )
    )
    row = next(item for item in out.derived["vehicle_mods"] if item["id"] == "arm1")
    assert row["capacity_used"] == 16
    assert any("容量超過" in err for err in out.derived["errors"])


def test_hand_blade_without_drone_arm_is_dropped() -> None:
    drone = GearInstall(gear_id=DOBERMAN)
    out = compute(
        _mundane(
            "dob-bare",
            drones=[drone],
            cyberware=[CyberwareInstall(ware_id=HAND_BLADE, parent_id=drone.id)],
        )
    )
    assert all(item["name"] != "Hand Blade" for item in out.derived["cyberware"])
    assert out.derived["nuyen_spent"] == 5000
    assert out.derived["essence"] == 6


def test_hand_blade_on_commlink_is_dropped() -> None:
    link = CommlinkInstall(gear_id=META_LINK)
    out = compute(
        _mundane(
            "link-blade",
            commlinks=[link],
            cyberware=[CyberwareInstall(ware_id=HAND_BLADE, parent_id=link.id)],
        )
    )
    assert all(item["name"] != "Hand Blade" for item in out.derived["cyberware"])


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


def test_doberman_mounts_predator() -> None:
    drone = GearInstall(gear_id=DOBERMAN)
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(_mundane("dob-empty", drones=[drone], weapons=[weapon]))
    mount = out.derived["drones"][0]["weapon_mounts"][0]
    out = compute(
        _mundane(
            "dob-gun",
            drones=[drone],
            weapons=[weapon],
            weapon_mounts=[
                WeaponMountInstall(
                    id=mount["id"],
                    parent_id=drone.id,
                    size_id=mount["size_id"],
                    visibility_id=mount["visibility_id"],
                    flexibility_id=mount["flexibility_id"],
                    control_id=mount["control_id"],
                    included=True,
                    weapon_install_id=weapon.id,
                )
            ],
        )
    )
    row = out.derived["drones"][0]
    assert row["weapon_mounts"][0]["weapon_name"] == "Ares Predator V"
    assert out.derived["weapons"][0]["mounted_on"] == drone.id
    assert out.derived["nuyen_spent"] == 5725
    assert out.derived["errors"] == []


MEDKIT = "ae9c37df-6d82-44c1-aa21-6c87e45e2dc1"
FAKE_SIN = "0c800bca-e6ff-475b-a014-c2069f5e364c"
FAKE_LICENSE = "8a16bbb2-8028-4c74-b22b-7aad9d001073"
REGULAR_AMMO = "b2a0b340-c793-4322-8422-8b03d18a6fae"
MAGLOCK = "d0cde5ea-d524-451d-9fd6-eeccd1439293"
ANTI_TAMPER = "caa0f85d-e6f0-415a-98c7-fc4f16139964"


def test_tool_kit_costs_five_hundred() -> None:
    out = compute(_mundane("kit", gear=[GearInstall(gear_id=TOOL_KIT, extra="Hardware")]))
    row = out.derived["gear"][0]
    assert row["name"] == "Tool Kit"
    assert row["nuyen"] == 500
    assert row["label"] == "Tool Kit (Hardware)"
    assert out.derived["nuyen_spent"] == 500
    assert out.derived["errors"] == []


def test_medkit_rating_multiplies_cost() -> None:
    out = compute(_mundane("med", gear=[GearInstall(gear_id=MEDKIT, rating=3)]))
    assert out.derived["gear"][0]["nuyen"] == 750
    assert out.derived["nuyen_spent"] == 750


def test_fake_sin_needs_name_and_holds_license() -> None:
    sin = GearInstall(gear_id=FAKE_SIN, rating=4)
    out = compute(_mundane("sin-empty", gear=[sin]))
    assert any("対象" in warn for warn in out.derived["warnings"])
    license = GearInstall(gear_id=FAKE_LICENSE, rating=4, parent_id=sin.id, extra="Drivers License")
    sin.extra = "John Doe"
    out = compute(_mundane("sin", gear=[sin, license]))
    names = [row["name"] for row in out.derived["gear"]]
    assert "Fake SIN" in names
    assert "Fake License" in names
    assert out.derived["nuyen_spent"] == 10000 + 800
    assert out.derived["errors"] == []
    lone = compute(_mundane("license-only", gear=[GearInstall(gear_id=FAKE_LICENSE, rating=2)]))
    assert lone.derived["gear"] == []
    assert any("装着" in warn for warn in lone.derived["warnings"])


def test_ammo_quantity_multiplies_cost() -> None:
    out = compute(_mundane("ammo", gear=[GearInstall(gear_id=REGULAR_AMMO, qty=10)]))
    assert out.derived["gear"][0]["nuyen"] == 200
    assert out.derived["nuyen_spent"] == 200


def test_maglock_anti_tamper_attaches() -> None:
    lock = GearInstall(gear_id=MAGLOCK, rating=3)
    circuit = GearInstall(gear_id=ANTI_TAMPER, rating=2, parent_id=lock.id)
    out = compute(_mundane("lock", gear=[lock, circuit]))
    assert {row["name"] for row in out.derived["gear"]} == {"Maglock", "Anti-Tamper Circuits"}
    assert out.derived["nuyen_spent"] == 300 + 500
    assert out.derived["errors"] == []


CLEANER = "373638b9-4334-4645-99f5-c3673e4f809b"
DIFFUSION = "33e75cd6-cad7-43dd-87ac-9838c83eccb5"
OVERDRIVE = "60b3f99f-f903-426a-ae13-ea604e77a956"
COURIER_SPRITE = "acf0c123-0881-4f13-8a98-010516e74019"
PULSE_STORM = "d8b11a80-eb95-409e-a53b-18c48e09342e"
EDITOR = "6b4ed8d5-75c8-4415-9578-15afa4ac8494"
STATIC_VEIL = "dbb1d719-c829-4c45-9a53-9ff538865c14"
RESONANCE_SPIKE = "704abd70-c0e6-4f06-b186-53a7cb856584"
RESONANT_STREAM_MACHINIST = "e3d04705-b90a-4d94-90d0-4ad2c7adfa79"
RESONANT_STREAM_SOURCEROR = "11d6c3b6-47c4-4765-a625-7a5907ba1b4a"
RESONANT_STREAM_CYBERADEPT = "d2873478-d265-45bb-8a9f-320b8d0d33d3"
SOURCERER_DAEMON = "08848a07-a013-4c45-b103-f5600f1e7171"
OTAKU_TO_TECHNOMANCER = "d62880dd-3e28-4b0c-8c71-dc0e4b72397b"


def _techno(cid: str, letter: str = "A", **kwargs: object) -> CharacterState:
    table = {
        "A": Priorities(Heritage="C", Attributes="B", Talent="A", Skills="D", Resources="E"),
        "B": Priorities(Heritage="C", Attributes="D", Talent="B", Skills="A", Resources="E"),
        "C": Priorities(Heritage="E", Attributes="B", Talent="C", Skills="A", Resources="D"),
    }
    attrs = kwargs.pop("attributes", None) or default_attributes(find_metatype("Human", None))
    return CharacterState(
        id=cid,
        name=cid,
        priorities=table[letter],
        metatype="Human",
        talent="Technomancer",
        attributes=attrs,  # type: ignore[arg-type]
        **kwargs,  # type: ignore[arg-type]
    )


def test_complex_form_fade_formula() -> None:
    assert spell_drain_value("L-2", 3) == 2
    assert spell_drain_value("L+1", 3) == 4
    assert spell_drain_value("L-3", 3) == 2


def test_technomancer_a_gets_seven_free_complex_forms() -> None:
    out = compute(
        _techno(
            "cf-free",
            "A",
            complex_forms=[
                ComplexFormInstall(form_id=CLEANER),
                ComplexFormInstall(form_id=EDITOR),
                ComplexFormInstall(form_id=STATIC_VEIL),
            ],
        )
    )
    assert out.derived["complex_form_points"]["free"] == 7
    assert out.derived["complex_form_points"]["used"] == 3
    assert out.derived["complex_form_points"]["paid"] == 0
    assert all(row["karma"] == 0 for row in out.derived["complex_forms"])
    assert out.derived["karma"]["remaining"] == 25
    cleaner = next(row for row in out.derived["complex_forms"] if row["name"] == "Cleaner")
    assert cleaner["level"] == 6
    assert cleaner["fade"] == 4
    assert cleaner["fade_code"] == "S"


def test_eighth_complex_form_costs_karma() -> None:
    ids = [CLEANER, EDITOR, STATIC_VEIL, PULSE_STORM, RESONANCE_SPIKE, DIFFUSION, "cfebf27d-707e-4ea2-a376-394738a11b3c", "42cc98b0-2b3f-42a0-bbe7-fb7d2633d11a"]
    forms = [ComplexFormInstall(form_id=fid, extra="Attack" if fid == DIFFUSION else None) for fid in ids]
    out = compute(_techno("cf-paid", "A", complex_forms=forms))
    assert out.derived["complex_form_points"]["used"] == 8
    assert out.derived["complex_form_points"]["paid"] == 1
    assert out.derived["complex_forms"][-1]["karma"] == 4
    assert out.derived["karma"]["spent"] == 4


def test_duplicate_complex_form_is_dropped() -> None:
    out = compute(
        _techno(
            "cf-dup",
            complex_forms=[ComplexFormInstall(form_id=CLEANER), ComplexFormInstall(form_id=CLEANER)],
        )
    )
    assert len(out.derived["complex_forms"]) == 1
    assert any("重複" in warn for warn in out.derived["warnings"])


def test_diffusion_needs_matrix_attribute() -> None:
    out = compute(_techno("diff-none", complex_forms=[ComplexFormInstall(form_id=DIFFUSION)]))
    row = out.derived["complex_forms"][0]
    assert row["needs_extra"] is True
    assert any("マトリクス属性" in warn for warn in out.derived["warnings"])
    out = compute(_techno("diff-atk", complex_forms=[ComplexFormInstall(form_id=DIFFUSION, extra="Attack")]))
    assert out.derived["complex_forms"][0]["extra"] == "Attack"
    assert out.derived["complex_forms"][0]["label"] == "Diffusion of Attack"
    assert not any("マトリクス属性" in warn for warn in out.derived["warnings"])


def test_overdrive_requires_stream_quality() -> None:
    out = compute(_techno("overdrive", complex_forms=[ComplexFormInstall(form_id=OVERDRIVE)]))
    assert out.derived["complex_forms"] == []
    assert any("Resonant Stream: Cyberadept" in warn for warn in out.derived["warnings"])


def test_resonant_stream_machinist_reduces_specific_complex_form_fade() -> None:
    base = compute(
        _techno(
            "mach-base",
            complex_forms=[ComplexFormInstall(form_id=DIFFUSION, extra="Attack")],
        )
    )
    out = compute(
        _techno(
            "mach",
            quality_ids=[RESONANT_STREAM_MACHINIST],
            complex_forms=[ComplexFormInstall(form_id=DIFFUSION, extra="Attack")],
        )
    )
    assert base.derived["complex_forms"][0]["fade"] == 4
    row = out.derived["complex_forms"][0]
    assert row["fade_mod"] == -2
    assert row["fade"] == 2
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "fadingvalue" not in tags


def test_resonant_stream_sourceror_reduces_all_complex_form_fade() -> None:
    base = compute(_techno("sour-base", complex_forms=[ComplexFormInstall(form_id=CLEANER)]))
    out = compute(
        _techno(
            "sour",
            quality_ids=[RESONANT_STREAM_SOURCEROR],
            complex_forms=[ComplexFormInstall(form_id=CLEANER)],
        )
    )
    assert base.derived["complex_forms"][0]["fade"] == 4
    row = out.derived["complex_forms"][0]
    assert row["fade_mod"] == -2
    assert row["fade"] == 2


def test_otaku_to_technomancer_fading_resist() -> None:
    base = compute(_techno("otaku-base"))
    out = compute(_techno("otaku", quality_ids=[OTAKU_TO_TECHNOMANCER]))
    assert base.derived["fade_resist"]["pool"] == 7
    assert out.derived["fade_resist"]["pool"] == 9
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "fadingresist" not in tags


DAREADRENALINE = "6a62e21f-f291-4e93-b109-df9c56c938f9"
DIMMER_BULB = "7706ce23-77c2-470f-bb7e-6a4e56fa78fe"


def test_dareadrenaline_drain_resist() -> None:
    base = compute(_mage("drain-base", tradition_id=HERMETIC))
    out = compute(
        _mage(
            "drain",
            tradition_id=HERMETIC,
            bioware=[CyberwareInstall(ware_id=DAREADRENALINE)],
        )
    )
    assert base.derived["drain_resist"]["pool"] == 2
    assert out.derived["drain_resist"]["pool"] == 3
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "drainresist" not in tags


def test_dareadrenaline_spell_defense_resists() -> None:
    out = compute(_human("dd", bioware=[CyberwareInstall(ware_id=DAREADRENALINE)]))
    sd = out.derived["spell_defense"]
    assert sd["general"] == 0
    assert sd["direct_mana"] == 1
    assert sd["detection"] == 1
    assert sd["mental_manipulation"] == 1
    assert sd["mana_illusion"] == 1
    assert sd["decrease"]["BOD"] == 1
    assert sd["decrease"]["WIL"] == 1
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    for tag in (
        "directmanaspellresist",
        "detectionspellresist",
        "mentalmanipulationresist",
        "manaillusionresist",
        "decreasebodresist",
        "decreasewilresist",
    ):
        assert tag not in tags


def test_magic_resistance_stacks_with_spell_defense() -> None:
    out = compute(_mundane("mr", quality_ids=[MAGIC_RESISTANCE]))
    assert out.derived["spell_defense"]["general"] == 1
    assert out.derived["spell_defense"]["detection"] == 1
    out2 = compute(
        _human("mr-dd", quality_ids=[MAGIC_RESISTANCE], bioware=[CyberwareInstall(ware_id=DAREADRENALINE)])
    )
    assert out2.derived["spell_defense"]["detection"] == 2
    assert out2.derived["spell_defense"]["mental_manipulation"] == 2


def test_dimmer_bulb_spell_defense_penalty() -> None:
    out = compute(_human("dim", quality_ids=[DIMMER_BULB]))
    sd = out.derived["spell_defense"]
    assert sd["mana_illusion"] == -1
    assert sd["detection"] == -1
    assert sd["decrease"]["LOG"] == -1
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "manaillusionresist" not in tags


def test_sourceror_grants_sourcerer_daemon_echo() -> None:
    out = compute(_techno("sour-daemon", quality_ids=[RESONANT_STREAM_SOURCEROR]))
    echo = next(row for row in out.derived["submersion"]["echoes"] if row["name"] == "Sourcerer Daemon")
    assert echo["echo_id"] == SOURCERER_DAEMON
    assert echo["granted"] is True
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "addecho" not in tags


def test_cyberadept_daemon_reduces_res_essence_penalty() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    attrs["RES"] = 6
    common = dict(
        attributes=attrs,
        cyberware=[CyberwareInstall(ware_id=DATAJACK)],
        submersion_grade=2,
        submersions=[
            SubmersionChoice(grade=1, echo_id=OVERCLOCKING),
            SubmersionChoice(grade=2, echo_id=OVERCLOCKING),
        ],
    )
    base = compute(_techno("ca-base", "A", **common))
    out = compute(_techno("ca", "A", quality_ids=[RESONANT_STREAM_CYBERADEPT], **common))
    assert base.attributes["RES"] == 5
    assert out.attributes["RES"] == 6
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "cyberadeptdaemon" not in tags


def test_courier_sprite_matrix_stats() -> None:
    out = compute(
        _techno(
            "courier",
            "A",
            sprites=[SpriteInstall(sprite_id=COURIER_SPRITE, level=3, services=2, registered=True)],
        )
    )
    row = out.derived["sprites"][0]
    assert row["name"] == "Courier Sprite"
    assert row["level"] == 3
    assert row["services"] == 2
    assert row["registered"] is True
    assert row["matrix"]["attack"] == 3
    assert row["matrix"]["sleaze"] == 6
    assert row["matrix"]["dataprocessing"] == 4
    assert row["matrix"]["firewall"] == 5
    assert row["matrix"]["initiative"] == 7
    assert "Cookie" in row["powers"]
    assert out.derived["errors"] == []


def test_registered_sprite_clamps_to_resonance() -> None:
    out = compute(
        _techno("sprite-cap", "C", sprites=[SpriteInstall(sprite_id=COURIER_SPRITE, level=12, services=9)])
    )
    row = out.derived["sprites"][0]
    assert row["level"] == 3
    assert row["services"] == 3


def test_compiled_sprite_can_exceed_resonance() -> None:
    out = compute(
        _techno(
            "compile-over",
            "C",
            sprites=[SpriteInstall(sprite_id=COURIER_SPRITE, level=6, registered=False, hits=4, opposed_hits=1)],
        )
    )
    row = out.derived["sprites"][0]
    assert row["level"] == 6
    assert row["services"] == 3
    assert row["registered"] is False
    assert row["test"]["physical"] is True


def test_too_many_registered_sprites() -> None:
    sprites = [SpriteInstall(sprite_id=COURIER_SPRITE, level=1, registered=True) for _ in range(4)]
    out = compute(_techno("too-many", "C", sprites=sprites))
    assert any("登録できるスプライト" in err for err in out.derived["errors"])


def test_mage_has_no_technomancer_tabs() -> None:
    out = compute(
        CharacterState(
            id="mage-no-techno",
            name="mage",
            priorities=Priorities(Heritage="C", Attributes="B", Talent="A", Skills="D", Resources="E"),
            metatype="Human",
            talent="Magician",
            attributes=default_attributes(find_metatype("Human", None)),
        )
    )
    assert "complexforms" not in out.derived["enabled_tabs"]
    assert "sprites" not in out.derived["enabled_tabs"]
    assert out.derived["living_persona"] is None


def test_contact_free_points_are_charisma_times_three() -> None:
    out = compute(_human("contact-free"))
    assert out.derived["totals"]["CHA"] == 1
    assert out.derived["contact_points"]["used"] == 0
    assert out.derived["contact_points"]["free"] == 3
    assert out.derived["contact_points"]["paid"] == 0
    assert out.derived["contact_points"]["karma"] == 0
    assert out.derived["contact_points"]["karma_per_point"] == 1
    assert out.derived["points"]["contacts"] == {"used": 0, "max": 3}
    high = _human("contact-cha3")
    high.attributes["CHA"] = 3
    high_out = compute(high)
    assert high_out.derived["contact_points"]["free"] == 9
    assert high_out.derived["karma"]["remaining"] == 25


def test_contact_spends_free_points_before_karma() -> None:
    out = compute(
        _human(
            "contact-free-spend",
            contacts=[ContactInstall(name="Fixer", role="Fixer", connection=2, loyalty=1)],
        )
    )
    row = out.derived["contacts"][0]
    assert row["name"] == "Fixer"
    assert row["role"] == "Fixer"
    assert row["connection"] == 2
    assert row["loyalty"] == 1
    assert row["cost"] == 3
    assert out.derived["contact_points"]["used"] == 3
    assert out.derived["contact_points"]["free"] == 3
    assert out.derived["contact_points"]["paid"] == 0
    assert out.derived["karma"]["remaining"] == 25
    assert out.derived["errors"] == []


def test_contact_overspend_costs_karma() -> None:
    state = _human("contact-paid")
    state.attributes["CHA"] = 3
    state.contacts = [
        ContactInstall(name="Fixer", connection=4, loyalty=3),
        ContactInstall(name="Street Doc", connection=2, loyalty=2),
    ]
    out = compute(state)
    assert out.derived["contact_points"]["used"] == 11
    assert out.derived["contact_points"]["free"] == 9
    assert out.derived["contact_points"]["paid"] == 2
    assert out.derived["contact_points"]["karma"] == 2
    assert out.derived["karma"]["spent"] == 2
    assert out.derived["karma"]["remaining"] == 23


def test_contact_chargen_cost_is_capped_at_seven() -> None:
    out = compute(
        _human("contact-cap", contacts=[ContactInstall(name="Mr. Johnson", connection=6, loyalty=6)])
    )
    row = out.derived["contacts"][0]
    assert row["connection"] == 6
    assert row["loyalty"] == 1
    assert row["cost"] == 7
    assert any("7まで" in warn for warn in out.derived["warnings"])


def test_unnamed_contact_is_warned() -> None:
    out = compute(_human("contact-noname", contacts=[ContactInstall(connection=1, loyalty=1)]))
    assert any("名前のないコネクト" in warn for warn in out.derived["warnings"])
    assert out.derived["contact_points"]["used"] == 2


def _karate_id() -> str:
    return next(item["id"] for item in catalog()["martial_arts"] if item["name"] == "Karate")


def test_martial_art_style_includes_one_technique() -> None:
    out = compute(
        _human(
            "karate-basic",
            martial_arts=[MartialArtInstall(art_id=_karate_id(), techniques=["Counterstrike"])],
        )
    )
    row = out.derived["martial_arts"][0]
    assert row["name"] == "Karate"
    assert row["karma"] == 7
    assert row["techniques"][0]["free"] is True
    assert out.derived["martial_art_points"]["karma"] == 7
    assert out.derived["martial_spec_options"]["Unarmed Combat"] == ["Karate"]
    assert out.derived["karma"]["spent"] == 7
    assert out.derived["errors"] == []


def test_martial_art_extra_technique_and_kick_reach() -> None:
    out = compute(
        _human(
            "karate-kick",
            martial_arts=[
                MartialArtInstall(art_id=_karate_id(), techniques=["Counterstrike", "Kick Attack"])
            ],
        )
    )
    row = out.derived["martial_arts"][0]
    assert row["karma"] == 12
    assert out.derived["unarmed_reach"] == 1
    assert out.derived["martial_art_points"]["techniques"] == 2
    assert out.derived["errors"] == []


def test_martial_art_chargen_limits() -> None:
    aikido = next(item["id"] for item in catalog()["martial_arts"] if item["name"] == "Aikido")
    out = compute(
        _human(
            "too-many-arts",
            martial_arts=[
                MartialArtInstall(art_id=_karate_id(), techniques=["Counterstrike"]),
                MartialArtInstall(art_id=aikido, techniques=["Counterstrike"]),
            ],
        )
    )
    assert any("流派は1つまで" in err for err in out.derived["errors"])

    techs = [
        "Counterstrike",
        "Kick Attack",
        "Kip-Up",
        "Opposing Force (Block)",
        "Sweep",
        "Yielding Force (Counterstrike)",
    ]
    out2 = compute(
        _human(
            "too-many-techs",
            martial_arts=[MartialArtInstall(art_id=_karate_id(), techniques=techs)],
        )
    )
    assert any("技は合計5つまで" in err for err in out2.derived["errors"])


ONE_TRICK_PONY = "98644894-e3a4-41f2-9b7e-91feb74d0334"
ONE_TRICK_PONY_ART = "0325b2c8-0a48-497f-92b1-2830a5ac467f"


def test_one_trick_pony_grants_free_quality_art() -> None:
    out = compute(_mundane("otp", quality_ids=[ONE_TRICK_PONY]))
    row = next(a for a in out.derived["martial_arts"] if a.get("art_id") == ONE_TRICK_PONY_ART)
    assert row["free"] is True
    assert row["locked"] is True
    assert row["karma"] == 0
    assert row["style_karma"] == 0
    assert row["technique_max"] == 1
    assert out.derived["martial_art_points"]["styles"] == 0
    assert out.derived["martial_art_points"]["karma"] == 0
    assert any("技を1つ選んでください" in warn for warn in out.derived["warnings"])
    assert "martialart" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    # quality karma only
    assert out.derived["karma"]["spent"] == 7


def test_one_trick_pony_technique_is_free_and_single() -> None:
    out = compute(
        _mundane(
            "otp-kick",
            quality_ids=[ONE_TRICK_PONY],
            martial_arts=[
                MartialArtInstall(
                    art_id=ONE_TRICK_PONY_ART,
                    techniques=["Kick Attack", "Counterstrike"],
                    free=True,
                    source_quality_id=ONE_TRICK_PONY,
                )
            ],
        )
    )
    row = next(a for a in out.derived["martial_arts"] if a.get("art_id") == ONE_TRICK_PONY_ART)
    assert len(row["techniques"]) == 1
    assert row["techniques"][0]["name"] == "Kick Attack"
    assert row["techniques"][0]["free"] is True
    assert row["karma"] == 0
    assert out.derived["unarmed_reach"] == 1
    assert out.derived["martial_art_points"]["techniques"] == 1
    assert any("技を1つまで" in warn for warn in out.derived["warnings"])


def test_one_trick_pony_does_not_block_paid_style() -> None:
    out = compute(
        _mundane(
            "otp-karate",
            quality_ids=[ONE_TRICK_PONY],
            martial_arts=[
                MartialArtInstall(
                    art_id=ONE_TRICK_PONY_ART,
                    techniques=["Counterstrike"],
                    free=True,
                    source_quality_id=ONE_TRICK_PONY,
                ),
                MartialArtInstall(art_id=_karate_id(), techniques=["Kick Attack"]),
            ],
        )
    )
    assert out.derived["martial_art_points"]["styles"] == 1
    assert len(out.derived["martial_arts"]) == 2
    assert out.derived["errors"] == []
    # quality 7 + karate style 7
    assert out.derived["karma"]["spent"] == 14


ATTACK_UPGRADE = "36aa9af4-5c04-40d9-ba09-31b401cc1ff0"
OVERCLOCKING = "61055141-71f5-400e-9e67-cef650ce4801"
RESONANCE_PROGRAM = "d5dbe3f7-8a44-466b-8d5d-db9f0c68ee6b"


def test_submersion_grade_one_costs_thirteen_karma() -> None:
    out = compute(
        _techno(
            "sub1",
            "A",
            submersion_grade=1,
            submersions=[SubmersionChoice(grade=1, echo_id=OVERCLOCKING)],
        )
    )
    assert "submersion" in out.derived["enabled_tabs"]
    assert out.derived["submersion"]["grade"] == 1
    assert out.derived["submersion"]["karma"] == 13
    assert out.derived["submersion"]["echoes"][0]["name"] == "Overclocking"
    assert out.derived["karma"]["spent"] == 13
    assert out.derived["living_persona"]["matrix_initiative_dice"] == 1


def test_submersion_raises_res_max_and_attack_upgrade() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    attrs["RES"] = 7
    attrs["CHA"] = 3
    base = compute(_techno("sub-base", "A", attributes=dict(attrs)))
    out = compute(
        _techno(
            "sub-res",
            "A",
            attributes=attrs,
            submersion_grade=1,
            submersions=[SubmersionChoice(grade=1, echo_id=ATTACK_UPGRADE)],
        )
    )
    assert out.derived["metatype_info"]["attributes"]["RES"]["max"] == 7
    assert out.attributes["RES"] == 7
    assert out.derived["living_persona"]["attack"] == int(base.derived["living_persona"]["attack"]) + 1


def test_submersion_grade_above_res_errors() -> None:
    out = compute(_techno("sub-over", "C", submersion_grade=5))
    assert any("サブマージョン等級はレゾナンス以下" in err for err in out.derived["errors"])


def test_echo_max_takes_blocks_third_attack_upgrade() -> None:
    out = compute(
        _techno(
            "sub-dup",
            "A",
            submersion_grade=3,
            submersions=[
                SubmersionChoice(grade=1, echo_id=ATTACK_UPGRADE),
                SubmersionChoice(grade=2, echo_id=ATTACK_UPGRADE),
                SubmersionChoice(grade=3, echo_id=ATTACK_UPGRADE),
            ],
        )
    )
    assert len(out.derived["submersion"]["echoes"]) == 2
    assert any("最大 2 回" in warn for warn in out.derived["warnings"])


def test_resonance_program_echo_needs_extra() -> None:
    out = compute(
        _techno(
            "sub-prog",
            "A",
            submersion_grade=1,
            submersions=[SubmersionChoice(grade=1, echo_id=RESONANCE_PROGRAM)],
        )
    )
    assert any("対象" in warn for warn in out.derived["warnings"])
    out2 = compute(
        _techno(
            "sub-prog2",
            "A",
            submersion_grade=1,
            submersions=[SubmersionChoice(grade=1, echo_id=RESONANCE_PROGRAM, extra="Browse")],
        )
    )
    assert out2.derived["submersion"]["echoes"][0]["extra"] == "Browse"
    assert not any("対象" in warn for warn in out2.derived["warnings"])


BLANDNESS = "9cffd452-8489-48d5-888c-ac35459d9174"
RESIST_PATHOGENS_TOXINS = "5c022754-f7cf-479f-80b2-de8454fd76e4"
EXCEPTIONAL_ATTRIBUTE = "2ac8a95a-a4d0-4bef-a2f2-dcde020258cf"
EX_CON = "4fe8fa5e-e31b-4126-a880-3e719a0a5820"
PHOTOGRAPHIC_MEMORY = "9d3be1d9-1309-45e7-8bd9-1f5a3ede3522"
QUICK_HEALER = "291efdb6-a8b8-49ce-b2be-72f9d3f8a243"
UNCANNY_HEALER = "0ebdfce5-c613-4fd9-9763-cae2d21c2153"
HOME_GROUND = "823eb204-c155-45a9-bb9a-98dcbe17a707"
SPIRIT_AFFINITY = "c067baa6-0dfa-4783-a0c8-0873564f0308"
CELERITY = "bd2cf8ea-4eb3-458c-aa04-2de47067f3ad"
CRYSTAL_BREATH = "c2b4f018-7b14-4e04-aab9-71c891dd0a18"
MAGIC_RESISTANCE = "f80ef6fc-e844-441c-81e3-b1264b34a4e7"
DEPENDENT_NUISANCE = "2b9a495d-b735-416b-a000-f648c3b4191a"
SINNER_CRIMINAL = "d9479e5c-d44a-45b9-8fb4-d1e08a9487b2"


def test_mage_enableattribute_not_unimplemented() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    attrs["MAG"] = 6
    out = compute(
        CharacterState(
            id="mage-enable",
            name="Mage",
            priorities=Priorities(Heritage="E", Attributes="B", Talent="A", Skills="C", Resources="D"),
            metatype="Human",
            talent="Magician",
            attributes=attrs,
        )
    )
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "enableattribute" not in tags


def test_troll_reach_and_lifestyle_cost() -> None:
    out = compute(
        CharacterState(
            id="troll-reach",
            name="Troll",
            priorities=Priorities(Heritage="A", Attributes="B", Talent="E", Skills="C", Resources="C"),
            metatype="Troll",
            attributes=default_attributes(find_metatype("Troll", None)),
            lifestyles=[LifestyleInstall(lifestyle_id=LOW_LIFESTYLE, months=1)],
        )
    )
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "reach" not in tags
    assert "lifestylecost" not in tags
    assert out.derived["reach"] == 1
    assert out.derived["unarmed_reach"] >= 1
    assert out.derived["lifestyle_cost_mod"] == 100
    assert out.derived["lifestyle"]["nuyen"] == 4000


def test_blandness_notoriety() -> None:
    out = compute(_human("bland", quality_ids=[BLANDNESS]))
    assert out.derived["notoriety"] == -1
    assert "notoriety" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


def test_resistance_pathogens_toxins_special_armor() -> None:
    out = compute(_human("rpt", quality_ids=[RESIST_PATHOGENS_TOXINS]))
    sa = out.derived["special_armor"]
    assert sa["toxin_contact"] == 1
    assert sa["toxin_ingestion"] == 1
    assert sa["pathogen_injection"] == 1
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "toxiningestionresist" not in tags
    assert "pathogeninjectionresist" not in tags


def test_exceptional_attribute_raises_max() -> None:
    missing = compute(_human("ea-miss", quality_ids=[EXCEPTIONAL_ATTRIBUTE]))
    assert any("属性を選んでください" in warn for warn in missing.derived["warnings"])
    attrs = default_attributes(find_metatype("Human", None))
    attrs["BOD"] = 6
    out = compute(
        CharacterState(
            id="ea-bod",
            name="ea-bod",
            priorities=Priorities(),
            metatype="Human",
            attributes=attrs,
            quality_ids=[EXCEPTIONAL_ATTRIBUTE],
            quality_extras={EXCEPTIONAL_ATTRIBUTE: "BOD"},
        )
    )
    assert out.derived["attribute_max_bonus"]["BOD"] == 1
    assert out.derived["metatype_info"]["attributes"]["BOD"]["max"] == 7
    assert out.derived["totals"]["BOD"] == 6
    assert "selectattributes" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


def test_ex_con_adds_sinner_quality() -> None:
    out = compute(_human("excon", quality_ids=[EX_CON]))
    names = {q["name"] for q in out.derived["qualities"]}
    assert "Ex-Con" in names
    assert "SINner (Criminal)" in names
    assert SINNER_CRIMINAL in out.quality_ids or any(q["id"] == SINNER_CRIMINAL for q in out.derived["qualities"])
    assert out.derived["excon"] is True
    assert "excon" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


ERASED = "07f1833e-e5e0-41e1-91de-9044b2f48367"
FAME_LOCAL = "51e9e615-e3ba-4b25-b7b0-ffa8acf076f8"
LIFESTYLE_HIGH = "4a37d519-c9be-4ecc-97bb-e9d78708c374"
LIFESTYLE_MEDIUM = "9cb0222c-14c1-4bea-bf83-055513a1f33e"


def test_erased_caps_public_awareness() -> None:
    out = compute(
        _human(
            "erased-pa",
            quality_ids=[ERASED, FAME_LOCAL],
            street_cred=9,
        )
    )
    assert out.derived["erased"] is True
    assert out.derived["public_awareness"] == 1
    assert "erased" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


def test_erased_blocks_high_lifestyle() -> None:
    out = compute(
        _human(
            "erased-high",
            quality_ids=[ERASED],
            lifestyles=[LifestyleInstall(lifestyle_id=LIFESTYLE_HIGH)],
        )
    )
    assert any("Medium より高い" in warn for warn in out.derived["warnings"])
    ok = compute(
        _human(
            "erased-med",
            quality_ids=[ERASED],
            lifestyles=[LifestyleInstall(lifestyle_id=LIFESTYLE_MEDIUM)],
        )
    )
    assert not any("Medium より高い" in warn for warn in ok.derived["warnings"])


def test_ex_con_bans_restricted_ware() -> None:
    out = compute(
        _human(
            "excon-ware",
            quality_ids=[EX_CON],
            cyberware=[CyberwareInstall(ware_id=MUSCLE, rating=1)],
        )
    )
    assert any("制限ウェア" in err for err in out.derived["errors"])


def test_ex_con_raises_corp_and_law_loyalty() -> None:
    corp = compute(
        _human(
            "excon-corp",
            quality_ids=[EX_CON],
            contacts=[ContactInstall(name="Boss", role="Mr. Johnson", connection=2, loyalty=2)],
        )
    )
    row = corp.derived["contacts"][0]
    assert row["loyalty"] == 4
    assert row["loyalty_min"] == 4
    law = compute(
        _human(
            "excon-law",
            quality_ids=[EX_CON],
            contacts=[ContactInstall(name="Buddy", role="Cop", connection=1, loyalty=2)],
        )
    )
    assert law.derived["contacts"][0]["loyalty"] == 5
    assert law.derived["contacts"][0]["loyalty_min"] == 5


INSPIRED_SASS = "fd9b9b6d-c969-40f1-8dc7-61f8e5d9cd4d"


def test_inspired_grants_free_artisan_expertise() -> None:
    out = compute(
        _human(
            "inspired",
            quality_ids=[INSPIRED_SASS],
            skills={"Artisan": 3},
            quality_extras={INSPIRED_SASS: "Cooking"},
        )
    )
    assert out.derived["skill_specializations"]["Artisan"] == "Cooking"
    row = out.derived["skill_expertises"][0]
    assert row["skill"] == "Artisan"
    assert row["spec"] == "Cooking"
    assert row["bonus"] == 3
    assert row["free"] is True
    assert out.derived["points"]["skills"]["used"] == 3  # rating only; expertise is free
    assert "selectexpertise" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


def test_inspired_requires_choice_and_skill() -> None:
    missing = compute(_human("insp-empty", quality_ids=[INSPIRED_SASS], skills={"Artisan": 2}))
    assert any("Expertise" in warn for warn in missing.derived["warnings"])
    no_skill = compute(
        _human(
            "insp-noskill",
            quality_ids=[INSPIRED_SASS],
            skills={"Artisan": 0},
            quality_extras={INSPIRED_SASS: "Cooking"},
        )
    )
    assert any("Artisan スキル" in warn for warn in no_skill.derived["warnings"])


def test_photographic_memory_and_quick_healer() -> None:
    out = compute(_human("mem-heal", quality_ids=[PHOTOGRAPHIC_MEMORY, QUICK_HEALER]))
    assert out.derived["test_mods"]["memory"] == 2
    assert out.derived["cm_recovery"]["physical"] == 2
    assert out.derived["cm_recovery"]["stun"] == 2
    assert any(row["name"] == "Heal" and row["bonus"] == 2 for row in out.derived["spell_dice_pool"])
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "memory" not in tags
    assert "spelldicepool" not in tags
    assert "physicalcmrecovery" not in tags


def test_uncanny_healer_cm_recovery() -> None:
    out = compute(_human("uncanny", quality_ids=[UNCANNY_HEALER]))
    assert out.derived["essence"] == 6.0
    assert out.derived["cm_recovery"]["physical"] == 6
    assert out.derived["cm_recovery"]["stun"] == 6
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "addesstophysicalcmrecovery" not in tags
    assert "addesstostuncmrecovery" not in tags


def test_home_ground_selecttext() -> None:
    missing = compute(_human("hg-missing", quality_ids=[HOME_GROUND]))
    tags = [item["tag"] for item in missing.derived["unimplemented_bonuses"]]
    assert "selecttext" not in tags
    assert any("対象を入力" in err for err in missing.derived["errors"])
    out = compute(
        _human("hg", quality_ids=[HOME_GROUND], quality_extras={HOME_GROUND: "Barrens"})
    )
    row = next(item for item in out.derived["qualities"] if item["id"] == HOME_GROUND)
    assert row["extra"] == "Barrens"
    assert not any("対象を入力" in err for err in out.derived["errors"])


def test_selecttext_quality_populates_catalog_options() -> None:
    from app.data_loader import catalog

    spirit_affinity = next(q for q in catalog()["qualities"] if q["id"] == SPIRIT_AFFINITY)
    assert spirit_affinity["extra_kind"] == "text"
    assert spirit_affinity["select_options"]
    assert "Spirit of Man" in spirit_affinity["select_options"]


def test_celerity_replaces_movement() -> None:
    out = compute(_human("celerity", quality_ids=[CELERITY]))
    assert out.derived["movement"]["walk"].startswith("3")
    assert out.derived["movement"]["run"].startswith("6")
    assert out.derived["movement"]["sprint_bonus"] == 100
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "movementreplace" not in tags
    assert "sprintbonus" not in tags


def test_crystal_breath_essence_penalty() -> None:
    out = compute(_human("crystal", quality_ids=[CRYSTAL_BREATH]))
    assert out.derived["essence_penalty"] == 1.0
    assert out.derived["essence"] == 5.0
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "essencepenaltyt100" not in tags
    assert "fatigueresist" not in tags
    assert out.derived["fatigue_resist"] == 1


def test_magic_resistance_and_dependent_lifestyle() -> None:
    out = compute(
        _mundane(
            "resist-dep",
            quality_ids=[MAGIC_RESISTANCE, DEPENDENT_NUISANCE],
            lifestyles=[LifestyleInstall(lifestyle_id=LOW_LIFESTYLE, months=1)],
        )
    )
    assert out.derived["spell_resistance"] == 1
    assert out.derived["lifestyle_cost_mod"] == 10
    assert out.derived["lifestyle"]["nuyen"] == 2200


MEDIUM_LIFESTYLE = "9cb0222c-14c1-4bea-bf83-055513a1f33e"
LIFESTYLE_GYM = "23c785d3-e086-46a6-8491-603fa1e6963d"
LIFESTYLE_CRAMPED = "ff0cb981-4459-46e7-ab75-d8c5bcb0c486"
JAZZ = "929c4835-1754-4999-9215-9859e8ec5384"
STREET_COOKED = "f22e79fa-fb04-4369-a761-a1a46e242bc8"
PHARMACEUTICAL = "21f33089-cb7a-4bef-80ae-03d04f1c47ad"


def test_medium_lifestyle_freegrids_and_quality() -> None:
    out = compute(
        _mundane(
            "medium-gym",
            lifestyles=[
                LifestyleInstall(
                    lifestyle_id=MEDIUM_LIFESTYLE,
                    months=1,
                    quality_ids=[LIFESTYLE_GYM],
                )
            ],
        )
    )
    ls = out.derived["lifestyle"]
    assert ls["name"] == "Medium"
    assert ls["base_monthly"] == 5000
    assert ls["monthly"] == 5000  # Gym is free on Medium via allowed
    assert ls["lp_used"] == 4
    assert ls["lp_max"] == 4
    grids = [q for q in ls["qualities"] if q["name"] == "Grid Subscription"]
    assert len(grids) == 2
    assert {q["extra"] for q in grids} == {"Local Grid", "Public Grid"}
    assert all(q.get("from_freegrid") for q in grids)
    gym = next(q for q in ls["qualities"] if q["name"] == "Gym")
    assert gym["free"] is True
    assert gym["cost"] == 0
    assert out.derived["nuyen_spent"] == 5000
    assert out.derived["errors"] == []


def test_lifestyle_quality_multiplier_cramped() -> None:
    out = compute(
        _mundane(
            "cramped",
            lifestyles=[
                LifestyleInstall(
                    lifestyle_id=MEDIUM_LIFESTYLE,
                    months=1,
                    quality_ids=[LIFESTYLE_CRAMPED],
                )
            ],
        )
    )
    ls = out.derived["lifestyle"]
    assert ls["multiplier_pct"] == -10
    assert ls["monthly"] == 4500
    assert ls["nuyen"] == 4500


def test_lifestyle_lp_overflow_warns() -> None:
    # Gym (2) + Cramped (1) + 2 freegrids (2) = 5 > Medium LP 4
    out = compute(
        _mundane(
            "lp-over",
            lifestyles=[
                LifestyleInstall(
                    lifestyle_id=MEDIUM_LIFESTYLE,
                    months=1,
                    quality_ids=[LIFESTYLE_GYM, LIFESTYLE_CRAMPED],
                )
            ],
        )
    )
    assert any("ライフスタイルポイント超過" in w for w in out.derived["warnings"])


def test_jazz_street_cooked_parent_cost() -> None:
    jazz = GearInstall(gear_id=JAZZ, id="jazz1")
    grade = GearInstall(gear_id=STREET_COOKED, parent_id="jazz1", id="grade1")
    out = compute(_mundane("jazz-street", gear=[jazz, grade]))
    by_name = {row["name"]: row for row in out.derived["gear"]}
    assert by_name["Jazz"]["nuyen"] == 75
    assert by_name["Street Cooked"]["nuyen"] == -37  # Parent Cost * -0.5
    assert out.derived["nuyen_spent"] == 38


def test_jazz_pharmaceutical_parent_cost() -> None:
    jazz = GearInstall(gear_id=JAZZ, id="jazz2")
    grade = GearInstall(gear_id=PHARMACEUTICAL, parent_id="jazz2", id="grade2")
    out = compute(_mundane("jazz-pharma", gear=[jazz, grade]))
    by_name = {row["name"]: row for row in out.derived["gear"]}
    assert by_name["Pharmaceutical"]["nuyen"] == 75
    assert out.derived["nuyen_spent"] == 150


def test_career_mode_skips_avail_limit() -> None:
    from app.data_loader import catalog, parse_avail

    high = None
    for g in catalog()["gear"]:
        if g.get("requireparent"):
            continue
        parsed = parse_avail(str(g.get("avail") or "0"))
        value = parsed[0] if isinstance(parsed, (tuple, list)) else int(parsed or 0)
        if value > 12:
            high = g
            break
    assert high is not None
    gear = [GearInstall(gear_id=high["id"])]
    charged = compute(_mundane("career-avail-cg", gear=gear))
    assert any("入手制限超過" in e for e in charged.derived["errors"])
    career = compute(_mundane("career-avail", career=True, gear=gear, nuyen_earned=10_000_000))
    assert not any("入手制限超過" in e for e in career.derived["errors"])
    assert career.derived["avail_limit"] is None
    assert career.derived["career"] is True
    assert career.derived["nuyen"] == career.derived["nuyen_pool"] - career.derived["nuyen_spent"]


def test_career_priority_attribute_raise_uses_new_rating_times_5() -> None:
    from app.engine import snapshot_career_baseline

    st = _mundane("career-agi")
    st.attributes["AGI"] = 4
    st = compute(st)
    st.career = True
    st.career_baseline = snapshot_career_baseline(st)
    st.attributes["AGI"] = 5
    out = compute(st)
    assert out.derived["career_advancement_karma"] == 25
    assert out.derived["karma"]["spent"] == 25
    assert out.derived["karma"]["remaining"] == 0
    assert out.derived["skill_rating_max"] == 12


def test_career_earned_rewards_expand_pools() -> None:
    # Priority Resources D = 50_000¥; chargen karma pool = 25
    out = compute(_mundane("career-earn", career=True, karma_earned=40, nuyen_earned=5000))
    assert out.derived["karma"]["pool"] == 65
    assert out.derived["nuyen_pool"] == 55_000


BORN_RICH = "8f232e71-d4bf-4bea-b1b2-b88c7e652073"
IN_DEBT = "2b4dd1b1-b806-44e3-9067-65dc39c82d13"
TRUST_FUND_I = "2656bcd7-3fe1-4c34-a4fb-89ebebfbf016"
SINNER_NATIONAL = "9ac85feb-ae1e-4996-8514-3570d411e1d5"
BIOCOMPAT_CYBER = "23bfa65d-9241-4183-b7ea-0e2935e42f29"
SENSITIVE_SYSTEM = "13fd45c3-e031-4452-8bf8-31829d2401f9"
DEALER_CONNECTION = "ef6796eb-6559-4f22-bfa6-7e6571a3690d"
COLLEGE_EDUCATION_RF = "604aea10-3f13-4f28-a87b-25b8bf677276"
UNCOUTH = "f0873c37-4f09-41cd-be81-88e8df5b42ae"
BLACK_MARKET_PIPELINE = "a68a897e-412f-4659-a637-4848f39a9c90"
AMBIDEXTROUS = "68cfe94a-fa7e-4129-a9b9-b5d73e3ced99"
MEDIUM_LIFESTYLE = "9cb0222c-14c1-4bea-bf83-055513a1f33e"


def test_born_rich_raises_priority_karma_nuyen_cap() -> None:
    out = compute(_mundane("born-rich", quality_ids=[BORN_RICH], karma_nuyen=40))
    assert out.derived["karma_chargen"]["nuyen_karma_max"] == 40
    assert out.derived["nuyen_pool"] == 50_000 + 80_000
    assert out.derived["karma"]["spent"] == 5 + 40


def test_in_debt_adds_nuyen_and_lowers_cap() -> None:
    out = compute(_mundane("in-debt", quality_ids=[IN_DEBT]))
    assert out.derived["nuyen_amt"] == 5000
    assert out.derived["karma_chargen"]["nuyen_karma_max"] == 9
    assert out.derived["nuyen_pool"] == 55_000


def test_trust_fund_covers_medium_lifestyle() -> None:
    out = compute(
        _mundane(
            "trust-fund",
            quality_ids=[TRUST_FUND_I, SINNER_NATIONAL],
            lifestyles=[LifestyleInstall(lifestyle_id=MEDIUM_LIFESTYLE, months=1)],
        )
    )
    assert out.derived["trustfund"] == 1
    assert out.derived["lifestyles"][0]["nuyen"] == 0
    assert out.derived["lifestyles"][0].get("trustfund") is True


def test_biocompatibility_and_sensitive_system_essence() -> None:
    base = compute(_mundane("ess0", cyberware=[CyberwareInstall(ware_id=WIRED, rating=1)]))
    compat = compute(
        _mundane(
            "ess1",
            quality_ids=[BIOCOMPAT_CYBER],
            cyberware=[CyberwareInstall(ware_id=WIRED, rating=1)],
        )
    )
    sens = compute(
        _mundane(
            "ess2",
            quality_ids=[SENSITIVE_SYSTEM],
            cyberware=[CyberwareInstall(ware_id=WIRED, rating=1)],
        )
    )
    assert compat.derived["cyberware_ess_multiplier"] == 90
    assert compat.derived["essence_lost_cyber"] == 1.8
    assert sens.derived["essence_lost_cyber"] == 4.0
    assert base.derived["essence_lost_cyber"] == 2.0


def test_dealer_connection_discounts_groundcraft() -> None:
    car = next(v for v in catalog()["vehicles"] if v.get("category") == "Cars")
    base = compute(_mundane("dealer0", gear=[GearInstall(gear_id=car["id"])]))
    deal = compute(
        _mundane("dealer1", quality_ids=[DEALER_CONNECTION], gear=[GearInstall(gear_id=car["id"])])
    )
    assert deal.derived["nuyen_spent"] == int(round(base.derived["nuyen_spent"] * 0.9))


def test_college_education_halves_academic_knowledge_points() -> None:
    out = compute(
        _mundane(
            "college",
            quality_ids=[COLLEGE_EDUCATION_RF],
            knowledge_skills={"History": 4},
            knowledge_categories={"History": "Academic"},
        )
    )
    assert out.derived["points"]["knowledge"]["used"] == 2


def test_uncouth_doubles_social_active_skill_points() -> None:
    out = compute(_mundane("uncouth", quality_ids=[UNCOUTH], skills={"Negotiation": 2}))
    assert out.derived["points"]["skills"]["used"] == 4


def test_black_market_pipeline_discounts_weapons() -> None:
    weapon = next(w for w in catalog()["weapons"] if w.get("name") == "Ares Predator V")
    contact = ContactInstall(name="Fence", connection=3, loyalty=2)
    base = compute(_mundane("bmp0", weapons=[WeaponInstall(weapon_id=weapon["id"])]))
    disc = compute(
        _mundane(
            "bmp1",
            quality_ids=[BLACK_MARKET_PIPELINE],
            quality_extras={
                BLACK_MARKET_PIPELINE: "Weapons",
                f"{BLACK_MARKET_PIPELINE}:contact": contact.id,
            },
            contacts=[contact],
            weapons=[WeaponInstall(weapon_id=weapon["id"])],
        )
    )
    assert disc.derived["nuyen_spent"] == int(round(base.derived["nuyen_spent"] * 0.9))
    assert disc.derived["black_market_contact_id"] == contact.id
    assert any(c.get("black_market_pipeline") for c in disc.derived["contacts"])


def test_black_market_pipeline_lowers_weapon_avail_by_two() -> None:
    spear = next(w for w in catalog()["weapons"] if w.get("name") == "Cougar Collapsible Spear")
    contact = ContactInstall(name="Arms Dealer", connection=2, loyalty=2)
    bare = compute(_mundane("bmp-avail0", weapons=[WeaponInstall(weapon_id=spear["id"])]))
    linked = compute(
        _mundane(
            "bmp-avail1",
            quality_ids=[BLACK_MARKET_PIPELINE],
            quality_extras={
                BLACK_MARKET_PIPELINE: "Weapons",
                f"{BLACK_MARKET_PIPELINE}:contact": contact.id,
            },
            contacts=[contact],
            weapons=[WeaponInstall(weapon_id=spear["id"])],
        )
    )
    assert bare.derived["weapons"][0]["avail"] == "14R"
    assert any("入手制限超過" in err for err in bare.derived["errors"])
    assert linked.derived["weapons"][0]["avail_base"] == 14
    assert linked.derived["weapons"][0]["avail"] == "12R"
    assert linked.derived["weapons"][0].get("black_market_avail") is True
    assert linked.derived["black_market_avail_bonus"] == 2
    assert not any("入手制限超過" in err for err in linked.derived["errors"])


def test_black_market_pipeline_warns_without_contact() -> None:
    out = compute(
        _mundane(
            "bmp-nocontact",
            quality_ids=[BLACK_MARKET_PIPELINE],
            quality_extras={BLACK_MARKET_PIPELINE: "Weapons"},
        )
    )
    assert any("コネクトを選んでください" in warn for warn in out.derived["warnings"])
    assert out.derived["black_market_avail_bonus"] == 0


def test_ambidextrous_flag() -> None:
    out = compute(_mundane("ambi", quality_ids=[AMBIDEXTROUS]))
    assert out.derived["ambidextrous"] is True


CYBER_SNOB = "aaac8dfd-dee6-4277-b967-9ec9089260a7"


def test_cyber_snob_disables_low_grades() -> None:
    out = compute(_mundane("cyber-snob", quality_ids=[CYBER_SNOB]))
    assert "Standard" in out.derived["disabled_cyberware_grades"]
    assert "Alphaware" in out.derived["disabled_cyberware_grades"]
    assert "Used" in out.derived["disabled_bioware_grades"]
    assert "Betaware" not in out.derived["disabled_cyberware_grades"]
    assert "disablecyberwaregrade" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "disablebiowaregrade" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


def test_cyber_snob_clamps_standard_to_betaware() -> None:
    out = compute(
        _mundane(
            "snob-clamp",
            quality_ids=[CYBER_SNOB],
            cyberware=[CyberwareInstall(ware_id=DATAJACK, grade="Standard")],
        )
    )
    row = out.derived["cyberware"][0]
    assert row["grade"] == "Betaware"
    assert any("Betaware に変更" in warn for warn in out.derived["warnings"])
    # Datajack 0.1 × Betaware 0.7
    assert out.derived["essence"] == 5.93
    assert out.derived["nuyen_spent"] == 1500


def test_cyber_snob_allows_betaware() -> None:
    out = compute(
        _mundane(
            "snob-beta",
            quality_ids=[CYBER_SNOB],
            cyberware=[CyberwareInstall(ware_id=DATAJACK, grade="Betaware")],
        )
    )
    assert out.derived["cyberware"][0]["grade"] == "Betaware"
    assert not any("グレードを使えません" in warn for warn in out.derived["warnings"])


MADE_MAN = "45be40cc-a21a-4771-b47d-a532ea60b205"
PRIME_DATAHAVEN = "7297d8b0-8bb8-4d7a-ab10-2d4e4381e5d0"
NETWORKER = "fc195df5-83f6-4aff-aca8-4287a56e4d4c"
MASSIVE_NETWORK = "f8384574-ce99-4e33-8a94-b5aea7ddf4bd"


def test_made_man_adds_free_group_contact() -> None:
    out = compute(_mundane("made-man", quality_ids=[MADE_MAN]))
    row = next(c for c in out.derived["contacts"] if c.get("source_quality_id") == MADE_MAN)
    assert row["connection"] == 1
    assert row["loyalty"] == 3
    assert row["free"] is True
    assert row["group"] is True
    assert row["locked"] is True
    assert row["billable"] == 0
    assert out.derived["made_man"] is True
    assert out.derived["contact_points"]["used"] == 0
    assert "addcontact" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


def test_prime_datahaven_adds_connection_five_contact() -> None:
    out = compute(_mundane("datahaven", quality_ids=[PRIME_DATAHAVEN]))
    row = next(c for c in out.derived["contacts"] if c.get("source_quality_id") == PRIME_DATAHAVEN)
    assert row["connection"] == 5
    assert row["loyalty"] == 3
    assert row["free"] is True
    assert row["group"] is True
    assert row["billable"] == 0
    assert row["loyalty_min"] == 3


def test_quality_contact_removed_when_quality_dropped() -> None:
    with_q = compute(_mundane("mm-on", quality_ids=[MADE_MAN]))
    assert any(c.get("source_quality_id") == MADE_MAN for c in with_q.derived["contacts"])
    # Persist quality-linked contact then drop the quality
    state = _mundane("mm-off", contacts=list(with_q.contacts or []))
    out = compute(state)
    assert not any(c.get("source_quality_id") == MADE_MAN for c in out.derived["contacts"])


def test_made_man_contact_excess_connection_costs_points() -> None:
    base = compute(_mundane("mm-base", quality_ids=[MADE_MAN]))
    contact = next(c for c in (base.contacts or []) if c.source_quality_id == MADE_MAN)
    contact.connection = 4  # free baseline 1+3=4; excess 3
    out = compute(
        _mundane(
            "mm-excess",
            quality_ids=[MADE_MAN],
            contacts=[contact],
        )
    )
    row = next(c for c in out.derived["contacts"] if c.get("source_quality_id") == MADE_MAN)
    assert row["billable"] == 3
    assert out.derived["contact_points"]["used"] == 3


def test_networker_zeros_excess_contact_karma() -> None:
    state = _mundane(
        "networker",
        quality_ids=[NETWORKER],
        contacts=[
            ContactInstall(name="Fixer", connection=4, loyalty=3),
            ContactInstall(name="Street Doc", connection=3, loyalty=3),
        ],
    )
    state.attributes["CHA"] = 3  # free 9; used 13; paid points 4
    out = compute(state)
    assert out.derived["contact_points"]["karma_per_point"] == 0
    assert out.derived["contact_points"]["paid"] == 4
    assert out.derived["contact_points"]["karma"] == 0
    # quality karma 5 only
    assert out.derived["karma"]["spent"] == 5
    assert "contactkarma" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


def test_massive_network_zeros_excess_contact_karma() -> None:
    state = _mundane(
        "massive-net",
        quality_ids=[MASSIVE_NETWORK],
        contacts=[ContactInstall(name="Fixer", connection=6, loyalty=1)],
    )
    state.attributes["CHA"] = 1  # free 3; used 7; paid 4
    out = compute(state)
    assert out.derived["contact_points"]["karma_per_point"] == 0
    assert out.derived["contact_points"]["karma"] == 0


CODESLINGER = "41cc3e26-ae55-4e28-bd6a-b08866c21424"


def test_codeslinger_requires_matrix_action() -> None:
    out = compute(_mundane("code-empty", quality_ids=[CODESLINGER]))
    assert any("マトリクスアクションを選んでください" in err for err in out.derived["errors"])
    assert out.derived["action_dice_pools"] == []


def test_codeslinger_adds_action_dice_pool() -> None:
    out = compute(
        _mundane(
            "code-hack",
            quality_ids=[CODESLINGER],
            quality_extras={CODESLINGER: "Hack on the Fly"},
        )
    )
    assert out.derived["action_dice_pools"] == [
        {"category": "Matrix", "name": "Hack on the Fly", "bonus": 2, "source": "Codeslinger"}
    ]
    assert "actiondicepool" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert out.derived["karma"]["spent"] == 10


CRYSTAL_LIMB_ARM = "350844b9-db9f-4cce-83c3-e8965511e928"


def test_crystal_limb_requires_side() -> None:
    out = compute(_mage("crystal-empty", quality_ids=[CRYSTAL_LIMB_ARM]))
    assert any("左右を選んでください" in err for err in out.derived["errors"])


def test_crystal_limb_arm_selects_side() -> None:
    out = compute(
        _mage(
            "crystal-left",
            quality_ids=[CRYSTAL_LIMB_ARM],
            quality_extras={CRYSTAL_LIMB_ARM: "Left"},
        )
    )
    row = next(q for q in out.derived["qualities"] if q["id"] == CRYSTAL_LIMB_ARM)
    assert row["selectside"] is True
    assert row["side"] == "Left"
    assert not any("左右" in err for err in out.derived["errors"])


def test_crystal_limb_conflicts_with_cyberarm_same_side() -> None:
    out = compute(
        _mage(
            "crystal-dup",
            quality_ids=[CRYSTAL_LIMB_ARM],
            quality_extras={CRYSTAL_LIMB_ARM: "Left"},
            cyberware=[CyberwareInstall(id="arm1", ware_id=ARM, side="Left")],
        )
    )
    assert any("重複" in err for err in out.derived["errors"])


def test_crystal_limb_allows_opposite_cyberarm() -> None:
    out = compute(
        _mage(
            "crystal-ok",
            quality_ids=[CRYSTAL_LIMB_ARM],
            quality_extras={CRYSTAL_LIMB_ARM: "Left"},
            cyberware=[CyberwareInstall(id="arm1", ware_id=ARM, side="Right")],
        )
    )
    assert not any("重複" in err for err in out.derived["errors"])


ELEMENTALIST_AIR = "4d5e0fd2-dab3-4de0-9756-096a748bb3cc"
HEDGE_WITCH = "d03a9696-2341-4894-8cf2-0537c4e74af2"
MANABOLT = "85c12bae-3954-483c-a211-d8ee43a1c65e"
HEAL = "92fe97e1-2f16-4398-b12b-b29bfa23c75d"
SPIRIT_AIR = "380a4860-e5b7-4d07-9b8f-24951c1d656a"
SPIRIT_FIRE = "c0178bf8-1fc5-4c56-9ce1-92a3ae1adc45"


def test_elementalist_requires_spell_category() -> None:
    out = compute(_mage("elem-empty", quality_ids=[ELEMENTALIST_AIR]))
    assert any("呪文カテゴリを選んでください" in err for err in out.derived["errors"])
    assert "limitspellcategory" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


def test_elementalist_limits_spells_and_spirits() -> None:
    out = compute(
        _mage(
            "elem-air",
            quality_ids=[ELEMENTALIST_AIR],
            quality_extras={ELEMENTALIST_AIR: "Combat"},
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=MANABOLT), SpellInstall(spell_id=HEAL)],
            spirits=[
                SpiritInstall(spirit_id=SPIRIT_AIR, force=1, services=1, bound=False),
                SpiritInstall(spirit_id=SPIRIT_FIRE, force=1, services=1, bound=False),
            ],
        )
    )
    assert out.derived["limit_spell_categories"] == ["Combat"]
    assert out.derived["limit_spirit_categories"] == ["Spirit of Air"]
    assert [s["name"] for s in out.derived["spells"]] == ["Manabolt"]
    assert any("Heal" in warn or "制限では習得" in warn for warn in out.derived["warnings"])
    assert [s["name"] for s in out.derived["spirits"]] == ["Spirit of Air"]
    assert any("Spirit of Fire" in warn and "制限" in warn for warn in out.derived["warnings"])
    assert "Enchanting" in (out.derived["disabled_skill_groups"] or [])


def test_hedge_witch_allows_rituals_plus_selected_category() -> None:
    out = compute(
        _mage(
            "hedge",
            quality_ids=[HEDGE_WITCH],
            quality_extras={HEDGE_WITCH: "Health"},
        )
    )
    assert out.derived["limit_spell_categories"] == ["Health"]
    assert out.derived["allow_spell_categories"] == ["Rituals"]
    assert "Conjuring" in (out.derived["disabled_skill_groups"] or [])


def test_hedge_witch_reduces_selected_category_drain() -> None:
    heal_id = "c09e8bb5-4bed-44f9-a41c-bed6a4deb871"
    out = compute(
        _mage(
            "hedge-drain",
            quality_ids=[HEDGE_WITCH],
            quality_extras={HEDGE_WITCH: "Health"},
            tradition_id=HERMETIC,
            spells=[SpellInstall(spell_id=heal_id, force=8)],
        )
    )
    heal = next(s for s in out.derived["spells"] if s["name"] == "Heal")
    assert heal["spell"]["drain_mod"] == -2
    # F-4 @8 = 4, with -2 = 2
    assert heal["spell"]["drain"] == 2
    assert "spellcategorydrain" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


DEATH_DEALER = "36e76b70-bf6a-4e66-8dac-13cd529b9274"
DEATH_DEALER_ADEPT = "cfc637e9-0071-4313-a25b-b411793f2321"
CRITICAL_STRIKE = "dbf16604-164c-485c-96c8-fe3136cd5caa"


def test_death_dealer_combat_spell_drain_and_damage() -> None:
    heal_id = "c09e8bb5-4bed-44f9-a41c-bed6a4deb871"
    out = compute(
        _mage(
            "death-dealer",
            quality_ids=[DEATH_DEALER],
            tradition_id=HERMETIC,
            skills={"Spellcasting": 6},
            spells=[SpellInstall(spell_id=MANABOLT, force=6), SpellInstall(spell_id=heal_id, force=6)],
        )
    )
    bolt = next(s for s in out.derived["spells"] if s["name"] == "Manabolt")
    heal = next(s for s in out.derived["spells"] if s["name"] == "Heal")
    assert bolt["spell"]["drain_mod"] == 1
    assert bolt["damage_mod"] == 1
    # F-3 @6 = 3, with +1 = 4
    assert bolt["spell"]["drain"] == 4
    assert heal["spell"]["drain_mod"] == 0
    assert heal["damage_mod"] == 0
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "spellcategorydrain" not in tags
    assert "spellcategorydamage" not in tags


WITNESS_MY_HATE = "f8af38e2-e79a-44f9-8e72-57aba35b7056"
MANABALL = "d866f612-7160-41d2-8ce9-b64262327559"


def test_witness_my_hate_direct_non_area_drain_and_damage() -> None:
    heal_id = "c09e8bb5-4bed-44f9-a41c-bed6a4deb871"
    out = compute(
        _mage(
            "wmh",
            quality_ids=[WITNESS_MY_HATE],
            tradition_id=HERMETIC,
            spells=[
                SpellInstall(spell_id=MANABOLT, force=6),
                SpellInstall(spell_id=MANABALL, force=6),
                SpellInstall(spell_id=heal_id, force=6),
            ],
        )
    )
    bolt = next(s for s in out.derived["spells"] if s["name"] == "Manabolt")
    ball = next(s for s in out.derived["spells"] if s["name"] == "Manaball")
    heal = next(s for s in out.derived["spells"] if s["name"] == "Heal")
    # Direct,NOT(Area): Manabolt gets +2 drain / +2 damage
    assert bolt["spell"]["drain_mod"] == 2
    assert bolt["damage_mod"] == 2
    # F-3 @6 = 3, with +2 = 5
    assert bolt["spell"]["drain"] == 5
    # Direct+Area excluded
    assert ball["spell"]["drain_mod"] == 0
    assert ball["damage_mod"] == 0
    # Non-Direct unaffected
    assert heal["spell"]["drain_mod"] == 0
    assert heal["damage_mod"] == 0
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "spelldescriptordrain" not in tags
    assert "spelldescriptordamage" not in tags


BAREHANDED_ADEPT = "742caf46-a10b-4aa1-a6bc-a53feb99748c"
DEATH_TOUCH = "9baed162-5e84-4f19-9b94-d543a560c067"
BUDDHISM = "a283220f-2197-4526-b15a-331b9185b326"


def test_barehanded_adept_touch_spells_and_doubled_drain() -> None:
    out = compute(
        _adept(
            "bha",
            quality_ids=[BAREHANDED_ADEPT],
            tradition_id=BUDDHISM,
            skills={"Unarmed Combat": 6},
            spells=[
                SpellInstall(spell_id=DEATH_TOUCH, force=6),
                SpellInstall(spell_id=MANABOLT, force=6),
            ],
        )
    )
    assert "spells" in out.derived["enabled_tabs"]
    assert set(out.derived["allow_spell_ranges"] or []) >= {"T", "T (A)"}
    assert out.derived["spell_range_gated"] is True
    # MAG 6 → half touch-only free spells = 3
    assert out.derived["spell_points"]["free"] == 3
    assert [s["name"] for s in out.derived["spells"]] == ["Death Touch"]
    assert any("Manabolt" in warn or "制限では習得" in warn for warn in out.derived["warnings"])
    touch = out.derived["spells"][0]
    assert touch["free"] is True
    assert touch["barehanded_adept"] is True
    assert touch["useskill"] == "Unarmed Combat"
    assert touch["spell"]["force_max"] == 2  # MAG/3 rounded up
    assert touch["spell"]["force"] == 2
    # F-6 @2 → base 2, ×2 → 4
    assert touch["spell"]["drain"] == 4
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "allowspellrange" not in tags
    assert "freespells" not in tags


PRACTICE_PRACTICE_PRACTICE = "81fc0829-3456-4701-8ecc-f101d145b538"
KRIME_CALLIOPE = "7fffffff-e125-44fb-8977-7fffffffc59c"


def test_practice_practice_practice_weapon_skill_accuracy() -> None:
    missing = compute(_human("ppp-empty", quality_ids=[PRACTICE_PRACTICE_PRACTICE]))
    assert any("スキルを選んでください" in warn for warn in missing.derived["warnings"])
    base = compute(
        _human(
            "ppp-base",
            weapons=[WeaponInstall(weapon_id=KRIME_CALLIOPE)],
        )
    )
    out = compute(
        _human(
            "ppp",
            quality_ids=[PRACTICE_PRACTICE_PRACTICE],
            quality_extras={PRACTICE_PRACTICE_PRACTICE: "Gunnery"},
            weapons=[WeaponInstall(weapon_id=KRIME_CALLIOPE)],
        )
    )
    base_weapon = base.derived["weapons"][0]
    weapon = out.derived["weapons"][0]
    assert base_weapon["accuracy"] == "4"
    assert weapon["accuracy"] == "5"
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "weaponskillaccuracy" not in tags


def test_death_dealer_adept_weapon_dv_and_skill_select() -> None:
    missing = compute(
        _adept(
            "dda-empty",
            quality_ids=[DEATH_DEALER_ADEPT],
            adept_powers=[AdeptPowerInstall(power_id=CRITICAL_STRIKE)],
            weapons=[WeaponInstall(weapon_id=KATANA)],
        )
    )
    assert any("武器スキル" in err for err in missing.derived["errors"])
    out = compute(
        _adept(
            "dda-blades",
            quality_ids=[DEATH_DEALER_ADEPT],
            quality_extras={DEATH_DEALER_ADEPT: "Blades"},
            adept_powers=[AdeptPowerInstall(power_id=CRITICAL_STRIKE)],
            weapons=[WeaponInstall(weapon_id=KATANA)],
        )
    )
    katana = next(w for w in out.derived["weapons"] if w["name"] == "Katana")
    assert "({STR}+4)P" in katana["damage"] or katana["damage"] == "({STR}+4)P"
    assert "weaponcategorydv" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


CHAIN_BREAKER = "8c49fcfb-54fa-43ce-b2af-51780dabf40f"
DARK_ALLY = "39384189-d15a-4f2e-97a9-7f9a0b85ef64"
DEDICATED_CONJURER = "2a599984-62e4-4110-9784-dc1922df395d"
SEER = "90691f29-5b81-4a81-9ebc-21f2f5da1d55"
NULL_WIZARD = "ecb5ab50-68c9-45ee-9fb4-c2f0b3051096"
GUARDIAN_SPIRIT = next(s["id"] for s in catalog()["spirits"] if s["name"] == "Guardian Spirit")
PLANT_SPIRIT = next(s["id"] for s in catalog()["spirits"] if s["name"] == "Plant Spirit")
TASK_SPIRIT = next(s["id"] for s in catalog()["spirits"] if s["name"] == "Task Spirit")


def test_chain_breaker_adds_extra_spirit_types() -> None:
    from app.engine import quality_addspirit_extra_key

    missing = compute(_mage("cb-empty", quality_ids=[CHAIN_BREAKER], tradition_id=HERMETIC))
    assert any("追加精霊" in err for err in missing.derived["errors"])
    assert "addspirit" not in [item["tag"] for item in missing.derived["unimplemented_bonuses"]]
    out = compute(
        _mage(
            "cb",
            quality_ids=[CHAIN_BREAKER],
            tradition_id=HERMETIC,
            quality_extras={
                quality_addspirit_extra_key(CHAIN_BREAKER, 0): "Guardian Spirit",
                quality_addspirit_extra_key(CHAIN_BREAKER, 1): "Plant Spirit",
            },
            spirits=[
                SpiritInstall(spirit_id=GUARDIAN_SPIRIT, force=1, services=1, bound=False),
                SpiritInstall(spirit_id=next(s["id"] for s in catalog()["spirits"] if s["name"] == "Spirit of Fire"), force=1, services=1, bound=False),
            ],
        )
    )
    assert set(out.derived["extra_spirits"]) == {"Guardian Spirit", "Plant Spirit"}
    names = {s["name"] for s in out.derived["spirits"]}
    assert "Guardian Spirit" in names
    assert "Spirit of Fire" in names
    assert "Binding" in (out.derived["disabled_skills"] or [])


def test_dedicated_conjurer_spirit_slots_scale_with_summoning() -> None:
    from app.engine import quality_addspirit_extra_key

    low = compute(
        _mage(
            "dc-low",
            quality_ids=[DEDICATED_CONJURER],
            tradition_id=HERMETIC,
            skills={"Summoning": 1},
        )
    )
    assert low.derived["add_spirit_picks"] == []
    assert "Spellcasting" in (low.derived["disabled_skills"] or [])
    mid = compute(
        _mage(
            "dc-mid",
            quality_ids=[DEDICATED_CONJURER],
            tradition_id=HERMETIC,
            skills={"Summoning": 4},
            quality_extras={
                quality_addspirit_extra_key(DEDICATED_CONJURER, 0): "Guardian Spirit",
                quality_addspirit_extra_key(DEDICATED_CONJURER, 1): "Task Spirit",
            },
            spirits=[SpiritInstall(spirit_id=TASK_SPIRIT, force=1, services=1, bound=False)],
        )
    )
    assert len(mid.derived["add_spirit_picks"]) == 2
    assert set(mid.derived["extra_spirits"]) == {"Guardian Spirit", "Task Spirit"}
    assert any(s["name"] == "Task Spirit" for s in mid.derived["spirits"])


def test_seer_and_null_wizard_grant_free_metamagics() -> None:
    seer = compute(_mage("seer", quality_ids=[SEER], tradition_id=HERMETIC))
    free_names = {m["name"] for m in seer.derived["initiation"]["metamagics"] if m.get("free")}
    assert free_names == {"Psychometry", "Sensing"}
    assert set(seer.derived["disabled_skill_groups"]) >= {"Sorcery", "Conjuring", "Enchanting"}
    assert "addmetamagic" not in [item["tag"] for item in seer.derived["unimplemented_bonuses"]]

    null = compute(_mage("null", quality_ids=[NULL_WIZARD], tradition_id=HERMETIC))
    free_names = {m["name"] for m in null.derived["initiation"]["metamagics"] if m.get("free")}
    assert free_names == {"Reflection"}
    assert any(q["name"] == "Magic Resistance" and q.get("free") for q in null.derived["qualities"])
    assert set(null.derived["disabled_skills"] or []) >= {
        "Binding",
        "Spellcasting",
        "Ritual Spellcasting",
        "Alchemy",
        "Artificing",
    }
    assert null.derived["spell_resistance"] >= 1


MENTORS_MASK = "bf68095e-35b9-49dc-a008-f67bbac9b83b"


def test_mentors_mask_reduces_spell_drain() -> None:
    base = compute(_mage("mm-base", tradition_id=HERMETIC, spells=[SpellInstall(spell_id=STUNBOLT, force=6)]))
    out = compute(
        _mage(
            "mm",
            tradition_id=HERMETIC,
            quality_ids=[MENTORS_MASK],
            spells=[SpellInstall(spell_id=STUNBOLT, force=6)],
        )
    )
    base_row = base.derived["spells"][0]
    row = out.derived["spells"][0]
    assert base_row["spell"]["drain_mod"] == 0
    assert row["spell"]["drain_mod"] == -1
    # F-3 @6 = 3, with -1 = 2
    assert base_row["spell"]["drain"] == 3
    assert row["spell"]["drain"] == 2
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "drainvalue" not in tags


ALCHEMICAL_ARMORER = "e508350b-f61d-4878-bd6d-98f8c9e3588b"
ALTER_BALLISTICS = "243313e6-a9af-456a-9631-6581d869aa02"


def test_alchemical_armorer_grants_alter_ballistics() -> None:
    out = compute(
        _mage(
            "aa",
            tradition_id=HERMETIC,
            quality_ids=[ALCHEMICAL_ARMORER],
        )
    )
    spell = next(s for s in out.derived["spells"] if s["name"] == "Alter Ballistics")
    assert spell["spell_id"] == ALTER_BALLISTICS
    assert spell["free"] is True
    assert spell["granted"] is True
    assert spell["alchemical"] is True
    assert spell["karma"] == 0
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "addspell" not in tags


DEDICATED_SPELLSLINGER = "bbc6879e-b50d-4862-b85c-a86c5b9e5d67"


def test_dedicated_spellslinger_free_spells_and_karma_discount() -> None:
    # Magician A: priority free spells + Spellcasting rating from freespells
    base = compute(_mage("dss0", tradition_id=HERMETIC, skills={"Spellcasting": 4}))
    priority_free = int(base.derived["spell_points"]["free"])
    ids = _learnable_ids(priority_free + 5)
    assert len(ids) == priority_free + 5
    out = compute(
        _mage(
            "dss",
            tradition_id=HERMETIC,
            quality_ids=[DEDICATED_SPELLSLINGER],
            skills={"Spellcasting": 4},
            spells=[SpellInstall(spell_id=sid) for sid in ids],
        )
    )
    assert out.derived["spell_points"]["free"] == priority_free + 4
    assert out.derived["spell_points"]["spell_karma"] == 4
    assert "Summoning" in (out.derived["disabled_skills"] or [])
    assert "Binding" in (out.derived["disabled_skills"] or [])
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "freespells" not in tags
    assert "newspellkarmacost" not in tags
    # First priority_free+4 are free; remaining 1 paid at 4 karma
    assert out.derived["spell_points"]["used"] == priority_free + 5
    assert out.derived["spell_points"]["paid"] == 1
    assert out.derived["spell_points"]["karma"] == 4
    paid_row = next(s for s in out.derived["spells"] if not s["free"])
    assert paid_row["karma"] == 4


PROTOTYPE_TRANSHUMAN = "08c4dfad-3661-48d9-a265-43cce84e20d8"
INCOMPETENT = "216290b9-053d-4f6d-81c9-d1fe8ae346be"
JACK_OF_ALL_TRADES = "624fa943-c0a1-44ee-8cd8-3aef4bea3f4b"
BILINGUAL = "c734e46a-d391-45a6-b022-6f18db5019f1"
AGED = "97e9b186-8924-4885-a948-3c781244a5cb"
UNEDUCATED = "d8362a78-54e9-4dbe-8388-6ba0a7b9df31"
CATS_EYES = "f038260b-f2de-4a9a-9507-5602d0e64a22"


def test_prototype_transhuman_waives_bioware_essence_and_forced_quality() -> None:
    out = compute(
        _mundane(
            "proto",
            quality_ids=[PROTOTYPE_TRANSHUMAN],
            quality_extras={PROTOTYPE_TRANSHUMAN: "Astral Beacon"},
            bioware=[
                CyberwareInstall(ware_id=ORTHOSKIN, rating=2),
                CyberwareInstall(ware_id=CATS_EYES),
            ],
        )
    )
    assert out.derived["prototype_transhuman_ess"] == 1.0
    assert out.derived["essence_lost_bio"] == 0.0
    assert out.derived["karma"]["spent"] == 10
    assert out.derived["karma"]["negative"]["used"] == 0
    free = [q for q in out.derived["qualities"] if q.get("free")]
    assert any(q["name"] == "Astral Beacon" and q["karma"] == 0 for q in free)


def test_prototype_transhuman_requires_forced_quality_choice() -> None:
    out = compute(_mundane("proto-empty", quality_ids=[PROTOTYPE_TRANSHUMAN]))
    assert any("対象を入力してください" in err for err in out.derived["errors"])


def test_uncouth_disables_social_skill_groups() -> None:
    out = compute(_mundane("uncouth-groups", quality_ids=[UNCOUTH], skill_groups={"Acting": 1}))
    assert set(out.derived["disabled_skill_groups"]) >= {"Acting", "Influence"}
    assert any("Acting" in warn for warn in out.derived["warnings"])


def test_incompetent_disables_chosen_skill_group() -> None:
    out = compute(
        _mundane(
            "incomp",
            quality_ids=[INCOMPETENT],
            quality_extras={INCOMPETENT: "Athletics"},
            skill_groups={"Athletics": 2},
        )
    )
    assert "Athletics" in out.derived["disabled_skill_groups"]
    assert any("Athletics" in warn for warn in out.derived["warnings"])


def test_jack_of_all_trades_adjusts_career_active_skill_karma() -> None:
    from app.engine import snapshot_career_baseline

    base = compute(_mundane("joat0", skills={"Pistols": 4}))
    base.career = True
    base.career_baseline = snapshot_career_baseline(base)
    base.skills = {**dict(base.skills), "Pistols": 5}
    without = compute(base)

    st = compute(_mundane("joat1", quality_ids=[JACK_OF_ALL_TRADES], skills={"Pistols": 4}))
    st.career = True
    st.career_baseline = snapshot_career_baseline(st)
    st.skills = {**dict(st.skills), "Pistols": 5}
    with_q = compute(st)
    assert without.derived["career_advancement_karma"] == 10
    assert with_q.derived["career_advancement_karma"] == 9

    st.skills = {**dict(st.skills), "Pistols": 6}
    high = compute(st)
    # 4→5:9 + 5→6:14 = 23
    assert high.derived["career_advancement_karma"] == 23


def test_bilingual_allows_two_native_languages() -> None:
    out = compute(
        _mundane(
            "bilingual",
            quality_ids=[BILINGUAL],
            native_languages=["Japanese", "English"],
        )
    )
    assert out.native_languages == ["Japanese", "English"]
    assert out.derived["native_language_limit"] == 2
    assert not any("母語" in warn for warn in out.derived["warnings"])


def test_aged_adds_knowledge_points_and_lowers_physical_max() -> None:
    out = compute(_mundane("aged", quality_ids=[AGED]))
    assert out.derived["points"]["knowledge"]["max"] == 9
    assert out.derived["metatype_info"]["attributes"]["BOD"]["max"] == 5
    assert out.derived["metatype_info"]["attributes"]["AGI"]["max"] == 5


def test_uneducated_blocks_defaulting_and_doubles_tech_group_karma() -> None:
    from app.engine import snapshot_career_baseline

    out = compute(_mundane("uned", quality_ids=[UNEDUCATED]))
    assert set(out.derived["blocked_default_categories"]) >= {
        "Professional",
        "Academic",
        "Technical Active",
    }
    assert any("デフォルト不可" in warn for warn in out.derived["warnings"])

    st = compute(_mundane("uned-g", quality_ids=[UNEDUCATED], skill_groups={"Electronics": 1}))
    st.career = True
    st.career_baseline = snapshot_career_baseline(st)
    st.skill_groups = {**dict(st.skill_groups), "Electronics": 2}
    raised = compute(st)
    # group rating 2 normally costs 10; Uneducated Technical Active groups ×2 → 20
    assert raised.derived["career_advancement_karma"] == 20


def test_career_street_cred_and_public_awareness() -> None:
    out = compute(
        _mundane(
            "rep",
            career=True,
            street_cred=7,
            notoriety_bonus=2,
            quality_ids=[BLANDNESS],
        )
    )
    # quality -1 + bonus 2 = 1; PA = (7+1)//3 = 2
    assert out.derived["street_cred"] == 7
    assert out.derived["notoriety"] == 1
    assert out.derived["public_awareness"] == 2


def test_career_reward_log_sets_earned_totals() -> None:
    from app.models import RewardEntry

    out = compute(
        _mundane(
            "rewards",
            career=True,
            reward_log=[
                RewardEntry(label="Run A", karma=6, nuyen=4000),
                RewardEntry(label="Run B", karma=4, nuyen=1000),
            ],
        )
    )
    assert out.derived["karma_earned"] == 10
    assert out.derived["nuyen_earned"] == 5000
    assert out.derived["karma"]["pool"] == 35
    assert len(out.derived["reward_log"]) == 2


def test_career_spend_breakdown_lists_attribute_raise() -> None:
    from app.engine import snapshot_career_baseline

    st = _mundane("break")
    st.attributes["AGI"] = 4
    st = compute(st)
    st.career = True
    st.career_baseline = snapshot_career_baseline(st)
    st.attributes["AGI"] = 5
    out = compute(st)
    assert out.derived["career_advancement_karma"] == 25
    assert any(row["label"].startswith("属性 AGI") and row["amount"] == 25 for row in out.derived["career_advancement_lines"])
    assert any(row["amount"] == 25 for row in out.derived["karma_spend_breakdown"])


SPECIAL_MODIFICATIONS = "0dd183a3-85ce-4029-9de5-9b6aa1eb539c"
SM_IMPROVED_AP = "b741b729-106e-46f2-9143-0f745fd48789"
SM_DAMAGE = "3c82e17b-76cd-47b9-9bda-c3131a64e0ee"
SM_AMMO_CAP = "9084d801-c654-4eec-960e-4186a6de81d6"


def test_special_modifications_grants_limit() -> None:
    out = compute(_mundane("sm-limit", quality_ids=[SPECIAL_MODIFICATIONS]))
    assert out.derived["special_modification_limit"] == {"used": 0, "max": 2}
    assert "specialmodificationlimit" not in [item["tag"] for item in out.derived["unimplemented_bonuses"]]


def test_special_modifications_stacks_twice() -> None:
    out = compute(_mundane("sm-x2", quality_ids=[SPECIAL_MODIFICATIONS, SPECIAL_MODIFICATIONS]))
    assert out.derived["special_modification_limit"]["max"] == 4
    assert len([q for q in out.derived["qualities"] if q["id"] == SPECIAL_MODIFICATIONS]) == 2
    assert out.derived["karma"]["spent"] == 10


def test_special_modification_improved_ap() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "sm-ap",
            quality_ids=[SPECIAL_MODIFICATIONS],
            weapons=[weapon],
            weapon_accessories=[WeaponAccessoryInstall(accessory_id=SM_IMPROVED_AP, parent_id=weapon.id)],
        )
    )
    row = out.derived["weapons"][0]
    assert row["ap"] == "-2"
    assert out.derived["special_modification_limit"] == {"used": 1, "max": 2}
    assert any(acc["name"] == "Special Modification: Improved AP" for acc in row["accessories"])
    assert out.derived["errors"] == []


def test_special_modification_requires_quality() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "sm-noq",
            weapons=[weapon],
            weapon_accessories=[WeaponAccessoryInstall(accessory_id=SM_IMPROVED_AP, parent_id=weapon.id)],
        )
    )
    assert not any(acc["name"].startswith("Special Modification:") for acc in out.derived["weapons"][0]["accessories"])
    assert any("Special Modifications が必要" in warn for warn in out.derived["warnings"])


def test_special_modification_damage_costs_two() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "sm-dmg",
            quality_ids=[SPECIAL_MODIFICATIONS],
            weapons=[weapon],
            weapon_accessories=[
                WeaponAccessoryInstall(accessory_id=SM_DAMAGE, parent_id=weapon.id),
                WeaponAccessoryInstall(accessory_id=SM_IMPROVED_AP, parent_id=weapon.id),
            ],
        )
    )
    row = out.derived["weapons"][0]
    assert row["damage"] == "9P"
    assert not any(acc["name"] == "Special Modification: Improved AP" for acc in row["accessories"])
    assert out.derived["special_modification_limit"] == {"used": 2, "max": 2}
    assert any("上限を超えています" in warn for warn in out.derived["warnings"])


def test_special_modification_ammo_capacity() -> None:
    weapon = WeaponInstall(weapon_id=PREDATOR)
    out = compute(
        _mundane(
            "sm-ammo",
            quality_ids=[SPECIAL_MODIFICATIONS],
            weapons=[weapon],
            weapon_accessories=[WeaponAccessoryInstall(accessory_id=SM_AMMO_CAP, parent_id=weapon.id)],
        )
    )
    assert out.derived["weapons"][0]["ammo"] == "23(c)"
