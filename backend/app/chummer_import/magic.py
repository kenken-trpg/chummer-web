"""Magic and resonance: tradition or stream, mentor, spells, powers, complex
forms, spirits and sprites, initiation and submersion, foci."""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET  # the Element type only — parsing goes through parse_untrusted
from typing import Any

from ..data_loader import CatalogDict
from ..data_loader._xml import _int, _text
from ..notices import Notice, notice, ui
from ._common import _Resolver


def _bonus_names(bonus: list[dict[str, Any]] | None) -> set[str]:
    """Every `<name>` a bonus list names, lower-cased."""
    out: set[str] = set()
    for node in bonus or []:
        raw = (node.get("fields") or {}).get("name")
        for name in raw if isinstance(raw, list) else [raw]:
            if name and str(name).strip():
                out.add(str(name).strip().lower())
    return out


def _mentor_choices_from_improvements(root: ET.Element, mentor: dict[str, Any]) -> list[str]:
    """The mentor's picks, recovered from what they did.

    A save without `<extrachoice1>` keeps the choice only as the improvements
    it made — `AdeptPowerFreeLevels` "Combat Sense", `SpellCategory`
    "Combat" — with `<improvementsource>MentorSpirit`. A choice is taken when
    every name its bonus mentions is among them. Names the mentor's own bonus
    already grants prove nothing, so a choice made only of those is skipped.
    """
    granted = {
        _text(imp.find("improvedname")).lower()
        for imp in root.findall("./improvements/improvement")
        if _text(imp.find("improvementsource")) == "MentorSpirit" and _text(imp.find("improvedname"))
    }
    base = _bonus_names(mentor.get("bonus"))
    picks = []
    for choice in mentor.get("choices") or []:
        names = _bonus_names(choice.get("bonus")) - base
        if names and names <= granted:
            picks.append(str(choice["name"]))
    return picks


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
        # Rating 0 is how Chummer keeps a power that only a mentor's free
        # levels hold up (Eagle's Combat Sense): nothing was bought. The free
        # levels come back from the mentor choice; importing the row as a
        # paid level 1 billed power points the character never spent.
        if _text(p.find("rating")) == "0":
            continue
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

    trad = root.find("tradition")
    if trad is not None and _text(trad.find("traditiontype")) == "RES":
        # Current Chummer saves a technomancer's stream here, as a tradition
        # of type RES with the streams.xml `<id>`; `<stream>` below is the
        # legacy spelling it still reads.
        stream_r = _Resolver(cat["streams"])
        data_id = _text(trad.find("id"))
        stream_id = data_id if data_id in stream_r.ids else stream_r.resolve(trad, warn, ui("engine.kind.stream"))
        if stream_id:
            st["stream_id"] = stream_id
    elif trad is not None and _text(trad.find("name")):
        tid = _Resolver(cat["traditions"]).resolve(trad, warn, ui("engine.kind.tradition"))
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
        if not choices and mid:
            row = next((m for m in mentors if m["id"] == mid), None)
            choices = _mentor_choices_from_improvements(root, row) if row else []
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
