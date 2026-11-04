"""What the export copies from a data file onto an item, as Chummer's own
`Create` does when the item is bought: `Load` reads these off the save and
never looks the data up again."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from app.chummer_export.data_fields import _from_data


def _fields(kind: str, source_id: str) -> ET.Element:
    el = ET.Element("item")
    _from_data(el, kind, source_id)
    return el


def test_a_drone_keeps_the_mod_slots_its_data_gives() -> None:
    """The Roto-drone's built-in Rigger Interface adds 3 slots
    (`<mods><addslots>`), and it has its own drone and weapon mod slots."""
    drone = _fields("vehicle", "1291ab59-2483-42ca-b7a9-503b2c354cee")
    assert (drone.findtext("addslots"), drone.findtext("modslots"), drone.findtext("weaponmodslots")) == ("3", "7", "3")


def test_a_vehicle_without_drone_mod_slots_takes_its_body() -> None:
    """`Vehicle.Create` takes the body when the data names no `<modslots>`;
    a save without either opened at 0."""
    car = _fields("vehicle", "898906ec-f2b9-43a4-98ad-6f79230b9a0c")
    assert car.findtext("modslots") == car.findtext("body") == "11"
    assert car.find("addslots") is None


def test_what_ware_and_a_vehicle_mod_let_you_add_inside_them() -> None:
    """`Create` joins the data's categories; Chummer reads the joined list off
    the save alone, and offers nothing to add without it."""
    eyes = _fields("cyberware", _ids("cyberware.xml", "./cyberwares/cyberware", "Cybereyes Basic System")[0])
    assert eyes.findtext("subsystems") == "Eyeware"
    arm = _fields("mod", "af87f3e0-aca3-4459-9d40-1573c758d137")
    assert (arm.findtext("subsystems") or "").startswith("Bodyware,Headware,Cosmetic Enhancement,Cyberlimb,")


def test_an_armor_mod_keeps_the_gear_it_can_hold() -> None:
    hardpoint = _fields("armormod", "c2fdc729-bc1d-4d3a-a0da-1d5dfa3b897d")
    assert hardpoint.findtext("gearcapacity") == "1"


def _ids(file: str, path: str, name: str) -> list[str]:
    from app.data_loader._xml import parse_data

    return [n.findtext("id") or "" for n in parse_data(file).findall(path) if n.findtext("name") == name]
