"""Import a Foundry VTT shadowrun5e (0.34.5) character actor — the JSON its
"Export Data" writes — into this app's ``CharacterState``.

What comes over: identity, attributes, skills, qualities, spells, adept
powers, complex forms, armor (and its mods), weapons (and their accessories),
cyber- and bioware, gear (routed to its bucket: commlinks, decks, programs, ...),
contacts, lifestyles, the tradition and reputation. Items are matched on ``system.importFlags.sourceid``, the
Chummer GUID the system's own importers (Chummer and compendium) write on every
item they make, then on the English name they keep beside it, then on the
display name. What cannot be matched becomes a warning, as with a ``.chum5``.

Foundry keeps no priorities, so the character comes back as a Karma build
already in play (career), its karma and nuyen balance as Foundry had them.
"""

from __future__ import annotations

import copy
import json
import math
import uuid
from html.parser import HTMLParser
from typing import Any, cast

from ..chummer_import._common import _by_name
from ..data_loader import CatalogDict, catalog, catalog_list
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

#: Foundry cyberware grade -> this app's
_GRADES = {
    "standard": "Standard",
    "alpha": "Alphaware",
    "beta": "Betaware",
    "delta": "Deltaware",
    "gamma": "Gammaware",
    "grey": "Greyware",
    "used": "Used",
}

#: Foundry lifestyle `type` -> the catalog lifestyle it stands for
_LIFESTYLES = {
    "street": "Street",
    "squatter": "Squatter",
    "low": "Low",
    "medium": "Medium",
    "high": "High",
    "luxury": "Luxury",
}

#: gear buckets tried before plain gear, as the .chum5 import does
_GEAR_BUCKETS = ("commlinks", "cyberdecks", "rccs", "programs", "apps", "sensors", "optics")

#: Foundry item types that are gear of some kind
_GEAR_TYPES = ("equipment", "device", "program", "sin", "ammo")

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

    def find(self, item: dict[str, Any]) -> str | None:
        flags = _flags(item)
        sid = str(flags.get("sourceid") or "").strip().lower()
        if sid in self.ids:
            return self.ids[sid]
        for name in (flags.get("name"), item.get("name"), _base_name(str(item.get("name") or ""))):
            got = self.by_name.get(str(name or "").strip().lower())
            if got:
                return got
        return None

    def match(self, item: dict[str, Any], warn: list[Notice], kind: str) -> str | None:
        got = self.find(item)
        if not got:
            warn.append(notice("engine.import.skippedUnknown", kind=ui(kind), name=str(item.get("name") or "")))
        return got


def _paren(name: str) -> tuple[str, str] | None:
    """ "Improved Ability (Pistols)" -> ("Improved Ability", "Pistols").
    Slicing, not a regex: the name comes from an uploaded file (ReDoS)."""
    rest = name.rstrip()
    if not rest.endswith(")"):
        return None
    start = rest.rfind("(", 0, -1)
    if start < 0 or ")" in rest[start + 1 : -1]:
        return None
    return rest[:start].rstrip(), rest[start + 1 : -1]


def _base_name(name: str) -> str:
    """ "Improved Ability (Pistols)" -> "Improved Ability"."""
    got = _paren(name)
    return got[0] if got else name


def _extra(item: dict[str, Any]) -> str | None:
    """What the name carries in parentheses past the English name — the
    Chummer importer names an item by its `fullname`."""
    name = str(item.get("name") or "")
    got = _paren(name)
    if not got:
        return None
    english = str(_flags(item).get("name") or "")
    return None if english and english == name else got[1].strip() or None


def _tech(item: dict[str, Any]) -> dict[str, Any]:
    return (item.get("system") or {}).get("technology") or {}


def _rating(item: dict[str, Any]) -> int:
    return max(1, _num(_tech(item).get("rating"), 1))


def _embedded(item: dict[str, Any]) -> list[dict[str, Any]]:
    """What Foundry keeps inside an item: a weapon's accessories and ammo, an
    armor's mods."""
    got = ((item.get("flags") or {}).get("shadowrun5e") or {}).get("embeddedItems")
    return [i for i in got or [] if isinstance(i, dict)]


class _Text(HTMLParser):
    """The text of an HTML fragment, a line break for <br> and </p>."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag == "p":
            self.parts.append("\n")


def _plain(text: str) -> str:
    """HTML description -> plain text, a paragraph per line. A parser, not a
    regex: the text comes from an uploaded file (ReDoS)."""
    parser = _Text()
    parser.feed(text)
    parser.close()
    return "".join(parser.parts).strip()


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


def _import_combat(items: list[dict[str, Any]], cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Armor and its mods, weapons and their accessories, cyber- and bioware."""
    armor_m = _Matcher(cat["armor"])
    amod_m = _Matcher(cat["armor_mods"])
    variable_armor = {str(r["id"]) for r in cat["armor"] if r.get("cost_range")}
    armor: list[dict[str, Any]] = []
    armor_mods: list[dict[str, Any]] = []
    for i in items:
        if i.get("type") != "armor" or not (aid := armor_m.match(i, warn, "engine.kind.armor")):
            continue
        row: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "armor_id": aid,
            "rating": _rating(i),
            "equipped": bool(_tech(i).get("equipped", True)),
        }
        if aid in variable_armor:
            row["cost"] = _num(_tech(i).get("cost"))
        armor.append(row)
        for m in _embedded(i):
            if m.get("type") == "modification" and (mid := amod_m.match(m, warn, "engine.kind.armorMod")):
                armor_mods.append(
                    {"id": str(uuid.uuid4()), "mod_id": mid, "parent_id": row["id"], "rating": _rating(m)}
                )

    weapons_by_id = {str(r["id"]): r for r in cat["weapons"]}
    weap_m = _Matcher(cat["weapons"])
    wacc_m = _Matcher(cat["weapon_accessories"])
    weapons: list[dict[str, Any]] = []
    accessories: list[dict[str, Any]] = []
    for i in items:
        if i.get("type") != "weapon" or not (wid := weap_m.match(i, warn, "engine.kind.weapon")):
            continue
        spec = weapons_by_id[wid]
        if not spec.get("purchasable", True):
            # a cyberspur, bioware claws: the ware that grants it brings it back
            continue
        row = {"id": str(uuid.uuid4()), "weapon_id": wid, "qty": max(1, _num(_tech(i).get("quantity"), 1))}
        weapons.append(row)
        built_in = {str(n).lower() for n in spec.get("included") or []}
        for acc in _embedded(i):
            if acc.get("type") != "modification":
                continue
            english = str(_flags(acc).get("name") or acc.get("name") or "").lower()
            if english in built_in:
                continue  # comes with the weapon
            if acid := wacc_m.match(acc, warn, "engine.kind.weaponAccessory"):
                mount = str(((acc.get("system") or {}).get("mod_weapon") or {}).get("mount_point") or "")
                accessories.append(
                    {
                        "id": str(uuid.uuid4()),
                        "accessory_id": acid,
                        "parent_id": row["id"],
                        "mount": mount.capitalize(),
                        "rating": _rating(acc),
                    }
                )

    ware_ids: dict[str, set[str]] = {}
    ware_rows: list[dict[str, Any]] = []
    for kind in ("cyberware", "bioware"):
        rows = cast(dict[str, Any], cat.get(kind) or {}).get("items") or []
        ware_ids[kind] = {str(r["id"]) for r in rows}
        ware_rows += rows
    ware_m = _Matcher(ware_rows)
    variable_ware = {str(r["id"]) for r in ware_rows if r.get("cost_range")}
    ware: dict[str, list[dict[str, Any]]] = {"cyberware": [], "bioware": []}
    for i in items:
        kind = str(i.get("type") or "")
        if kind not in ware or not (wid := ware_m.match(i, warn, f"engine.kind.{kind}")):
            continue
        row = {
            "id": str(uuid.uuid4()),
            "ware_id": wid,
            "rating": _rating(i),
            "grade": _GRADES.get(str((i.get("system") or {}).get("grade") or ""), "Standard"),
            "extra": _extra(i),
        }
        if wid in variable_ware:
            row["cost"] = _num(_tech(i).get("cost"))
        # the bucket the catalog has it in, whatever Foundry called it
        ware["bioware" if wid in ware_ids["bioware"] else "cyberware"].append(row)
    st.update(armor=armor, armor_mods=armor_mods, weapons=weapons, weapon_accessories=accessories, **ware)


def _import_gear(items: list[dict[str, Any]], st: dict[str, Any], warn: list[Notice]) -> None:
    """Gear, into whichever bucket matches it. Foundry keeps it flat."""
    matchers = {b: _Matcher(catalog_list(b)) for b in (*_GEAR_BUCKETS, "gear")}
    rows_by_id = {str(r["id"]): r for b in matchers for r in catalog_list(b)}
    routed: dict[str, list[dict[str, Any]]] = {b: [] for b in matchers}
    for i in items:
        if i.get("type") not in _GEAR_TYPES:
            continue
        got = next(((b, gid) for b, m in matchers.items() if (gid := m.find(i))), None)
        if not got:
            warn.append(notice("engine.import.skippedUnknown", kind=ui("engine.kind.gear"), name=str(i.get("name"))))
            continue
        bucket, gid = got
        spec = rows_by_id[gid]
        qty = max(1, _num(_tech(i).get("quantity"), 1))
        row: dict[str, Any] = {"id": str(uuid.uuid4()), "gear_id": gid, "rating": _rating(i)}
        # Foundry counts single items (100 rounds); this app counts what the
        # price is quoted for (a box of 10)
        row["qty"] = qty if bucket == "commlinks" else max(1, math.ceil(qty / max(1, _num(spec.get("costfor")))))
        if spec.get("cost_range"):
            row["cost"] = _num(_tech(i).get("cost"))
        if extra := _extra(i):
            row["extra"] = extra
        routed[bucket].append(row)
    st.update(routed)


def _import_life(
    system: dict[str, Any], items: list[dict[str, Any]], cat: CatalogDict, st: dict[str, Any], warn: list[Notice]
) -> None:
    """Contacts, lifestyles and the tradition."""
    st["contacts"] = [
        {
            "id": str(uuid.uuid4()),
            "name": str(i.get("name") or ""),
            "role": str((i.get("system") or {}).get("type") or "") or None,
            "connection": max(1, _num((i.get("system") or {}).get("connection"), 1)),
            "loyalty": max(1, _num((i.get("system") or {}).get("loyalty"), 1)),
            "group": bool((i.get("system") or {}).get("group")),
        }
        for i in items
        if i.get("type") == "contact"
    ]
    ls_m = _Matcher(cat["lifestyles"])
    lifestyles: list[dict[str, Any]] = []
    for i in items:
        if i.get("type") != "lifestyle":
            continue
        # a lifestyle is named by the player: the catalog one is its `type`
        lid = ls_m.find(i) or ls_m.by_name.get(
            _LIFESTYLES.get(str((i.get("system") or {}).get("type") or ""), "").lower()
        )
        if lid:
            lifestyles.append({"id": str(uuid.uuid4()), "lifestyle_id": lid, "months": 1})
        else:
            warn.append(
                notice("engine.import.skippedUnknown", kind=ui("engine.kind.lifestyle"), name=str(i.get("name")))
            )
    st["lifestyles"] = lifestyles
    if st["talent"] in ("Magician", "Mystic Adept", "Aspected Magician"):
        # Foundry keeps only the drain attribute: the first tradition that
        # resists drain with it (Hermetic for LOG, Shamanic for CHA)
        drain = _ATTRIBUTES.get(str((system.get("magic") or {}).get("attribute") or ""))
        tid = next((str(t["id"]) for t in cat["traditions"] if (t.get("drain_attrs") or [])[-1:] == [drain]), None)
        if tid:
            st["tradition_id"] = tid


def _import_balance(system: dict[str, Any], st: dict[str, Any]) -> None:
    """Karma and nuyen left as Foundry had them, the rest kept as an adjustment
    (as for a Chummer career save without its expense log); street cred,
    notoriety and public awareness likewise, as the part not worked out here."""
    from ..engine import compute
    from ..models import CharacterState

    def derived() -> dict[str, Any]:
        bare = copy.deepcopy({k: v for k, v in st.items() if not k.startswith("_")})
        return compute(CharacterState.model_validate(bare)).derived

    d = derived()
    st["karma_adjust"] = _num((system.get("karma") or {}).get("value")) - _num((d.get("karma") or {}).get("remaining"))
    st["nuyen_adjust"] = _num(system.get("nuyen")) - _num(d.get("nuyen"))
    # karma earned counts toward street cred: worked out again with it in
    d = derived()
    st["street_cred"] = max(0, _num(system.get("street_cred")) - _num(d.get("street_cred")))
    st["notoriety_bonus"] = _num(system.get("notoriety")) - _num(d.get("notoriety"))
    st["public_awareness"] = max(0, _num(system.get("public_awareness")) - _num(d.get("public_awareness")))


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
    _import_combat(items, cat, st, warn)
    _import_gear(items, st, warn)
    _import_life(system, items, cat, st, warn)
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
