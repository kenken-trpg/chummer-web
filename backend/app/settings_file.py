"""Read a Chummer settings XML into a `SettingsState`.

Chummer's settings files carry ~160 knobs and this app implements about 25 of
them. Parsing therefore has two jobs: pull out what the engine can use, and
say plainly what it could not.

The "could not" list is filtered against Chummer's own `Standard` preset, not
against the whole tag set. A file that leaves `<armordegredation>` at its
default has not asked for anything, and reporting all 140 untouched knobs would
bury the two or three the GM actually changed.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from functools import lru_cache
from typing import Any

from .data_loader._xml import DATA_DIR, _text
from .models import SettingsState
from .rules import DEFAULT_PRIORITY_TABLE

#: Cap on an uploaded settings file. A real one is ~10 KB; the largest thing
#: Chummer ships is its whole preset library at ~320 KB.
MAX_SETTINGS_BYTES = 1024 * 1024

#: `<tag>` -> `SettingsState` field, for the knobs read straight as integers.
_INT_FIELDS: dict[str, str] = {
    "sumtoten": "sum_to_ten",
    "buildpoints": "chargen_karma",
    "qualitykarmalimit": "quality_karma_limit",
    "maxskillratingcreate": "chargen_skill_max",
    "maxknowledgeskillratingcreate": "chargen_knowledge_skill_max",
    "maxskillrating": "career_skill_max",
    "maxknowledgeskillrating": "career_skill_group_max",
    "availability": "chargen_avail_max",
    "nuyenmaxbp": "priority_karma_nuyen_base",
    "nuyenperbpwftm": "karma_to_nuyen",
    "minastralinitiativedice": "min_astral_initiative_dice",
    "maxastralinitiativedice": "max_astral_initiative_dice",
}

#: `<karmacost>` child -> `SettingsState` field.
_KARMA_FIELDS: dict[str, str] = {
    "karmaattribute": "karma_attribute",
    "karmaimproveactiveskill": "karma_active_skill",
    "karmaimproveskillgroup": "karma_skill_group",
    "karmaimproveknowledgeskill": "karma_knowledge",
    "karmaspecialization": "karma_specialization",
    "karmaspell": "karma_spell",
    "karmanewcomplexform": "karma_complex_form",
    "karmaenhancement": "karma_enhancement",
    "karmamysadpp": "karma_mystic_pp",
    "karmatechnique": "karma_martial_technique",
    "karmainitiationflat": "karma_initiation_flat",
    "karmainitiation": "karma_initiation_per_grade",
}

#: Tags read for something other than a `Rules` number — the books, the build
#: method, the name — or deliberately equivalent to one that is. Listed so
#: they are not reported as ignored.
_HANDLED_ELSEWHERE = {
    "id",
    "name",
    "gameplayoptionname",
    "books",
    "buildmethod",
    "customdatadirectorynames",
    "bannedwaregrades",
    "prioritytable",
    # `<priorityarray>` is the letters a Priority build may spend (`ABCDE`).
    # This app offers each letter once, which is that array — a file that
    # writes another one is caught by the baseline diff.
    "priorityarray",
    # `<nuyenperbpwftp>` is the career-mode twin of `<nuyenperbpwftm>`; this
    # app has one rate, and a file that sets them differently is caught by the
    # mismatch check in `_karma_to_nuyen`.
    "nuyenperbpwftp",
    # Read by `_karma_to_nuyen` when it is the plain multiplier shape.
    "chargenkarmatonuyenexpression",
    # Read by `_contact_points` when it is the plain multiplier shape.
    "contactpointsexpression",
    # Read into `_ATTR_FIELDS` when they are a single attribute.
    "boundspiritexpression",
    "registeredspriteexpression",
}

#: `<tag>` -> `SettingsState` field, for the `True` / `False` knobs.
_BOOL_FIELDS: dict[str, str] = {
    "exceednegativequalities": "exceed_negative_qualities",
    "exceednegativequalitiesnobonus": "exceed_negative_qualities_no_bonus",
}

#: `{Karma} * 3000 + {PriorityNuyen}` — the only shape of
#: `<chargenkarmatonuyenexpression>` this app can honour, because its own
#: conversion *is* that formula. Anything else is a real expression and gets
#: reported instead of being approximated.
_KARMA_NUYEN_EXPR = re.compile(r"^\{Karma\}\s*\*\s*(\d+)\s*\+\s*\{PriorityNuyen\}$")

#: `{CHAUnaug} * 3` — `<contactpointsexpression>` in the one shape the engine
#: prices contacts with: unaugmented Charisma times a multiplier. Prime Runner
#: writes `* 6`; anything that is not a plain multiplier gets reported.
_CONTACT_POINTS_EXPR = re.compile(r"^\{CHAUnaug\}\s*\*\s*(\d+)$")

#: `{CHA}` — `<boundspiritexpression>` / `<registeredspriteexpression>` as a
#: single attribute, which is every shape Chummer ships (Standard `{CHA}`,
#: the German presets `{LOG}` for sprites).
_ATTR_EXPR = re.compile(r"^\{(BOD|AGI|REA|STR|CHA|INT|LOG|WIL|EDG|MAG|RES)\}$")

#: `<tag>` -> `SettingsState` field, for the single-attribute limits.
_ATTR_FIELDS: dict[str, str] = {
    "boundspiritexpression": "bound_spirit_attr",
    "registeredspriteexpression": "registered_sprite_attr",
}


@lru_cache(maxsize=1)
def _baseline() -> dict[str, str]:
    """Chummer's `Standard` preset, flattened to `{tag: text}`.

    The yardstick for "did this file change anything". Missing vendor data
    yields an empty baseline, which makes every set tag look changed — noisy,
    but it never hides one.
    """
    path = DATA_DIR / "settings.xml"
    if not path.exists():
        return {}
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return {}
    for setting in root.findall("./settings/setting"):
        if _text(setting.find("name")) == "Standard":
            return _flatten(setting)
    return {}


def _flatten(root: ET.Element) -> dict[str, str]:
    """`{tag: text}` for leaf elements, one level into `<karmacost>`.

    Containers whose meaning is the list of children (`<books>`, the ware
    grades) are skipped: they are read directly, and comparing them as text
    would be meaningless.
    """
    out: dict[str, str] = {}
    for child in root:
        if child.tag == "karmacost":
            for cost in child:
                out[cost.tag] = (cost.text or "").strip()
        elif len(child) == 0:
            out[child.tag] = (child.text or "").strip()
    return out


def _int(value: str) -> int | None:
    try:
        return int(float(value))
    except ValueError:
        return None


def _karma_to_nuyen(flat: dict[str, str]) -> tuple[int | None, bool]:
    """The karma->nuyen rate, and whether the file's expression was readable.

    Chummer carries the rate twice: `<nuyenperbpwftm>` as a number and
    `<chargenkarmatonuyenexpression>` as a formula. The formula wins in
    Chummer, so it wins here — but only when it is the plain multiplier this
    app's own conversion matches.
    """
    expression = flat.get("chargenkarmatonuyenexpression", "")
    if expression:
        match = _KARMA_NUYEN_EXPR.match(expression)
        if match is None:
            return _int(flat.get("nuyenperbpwftm", "")), False
        return int(match.group(1)), True
    return _int(flat.get("nuyenperbpwftm", "")), True


def _customdata_names(root: ET.Element) -> list[str]:
    """The enabled `<customdatadirectoryname>` entries, in file order.

    Order is the file's, not sorted: when two directories edit the same entry
    the later one wins, which is how Chummer's `<order>` is meant to read.
    A disabled entry is dropped — the settings file already said no.
    """
    names = []
    for entry in root.findall("./customdatadirectorynames/customdatadirectoryname"):
        if _text(entry.find("enabled"), "True").strip().lower() == "false":
            continue
        name = _text(entry.find("directoryname"))
        if name:
            names.append(name)
    return names


def parse_settings_xml(raw: str | bytes) -> SettingsState:
    """One Chummer `settings/*.xml` -> `SettingsState`.

    Raises `ValueError` on anything that is not a settings document, so the
    endpoint can answer 400 rather than returning an all-defaults object that
    looks like a successful import.
    """
    if isinstance(raw, bytes):
        if len(raw) > MAX_SETTINGS_BYTES:
            raise ValueError("settings file too large")
        raw = raw.decode("utf-8-sig", errors="replace")
    elif len(raw.encode("utf-8")) > MAX_SETTINGS_BYTES:
        raise ValueError("settings file too large")
    try:
        root = ET.fromstring(raw.lstrip("﻿"))
    except ET.ParseError as exc:
        raise ValueError(f"not valid XML: {exc}") from exc
    # A file saved from Chummer's settings folder is a bare `<settings>`; the
    # preset library nests them under `<chummer><settings><setting>`.
    if root.tag != "settings":
        found = root.find("./settings/setting")
        if found is None:
            raise ValueError("no <settings> element")
        root = found

    flat = _flatten(root)
    fields: dict[str, Any] = {}
    for tag, field in _INT_FIELDS.items():
        value = _int(flat.get(tag, ""))
        if value is not None:
            fields[field] = value
    for tag, field in _KARMA_FIELDS.items():
        value = _int(flat.get(tag, ""))
        if value is not None:
            fields[field] = value
    for tag, field in _BOOL_FIELDS.items():
        text = flat.get(tag, "").lower()
        if text in ("true", "false"):
            fields[field] = text == "true"

    rate, expression_understood = _karma_to_nuyen(flat)
    if rate is not None:
        fields["karma_to_nuyen"] = rate

    contact_mult, contact_understood = _contact_points(flat)
    if contact_mult is not None:
        fields["contact_free_mult"] = contact_mult

    baseline = _baseline()
    read = set(_INT_FIELDS) | set(_KARMA_FIELDS) | set(_BOOL_FIELDS) | _HANDLED_ELSEWHERE
    unsupported = sorted(tag for tag, value in flat.items() if tag not in read and baseline.get(tag, value) != value)
    if not expression_understood:
        unsupported.append("chargenkarmatonuyenexpression")
    if not contact_understood:
        unsupported.append("contactpointsexpression")
    for tag, field in _ATTR_FIELDS.items():
        expression = flat.get(tag, "")
        if not expression:
            continue
        match = _ATTR_EXPR.match(expression)
        if match is None:
            unsupported.append(tag)
        else:
            fields[field] = match.group(1)

    return SettingsState(
        name=_text(root.find("name")),
        priority_table=_text(root.find("prioritytable"), DEFAULT_PRIORITY_TABLE),
        books=[code for code in (_text(b) for b in root.findall("./books/book")) if code],
        banned_ware_grades=[grade for grade in (_text(g) for g in root.findall("./bannedwaregrades/grade")) if grade],
        customdata=_customdata_names(root),
        unsupported=unsupported,
        **fields,
    )


def _contact_points(flat: dict[str, str]) -> tuple[int | None, bool]:
    """The free-contact-point multiplier, and whether the expression was readable."""
    expression = flat.get("contactpointsexpression", "")
    if not expression:
        return None, True
    match = _CONTACT_POINTS_EXPR.match(expression)
    if match is None:
        return None, False
    return int(match.group(1)), True


def build_method_of(raw: str | bytes) -> str | None:
    """The file's `<buildmethod>`, as `CharacterState.build_method` spells it.

    Separate from `parse_settings_xml` because the build method lives on the
    character, not in its settings — the caller patches both.
    """
    from .chummer_import import _BUILD_METHODS

    if isinstance(raw, bytes):
        raw = raw.decode("utf-8-sig", errors="replace")
    try:
        root = ET.fromstring(raw.lstrip("﻿"))
    except ET.ParseError:
        return None
    if root.tag != "settings":
        found = root.find("./settings/setting")
        if found is None:
            return None
        root = found
    return _BUILD_METHODS.get(_text(root.find("buildmethod")).lower())
