"""Everything a character carries or wears: ware, armor, weapons, gear, the
bonded foci that are gear, and vehicles.

The mirror of :mod:`app.chummer_import.gear`.
"""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from typing import Any

from ..data_loader import catalog, catalog_list
from ..data_loader._xml import parse_data
from ..engine.gear.ammo import ammo_fits_weapon
from ..engine.gear.weapons.hosts import ware_weapon_specs
from ..engine.lookups import _focus_by_id
from ..models import CharacterState, FocusInstall, GearInstall
from ._common import _Ctx, _Names, _sub
from .improvements import _bonus_improvements, _Imp, _text, _with_rows, _write_improvements
from .metatype import export_metatype_weapons


def _ware_writer(state: CharacterState, names: _Names) -> Any:
    """Return ``(by_parent, emit)`` for cyber- and bioware rows.

    An implant with a `<selectskill>` or `<hardwires>` bonus also carries the
    skill that was picked for it. This app keys those picks by the *install*
    row, whose id is regenerated on every import, so the pick travels on the
    implant itself rather than in a map of ids.
    """

    def _picks_of(inst_id: str) -> list[tuple[str, str]]:
        prefix = f"ware:{inst_id}:"
        return sorted((key[len(prefix) :], value) for key, value in state.skill_picks.items() if key.startswith(prefix))

    gear_by_parent, emit_gear = _gear_writer(state, names)
    weapon_specs = ware_weapon_specs(state)
    gear_specs = {row["id"]: row for row in catalog_list("gear")}
    ware_specs = {row["id"]: row for kind in ("cyberware", "bioware") for row in catalog()[kind]["items"]}
    by_parent: dict[str | None, list[Any]] = {}
    for r in [*state.cyberware, *state.bioware]:
        by_parent.setdefault(r.parent_id, []).append(r)

    def emit(parent_el: ET.Element, rowset: list[Any], tag: str) -> None:
        for r in rowset:
            w = _sub(parent_el, tag)
            _sub(w, "guid", r.id)
            _sub(w, "sourceid", r.ware_id)
            _sub(w, "name", names["ware"].get(r.ware_id, ""))
            _sub(w, "grade", r.grade)
            _sub(w, "rating", r.rating)
            spec = ware_specs.get(r.ware_id) or {}
            if r.id in weapon_specs:
                _sub(w, "weaponguid", _ware_weapon_guid(r.id))
            if (
                spec.get("category") == "Cyberlimb"
                or spec.get("limbslot")
                or spec.get("inherit_attributes")
                or spec.get("mounts_to")
                or spec.get("modular_mount")
                or spec.get("blocks_mounts")
            ):
                # Cyberware.Load reads these saved fields rather than
                # rebuilding the limb/connector from the catalog definition.
                _sub(w, "category", spec.get("category") or "")
                _sub(w, "limbslot", spec.get("limbslot") or "")
                _sub(w, "limbslotcount", spec.get("limbslotcount") or "1")
                _sub(w, "inheritattributes", "True" if spec.get("inherit_attributes") else "False")
                _sub(w, "hasmodularmount", spec.get("modular_mount") or "")
                _sub(w, "plugsintomodularmount", spec.get("mounts_to") or "")
                _sub(w, "blocksmounts", ",".join(spec.get("blocks_mounts") or []))
            if getattr(r, "cost", None) is not None:
                _sub(w, "cost", r.cost)
            if r.side:
                _sub(w, "location", r.side)
            if r.extra:
                _sub(w, "extra", r.extra)
            if getattr(r, "included", False):
                _sub(w, "included", "True")
            # Chummer's mark for "came with its parent": the parent's guid.
            # Empty on a top-level piece and on anything bought for a parent.
            _sub(w, "parentid", r.parent_id if r.parent_id and getattr(r, "included", False) else "")
            _sub(w, "discountedcost", "True" if getattr(r, "discounted", False) else "False")
            _sub(w, "essdiscount", getattr(r, "ess_discount", 0) or 0)
            picks = _picks_of(r.id)
            if picks:
                picks_el = _sub(w, "skillpicks")
                for index, skill in picks:
                    pick = _sub(picks_el, "pick")
                    _sub(pick, "index", index)
                    _sub(pick, "skill", skill)
            kids = by_parent.get(r.id)
            if kids:
                emit(_sub(w, "children"), kids, tag)
            # what it holds (a Chemical Gland's chemical)
            held = gear_by_parent.get(r.id) or []
            if r.id in weapon_specs:
                held = [g for g in held if not ammo_fits_weapon(gear_specs.get(g.gear_id) or {}, weapon_specs[r.id])]
            if held:
                emit_gear(_sub(w, "gears"), held)

    return by_parent, emit


def _export_ware(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write cyber- and bioware, re-nested by parent. What sits in a vehicle
    mod (a drone arm's Shock Hand) is written with the mod instead."""
    by_parent, emit = _ware_writer(state, names)
    cyber_ids = {r.id for r in state.cyberware}
    bio_ids = {r.id for r in state.bioware}
    top = by_parent.get(None, [])
    emit(_sub(root, "cyberwares"), [r for r in top if r.id in cyber_ids], "cyberware")
    emit(_sub(root, "biowares"), [r for r in top if r.id in bio_ids], "bioware")
    _export_ware_improvements(root, state, by_parent, top, cyber_ids)


def _export_ware_improvements(
    root: ET.Element,
    state: CharacterState,
    by_parent: dict[str | None, list[Any]],
    top: list[Any],
    cyber_ids: set[str],
) -> None:
    """What `Cyberware.Create` leaves in `<improvements>` when it runs an
    implant's `<bonus>` at its rating, under the implant's guid — Chummer
    never runs it again on load. Only the implants written above: one in a
    vehicle mod works on the vehicle, not the character."""
    definitions = {
        node.findtext("id") or "": node
        for name, path in (("cyberware.xml", "./cyberwares/cyberware"), ("bioware.xml", "./biowares/bioware"))
        for node in parse_data(name).findall(path)
    }
    stack = list(top)
    while stack:
        row = stack.pop()
        stack.extend(by_parent.get(row.id) or [])
        definition = definitions.get(row.ware_id)
        bonus = definition.find("bonus") if definition is not None else None
        if definition is None or bonus is None:
            continue
        source = "Cyberware" if row.id in cyber_ids else "Bioware"
        owner = definition.findtext("name") or ""
        prefix = f"ware:{row.id}:"
        skills = {key[len(prefix) :]: value for key, value in state.skill_picks.items() if key.startswith(prefix)}
        rows = _bonus_improvements(bonus, int(row.rating or 1), row.extra or "", skills=skills)
        _write_improvements(root, _with_rows(root, rows, row.id, owner), row.id, source)


def _export_armor(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write armor and its mods."""
    armors = _sub(root, "armors")
    amods_by_parent: dict[str | None, list[Any]] = {}
    for mrow in state.armor_mods:
        amods_by_parent.setdefault(mrow.parent_id, []).append(mrow)
    gear_by_parent, emit_gear = _gear_writer(state, names)
    for a in state.armor:
        el = _sub(armors, "armor")
        _sub(el, "guid", a.id)
        _sub(el, "sourceid", a.armor_id)
        _sub(el, "name", names["armor"].get(a.armor_id, ""))
        if a.cost is not None:
            _sub(el, "cost", a.cost)
        _sub(el, "rating", a.rating)
        _sub(el, "equipped", "True" if a.equipped else "False")
        _sub(el, "discountedcost", "True" if a.discounted else "False")
        mods = _sub(el, "armormods")
        for mrow in amods_by_parent.get(a.id, []):
            mm = _sub(mods, "armormod")
            _sub(mm, "guid", mrow.id)
            _sub(mm, "sourceid", mrow.mod_id)
            _sub(mm, "name", names["armormod"].get(mrow.mod_id, ""))
            _sub(mm, "rating", mrow.rating)
            _sub(mm, "included", "True" if mrow.included else "False")
            if mrow.stack_with:
                _sub(mm, "extra", mrow.stack_with)
        # the gear it carries (a Holster, a Medkit), as Chummer keeps it
        carried = gear_by_parent.get(a.id)
        if carried:
            emit_gear(_sub(el, "gears"), carried)
    _export_armor_improvements(root, state, amods_by_parent)


def _export_armor_improvements(
    root: ET.Element, state: CharacterState, amods_by_parent: dict[str | None, list[Any]]
) -> None:
    """What `Armor.Create` and `ArmorMod.Create` leave in `<improvements>`
    when they run the `<bonus>` at the piece's rating, under its guid. Armor
    not worn keeps them disabled, its mods' with it."""
    armor = parse_data("armor.xml")
    definitions = {
        node.findtext("id") or "": node for node in [*armor.findall("./armors/armor"), *armor.findall("./mods/mod")]
    }
    for a in state.armor:
        for row, ref, source in [
            (a, a.armor_id, "Armor"),
            *((m, m.mod_id, "ArmorMod") for m in amods_by_parent.get(a.id, [])),
        ]:
            definition = definitions.get(ref)
            bonus = definition.find("bonus") if definition is not None else None
            if definition is None or bonus is None:
                continue
            rows = _bonus_improvements(bonus, int(row.rating or 1), None)
            owner = definition.findtext("name") or ""
            _write_improvements(root, _with_rows(root, rows, row.id, owner), row.id, source, enabled=a.equipped)


def _ware_weapon_guid(install_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"chummer-web:ware-weapon:{install_id}"))


def _export_weapons(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write weapons and their accessories."""
    weapons = _sub(root, "weapons")
    wacc_by_parent: dict[str | None, list[Any]] = {}
    for arow in state.weapon_accessories:
        wacc_by_parent.setdefault(arow.parent_id, []).append(arow)
    # Chummer writes "None" for an accessory that takes no mount; one that
    # wants a mount and found none keeps its empty value, and its error
    mountless = {str(row["id"]) for row in catalog().get("weapon_accessories") or [] if not row.get("mounts")}
    # a gun a vehicle's own entry brought with it: Chummer marks one with the
    # host's id in `<parentid>`, and the reader skips it there because the
    # entry grants it again
    host_of = {
        row.weapon_install_id: row.parent_id
        for row in state.weapon_mounts or []
        if row.weapon_install_id and row.parent_id
    }
    gear_by_parent, emit_gear = _gear_writer(state, names)
    specs = ware_weapon_specs(state)
    gear_specs = {row["id"]: row for row in catalog_list("gear")}

    def emit_contents(el: ET.Element, inst_id: str, loaded_ammo_id: str | None) -> None:
        # Web extension: ammunition ownership/selection, not Chummer clips.
        if loaded_ammo_id:
            _sub(el, "loadedammoguid", loaded_ammo_id)
        held = gear_by_parent.get(inst_id) or []
        if inst_id in specs:
            held = [g for g in held if ammo_fits_weapon(gear_specs.get(g.gear_id) or {}, specs[inst_id])]
        if held:
            emit_gear(_sub(el, "gears"), held)

    for w in state.weapons:
        el = _sub(weapons, "weapon")
        # the guid a Weapon Focus's improvement names it by
        _sub(el, "guid", w.id)
        _sub(el, "sourceid", w.weapon_id)
        _sub(el, "name", names["weapon"].get(w.weapon_id, ""))
        _sub(el, "qty", w.qty)
        if w.included:
            _sub(el, "parentid", host_of.get(w.id, ""))
        _sub(el, "discountedcost", "True" if w.discounted else "False")
        emit_contents(el, w.id, w.loaded_ammo_id)
        _emit_accessories(el, w.id, wacc_by_parent, names, mountless)

    for inst in [*state.cyberware, *state.bioware]:
        spec = specs.get(inst.id)
        if not spec:
            continue
        el = _sub(weapons, "weapon")
        _sub(el, "guid", _ware_weapon_guid(inst.id))
        _sub(el, "sourceid", spec["id"])
        _sub(el, "name", spec["name"])
        _sub(el, "parentid", inst.id)
        _sub(el, "cyberware", "True")
        _sub(el, "cost", 0)
        for key in ("category", "type", "reach", "damage", "ap", "mode", "rc", "ammo", "accuracy", "useskill"):
            _sub(el, key, spec.get(key) or "")
        emit_contents(el, inst.id, inst.loaded_ammo_id)
        _emit_accessories(el, inst.id, wacc_by_parent, names, mountless)

    export_metatype_weapons(weapons, state, ctx)


def _emit_accessories(
    el: ET.Element, inst_id: str, by_parent: dict[str | None, list[Any]], names: _Names, mountless: set[str]
) -> None:
    accs = _sub(el, "accessories")
    for arow in by_parent.get(inst_id, []):
        ac = _sub(accs, "accessory")
        _sub(ac, "sourceid", arow.accessory_id)
        _sub(ac, "name", names["wacc"].get(arow.accessory_id, ""))
        _sub(ac, "mount", arow.mount or ("None" if arow.accessory_id in mountless else ""))
        _sub(ac, "rating", arow.rating)
        _sub(ac, "included", "True" if arow.included else "False")


def _gear_writer(state: CharacterState, names: _Names) -> tuple[dict[str | None, list[Any]], Any]:
    """Gear of every bucket by parent id, and the writer of a `<gear>` list."""
    gear_rows: list[Any] = [
        *state.gear,
        *state.commlinks,
        *state.cyberdecks,
        *state.rccs,
        *state.sensors,
        *state.optics,
        *state.programs,
        *state.apps,
    ]
    from ..engine.compute.gear import resolve_gear
    from ..engine.gear.electronic_modifications import SINGLE_PARTS

    bundle = resolve_gear(state.model_copy(deep=True))
    parts_remaining = {
        str(r["id"]): int(r["parts_remaining_units"]) for r in bundle["gear"] if "parts_remaining_units" in r
    }
    draft_ids = {str(r["id"]) for r in bundle["gear"] if r.get("modification_status") == "pending"}
    used_supplies = {
        s.id: sum(
            a.units
            for r in state.electronic_modification_records
            if r.status == "completed"
            for a in r.allocations
            if a.source_id == s.id
        )
        for s in state.electronic_parts_supplies
    }
    for supply in state.electronic_parts_supplies:
        left = max(0, supply.units - used_supplies[supply.id])
        if left:
            gear_rows.append(
                GearInstall(
                    id=supply.id, gear_id=SINGLE_PARTS, qty=1, purchased_parts_units=left, included=True, cost=0
                )
            )
            parts_remaining[supply.id] = left
    by_parent_g: dict[str | None, list[Any]] = {}
    program_ids = {p.id for p in state.programs}
    module_gids = {str(r["id"]) for r in catalog_list("gear") if r.get("category") == "Cyberdeck Modules"}
    for g in gear_rows:
        if g.id in draft_ids or getattr(g, "parent_id", None) in draft_ids or parts_remaining.get(g.id) == 0:
            continue
        # Flatten residual parts; parent quantity must not multiply partial stock.
        by_parent_g.setdefault(None if g.id in parts_remaining else getattr(g, "parent_id", None), []).append(g)

    # this app's `qty` is in lots of `costfor` (a box of 10 rounds); Chummer's
    # `<qty>` counts the single items
    cost_for = {
        str(row["id"]): int(row.get("costfor") or 0)
        for bucket in ("gear", "commlinks", "cyberdecks", "rccs", "sensors", "optics", "programs", "apps")
        for row in catalog_list(bucket)
    }

    def emit_gear(parent_el: ET.Element, rows: list[Any]) -> None:
        for g in rows:
            gid = g.gear_id
            el = _sub(parent_el, "gear")
            _sub(el, "guid", g.id)
            _sub(el, "sourceid", gid)
            _sub(el, "name", names["gear"].get(gid, ""))
            if getattr(g, "name", None):
                # a Custom Item goes by the name the player gave it
                el.find("name").text = g.name  # type: ignore[union-attr]
            _sub(el, "rating", getattr(g, "rating", 1))
            if g.id == state.home_node:
                # an A.I.'s home node (`IHasMatrixAttributes.IsHomeNode`)
                _sub(el, "homenode", "True")
            if g.id in program_ids:
                _sub(el, "equipped", "True" if g.running else "False")
            elif gid in module_gids:
                _sub(el, "equipped", "True" if g.equipped else "False")
            if getattr(g, "extra", None):
                _sub(el, "extra", g.extra)
            _sub(
                el,
                "qty",
                (parts_remaining[g.id] // 4 if parts_remaining[g.id] % 4 == 0 else parts_remaining[g.id] / 4)
                if g.id in parts_remaining
                else int(getattr(g, "qty", 1) or 1) * max(1, cost_for.get(gid, 0)),
            )
            _sub(el, "discountedcost", "True" if getattr(g, "discounted", False) else "False")
            if getattr(g, "cost", None) is not None:
                _sub(el, "cost", g.cost)
            if getattr(g, "parent_id", None):
                _sub(el, "included", "True" if getattr(g, "included", False) else "False")
            kids = by_parent_g.get(g.id)
            if kids:
                emit_gear(_sub(el, "children"), kids)

    return by_parent_g, emit_gear


def _export_gear(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write gear from every bucket, flattened back into one <gears>."""
    # a quality's own gear (a Technomancer's Living Persona) may be there already
    gears = root.find("gears")
    if gears is None:
        gears = _sub(root, "gears")
    by_parent_g, emit_gear = _gear_writer(state, names)
    emit_gear(gears, by_parent_g.get(None, []))
    _emit_focus_gear(gears, state, names)
    _export_gear_improvements(root, state, by_parent_g)


def _export_gear_improvements(root: ET.Element, state: CharacterState, by_parent: dict[str | None, list[Any]]) -> None:
    """What `Gear.Create` leaves in `<improvements>` when it runs the item's
    `<bonus>` at its rating, with its extra as the pick, under its guid: the
    character's own gear and what their armor carries, which is off with
    armor not worn. Not a focus, whose improvements wait for its bonding,
    nor what sits in a weapon, which works on that.

    A vehicle's gear counts only when it came with the vehicle (the Shiawase
    Caduceus's Medkit): `Vehicle.Create` makes its `<gears>` with improvements,
    but gear put in a vehicle afterwards is made without them
    (`PurchaseVehicleGear` passes `blnAddImprovements: false`), and so is
    what is put in that gear."""
    definitions = {node.findtext("id") or "": node for node in parse_data("gear.xml").findall("./gears/gear")}
    # (row, enabled, only what came with its parent)
    stack = [(row, True, False) for row in by_parent.get(None, [])]
    stack += [(row, a.equipped, False) for a in state.armor for row in by_parent.get(a.id, [])]
    stack += [(row, True, True) for v in [*state.vehicles, *state.drones] for row in by_parent.get(v.id, [])]
    while stack:
        row, enabled, built_in = stack.pop()
        if built_in and not getattr(row, "included", False):
            continue
        stack += [(child, enabled, built_in) for child in by_parent.get(row.id) or []]
        definition = definitions.get(row.gear_id)
        bonus = definition.find("bonus") if definition is not None else None
        if definition is None or bonus is None or (definition.findtext("category") or "").endswith("Foci"):
            continue
        rows = _bonus_improvements(bonus, int(getattr(row, "rating", 1) or 1), getattr(row, "extra", None) or "")
        owner = getattr(row, "name", None) or definition.findtext("name") or ""
        _write_improvements(root, _with_rows(root, rows, row.id, owner), row.id, "Gear", enabled=enabled)


def _focus_tradition(frow: FocusInstall) -> str:
    """The tradition a `<selecttradition>` focus is made for, if its pick
    names one."""
    if not (_focus_by_id(frow.gear_id) or {}).get("needs_tradition"):
        return ""
    names = {str(t.get("name") or "") for t in catalog().get("traditions") or []}
    return frow.extra if frow.extra and frow.extra in names else ""


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
        tradition = _focus_tradition(frow)
        if tradition:
            # the tradition it is made for, which bonding asks for: Chummer
            # keeps the pick as the gear's `<extra>`
            _sub(el, "extra", tradition)
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


def _focus_guid(gear_id: str) -> str:
    """The `<focus>` pointer's own guid: Chummer's `Focus` is a row apart from
    the gear it points at, and a shared guid would make the gear's
    improvements name the pointer instead."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{gear_id}:focus"))


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
        _sub(el, "guid", _focus_guid(frow.id))
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
        _sub(el, "guid", _focus_guid(qrow.id))
        _sub(el, "gearid", qrow.id)
        _sub(el, "powerrating", qrow.power_rating)
        if qrow.extra:
            _sub(el, "powerextra", qrow.extra)
    _export_focus_improvements(root, state, names, "adept" in set(ctx["derived"].get("enabled_tabs") or []))


def _export_focus_improvements(root: ET.Element, state: CharacterState, names: _Names, adept: bool) -> None:
    """What bonding a focus leaves in `<improvements>`: its `<bonus>` run at
    its force, under its gear's guid — a Weapon Focus's dice name the weapon
    it is bound to. A Qi focus's power gets its free points (an adept's only,
    as `selectpowers` checks); `_export_free_power_rows` gives them a row."""
    definitions = {node.findtext("id") or "": node for node in parse_data("gear.xml").findall("./gears/gear")}
    for frow in state.foci:
        definition = definitions.get(frow.gear_id)
        bonus = definition.find("bonus") if definition is not None else None
        if definition is None or bonus is None:
            continue
        pick = _focus_tradition(frow) if (_focus_by_id(frow.gear_id) or {}).get("needs_tradition") else frow.extra
        rows = _bonus_improvements(bonus, int(frow.force or 1), pick)
        _write_improvements(root, _with_rows(root, rows, frow.id, definition.findtext("name") or ""), frow.id, "Gear")
    qi = definitions.get(names["qifocus"].get("id", ""))
    choices = qi.findall("./bonus/selectpowers/selectpower") if qi is not None and adept else []
    for qrow in state.qi_foci:
        power = names["power"].get(qrow.power_id, "")
        rows = []
        for choice in choices:
            levels = _text(choice, "val").replace("Rating", str(qrow.rating))
            kind = "AdeptPowerFreePoints" if _text(choice, "pointsperlevel") else "AdeptPowerFreeLevels"
            rows.append(_Imp(kind, power, unique=qrow.extra or "", rating=int(levels) if levels.isdigit() else 0))
        _write_improvements(root, rows, qrow.id, "Gear")


def _export_vehicles(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write vehicles, drones and vehicle mods."""
    vehs = _sub(root, "vehicles")
    vmod_by_parent: dict[str | None, list[Any]] = {}
    for vrow in state.vehicle_mods:
        vmod_by_parent.setdefault(vrow.parent_id, []).append(vrow)
    gear_by_parent, emit_gear = _gear_writer(state, names)
    ware_by_parent, emit_ware = _ware_writer(state, names)
    for v in [*state.vehicles, *state.drones]:
        el = _sub(vehs, "vehicle")
        _sub(el, "sourceid", v.gear_id)
        _sub(el, "name", names["gear"].get(v.gear_id, ""))
        if v.id == state.home_node:
            # an A.I. living in it (`Vehicle.IsHomeNode`)
            _sub(el, "homenode", "True")
        mods = _sub(el, "mods")
        for vrow in vmod_by_parent.get(v.id, []):
            mm = _sub(mods, "mod")
            _sub(mm, "sourceid", vrow.mod_id)
            _sub(mm, "name", names["vmod"].get(vrow.mod_id, ""))
            _sub(mm, "rating", vrow.rating)
            _sub(mm, "included", "True" if vrow.included else "False")
            if vrow.free:
                # Chummer's "free item" tick is a `<cost>` of 0
                _sub(mm, "cost", 0)
            # the implants in it (a drone arm's Shock Hand)
            ware = ware_by_parent.get(vrow.id)
            if ware:
                emit_ware(_sub(mm, "cyberwares"), ware, "cyberware")
        # what is stowed in it (a camera, a medkit), as Chummer keeps it
        stowed = gear_by_parent.get(v.id)
        if stowed:
            emit_gear(_sub(el, "gears"), stowed)
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
