"""Who the character is and how they were built: identity, settings, the
career ledger, attributes and skills."""

from __future__ import annotations

import copy
import uuid
import xml.etree.ElementTree as ET  # the Element type only — parsing goes through parse_untrusted
from typing import Any

from ..data_loader import CatalogDict
from ..data_loader._xml import _int, _text
from ..models import clean_portrait
from ..notices import Notice, notice, ui
from ..rules import DEFAULT_RULES
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


def _spend_log_from_expenses(root: ET.Element) -> list[dict[str, Any]]:
    """What the save's `<expenses>` spent, as rows with negative amounts.

    History only: what it bought is priced from the character itself, so
    counting these as well would charge for everything twice. They say where
    the balance went, which the adjustment alone cannot.
    """
    out: list[dict[str, Any]] = []
    for el in root.findall("./expenses/expense"):
        amount = _int(el.find("amount"))
        kind = _text(el.find("type")).lower()
        if amount >= 0 or kind not in ("karma", "nuyen"):
            continue
        out.append(
            {
                "id": str(uuid.uuid4()),
                "label": _text(el.find("reason")),
                "karma": amount if kind == "karma" else 0,
                "nuyen": amount if kind == "nuyen" else 0,
            }
        )
    return out


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


def _skill_nodes(root: ET.Element, section: str) -> list[ET.Element]:
    """One skills section in both layouts: `<newskills>` is what Chummer writes
    (`skills` / `knoskills` / `groups`); `<skills>` is this app's older export."""
    return root.findall(f"./newskills/{section}") + root.findall(f"./skills/{section}")


def _talent_free_ratings(root: ET.Element) -> tuple[dict[str, int], dict[str, int]]:
    """The priority talent's free skills and groups, name -> free rating.

    Chummer keeps them as `Heritage` improvements (`SkillBase` /
    `SkillGroupBase`) rather than on the skill, whose `<base>` holds only
    what points bought.
    """
    skills: dict[str, int] = {}
    groups: dict[str, int] = {}
    for imp in root.findall("./improvements/improvement"):
        if _text(imp.find("improvementsource")) != "Heritage":
            continue
        kind = _text(imp.find("improvementttype"))
        target = skills if kind == "SkillBase" else groups if kind == "SkillGroupBase" else None
        name = _text(imp.find("improvedname"))
        if target is not None and name:
            target[name] = target.get(name, 0) + _int(imp.find("val"))
    return skills, groups


def _import_skills(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read active skills, groups, specialisations and knowledge.

    Chummer names an active skill only by its skills.xml id (`<suid>`); a
    knowledge skill and a group carry their `<name>`.
    """
    rows = cat["skills"].get("skills") or []
    names_by_id = {str(row["id"]): str(row["name"]) for row in rows}
    exotic_names = {row["name"] for row in rows if row.get("exotic")}
    skills: dict[str, int] = {}
    specs: dict[str, str] = {}
    exotic: list[dict[str, Any]] = []
    # Before creation is finished, <karma> is the top levels bought with karma
    # rather than skill points (as for attributes); after it, every career
    # raise is in there too, which the career baseline already accounts for.
    split = not st.get("career")
    skill_karma: dict[str, int] = {}
    knowledge_karma: dict[str, int] = {}
    free_skills, free_groups = _talent_free_ratings(root)
    st["talent_skills"] = list(free_skills or free_groups)
    for s in _skill_nodes(root, "skills/skill"):
        name = _text(s.find("name")) or names_by_id.get(_text(s.find("suid")), "")
        # `<base>` is the points only: the talent's free levels sit under it
        rating = _int(s.find("base")) + _int(s.find("karma")) + free_skills.get(name, 0)
        if not name:
            if rating > 0:
                warn.append(
                    notice("engine.import.skippedUnknown", kind=ui("engine.kind.skill"), name=_text(s.find("suid")))
                )
            continue
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
            if split and _int(s.find("karma")) > 0:
                skill_karma[name] = _int(s.find("karma"))
        sp = (
            _text(s.find("./specs/spec/name"))
            or _text(s.find("./specializations/spec/name"))
            or _text(s.find("./specializations/skillspecialization/name"))
        )
        if sp:
            specs[name] = sp
    st["skills"] = skills
    st["skill_karma"] = skill_karma
    st["skill_specializations"] = specs
    st["exotic_skills"] = exotic

    groups: dict[str, int] = {}
    group_karma: dict[str, int] = {}
    for g in _skill_nodes(root, "groups/group"):
        name = _text(g.find("name"))
        r = _int(g.find("base")) + _int(g.find("karma")) + free_groups.get(name, 0)
        if r > 0 and name:
            groups[name] = r
            if split and _int(g.find("karma")) > 0:
                group_karma[name] = _int(g.find("karma"))
    st["skill_groups"] = groups
    st["skill_group_karma"] = group_karma

    know: dict[str, int] = {}
    know_cat: dict[str, str] = {}
    natives: list[str] = []
    for s in _skill_nodes(root, "knoskills/skill"):
        name = _text(s.find("name"))
        if not name:
            continue
        know_spec = _text(s.find("./specs/spec/name"))
        if know_spec:
            specs[name] = know_spec
        r = _int(s.find("base")) + _int(s.find("karma"))
        typ = _text(s.find("skillcategory")) or _text(s.find("type"))
        native = _text(s.find("isnativelanguage")).lower()
        # Saves from before Chummer 5.212.72 carry no flag: Chummer reads a
        # language nobody put a point into as the native one (KnowledgeSkill.Load).
        if native == "true" or (not native and typ == "Language" and r == 0):
            natives.append(name)
            continue
        if r > 0:
            know[name] = r
            if split and _int(s.find("karma")) > 0:
                knowledge_karma[name] = _int(s.find("karma"))
        if typ:
            know_cat[name] = typ
    st["knowledge_skills"] = know
    st["knowledge_karma"] = knowledge_karma
    st["knowledge_categories"] = know_cat
    st["native_languages"] = natives


def _import_balance(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """A career character's money, from the balance Chummer saved.

    Chummer keeps `<karma>` and `<nuyen>` as what is left to spend
    (`Character.Karma` / `Nuyen`) and `<expenses>` as the history. This app
    keeps what was earned — the earning rows of that history, which are also
    what Street Cred counts (`CareerKarma`) — and works the balance out. What
    that leaves apart from the saved balance (rent paid, purchases at their
    own prices) is kept as an adjustment, so the balance comes back as saved.
    """
    if not st.get("career"):
        return
    from ..engine import compute
    from ..models import CharacterState

    log = _reward_log_from_expenses(root) or []
    if log:
        st["reward_log"] = log
    spent = _spend_log_from_expenses(root)
    if spent:
        st["expense_log"] = spent
    st["karma_earned"] = sum(row["karma"] for row in log)
    st["nuyen_earned"] = sum(row["nuyen"] for row in log)
    bare = copy.deepcopy({k: v for k, v in st.items() if not k.startswith("_")})
    derived = compute(CharacterState.model_validate(bare)).derived
    try:
        nuyen_balance = round(float(_text(root.find("nuyen")) or 0))
    except ValueError:
        nuyen_balance = 0
    st["karma_adjust"] = _int(root.find("karma")) - int((derived.get("karma") or {}).get("remaining") or 0)
    st["nuyen_adjust"] = nuyen_balance - int(derived.get("nuyen") or 0)
