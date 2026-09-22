"""Import a Foundry VTT shadowrun5e (0.34.5) character actor — the JSON its
"Export Data" writes — into this app's ``CharacterState``.

The first cut: identity, attributes, skills, qualities, spells, adept powers
and complex forms. Items are matched on ``system.importFlags.sourceid``, the
Chummer GUID the system's own importers (Chummer and compendium) write on every
item they make, then on the English name they keep beside it, then on the
display name. What cannot be matched becomes a warning, as with a ``.chum5``.

Foundry keeps no priorities, so the character comes back as a Karma build
already in play (career), its karma and nuyen balance as Foundry had them.
"""

from __future__ import annotations

import copy
import html
import json
import re
import uuid
from typing import Any

from ..chummer_import._common import _by_name
from ..data_loader import CatalogDict, catalog
from ..notices import Notice, NoticeError, notice, ui

#: Foundry attribute key -> this app's
_ATTRIBUTES = {
    "body": "BOD",
    "agility": "AGI",
    "reaction": "REA",
    "strength": "STR",
    "charisma": "CHA",
    "intuition": "INT",
    "logic": "LOG",
    "willpower": "WIL",
    "edge": "EDG",
    "magic": "MAG",
    "resonance": "RES",
}

#: Foundry `knowledgeType` -> Chummer's knowledge skill category
_KNOWLEDGE_TYPES = {"academic": "Academic", "interest": "Interest", "professional": "Professional", "street": "Street"}


def _num(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _flags(item: dict[str, Any]) -> dict[str, Any]:
    return ((item.get("system") or {}).get("importFlags")) or {}


class _Matcher:
    """Foundry item -> catalog id for one bucket: GUID, English name, name."""

    def __init__(self, rows: list[dict[str, Any]]):
        self.ids = {str(r["id"]).lower(): str(r["id"]) for r in rows}
        self.by_name = _by_name(rows)

    def match(self, item: dict[str, Any], warn: list[Notice], kind: str) -> str | None:
        flags = _flags(item)
        sid = str(flags.get("sourceid") or "").strip().lower()
        if sid in self.ids:
            return self.ids[sid]
        for name in (flags.get("name"), item.get("name"), _base_name(str(item.get("name") or ""))):
            got = self.by_name.get(str(name or "").strip().lower())
            if got:
                return got
        warn.append(notice("engine.import.skippedUnknown", kind=ui(kind), name=str(item.get("name") or "")))
        return None


def _base_name(name: str) -> str:
    """ "Improved Ability (Pistols)" -> "Improved Ability"."""
    return re.sub(r"\s*\([^()]*\)\s*$", "", name)


def _extra(item: dict[str, Any]) -> str | None:
    """What the name carries in parentheses past the English name — the
    Chummer importer names an item by its `fullname`."""
    name = str(item.get("name") or "")
    got = re.search(r"\(([^()]*)\)\s*$", name)
    if not got or _base_name(name) == name:
        return None
    english = str(_flags(item).get("name") or "")
    return None if english and english == name else got.group(1).strip() or None


def _plain(text: str) -> str:
    """HTML description -> plain text, a paragraph per line."""
    text = re.sub(r"(?i)<br\s*/?>|</p>", "\n", text)
    return html.unescape(re.sub(r"<[^>]+>", "", text)).strip()


def _talent(system: dict[str, Any], items: list[dict[str, Any]]) -> str:
    """Foundry keeps only mundane / magic / resonance: the kind of magic user
    is read off what they have."""
    special = str(system.get("special") or "")
    if special == "resonance":
        return "Technomancer"
    if special != "magic":
        return "Mundane"
    types = {str(i.get("type") or "") for i in items}
    casts = bool(types & {"spell", "ritual"})
    if "adept_power" in types:
        return "Mystic Adept" if casts else "Adept"
    return "Magician"


def _import_skills(items: list[dict[str, Any]], cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    active = {str(r["name"]).lower(): str(r["name"]) for r in cat["skills"].get("skills") or []}
    groups = {str(g).lower(): str(g) for g in cat["skills"].get("group_names") or []}
    skills: dict[str, int] = {}
    know: dict[str, int] = {}
    know_cat: dict[str, str] = {}
    natives: list[str] = []
    specs: dict[str, str] = {}
    skill_groups: dict[str, int] = {}
    for item in items:
        if item.get("type") != "skill":
            continue
        system = item.get("system") or {}
        name = str(item.get("name") or "").strip()
        if system.get("type") == "group":
            rating = _num((system.get("group") or {}).get("rating"))
            if rating > 0:
                if name.lower() in groups:
                    skill_groups[groups[name.lower()]] = rating
                else:
                    warn.append(notice("engine.import.skippedUnknown", kind=ui("engine.kind.skill"), name=name))
            continue
        skill = system.get("skill") or {}
        rating = _num(skill.get("rating"))
        category = str(skill.get("category") or "active")
        spec = next((str(s.get("name") or "") for s in skill.get("specializations") or [] if s.get("name")), "")
        if category == "active":
            if rating <= 0:
                continue
            if name.lower() not in active:
                warn.append(notice("engine.import.skippedUnknown", kind=ui("engine.kind.skill"), name=name))
                continue
            name = active[name.lower()]
            skills[name] = rating
        elif category == "language" and (skill.get("language") or {}).get("isNative"):
            natives.append(name)
            continue
        else:
            if rating <= 0:
                continue
            know[name] = rating
            know_cat[name] = (
                "Language"
                if category == "language"
                else _KNOWLEDGE_TYPES.get(str(skill.get("knowledgeType") or ""), "Academic")
            )
        if spec:
            specs[name] = spec
    st.update(
        skills=skills,
        skill_groups=skill_groups,
        skill_specializations=specs,
        knowledge_skills=know,
        knowledge_categories=know_cat,
        native_languages=natives,
    )


def _import_items(items: list[dict[str, Any]], cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    def of(*types: str) -> list[dict[str, Any]]:
        return [i for i in items if i.get("type") in types]

    qualities = _Matcher(cat["qualities"])
    st["quality_ids"] = [qid for i in of("quality") if (qid := qualities.match(i, warn, "engine.kind.quality"))]
    spells = _Matcher(cat["spells"])
    st["spells"] = [
        {"id": str(uuid.uuid4()), "spell_id": sid}
        for i in of("spell", "ritual")
        if (sid := spells.match(i, warn, "engine.kind.spell"))
    ]
    powers = _Matcher(cat["powers"])
    st["adept_powers"] = [
        {
            "id": str(uuid.uuid4()),
            "power_id": pid,
            "rating": max(1, _num((i.get("system") or {}).get("level"), 1)),
            "extra": _extra(i),
        }
        for i in of("adept_power")
        if (pid := powers.match(i, warn, "engine.kind.adeptPower"))
    ]
    forms = _Matcher(cat["complex_forms"])
    st["complex_forms"] = [
        {"id": str(uuid.uuid4()), "form_id": fid, "level": None, "extra": _extra(i)}
        for i in of("complex_form")
        if (fid := forms.match(i, warn, "engine.kind.complexForm"))
    ]


def _import_balance(system: dict[str, Any], st: dict[str, Any]) -> None:
    """Karma and nuyen left as Foundry had them, the rest kept as an adjustment
    (as for a Chummer career save without its expense log)."""
    from ..engine import compute
    from ..models import CharacterState

    bare = copy.deepcopy({k: v for k, v in st.items() if not k.startswith("_")})
    derived = compute(CharacterState.model_validate(bare)).derived
    st["karma_adjust"] = _num((system.get("karma") or {}).get("value")) - _num(
        (derived.get("karma") or {}).get("remaining")
    )
    st["nuyen_adjust"] = _num(system.get("nuyen")) - _num(derived.get("nuyen"))


def fvtt_to_state(payload: dict[str, Any]) -> tuple[dict[str, Any], list[Notice]]:
    """A Foundry character actor in, a `CharacterState` dict plus warnings out."""
    if not is_fvtt_actor(payload):
        raise NoticeError(notice("api.notAnFvttActor"))
    cat = catalog()
    warn: list[Notice] = []
    system = payload.get("system") or {}
    items = [i for i in payload.get("items") or [] if isinstance(i, dict)]
    metatypes = {str(m["name"]).lower(): str(m["name"]) for m in cat["metatypes"]}
    metatype = metatypes.get(str(system.get("metatype") or "").lower())
    if not metatype:
        warn.append(
            notice("engine.import.skippedUnknown", kind=ui("engine.kind.other"), name=str(system.get("metatype")))
        )
    attrs = system.get("attributes") or {}
    st: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "name": str(payload.get("name") or "Imported Runner"),
        "build_method": "Karma",
        "priorities": {},
        "metatype": metatype or "Human",
        "talent": _talent(system, items),
        "career": True,
        "attributes": {
            key: max(1, _num((attrs.get(fvtt) or {}).get("base"), 1))
            for fvtt, key in _ATTRIBUTES.items()
            if fvtt in attrs and (key not in ("MAG", "RES") or _num((attrs.get(fvtt) or {}).get("base")) > 0)
        },
        "initiate_grade": max(0, _num((system.get("magic") or {}).get("initiation"))),
        "submersion_grade": max(0, _num((system.get("technomancer") or {}).get("submersion"))),
        "background": _plain(str((system.get("description") or {}).get("value") or "")),
    }
    _import_skills(items, cat, st, warn)
    _import_items(items, cat, st, warn)
    _import_balance(system, st)

    seen: set[str] = set()
    unique: list[Notice] = []
    for item in warn:
        marker = json.dumps(item, sort_keys=True, ensure_ascii=False)
        if marker not in seen:
            seen.add(marker)
            unique.append(item)
    return st, unique


def is_fvtt_actor(payload: Any) -> bool:
    """A Foundry character actor export: a `system` object and an `items` list."""
    return (
        isinstance(payload, dict)
        and payload.get("type") == "character"
        and isinstance(payload.get("system"), dict)
        and isinstance(payload.get("items"), list)
    )
