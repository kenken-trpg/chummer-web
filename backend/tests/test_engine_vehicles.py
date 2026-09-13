"""Vehicles and drones: mods, slots, mounts, autosofts."""

from app.data_loader import catalog
from app.engine import (
    compute,
)
from app.models import (
    CommlinkInstall,
    CyberwareInstall,
    GearInstall,
    VehicleModInstall,
    WeaponInstall,
    WeaponMountInstall,
)
from tests.engine_support import (
    ATMOSPHERE,
    CYBERLIMB_OPTIMIZATION,
    DEALER_CONNECTION,
    FORD_AMERICAR,
    HAND_BLADE,
    MADE_MAN,
    MECHANICAL_ARM,
    META_LINK,
    ORTHOSKIN,
    PREDATOR,
    RADIO_SHACK_RCC,
    SENSOR_ARRAY,
    _mundane,
)
from tests.notice_asserts import has

CLEARSIGHT = "149a8dd2-dfef-473f-94a4-1bdd77e4f855"


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


SKILL_AUTOSOFT = "87d24cff-e63b-4f73-a115-7aa5e29ea467"
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
    assert has(out.derived["warnings"], "engine.gear.pickSkill")
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
    assert not has(out.derived["warnings"], "engine.skills.pickSkill")


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
    assert has(out.derived["errors"], "engine.gear.vehicleCategorySlotsOver", category="engine.vehicleSlot.Powertrain")


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
    assert has(out.derived["warnings"], "engine.gear.doesNotFit")
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
    assert has(out.derived["warnings"], "engine.gear.mountOnVehicle")
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
    assert has(out.derived["warnings"], "engine.gear.needsHost")


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
    assert has(out.derived["warnings"], "engine.gear.doesNotFit")
    assert out.derived["nuyen_spent"] == 12000


GROUP_AUTOSOFT = "25235dcf-089a-4c17-bc8f-6a1f5b2fb0b6"
MANEUVERING = "9d81218f-ee70-4304-9a09-ac865d84b8e0"
TARGETING = "0949997a-acb7-49d9-9905-5ae2cd35626f"
SIGNATURE_MASKING = "a249d87f-ec07-4716-9c62-e26061e80eac"
HANDLING_ENH = "956a20f7-64f3-4160-88a0-d6d6b29b0bd1"
GECKO_TIPS = "06940788-ad0b-453c-bc8a-e54e6221c185"


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
    assert has(out.derived["warnings"], "engine.gear.pickGroup")


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
    assert not has(out.derived["warnings"], "engine.gear.pickGroup")


def test_model_maneuvering_autosoft() -> None:
    rcc = GearInstall(gear_id=RADIO_SHACK_RCC)
    out = compute(
        _mundane(
            "model-auto",
            rccs=[rcc],
            programs=[
                GearInstall(gear_id=MANEUVERING, rating=2, parent_id=rcc.id, extra="GM-Nissan Doberman (Medium)")
            ],
        )
    )
    row = out.derived["programs"][0]
    assert row["label"] == "Maneuvering Autosoft (GM-Nissan Doberman (Medium))"
    assert row["nuyen"] == 1000
    assert "GM-Nissan Doberman (Medium)" in row["extra_options"]
    assert not has(out.derived["warnings"], "engine.qualities.pickExtra")


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
    assert has(out.derived["errors"], "engine.gear.availOver", name="Signature Masking")


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
    assert has(over.derived["errors"], "engine.gear.vehicleSlotsOver")


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
    assert has(out.derived["errors"], "engine.gear.vehicleModCapacityOver")


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
    assert has(out.derived["warnings"], "engine.gear.pickExtra", name="Fake SIN")
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
    assert has(lone.derived["warnings"], "engine.gear.needsHost", name="Fake License")


def test_dealer_connection_matches_drone_and_watercraft_categories() -> None:
    drone = next(d for d in catalog()["drones"] if str(d.get("category") or "").startswith("Drones"))
    boat = next(v for v in catalog()["vehicles"] if v.get("category") == "Boats")
    d_base = compute(_mundane("dc-drone0", drones=[GearInstall(gear_id=drone["id"])]))
    d_deal = compute(_mundane("dc-drone1", quality_ids=[DEALER_CONNECTION], drones=[GearInstall(gear_id=drone["id"])]))
    b_base = compute(_mundane("dc-boat0", vehicles=[GearInstall(gear_id=boat["id"])]))
    b_deal = compute(_mundane("dc-boat1", quality_ids=[DEALER_CONNECTION], vehicles=[GearInstall(gear_id=boat["id"])]))
    # "Drones: …" is matched by prefix; "Boats" is matched via the Watercraft prefix list.
    assert d_deal.derived["nuyen_spent"] == int(round(d_base.derived["nuyen_spent"] * 0.9))
    assert b_deal.derived["nuyen_spent"] == int(round(b_base.derived["nuyen_spent"] * 0.9))


def test_made_man_discounts_restricted_vehicle() -> None:
    restricted = next(
        v for v in catalog()["vehicles"] if "R" in str(v.get("avail") or "").upper() and int(v.get("cost") or 0) > 0
    )
    base = compute(_mundane("mm-veh0", vehicles=[GearInstall(gear_id=restricted["id"])]))
    made = compute(_mundane("mm-veh1", quality_ids=[MADE_MAN], vehicles=[GearInstall(gear_id=restricted["id"])]))
    assert made.derived["nuyen_spent"] == int(round(base.derived["nuyen_spent"] * 0.9))
    assert made.derived["vehicles"][0]["discount_pct"] == 10


PROTOTYPE_TRANSHUMAN = "08c4dfad-3661-48d9-a265-43cce84e20d8"
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
    assert has(out.derived["errors"], "engine.qualities.pickExtra")


def test_cyberlimb_optimization_in_a_drone_arm_is_the_drones() -> None:
    """Ware in a vehicle mod gives the character nothing — so no pick either."""
    drone = GearInstall(gear_id=DOBERMAN)
    arm = VehicleModInstall(id="arm1", mod_id=DRONE_ARM, parent_id=drone.id)
    out = compute(
        _mundane(
            "dob-opt",
            drones=[drone],
            vehicle_mods=[arm],
            cyberware=[CyberwareInstall(id="opt", ware_id=CYBERLIMB_OPTIMIZATION, parent_id=arm.id)],
            skill_picks={"ware:opt:acc0": "Pistols"},
        )
    ).derived
    assert any(item["name"] == "Cyberlimb Optimization" for item in out["cyberware"])
    assert out["skill_pick_slots"] == []


def _vehicle_item(kind: str, name: str) -> dict:
    rows = catalog()[kind]
    rows = rows["items"] if isinstance(rows, dict) and "items" in rows else rows
    return next(item for item in rows if item["name"] == name)


def test_off_road_mods_move_the_second_value() -> None:
    """A "4/3" vehicle's off-road half takes `<offroad*>` mods: Off-Road
    Suspension trades 1 on-road Handling for 1 off-road, Speed Enhancement
    raises both Speeds (R5 p.154-155)."""
    xenon = _vehicle_item("vehicles", "Dodge Xenon")  # Handling 3/2, Speed 4/3
    assert (xenon["handling"], xenon["speed"]) == ("3/2", "4/3")
    car = GearInstall(gear_id=xenon["id"])
    mods = [
        VehicleModInstall(mod_id=_vehicle_item("vehicle_mods", "Off-Road Suspension")["id"], parent_id=car.id),
        VehicleModInstall(mod_id=_vehicle_item("vehicle_mods", "Speed Enhancement")["id"], parent_id=car.id, rating=2),
    ]
    row = compute(_mundane("offroad", vehicles=[car], vehicle_mods=mods)).derived["vehicles"][0]
    assert row["handling"] == "2/3"
    assert row["speed"] == "6/5"
    assert row["accel"] == "2"


def test_off_road_mods_do_nothing_on_a_single_value() -> None:
    """No second value printed, nothing for the off-road half to move."""
    car_spec = next(
        v
        for v in catalog()["vehicles"]
        if str(v.get("handling") or "").isdigit() and str(v.get("speed") or "").isdigit()
    )
    car = GearInstall(gear_id=car_spec["id"])
    mod = VehicleModInstall(mod_id=_vehicle_item("vehicle_mods", "Off-Road Suspension")["id"], parent_id=car.id)
    row = compute(_mundane("offroad-single", vehicles=[car], vehicle_mods=[mod])).derived["vehicles"][0]
    assert row["handling"] == str(int(car_spec["handling"]) - 1)
    assert "/" not in row["speed"]
