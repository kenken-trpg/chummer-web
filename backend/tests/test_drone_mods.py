"""Rigger 5.0's optional drone modification rules (`<dronemods>`, R5 p.122)."""

from typing import Any

from app.catalog_view import public_catalog
from app.chummer_import.vehicles import _infer_drone_mods
from app.data_loader import catalog
from app.engine import compute
from app.models import GearInstall, SettingsState, VehicleModInstall
from app.settings_file import parse_settings_xml
from tests.engine_support import _mundane
from tests.notice_asserts import has

DOBERMAN = "9186a0a7-635f-4242-a0e8-238f48b17ca2"  # H5 S3 A1 B4 Ar4 P3 Se3
KANMUSHI = "1f3308cb-837a-45c5-b581-9fef48cd4d8c"  # Body 0
GOLDFISH = "Sony Goldfish (Microdrone)"  # Pilot 2
HANDLING_ENH = "956a20f7-64f3-4160-88a0-d6d6b29b0bd1"
ARMOR_DRONE = "dfa7cdcd-5d0e-4c9c-9f0b-90bf29ac5aff"
HANDLING_DRONE = "17da9812-5264-4ac6-a31c-3e8b7ddb6212"
PILOT_PROGRAM = "ed241716-0d10-4493-83c6-aa141a854ec3"
ACCEL_DOWNGRADE = "57a3c9c6-76ec-4f65-9747-001ca3f7515b"
SPEED_DOWNGRADE = "16aed61a-a163-4927-9b5d-7949c763abe3"
BODY_DOWNGRADE = "e6de30bf-310e-4a3d-b44a-9d98f4618964"
SMALL_DRONE_MOUNT = "9ee5e112-8ced-4266-9141-02ef18e33f43"

ON = SettingsState(drone_mods=True)


def _drone(gear_id: str, mods: list[tuple[str, int]], settings: SettingsState | None = None) -> Any:
    drone = GearInstall(gear_id=gear_id)
    out = compute(
        _mundane(
            "drone-mods",
            drones=[drone],
            vehicle_mods=[VehicleModInstall(mod_id=mod, parent_id=drone.id, rating=r) for mod, r in mods],
            settings=settings or SettingsState(),
        )
    )
    return out.derived["drones"][0], out.derived["errors"]


def test_the_settings_file_turns_the_rules_on() -> None:
    xml = "<settings><name>H</name><dronemods>True</dronemods><dronemodsmaximumpilot>True</dronemodsmaximumpilot></settings>"
    parsed = parse_settings_xml(xml)
    assert parsed.drone_mods is True
    assert parsed.drone_mods_maximum_pilot is True


def test_off_a_drone_fills_one_track_per_category() -> None:
    # Chummer's `OverR5Capacity`: without the rules a drone is fitted like a car
    row, errors = _drone(DOBERMAN, [(HANDLING_ENH, 1)])
    tracks = {item["category"]: item for item in row["slot_tracks"]}
    assert (tracks["Powertrain"]["used"], tracks["Powertrain"]["max"]) == (4, 4)
    assert errors == []


def test_on_a_drone_shares_one_pool() -> None:
    row, _ = _drone(DOBERMAN, [(HANDLING_ENH, 1)], ON)
    assert row["slot_tracks"] == []
    assert (row["slots_used"], row["slots_max"]) == (4, 4)


def test_on_armor_has_no_ceiling_and_slows_the_drone() -> None:
    # Armor 20 on Body 4 is 8 past 3 x Body: -2 Speed and Handling, -1 Accel
    row, _ = _drone(DOBERMAN, [(ARMOR_DRONE, 20)], ON)
    assert row["mods"][0]["rating"] == 20
    assert (row["armor"], row["speed"], row["handling"], row["accel"]) == ("20", "1", "3", "0")


def test_off_armor_stops_at_body_plus_armor_and_costs_no_speed() -> None:
    row, _ = _drone(DOBERMAN, [(ARMOR_DRONE, 20)])
    assert (row["armor"], row["speed"], row["handling"]) == ("8", "3", "5")


def test_a_stat_mod_stops_at_twice_the_printed_stat() -> None:
    # R5 p.123: Handling 5 goes no higher than 10
    row, _ = _drone(DOBERMAN, [(HANDLING_DRONE, 20)], ON)
    assert row["mods"][0]["rating"] == 10
    assert row["handling"] == "10"


def _goldfish_pilot(settings: SettingsState) -> int:
    gear_id = next(d["id"] for d in catalog()["drones"] if d["name"] == GOLDFISH)
    row, _ = _drone(gear_id, [(PILOT_PROGRAM, 6)], settings)
    return int(row["mods"][0]["rating"])


def test_pilot_is_held_to_double_only_under_its_own_setting() -> None:
    assert _goldfish_pilot(ON) == 6
    assert _goldfish_pilot(SettingsState(drone_mods=True, drone_mods_maximum_pilot=True)) == 4


def test_a_downgrade_may_not_take_a_stat_below_one() -> None:
    # Doberman Acceleration 1 -> 0
    _, errors = _drone(DOBERMAN, [(ACCEL_DOWNGRADE, 0)], ON)
    assert has(errors, "engine.gear.droneIllegalDowngrade")
    # Speed may reach 0: Kanmushi Speed 2 -> 1 is fine, and Body 0 -> -1 is not
    _, errors = _drone(KANMUSHI, [(SPEED_DOWNGRADE, 0)], ON)
    assert not has(errors, "engine.gear.droneIllegalDowngrade")
    _, errors = _drone(KANMUSHI, [(BODY_DOWNGRADE, 0)], ON)
    assert has(errors, "engine.gear.droneIllegalDowngrade")


def test_the_downgrade_check_waits_for_the_rules() -> None:
    _, errors = _drone(DOBERMAN, [(ACCEL_DOWNGRADE, 0)])
    assert not has(errors, "engine.gear.droneIllegalDowngrade")


def test_the_free_drone_mods_are_served_and_flagged() -> None:
    mods = {item["id"]: item for item in public_catalog()["vehicle_mods"]}
    assert mods[SPEED_DOWNGRADE]["optionaldrone"] is True
    assert mods[HANDLING_ENH]["optionaldrone"] is False
    mounts = {item["id"]: item for item in public_catalog()["weapon_mounts"]}
    assert mounts[SMALL_DRONE_MOUNT]["optionaldrone"] is True


def test_a_save_with_a_drone_mod_was_built_under_the_rules() -> None:
    st: dict[str, Any] = {"settings": {"name": "Standard"}}
    _infer_drone_mods(catalog(), st, [{"mod_id": SPEED_DOWNGRADE}], [])
    assert st["settings"]["drone_mods"] is True
    # an included one came with the drone and says nothing about the settings
    st = {"settings": {}}
    _infer_drone_mods(catalog(), st, [{"mod_id": SPEED_DOWNGRADE, "included": True}], [])
    _infer_drone_mods(catalog(), st, [{"mod_id": HANDLING_ENH}], [])
    assert "drone_mods" not in st["settings"]
    _infer_drone_mods(catalog(), st, [], [{"size_id": SMALL_DRONE_MOUNT}])
    assert st["settings"]["drone_mods"] is True


def test_ticking_rigger_5_turns_the_rules_on() -> None:
    row, _ = _drone(DOBERMAN, [(HANDLING_ENH, 1)], SettingsState(books=["SR5", "R5"]))
    assert row["slot_tracks"] == []
    # without R5 among the books, the categories come back
    row, _ = _drone(DOBERMAN, [(HANDLING_ENH, 1)], SettingsState(books=["SR5"]))
    assert row["slot_tracks"] != []


def test_a_settings_file_that_switched_them_off_wins_over_the_book() -> None:
    row, _ = _drone(DOBERMAN, [(HANDLING_ENH, 1)], SettingsState(books=["SR5", "R5"], drone_mods=False))
    assert row["slot_tracks"] != []
