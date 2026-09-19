"""The parts of `scripts/chum5_reconcile.py` that read a save's own prices.

The script itself needs Chummer's test files and a network fetch, so it is a
tool rather than a test. These cover the two pieces that decide what a gap
*means* — whether the save's price list has moved under us, and which pieces
were never priced at all — because both are read off the XML and both have a
failure mode that silently invents findings.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from scripts.chum5_reconcile import _stored_prices


def _save(body: str) -> ET.Element:
    return ET.fromstring(f"<character>{body}</character>")


def test_a_piece_that_came_with_its_parent_is_not_a_price() -> None:
    """Chummer writes `cost` 0 and a `parentid` for an item it granted.

    Reading that 0 as the item's price reports it as drift against every
    catalogue entry that charges for it — `Camera, Micro` did exactly that in
    three of the test saves before this filter.
    """
    root = _save("""
        <gears>
          <gear><name>Camera, Micro</name><cost>0</cost>
                <parentid>876ba7c9-b2d8-402f-8e97-019a72c99468</parentid></gear>
          <gear><name>Betameth</name><cost>30</cost><parentid></parentid></gear>
        </gears>
    """)
    assert _stored_prices(root) == [("otherGear", "Betameth", 30.0)]


def test_a_cost_that_is_an_expression_is_left_alone() -> None:
    """`Rating * 25` is the catalogue formula, not a number this can compare."""
    root = _save("""
        <gears>
          <gear><name>Slap Patch, Stim Patch</name><cost>Rating * 25</cost></gear>
          <gear><name>Kamikaze</name><cost>100</cost></gear>
        </gears>
    """)
    assert _stored_prices(root) == [("otherGear", "Kamikaze", 100.0)]


def test_every_priced_kind_of_element_is_read() -> None:
    """A weapon accessory is paid for separately, so it is priced on its own."""
    root = _save("""
        <armors><armor><name>Chameleon Suit</name><cost>1700</cost>
          <gears><gear><name>Holster</name><cost>0</cost><parentid>x</parentid></gear></gears>
        </armor></armors>
        <weapons><weapon><name>Survival Knife</name><cost>100</cost>
          <accessories><accessory><name>Personalized Grip</name><cost>100</cost></accessory></accessories>
        </weapon></weapons>
        <cyberwares><cyberware><name>Claws, Retractable (Hands)</name><cost>1000</cost></cyberware></cyberwares>
    """)
    assert sorted(_stored_prices(root)) == [
        ("armor", "Chameleon Suit", 1700.0),
        ("ware", "Claws, Retractable (Hands)", 1000.0),
        ("weaponAccessories", "Personalized Grip", 100.0),
        ("weapons", "Survival Knife", 100.0),
    ]
