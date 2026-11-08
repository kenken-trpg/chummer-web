"""Free purchases of ware, armor and armor mods: Chummer's literal `<cost>0`.

The XML below is a synthetic save in Chummer's format, not a GUI-made one.
The reference is Chummer's own code: `Cyberware.Purchase`, and the armor and
armor mod pickers in `CharacterCreate`/`CharacterCareer`, set `Cost = "0"` on
a free purchase, and `Load` reads `<cost>` back from the save alone.
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


def _ware(cost: str, child_cost: str = "", parentid: str = "") -> str:
    return f"""<cyberwares><cyberware><name>Cybereyes Basic System</name><rating>2</rating>
      <grade>Standard</grade>{cost}<improvementsource>Cyberware</improvementsource>
      <children><cyberware><name>Vision Magnification</name><grade>Standard</grade>{child_cost}
        <parentid>{parentid}</parentid><improvementsource>Cyberware</improvementsource></cyberware></children>
    </cyberware></cyberwares>"""


def _armor(cost: str, mod: str = "Gel Packs", mod_cost: str = "", included: str = "False") -> str:
    return f"""<armors><armor><name>Armor Jacket</name>{cost}<equipped>True</equipped>
      <armormods><armormod><name>{mod}</name><rating>1</rating>{mod_cost}<included>{included}</included></armormod></armormods>
    </armor></armors>"""


def _ware_rows(out: CharacterState) -> dict[str, dict[str, Any]]:
    return {row["name"]: row for row in out.derived["cyberware"]}


@pytest.mark.parametrize(
    ("cost", "child_cost", "free_eyes", "free_child"),
    [
        ("<cost>0</cost>", "<cost>2000</cost>", True, False),
        ("", "<cost>0</cost>", False, True),
        ("<cost>0.00</cost>", "<cost>0</cost>", True, True),
        ("", "", False, False),
        ("<cost>bad</cost>", "<cost>1</cost>", False, False),
    ],
)
def test_free_ware_costs_nothing_and_keeps_its_essence(
    cost: str, child_cost: str, free_eyes: bool, free_child: bool
) -> None:
    state, out = _load(_ware(cost, child_cost))
    assert [row["free"] for row in state["cyberware"]] == [free_eyes, free_child]
    rows = _ware_rows(out)
    eyes, child = rows["Cybereyes Basic System"], rows["Vision Magnification"]
    assert (eyes["free"], child["free"]) == (free_eyes, free_child)
    assert eyes["nuyen"] == (0 if free_eyes else 6000)
    assert child["nuyen"] == (0 if free_child else 2000)
    # free is about nuyen only: the eye still costs its essence and holds the child
    _, paid = _load(_ware("", ""))
    assert eyes["essence"] == _ware_rows(paid)["Cybereyes Basic System"]["essence"] > 0
    assert child["parent_id"] == eyes["id"]


def test_ware_that_came_with_its_parent_is_included_not_free() -> None:
    state, out = _load(_ware("", "<cost>0</cost>", parentid="d6e9a9a4-0000-4000-8000-000000000001"))
    child = next(row for row in state["cyberware"] if row["included"])
    assert child["free"] is False
    assert _ware_rows(out)["Vision Magnification"]["free"] is False


@pytest.mark.parametrize(
    ("cost", "mod_cost", "free_armor", "free_mod", "nuyen"),
    [
        ("<cost>0</cost>", "<cost>1500</cost>", True, False, 1500),
        ("<cost>1000</cost>", "<cost>0</cost>", False, True, 1000),
        ("<cost>0</cost>", "<cost>0</cost>", True, True, 0),
        ("", "", False, False, 2500),
    ],
)
def test_free_armor_and_mod_are_priced_apart(
    cost: str, mod_cost: str, free_armor: bool, free_mod: bool, nuyen: int
) -> None:
    state, out = _load(_armor(cost, mod_cost=mod_cost))
    assert state["armor"][0]["free"] is free_armor
    assert state["armor_mods"][0]["free"] is free_mod
    row = out.derived["armor_items"][0]
    assert row["free"] is free_armor
    assert row["mods"][0]["free"] is free_mod
    assert row["nuyen"] == nuyen
    # still worn, and the mod still takes capacity and adds its armor
    _, paid = _load(_armor(""))
    assert row["equipped"]
    assert row["armor_value"] == paid.derived["armor_items"][0]["armor_value"]
    assert row["capacity_used"] == paid.derived["armor_items"][0]["capacity_used"]
    assert row["mod_armor"] == paid.derived["armor_items"][0]["mod_armor"] > 0


def test_mod_priced_off_a_free_armor_sees_its_own_cost_of_zero() -> None:
    """`ArmorMod` replaces `Armor Cost` with the armor's OwnCost, 0 when free."""
    _, free = _load(_armor("<cost>0</cost>", "YNT Softweave Armor", "<cost>Armor Cost</cost>"))
    _, paid = _load(_armor("", "YNT Softweave Armor", "<cost>Armor Cost</cost>"))
    assert paid.derived["armor_items"][0]["mods"][0]["nuyen"] == 1000
    mod = free.derived["armor_items"][0]["mods"][0]
    assert mod["nuyen"] == 0
    assert mod["free"] is False


def test_included_armor_mod_and_variable_price_pick_are_not_free() -> None:
    state, _ = _load(_armor("", mod_cost="<cost>0</cost>", included="True"))
    assert state["armor_mods"][0]["free"] is False
    # Clothing is `Variable(20-100000)`: a saved 0 cannot be a pick from that range
    clothing = "<armors><armor><name>Clothing</name><cost>{}</cost></armor></armors>"
    picked, out = _load(clothing.format(50))
    assert picked["armor"][0]["free"] is False
    assert out.derived["armor_items"][0]["nuyen"] == 50
    zero, out = _load(clothing.format(0))
    assert zero["armor"][0]["free"] is True
    assert out.derived["armor_items"][0]["nuyen"] == 0


def test_free_ware_and_armor_survive_json_and_chummer_round_trips() -> None:
    _, out = _load(_ware("<cost>0</cost>", "<cost>0</cost>") + _armor("<cost>0</cost>", mod_cost="<cost>0</cost>"))
    restored = import_character(out.model_dump(mode="json"))
    assert restored.derived["nuyen_spent"] == out.derived["nuyen_spent"]
    xml = state_to_chum5(restored)
    root = ET.fromstring(xml)
    for path in (
        "./cyberwares/cyberware",
        "./cyberwares/cyberware/children/cyberware",
        "./armors/armor",
        "./armors/armor/armormods/armormod",
    ):
        node = root.find(path)
        assert node is not None, path
        assert [c.text for c in node.findall("cost")] == ["0"], path
    again = import_character(chum5_to_state(xml)[0])
    # the Image Link the eyes come with is added back as included, not free
    assert [(row.free, row.included) for row in again.cyberware] == [(True, False), (True, False), (False, True)]
    assert again.armor[0].free and again.armor_mods[0].free
    assert again.derived["nuyen_spent"] == out.derived["nuyen_spent"]
