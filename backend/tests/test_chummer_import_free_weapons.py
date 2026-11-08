"""Free purchases use Chummer's literal `<cost>0`, not included equipment.

The XML below is a synthetic save in Chummer's format. It is not an actual
GUI-generated save; CharacterShared's free purchase and WeaponAccessory's
OwnCost/Weapon Cost handling provide the independent reference.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from app.characters import import_character
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.models import CharacterState
from tests.test_chummer_import import SAMPLE


def _purchase(weapon_cost: str, accessory_cost: str, accessory: str = "Laser Sight", qty: int = 1) -> CharacterState:
    xml = f"""<weapons><weapon><name>AK-97</name>{weapon_cost}<qty>{qty}</qty>
      <accessories><accessory><name>{accessory}</name>{accessory_cost}
        <included>False</included><mount>Top</mount><equipped>True</equipped>
      </accessory></accessories></weapon></weapons>""".encode()
    state, _ = chum5_to_state(SAMPLE.replace(b"</character>", xml + b"</character>"))
    return import_character(state)


@pytest.mark.parametrize(
    ("weapon_cost", "accessory_cost", "free_weapon", "free_accessory", "cost"),
    [
        ("<cost>0</cost>", "<cost>125</cost>", True, False, 125),
        ("<cost>950</cost>", "<cost>0</cost>", False, True, 950),
        ("<cost>0.00</cost>", "<cost>0</cost>", True, True, 0),
        ("", "", False, False, 1075),
        ("<cost>1</cost>", "<cost>1</cost>", False, False, 1075),
        ("<cost>bad</cost>", "<cost>bad</cost>", False, False, 1075),
    ],
)
def test_free_price_is_independent_for_weapon_and_accessory(
    weapon_cost: str, accessory_cost: str, free_weapon: bool, free_accessory: bool, cost: int
) -> None:
    out = _purchase(weapon_cost, accessory_cost, qty=2)
    weapon, accessory = out.weapons[0], out.weapon_accessories[0]
    assert (weapon.free, accessory.free) == (free_weapon, free_accessory)
    assert not weapon.included and not accessory.included
    row = out.derived["weapons"][0]
    assert row["nuyen"] == cost * 2
    assert row["free"] is free_weapon
    assert row["accessories"][0]["free"] is free_accessory
    # Free purchases retain the normal accessory mount and Accuracy bonus.
    assert row["accessories"][0]["mount"] == "Top"
    assert row["accuracy"] == "6"
    paid = _purchase("", "", qty=2)
    assert paid.derived["nuyen_spent"] - out.derived["nuyen_spent"] == (1075 - cost) * 2


def test_free_weapon_still_prices_accessories_using_its_own_cost() -> None:
    free = _purchase("<cost>0</cost>", "<cost>Weapon Cost</cost>", "Smartgun System, Internal")
    paid = _purchase("", "<cost>Weapon Cost</cost>", "Smartgun System, Internal")
    assert free.derived["weapons"][0]["nuyen"] == 0
    assert paid.derived["weapons"][0]["nuyen"] == 1900
    assert free.weapons[0].free
    assert not free.weapon_accessories[0].free  # formula retained, no free purchase


def test_free_purchases_survive_json_and_chummer_round_trips() -> None:
    out = _purchase("<cost>0</cost>", "<cost>0</cost>", qty=3)
    restored = import_character(out.model_dump(mode="json"))
    xml = state_to_chum5(restored)
    root = ET.fromstring(xml)
    weapon = root.find("./weapons/weapon")
    assert weapon is not None
    assert [node.text for node in weapon.findall("cost")] == ["0"]
    assert weapon.findtext("parentid") in (None, "")
    accessory = weapon.find("./accessories/accessory")
    assert accessory is not None
    assert [node.text for node in accessory.findall("cost")] == ["0"]
    assert accessory.findtext("included") == "False"
    again = import_character(chum5_to_state(xml)[0])
    assert again.weapons[0].free and again.weapon_accessories[0].free
    assert again.weapons[0].qty == 3
    assert again.derived["nuyen_spent"] == out.derived["nuyen_spent"]


def test_included_and_catalogue_zero_cost_accessories_are_not_free_purchases() -> None:
    xml = b"""<weapons><weapon><name>Ares Predator V</name><accessories>
      <accessory><name>Smartgun System, Internal</name><cost>0</cost><included>True</included></accessory>
      <accessory><name>Vintage</name><cost>0</cost><included>False</included></accessory>
      </accessories></weapon></weapons>"""
    state, _ = chum5_to_state(SAMPLE.replace(b"</character>", xml + b"</character>"))
    assert len(state["weapon_accessories"]) == 2
    assert all(not row["free"] for row in state["weapon_accessories"])
    out = import_character(state)
    assert all(not row.free for row in out.weapon_accessories)
    included = next(row for row in out.weapon_accessories if row.included)
    root = ET.fromstring(state_to_chum5(out))
    saved = next(a for a in root.findall("./weapons/weapon/accessories/accessory") if a.findtext("included") == "True")
    assert saved.findtext("cost") == "0"
    assert included.accessory_id == saved.findtext("sourceid")
