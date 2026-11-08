"""Free purchases of gear, commlinks, decks, drones and vehicles (`<cost>0`).

The XML below is a synthetic save in Chummer's format, not a GUI-made one.
The reference is Chummer's own code: every gear and vehicle picker in
`CharacterCreate`/`CharacterCareer`/`CharacterShared` sets `Cost = "0"` on a
free purchase, `Load` reads `<cost>` back from the save alone, and a child's
`Parent Cost` (`Gear.OwnCostPreMultipliers`) and a mod's `Vehicle Cost`
(`Vehicle.OwnCost`) are the parent's own price — 0 when it was free.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

import pytest

from app.characters import import_character
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.models import CharacterState
from tests.test_chummer_import import SAMPLE


def _load(xml: str) -> tuple[dict[str, Any], CharacterState]:
    state, _ = chum5_to_state(SAMPLE.replace(b"</character>", xml.encode() + b"</character>"))
    return state, import_character(state)


def _gear(name: str, cost: str, extra: str = "") -> str:
    return f"<gears><gear><name>{name}</name>{extra}{cost}<qty>1</qty></gear></gears>"


def _row(out: CharacterState, key: str, name: str) -> dict[str, Any]:
    return next(row for row in out.derived[key] if row["name"] == name)


@pytest.mark.parametrize(
    ("name", "extra", "bucket", "paid"),
    [
        ("Medkit", "<rating>3</rating>", "gear", 750),
        ("Meta Link", "<category>Commlinks</category>", "commlinks", 100),
        ("Erika MCD-1", "<category>Cyberdecks</category>", "cyberdecks", 49500),
    ],
)
def test_free_gear_costs_nothing_in_each_bucket(name: str, extra: str, bucket: str, paid: int) -> None:
    state, out = _load(_gear(name, "<cost>0</cost>", extra))
    assert [row["free"] for row in state[bucket]] == [True]
    row = _row(out, bucket, name)
    assert (row["nuyen"], row["free"]) == (0, True)
    _, bought = _load(_gear(name, "", extra))
    assert _row(bought, bucket, name)["nuyen"] == paid
    assert bought.derived["nuyen_spent"] - out.derived["nuyen_spent"] == paid


def test_a_child_priced_off_a_free_parent_costs_nothing_but_is_not_free() -> None:
    def jazz(cost: str) -> str:
        return (
            f"<gears><gear><name>Jazz</name><qty>1</qty>{cost}"
            "<children><gear><name>Pharmaceutical</name><qty>1</qty></gear></children></gear></gears>"
        )

    _, paid = _load(jazz(""))
    assert _row(paid, "gear", "Pharmaceutical")["nuyen"] == _row(paid, "gear", "Jazz")["nuyen"] > 0
    state, free = _load(jazz("<cost>0</cost>"))
    child = _row(free, "gear", "Pharmaceutical")
    assert (child["nuyen"], child["free"]) == (0, False)
    assert [row["free"] for row in state["gear"]] == [True, False]


def test_free_vehicle_and_drone_and_their_vehicle_cost_mod() -> None:
    xml = """<vehicles>
      <vehicle><name>Dodge Scoot (Scooter)</name>{cost}
        <mods><mod><name>Off-Road Suspension</name><rating>1</rating></mod></mods></vehicle>
      <vehicle><name>MCT Fly-Spy (Minidrone)</name>{cost}</vehicle></vehicles>"""
    _, paid = _load(xml.format(cost=""))
    state, free = _load(xml.format(cost="<cost>0</cost>"))
    assert [row["free"] for row in state["vehicles"] + state["drones"]] == [True, True]
    scoot, spy = _row(free, "vehicles", "Dodge Scoot (Scooter)"), _row(free, "drones", "MCT Fly-Spy (Minidrone)")
    assert (scoot["nuyen"], spy["nuyen"]) == (0, 0)
    assert scoot["free"] and spy["free"]
    # `Vehicle Cost * 0.25` follows the vehicle's own (free) price; the mod
    # itself is still a paid purchase that happens to cost 0
    paid_mod = _row(paid, "vehicles", "Dodge Scoot (Scooter)")["mods"][0]
    assert paid_mod["nuyen"] == 750
    assert scoot["mods"][0]["nuyen"] == 0
    assert not state["vehicle_mods"][0].get("free")


def test_included_gear_and_a_pick_of_zero_are_not_free() -> None:
    # Theme Music is `Variable(0-50)`: 0 is a price the player may pick
    state, out = _load(_gear("Theme Music", "<cost>0</cost>"))
    assert [row["free"] for row in state["apps"]] == [False]
    # what comes with its parent (`<parentid>`, `<included>`) is included
    xml = """<gears><gear><guid>11111111-1111-4111-8111-111111111111</guid><name>Meta Link</name>
      <category>Commlinks</category><qty>1</qty><children>
      <gear><name>Medkit</name><rating>1</rating><qty>1</qty><cost>0</cost>
        <parentid>11111111-1111-4111-8111-111111111111</parentid><included>True</included></gear>
      </children></gear></gears>"""
    state, _ = _load(xml)
    assert all(not row["free"] for bucket in ("gear", "commlinks") for row in state[bucket])


def test_free_gear_and_vehicles_survive_json_and_chummer_round_trips() -> None:
    xml = (
        "<gears><gear><name>Medkit</name><rating>3</rating><cost>0</cost><qty>1</qty></gear>"
        "<gear><name>Meta Link</name><category>Commlinks</category><cost>0</cost><qty>2</qty></gear></gears>"
        "<vehicles><vehicle><name>Dodge Scoot (Scooter)</name><cost>0</cost></vehicle></vehicles>"
    )
    _, out = _load(xml)
    restored = import_character(out.model_dump(mode="json"))
    assert restored.derived["nuyen_spent"] == out.derived["nuyen_spent"]
    root = ET.fromstring(state_to_chum5(restored))
    for path in ("./gears/gear", "./vehicles/vehicle"):
        for node in root.findall(path):
            assert [c.text for c in node.findall("cost")] == ["0"], node.findtext("name")
    again = import_character(chum5_to_state(ET.tostring(root))[0])
    assert again.gear[0].free and again.commlinks[0].free and again.vehicles[0].free
    assert again.commlinks[0].qty == 2
    assert again.derived["nuyen_spent"] == out.derived["nuyen_spent"]
