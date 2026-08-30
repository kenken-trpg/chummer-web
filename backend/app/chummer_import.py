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

import lzma
import re
import uuid
import xml.etree.ElementTree as ET
import zlib
from typing import Any

from .data_loader import catalog

_BUILD_METHODS = {
    "priority": "Priority",
    "sumtoten": "SumToTen",
    "sum-to-ten": "SumToTen",
    "karma": "Karma",
    "lifemodule": "Priority",
}


def decompress_chum5lz(raw: bytes | str) -> bytes:
    """Return the inner XML bytes from a ``.chum5`` / ``.chum5lz`` payload.

    Plain XML is returned as-is. Chummer5a's ``.chum5lz`` (LzmaHelper.cs
    ``CompressToLzmaFile``) is the legacy ``.lzma`` "alone" container: a 5-byte
    LZMA property header, an 8-byte little-endian uncompressed size (``0xFF``*8
    when written with an end marker), then a raw LZMA1 stream — i.e. Python's
    ``lzma.FORMAT_ALONE``. xz / zlib / gzip are also tried as a courtesy.
    """
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    head = raw.lstrip()[:64].lstrip(b"\xef\xbb\xbf").lstrip()
    if head.startswith(b"<"):  # already plain XML
        return raw
    errors: list[str] = []
    for attempt in (
        lambda: lzma.decompress(raw, format=lzma.FORMAT_ALONE),  # Chummer's format
        lambda: lzma.LZMADecompressor(format=lzma.FORMAT_ALONE).decompress(raw),
        lambda: lzma.decompress(raw),  # xz / auto
        lambda: zlib.decompress(raw),
        lambda: zlib.decompress(raw, -zlib.MAX_WBITS),
        lambda: zlib.decompress(raw, zlib.MAX_WBITS | 16),  # gzip
    ):
        try:
            out = attempt()
            if out.lstrip()[:16].lower().startswith((b"<?xml", b"<character", b"\xef\xbb\xbf")):
                return out
        except Exception as exc:  # noqa: BLE001 - trying formats
            errors.append(type(exc).__name__)
    raise ValueError(
        "この .chum5lz を展開できませんでした。Chummer で「名前を付けて保存」から "
        "非圧縮の .chum5 で書き出して読み込んでください。"
        f"（{', '.join(dict.fromkeys(errors))}）"
    )


def _text(el: ET.Element | None, default: str = "") -> str:
    return (el.text or default).strip() if el is not None and el.text else default


def _int(el: ET.Element | None, default: int = 0) -> int:
    try:
        return int(float(_text(el) or default))
    except (TypeError, ValueError):
        return default


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

    def resolve(self, node: ET.Element, warn: list[str], kind: str) -> str | None:
        sid = _text(node.find("sourceid")) or _text(node.find("guid"))
        if sid and sid in self.ids:
            return sid
        name = _text(node.find("name"))
        got = self.by_name.get(name.lower())
        if got:
            return got
        if name:
            warn.append(f"{kind}「{name}」はカタログに無いためスキップしました")
        return None


def chum5_to_state(xml_bytes: bytes) -> tuple[dict[str, Any], list[str]]:
    xml_bytes = decompress_chum5lz(xml_bytes)
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise ValueError(f"XML を解析できませんでした: {exc}") from exc
    if root.tag != "character":
        root = root.find("character") or root
    if root.tag != "character":
        raise ValueError("Chummer のキャラクターファイルではないようです（<character> が見つかりません）")

    cat = catalog()
    warn: list[str] = []
    st: dict[str, Any] = {"id": str(uuid.uuid4())}

    # --- identity -----------------------------------------------------------
    st["name"] = _text(root.find("alias")) or _text(root.find("name")) or "Imported Runner"
    st["metatype"] = _text(root.find("metatype")) or "Human"
    mv = _text(root.find("metavariant"))
    st["metavariant"] = mv if mv and mv.lower() not in ("none", "") else None
    st["talent"] = _text(root.find("./priorities/prioritytalent")) or _text(root.find("prioritytalent")) or "Mundane"
    st["build_method"] = _BUILD_METHODS.get(_text(root.find("buildmethod")).lower(), "Priority")
    created = _text(root.find("created")).lower() == "true"
    st["career"] = created

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

    # --- attributes -------------------------------------------------------
    attrs: dict[str, int] = {}
    for a in root.findall("./attributes/attribute"):
        name = _text(a.find("name")).upper()
        if name in ("ESS", "ESSENCE") or not name:
            continue
        # Chummer <base> is points spent above the metatype minimum.
        lo = _int(a.find("metatypemin"), 1)
        attrs[name] = max(lo + _int(a.find("base")) + _int(a.find("karma")), lo)
    st["attributes"] = attrs or {"BOD": 1, "AGI": 1, "REA": 1, "STR": 1, "CHA": 1, "INT": 1, "LOG": 1, "WIL": 1}

    # --- skills ---------------------------------------------------------
    skills: dict[str, int] = {}
    specs: dict[str, str] = {}
    for s in root.findall("./skills/skills/skill"):
        name = _text(s.find("name"))
        if not name:
            continue
        rating = _int(s.find("base")) + _int(s.find("karma"))
        if rating > 0:
            skills[name] = rating
        sp = _text(s.find("./specializations/spec/name")) or _text(s.find("./specializations/skillspecialization/name"))
        if sp:
            specs[name] = sp
    st["skills"] = skills
    st["skill_specializations"] = specs

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

    # --- qualities -----------------------------------------------------
    q_by_name = _by_name(cat["qualities"])
    q_ids = {r["id"] for r in cat["qualities"]}
    quality_ids: list[str] = []
    quality_extras: dict[str, str] = {}
    for q in root.findall("./qualities/quality"):
        src = _text(q.find("qualitysource")).lower()
        if src and src not in ("selected", "builtin", ""):
            continue  # metatype / life-module grants are re-derived by the engine
        sid = _text(q.find("sourceid")) or _text(q.find("guid"))
        qid = sid if sid in q_ids else q_by_name.get(_text(q.find("name")).lower())
        if not qid:
            nm = _text(q.find("name"))
            if nm:
                warn.append(f"資質「{nm}」はカタログに無いためスキップしました")
            continue
        if qid not in quality_ids:
            quality_ids.append(qid)
        extra = _text(q.find("extra"))
        if extra:
            quality_extras[qid] = extra
    st["quality_ids"] = quality_ids
    st["quality_extras"] = quality_extras

    # --- magic: spells / powers / complex forms / arts ---------------
    spell_r = _Resolver(cat["spells"])
    st["spells"] = [
        {"id": str(uuid.uuid4()), "spell_id": sid, "alchemical": _text(sp.find("alchemical")).lower() == "true"}
        for sp in root.findall("./spells/spell")
        if (sid := spell_r.resolve(sp, warn, "術式"))
    ]
    power_r = _Resolver(cat["powers"])
    powers = []
    for p in root.findall("./powers/power"):
        pid = power_r.resolve(p, warn, "アデプトパワー")
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
        {"id": str(uuid.uuid4()), "form_id": fid, "level": _int(c.find("rating"), 1) or None, "extra": _text(c.find("extra")) or None}
        for c in root.findall("./complexforms/complexform")
        if (fid := cf_r.resolve(c, warn, "複合体"))
    ]

    tr_r = _Resolver(cat["traditions"])
    trad = root.find("tradition")
    if trad is not None and _text(trad.find("name")):
        tid = tr_r.resolve(trad, warn, "伝統")
        if tid:
            st["tradition_id"] = tid

    men = root.find("mentorspirit") or root.find("./mentorspirits/mentorspirit")
    if men is not None:
        mid = _Resolver(cat["mentors"]).resolve(men, warn, "メンター")
        if mid:
            st["mentor_id"] = mid

    # --- initiation / submersion ------------------------------------
    mm_r = _Resolver(cat["metamagics"])
    art_r = _Resolver(cat.get("magic_arts") or [])
    init_grade = sub_grade = 0
    inits: list[dict[str, Any]] = []
    for g in root.findall("./initiationgrades/initiationgrade"):
        gnum = _int(g.find("grade"))
        is_sub = _text(g.find("res")).lower() == "true"
        if is_sub:
            sub_grade = max(sub_grade, gnum)
        else:
            init_grade = max(init_grade, gnum)
    for m in root.findall("./metamagics/metamagic"):
        oid = mm_r.resolve(m, [], "メタマジック") or art_r.resolve(m, [], "術")
        if oid:
            inits.append({"id": str(uuid.uuid4()), "grade": 1, "kind": "metamagic", "option_id": oid})
    st["initiate_grade"] = init_grade
    st["submersion_grade"] = sub_grade
    st["initiations"] = inits

    # --- ware ---------------------------------------------------------
    ware_rows = (cat.get("cyberware") or {}).get("items") or []
    ware_rows = ware_rows + ((cat.get("bioware") or {}).get("items") or [])
    ware_r = _Resolver(ware_rows)

    def load_ware(nodes: list[ET.Element], kind: str) -> list[dict[str, Any]]:
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
            }
            out.append(row)
            kids = w.findall("./children/cyberware") + w.findall("./children/bioware")
            for child in load_ware(kids, kind):
                child["parent_id"] = row["id"]
                child["included"] = True
                out.append(child)
            if w.find("./gears/gear") is not None:
                warn.append(f"{kind}「{_text(w.find('name'))}」内蔵のギアは取り込めませんでした")
        return out

    st["cyberware"] = load_ware(root.findall("./cyberwares/cyberware"), "サイバーウェア")
    st["bioware"] = load_ware(
        root.findall("./biowares/bioware") + root.findall("./cyberwares/bioware"), "バイオウェア"
    )

    # --- armor + mods -------------------------------------------------
    armor_r = _Resolver(cat["armor"])
    amod_r = _Resolver(cat["armor_mods"])
    st_armor: list[dict[str, Any]] = []
    st_amods: list[dict[str, Any]] = []
    for a in root.findall("./armors/armor"):
        aid = armor_r.resolve(a, warn, "防具")
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
            mid = amod_r.resolve(m, warn, "防具改造")
            if mid:
                st_amods.append(
                    {
                        "id": str(uuid.uuid4()),
                        "mod_id": mid,
                        "parent_id": row["id"],
                        "rating": max(1, _int(m.find("rating"), 1)),
                        "included": _text(m.find("included")).lower() == "true",
                    }
                )
    st["armor"] = st_armor
    st["armor_mods"] = st_amods

    # --- weapons + accessories -------------------------------------
    weap_r = _Resolver(cat["weapons"])
    wacc_r = _Resolver(cat["weapon_accessories"])
    st_weap: list[dict[str, Any]] = []
    st_wacc: list[dict[str, Any]] = []
    for w in root.findall("./weapons/weapon"):
        if _text(w.find("cyberware")).lower() == "true":
            continue
        wid = weap_r.resolve(w, warn, "武器")
        if not wid:
            continue
        row = {"id": str(uuid.uuid4()), "weapon_id": wid, "qty": max(1, _int(w.find("qty"), 1))}
        st_weap.append(row)
        for acc in w.findall("./accessories/accessory"):
            acid = wacc_r.resolve(acc, warn, "武器アクセサリ")
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

    # --- gear (nested, routed to the matching catalog bucket) -----
    BUCKETS = ("commlinks", "cyberdecks", "rccs", "sensors", "optics", "programs", "apps", "drones")
    gear_res = {b: _Resolver(cat[b]) for b in ("gear", *BUCKETS)}
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
                warn.append(f"ギア「{name}」はカタログに無いためスキップしました")
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
        route_gear(g, None, None)
    for b, rows in routed.items():
        st[b] = rows

    # --- vehicles + drones + vehicle mods ------------------------
    veh_r = _Resolver(cat["vehicles"])
    drone_r = _Resolver(cat["drones"])
    vmod_r = _Resolver(cat["vehicle_mods"])
    st_veh: list[dict[str, Any]] = list(st.get("drones") or [])
    st_veh_only: list[dict[str, Any]] = []
    st_vmods: list[dict[str, Any]] = []
    for v in root.findall("./vehicles/vehicle"):
        is_drone = veh_r.resolve(v, [], "") is None
        vid = drone_r.resolve(v, [], "") if is_drone else veh_r.resolve(v, warn, "ヴィークル")
        if not vid:
            vid = veh_r.resolve(v, [], "") or drone_r.resolve(v, warn, "ヴィークル")
        if not vid:
            continue
        row = {"id": str(uuid.uuid4()), "gear_id": vid, "rating": 1, "qty": 1}
        (st_veh if is_drone else st_veh_only).append(row)
        for m in v.findall("./mods/mod") + v.findall("./vehiclemods/vehiclemod"):
            mid = vmod_r.resolve(m, warn, "ヴィークル改造")
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
        if v.find("./weapons/weapon") is not None or v.find("./gears/gear") is not None:
            warn.append(f"ヴィークル「{_text(v.find('name'))}」搭載の武器/ギアは取り込めませんでした")
    st["drones"] = st_veh
    st["vehicles"] = st_veh_only
    st["vehicle_mods"] = st_vmods

    # --- lifestyles / contacts / martial arts --------------------
    ls_r = _Resolver(cat["lifestyles"])
    lifestyles = []
    for ls in root.findall("./lifestyles/lifestyle"):
        base = _text(ls.find("baselifestyle")) or _text(ls.find("name"))
        lid = ls_r.by_name.get(base.lower())
        if lid:
            lifestyles.append({"id": str(uuid.uuid4()), "lifestyle_id": lid, "months": max(1, _int(ls.find("months"), 1))})
        elif base:
            warn.append(f"ライフスタイル「{base}」はカタログに無いためスキップしました")
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
        aid = ma_r.resolve(m, warn, "武術")
        if aid:
            techs = [_text(t.find("name")) for t in m.findall("./martialarttechniques/martialarttechnique")]
            techs = [t for t in techs if t]
            marts.append({"id": str(uuid.uuid4()), "art_id": aid, "techniques": techs})
    st["martial_arts"] = marts

    # collapse duplicate warnings, keep order
    st["_warnings"] = list(dict.fromkeys(warn))
    return st, st["_warnings"]
