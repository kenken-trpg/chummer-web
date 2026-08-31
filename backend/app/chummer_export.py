"""Export a CharacterState to a Chummer5a-style ``.chum5`` (plain XML).

Not a byte-perfect Chummer save — Chummer recomputes most derived data — but a
structurally compatible ``<character>`` document that Chummer can open and that
round-trips through :func:`app.chummer_import.chum5_to_state`.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any
from xml.dom import minidom

from .data_loader import catalog
from .engine import find_metatype
from .models import CharacterState

_ATTR_ORDER = ("BOD", "AGI", "REA", "STR", "CHA", "INT", "LOG", "WIL", "EDG", "MAG", "RES", "DEP")
_BUILD_METHOD_OUT = {"Priority": "Priority", "SumToTen": "SumtoTen", "Karma": "Karma"}


def _sub(parent: ET.Element, tag: str, text: Any = None) -> ET.Element:
    el = ET.SubElement(parent, tag)
    if text is not None:
        el.text = str(text)
    return el


def _id_name(rows: list[dict[str, Any]]) -> dict[str, str]:
    return {r["id"]: r.get("name") or "" for r in rows if r.get("id")}


def state_to_chum5(state: CharacterState) -> bytes:
    cat = catalog()
    meta = find_metatype(state.metatype, state.metavariant) or {"attributes": {}}
    m_attr = meta.get("attributes") or {}

    names = {
        "quality": _id_name(cat["qualities"]),
        "spell": _id_name(cat["spells"]),
        "power": _id_name(cat["powers"]),
        "complexform": _id_name(cat["complex_forms"]),
        "martialart": _id_name(cat["martial_arts"]),
        "ware": _id_name((cat.get("cyberware") or {}).get("items") or [])
        | _id_name((cat.get("bioware") or {}).get("items") or []),
        "armor": _id_name(cat["armor"]),
        "armormod": _id_name(cat["armor_mods"]),
        "weapon": _id_name(cat["weapons"]),
        "wacc": _id_name(cat["weapon_accessories"]),
        "gear": _id_name(cat["gear"])
        | {k: v for b in ("commlinks", "cyberdecks", "rccs", "sensors", "optics", "programs", "apps", "drones", "vehicles") for k, v in _id_name(cat[b]).items()},
        "vmod": _id_name(cat["vehicle_mods"]),
        "lifestyle": _id_name(cat["lifestyles"]),
        "tradition": _id_name(cat["traditions"]),
        "mentor": _id_name(cat["mentors"]),
        "metamagic": _id_name(cat["metamagics"]),
        "art": _id_name(cat.get("magic_arts") or []),
    }

    root = ET.Element("character")
    _sub(root, "appversion", "Chummer Web")
    _sub(root, "name", "")
    _sub(root, "alias", state.name)
    _sub(root, "metatype", state.metatype)
    _sub(root, "metavariant", state.metavariant or "")
    _sub(root, "buildmethod", _BUILD_METHOD_OUT.get(state.build_method, "Priority"))
    _sub(root, "created", "True" if state.career else "False")
    if state.notes:
        _sub(root, "notes", state.notes)
    for field, tag in (
        ("age", "age"), ("sex", "sex"), ("height", "height"), ("weight", "weight"),
        ("eyes", "eyes"), ("hair", "hair"), ("skin", "skin"),
        ("appearance", "description"), ("background", "background"), ("concept", "concept"),
    ):
        value = getattr(state, field, "")
        if value:
            _sub(root, tag, value)
    _sub(root, "karma", state.karma_earned if state.career else 0)
    _sub(root, "nuyen", state.nuyen_earned if state.career else 0)

    pr = _sub(root, "priorities")
    _sub(pr, "prioritymetatype", state.priorities.Heritage)
    _sub(pr, "priorityattributes", state.priorities.Attributes)
    _sub(pr, "priorityspecial", state.priorities.Talent)
    _sub(pr, "priorityskills", state.priorities.Skills)
    _sub(pr, "priorityresources", state.priorities.Resources)
    _sub(pr, "prioritytalent", state.talent)

    attrs = _sub(root, "attributes")
    for key in _ATTR_ORDER:
        spec = m_attr.get(key) or {}
        lo = int(spec.get("min", 0 if key in ("MAG", "RES", "DEP") else 1))
        val = int(state.attributes.get(key, lo))
        a = _sub(attrs, "attribute")
        _sub(a, "name", key)
        _sub(a, "metatypemin", lo)
        _sub(a, "metatypemax", int(spec.get("max", 6)))
        _sub(a, "metatypeaugmax", int(spec.get("aug", spec.get("max", 6))))
        _sub(a, "base", max(val - lo, 0))
        _sub(a, "karma", 0)
    ess = _sub(attrs, "attribute")
    _sub(ess, "name", "ESS")
    _sub(ess, "base", 6)
    _sub(ess, "karma", 0)

    sk = _sub(root, "skills")
    active = _sub(sk, "skills")
    for name, rating in sorted(state.skills.items()):
        s = _sub(active, "skill")
        _sub(s, "name", name)
        _sub(s, "base", rating)
        _sub(s, "karma", 0)
        spn = state.skill_specializations.get(name)
        if spn:
            _sub(_sub(_sub(s, "specializations"), "spec"), "name", spn)
    grps = _sub(sk, "groups")
    for name, rating in sorted(state.skill_groups.items()):
        g = _sub(grps, "group")
        _sub(g, "name", name)
        _sub(g, "base", rating)
        _sub(g, "karma", 0)
    kno = _sub(sk, "knoskills")
    for name in state.native_languages:
        s = _sub(kno, "skill")
        _sub(s, "name", name)
        _sub(s, "type", "Language")
        _sub(s, "isnativelanguage", "True")
    for name, rating in sorted(state.knowledge_skills.items()):
        s = _sub(kno, "skill")
        _sub(s, "name", name)
        _sub(s, "type", state.knowledge_categories.get(name, "Academic"))
        _sub(s, "base", rating)
        _sub(s, "karma", 0)

    quals = _sub(root, "qualities")
    for qid in state.quality_ids:
        q = _sub(quals, "quality")
        _sub(q, "sourceid", qid)
        _sub(q, "name", names["quality"].get(qid, ""))
        _sub(q, "extra", state.quality_extras.get(qid, ""))
        _sub(q, "qualitysource", "Selected")

    def _named_list(container: str, item: str, rows: list, id_key: str, bag: str, extra: dict | None = None):
        parent = _sub(root, container)
        for row in rows:
            iid = getattr(row, id_key)
            el = _sub(parent, item)
            _sub(el, "sourceid", iid)
            _sub(el, "name", names[bag].get(iid, ""))
            for k, fn in (extra or {}).items():
                _sub(el, k, fn(row))
        return parent

    _named_list("spells", "spell", state.spells, "spell_id", "spell")
    _named_list("powers", "power", state.adept_powers, "power_id", "power",
                {"rating": lambda r: r.rating, "extra": lambda r: r.extra or ""})
    _named_list("complexforms", "complexform", state.complex_forms, "form_id", "complexform",
                {"rating": lambda r: r.level or 1})

    marts = _sub(root, "martialarts")
    for row in state.martial_arts:
        el = _sub(marts, "martialart")
        _sub(el, "sourceid", row.art_id)
        _sub(el, "name", names["martialart"].get(row.art_id, ""))
        techs = _sub(el, "martialarttechniques")
        for tn in row.techniques:
            _sub(_sub(techs, "martialarttechnique"), "name", tn)

    def _ware(container: str, rows: list[Any]) -> None:
        top = _sub(root, container)
        by_parent: dict[str | None, list[Any]] = {}
        for r in rows:
            by_parent.setdefault(r.parent_id, []).append(r)

        def emit(parent_el: ET.Element, rowset: list[Any]) -> None:
            for r in rowset:
                w = _sub(parent_el, "cyberware" if container == "cyberwares" else "bioware")
                _sub(w, "sourceid", r.ware_id)
                _sub(w, "name", names["ware"].get(r.ware_id, ""))
                _sub(w, "grade", r.grade)
                _sub(w, "rating", r.rating)
                if r.side:
                    _sub(w, "location", r.side)
                kids = by_parent.get(r.id)
                if kids:
                    emit(_sub(w, "children"), kids)

        emit(top, by_parent.get(None, []))

    _ware("cyberwares", state.cyberware)
    _ware("biowares", state.bioware)

    armors = _sub(root, "armors")
    amods_by_parent: dict[str | None, list[Any]] = {}
    for mrow in state.armor_mods:
        amods_by_parent.setdefault(mrow.parent_id, []).append(mrow)
    for a in state.armor:
        el = _sub(armors, "armor")
        _sub(el, "sourceid", a.armor_id)
        _sub(el, "name", names["armor"].get(a.armor_id, ""))
        _sub(el, "equipped", "True" if a.equipped else "False")
        mods = _sub(el, "armormods")
        for mrow in amods_by_parent.get(a.id, []):
            mm = _sub(mods, "armormod")
            _sub(mm, "sourceid", mrow.mod_id)
            _sub(mm, "name", names["armormod"].get(mrow.mod_id, ""))
            _sub(mm, "rating", mrow.rating)

    weapons = _sub(root, "weapons")
    wacc_by_parent: dict[str | None, list[Any]] = {}
    for arow in state.weapon_accessories:
        wacc_by_parent.setdefault(arow.parent_id, []).append(arow)
    for w in state.weapons:
        el = _sub(weapons, "weapon")
        _sub(el, "sourceid", w.weapon_id)
        _sub(el, "name", names["weapon"].get(w.weapon_id, ""))
        _sub(el, "qty", w.qty)
        accs = _sub(el, "accessories")
        for arow in wacc_by_parent.get(w.id, []):
            ac = _sub(accs, "accessory")
            _sub(ac, "sourceid", arow.accessory_id)
            _sub(ac, "name", names["wacc"].get(arow.accessory_id, ""))
            _sub(ac, "mount", arow.mount)

    gears = _sub(root, "gears")
    gear_rows = [
        *state.gear, *state.commlinks, *state.cyberdecks, *state.rccs,
        *state.sensors, *state.optics, *state.programs, *state.apps,
    ]
    by_parent_g: dict[str | None, list[Any]] = {}
    for g in gear_rows:
        by_parent_g.setdefault(getattr(g, "parent_id", None), []).append(g)

    def emit_gear(parent_el: ET.Element, rows: list[Any]) -> None:
        for g in rows:
            gid = getattr(g, "gear_id")
            el = _sub(parent_el, "gear")
            _sub(el, "sourceid", gid)
            _sub(el, "name", names["gear"].get(gid, ""))
            _sub(el, "rating", getattr(g, "rating", 1))
            _sub(el, "qty", getattr(g, "qty", 1))
            kids = by_parent_g.get(g.id)
            if kids:
                emit_gear(_sub(el, "children"), kids)

    emit_gear(gears, by_parent_g.get(None, []))

    vehs = _sub(root, "vehicles")
    vmod_by_parent: dict[str | None, list[Any]] = {}
    for mrow in state.vehicle_mods:
        vmod_by_parent.setdefault(mrow.parent_id, []).append(mrow)
    for v in [*state.vehicles, *state.drones]:
        el = _sub(vehs, "vehicle")
        _sub(el, "sourceid", v.gear_id)
        _sub(el, "name", names["gear"].get(v.gear_id, ""))
        mods = _sub(el, "mods")
        for mrow in vmod_by_parent.get(v.id, []):
            mm = _sub(mods, "mod")
            _sub(mm, "sourceid", mrow.mod_id)
            _sub(mm, "name", names["vmod"].get(mrow.mod_id, ""))
            _sub(mm, "rating", mrow.rating)

    ls = _sub(root, "lifestyles")
    for lrow in state.lifestyles:
        base = names["lifestyle"].get(lrow.lifestyle_id, "")
        el = _sub(ls, "lifestyle")
        _sub(el, "baselifestyle", base)
        _sub(el, "name", base)
        _sub(el, "months", lrow.months)

    cts = _sub(root, "contacts")
    for crow in state.contacts:
        el = _sub(cts, "contact")
        _sub(el, "name", crow.name)
        _sub(el, "role", crow.role or "")
        _sub(el, "connection", crow.connection)
        _sub(el, "loyalty", crow.loyalty)
        _sub(el, "type", "Group" if crow.group else "Contact")

    if state.tradition_id:
        tr = _sub(root, "tradition")
        _sub(tr, "guid", state.tradition_id)
        _sub(tr, "name", names["tradition"].get(state.tradition_id, ""))
    if state.mentor_id:
        me = _sub(root, "mentorspirit")
        _sub(me, "guid", state.mentor_id)
        _sub(me, "name", names["mentor"].get(state.mentor_id, ""))

    grades = _sub(root, "initiationgrades")
    init_by_grade = {int(c.grade): c for c in state.initiations}
    sub_by_grade = {int(c.grade): c for c in state.submersions}

    def _emit_grade(i: int, res: bool, choice: object) -> None:
        g = _sub(grades, "initiationgrade")
        _sub(g, "grade", i)
        _sub(g, "res", "True" if res else "False")
        _sub(g, "group", "True" if getattr(choice, "group", False) else "False")
        _sub(g, "ordeal", "True" if getattr(choice, "ordeal", False) else "False")
        _sub(g, "schooling", "True" if getattr(choice, "schooling", False) else "False")

    for i in range(1, state.initiate_grade + 1):
        _emit_grade(i, False, init_by_grade.get(i))
    for i in range(1, state.submersion_grade + 1):
        _emit_grade(i, True, sub_by_grade.get(i))
    mms = _sub(root, "metamagics")
    for ic in state.initiations:
        el = _sub(mms, "metamagic")
        _sub(el, "sourceid", ic.option_id)
        _sub(el, "name", names["metamagic"].get(ic.option_id) or names["art"].get(ic.option_id, ""))

    xml = ET.tostring(root, encoding="utf-8")
    return minidom.parseString(xml).toprettyxml(indent="  ", encoding="utf-8")
