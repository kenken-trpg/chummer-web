"""The fields of an item Chummer reads from the save alone, copied from the
data file the way Chummer's own save has them."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Callable
from functools import lru_cache

from ..data_loader._xml import current_overlay_key, parse_data
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
            "sizecategory",
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
        ("category", "armor", "armorcapacity", "gearcapacity", "maxrating", "avail", "cost", "source", "page"),
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
            "powertrainmodslots",
            "protectionmodslots",
            "weaponmodslots",
            "bodymodslots",
            "electromagneticmodslots",
            "cosmeticmodslots",
            "avail",
            "cost",
            "source",
            "page",
        ),
    ),
    "mod": (
        "vehicles.xml",
        "./mods/mod",
        ("category", "slots", "capacity", "conditionmonitor", "avail", "cost", "source", "page"),
    ),
    "quality": (
        "qualities.xml",
        "./qualities/quality",
        (
            "contributetolimit",
            "contributetobp",
            "doublecareer",
            "canbuywithspellpoints",
            "metagenic",
            "mutant",
            "implemented",
            "stagedpurchase",
            "source",
            "page",
        ),
    ),
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
#: `<multiplierbaseonly>` (Extra Secure's 20%) is saved as `<basemultiplier>`,
#: and a quality's `<karma>` as `<bp>`.
_SAVED_AS: dict[str, dict[str, str]] = {
    **{kind: {"maxrating": "rating"} for kind in ("gear", "armor", "cyberware", "bioware", "mod")},
    "vehicle": {"offroadhandling": "handling", "offroadaccel": "accel", "offroadspeed": "speed"},
    "lifestylequality": {"basemultiplier": "multiplierbaseonly"},
    "quality": {"bp": "karma"},
}


def _joined(definition: ET.Element, path: str) -> str:
    return ",".join(t for node in definition.findall(path) if (t := (node.text or "").strip()))


def _vehicle_fields(definition: ET.Element) -> dict[str, str]:
    # `Vehicle.Create` reads the extra mod slots a built-in mod gives from
    # `<mods><addslots>`, and takes a drone's mod slots for its body when the
    # data names none (Rigger 5.0's drone mods read them)
    out = {"addslots": (definition.findtext("mods/addslots") or "").strip()}
    if definition.find("modslots") is None:
        out["modslots"] = (definition.findtext("body") or "").strip()
    return out


#: Fields `Create` builds from the data rather than copying one element: the
#: categories a piece of ware or a vehicle mod lets you add inside it, which
#: Chummer reads off the save alone — with none, it offers nothing to add.
_COMPOSED: dict[str, Callable[[ET.Element], dict[str, str]]] = {
    "cyberware": lambda d: {"subsystems": _joined(d, "allowsubsystems/category")},
    "bioware": lambda d: {"subsystems": _joined(d, "allowsubsystems/category")},
    "mod": lambda d: {"subsystems": _joined(d, "subsystems/subsystem")},
    "vehicle": _vehicle_fields,
}


def _definitions(kind: str) -> dict[str, ET.Element]:
    """Each item of `kind` by id, in the custom data in force if any."""
    return _definitions_for(kind, current_overlay_key())


@lru_cache(maxsize=64)
def _definitions_for(kind: str, _overlay_key: str) -> dict[str, ET.Element]:
    """`_definitions` for one data set: keyed on it, so a character with
    custom data and one without never read each other's index (as
    `chummer_import._common._data_index` is)."""
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
    for tag, value in (_COMPOSED[kind](definition) if kind in _COMPOSED else {}).items():
        if value and el.find(tag) is None:
            _sub(el, tag, value)
