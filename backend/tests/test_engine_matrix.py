"""Commlinks, decks, RCCs, programs, sensors and device ratings."""

from app.data_loader import catalog
from app.engine import (
    compute,
    default_attributes,
    find_metatype,
)
from app.models import (
    CharacterState,
    CommlinkInstall,
    CyberwareInstall,
    GearInstall,
    Priorities,
)
from tests.engine_support import (
    ATMOSPHERE,
    CODESLINGER,
    ERIKA_DECK,
    HAND_BLADE,
    META_LINK,
    RADIO_SHACK_RCC,
    RESTRICTED_GEAR,
    SENSOR_ARRAY,
    _human,
    _mundane,
)
from tests.notice_asserts import has

VOICE_MODULATOR = "ebc25387-655f-4a24-8ae7-81548c097dac"


def test_voice_modulator_rating_adds_impersonation() -> None:
    out = compute(_human("voice", cyberware=[CyberwareInstall(ware_id=VOICE_MODULATOR, rating=2)]))
    assert out.derived["skill_bonus"]["Impersonation"] == 2


CUSTOM_LINK = "d63eb841-7b15-4539-9026-b90a4924aeeb"
FAIRLIGHT_CALIBAN = "1522dd91-99d9-42f9-ab19-b43e8e3c7322"
TRANSYS_AVALON = "01077e2d-4f67-428a-850d-250faad2007c"
PI_TAC_I = "b77b4cf8-8bdc-40bf-acca-f2afcca4965c"
PI_TAC_COPILOT = "d900aa9c-5914-4e5b-baa4-b4e0c0625123"
GLASSES = "b218dbd1-5706-4d9e-a6a7-ab9b658c3acd"
BINOCULARS = "1c6db3ed-a360-40b4-8118-9aca9d96001c"
FLARE_COMP = "7fc23c2f-b41a-46b0-9ed7-9dc93986fab3"
IMAGE_LINK = "2886d77a-1321-4a29-aec8-8040b9c5776f"
EARBUDS = "5d69d002-c33d-4d0f-9c4d-d78db4d78e5d"
SPATIAL = "3f086e04-8de6-4d4e-a503-a19cba8295f5"
BROWSE = "b3c0a6bd-e086-4971-be77-dc9a9cb2e174"
ARMOR_PROG = "a1e4b783-0751-43eb-b5bd-ee00f84b7bb3"
EXPLOIT = "67ea7c0c-1703-412b-80d3-9c23cc6d8291"
SINGLE_SENSOR = "2d4edef2-2891-4383-83f6-81f05cfbd046"
HANDHELD_HOUSING = "49bbc9d3-860d-47db-b4bc-8417f5b6ab65"
MOTION_SENSOR = "e853967a-a2b8-4d89-9a97-773034489a16"


def test_custom_commlink_rating_six_is_at_device_limit() -> None:
    out = compute(_mundane("dr-custom-6", commlinks=[CommlinkInstall(gear_id=CUSTOM_LINK, rating=6)]))
    row = out.derived["commlinks"][0]
    assert row["device_rating"] == 6
    assert row["avail"] == "12"
    assert out.derived["device_rating_limit"] == 6
    assert not has(out.derived["errors"], "engine.gear.deviceRatingOver")
    assert not has(out.derived["errors"], "engine.gear.availOver")


def test_custom_commlink_rating_seven_exceeds_device_rating() -> None:
    out = compute(_mundane("dr-custom-7", commlinks=[CommlinkInstall(gear_id=CUSTOM_LINK, rating=7)]))
    row = out.derived["commlinks"][0]
    assert row["device_rating"] == 7
    assert has(out.derived["errors"], "engine.gear.deviceRatingOver", value=7)


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
    assert not has(out.derived["errors"], "engine.gear.availOver")
    assert has(out.derived["errors"], "engine.gear.deviceRatingOver", name="Fairlight Caliban")


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
    assert not has(ok.derived["errors"], "engine.gear.deviceRatingOver")
    assert over.derived["sensors"][0]["device_rating"] == 7
    assert over.derived["sensors"][0]["avail"] == "7"
    assert has(over.derived["errors"], "engine.gear.deviceRatingOver", name="Sensor Array")
    assert not has(over.derived["errors"], "engine.gear.availOver")


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
    assert has(denied.derived["warnings"], "engine.gear.doesNotFit")


def test_a_deck_gives_its_owner_a_vr_initiative() -> None:
    """SR5 p.229: VR rolls Data Processing + Intuition, three dice in cold sim
    and four in hot. AR is the meat initiative, which the sheet already has."""
    attrs = default_attributes(find_metatype("Human", None))
    attrs["INT"] = 4
    out = compute(
        CharacterState(
            id="decker",
            name="Decker",
            priorities=Priorities(),
            metatype="Human",
            attributes=attrs,
            cyberdecks=[GearInstall(gear_id=ERIKA_DECK)],
        )
    )
    assert out.derived["matrix_initiative"] == {
        "device": "cyberdeck",
        "dataprocessing": 2,
        "value": 6,  # DP 2 + INT 4
        "cold_dice": 3,
        "hot_dice": 4,
    }


def test_the_coprocessor_die_lands_in_the_vr_initiative() -> None:
    """`matrixinitiativedice` had no surface until now (PR #48): the module's
    die shows up in both sim modes."""
    base = compute(_mundane("deck-only", cyberdecks=[GearInstall(gear_id=ERIKA_DECK)]))
    out = compute(
        _mundane(
            "deck-coproc",
            cyberdecks=[GearInstall(gear_id=ERIKA_DECK)],
            gear=[GearInstall(gear_id=MULTIDIMENSIONAL_COPROCESSOR)],
        )
    )
    assert base.derived["matrix_initiative"]["cold_dice"] == 3
    assert out.derived["matrix_initiative"]["cold_dice"] == 4
    assert out.derived["matrix_initiative"]["hot_dice"] == 5


def test_a_character_with_no_persona_has_no_matrix_initiative() -> None:
    assert compute(_mundane("meat")).derived["matrix_initiative"] is None


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
    assert has(out.derived["errors"], "engine.gear.capacityOver")


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
    assert has(out.derived["warnings"], "engine.gear.needsHost")


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
    assert not has(out.derived["warnings"], "engine.gear.programsOver")


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
    assert has(out.derived["warnings"], "engine.gear.programsOver", used=2, max=1)


def test_program_without_parent_is_dropped() -> None:
    out = compute(_mundane("loose-browse", programs=[GearInstall(gear_id=BROWSE)]))
    assert out.derived["programs"] == []
    assert has(out.derived["warnings"], "engine.gear.needsHost")
    assert out.derived["nuyen_spent"] == 0


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
    assert has(out.derived["warnings"], "engine.gear.needsHostKind", host="engine.host.cyberdeck")
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
    assert has(out.derived["errors"], "engine.gear.capacityOver")


def test_sensor_function_without_parent_is_dropped() -> None:
    out = compute(_mundane("loose-atmo", sensors=[GearInstall(gear_id=ATMOSPHERE)]))
    assert out.derived["sensors"] == []
    assert has(out.derived["warnings"], "engine.gear.needsHost")


DATASOFT = "1a55fbe3-b3c1-4568-882f-abe4dedb8572"
AGENT_APP = "2d8396ff-a4a9-4382-ab69-70d198856e7f"


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
    assert has(out.derived["warnings"], "engine.gear.needsCommlink")


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


MULTIDIMENSIONAL_COPROCESSOR = "8706c98d-b53b-4a29-b21b-a921030ae801"


def test_coprocessor_matrix_initiative_die_is_not_unimplemented() -> None:
    """Chummer keeps a "set" and an "add" flavour of the tag apart; the module
    is a +1 either way (DT p.65), so it lands in the same die count."""
    out = compute(_mundane("coproc", gear=[GearInstall(gear_id=MULTIDIMENSIONAL_COPROCESSOR)]))
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "matrixinitiativedice" not in tags


OVERCLOCKER = "554ca59c-22e6-46ef-9b05-250ec8abd728"


def test_overclocker_raises_top_cyberdeck_attack_attribute() -> None:
    base = compute(_mundane("oc-0", cyberdecks=[GearInstall(gear_id=ERIKA_DECK)]))
    oc = compute(_mundane("oc-1", quality_ids=[OVERCLOCKER], cyberdecks=[GearInstall(gear_id=ERIKA_DECK)]))
    assert base.derived["cyberdecks"][0]["attack"] == 4
    assert oc.derived["cyberdecks"][0]["attack"] == 5
    assert oc.derived["cyberdecks"][0]["overclocker"] == "attack"


def test_overclocker_without_a_cyberdeck_is_a_noop() -> None:
    out = compute(_mundane("oc-nodeck", quality_ids=[OVERCLOCKER]))
    assert out.derived["cyberdecks"] == []
    assert out.derived["errors"] == []


def test_codeslinger_requires_matrix_action() -> None:
    out = compute(_mundane("code-empty", quality_ids=[CODESLINGER]))
    assert has(out.derived["errors"], "engine.qualities.pickMatrixAction")
    assert out.derived["action_dice_pools"] == []


def test_dongles_give_a_commlink_attack_and_sleaze() -> None:
    """Attack / Stealth Dongle (DT p.61): `<modattack>{Rating}` on a
    commlink accessory becomes the commlink's Attack; same for Sleaze."""
    link = next(x for x in catalog()["commlinks"] if x["name"].startswith("Hermes Ikon"))
    attack = next(x["id"] for x in catalog()["gear"] if x["name"] == "Attack Dongle")
    stealth = next(x["id"] for x in catalog()["gear"] if x["name"] == "Stealth Dongle")
    host = CommlinkInstall(id="L", gear_id=link["id"])

    bare = compute(_human("bare", commlinks=[host])).derived["commlinks"][0]
    assert (bare["attack"], bare["sleaze"]) == (0, 0)

    out = compute(
        _human(
            "dongled",
            commlinks=[host],
            gear=[
                GearInstall(gear_id=attack, rating=3, parent_id="L"),
                GearInstall(gear_id=stealth, rating=2, parent_id="L"),
            ],
        )
    ).derived["commlinks"][0]
    assert (out["attack"], out["sleaze"]) == (3, 2)
    assert (out["dataprocessing"], out["firewall"]) == (bare["dataprocessing"], bare["firewall"])
