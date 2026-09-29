"""The export against the save Chummer wrote, field by field.

This answers the question `roundtrip` cannot. Reading the export back with
this app's own importer is blind by construction to anything Chummer needs
and this app does not: a field neither side reads comes back unchanged
because neither side looked, and the round trip calls that a pass. Chummer is
the other reader of these files, and the only statement of what it expects is
the save it wrote — so this compares the original against the export over the
character's own header (who they are, what they were built with, what the
build was allowed to spend), plus the two things Chummer keeps exactly one of
and loads field by field: the tradition and the mentor spirit. Everything
else a save holds is a list this app rebuilds from its own catalogue, which
is supposed to differ.

It fails on a field *both* sides state with different text, and on one
Chummer states and reads back that the export leaves out. A field Chummer
writes and never reads back — an attribute's `totalvalue`, recomputed on load
— is named in `_ACCEPTED_DROPS` with the reason, and reported rather than
counted against the export. Nothing else is: a field this app has not thought
about fails the run, which is what makes this a gate (CI's `fidelity` job)
rather than a reading to work down.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

#: A value Chummer wrote that says nothing: the element is there because
#: Chummer writes every field, not because this character has one.
_EMPTY_VALUES = {"", "0", "0.0", "False"}

#: Leaf elements whose text has to survive a round trip, checked by value
#: rather than by presence.
#:
#: `<settings>` is deliberately not among them. These saves are 5.202-era,
#: where it held a bare file name (`default.xml`); the Chummer this app is
#: pinned to takes it as a key into its loaded settings — a GUID for a
#: shipped preset. The two eras spell the same field differently, so there is
#: nothing here to compare against. `tests/test_settings.py` pins the rule
#: instead.
_SAME_VALUE_TAGS = (
    "gameplayoption",
    "buildmethod",
    "metatype",
    "metavariant",
    "prioritymetatype",
    "priorityattributes",
    "priorityspecial",
    "priorityskills",
    "priorityresources",
    "prioritytalent",
    "created",
)


#: The things Chummer holds one of and loads field by field, rather than a
#: list it rebuilds. Their fields count as the character's own.
_SINGLE_OBJECTS = ("./tradition", "./mentorspirits/mentorspirit")


def _leaves(root: ET.Element) -> dict[str, str]:
    """The character's own fields: the leaf elements directly under
    `<character>`, plus each attribute's own leaves.

    Deliberately not the whole tree. Everything else a save holds is a *list*
    of things — gear, qualities, vehicles — which this app rebuilds from its
    own catalogue rather than copying across, so comparing those element by
    element would bury the fields that matter under items that are supposed
    to differ. What is left is the header: who the character is, what they
    were built with, and what the build was allowed to spend.

    The exception is `_SINGLE_OBJECTS`: Chummer keeps exactly one of each and
    loads it field by field, so they are header too, just nested. Leaving them
    out cost a real bug — the export wrote `<tradition>` with two of its
    sixteen fields, which made Chummer drop the tradition whole, and this
    comparison called all 34 saves faithful because it never looked inside.
    """
    out: dict[str, str] = {}
    for child in root:
        # Chummer's `TryGetStringFieldQuickly` reads the *first* match, and
        # some 5.202 saves write a field twice — ten of the test saves carry a
        # second, empty `<priorityskills>` after the real one. Keeping the last
        # one read those as blank and reported the export as having invented a
        # value.
        if len(child) == 0 and child.tag not in out:
            out[child.tag] = (child.text or "").strip()
    for path in _SINGLE_OBJECTS:
        for obj in root.findall(path):
            prefix = obj.tag
            for leaf in obj:
                if len(leaf) == 0 and f"{prefix}/{leaf.tag}" not in out:
                    out[f"{prefix}/{leaf.tag}"] = (leaf.text or "").strip()
    for attr in root.findall("./attributes/attribute"):
        name = (attr.findtext("name") or "").strip()
        if not name:
            continue
        for leaf in attr:
            if leaf.tag != "name" and len(leaf) == 0:
                out[f"{name}/{leaf.tag}"] = (leaf.text or "").strip()
    return out


#: Fields Chummer states and this export deliberately does not, with why.
#: Anything else the export drops is a gap: `--fidelity` fails on it, so the
#: next field Chummer starts writing arrives as a test failure rather than as
#: a bug report from someone whose character opened wrong.
#:
#: "Output only" means `Character.Load` never reads it back — Chummer writes
#: it for other readers and recomputes it on load. Writing figures nobody
#: reads is how the two sides drift apart quietly, so they stay out. The rest
#: are 5.202-era spellings of something the export writes the current way;
#: `Load` reads them only as a fallback, and only when the field it prefers is
#: absent. See docs/plans/chum5-export-for-chummer-plan.md.
_ACCEPTED_DROPS: dict[str, str] = {
    "sumtoten": "output only",
    "buildkarma": "output only",
    "gameplayoptionqualitylimit": "output only",
    "contactmultiplier": "output only",
    "nuyenmaxbp": "output only",
    "totaless": "output only",
    "traditiondrain": "output only — the tradition states its own drain",
    "streamdrain": "output only — the stream states its own fading",
    "contactpointsused": "output only",
    "walkalt": "output only",
    "runalt": "output only",
    "sprintalt": "output only",
    "ESS/metatypemax": "output only — Essence's own maximum is the metatype's",
    "ESS/metatypeaugmax": "output only",
    "essenceatspecialstart": "Chummer's own unset value (decimal.MinValue) on a mundane character",
    "movement": "legacy — walk / run / sprint say it now",
    "priorityskill1": "legacy — <priorityskills><priorityskill> says it now",
    "priorityskill2": "legacy — <priorityskills><priorityskill> says it now",
    "stream": "legacy — <tradition> with traditiontype RES says it now",
    "tradition": "legacy — the nested <tradition> says it now",
    "tradition/id": "legacy — Tradition.Load prefers <sourceid>, which is written",
}

#: The same, by suffix, for the fields each attribute repeats.
_ACCEPTED_DROP_SUFFIXES: dict[str, str] = {
    "/totalvalue": "output only — recomputed on load",
    "/metatypecategory": "output only — read off the abbreviation",
    "/value": "legacy — pre-split saves only; base / karma say it now",
}

#: An attribute only pre-split Chummer had. Initiative is worked out from
#: REA + INT now, so none of its fields have anywhere to go.
_LEGACY_ATTRIBUTES = ("INI/",)


def _accepted_drop(tag: str) -> str | None:
    """Why this export leaves `tag` out, or `None` if it is a gap."""
    if tag in _ACCEPTED_DROPS:
        return _ACCEPTED_DROPS[tag]
    for suffix, reason in _ACCEPTED_DROP_SUFFIXES.items():
        if tag.endswith(suffix):
            return reason
    if tag.startswith(_LEGACY_ATTRIBUTES):
        return "legacy attribute — Initiative is derived now"
    return None


def fidelity(path: Path) -> tuple[list[str], list[tuple[str, str, str]]]:
    """What Chummer states about a character that this app's export does not.

    `--roundtrip` reads the export back with *this app's own* importer, so it
    is blind by construction to anything Chummer needs and this app does not:
    a field neither side reads comes back unchanged because neither side
    looked. Chummer itself is the other reader, and the only statement of
    what it expects is the save it wrote — so the comparison is the original
    against the export, field by field.

    A field Chummer wrote empty (`0`, `False`) is not reported: it is there
    because Chummer writes every field, not because this character has one.
    """
    from app.characters import import_character
    from app.chummer_export import state_to_chum5
    from app.chummer_import import chum5_to_state

    theirs = _leaves(ET.fromstring(path.read_bytes()))
    exported = state_to_chum5(import_character(chum5_to_state(path.read_bytes())[0]))
    ours = _leaves(ET.fromstring(exported if isinstance(exported, bytes) else exported.encode()))
    dropped = [tag for tag, text in theirs.items() if tag not in ours and text not in _EMPTY_VALUES]
    changed = [
        (tag, theirs[tag], ours[tag])
        for tag in _SAME_VALUE_TAGS
        if tag in theirs and tag in ours and theirs[tag] != ours[tag]
    ]
    return dropped, changed
