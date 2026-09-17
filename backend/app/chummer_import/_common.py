"""What every section shares: catalog lookup by id or name, and knowing which
entries in a save Chummer added itself."""

from __future__ import annotations

import functools
import uuid
import xml.etree.ElementTree as ET  # the Element type only — parsing goes through parse_untrusted
from typing import Any, NamedTuple

from ..data_loader._xml import _text, current_overlay_key, data_root
from ..notices import Notice, Phrase, notice

#: Names Chummer's data has since corrected, old spelling -> current one.
#: Matching is by `sourceid` first, but older saves carry none on these entries,
#: so the name is all there is to go on — and it is the one the data dropped.
_LEGACY_NAMES = {
    "biocompatability (cyberware)": "biocompatibility (cyberware)",
    "biocompatability (bioware)": "biocompatibility (bioware)",
    "dishevelled": "disheveled",
    "rapelling gloves": "rappelling gloves",
    "ondanstron": "ondansetron",
    "spirit of guidance": "guidance spirit",
    "silencer": "silencer/suppressor",
    **{
        f"metagenetic improvement ({a})": f"metagenic improvement ({a})"
        for a in ("body", "agility", "reaction", "strength", "charisma", "intuition", "logic", "willpower")
    },
}


def _by_name(rows: list[dict[str, Any]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for r in rows:
        n = (r.get("name") or "").strip()
        if n:
            out.setdefault(n.lower(), r["id"])
    for old, new in _LEGACY_NAMES.items():
        if new in out:
            out.setdefault(old, out[new])
    return out


# Data files whose entries a save can carry, for `_DataIndex` below.
_INDEXED_FILES = ("weapons.xml", "gear.xml", "armor.xml", "cyberware.xml", "bioware.xml", "vehicles.xml")


class _DataIndex(NamedTuple):
    hidden_ids: frozenset[str]
    #: names every entry of which is hidden, lower-cased — a fallback for a
    #: save without ids, safe only where no pickable entry shares the name
    hidden_names: frozenset[str]
    #: parent id -> lower-cased names of the gear / weapons its entry includes
    included: dict[str, frozenset[str]]


@functools.lru_cache(maxsize=4)
def _data_index(_overlay_key: str) -> _DataIndex:
    """What a save can hold that nobody picked: `<hide />` entries, and the
    `<gears>` / `<weapons>` a ware or vehicle entry brings with it.

    Chummer adds those itself — the Unarmed Attack on every character, a
    Survival Kit's lighter and compass, a vehicle's Sensor Array, a
    Datajack's connector cord — so a save lists them though nobody picked
    them. The app models them through their parent or not at all, and naming
    each one "could not be imported" buried the entries that really were lost.
    """
    hidden_ids: set[str] = set()
    hidden: set[str] = set()
    visible: set[str] = set()
    included: dict[str, frozenset[str]] = {}
    for filename in _INDEXED_FILES:
        root = data_root(filename)
        if root is None:
            continue
        for el in root.iter():
            eid = _text(el.find("id"))
            name = _text(el.find("name")).lower()
            if not eid or not name:
                continue
            if el.find("hide") is not None:
                hidden_ids.add(eid)
                hidden.add(name)
            else:
                visible.add(name)
            kids = {
                _text(n).lower()
                for sub in ("gears", "weapons")
                for holder in el.findall(sub)
                for n in holder.iter("name")
                if _text(n)
            }
            # `<usegear>Holster</usegear>` (Ares Victory: Wild Hunt) and
            # `<gear>Quicksilver Camera</gear>` (Telestrian Shamus) name the
            # gear in their own text rather than in a `<name>` child.
            kids |= {
                _text(n).lower()
                for holder in el.findall("gears")
                for n in holder.iter()
                if n.tag in ("gear", "usegear") and n.find("name") is None and _text(n)
            }
            if kids:
                included[eid] = frozenset(kids)
    return _DataIndex(frozenset(hidden_ids), frozenset(hidden - visible), included)


#: The id Chummer gives what it makes up rather than takes from its data — a
#: Shapeshifter's Bite (Vulpine Form), built from the metatype's critter powers.
_NO_SOURCE_ID = "00000000-0000-0000-0000-000000000000"


def _chummer_added(node: ET.Element) -> bool:
    """A `<hide />` entry, or one with no data behind it: Chummer put it
    there, nobody picked it."""
    index = _data_index(current_overlay_key())
    sid = _text(node.find("sourceid")) or _text(node.find("id"))
    if sid == _NO_SOURCE_ID:
        return True
    if sid:
        return sid in index.hidden_ids
    return _text(node.find("name")).lower() in index.hidden_names


def _unexpected_children(parent_id: str, nodes: list[ET.Element]) -> list[ET.Element]:
    """`nodes` minus what the parent's entry includes or Chummer adds itself.

    Matched by prefix as well: a Datajack's entry includes "Universal
    Connector Cord", which the save names "Universal Connector Cord (Meter)".
    """
    included = _data_index(current_overlay_key()).included.get(parent_id, frozenset())
    out = []
    for node in nodes:
        name = _text(node.find("name")).lower()
        if _chummer_added(node) or any(name == n or name.startswith(n + " ") for n in included):
            continue
        out.append(node)
    return out


class _Resolver:
    """name / sourceid -> catalog id for one bucket."""

    def __init__(self, rows: list[dict[str, Any]]):
        self.by_name = _by_name(rows)
        self.ids = {r["id"] for r in rows}

    def resolve(self, node: ET.Element, warn: list[Notice], kind: Phrase) -> str | None:
        sid = _text(node.find("sourceid")) or _text(node.find("guid"))
        if sid and sid in self.ids:
            return sid
        name = _text(node.find("name"))
        got = self.by_name.get(name.lower())
        if got:
            return got
        if name and not _chummer_added(node):
            warn.append(notice("engine.import.skippedUnknown", kind=kind, name=name))
        return None


def _is_uuid(text: str) -> bool:
    try:
        uuid.UUID(text)
    except ValueError:
        return False
    return True
