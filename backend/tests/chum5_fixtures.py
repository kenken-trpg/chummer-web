"""Chummer-shaped XML in, and the import ⇄ export loop that must be a fixed
point on it.

Shared by the hand-written scenarios in ``test_chummer_roundtrip.py`` and the
generated ones in ``test_chummer_roundtrip_property.py``. No real ``.chum5``
binaries are vendored (GPL-3.0 data), so every document here is built from
names that exist in the live ``catalog()``.

Not collected by pytest — the filename is deliberately not ``test_*``.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.engine import compute
from app.models import CharacterState

_PRIO_TAGS = (
    "prioritymetatype",
    "priorityattributes",
    "priorityspecial",
    "priorityskills",
    "priorityresources",
)


def _e(parent: ET.Element, tag: str, text: Any = None) -> ET.Element:
    el = ET.SubElement(parent, tag)
    if text is not None:
        el.text = str(text)
    return el


def _flag(parent: ET.Element, tag: str, on: bool) -> None:
    _e(parent, tag, "True" if on else "False")


def _pick_nodes(parent: ET.Element, skills: list[str]) -> None:
    """`<skillpicks>`: the skill chosen for each `<selectskill>` slot, in order."""
    if not skills:
        return
    picks = _e(parent, "skillpicks")
    for index, skill in enumerate(skills):
        pick = _e(picks, "pick")
        _e(pick, "index", index)
        _e(pick, "skill", skill)


def _ware_nodes(parent: ET.Element, item_tag: str, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        w = _e(parent, item_tag)
        _e(w, "name", row["name"])
        _e(w, "rating", row.get("rating", 1))
        _e(w, "grade", row.get("grade", "Standard"))
        if row.get("side"):
            _e(w, "location", row["side"])
        if row.get("extra"):
            _e(w, "extra", row["extra"])
        _pick_nodes(w, row.get("skill_picks") or [])
        kids = row.get("children") or []
        if kids:
            _ware_nodes(_e(w, "children"), item_tag, kids)


def _gear_nodes(parent: ET.Element, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        g = _e(parent, "gear")
        _e(g, "name", row["name"])
        _e(g, "rating", row.get("rating", 1))
        _e(g, "qty", row.get("qty", 1))
        if "included" in row:
            _flag(g, "included", row["included"])
        kids = row.get("children") or []
        if kids:
            _gear_nodes(_e(g, "children"), kids)


def build_chum5(
    *,
    name: str = "RoundTrip",
    metatype: str = "Human",
    metavariant: str | None = None,
    talent: str = "Mundane",
    build_method: str = "Priority",
    created: bool = False,
    priorities: tuple[str, str, str, str, str] = ("E", "B", "E", "C", "A"),
    attributes: dict[str, int] | None = None,
    karma: int = 0,
    nuyen: int = 0,
    notes: str = "",
    bio: dict[str, str] | None = None,
    skills: dict[str, int] | None = None,
    skill_specs: dict[str, str] | None = None,
    groups: dict[str, int] | None = None,
    knowledge: list[dict[str, Any]] | None = None,
    qualities: list[str] | None = None,
    spells: list[str] | None = None,
    powers: list[dict[str, Any]] | None = None,
    complex_forms: list[str] | None = None,
    tradition: str | None = None,
    mentor: str | None = None,
    initiation: list[dict[str, Any]] | None = None,
    cyberware: list[dict[str, Any]] | None = None,
    bioware: list[dict[str, Any]] | None = None,
    armor: list[dict[str, Any]] | None = None,
    weapons: list[dict[str, Any]] | None = None,
    gear: list[dict[str, Any]] | None = None,
    vehicles: list[dict[str, Any]] | None = None,
    lifestyles: list[dict[str, Any]] | None = None,
    contacts: list[dict[str, Any]] | None = None,
    martial_arts: list[dict[str, Any]] | None = None,
    foci: list[dict[str, Any]] | None = None,
    weapon_mounts: list[dict[str, Any]] | None = None,
    custom_drugs: list[dict[str, Any]] | None = None,
    spirits: list[dict[str, Any]] | None = None,
    sprites: list[dict[str, Any]] | None = None,
    enhancements: list[str] | None = None,
    stream: str | None = None,
    mystic_pp: int = 0,
    mentor_choices: list[str] | None = None,
    exotic_skills: list[dict[str, Any]] | None = None,
    quality_picks: dict[str, list[str]] | None = None,
    street_cred: int = 0,
    notoriety: int = 0,
    karma_nuyen: int = 0,
) -> bytes:
    root = ET.Element("character")
    _e(root, "name", "")
    _e(root, "alias", name)
    _e(root, "metatype", metatype)
    _e(root, "metavariant", metavariant or "None")
    _e(root, "buildmethod", build_method)
    _flag(root, "created", created)
    if notes:
        _e(root, "notes", notes)
    for field, value in (bio or {}).items():
        _e(root, "description" if field == "appearance" else field, value)
    if created:
        _e(root, "karma", karma)
        _e(root, "nuyen", nuyen)
    if street_cred:
        _e(root, "streetcred", street_cred)
    if notoriety:
        _e(root, "notoriety", notoriety)
    if karma_nuyen:
        _e(root, "nuyenbp", karma_nuyen)

    # the way Chummer saves them: straight under <character>, "letter,value"
    for tag, letter in zip(_PRIO_TAGS, priorities, strict=True):
        _e(root, tag, f"{letter},{'EDCBA'.index(letter)}")
    _e(root, "prioritytalent", talent)

    attr_el = _e(root, "attributes")
    for attr_name, value in (attributes or {"BOD": 3}).items():
        a = _e(attr_el, "attribute")
        _e(a, "name", attr_name)
        _e(a, "metatypemin", 1)
        _e(a, "base", max(int(value) - 1, 0))
        _e(a, "karma", 0)

    sk = _e(root, "skills")
    active = _e(sk, "skills")
    for sname, rating in (skills or {}).items():
        s = _e(active, "skill")
        _e(s, "name", sname)
        _e(s, "base", rating)
        _e(s, "karma", 0)
        spec = (skill_specs or {}).get(sname)
        if spec:
            _e(_e(_e(s, "specializations"), "spec"), "name", spec)
    for row in exotic_skills or []:
        # An exotic skill is an ordinary <skill> carrying <specific>.
        ex = _e(active, "skill")
        _e(ex, "name", row["name"])
        _e(ex, "specific", row["specific"])
        _e(ex, "base", row.get("rating", 1))
        _e(ex, "karma", 0)
    grp_el = _e(sk, "groups")
    for gname, rating in (groups or {}).items():
        g = _e(grp_el, "group")
        _e(g, "name", gname)
        _e(g, "base", rating)
        _e(g, "karma", 0)
    kno = _e(sk, "knoskills")
    for row in knowledge or []:
        s = _e(kno, "skill")
        _e(s, "name", row["name"])
        _e(s, "type", row.get("type", "Academic"))
        if row.get("native"):
            _e(s, "isnativelanguage", "True")
        else:
            _e(s, "base", row.get("rating", 1))
            _e(s, "karma", 0)

    q_el = _e(root, "qualities")
    for qname in qualities or []:
        q = _e(q_el, "quality")
        _e(q, "name", qname)
        _e(q, "qualitysource", "Selected")
        _pick_nodes(q, (quality_picks or {}).get(qname) or [])

    sp_el = _e(root, "spells")
    for sname in spells or []:
        _e(_e(sp_el, "spell"), "name", sname)
    pw_el = _e(root, "powers")
    for row in powers or []:
        p = _e(pw_el, "power")
        _e(p, "name", row["name"])
        _e(p, "rating", row.get("rating", 1))
    cf_el = _e(root, "complexforms")
    for cname in complex_forms or []:
        _e(_e(cf_el, "complexform"), "name", cname)

    sp_el = _e(root, "spirits")
    # Chummer keeps spirits and sprites in the one list, told apart by <type>.
    for row in spirits or []:
        sp = _e(sp_el, "spirit")
        _e(sp, "name", row["name"])
        _e(sp, "type", "Spirit")
        _e(sp, "force", row.get("force", 1))
        _e(sp, "services", row.get("services", 1))
        _flag(sp, "bound", bool(row.get("bound", True)))
    for row in sprites or []:
        sp = _e(sp_el, "spirit")
        _e(sp, "name", row["name"])
        _e(sp, "type", "Sprite")
        _e(sp, "force", row.get("level", 1))
        _e(sp, "services", row.get("services", 1))
        _flag(sp, "bound", bool(row.get("registered", True)))

    en_el = _e(root, "enhancements")
    for ename in enhancements or []:
        _e(_e(en_el, "enhancement"), "name", ename)

    if stream:
        _e(root, "stream", stream)
    if mystic_pp:
        _e(root, "magsplitadept", mystic_pp)

    if tradition:
        _e(_e(root, "tradition"), "name", tradition)
    if mentor:
        me = _e(root, "mentorspirit")
        _e(me, "name", mentor)
        # As Chummer writes them: at most two, and only the pick's own name.
        for tag, picked in zip(("extrachoice1", "extrachoice2"), mentor_choices or [], strict=False):
            _e(me, tag, picked)

    grades = _e(root, "initiationgrades")
    metamagics = _e(root, "metamagics")
    for row in initiation or []:
        g = _e(grades, "initiationgrade")
        _e(g, "grade", row["grade"])
        _flag(g, "res", row.get("res", False))
        for flag in ("group", "ordeal", "schooling"):
            _flag(g, flag, row.get(flag, False))
        if row.get("metamagic"):
            _e(_e(metamagics, "metamagic"), "name", row["metamagic"])

    _ware_nodes(_e(root, "cyberwares"), "cyberware", cyberware or [])
    _ware_nodes(_e(root, "biowares"), "bioware", bioware or [])

    armors = _e(root, "armors")
    for row in armor or []:
        a = _e(armors, "armor")
        _e(a, "name", row["name"])
        _e(a, "equipped", "True")
        mods = _e(a, "armormods")
        for mrow in row.get("mods") or []:
            m = _e(mods, "armormod")
            _e(m, "name", mrow["name"])
            _e(m, "rating", mrow.get("rating", 1))

    weap_el = _e(root, "weapons")
    for row in weapons or []:
        w = _e(weap_el, "weapon")
        _e(w, "name", row["name"])
        _e(w, "qty", row.get("qty", 1))
        accs = _e(w, "accessories")
        for arow in row.get("accessories") or []:
            ac = _e(accs, "accessory")
            _e(ac, "name", arow["name"])
            _e(ac, "mount", arow.get("mount", ""))

    gear_el = _e(root, "gears")
    _gear_nodes(gear_el, gear or [])

    veh_el = _e(root, "vehicles")
    for row in vehicles or []:
        v = _e(veh_el, "vehicle")
        _e(v, "name", row["name"])
        mods = _e(v, "mods")
        for mrow in row.get("mods") or []:
            m = _e(mods, "mod")
            _e(m, "name", mrow["name"])
            _e(m, "rating", mrow.get("rating", 1))
        mounts = _e(v, "weaponmounts")
        for mrow in row.get("weapon_mounts") or []:
            mount = _e(mounts, "weaponmount")
            _e(mount, "name", mrow["size"])
            _e(mount, "category", "Size")
            opts = _e(mount, "weaponmountoptions")
            for part, category in (
                ("visibility", "Visibility"),
                ("flexibility", "Flexibility"),
                ("control", "Control"),
            ):
                if not mrow.get(part):
                    continue
                opt = _e(opts, "weaponmountoption")
                _e(opt, "name", mrow[part])
                _e(opt, "category", category)
            if mrow.get("weapon"):
                _e(mount, "mountedweaponname", mrow["weapon"])

    foci_el = _e(root, "foci")
    for row in foci or []:
        # A focus is gear with `<bonded>`; `<foci>` only points at it.
        g = _e(gear_el, "gear")
        _e(g, "guid", row["name"])
        _e(g, "name", row["name"])
        _e(g, "category", "Foci")
        _e(g, "rating", row.get("force", 1))
        _flag(g, "bonded", True)
        if row.get("power"):
            _e(g, "extra", row["power"])
        f = _e(foci_el, "focus")
        _e(f, "gearid", row["name"])
        if row.get("power"):
            _e(f, "powerrating", row.get("power_rating", 1))
        if row.get("crafted"):
            _flag(f, "crafted", True)
        if row.get("weapon"):
            _e(f, "weaponname", row["weapon"])

    drugs_el = _e(root, "drugs")
    for row in custom_drugs or []:
        d = _e(drugs_el, "drug")
        _e(d, "name", row["name"])
        _e(d, "grade", row.get("grade", "Standard"))
        _e(d, "quantity", row.get("qty", 1))
        _flag(d, "active", bool(row.get("active")))
        comps = _e(d, "drugcomponents")
        for crow in row["components"]:
            c = _e(comps, "drugcomponent")
            _e(c, "name", crow["name"])
            _e(c, "level", crow.get("level", 0))

    ls_el = _e(root, "lifestyles")
    for row in lifestyles or []:
        ls = _e(ls_el, "lifestyle")
        _e(ls, "baselifestyle", row["name"])
        _e(ls, "months", row.get("months", 1))

    ct_el = _e(root, "contacts")
    for row in contacts or []:
        c = _e(ct_el, "contact")
        _e(c, "name", row.get("name", ""))
        _e(c, "role", row.get("role", ""))
        _e(c, "connection", row.get("connection", 1))
        _e(c, "loyalty", row.get("loyalty", 1))
        _e(c, "type", "Group" if row.get("group") else "Contact")

    ma_el = _e(root, "martialarts")
    for row in martial_arts or []:
        ma = _e(ma_el, "martialart")
        _e(ma, "name", row["name"])
        techs = _e(ma, "martialarttechniques")
        for tname in row.get("techniques") or []:
            _e(_e(techs, "martialarttechnique"), "name", tname)

    return b'<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding="utf-8")


# --------------------------------------------------------------------------- #
# Normalisers + the loop                                                       #
# --------------------------------------------------------------------------- #

# ``id`` / ``parent_id`` are freshly-generated uuids on every import; ``derived``
# and ``career_baseline`` are compute side-cars compared separately via _stable.
#: `weapon_install_id` is a weapon-mount's pointer at a weapon row, generated
#: like `parent_id` and regenerated on every import.
_DROP_KEYS = {"id", "parent_id", "weapon_install_id", "derived", "career_baseline", "_warnings"}


#: A skill-pick key names the row that granted the slot — `ware:<install id>:0`
#: — so the id sits inside the key rather than in a field of its own.
_GENERATED_IN_KEY = re.compile(r"^(ware):[0-9a-fA-F-]{36}:")


def _scrub(obj: Any) -> Any:
    """Drop generated ids / computed side-cars, sort list rows for a stable compare."""
    if isinstance(obj, dict):
        obj = {_GENERATED_IN_KEY.sub(r"\1:*:", k) if isinstance(k, str) else k: v for k, v in obj.items()}
        drop = _DROP_KEYS
        # A weapon focus keeps the weapon row it is bound to in `extra`, so on
        # a focus that field is a generated id rather than text.
        if "force" in obj and "gear_id" in obj:
            drop = drop | {"extra"}
        return {k: _scrub(v) for k, v in sorted(obj.items()) if k not in drop}
    if isinstance(obj, list):
        cleaned = [_scrub(v) for v in obj]
        try:
            return sorted(cleaned, key=lambda v: _sort_key(v))
        except TypeError:
            return cleaned
    return obj


def _sort_key(v: Any) -> str:
    if isinstance(v, dict):
        for k in (
            "ware_id",
            "weapon_id",
            "armor_id",
            "gear_id",
            "spell_id",
            "form_id",
            "mod_id",
            "accessory_id",
            "power_id",
            "art_id",
            "lifestyle_id",
            "name",
            "grade",
        ):
            if k in v:
                # The id alone is not a key: a character can hold the same
                # implant twice — one bought, one bundled with its parent (a
                # Control Rig comes with a Datajack) — and rows that tie sort
                # in input order, which is exactly what differs between two
                # passes. The rest of the row breaks the tie.
                return f"{k}:{v[k]}|{repr(sorted(v.items()))}"
        return repr(sorted(v.items()))
    return repr(v)


def _stable(derived: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "errors",
        "totals",
        "essence",
        "limits",
        "condition_monitor",
        "initiative",
        "armor",
        "nuyen",
        "karma",
        "enabled_tabs",
        "movement",
        "initiate_grade",
        "submersion_grade",
    )
    out: dict[str, Any] = {k: derived.get(k) for k in keys}
    for bucket in (
        "cyberware",
        "bioware",
        "weapons",
        "armor_items",
        "gear",
        "drones",
        "vehicles",
        "spells",
        "adept_powers",
        "complex_forms",
        "contacts",
        "lifestyles",
        "martial_arts",
        "foci",
        "qi_foci",
        "weapon_mounts",
        "custom_drugs",
    ):
        out[f"len:{bucket}"] = len(derived.get(bucket) or [])
    return out


def _compute(state: dict[str, Any]) -> CharacterState:
    return compute(CharacterState.model_validate({k: v for k, v in state.items() if k != "_warnings"}))


def _loop(xml: bytes) -> tuple[dict[str, Any], CharacterState, CharacterState]:
    s1, _ = chum5_to_state(xml)
    ch1 = _compute(s1)
    xml2 = state_to_chum5(ch1)
    assert xml2 == state_to_chum5(ch1), "export is not deterministic"
    s2, _ = chum5_to_state(xml2)
    ch2 = _compute(s2)
    assert _scrub(ch2.model_dump()) == _scrub(ch1.model_dump()), "import/export is not a fixed point"
    assert _stable(ch2.derived) == _stable(ch1.derived), "compute is not loop-invariant"
    return s1, ch1, ch2
