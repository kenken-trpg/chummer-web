"""Chummer5a import ⇄ export is a fixed point on a computed character.

No real ``.chum5`` binaries are vendored (GPL-3.0 data). Instead each scenario
builds a Chummer-shaped ``<character>`` document from names that exist in the
live ``catalog()`` and pins the loop:

    xml -> chum5_to_state -> compute -> state_to_chum5 -> chum5_to_state -> compute

The re-imported/re-computed state must equal the first computed state (row ids
stripped), and ``compute`` must land on the same ``derived`` both times.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.engine import compute
from app.models import CharacterState

# --------------------------------------------------------------------------- #
# Chummer-shaped XML builder                                                   #
# --------------------------------------------------------------------------- #

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


def _ware_nodes(parent: ET.Element, item_tag: str, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        w = _e(parent, item_tag)
        _e(w, "name", row["name"])
        _e(w, "rating", row.get("rating", 1))
        _e(w, "grade", row.get("grade", "Standard"))
        if row.get("side"):
            _e(w, "location", row["side"])
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

    pr = _e(root, "priorities")
    for tag, letter in zip(_PRIO_TAGS, priorities, strict=True):
        _e(pr, tag, letter)
    _e(pr, "prioritytalent", talent)

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

    if tradition:
        _e(_e(root, "tradition"), "name", tradition)
    if mentor:
        _e(_e(root, "mentorspirit"), "name", mentor)

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

    _gear_nodes(_e(root, "gears"), gear or [])

    veh_el = _e(root, "vehicles")
    for row in vehicles or []:
        v = _e(veh_el, "vehicle")
        _e(v, "name", row["name"])
        mods = _e(v, "mods")
        for mrow in row.get("mods") or []:
            m = _e(mods, "mod")
            _e(m, "name", mrow["name"])
            _e(m, "rating", mrow.get("rating", 1))

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
_DROP_KEYS = {"id", "parent_id", "derived", "career_baseline", "_warnings"}


def _scrub(obj: Any) -> Any:
    """Drop generated ids / computed side-cars, sort list rows for a stable compare."""
    if isinstance(obj, dict):
        return {k: _scrub(v) for k, v in sorted(obj.items()) if k not in _DROP_KEYS}
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
                return f"{k}:{v[k]}"
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


# --------------------------------------------------------------------------- #
# Scenario A — street samurai: heavy ware / gear / weapons / vehicles          #
# --------------------------------------------------------------------------- #

_SAMURAI_XML = build_chum5(
    name="Chrome",
    metatype="Human",
    talent="Mundane",
    priorities=("D", "A", "E", "B", "C"),
    attributes={"BOD": 5, "AGI": 6, "REA": 4, "STR": 4, "CHA": 2, "INT": 3, "LOG": 3, "WIL": 3},
    notes="街の顔役に借り 2 件。",
    bio={"age": "29", "sex": "女", "concept": "元企業ウェットワーク"},
    skills={"Automatics": 6, "Pistols": 4, "Sneaking": 3},
    skill_specs={"Automatics": "Assault Rifles"},
    groups={"Stealth": 2},
    knowledge=[
        {"name": "Sperethiel", "type": "Language", "native": True},
        {"name": "Corporate Security", "type": "Professional", "rating": 3},
    ],
    cyberware=[
        {"name": "Wired Reflexes", "rating": 2, "grade": "Alphaware"},
        {
            "name": "Obvious Full Arm",
            "grade": "Standard",
            "side": "Left",
            "children": [{"name": "Cyberarm Gyromount", "grade": "Standard"}],
        },
    ],
    bioware=[{"name": "Muscle Toner", "rating": 2, "grade": "Standard"}],
    armor=[{"name": "Armor Jacket", "mods": [{"name": "Fire Resistance", "rating": 3}]}],
    weapons=[
        {"name": "Ares Predator V", "accessories": [{"name": "Silencer/Suppressor", "mount": "Barrel"}]},
        {"name": "AK-97"},
    ],
    gear=[{"name": "Medkit", "rating": 6}, {"name": "Sony Emperor"}],
    vehicles=[{"name": "Dodge Scoot (Scooter)"}],
    lifestyles=[{"name": "Medium", "months": 3}],
    contacts=[{"name": "Fixer Sam", "role": "Fixer", "connection": 4, "loyalty": 3, "group": True}],
)


def test_samurai_sections_import() -> None:
    s1, ch1, _ = _loop(_SAMURAI_XML)
    assert s1["name"] == "Chrome"
    assert s1["priorities"] == {
        "Heritage": "D",
        "Attributes": "A",
        "Talent": "E",
        "Skills": "B",
        "Resources": "C",
    }
    assert s1["attributes"]["AGI"] == 6
    assert s1["skills"]["Automatics"] == 6
    assert s1["skill_specializations"]["Automatics"] == "Assault Rifles"
    assert s1["skill_groups"]["Stealth"] == 2
    assert s1["native_languages"] == ["Sperethiel"]
    assert s1["knowledge_skills"] == {"Corporate Security": 3}
    # two roots + one nested child
    assert len(s1["cyberware"]) == 3
    assert any(w.get("parent_id") for w in s1["cyberware"])
    assert len(s1["bioware"]) == 1
    assert len(s1["armor"]) == 1 and len(s1["armor_mods"]) == 1
    assert len(s1["weapons"]) == 2 and len(s1["weapon_accessories"]) == 1
    assert s1["weapon_accessories"][0]["mount"] == "Barrel"
    assert s1["commlinks"] and len(s1["gear"]) == 1  # Sony Emperor -> commlinks bucket
    assert len(s1["vehicles"]) == 1
    assert s1["lifestyles"][0]["months"] == 3
    assert s1["contacts"][0]["group"] is True
    assert s1["notes"] == "街の顔役に借り 2 件。"
    assert s1["age"] == "29" and s1["sex"] == "女"


def test_samurai_roundtrip_is_a_fixed_point() -> None:
    # _loop already asserts the fixed point + loop-invariant compute; this pins
    # a couple of derived aggregates so a regression names the section.
    _, ch1, ch2 = _loop(_SAMURAI_XML)
    assert ch1.derived["essence"] == ch2.derived["essence"]
    assert ch1.derived["essence"] < 6
    assert len(ch1.derived["weapons"]) >= 2
    assert ch1.derived["totals"]["AGI"] >= 6


# --------------------------------------------------------------------------- #
# Scenario B — full mage: spells / tradition / mentor / initiation             #
# --------------------------------------------------------------------------- #

_MAGE_XML = build_chum5(
    name="Sable",
    metatype="Elf",
    talent="Magician",
    priorities=("C", "B", "A", "D", "E"),
    attributes={"BOD": 2, "AGI": 3, "REA": 3, "STR": 2, "CHA": 4, "INT": 4, "LOG": 5, "WIL": 5, "MAG": 6},
    skills={"Spellcasting": 6, "Counterspelling": 4, "Summoning": 3},
    skill_specs={"Spellcasting": "Combat"},
    knowledge=[{"name": "Sperethiel", "type": "Language", "native": True}],
    qualities=["Focused Concentration"],
    spells=["Manabolt", "Heal", "Increase Reflexes"],
    tradition="Hermetic",
    mentor="Bear",
    initiation=[
        {"grade": 1, "ordeal": True, "metamagic": "Centering"},
        {"grade": 2, "group": True, "metamagic": "Masking"},
    ],
    lifestyles=[{"name": "Low", "months": 4}],
)


def test_mage_magic_sections_import() -> None:
    s1, ch1, _ = _loop(_MAGE_XML)
    assert s1["talent"] == "Magician"
    assert s1["attributes"]["MAG"] == 6
    assert len(s1["spells"]) == 3
    assert s1["tradition_id"] and s1["mentor_id"]
    assert s1["initiate_grade"] == 2
    assert len(s1["initiations"]) == 2
    assert [row["option_id"] for row in s1["initiations"]] == [
        s1["initiations"][0]["option_id"],
        s1["initiations"][1]["option_id"],
    ]
    assert all(row["option_id"] for row in s1["initiations"])  # both metamagics resolved
    assert s1["initiations"][0]["ordeal"] is True
    assert s1["initiations"][1]["group"] is True
    assert "magic" in ch1.derived["enabled_tabs"] or ch1.derived["initiate_grade"] == 2


def test_mage_roundtrip_is_a_fixed_point() -> None:
    _, ch1, ch2 = _loop(_MAGE_XML)
    assert ch1.derived["initiate_grade"] == ch2.derived["initiate_grade"] == 2
    assert len(ch1.derived["spells"]) == 3
    assert ch1.derived["tradition"] == ch2.derived["tradition"]
