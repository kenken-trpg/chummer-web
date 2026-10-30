"""The fields of an item Chummer reads from the save alone, copied from the
data file the way Chummer's own save has them."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from functools import cache

from ..data_loader._xml import parse_data
from ._common import _sub

#: What Chummer's `Load` of each kind of item reads from the save alone: the
#: fields its own save copies from the data file when the item is made. With
#: no `<cost>`, `<armor>` or `<damage>` in the save, Chummer opens the item at
#: 0 nuyen, no armor and no damage. Each list is what the 34 test saves carry
#: verbatim from the data, in at least three saves.
_FROM_DATA: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "gear": (
        "gear.xml",
        "./gears/gear",
        (
            "category",
            "minrating",
            "capacity",
            "armorcapacity",
            "avail",
            "cost",
            "costfor",
            "devicerating",
            "attack",
            "sleaze",
            "dataprocessing",
            "firewall",
            "canformpersona",
            "source",
            "page",
        ),
    ),
    "weapon": (
        "weapons.xml",
        "./weapons/weapon",
        (
            "category",
            "type",
            "spec",
            "reach",
            "accuracy",
            "damage",
            "ap",
            "mode",
            "rc",
            "ammo",
            "ammocategory",
            "conceal",
            "range",
            "useskill",
            "allowaccessory",
            "avail",
            "cost",
            "source",
            "page",
        ),
    ),
    "accessory": (
        "weapons.xml",
        "./accessories/accessory",
        ("accuracy", "rc", "rcgroup", "rcdeployable", "ammoslots", "conceal", "avail", "cost", "source", "page"),
    ),
    "armor": (
        "armor.xml",
        "./armors/armor",
        ("category", "armor", "armoroverride", "armorcapacity", "avail", "cost", "source", "page"),
    ),
    "armormod": (
        "armor.xml",
        "./mods/mod",
        ("category", "armor", "armorcapacity", "maxrating", "avail", "cost", "source", "page"),
    ),
    "cyberware": (
        "cyberware.xml",
        "./cyberwares/cyberware",
        ("category", "minrating", "ess", "capacity", "avail", "cost", "source", "page"),
    ),
    "bioware": (
        "bioware.xml",
        "./biowares/bioware",
        ("category", "minrating", "ess", "capacity", "avail", "cost", "source", "page"),
    ),
    "vehicle": (
        "vehicles.xml",
        "./vehicles/vehicle",
        (
            "category",
            "handling",
            "accel",
            "speed",
            "pilot",
            "body",
            "armor",
            "sensor",
            "seats",
            "modslots",
            "avail",
            "cost",
            "source",
            "page",
        ),
    ),
    "mod": ("vehicles.xml", "./mods/mod", ("category", "slots", "capacity", "avail", "cost", "source", "page")),
    "lifestyle": (
        "lifestyles.xml",
        "./lifestyles/lifestyle",
        ("cost", "dice", "lp", "multiplier", "costforarea", "costforcomforts", "costforsecurity", "source", "page"),
    ),
    "lifestylequality": (
        "lifestyles.xml",
        "./qualities/quality",
        ("category", "cost", "lp", "multiplier", "source", "page"),
    ),
}


#: Fields Chummer's save names apart from its data: the data file's
#: `<rating>` is the highest rating, which the save keeps as `<maxrating>`
#: (its `<rating>` is the one chosen). Without it Chummer caps the rating at
#: 0, and a price or essence of `Rating * …` comes to nothing.
#: A vehicle's off-road stats are the same field: Chummer splits `3/2` itself,
#: but reads a plain `3` off road from `<offroadspeed>` and the like, saved at
#: the same value, and takes a missing one for 0. A lifestyle quality's
#: `<multiplierbaseonly>` (Extra Secure's 20%) is saved as `<basemultiplier>`.
_SAVED_AS: dict[str, dict[str, str]] = {
    **{kind: {"maxrating": "rating"} for kind in ("gear", "armor", "cyberware", "bioware", "mod")},
    "vehicle": {"offroadhandling": "handling", "offroadaccel": "accel", "offroadspeed": "speed"},
    "lifestylequality": {"basemultiplier": "multiplierbaseonly"},
}


@cache
def _definitions(kind: str) -> dict[str, ET.Element]:
    file, path, _ = _FROM_DATA[kind]
    return {node.findtext("id") or "": node for node in parse_data(file).findall(path)}


def _from_data(el: ET.Element, kind: str, source_id: str, *, included: bool = False) -> None:
    """Copy onto `el` what Chummer reads of the item from the save only, as
    its own save has it: the data file's text. What `el` already says (a
    price the player set) stays. Chummer saves a piece that came with its
    parent at `<cost>0`."""
    if included and el.find("cost") is None:
        _sub(el, "cost", 0)
    definition = _definitions(kind).get(source_id)
    if definition is None:
        return
    renamed = _SAVED_AS.get(kind, {})
    for tag in (*_FROM_DATA[kind][2], *renamed):
        node = definition.find(renamed.get(tag, tag))
        if el.find(tag) is None and node is not None and not len(node) and (node.text or "").strip():
            _sub(el, tag, node.text)
