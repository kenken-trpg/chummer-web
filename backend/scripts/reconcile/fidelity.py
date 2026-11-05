"""The export against the save Chummer wrote, field by field.

This answers the question `roundtrip` cannot. Reading the export back with
this app's own importer is blind by construction to anything Chummer needs
and this app does not: a field neither side reads comes back unchanged
because neither side looked, and the round trip calls that a pass. Chummer is
the other reader of these files, and the only statement of what it expects is
the save it wrote — so this compares the original against the export over the
character's own header (who they are, what they were built with, what the
build was allowed to spend), plus the two things Chummer keeps exactly one of
and loads field by field: the tradition and the mentor spirit — and inside
each row of the lists (`_ROWS`). Which rows a list holds is rebuilt from this
app's catalogue and supposed to differ, so a row only one side has is passed
over; but a row both have is loaded by Chummer field by field, mostly without
looking the catalogue up again, and a field the export leaves out of it is a
gap like any other. A row field Chummer would read at its default anyway
(`_ROW_DEFAULTS`) is not one.

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
    if tag in _ACCEPTED_ROW_DROPS:
        return _ACCEPTED_ROW_DROPS[tag]
    for suffix, reason in _ACCEPTED_DROP_SUFFIXES.items():
        if tag.endswith(suffix):
            return reason
    if tag.startswith(_LEGACY_ATTRIBUTES):
        return "legacy attribute — Initiative is derived now"
    return None


#: The lists whose rows `--fidelity` looks inside, by the name a field is
#: reported under (`spell/dv`). The header comparison above never looked
#: inside a row, which is how the export wrote powers without their levels,
#: and spells without their drain, and every save still came back faithful.
#: A row is matched to the export's by its name and extra (an active skill by
#: its `<suid>`); a row only one side has is not compared — these lists are
#: rebuilt from the catalogue, and what each holds is `--roundtrip`'s question.
_ROWS: tuple[tuple[str, str], ...] = (
    ("quality", "./qualities/quality"),
    ("power", "./powers/power"),
    ("spell", "./spells/spell"),
    ("complexform", "./complexforms/complexform"),
    ("martialart", "./martialarts/martialart"),
    ("metamagic", "./metamagics/metamagic"),
    ("art", "./arts/art"),
    ("initiation", "./initiationgrades/initiationgrade"),
    ("spirit", "./spirits/spirit"),
    ("focus", "./foci/focus"),
    ("skill", "./newskills/skills/skill"),
    ("knowledgeskill", "./newskills/knoskills/skill"),
    ("contact", "./contacts/contact"),
    ("cyberware", "./cyberwares/cyberware"),
    ("armor", "./armors/armor"),
    ("armormod", "./armors/armor/armormods/armormod"),
    ("weapon", "./weapons/weapon"),
    ("accessory", "./weapons/weapon/accessories/accessory"),
    ("gear", "./gears/gear"),
    ("vehicle", "./vehicles/vehicle"),
    ("vehiclemod", "./vehicles/vehicle/mods/mod"),
    ("lifestyle", "./lifestyles/lifestyle"),
    ("lifestylequality", "./lifestyles/lifestyle/lifestylequalities/lifestylequality"),
)

#: What a row's `Load` takes a field to be when the save leaves it out — the
#: field's initial value in Chummer's class. A field the export leaves out is
#: only a gap when Chummer's save says something else: Chummer writes
#: `<equipped>True</equipped>` on every piece of gear, and the export saying
#: nothing means the same. Where this has no entry, the default is empty
#: (`_EMPTY_VALUES`).
_ROW_DEFAULTS: dict[str, str] = {
    "quality/contributetolimit": "True",
    "quality/doublecareer": "True",
    "quality/implemented": "True",
    "quality/print": "True",
    "martialart/cost": "7",
    "contact/groupenabled": "True",
    "cyberware/extraessmultiplicativemultiplier": "1",
    "cyberware/limbslotcount": "1",
    "cyberware/overclocked": "None",
    "armormod/equipped": "True",
    "weapon/allowaccessory": "True",
    "weapon/equipped": "True",
    "weapon/fullburst": "10",
    "weapon/installed": "True",
    "weapon/overclocked": "None",
    "weapon/rangemultiply": "1",
    "weapon/requireammo": "True",
    "weapon/suppressive": "20",
    "accessory/equipped": "True",
    "gear/equipped": "True",
    "gear/overclocked": "None",
    "vehiclemod/equipped": "True",
    "lifestylequality/contributetolimit": "True",
    "lifestylequality/print": "True",
}

_PLAYERS_TEXT = "the player's own text, which this app does not hold"
_NEW_ON_LOAD = "a new one is made on load; the export names a row by guid where something points at it"

#: Row fields Chummer states and this export does not, with why — as
#: `_ACCEPTED_DROPS` is for the header. A reason that starts "not written
#: yet" is a gap that is known and not fixed: it is listed, so the next one
#: still fails the run, but it is not counted against the export.
_ACCEPTED_ROW_DROPS: dict[str, str] = {
    **{
        f"{kind}/notes": _PLAYERS_TEXT
        for kind in (
            "quality",
            "power",
            "spell",
            "cyberware",
            "armor",
            "weapon",
            "accessory",
            "gear",
            "vehicle",
            "contact",
        )
    },
    **{
        f"{kind}/guid": _NEW_ON_LOAD
        for kind in (
            "quality",
            "skill",
            "knowledgeskill",
            "initiation",
            "metamagic",
            "art",
            "accessory",
            "vehicle",
            "vehiclemod",
            "lifestylequality",
        )
    },
    **{f"{kind}/id": "legacy — <sourceid> says it now" for kind in ("quality", "power", "gear", "vehicle")},
    **{
        f"contact/{tag}": _PLAYERS_TEXT
        for tag in (
            "location",
            "metatype",
            "sex",
            "age",
            "hobbiesvice",
            "personallife",
            "preferredpayment",
            "contacttype",
            "colour",
            "family",
            "group",
        )
    },
    "contact/mainmugshotindex": "the portrait shown; this app holds no portraits",
    "spirit/mainmugshotindex": "the portrait shown; this app holds no portraits",
    "spirit/crittername": _PLAYERS_TEXT,
    "armor/armorname": _PLAYERS_TEXT,
    "gear/gearname": _PLAYERS_TEXT,
    "vehicle/vehiclename": _PLAYERS_TEXT,
    "armor/location": "the player's own storage location, which this app does not hold",
    "gear/location": "the player's own storage location, which this app does not hold",
    "gear/allowrename": "only lets the player rename the piece in Chummer",
    "gear/overclocked": "the attribute an Overclocker boosts, which this app does not hold",
    "gear/conditionmonitor": "output only",
    "gear/programlimit": "falls back to the catalogue's <programs> when absent",
    "vehicle/devicerating": "falls back to the catalogue when absent",
    "weapon/alternaterange": "falls back to the catalogue when absent",
    "lifestylequality/allowed": "falls back to the catalogue when absent",
    "vehiclemod/markup": "output only",
    "weapon/firingmode": "only a weapon mounted on a vehicle reads it",
    "accessory/extramount": "None — no extra mount, which is what the empty default means",
    "cyberware/forcegrade": "only Chummer's grade picker reads it",
    "cyberware/prototypetranshuman": "this app picks the pieces the allowance covers itself, smallest first; "
    "the player's own pick is not kept",
    "power/maxlevel": "legacy — <maxlevels> says it now",
    "quality/metagenetic": "legacy — <metagenic> says it now",
    "quality/implemented": "copied from the catalogue, which no longer marks a quality unimplemented",
    "quality/contributetolimit": "a take bought after creation, which Chummer keeps out of the creation limit; "
    "this app does not tell takes apart by when they were bought",
    "accessory/ammoslots": "copied from the catalogue, which no longer gives an Extended Clip an ammo slot",
    "martialart/rating": "output only",
    "martialart/source": "only shown",
    "martialart/page": "only shown",
    "metamagic/source": "only shown",
    "metamagic/page": "only shown",
    "art/source": "only shown",
    "art/page": "only shown",
    "metamagic/improvementsource": "Metamagic, the default, unless it is an echo — which the row's own name says",
    "art/improvementsource": "Metamagic, the default",
    "gear/active": "this app marks the device its Matrix initiative runs, the highest Data Processing; "
    "a save that ran another keeps that pick only in Chummer",
}


def _row_key(el: ET.Element) -> str:
    if el.tag == "skill" and not el.findtext("name"):
        return (el.findtext("suid") or "").strip()
    return f"{(el.findtext('name') or '').strip()}|{(el.findtext('extra') or '').strip()}"


def _same(text: str, default: str) -> bool:
    try:
        return float(text) == float(default)
    except ValueError:
        return text == default


def _row_drops(theirs: ET.Element, ours: ET.Element) -> list[str]:
    """`kind/tag` once for each field a row of Chummer's states that the same
    row in the export leaves out, where Chummer would read it otherwise."""
    out: list[str] = []
    for kind, path in _ROWS:
        exported: dict[str, list[ET.Element]] = {}
        for el in ours.findall(path):
            exported.setdefault(_row_key(el), []).append(el)
        seen: dict[str, int] = {}
        for el in theirs.findall(path):
            key = _row_key(el)
            index = seen.get(key, 0)
            seen[key] = index + 1
            matches = exported.get(key) or []
            if index >= len(matches):
                continue
            mine = matches[index]
            for leaf in el:
                if len(leaf) or mine.find(leaf.tag) is not None:
                    continue
                tag = f"{kind}/{leaf.tag}"
                text = (leaf.text or "").strip()
                default = _ROW_DEFAULTS.get(tag)
                if (text in _EMPTY_VALUES) if default is None else (not text or _same(text, default)):
                    continue
                out.append(tag)
    return out


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

    their_root = ET.fromstring(path.read_bytes())
    exported = state_to_chum5(import_character(chum5_to_state(path.read_bytes())[0]))
    our_root = ET.fromstring(exported if isinstance(exported, bytes) else exported.encode())
    theirs, ours = _leaves(their_root), _leaves(our_root)
    dropped = [tag for tag, text in theirs.items() if tag not in ours and text not in _EMPTY_VALUES]
    dropped += _row_drops(their_root, our_root)
    changed = [
        (tag, theirs[tag], ours[tag])
        for tag in _SAME_VALUE_TAGS
        if tag in theirs and tag in ours and theirs[tag] != ours[tag]
    ]
    return dropped, changed
