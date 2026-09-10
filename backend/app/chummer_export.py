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


#: `_id_name` maps per catalog bucket, built once and read by most sections.
_Names = dict[str, dict[str, str]]
#: The little that is neither the state nor a name map: the metatype's
#: attribute minimums, which only the attribute section needs.
_Ctx = dict[str, Any]


def _export_identity(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write name, metatype, build method, the bio fields, portrait and career totals."""
    _sub(root, "appversion", "Chummer Web")
    _sub(root, "name", "")
    _sub(root, "alias", state.name)
    _sub(root, "metatype", state.metatype)
    _sub(root, "metavariant", state.metavariant or "")
    _sub(root, "buildmethod", _BUILD_METHOD_OUT.get(state.build_method, "Priority"))
    # Chummer keeps the enabled books in the settings *file*, not in the
    # character, so all a .chum5 can carry is which settings the character was
    # built under. The book list is restored on import by matching this name
    # against the shipped presets; a name from elsewhere comes back
    # unrestricted. Written only when set, so an untouched character exports
    # byte-identically to before.
    if state.settings.name:
        _sub(root, "settings", state.settings.name)
    _sub(root, "created", "True" if state.career else "False")
    if state.notes:
        _sub(root, "notes", state.notes)
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
        value = getattr(state, field, "")
        if value:
            _sub(root, tag, value)
    if state.portrait:
        b64 = state.portrait.split(",", 1)[-1] if state.portrait.startswith("data:") else state.portrait
        _sub(root, "mainmugshotindex", "0")
        _sub(_sub(root, "mugshots"), "mugshot", b64)
    _sub(root, "karma", state.karma_earned if state.career else 0)
    _sub(root, "nuyen", state.nuyen_earned if state.career else 0)
    # Reputation, and the nuyen bought with karma at chargen — Chummer keeps
    # the latter in `<nuyenbp>`, which is build points in old money.
    _sub(root, "streetcred", state.street_cred)
    _sub(root, "notoriety", state.notoriety_bonus)
    _sub(root, "nuyenbp", state.karma_nuyen)


def _export_priorities(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write the five priority letters and the talent."""
    pr = _sub(root, "priorities")
    _sub(pr, "prioritymetatype", state.priorities.Heritage)
    _sub(pr, "priorityattributes", state.priorities.Attributes)
    _sub(pr, "priorityspecial", state.priorities.Talent)
    _sub(pr, "priorityskills", state.priorities.Skills)
    _sub(pr, "priorityresources", state.priorities.Resources)
    _sub(pr, "prioritytalent", state.talent)


def _export_attributes(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write each attribute as Chummer's base/karma pair, relative to the metatype minimum."""
    m_attr = ctx["meta_attrs"]
    attrs = _sub(root, "attributes")
    for key in _ATTR_ORDER:
        spec = m_attr.get(key) or {}
        lo = int(spec.get("min", 0 if key in ("MAG", "RES", "DEP") else 1))
        val = int(state.attributes.get(key, lo))
        attr_el = _sub(attrs, "attribute")
        _sub(attr_el, "name", key)
        _sub(attr_el, "metatypemin", lo)
        _sub(attr_el, "metatypemax", int(spec.get("max", 6)))
        _sub(attr_el, "metatypeaugmax", int(spec.get("aug", spec.get("max", 6))))
        _sub(attr_el, "base", max(val - lo, 0))
        _sub(attr_el, "karma", 0)
    ess = _sub(attrs, "attribute")
    _sub(ess, "name", "ESS")
    _sub(ess, "base", 6)
    _sub(ess, "karma", 0)
    if state.mystic_pp:
        # A Mystic Adept's MAG is split between spells and power points, and
        # the adept half is what this app calls `mystic_pp`.
        _sub(root, "magsplitadept", state.mystic_pp)
        _sub(root, "magsplitmagician", max(0, int(state.attributes.get("MAG", 0)) - int(state.mystic_pp)))


def _export_skills(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write active skills, groups, native languages and knowledge."""
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
    for exotic in state.exotic_skills:
        # An exotic skill is one skill per weapon, which Chummer writes as an
        # ordinary skill carrying `<specific>`.
        s = _sub(active, "skill")
        _sub(s, "name", exotic.skill_name)
        _sub(s, "specific", exotic.extra)
        _sub(s, "base", exotic.rating)
        _sub(s, "karma", 0)
    grps = _sub(sk, "groups")
    for name, rating in sorted(state.skill_groups.items()):
        grp_el = _sub(grps, "group")
        _sub(grp_el, "name", name)
        _sub(grp_el, "base", rating)
        _sub(grp_el, "karma", 0)
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


def _export_qualities(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write qualities, spells, adept powers and complex forms."""
    quals = _sub(root, "qualities")
    for qid in state.quality_ids:
        q = _sub(quals, "quality")
        _sub(q, "sourceid", qid)
        _sub(q, "name", names["quality"].get(qid, ""))
        _sub(q, "extra", state.quality_extras.get(qid, ""))
        _sub(q, "qualitysource", "Selected")
        # A quality with a `<selectskill>` bonus carries the skill picked for
        # it. Unlike the implant picks in `_export_ware`, these are keyed by
        # the quality's catalog id, which survives an import unchanged.
        prefix = f"quality:{qid}:"
        picks = sorted(
            (key[len(prefix) :], value) for key, value in state.skill_picks.items() if key.startswith(prefix)
        )
        if picks:
            picks_el = _sub(q, "skillpicks")
            for index, skill in picks:
                pick = _sub(picks_el, "pick")
                _sub(pick, "index", index)
                _sub(pick, "skill", skill)

    def _named_list(
        container: str,
        item: str,
        rows: list[Any],
        id_key: str,
        bag: str,
        extra: dict[str, Any] | None = None,
    ) -> ET.Element:
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
    _named_list(
        "powers",
        "power",
        state.adept_powers,
        "power_id",
        "power",
        {"rating": lambda r: r.rating, "extra": lambda r: r.extra or ""},
    )
    _named_list(
        "complexforms", "complexform", state.complex_forms, "form_id", "complexform", {"rating": lambda r: r.level or 1}
    )


def _export_martial_arts(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write martial arts and their techniques."""
    marts = _sub(root, "martialarts")
    for row in state.martial_arts:
        el = _sub(marts, "martialart")
        _sub(el, "sourceid", row.art_id)
        _sub(el, "name", names["martialart"].get(row.art_id, ""))
        techs = _sub(el, "martialarttechniques")
        for tn in row.techniques:
            _sub(_sub(techs, "martialarttechnique"), "name", tn)


def _export_ware(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write cyber- and bioware, re-nested by parent.

    An implant with a `<selectskill>` or `<hardwires>` bonus also carries the
    skill that was picked for it. This app keys those picks by the *install*
    row, whose id is regenerated on every import, so the pick travels on the
    implant itself rather than in a map of ids.
    """

    def _picks_of(inst_id: str) -> list[tuple[str, str]]:
        prefix = f"ware:{inst_id}:"
        return sorted((key[len(prefix) :], value) for key, value in state.skill_picks.items() if key.startswith(prefix))

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
                if r.extra:
                    _sub(w, "extra", r.extra)
                if getattr(r, "included", False):
                    _sub(w, "included", "True")
                picks = _picks_of(r.id)
                if picks:
                    picks_el = _sub(w, "skillpicks")
                    for index, skill in picks:
                        pick = _sub(picks_el, "pick")
                        _sub(pick, "index", index)
                        _sub(pick, "skill", skill)
                kids = by_parent.get(r.id)
                if kids:
                    emit(_sub(w, "children"), kids)

        emit(top, by_parent.get(None, []))

    _ware("cyberwares", state.cyberware)
    _ware("biowares", state.bioware)


def _export_armor(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write armor and its mods."""
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
            _sub(mm, "included", "True" if mrow.included else "False")


def _export_weapons(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write weapons and their accessories."""
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
            _sub(ac, "included", "True" if arow.included else "False")


def _export_gear(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write gear from every bucket, flattened back into one <gears>."""
    gears = _sub(root, "gears")
    gear_rows = [
        *state.gear,
        *state.commlinks,
        *state.cyberdecks,
        *state.rccs,
        *state.sensors,
        *state.optics,
        *state.programs,
        *state.apps,
    ]
    by_parent_g: dict[str | None, list[Any]] = {}
    for g in gear_rows:
        by_parent_g.setdefault(getattr(g, "parent_id", None), []).append(g)

    def emit_gear(parent_el: ET.Element, rows: list[Any]) -> None:
        for g in rows:
            gid = g.gear_id
            el = _sub(parent_el, "gear")
            _sub(el, "sourceid", gid)
            _sub(el, "name", names["gear"].get(gid, ""))
            _sub(el, "rating", getattr(g, "rating", 1))
            _sub(el, "qty", getattr(g, "qty", 1))
            if getattr(g, "parent_id", None):
                _sub(el, "included", "True" if getattr(g, "included", False) else "False")
            kids = by_parent_g.get(g.id)
            if kids:
                emit_gear(_sub(el, "children"), kids)

    emit_gear(gears, by_parent_g.get(None, []))
    _emit_focus_gear(gears, state, names)


def _emit_focus_gear(gears: ET.Element, state: CharacterState, names: _Names) -> None:
    """A bonded focus is gear: Chummer keeps it in `<gears>` with `<bonded>`,
    and `<foci>` only holds a pointer to it.

    The gear's `<guid>` is the focus row's own id, which is what `_export_foci`
    writes as the `<gearid>` on the other side of that pointer.
    """
    for frow in state.foci:
        el = _sub(gears, "gear")
        _sub(el, "guid", frow.id)
        _sub(el, "sourceid", frow.gear_id)
        _sub(el, "name", names["focus"].get(frow.gear_id, ""))
        _sub(el, "category", "Foci")
        _sub(el, "rating", frow.force)
        _sub(el, "qty", 1)
        _sub(el, "bonded", "True")
    for qrow in state.qi_foci:
        el = _sub(gears, "gear")
        _sub(el, "guid", qrow.id)
        _sub(el, "sourceid", names["qifocus"].get("id", ""))
        _sub(el, "name", names["qifocus"].get("name", ""))
        _sub(el, "category", "Foci")
        _sub(el, "rating", qrow.rating)
        _sub(el, "qty", 1)
        _sub(el, "bonded", "True")
        # Which power the Qi focus carries — Chummer's own `<extra>` on the
        # gear, the same field its `<selectpower>` bonus fills in.
        _sub(el, "extra", names["power"].get(qrow.power_id, ""))


def _export_foci(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write `<foci>`, the bonded-focus pointers into `<gears>`.

    Chummer stores nothing here but the link. What this app knows on top —
    whether the focus was crafted rather than bought, the artificing test, the
    weapon a weapon focus is bound to, the rating a Qi focus grants its power —
    rides along as extra children, which Chummer's loader ignores.
    """
    foci = _sub(root, "foci")
    weapon_names = {w.id: names["weapon"].get(w.weapon_id, "") for w in state.weapons}
    for frow in state.foci:
        el = _sub(foci, "focus")
        _sub(el, "guid", frow.id)
        _sub(el, "gearid", frow.id)
        _sub(el, "crafted", "True" if frow.crafted else "False")
        _sub(el, "formulabought", "True" if frow.formula_bought else "False")
        if frow.hits is not None:
            _sub(el, "hits", frow.hits)
        if frow.opposed_hits is not None:
            _sub(el, "opposedhits", frow.opposed_hits)
        # A weapon focus points at a weapon *row*, whose id is regenerated on
        # every import — so the link travels as the weapon's name instead.
        if frow.extra:
            _sub(el, "weaponname", weapon_names.get(frow.extra, ""))
    for qrow in state.qi_foci:
        el = _sub(foci, "focus")
        _sub(el, "guid", qrow.id)
        _sub(el, "gearid", qrow.id)
        _sub(el, "powerrating", qrow.power_rating)
        if qrow.extra:
            _sub(el, "powerextra", qrow.extra)


def _export_vehicles(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write vehicles, drones and vehicle mods."""
    vehs = _sub(root, "vehicles")
    vmod_by_parent: dict[str | None, list[Any]] = {}
    for vrow in state.vehicle_mods:
        vmod_by_parent.setdefault(vrow.parent_id, []).append(vrow)
    for v in [*state.vehicles, *state.drones]:
        el = _sub(vehs, "vehicle")
        _sub(el, "sourceid", v.gear_id)
        _sub(el, "name", names["gear"].get(v.gear_id, ""))
        mods = _sub(el, "mods")
        for vrow in vmod_by_parent.get(v.id, []):
            mm = _sub(mods, "mod")
            _sub(mm, "sourceid", vrow.mod_id)
            _sub(mm, "name", names["vmod"].get(vrow.mod_id, ""))
            _sub(mm, "rating", vrow.rating)
            _sub(mm, "included", "True" if vrow.included else "False")
        _emit_weapon_mounts(el, state, names, v.id)


def _emit_weapon_mounts(vehicle_el: ET.Element, state: CharacterState, names: _Names, vehicle_id: str) -> None:
    """Write one vehicle's weapon mounts.

    A mount is its size plus three options (visibility, flexibility, control),
    which is how Chummer stores it: the size on the mount itself, the rest as
    `<weaponmountoption>` rows.

    The gun bolted to it is not written into the mount, though Chummer would:
    the weapon is a row in the character's own `<weapons>` here, and writing it
    in both places would import it twice. The link travels as
    `<mountedweaponname>` instead, which Chummer ignores.
    """
    rows = [row for row in state.weapon_mounts if row.parent_id == vehicle_id]
    if not rows:
        return
    weapon_names = {w.id: names["weapon"].get(w.weapon_id, "") for w in state.weapons}
    mounts = _sub(vehicle_el, "weaponmounts")
    for row in rows:
        el = _sub(mounts, "weaponmount")
        _sub(el, "guid", row.id)
        _sub(el, "sourceid", row.size_id)
        _sub(el, "name", names["wmount"].get(row.size_id, ""))
        _sub(el, "category", "Size")
        _sub(el, "included", "True" if row.included else "False")
        _sub(el, "weaponmountcategories", row.allowedweapons)
        options = _sub(el, "weaponmountoptions")
        for part_id, category in (
            (row.visibility_id, "Visibility"),
            (row.flexibility_id, "Flexibility"),
            (row.control_id, "Control"),
        ):
            if not part_id:
                continue
            opt = _sub(options, "weaponmountoption")
            _sub(opt, "sourceid", part_id)
            _sub(opt, "name", names["wmount"].get(part_id, ""))
            _sub(opt, "category", category)
        if row.weapon_install_id:
            _sub(el, "mountedweaponname", weapon_names.get(row.weapon_install_id, ""))


def _export_lifestyles(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write lifestyles."""
    ls = _sub(root, "lifestyles")
    for lrow in state.lifestyles:
        base = names["lifestyle"].get(lrow.lifestyle_id, "")
        el = _sub(ls, "lifestyle")
        _sub(el, "baselifestyle", base)
        _sub(el, "name", base)
        _sub(el, "months", lrow.months)


def _export_custom_drugs(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write mixed drugs as Chummer's `<drugs><drug>` with their components.

    Chummer rebuilds a custom drug from the components it was mixed from, so
    the component ids and their levels are the whole payload — every total
    (cost, availability, addiction, onset) is recomputed on load, here and
    there alike.

    `<active>` is this app's own: Chummer has no "currently dosed" flag, and
    it ignores elements it does not know.
    """
    drugs = _sub(root, "drugs")
    for drow in state.custom_drugs:
        el = _sub(drugs, "drug")
        _sub(el, "guid", drow.id)
        _sub(el, "name", drow.name)
        _sub(el, "category", "Custom Drugs")
        _sub(el, "quantity", drow.qty)
        _sub(el, "grade", drow.grade)
        _sub(el, "active", "True" if drow.active else "False")
        parts = _sub(el, "drugcomponents")
        for part in drow.parts:
            comp = _sub(parts, "drugcomponent")
            _sub(comp, "sourceid", part.component_id)
            _sub(comp, "name", names["drugcomponent"].get(part.component_id, ""))
            _sub(comp, "level", part.level)


def _export_contacts(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write contacts, plus the tradition and mentor a magician carries."""
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
    if state.stream_id:
        # A technomancer's stream is a tradition-shaped thing of its own;
        # Chummer reads it from `<stream>`.
        _sub(root, "stream", names["stream"].get(state.stream_id, ""))
    if state.mentor_id:
        me = _sub(root, "mentorspirit")
        _sub(me, "guid", state.mentor_id)
        _sub(me, "name", names["mentor"].get(state.mentor_id, ""))
        # Chummer holds at most two mentor picks, in two fixed fields. This app
        # keeps a list plus a map of what each pick resolved to, so the pair of
        # lists below is what actually round-trips; the two fields mirror the
        # first two picks so Chummer has something to show.
        for index, tag in enumerate(("extrachoice1", "extrachoice2")):
            _sub(me, tag, state.mentor_choices[index] if index < len(state.mentor_choices) else "")
        choices = _sub(me, "choices")
        for picked in state.mentor_choices:
            _sub(choices, "choice", picked)
        extras = _sub(me, "extras")
        for key, value in sorted(state.mentor_extras.items()):
            row = _sub(extras, "extra")
            _sub(row, "key", key)
            _sub(row, "value", value)


def _export_spirits(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write bound spirits and registered sprites into one `<spirits>`.

    Chummer keeps both in the same list and tells them apart by `<type>`; a
    sprite's Level is its `<force>`. The hits of the summoning/compiling test
    are this app's own and ride along as extra children.
    """
    spirits = _sub(root, "spirits")
    for srow in state.spirits:
        el = _sub(spirits, "spirit")
        _sub(el, "guid", srow.id)
        _sub(el, "name", names["spirit"].get(srow.spirit_id, ""))
        _sub(el, "type", "Spirit")
        _sub(el, "force", srow.force)
        _sub(el, "services", srow.services)
        _sub(el, "bound", "True" if srow.bound else "False")
        _sub(el, "fettered", "False")
        if srow.hits is not None:
            _sub(el, "hits", srow.hits)
        if srow.opposed_hits is not None:
            _sub(el, "opposedhits", srow.opposed_hits)
    for prow in state.sprites:
        el = _sub(spirits, "spirit")
        _sub(el, "guid", prow.id)
        _sub(el, "name", names["sprite"].get(prow.sprite_id, ""))
        _sub(el, "type", "Sprite")
        _sub(el, "force", prow.level)
        _sub(el, "services", prow.services)
        _sub(el, "bound", "True" if prow.registered else "False")
        _sub(el, "fettered", "False")
        if prow.hits is not None:
            _sub(el, "hits", prow.hits)
        if prow.opposed_hits is not None:
            _sub(el, "opposedhits", prow.opposed_hits)


def _export_enhancements(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write the adept-power enhancements (`<enhancements>`)."""
    el = _sub(root, "enhancements")
    for eid in state.adept_enhancements:
        row = _sub(el, "enhancement")
        _sub(row, "sourceid", eid)
        _sub(row, "name", names["enhancement"].get(eid, ""))


def _export_initiation(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write initiation and submersion grades, and the metamagics on them."""
    grades = _sub(root, "initiationgrades")
    init_by_grade = {int(c.grade): c for c in state.initiations}
    sub_by_grade = {int(c.grade): c for c in state.submersions}

    def _emit_grade(i: int, res: bool, choice: object) -> None:
        grade_el = _sub(grades, "initiationgrade")
        _sub(grade_el, "grade", i)
        _sub(grade_el, "res", "True" if res else "False")
        _sub(grade_el, "group", "True" if getattr(choice, "group", False) else "False")
        _sub(grade_el, "ordeal", "True" if getattr(choice, "ordeal", False) else "False")
        _sub(grade_el, "schooling", "True" if getattr(choice, "schooling", False) else "False")

    for i in range(1, state.initiate_grade + 1):
        _emit_grade(i, False, init_by_grade.get(i))
    for i in range(1, state.submersion_grade + 1):
        _emit_grade(i, True, sub_by_grade.get(i))
    mms = _sub(root, "metamagics")
    for ic in state.initiations:
        el = _sub(mms, "metamagic")
        _sub(el, "sourceid", ic.option_id)
        _sub(el, "name", names["metamagic"].get(ic.option_id) or names["art"].get(ic.option_id, ""))


def state_to_chum5(state: CharacterState) -> bytes:
    """A computed `CharacterState` out as Chummer5a-compatible XML.

    The mirror of `chummer_import.chum5_to_state`, and held to the same
    property: the pair is a fixed point on a computed character
    (`tests/test_chummer_roundtrip*.py`).

    Each `_export_*` below writes one top-level element under `<character>`.
    They are independent — none reads what another wrote — so the 322-line
    function they came from split along its own `_sub(root, ...)` boundaries.
    """
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
        | {
            k: v
            for b in ("commlinks", "cyberdecks", "rccs", "sensors", "optics", "programs", "apps", "drones", "vehicles")
            for k, v in _id_name(cat[b]).items()
        },
        "vmod": _id_name(cat["vehicle_mods"]),
        "wmount": _id_name(cat["weapon_mounts"]),
        "lifestyle": _id_name(cat["lifestyles"]),
        "tradition": _id_name(cat["traditions"]),
        "mentor": _id_name(list(cat["mentors"]) + list(cat["paragons"])),
        "metamagic": _id_name(cat["metamagics"]),
        "art": _id_name(cat.get("magic_arts") or []),
        "focus": _id_name(cat.get("foci") or []),
        # The one gear a Qi focus is, kept as id/name rather than a lookup map.
        "qifocus": {
            "id": str((cat.get("qi_focus") or {}).get("id") or ""),
            "name": str((cat.get("qi_focus") or {}).get("name") or ""),
        },
        "drugcomponent": _id_name(cat.get("drug_components") or []),
        "spirit": _id_name(cat.get("spirits") or []),
        "sprite": _id_name(cat.get("sprites") or []),
        "stream": _id_name(cat.get("streams") or []),
        "enhancement": _id_name(cat.get("enhancements") or []),
    }

    root = ET.Element("character")

    ctx: _Ctx = {"meta_attrs": m_attr}
    for section in _SECTIONS:
        section(root, state, names, ctx)

    xml = ET.tostring(root, encoding="utf-8")
    return minidom.parseString(xml).toprettyxml(indent="  ", encoding="utf-8")


#: Written in this order, which is the order Chummer's own files use. Nothing
#: here reads what an earlier section wrote — the order is for the reader (and
#: for a diff against a real .chum5), not for correctness.
_SECTIONS = (
    _export_identity,
    _export_priorities,
    _export_attributes,
    _export_skills,
    _export_qualities,
    _export_martial_arts,
    _export_ware,
    _export_armor,
    _export_weapons,
    _export_gear,
    _export_foci,
    _export_vehicles,
    _export_lifestyles,
    _export_custom_drugs,
    _export_contacts,
    _export_spirits,
    _export_enhancements,
    _export_initiation,
)
