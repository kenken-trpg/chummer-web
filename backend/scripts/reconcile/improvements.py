"""How much of what a quality does reaches Chummer through the export.

Chummer never runs a `<bonus>` when it opens a file: it uses the
improvements the save holds, as they are. So an effect the export writes no
improvement for does nothing in Chummer — a drake's armor did not count until
the powers' improvements were written (docs/fixtures/critter-powers). The
saves Chummer wrote are the statement of what it expects, so this counts the
improvements a quality made in each of them and how many the export of the
same character reproduces.

An improvement is matched on its quality's name, its type, what it names and
its numbers — never a guid, which every file draws afresh: one that names a
row of the save (the quality a SpecificQuality grants, the contact an
AddContact adds) is read as that row's name. Only an improvement whose
quality is in the save counts: Chummer leaves a Text behind every time it
makes a lifestyle's free grid again (over a hundred "Public Grid"s naming
no row at all), and a lifestyle quality's improvements are the lifestyles'
to write, not the qualities'. The figure is a
reading to work up, pinned by `FLOOR` so it cannot slide back: the export
reproduces three in five, and which types to write next is chosen
from the per-type table this prints.
"""

from __future__ import annotations

import collections
import xml.etree.ElementTree as ET
from pathlib import Path

#: Reproduced improvements over Chummer's 34 test saves at the pinned ref.
#: Raise it when the export writes more; a drop means an improvement went missing.
FLOOR = 206

Key = tuple[str, ...]


def _number(text: str | None) -> str:
    """`2`, `2.0` and an absent field are the same number to Chummer."""
    try:
        value = float(text or 0)
    except ValueError:
        return (text or "").strip()
    return str(int(value)) if value.is_integer() else str(value)


def quality_improvements(root: ET.Element) -> collections.Counter[Key]:
    """(quality, type, improved name, target, val, aug, min, max) for every
    improvement whose source is one of the save's qualities, counted."""
    rows = {el.findtext("guid") or "": el.findtext("name") or "" for el in root.iter() if el.find("guid") is not None}
    from app.chummer_import._common import _LEGACY_NAMES

    names: dict[str, str] = {}
    for quality in root.findall("./qualities/quality"):
        # an old save's spelling is the import's to read: "Biocompatability"
        name = quality.findtext("name") or ""
        name = _LEGACY_NAMES.get(name.lower(), name.lower())
        for field in ("guid", "sourceid"):
            if quality.findtext(field):
                names[quality.findtext(field) or ""] = name
    out: collections.Counter[Key] = collections.Counter()
    for imp in root.findall("./improvements/improvement"):
        owner = names.get(imp.findtext("sourcename") or "")
        if imp.findtext("improvementsource") != "Quality" or owner is None:
            continue
        out[
            (
                owner,
                imp.findtext("improvementttype") or "",
                rows.get(imp.findtext("improvedname") or "", imp.findtext("improvedname") or ""),
                imp.findtext("target") or "",
                *(_number(imp.findtext(field)) for field in ("val", "aug", "min", "max")),
            )
        ] += 1
    return out


def coverage(path: Path) -> tuple[collections.Counter[Key], collections.Counter[Key]]:
    """Chummer's quality improvements in one save, and those of them the
    export of the same character reproduces."""
    from app.characters import import_character
    from app.chummer_export import state_to_chum5
    from app.chummer_import import chum5_to_state

    raw = path.read_bytes()
    theirs = quality_improvements(ET.fromstring(raw))
    exported = state_to_chum5(import_character(chum5_to_state(raw)[0]))
    ours = quality_improvements(ET.fromstring(exported if isinstance(exported, bytes) else exported.encode()))
    return theirs, theirs & ours
