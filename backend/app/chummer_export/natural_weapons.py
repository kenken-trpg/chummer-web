"""The attacks a character was born with, as Chummer saves them.

A `<naturalweapon>` is not in `weapons.xml`: Chummer's
`AddImprovementCollection.naturalweapon` builds a Weapon from the node's
fields, adds it to the character's weapons and ties it to its owner with a
`Weapon` improvement. Chummer keeps both on load and never runs the node
again, so a save without them has no bite. The node sits in a metavariant's
`<bonus>` (a Shapeshifter's), a critter power's (Natural Weapon (Bite)) or,
outside the bonus, in a quality's `<naturalweapons>` (an Infected's, which
`Quality.Create` runs as one more bonus).

The import skips the weapon again (its source id is the empty GUID, see
`chummer_import._common`): the engine makes it from the same node.
"""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET

from ..data_loader import catalog
from ._common import _sub
from .data_fields import _from_data
from .improvements import _Imp, _write_improvements

__all__ = ["weapons_of", "write_added_weapon", "write_natural_weapons"]

#: `Weapon.SourceIDString` of a weapon built rather than taken from the data
EMPTY_GUID = "00000000-0000-0000-0000-000000000000"
#: `Tab_Critter` in the default language, the category the builder gives it
CATEGORY = "Critter Powers"


def weapons_of(root: ET.Element) -> ET.Element:
    """The one `<weapons>` under `<character>`, made on first use."""
    found = root.find("weapons")
    return found if found is not None else _sub(root, "weapons")


def write_added_weapon(root: ET.Element, owner_guid: str, weapon_id: str) -> str | None:
    """The weapon an `<addweapon>` makes — a grenade's, a Survival Kit's
    knife, a shield's, a Fangs quality's — as `Gear.Create`, `Armor.Create`
    and `Quality.Create` add it: a row of the character's weapons with its
    owner's guid in `<parentid>`, at no cost. Chummer never makes it again on
    load, so a save without it has no grenade to throw. Returns the weapon's
    guid, for the owner's `<weaponguid>`; `None` if the catalogue has no such
    weapon. The import skips the row (it has a parent): the engine makes it
    from the same owner."""
    spec = next((row for row in catalog()["weapons"] if row["id"] == weapon_id), None)
    if spec is None:
        return None
    guid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"chummer-web:added-weapon:{owner_guid}:{weapon_id}"))
    weapon = _sub(weapons_of(root), "weapon")
    for key, value in {
        "sourceid": weapon_id,
        "guid": guid,
        "name": spec.get("name") or "",
        "parentid": owner_guid,
        "cost": 0,
        "qty": 1,
        "included": "False",
        "cyberware": "False",
    }.items():
        _sub(weapon, key, value)
    _from_data(weapon, "weapon", weapon_id)
    # what the data file lacks keeps the catalogue's value
    for key in ("category", "type", "reach", "damage", "ap", "accuracy", "mode", "rc", "ammo", "useskill"):
        if weapon.find(key) is None:
            _sub(weapon, key, spec.get(key) or "")
    return guid


def write_natural_weapons(root: ET.Element, node: ET.Element | None, owner: str, source: str) -> None:
    """A weapon and its `Weapon` improvement for each `<naturalweapon>` in
    `node`, owned by `owner` (the guid or id the owner's other improvements
    name) from improvement source `source`."""
    if node is None or not owner:
        return
    rows = []
    for index, spec in enumerate(node.iter("naturalweapon")):
        guid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"chummer-web:natural-weapon:{owner}:{index}"))
        _write_weapon(weapons_of(root), spec, guid, owner)
        rows.append(_Imp(kind="Weapon", improved=guid))
    _write_improvements(root, rows, owner, source)


def _write_weapon(weapons: ET.Element, spec: ET.Element, guid: str, owner: str) -> None:
    def field(tag: str, default: str) -> str:
        return (spec.findtext(tag) or "").strip() or default

    weapon = _sub(weapons, "weapon")
    for key, value in {
        "sourceid": EMPTY_GUID,
        "guid": guid,
        "name": field("name", "Natural Weapon"),
        "category": CATEGORY,
        "type": "Melee",
        "reach": field("reach", "0"),
        "damage": field("damage", "({STR})S"),
        "ap": field("ap", "0"),
        "mode": "0",
        "rc": "0",
        "ammo": "0",
        "accuracy": field("accuracy", "Physical"),
        "conceal": "0",
        "avail": "0",
        "cost": "0",
        "useskill": field("useskill", ""),
        "source": field("source", "SR5"),
        "page": field("page", "0"),
        "parentid": owner,
        "qty": 1,
        "allowaccessory": "False",
        "equipped": "True",
        "included": "False",
        "cyberware": "False",
    }.items():
        _sub(weapon, key, value)
