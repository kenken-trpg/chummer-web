"""The places a player keeps their things in — a backpack, the car, a
safehouse — go through a .chum5 as Chummer saves them: the lists
(`<gearlocations>`, `<armorlocations>`) and each row's `<location>`, the
guid of the one it is in.

Nothing is computed from where a thing is; it only has to come back."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog, catalog_list
from app.engine import compute
from app.models import CharacterState
from app.models.gear import ArmorInstall, CommlinkInstall, GearInstall, StorageLocation
from tests.engine_support import _mundane

BACKPACK = "7590bad8-5449-4f57-86b6-8b25f27857de"
CAR = "3b1f3c2e-2f7e-4a35-9a55-1d6d0e6b7a01"
CLOSET = "c4f1b2a0-8d55-4e0e-9a2e-3f9c7c0b1d22"


def _id(rows: list[dict], name: str) -> str:
    return next(str(row["id"]) for row in rows if row.get("name") == name)


def _reimport(state: CharacterState) -> CharacterState:
    return CharacterState.model_validate(chum5_to_state(state_to_chum5(compute(state)))[0])


def _state() -> CharacterState:
    return _mundane(
        "locations",
        gear_locations=[
            StorageLocation(id=BACKPACK, name="Backpack", notes="The blue one"),
            StorageLocation(id=CAR, name="Car"),
        ],
        armor_locations=[StorageLocation(id=CLOSET, name="Closet")],
        gear=[
            GearInstall(id="kit", gear_id=_id(catalog_list("gear"), "Medkit"), rating=3, location=BACKPACK),
            # what is inside the kit goes where the kit goes
            GearInstall(gear_id=_id(catalog_list("gear"), "Medkit Supplies"), parent_id="kit", location=CAR),
            GearInstall(gear_id=_id(catalog_list("gear"), "Flashlight")),
        ],
        commlinks=[CommlinkInstall(gear_id=_id(catalog_list("commlinks"), "Meta Link"), location=CAR)],
        programs=[GearInstall(gear_id=_id(catalog_list("programs"), "Browse"), location=BACKPACK)],
        armor=[
            ArmorInstall(armor_id=_id(catalog()["armor"], "Armor Jacket"), location=CLOSET),
            ArmorInstall(armor_id=_id(catalog()["armor"], "Armor Vest")),
        ],
    )


def test_the_places_and_whats_in_them_come_back() -> None:
    back = _reimport(_state())
    assert [(loc.id, loc.name, loc.notes) for loc in back.gear_locations] == [
        (BACKPACK, "Backpack", "The blue one"),
        (CAR, "Car", ""),
    ]
    assert [(loc.id, loc.name) for loc in back.armor_locations] == [(CLOSET, "Closet")]
    kit = next(row for row in back.gear if not row.parent_id and row.rating == 3)
    supplies = next(row for row in back.gear if row.parent_id)
    assert (kit.location, supplies.location) == (BACKPACK, None)
    assert [row.location for row in back.gear if not row.parent_id and row.id != kit.id] == [None]
    assert [row.location for row in back.commlinks] == [CAR]
    assert [row.location for row in back.programs] == [BACKPACK]
    assert [row.location for row in back.armor] == [CLOSET, None]


def test_written_as_chummer_does() -> None:
    root = ET.fromstring(state_to_chum5(compute(_state())))
    assert [(loc.findtext("guid"), loc.findtext("name")) for loc in root.findall("./gearlocations/location")] == [
        (BACKPACK, "Backpack"),
        (CAR, "Car"),
    ]
    assert root.findtext("./armorlocations/location/name") == "Closet"
    kit = next(g for g in root.findall("./gears/gear") if g.findtext("name") == "Medkit")
    assert kit.findtext("location") == BACKPACK
    # the supplies inside it name no place of their own
    assert kit.find("./children/gear/location") is None
    assert root.findtext("./armors/armor/location") == CLOSET


def test_a_place_no_longer_listed_is_not_written() -> None:
    state = _state()
    state.gear_locations = []
    root = ET.fromstring(state_to_chum5(compute(state)))
    assert root.find("gearlocations") is None
    assert [g.findtext("location") for g in root.findall("./gears/gear") if g.find("location") is not None] == []


def test_where_a_thing_is_costs_nothing() -> None:
    plain = _state()
    plain.gear_locations, plain.armor_locations = [], []
    for rows in (plain.gear, plain.commlinks, plain.programs, plain.armor):
        for row in rows:
            row.location = None
    assert compute(_state()).derived["nuyen"] == compute(plain).derived["nuyen"]


_SAVES = sorted((Path(__file__).resolve().parents[1] / "vendor" / "chummer-tests").rglob("*.chum5"))
_LISTS = (("gearlocations", "./gears/gear"), ("armorlocations", "./armors/armor"))


def _placed(root: ET.Element) -> tuple[list[tuple[str, str]], dict[tuple[str, str], list[str]]]:
    """The places, and for each row of its own (by list and name) the names
    of the places it is in."""
    places: list[tuple[str, str]] = []
    rows: dict[tuple[str, str], list[str]] = {}
    for list_tag, row_path in _LISTS:
        named = {loc.findtext("guid"): loc.findtext("name") or "" for loc in root.findall(f"./{list_tag}/location")}
        places += [(list_tag, name) for name in named.values()]
        for row in root.findall(row_path):
            rows.setdefault((row_path, row.findtext("name") or ""), []).append(
                named.get(row.findtext("location") or "", "")
            )
    return places, {key: sorted(where) for key, where in rows.items()}


@pytest.mark.skipif(not _SAVES, reason="Chummer's test saves are fetched by `make reconcile`; absent in CI")
@pytest.mark.parametrize("path", _SAVES, ids=lambda p: p.stem)
def test_chummers_own_saves_keep_every_place(path: Path) -> None:
    """Every place in Chummer's test characters, and what is in each — for
    the rows the export keeps (a focus is written apart; a row the import
    leaves out is a question for `--roundtrip`)."""
    original = ET.fromstring(path.read_bytes())
    state = CharacterState.model_validate(chum5_to_state(path.read_bytes())[0])
    exported = ET.fromstring(state_to_chum5(compute(state)))
    their_places, their_rows = _placed(original)
    our_places, our_rows = _placed(exported)
    assert our_places == their_places
    for key in their_rows.keys() & our_rows.keys():
        if len(their_rows[key]) == len(our_rows[key]):
            assert our_rows[key] == their_rows[key], key
