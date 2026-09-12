"""Import a Chummer5a save (``.chum5`` plain XML or ``.chum5lz`` LZMA-compressed)
into this app's ``CharacterState``.

Best-effort: identity / priorities / attributes / skills / qualities / spells /
adept powers / complex forms / martial arts / contacts / lifestyles / tradition /
mentor / initiation, plus id-resolved ware (nested), armor + mods, weapons +
accessories, gear (nested, routed to commlink/deck/sensor/program/… buckets),
vehicles + drones + vehicle mods. Anything the catalog can't resolve is skipped
and named in the returned warning list rather than failing the import.
"""

from __future__ import annotations

import json
import lzma
import os
import uuid
import xml.etree.ElementTree as ET  # the Element type only — parsing goes through defusedxml
import zlib
from typing import Any

from defusedxml import DefusedXmlException
from defusedxml.ElementTree import fromstring as _xml_fromstring

from .data_loader import CatalogDict, catalog, catalog_list
from .engine.constants import (
    quality_addspirit_extra_key,
    quality_optional_power_extra_key,
    quality_spirit_category_extra_key,
)
from .engine.lookups import critter_power_label
from .engine.qualities import _quality_needs_spell_category, _quality_needs_spirit_category
from .notices import Notice, NoticeError, Phrase, notice, ui

# Upper bound on the decompressed size of a .chum5lz payload — a guard against
# decompression bombs on the import endpoint. A real Chummer save (even with
# base64 portraits) is a few MB; the default sits well clear of that.
_MAX_DECOMPRESSED_BYTES = int(os.environ.get("CHUM5_MAX_DECOMPRESSED_BYTES") or 32 * 1024 * 1024)

_BUILD_METHODS = {
    "priority": "Priority",
    "sumtoten": "SumToTen",
    "sum-to-ten": "SumToTen",
    "karma": "Karma",
    "lifemodule": "Priority",
}


def _bounded_lzma(raw: bytes, fmt: int) -> bytes:
    d = lzma.LZMADecompressor(format=fmt)
    out = d.decompress(raw, _MAX_DECOMPRESSED_BYTES + 1)
    if len(out) > _MAX_DECOMPRESSED_BYTES or not d.eof:
        raise ValueError("decompressed .chum5lz exceeds the size limit")
    return out


def _bounded_zlib(raw: bytes, wbits: int) -> bytes:
    d = zlib.decompressobj(wbits)
    out = d.decompress(raw, _MAX_DECOMPRESSED_BYTES + 1)
    if d.unconsumed_tail:
        raise ValueError("decompressed .chum5lz exceeds the size limit")
    out += d.flush()
    if len(out) > _MAX_DECOMPRESSED_BYTES:
        raise ValueError("decompressed .chum5lz exceeds the size limit")
    return out


def decompress_chum5lz(raw: bytes | str) -> bytes:
    """Return the inner XML bytes from a ``.chum5`` / ``.chum5lz`` payload.

    Plain XML is returned as-is. Chummer5a's ``.chum5lz`` (LzmaHelper.cs
    ``CompressToLzmaFile``) is the legacy ``.lzma`` "alone" container: a 5-byte
    LZMA property header, an 8-byte little-endian uncompressed size (``0xFF``*8
    when written with an end marker), then a raw LZMA1 stream — i.e. Python's
    ``lzma.FORMAT_ALONE``. xz / zlib / gzip are also tried as a courtesy.

    Every branch is bounded to ``_MAX_DECOMPRESSED_BYTES`` so a crafted payload
    cannot expand without limit (decompression bomb).
    """
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    head = raw.lstrip()[:64].lstrip(b"\xef\xbb\xbf").lstrip()
    if head.startswith(b"<"):  # already plain XML
        return raw
    errors: list[str] = []  # exception class names, for the failure message
    for attempt in (
        lambda: _bounded_lzma(raw, lzma.FORMAT_ALONE),  # Chummer's format
        lambda: _bounded_lzma(raw, lzma.FORMAT_AUTO),  # xz / auto
        lambda: _bounded_zlib(raw, zlib.MAX_WBITS),
        lambda: _bounded_zlib(raw, -zlib.MAX_WBITS),
        lambda: _bounded_zlib(raw, zlib.MAX_WBITS | 16),  # gzip
    ):
        try:
            out = attempt()
            if out.lstrip()[:16].lower().startswith((b"<?xml", b"<character", b"\xef\xbb\xbf")):
                return out
        except Exception as exc:  # noqa: BLE001 - trying formats
            errors.append(type(exc).__name__)
    raise NoticeError(notice("api.chum5lzUndecompressible", formats=", ".join(dict.fromkeys(errors))))


def _text(el: ET.Element | None, default: str = "") -> str:
    return (el.text or default).strip() if el is not None and el.text else default


def _int(el: ET.Element | None, default: int = 0) -> int:
    try:
        return int(float(_text(el) or default))
    except (TypeError, ValueError):
        return default


def _read_mugshot(root: ET.Element) -> str:
    """Chummer stores portraits as base64 either in ``<mugshots><mugshot>`` (with
    ``<mainmugshotindex>`` picking one) or a legacy flat ``<mugshot>``. Return a
    ``data:`` URI ready for an ``<img>`` ``src``, or ``""``."""
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
        return raw
    mime = "image/jpeg" if raw.startswith("/9j/") else "image/png"
    return f"data:{mime};base64,{raw}"


def _by_name(rows: list[dict[str, Any]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for r in rows:
        n = (r.get("name") or "").strip()
        if n:
            out.setdefault(n.lower(), r["id"])
    return out


class _Resolver:
    """name / sourceid -> catalog id for one bucket."""

    def __init__(self, rows: list[dict[str, Any]]):
        self.by_name = _by_name(rows)
        self.ids = {r["id"] for r in rows}

    def resolve(self, node: ET.Element, warn: list[Notice], kind: Phrase) -> str | None:
        sid = _text(node.find("sourceid")) or _text(node.find("guid"))
        if sid and sid in self.ids:
            return sid
        name = _text(node.find("name"))
        got = self.by_name.get(name.lower())
        if got:
            return got
        if name:
            warn.append(notice("engine.import.skippedUnknown", kind=kind, name=name))
        return None


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
        v = _text(root.find(f"./priorities/{tag}")) or _text(root.find(tag))
        return v.upper() if v in "ABCDEabcde" else "C"

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


def _import_attributes(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read the eight attributes plus EDG/MAG/RES, as base + karma."""
    attrs: dict[str, int] = {}
    for a in root.findall("./attributes/attribute"):
        name = _text(a.find("name")).upper()
        if name in ("ESS", "ESSENCE") or not name:
            continue
        # Chummer <base> is points spent above the metatype minimum.
        lo = _int(a.find("metatypemin"), 1)
        attrs[name] = max(lo + _int(a.find("base")) + _int(a.find("karma")), lo)
    st["attributes"] = attrs or {"BOD": 1, "AGI": 1, "REA": 1, "STR": 1, "CHA": 1, "INT": 1, "LOG": 1, "WIL": 1}


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


def _import_qualities(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read positive/negative qualities and the targets they were taken with."""
    q_by_name = _by_name(cat["qualities"])
    q_ids = {r["id"] for r in cat["qualities"]}
    quality_ids: list[str] = []
    quality_extras: dict[str, str] = {}
    picks: dict[str, str] = {}
    for q in root.findall("./qualities/quality"):
        src = _text(q.find("qualitysource")).lower()
        if src and src not in ("selected", "builtin", ""):
            continue  # metatype / life-module grants are re-derived by the engine
        sid = _text(q.find("sourceid")) or _text(q.find("guid"))
        qid = sid if sid in q_ids else q_by_name.get(_text(q.find("name")).lower())
        if not qid:
            nm = _text(q.find("name"))
            if nm:
                warn.append(notice("engine.import.skippedUnknown", kind=ui("engine.kind.quality"), name=nm))
            continue
        if qid not in quality_ids:
            quality_ids.append(qid)
        extra = _text(q.find("extra"))
        quality_extras.update(_quality_extra_in(cat, qid, extra, _text(q.find("guid")), root))
        for pick in q.findall("./skillpicks/pick"):
            skill = _text(pick.find("skill"))
            if skill:
                picks[f"quality:{qid}:{_text(pick.find('index'))}"] = skill
    _import_optional_powers(root, cat, quality_ids, quality_extras)
    st["quality_ids"] = quality_ids
    st["quality_extras"] = quality_extras
    # Merged rather than assigned: `_import_ware` fills in the implant picks,
    # and the two sections run in either order.
    st["skill_picks"] = {**(st.get("skill_picks") or {}), **picks}


def _import_optional_powers(
    root: ET.Element, cat: CatalogDict, quality_ids: list[str], quality_extras: dict[str, str]
) -> None:
    """An Infected quality's optional power, back out of `<critterpowers>`.

    The file lists every power the character has without saying which pick
    it was, so each quality first claims the powers it always grants and then
    the first remaining one on its optional list — by name and `<extra>`,
    because Immunity comes both ways (Grendel is granted Immunity (Toxins)
    and may pick it again).
    """
    pool = [
        critter_power_label({"name": _text(p.find("name")), "select": _text(p.find("extra"))})
        for p in root.findall("./critterpowers/critterpower")
        if _text(p.find("name"))
    ]
    by_id = {str(row["id"]): row for row in cat["qualities"]}
    for qid in quality_ids:
        spec = by_id.get(qid) or {}
        optional = [critter_power_label(row) for row in spec.get("optional_powers") or []]
        if not optional:
            continue
        for row in spec.get("critter_powers") or []:
            label = critter_power_label(row)
            if label in pool:
                pool.remove(label)
        picked = next((label for label in pool if label in optional), None)
        if picked is not None:
            pool.remove(picked)
            quality_extras[quality_optional_power_extra_key(qid)] = picked


def _quality_extra_in(cat: CatalogDict, qid: str, extra: str, guid: str, root: ET.Element) -> dict[str, str]:
    """The mirror of the export's `_quality_extra_out`: a quality's `<extra>`
    back into the keys the engine reads.

    Chain Breaker / Dark Ally: the `, `-joined spirits, one `:addspirit:N`
    slot each. Apprentice: `<extra>` is the spirit and the spell category is
    on the `LimitSpellCategory` improvement carrying the quality's guid — a
    file this app wrote before that has the category in `<extra>` instead,
    told apart by whether the text names a spirit.
    """
    spec = next((row for row in cat["qualities"] if row["id"] == qid), None) or {}
    if str(spec.get("extra_kind") or "") == "add_spirit":
        spirits = [part.strip() for part in extra.split(",") if part.strip()]
        return {quality_addspirit_extra_key(qid, idx): name for idx, name in enumerate(spirits)}
    if _quality_needs_spirit_category(spec) and _quality_needs_spell_category(spec):
        out: dict[str, str] = {}
        category = ""
        if guid:
            for imp in root.findall("./improvements/improvement"):
                if (
                    _text(imp.find("sourcename")) == guid
                    and _text(imp.find("improvementttype")) == "LimitSpellCategory"
                ):
                    category = _text(imp.find("improvedname"))
                    break
        spirit_names = {str(row.get("name") or "") for row in cat.get("spirits") or []}
        if category:
            out[qid] = category
            if extra:
                out[quality_spirit_category_extra_key(qid)] = extra
        elif extra in spirit_names:
            out[quality_spirit_category_extra_key(qid)] = extra
        elif extra:
            out[qid] = extra
        return out
    return {qid: extra} if extra else {}


def _import_magic(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read spells, adept powers, complex forms and magic arts."""
    spell_r = _Resolver(cat["spells"])
    st["spells"] = [
        {"id": str(uuid.uuid4()), "spell_id": spell_ref, "alchemical": _text(sp.find("alchemical")).lower() == "true"}
        for sp in root.findall("./spells/spell")
        if (spell_ref := spell_r.resolve(sp, warn, ui("engine.kind.spell")))
    ]
    power_r = _Resolver(cat["powers"])
    powers = []
    for p in root.findall("./powers/power"):
        pid = power_r.resolve(p, warn, ui("engine.kind.adeptPower"))
        if pid:
            powers.append(
                {
                    "id": str(uuid.uuid4()),
                    "power_id": pid,
                    "rating": max(1, _int(p.find("rating"), 1)),
                    "extra": _text(p.find("extra")) or None,
                }
            )
    st["adept_powers"] = powers

    cf_r = _Resolver(cat["complex_forms"])
    st["complex_forms"] = [
        {
            "id": str(uuid.uuid4()),
            "form_id": fid,
            "level": _int(c.find("rating"), 1) or None,
            "extra": _text(c.find("extra")) or None,
        }
        for c in root.findall("./complexforms/complexform")
        if (fid := cf_r.resolve(c, warn, ui("engine.kind.complexForm")))
    ]

    tr_r = _Resolver(cat["traditions"])
    trad = root.find("tradition")
    if trad is not None and _text(trad.find("name")):
        tid = tr_r.resolve(trad, warn, ui("engine.kind.tradition"))
        if tid:
            st["tradition_id"] = tid

    stream_name = _text(root.find("stream"))
    if stream_name:
        sid = _Resolver(cat["streams"]).by_name.get(stream_name.lower())
        if sid:
            st["stream_id"] = sid
        else:
            warn.append(notice("engine.import.skippedUnknown", kind=ui("engine.kind.stream"), name=stream_name))

    # A Mystic Adept's MAG is split; the adept half is the power points bought.
    split = _int(root.find("magsplitadept"), 0)
    if split > 0:
        st["mystic_pp"] = split

    men = root.find("mentorspirit")
    if men is None:
        men = root.find("./mentorspirits/mentorspirit")
    if men is not None:
        # Chummer writes a paragon into the same element with the same class,
        # so both lists answer here; the guids are unique across the two files.
        mentors = list(cat["mentors"]) + list(cat["paragons"])
        mid = _Resolver(mentors).resolve(men, warn, ui("engine.kind.mentor"))
        if mid:
            st["mentor_id"] = mid
        # This app's own pair of lists (see the export); a file Chummer wrote
        # has only `<extrachoice1>` / `<extrachoice2>`, which name the pick
        # itself rather than what it resolved to.
        choices = [_text(c) for c in men.findall("./choices/choice")]
        choices = [c for c in choices if c]
        extras = {
            key: _text(row.find("value")) for row in men.findall("./extras/extra") if (key := _text(row.find("key")))
        }
        if not choices:
            choices = [name for tag in ("extrachoice1", "extrachoice2") if (name := _text(men.find(tag)))]
        st["mentor_choices"] = choices
        st["mentor_extras"] = extras


def _import_spirits(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read bound spirits, registered sprites and adept enhancements.

    Chummer keeps spirits and sprites in one `<spirits>`, told apart by
    `<type>`; a sprite's Level is its `<force>`.
    """
    spirit_r = _Resolver(cat["spirits"])
    sprite_r = _Resolver(cat["sprites"])
    spirits: list[dict[str, Any]] = []
    sprites: list[dict[str, Any]] = []
    for el in root.findall("./spirits/spirit"):
        force = max(1, _int(el.find("force"), 1))
        services = max(0, _int(el.find("services"), 0))
        hits = _int(el.find("hits"), 0) or None
        opposed = _int(el.find("opposedhits"), 0) or None
        bound = _text(el.find("bound")).lower() == "true"
        if _text(el.find("type")).lower() == "sprite":
            pid = sprite_r.resolve(el, warn, ui("engine.kind.sprite"))
            if pid:
                sprites.append(
                    {
                        "id": str(uuid.uuid4()),
                        "sprite_id": pid,
                        "level": force,
                        "services": services,
                        "registered": bound,
                        "hits": hits,
                        "opposed_hits": opposed,
                    }
                )
            continue
        sid = spirit_r.resolve(el, warn, ui("engine.kind.spirit"))
        if sid:
            spirits.append(
                {
                    "id": str(uuid.uuid4()),
                    "spirit_id": sid,
                    "force": force,
                    "services": services,
                    "bound": bound,
                    "hits": hits,
                    "opposed_hits": opposed,
                }
            )
    st["spirits"] = spirits
    st["sprites"] = sprites

    enh_r = _Resolver(cat["enhancements"])
    st["adept_enhancements"] = [
        eid
        for el in root.findall("./enhancements/enhancement")
        if (eid := enh_r.resolve(el, warn, ui("engine.kind.enhancement")))
    ]


def _import_initiation(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read initiation and submersion grades, metamagics and echoes."""
    mm_r = _Resolver(cat["metamagics"])
    art_r = _Resolver(cat.get("magic_arts") or [])
    init_grade = sub_grade = 0
    init_flags: dict[int, dict[str, bool]] = {}
    sub_flags: dict[int, dict[str, bool]] = {}
    for g in root.findall("./initiationgrades/initiationgrade"):
        gnum = _int(g.find("grade"))
        is_sub = _text(g.find("res")).lower() == "true"
        flags = {
            "group": _text(g.find("group")).lower() == "true",
            "ordeal": _text(g.find("ordeal")).lower() == "true",
            "schooling": _text(g.find("schooling")).lower() == "true",
        }
        if is_sub:
            sub_grade = max(sub_grade, gnum)
            sub_flags[gnum] = flags
        else:
            init_grade = max(init_grade, gnum)
            init_flags[gnum] = flags
    picks = [
        oid
        for m in root.findall("./metamagics/metamagic")
        for oid in [mm_r.resolve(m, [], ui("engine.kind.metamagic")) or art_r.resolve(m, [], ui("engine.kind.art"))]
        if oid
    ]
    inits: list[dict[str, Any]] = []
    for grade in range(1, init_grade + 1):
        row: dict[str, Any] = {"id": str(uuid.uuid4()), "grade": grade, "kind": "metamagic", "option_id": ""}
        if grade <= len(picks):
            row["option_id"] = picks[grade - 1]
        row.update(init_flags.get(grade, {}))
        inits.append(row)
    subs = [
        {"id": str(uuid.uuid4()), "grade": grade, "echo_id": "", **sub_flags.get(grade, {})}
        for grade in range(1, sub_grade + 1)
    ]
    st["initiate_grade"] = init_grade
    st["submersion_grade"] = sub_grade
    st["initiations"] = inits
    st["submersions"] = subs


def _import_ware(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read cyber- and bioware, nested to any depth."""
    ware_rows = (cat.get("cyberware") or {}).get("items") or []
    ware_rows = ware_rows + ((cat.get("bioware") or {}).get("items") or [])
    ware_r = _Resolver(ware_rows)
    picks: dict[str, str] = {}

    def load_ware(nodes: list[ET.Element], kind: Phrase) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for w in nodes:
            wid = ware_r.resolve(w, warn, kind)
            if not wid:
                continue
            row = {
                "id": str(uuid.uuid4()),
                "ware_id": wid,
                "rating": max(1, _int(w.find("rating"), 1)),
                "grade": _text(w.find("grade")) or "Standard",
                "side": _text(w.find("location")) or None,
                "extra": _text(w.find("extra")) or None,
            }
            out.append(row)
            for pick in w.findall("./skillpicks/pick"):
                skill = _text(pick.find("skill"))
                if skill:
                    picks[f"ware:{row['id']}:{_text(pick.find('index'))}"] = skill
            kids = w.findall("./children/cyberware") + w.findall("./children/bioware")
            for child in load_ware(kids, kind):
                child["parent_id"] = row["id"]
                child["included"] = True
                out.append(child)
            if w.find("./gears/gear") is not None:
                warn.append(notice("engine.import.nestedGearSkipped", kind=kind, name=_text(w.find("name"))))
        return out

    st["cyberware"] = load_ware(root.findall("./cyberwares/cyberware"), ui("engine.kind.cyberware"))
    st["bioware"] = load_ware(
        root.findall("./biowares/bioware") + root.findall("./cyberwares/bioware"), ui("engine.kind.bioware")
    )
    st["skill_picks"] = {**(st.get("skill_picks") or {}), **picks}


def _import_armor(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read armor and the mods bolted to it."""
    armor_r = _Resolver(cat["armor"])
    amod_r = _Resolver(cat["armor_mods"])
    st_armor: list[dict[str, Any]] = []
    st_amods: list[dict[str, Any]] = []
    for a in root.findall("./armors/armor"):
        aid = armor_r.resolve(a, warn, ui("engine.kind.armor"))
        if not aid:
            continue
        row = {
            "id": str(uuid.uuid4()),
            "armor_id": aid,
            "rating": max(1, _int(a.find("rating"), 1)),
            "equipped": _text(a.find("equipped")).lower() != "false",
        }
        st_armor.append(row)
        for m in a.findall("./armormods/armormod"):
            mid = amod_r.resolve(m, warn, ui("engine.kind.armorMod"))
            if mid:
                st_amods.append(
                    {
                        "id": str(uuid.uuid4()),
                        "mod_id": mid,
                        "parent_id": row["id"],
                        "rating": max(1, _int(m.find("rating"), 1)),
                        "included": _text(m.find("included")).lower() == "true",
                        # Custom Fit (Stack): the armor it was tailored to
                        "stack_with": _text(m.find("extra")),
                    }
                )
    st["armor"] = st_armor
    st["armor_mods"] = st_amods


def _import_weapons(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read weapons and their accessories."""
    # Only weapons a character could have bought: the granted ones (a cyberspur,
    # bioware claws) come back with the ware that grants them, and matching them
    # here as well would give the character the weapon twice.
    weap_r = _Resolver([w for w in cat["weapons"] if w.get("purchasable")])
    wacc_r = _Resolver(cat["weapon_accessories"])
    st_weap: list[dict[str, Any]] = []
    st_wacc: list[dict[str, Any]] = []
    for w in root.findall("./weapons/weapon"):
        if _text(w.find("cyberware")).lower() == "true":
            continue
        wid = weap_r.resolve(w, warn, ui("engine.kind.weapon"))
        if not wid:
            continue
        row = {"id": str(uuid.uuid4()), "weapon_id": wid, "qty": max(1, _int(w.find("qty"), 1))}
        st_weap.append(row)
        for acc in w.findall("./accessories/accessory"):
            acid = wacc_r.resolve(acc, warn, ui("engine.kind.weaponAccessory"))
            if acid:
                st_wacc.append(
                    {
                        "id": str(uuid.uuid4()),
                        "accessory_id": acid,
                        "parent_id": row["id"],
                        "mount": _text(acc.find("mount")),
                        "rating": max(1, _int(acc.find("rating"), 1)),
                        "included": _text(acc.find("included")).lower() == "true",
                    }
                )
    st["weapons"] = st_weap
    st["weapon_accessories"] = st_wacc


def _import_gear(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read gear, routed to whichever catalog bucket resolves it."""
    BUCKETS = ("commlinks", "cyberdecks", "rccs", "sensors", "optics", "programs", "apps", "drones")
    gear_res = {b: _Resolver(catalog_list(b)) for b in ("gear", *BUCKETS)}
    routed: dict[str, list[dict[str, Any]]] = {b: [] for b in ("gear", *BUCKETS)}

    def route_gear(g: ET.Element, parent_id: str | None, parent_bucket: str | None) -> None:
        sid = _text(g.find("sourceid")) or _text(g.find("guid"))
        name = _text(g.find("name"))
        bucket = "gear"
        gid: str | None = None
        # a child stays with its parent's bucket if it resolves there
        order = ([parent_bucket] if parent_bucket else []) + list(BUCKETS) + ["gear"]
        for b in order:
            if not b:
                continue
            r = gear_res[b]
            cand = sid if sid in r.ids else r.by_name.get(name.lower())
            if cand:
                gid, bucket = cand, b
                break
        if not gid:
            if name:
                warn.append(notice("engine.import.skippedUnknown", kind=ui("engine.kind.gear"), name=name))
            return
        row: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "gear_id": gid,
            "rating": max(1, _int(g.find("rating"), 1)),
        }
        if bucket == "commlinks":
            row.pop("rating", None)
            row["rating"] = max(1, _int(g.find("rating"), 1))
        else:
            row["qty"] = max(1, _int(g.find("qty"), 1))
            if parent_id:
                row["parent_id"] = parent_id
                row["included"] = _text(g.find("included")).lower() == "true"
        routed[bucket].append(row)
        for child in g.findall("./children/gear"):
            route_gear(child, row["id"], bucket)

    for g in root.findall("./gears/gear"):
        # A bonded focus is gear too, but it belongs to `foci` / `qi_foci`
        # rather than to any gear bucket — `_import_foci` reads it there.
        if _text(g.find("category")) == "Foci":
            continue
        route_gear(g, None, None)
    for b, rows in routed.items():
        st[b] = rows


def _import_vehicles(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read vehicles, drones and vehicle mods."""
    veh_r = _Resolver(cat["vehicles"])
    drone_r = _Resolver(cat["drones"])
    vmod_r = _Resolver(cat["vehicle_mods"])
    mount_r = _Resolver(cat["weapon_mounts"])
    mount_categories = {row["id"]: row.get("category") or "" for row in cat["weapon_mounts"]}
    # A mount points at a weapon row by name: ids are regenerated on import.
    weapon_ids: dict[str, str] = {}
    for wrow in st.get("weapons") or []:
        wname = next((w["name"] for w in cat["weapons"] if w["id"] == wrow.get("weapon_id")), "")
        weapon_ids.setdefault(wname.lower(), wrow["id"])
    st_mounts: list[dict[str, Any]] = []
    st_veh: list[dict[str, Any]] = list(st.get("drones") or [])
    st_veh_only: list[dict[str, Any]] = []
    st_vmods: list[dict[str, Any]] = []
    for v in root.findall("./vehicles/vehicle"):
        is_drone = veh_r.resolve(v, [], ui("engine.kind.vehicle")) is None
        vid = (
            drone_r.resolve(v, [], ui("engine.kind.drone"))
            if is_drone
            else veh_r.resolve(v, warn, ui("engine.kind.vehicle"))
        )
        if not vid:
            vid = veh_r.resolve(v, [], ui("engine.kind.vehicle")) or drone_r.resolve(v, warn, ui("engine.kind.drone"))
        if not vid:
            continue
        row = {"id": str(uuid.uuid4()), "gear_id": vid, "rating": 1, "qty": 1}
        (st_veh if is_drone else st_veh_only).append(row)
        for m in v.findall("./mods/mod") + v.findall("./vehiclemods/vehiclemod"):
            mid = vmod_r.resolve(m, warn, ui("engine.kind.vehicleMod"))
            if mid:
                st_vmods.append(
                    {
                        "id": str(uuid.uuid4()),
                        "mod_id": mid,
                        "parent_id": row["id"],
                        "rating": max(1, _int(m.find("rating"), 1)),
                        "included": _text(m.find("included")).lower() == "true",
                    }
                )
        for m in v.findall("./weaponmounts/weaponmount"):
            size_id = mount_r.resolve(m, warn, ui("engine.kind.weaponMount"))
            if not size_id:
                continue
            parts = {"Visibility": "", "Flexibility": "", "Control": ""}
            for opt in m.findall("./weaponmountoptions/weaponmountoption"):
                part_id = mount_r.resolve(opt, warn, ui("engine.kind.weaponMount"))
                if part_id and mount_categories.get(part_id) in parts:
                    parts[mount_categories[part_id]] = part_id
            st_mounts.append(
                {
                    "id": str(uuid.uuid4()),
                    "parent_id": row["id"],
                    "size_id": size_id,
                    "visibility_id": parts["Visibility"],
                    "flexibility_id": parts["Flexibility"],
                    "control_id": parts["Control"],
                    "included": _text(m.find("included")).lower() == "true",
                    "weapon_install_id": weapon_ids.get(_text(m.find("mountedweaponname")).lower()),
                    "allowedweapons": _text(m.find("weaponmountcategories")),
                }
            )
        if v.find("./weapons/weapon") is not None or v.find("./gears/gear") is not None:
            warn.append(notice("engine.import.vehicleLoadSkipped", name=_text(v.find("name"))))
    st["drones"] = st_veh
    st["vehicles"] = st_veh_only
    st["vehicle_mods"] = st_vmods
    st["weapon_mounts"] = st_mounts


def _import_lifestyles(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read lifestyles, contacts and martial arts."""
    ls_r = _Resolver(cat["lifestyles"])
    lifestyles = []
    for ls in root.findall("./lifestyles/lifestyle"):
        base = _text(ls.find("baselifestyle")) or _text(ls.find("name"))
        lid = ls_r.by_name.get(base.lower())
        if lid:
            lifestyles.append(
                {"id": str(uuid.uuid4()), "lifestyle_id": lid, "months": max(1, _int(ls.find("months"), 1))}
            )
        elif base:
            warn.append(notice("engine.import.skippedUnknown", kind=ui("engine.kind.lifestyle"), name=base))
    st["lifestyles"] = lifestyles

    contacts = []
    for c in root.findall("./contacts/contact"):
        nm = _text(c.find("name"))
        if not nm and not _text(c.find("role")):
            continue
        contacts.append(
            {
                "id": str(uuid.uuid4()),
                "name": nm,
                "role": _text(c.find("role")) or None,
                "connection": max(1, _int(c.find("connection"), 1)),
                "loyalty": max(1, _int(c.find("loyalty"), 1)),
                "group": _text(c.find("type")).lower() == "group" or _text(c.find("isgroup")).lower() == "true",
            }
        )
    st["contacts"] = contacts

    ma_r = _Resolver(cat["martial_arts"])
    marts = []
    for m in root.findall("./martialarts/martialart"):
        aid = ma_r.resolve(m, warn, ui("engine.kind.martialArt"))
        if aid:
            techs = [_text(t.find("name")) for t in m.findall("./martialarttechniques/martialarttechnique")]
            techs = [t for t in techs if t]
            marts.append({"id": str(uuid.uuid4()), "art_id": aid, "techniques": techs})
    st["martial_arts"] = marts


def _import_foci(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read bonded foci back out of `<foci>` and the gear it points at.

    Chummer keeps the focus itself in `<gears>` (category `Foci`, `<bonded>`)
    and only a pointer in `<foci>`; a Qi focus is the same gear with the power
    it carries in `<extra>`. What this app knows on top of that — crafted vs.
    bought, the artificing test, the weapon a weapon focus is bound to — rides
    on the pointer and is simply absent on a file Chummer wrote.
    """
    qi_spec = cat.get("qi_focus") or {}
    qi_id = str(qi_spec.get("id") or "")
    focus_r = _Resolver(cat.get("foci") or [])
    power_r = _Resolver(cat["powers"])
    gear_by_id = {guid: g for g in root.findall("./gears/gear") if (guid := _text(g.find("guid")))}
    # Weapon foci point at a weapon row by name: ids are regenerated on import.
    weapon_ids: dict[str, str] = {}
    for row in st.get("weapons") or []:
        name = next((w["name"] for w in cat["weapons"] if w["id"] == row.get("weapon_id")), "")
        weapon_ids.setdefault(name.lower(), row["id"])

    foci: list[dict[str, Any]] = []
    qi_foci: list[dict[str, Any]] = []
    for f in root.findall("./foci/focus"):
        gear = gear_by_id.get(_text(f.find("gearid")))
        if gear is None:
            continue
        force = max(1, _int(gear.find("rating"), 1))
        sid = _text(gear.find("sourceid")) or _text(gear.find("guid"))
        if sid == qi_id or _text(gear.find("name")) == str(qi_spec.get("name") or ""):
            power_name = _text(gear.find("extra"))
            pid = power_r.by_name.get(power_name.lower())
            if not pid:
                if power_name:
                    warn.append(
                        notice("engine.import.skippedUnknown", kind=ui("engine.kind.adeptPower"), name=power_name)
                    )
                continue
            qi_foci.append(
                {
                    "id": str(uuid.uuid4()),
                    "rating": force,
                    "power_id": pid,
                    "power_rating": max(1, _int(f.find("powerrating"), 1)),
                    "extra": _text(f.find("powerextra")) or None,
                }
            )
            continue
        gid = focus_r.resolve(gear, warn, ui("engine.kind.focus"))
        if not gid:
            continue
        weapon_name = _text(f.find("weaponname"))
        foci.append(
            {
                "id": str(uuid.uuid4()),
                "gear_id": gid,
                "force": force,
                "crafted": _text(f.find("crafted")).lower() == "true",
                "formula_bought": _text(f.find("formulabought")).lower() != "false",
                "hits": _int(f.find("hits"), 0) or None,
                "opposed_hits": _int(f.find("opposedhits"), 0) or None,
                "extra": weapon_ids.get(weapon_name.lower()),
            }
        )
    st["foci"] = foci
    st["qi_foci"] = qi_foci


def _import_custom_drugs(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read mixed drugs back out of `<drugs><drug>`.

    A custom drug is its components: cost, availability, addiction and onset
    are recomputed from them, so nothing Chummer wrote about the totals is
    read back. `<active>` is this app's own element (see the export) and is
    simply absent on a file Chummer wrote.
    """
    comp_r = _Resolver(cat.get("drug_components") or [])
    drugs = []
    for d in root.findall("./drugs/drug"):
        parts = []
        for c in d.findall("./drugcomponents/drugcomponent"):
            cid = comp_r.resolve(c, warn, ui("engine.kind.drugComponent"))
            if cid:
                parts.append({"component_id": cid, "level": max(0, _int(c.find("level"), 0))})
        if not parts:
            continue
        drugs.append(
            {
                "id": str(uuid.uuid4()),
                "name": _text(d.find("name")),
                "grade": _text(d.find("grade")) or "Standard",
                "qty": max(1, _int(d.find("quantity"), 1)),
                "active": _text(d.find("active")).lower() == "true",
                "parts": parts,
            }
        )
    st["custom_drugs"] = drugs


def chum5_to_state(xml_bytes: bytes) -> tuple[dict[str, Any], list[str]]:
    """A Chummer5a save in, a `CharacterState` dict plus warnings out.

    Best-effort by design: anything the catalog cannot resolve becomes a
    warning, never an error, because a character that imports with three
    missing items is worth more to its owner than a refusal.

    Each `_import_*` below owns one section of the file. They are independent —
    each reads `root` and writes into `st` — which is why the 443-line function
    they came from could be cut along its own comment banners without moving a
    single line of logic.
    """
    xml_bytes = decompress_chum5lz(xml_bytes)
    try:
        root: ET.Element = _xml_fromstring(xml_bytes)
    except (ET.ParseError, DefusedXmlException) as exc:
        raise NoticeError(notice("api.xmlUnparsable", error=str(exc))) from exc
    if root.tag != "character":
        nested = root.find("character")
        root = nested if nested is not None else root
    if root.tag != "character":
        raise NoticeError(notice("api.notACharacterFile"))

    cat = catalog()
    warn: list[Notice] = []
    st: dict[str, Any] = {"id": str(uuid.uuid4())}

    for section in _SECTIONS:
        section(root, cat, st, warn)

    # collapse duplicate warnings, keep order. Notices are dicts, so dedupe on
    # a canonical rendering of each rather than on the object itself.
    seen: set[str] = set()
    unique: list[Notice] = []
    for item in warn:
        marker = json.dumps(item, sort_keys=True, ensure_ascii=False)
        if marker not in seen:
            seen.add(marker)
            unique.append(item)
    st["_warnings"] = unique
    return st, st["_warnings"]


#: Applied in order. Order matters only where a later section reads what an
#: earlier one wrote into `st` — ware before gear, because a cyberdeck can hang
#: off a cyberlimb.
_SECTIONS = (
    _import_identity,
    _import_attributes,
    _import_skills,
    _import_qualities,
    _import_magic,
    _import_spirits,
    _import_initiation,
    _import_ware,
    _import_armor,
    _import_weapons,
    _import_gear,
    _import_vehicles,
    _import_lifestyles,
    _import_foci,
    _import_custom_drugs,
)
