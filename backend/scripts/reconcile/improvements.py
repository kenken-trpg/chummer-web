"""How much of what a quality, an implant, a piece of gear, a spell or a martial art does reaches
Chummer through the export.

Chummer never runs a `<bonus>` when it opens a file: it uses the
improvements the save holds, as they are. So an effect the export writes no
improvement for does nothing in Chummer — a drake's armor did not count until
the powers' improvements were written (docs/fixtures/critter-powers). The
saves Chummer wrote are the statement of what it expects, so this counts the
improvements each kind of row made in each of them and how many the export
of the same character reproduces.

An improvement is matched on its source, its owner's name, its type, what it
names and its numbers — never a guid, which every file draws afresh: one
that names a row of the save (the quality a SpecificQuality grants, the
contact an AddContact adds) is read as that row's name. Only an improvement
whose owner is in the save counts: Chummer leaves a Text behind every time
it makes a lifestyle's free grid again (over a hundred "Public Grid"s naming
no row at all). A normal quality's owner must be in `<qualities>`; a
lifestyle quality's owner is its own nested row.

The figures are readings to work up, pinned by `FLOORS` so they cannot slide
back, and which types to write next is chosen from the per-type tables this
prints.
"""

from __future__ import annotations

import collections
import xml.etree.ElementTree as ET
from pathlib import Path

#: The sources counted, under the name each is reported by. An armor and the
#: mods on it are one row to the player.
GROUPS = {
    "Quality": ("Quality",),
    "LifestyleQuality": ("Quality",),
    "Cyberware": ("Cyberware",),
    "Bioware": ("Bioware",),
    "Gear": ("Gear",),
    "Armor": ("Armor", "ArmorMod"),
    "Power": ("Power",),
    "MentorSpirit": ("MentorSpirit",),
    "Spell": ("Spell",),
    "MartialArt": ("MartialArt",),
}

#: Reproduced improvements over Chummer's 34 test saves at the pinned ref, by
#: group. Raise one when the export writes more; a drop means an improvement
#: went missing.
FLOORS = {
    "Quality": 323,
    "LifestyleQuality": 6,
    "Cyberware": 51,
    "Bioware": 112,
    "Gear": 182,
    "Armor": 61,
    "Power": 69,
    "MentorSpirit": 37,
    "Spell": 15,
    "MartialArt": 1,
}

Key = tuple[str, ...]


def _number(text: str | None) -> str:
    """`2`, `2.0` and an absent field are the same number to Chummer."""
    try:
        value = float(text or 0)
    except ValueError:
        return (text or "").strip()
    return str(int(value)) if value.is_integer() else str(value)


def improvements(root: ET.Element) -> collections.Counter[Key]:
    """(group, owner, type, improved name, target, val, aug, min, max) for
    every improvement of a counted source whose owner is in the save."""
    from app.chummer_import._common import _LEGACY_NAMES

    def spelled(name: str) -> str:
        # an old save's spelling is the import's to read: "Biocompatability"
        return _LEGACY_NAMES.get(name.lower(), name.lower())

    rows = {el.findtext("guid") or "": el.findtext("name") or "" for el in root.iter() if el.find("guid") is not None}
    owners = {guid: spelled(name) for guid, name in rows.items()}
    qualities: dict[str, str] = {}
    for quality in root.findall("./qualities/quality"):
        for field in ("guid", "sourceid"):
            if quality.findtext(field):
                qualities[quality.findtext(field) or ""] = spelled(quality.findtext("name") or "")
    lifestyle_qualities = {
        value: spelled(quality.findtext("name") or "")
        for quality in root.findall("./lifestyles/lifestyle/lifestylequalities/lifestylequality")
        for field in ("guid", "id")
        if (value := quality.findtext(field))
    }
    group_of: dict[str, str] = {}
    for name, sources in GROUPS.items():
        for source in sources:
            group_of.setdefault(source, name)
    out: collections.Counter[Key] = collections.Counter()
    for imp in root.findall("./improvements/improvement"):
        group = group_of.get(imp.findtext("improvementsource") or "")
        source_name = imp.findtext("sourcename") or ""
        if group == "Quality" and source_name in lifestyle_qualities:
            group = "LifestyleQuality"
        owner = (
            qualities if group == "Quality" else lifestyle_qualities if group == "LifestyleQuality" else owners
        ).get(source_name)
        if group is None or owner is None:
            continue
        out[
            (
                group,
                owner,
                imp.findtext("improvementttype") or "",
                rows.get(imp.findtext("improvedname") or "", imp.findtext("improvedname") or ""),
                imp.findtext("target") or "",
                *(_number(imp.findtext(field)) for field in ("val", "aug", "min", "max")),
            )
        ] += 1
    return out


def quality_improvements(root: ET.Element) -> collections.Counter[Key]:
    """`improvements` of the qualities alone, without the group."""
    out: collections.Counter[Key] = collections.Counter()
    for key, count in improvements(root).items():
        if key[0] == "Quality":
            out[key[1:]] += count
    return out


def coverage(path: Path) -> tuple[collections.Counter[Key], collections.Counter[Key]]:
    """Chummer's improvements in one save, and those of them the export of
    the same character reproduces."""
    from app.characters import import_character
    from app.chummer_export import state_to_chum5
    from app.chummer_import import chum5_to_state

    raw = path.read_bytes()
    theirs = improvements(ET.fromstring(raw))
    exported = state_to_chum5(import_character(chum5_to_state(raw)[0]))
    ours = improvements(ET.fromstring(exported if isinstance(exported, bytes) else exported.encode()))
    return theirs, theirs & ours
