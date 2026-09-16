"""Who the character is and how they were built: identity, the reward log,
priorities, attributes, skills and contacts.

The mirror of :mod:`app.chummer_import.identity`.
"""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from datetime import datetime

from ..data_loader import catalog
from ..engine import compute
from ..models import CharacterState
from ._common import _Ctx, _Names, _sub

_ATTR_ORDER = ("BOD", "AGI", "REA", "STR", "CHA", "INT", "LOG", "WIL", "EDG", "MAG", "RES", "DEP")
_BUILD_METHOD_OUT = {"Priority": "Priority", "SumToTen": "SumtoTen", "Karma": "Karma"}


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
    # the creation availability limit does travel in the save — see the note in
    # `chummer_import.identity._import_settings`
    if state.settings.chargen_avail_max is not None:
        _sub(root, "maxavail", state.settings.chargen_avail_max)
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
    # Chummer's `<karma>` / `<nuyen>` are what is left to spend, not what was
    # earned (the reward log below is the history)
    left = compute(state.model_copy(deep=True)).derived if state.career else {}
    _sub(root, "karma", int((left.get("karma") or {}).get("remaining") or 0) if state.career else 0)
    _sub(root, "nuyen", int(left.get("nuyen") or 0) if state.career else 0)
    if state.career and (state.reward_log or state.expense_log):
        _export_reward_log(root, state)
    # Reputation, and the nuyen bought with karma at chargen — Chummer keeps
    # the latter in `<nuyenbp>`, which is build points in old money.
    _sub(root, "streetcred", state.street_cred)
    _sub(root, "burntstreetcred", state.burnt_street_cred)
    _sub(root, "notoriety", state.notoriety_bonus)
    _sub(root, "nuyenbp", state.karma_nuyen)


def _export_reward_log(root: ET.Element, state: CharacterState) -> None:
    """`<expenses>`: the career reward ledger as Chummer's expense log.

    Chummer logs karma and nuyen as separate rows, so a reward that paid both
    becomes two. `<rewardid>` is this app's — Chummer ignores it — and is what
    puts the pair back together on import. What a save's log spent comes back
    out the same way, as the negative rows it came in as.
    """
    expenses = _sub(root, "expenses")
    stamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    for row in [*state.reward_log, *state.expense_log]:
        for kind, amount in (("Karma", row.karma), ("Nuyen", row.nuyen)):
            if not amount:
                continue
            el = _sub(expenses, "expense")
            _sub(el, "guid", row.id if kind == "Karma" else str(uuid.uuid5(uuid.NAMESPACE_URL, f"{row.id}:nuyen")))
            _sub(el, "date", stamp)
            _sub(el, "amount", amount)
            _sub(el, "reason", row.label)
            _sub(el, "type", kind)
            _sub(el, "refund", "False")
            _sub(el, "rewardid", row.id)


#: Chummer writes a priority as "letter,sum-to-ten value" (`E,0` … `A,4`) —
#: the form every save it produces carries, in every build method.
_PRIORITY_VALUE = {"A": 4, "B": 3, "C": 2, "D": 1, "E": 0}


def _export_priorities(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write the five priorities and the talent, straight under `<character>`.

    That is where Chummer reads them (`Character.Load`); inside a wrapper
    element they would be ignored and the character would open on defaults.
    """
    p = state.priorities
    for tag, letter in (
        ("prioritymetatype", p.Heritage),
        ("priorityattributes", p.Attributes),
        ("priorityspecial", p.Talent),
        ("priorityskills", p.Skills),
        ("priorityresources", p.Resources),
    ):
        _sub(root, tag, f"{letter},{_PRIORITY_VALUE.get(letter, 0)}")
    _sub(root, "prioritytalent", state.talent)


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
        # the top levels bought with karma at creation are Chummer's <karma>
        karma = 0 if state.career else max(0, min(int(state.attribute_karma.get(key, 0)), val - lo))
        _sub(attr_el, "base", max(val - lo - karma, 0))
        _sub(attr_el, "karma", karma)
    ess = _sub(attrs, "attribute")
    _sub(ess, "name", "ESS")
    _sub(ess, "base", 6)
    _sub(ess, "karma", 0)
    if state.mystic_pp:
        # A Mystic Adept's MAG is split between spells and power points, and
        # the adept half is what this app calls `mystic_pp`.
        _sub(root, "magsplitadept", state.mystic_pp)
        _sub(root, "magsplitmagician", max(0, int(state.attributes.get("MAG", 0)) - int(state.mystic_pp)))


#: Chummer's id for a knowledge skill it has no data for (a custom one).
_NO_SKILL_ID = "00000000-0000-0000-0000-000000000000"


def _export_skills(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write skills the way Chummer does: `<newskills>`, an active skill named
    only by its skills.xml id (`<suid>`), a knowledge skill by name and type.

    Chummer drops a skill that has no `<suid>` (`Skill.Load`), and without
    `<newskills>` falls back to a pre-5 layout this app never wrote — so the
    old `<skills><skills>` export opened in Chummer with no skills at all.
    """
    data = catalog()["skills"]
    active_ids = {str(row["name"]): str(row["id"]) for row in data.get("skills") or []}
    active_cats = {str(row["name"]): str(row.get("category") or "") for row in data.get("skills") or []}
    knowledge_ids = {str(row["name"]): str(row["id"]) for row in data.get("knowledge") or [] if row.get("id")}
    ns = _sub(root, "newskills")

    def karma_of(levels: dict[str, int], name: str, rating: int) -> int:
        # the top levels bought with karma at creation are Chummer's <karma>
        return 0 if state.career else max(0, min(int(levels.get(name, 0)), int(rating)))

    def specs(el: ET.Element, name: str) -> None:
        spn = state.skill_specializations.get(name)
        if spn:
            spec = _sub(_sub(el, "specs"), "spec")
            _sub(spec, "guid", str(uuid.uuid5(uuid.NAMESPACE_URL, f"{state.id}:spec:{name}")))
            _sub(spec, "name", spn)
            _sub(spec, "free", "False")

    active = _sub(ns, "skills")
    for name, rating in sorted(state.skills.items()):
        if name not in active_ids:
            continue
        s = _sub(active, "skill")
        _sub(s, "suid", active_ids[name])
        _sub(s, "isknowledge", "False")
        _sub(s, "skillcategory", active_cats.get(name, ""))
        karma = karma_of(state.skill_karma, name, rating)
        _sub(s, "karma", karma)
        _sub(s, "base", rating - karma)
        specs(s, name)
    for exotic in state.exotic_skills:
        # One skill per weapon, which Chummer writes as the exotic skill's id
        # plus the weapon in `<specific>`.
        if exotic.skill_name not in active_ids:
            continue
        s = _sub(active, "skill")
        _sub(s, "suid", active_ids[exotic.skill_name])
        _sub(s, "isknowledge", "False")
        _sub(s, "skillcategory", active_cats.get(exotic.skill_name, ""))
        _sub(s, "karma", 0)
        _sub(s, "base", exotic.rating)
        _sub(s, "specific", exotic.extra)

    kno = _sub(ns, "knoskills")

    def knowledge(name: str, typ: str, base: int, karma: int, native: bool) -> None:
        s = _sub(kno, "skill")
        _sub(s, "suid", knowledge_ids.get(name, _NO_SKILL_ID))
        _sub(s, "isknowledge", "True")
        _sub(s, "skillcategory", typ)
        _sub(s, "karma", karma)
        _sub(s, "base", base)
        _sub(s, "name", name)
        _sub(s, "type", typ)
        _sub(s, "isnativelanguage", "True" if native else "False")
        specs(s, name)

    for name in state.native_languages:
        knowledge(name, "Language", 0, 0, True)
    for name, rating in sorted(state.knowledge_skills.items()):
        karma = karma_of(state.knowledge_karma, name, rating)
        knowledge(name, state.knowledge_categories.get(name, "Academic"), rating - karma, karma, False)

    grps = _sub(ns, "groups")
    for name, rating in sorted(state.skill_groups.items()):
        grp_el = _sub(grps, "group")
        karma = karma_of(state.skill_group_karma, name, rating)
        _sub(grp_el, "karma", karma)
        _sub(grp_el, "base", rating - karma)
        _sub(grp_el, "name", name)


def _export_contacts(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write contacts, plus the tradition and mentor a magician carries."""
    cts = _sub(root, "contacts")
    for crow in state.contacts:
        el = _sub(cts, "contact")
        # Chummer's `UniqueId`; kept so a quality's pick of this contact
        # points at the same row after an import
        _sub(el, "guid", crow.id)
        _sub(el, "name", crow.name)
        _sub(el, "role", crow.role or "")
        _sub(el, "connection", crow.connection)
        _sub(el, "loyalty", crow.loyalty)
        _sub(el, "type", "Group" if crow.group else "Contact")
