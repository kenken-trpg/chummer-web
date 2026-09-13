"""Who the character is and how they were built: identity, settings, the
career ledger, attributes and skills."""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET  # the Element type only — parsing goes through parse_untrusted
from typing import Any

from ..data_loader import CatalogDict
from ..data_loader._xml import _int, _text
from ..models import clean_portrait
from ..notices import Notice, notice
from ._common import _is_uuid

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
    """
    el = root.find("settings")
    # Some builds write `<settings>` as a container of house-rule elements
    # rather than a name; there is nothing to take from that.
    name = _text(el) if el is not None and len(el) == 0 else ""
    name = name.removesuffix(".xml").strip()
    if not name:
        return {}
    for preset in cat.get("settings_presets") or []:
        if preset.get("name") == name:
            return {"name": name, "books": list(preset.get("books") or [])}
    return {"name": name, "books": []}


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
    if created:
        st["karma_earned"] = _int(root.find("karma"))
        st["nuyen_earned"] = _int(root.find("nuyen"))
        log = _reward_log_from_expenses(root)
        if log is not None:
            karma = sum(row["karma"] for row in log)
            nuyen = sum(row["nuyen"] for row in log)
            if (karma, nuyen) == (st["karma_earned"], st["nuyen_earned"]):
                st["reward_log"] = log
            else:
                warn.append(notice("engine.import.expensesSkipped", karma=karma, nuyen=nuyen))


def _reward_log_from_expenses(root: ET.Element) -> list[dict[str, Any]] | None:
    """`<expenses>` back into reward rows, or `None` when there are none.

    Only what was earned counts — a positive amount that is not a refund.
    Rows this app wrote carry `<rewardid>`, which joins a karma row to the
    nuyen row of the same reward; any other row is a reward of its own.
    """
    rows = root.findall("./expenses/expense")
    if not rows:
        return None
    log: dict[str, dict[str, Any]] = {}
    for el in rows:
        amount = _int(el.find("amount"))
        kind = _text(el.find("type")).lower()
        if amount <= 0 or kind not in ("karma", "nuyen") or _text(el.find("refund")).lower() == "true":
            continue
        key = _text(el.find("rewardid")) or _text(el.find("guid")) or str(uuid.uuid4())
        row = log.setdefault(
            key,
            {
                "id": key if _is_uuid(key) else str(uuid.uuid4()),
                "label": _text(el.find("reason")),
                "karma": 0,
                "nuyen": 0,
            },
        )
        row[kind] += amount
    return list(log.values())


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


def _import_skills(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read active skills, groups, specialisations and knowledge."""
    skills: dict[str, int] = {}
    specs: dict[str, str] = {}
    exotic: list[dict[str, Any]] = []
    exotic_names = {row["name"] for row in (cat["skills"].get("skills") or []) if row.get("exotic")}
    for s in root.findall("./skills/skills/skill"):
        name = _text(s.find("name"))
        if not name:
            continue
        rating = _int(s.find("base")) + _int(s.find("karma"))
        # An exotic skill is one row per weapon, told apart by `<specific>` —
        # two of them share a name, so they cannot go in the `skills` map.
        if name in exotic_names:
            exotic.append(
                {
                    "id": str(uuid.uuid4()),
                    "skill_name": name,
                    "extra": _text(s.find("specific")),
                    "rating": max(1, rating),
                }
            )
            continue
        if rating > 0:
            skills[name] = rating
        sp = _text(s.find("./specializations/spec/name")) or _text(s.find("./specializations/skillspecialization/name"))
        if sp:
            specs[name] = sp
    st["skills"] = skills
    st["skill_specializations"] = specs
    st["exotic_skills"] = exotic

    groups: dict[str, int] = {}
    for g in root.findall("./skills/groups/group"):
        r = _int(g.find("base")) + _int(g.find("karma"))
        if r > 0:
            groups[_text(g.find("name"))] = r
    st["skill_groups"] = {k: v for k, v in groups.items() if k}

    know: dict[str, int] = {}
    know_cat: dict[str, str] = {}
    natives: list[str] = []
    for s in root.findall("./skills/knoskills/skill"):
        name = _text(s.find("name"))
        if not name:
            continue
        if _text(s.find("isnativelanguage")).lower() == "true":
            natives.append(name)
            continue
        r = _int(s.find("base")) + _int(s.find("karma"))
        if r > 0:
            know[name] = r
        typ = _text(s.find("skillcategory")) or _text(s.find("type"))
        if typ:
            know_cat[name] = typ
    st["knowledge_skills"] = know
    st["knowledge_categories"] = know_cat
    st["native_languages"] = natives
