"""Who the character is and how they were built: identity, settings and
attributes. Skills are in `skills`, the career balance in `balance`."""

from __future__ import annotations

import xml.etree.ElementTree as ET  # the Element type only — parsing goes through parse_untrusted
from typing import Any

from ..data_loader import CatalogDict
from ..data_loader._xml import _int, _text
from ..models import clean_portrait
from ..notices import Notice, notice
from ..rules import DEFAULT_RULES

_BUILD_METHODS = {
    "priority": "Priority",
    "sumtoten": "SumToTen",
    "sum-to-ten": "SumToTen",
    "karma": "Karma",
    "lifemodule": "Priority",
}


def _read_mugshot(root: ET.Element) -> str:
    """Chummer stores portraits as base64 either in ``<mugshots><mugshot>`` (with
    ``<mainmugshotindex>`` picking one) or a legacy flat ``<mugshot>``. Return a
    ``data:`` URI ready for an ``<img>`` ``src``, or ``""`` — also for a
    mugshot that is not a PNG / JPEG / GIF / WebP (see `clean_portrait`)."""
    shots = [_text(m) for m in root.findall("./mugshots/mugshot") if _text(m)]
    raw = ""
    if shots:
        try:
            i = int(_text(root.find("mainmugshotindex")) or "0")
        except ValueError:
            i = 0
        raw = shots[i] if 0 <= i < len(shots) else shots[0]
    raw = (raw or _text(root.find("mugshot"))).strip()
    if not raw:
        return ""
    if raw.startswith("data:"):
        return clean_portrait(raw)
    mime = "image/jpeg" if raw.startswith("/9j/") else "image/png"
    return clean_portrait(f"data:{mime};base64,{raw}")


def _import_settings(root: ET.Element, cat: CatalogDict) -> dict[str, Any]:
    """`<settings>` -> `SettingsState`.

    Chummer writes the name (older builds, the file name) of the settings the
    character was built under; the enabled books live in that file, which is
    not part of the save. So the books are recovered by looking the name up
    among the shipped presets, and a settings file this app has never seen
    comes back as a name with no book restriction — the whole catalog, which
    is what an unset `books` means everywhere else.

    `<maxavail>` is the exception that *is* in the save: it is the character's
    own creation availability limit, which the gameplay option sets (Standard
    12, Prime Runner 15) and a table can house-rule to anything. Ignoring it
    and using the preset's 12 called four of Chummer's own test characters
    illegal over equipment they were entitled to.

    The name is read from `<gameplayoption>` first. `<settings>` holds the
    *file* the rules came from, which is `default.xml` even for a character
    built as a Prime Runner, so matching on it finds the wrong preset — or, as
    here, no preset at all, and the character is then judged by Standard's
    25-karma quality cap instead of Prime Runner's 35.
    """
    el = root.find("settings")
    # Some builds write `<settings>` as a container of house-rule elements
    # rather than a name; there is nothing to take from that.
    name = _text(root.find("gameplayoption")).strip()
    if not name:
        name = _text(el) if el is not None and len(el) == 0 else ""
    name = name.removesuffix(".xml").strip()
    extra: dict[str, Any] = {}
    max_avail = _text(root.find("maxavail"))
    if max_avail:
        try:
            extra["chargen_avail_max"] = int(max_avail)
        except ValueError:
            pass
    if not name:
        return extra
    for preset in cat.get("settings_presets") or []:
        if preset.get("name") != name:
            continue
        found: dict[str, Any] = {"name": name, "books": list(preset.get("books") or [])}
        # Only when the preset moves it. A settings state says what it changes,
        # not everything (`rules_for`), so writing the printed 25 back would
        # turn "unset" into "set to the default" on every import.
        limit = preset.get("quality_karma_limit")
        if limit is not None and int(limit) != DEFAULT_RULES.quality_karma_cap_positive:
            found["quality_karma_limit"] = int(limit)
        table = preset.get("priority_table")
        if table and table != "Standard":
            found["priority_table"] = str(table)
        nuyen_max = preset.get("nuyen_max_bp")
        if nuyen_max is not None and int(nuyen_max) != DEFAULT_RULES.priority_karma_nuyen_base:
            found["priority_karma_nuyen_base"] = int(nuyen_max)
        return {**found, **extra}
    return {"name": name, "books": [], **extra}


def _import_identity(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read name, metatype, build method, the bio fields and the portrait."""
    st["name"] = _text(root.find("alias")) or _text(root.find("name")) or "Imported Runner"
    st["metatype"] = _text(root.find("metatype")) or "Human"
    mv = _text(root.find("metavariant"))
    st["metavariant"] = mv if mv and mv.lower() not in ("none", "") else None
    st["talent"] = _text(root.find("./priorities/prioritytalent")) or _text(root.find("prioritytalent")) or "Mundane"
    st["build_method"] = _BUILD_METHODS.get(_text(root.find("buildmethod")).lower(), "Priority")
    st["street_cred"] = max(0, _int(root.find("streetcred"), 0))
    st["burnt_street_cred"] = max(0, _int(root.find("burntstreetcred"), 0))
    st["notoriety_bonus"] = _int(root.find("notoriety"), 0)
    st["public_awareness"] = max(0, _int(root.find("publicawareness"), 0))
    # Nuyen bought with karma at chargen; `<nuyenbp>` is build points in old money.
    st["karma_nuyen"] = max(0, _int(root.find("nuyenbp"), 0))
    st["settings"] = _import_settings(root, cat)
    created = _text(root.find("created")).lower() == "true"
    st["career"] = created
    st["notes"] = _text(root.find("notes"))
    for field, tag in (
        ("age", "age"),
        ("sex", "sex"),
        ("height", "height"),
        ("weight", "weight"),
        ("eyes", "eyes"),
        ("hair", "hair"),
        ("skin", "skin"),
        ("appearance", "description"),
        ("background", "background"),
        ("concept", "concept"),
    ):
        val = _text(root.find(tag))
        if val:
            st[field] = val
    mug = _read_mugshot(root)
    if mug:
        st["portrait"] = mug
    elif any(_text(m).strip() for m in [*root.findall("./mugshots/mugshot"), root.find("mugshot")]):
        warn.append(notice("engine.import.portraitDropped"))

    def prio(tag: str) -> str:
        # Chummer writes `E,0` (letter, sum-to-ten value) and reads only the
        # letter back (`priority[0]`); a bare letter is what older exports
        # from this app wrote, nested in `<priorities>`.
        v = (_text(root.find(tag)) or _text(root.find(f"./priorities/{tag}")))[:1].upper()
        return v if v and v in "ABCDE" else "C"

    st["priorities"] = {
        "Heritage": prio("prioritymetatype"),
        "Attributes": prio("priorityattributes"),
        "Talent": prio("priorityspecial"),
        "Skills": prio("priorityskills"),
        "Resources": prio("priorityresources"),
    }
    # A career save's `<karma>` / `<nuyen>` are the balance, not what was
    # earned: `_import_balance` works that out once everything is read.


def _import_attributes(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read the eight attributes plus EDG/MAG/RES, as base + karma."""
    attrs: dict[str, int] = {}
    karma_levels: dict[str, int] = {}
    for a in root.findall("./attributes/attribute"):
        name = _text(a.find("name")).upper()
        if name in ("ESS", "ESSENCE") or not name:
            continue
        # Chummer <base> is points spent above the metatype minimum; <karma>
        # the levels on top of it bought with karma.
        lo = _int(a.find("metatypemin"), 1)
        karma = max(0, _int(a.find("karma")))
        attrs[name] = max(lo + _int(a.find("base")) + karma, lo)
        # Before creation is finished that split is a choice the sheet keeps.
        # After it, <karma> also holds every career raise, which the career
        # baseline taken from these ratings already accounts for.
        if karma and not st.get("career"):
            karma_levels[name] = karma
    st["attributes"] = attrs or {"BOD": 1, "AGI": 1, "REA": 1, "STR": 1, "CHA": 1, "INT": 1, "LOG": 1, "WIL": 1}
    st["attribute_karma"] = karma_levels
