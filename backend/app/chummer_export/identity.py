"""Who the character is: identity, attributes and contacts.

How they were built lives in ``build.py`` and their skills in ``skills.py``.
The mirror of :mod:`app.chummer_import.identity`.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from ..models import CharacterState
from ._common import _Ctx, _Names, _sub
from .build import _export_reward_log, _export_settings_key

_ATTR_ORDER = ("BOD", "AGI", "REA", "STR", "CHA", "INT", "LOG", "WIL", "EDG", "MAG", "RES", "DEP")
_BUILD_METHOD_OUT = {"Priority": "Priority", "SumToTen": "SumtoTen", "Karma": "Karma", "LifeModule": "LifeModule"}


def _export_identity(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write name, metatype, build method, the bio fields, portrait and career totals."""
    _sub(root, "appversion", "Chummer Web")
    _sub(root, "name", "")
    _sub(root, "alias", state.name)
    _sub(root, "metatype", state.metatype)
    _sub(root, "metavariant", state.metavariant or "")
    _sub(root, "buildmethod", _BUILD_METHOD_OUT.get(state.build_method, "Priority"))
    _export_settings_key(root, state)
    # the creation availability limit does travel in the save — see the note in
    # `chummer_import.identity._import_settings`
    if state.settings.chargen_avail_max is not None:
        _sub(root, "maxavail", state.settings.chargen_avail_max)
    _sub(root, "created", "True" if state.career else "False")
    if state.notes:
        _sub(root, "notes", state.notes)
    if state.player_name:
        _sub(root, "playername", state.player_name)
    if state.game_notes:
        _sub(root, "gamenotes", state.game_notes)
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
    # `<mainmugshotindex>` is which portrait is the main one, and -1 is
    # Chummer's "none": a save without it is read as having a portrait at
    # index 0 that is not there.
    pics = [p for p in (state.portrait, *state.extra_portraits) if p]
    _sub(root, "mainmugshotindex", "0" if pics else "-1")
    if pics:
        shots = _sub(root, "mugshots")
        for pic in pics:
            _sub(shots, "mugshot", pic.split(",", 1)[-1] if pic.startswith("data:") else pic)
    # Chummer's `<karma>` / `<nuyen>` are what is left to spend, not what was
    # earned (the reward log below is the history)
    left = ctx["derived"] if state.career else {}
    _sub(root, "karma", int((left.get("karma") or {}).get("remaining") or 0) if state.career else 0)
    _sub(root, "nuyen", int(left.get("nuyen") or 0) if state.career else 0)
    if state.career and (state.reward_log or state.expense_log):
        _export_reward_log(root, state)
    # Reputation, and the nuyen bought with karma at chargen — Chummer keeps
    # the latter in `<nuyenbp>`, which is build points in old money.
    _sub(root, "streetcred", state.street_cred)
    _sub(root, "burntstreetcred", state.burnt_street_cred)
    _sub(root, "notoriety", state.notoriety_bonus)
    # The GM's own counter, stored as told — not the total, which Chummer
    # works out again from this, the qualities and (under a house rule)
    # Street Cred and Notoriety.
    _sub(root, "publicawareness", state.public_awareness)
    _sub(root, "nuyenbp", state.karma_nuyen)


def _export_attributes(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write each attribute as Chummer's base/karma pair, relative to the metatype minimum."""
    m_attr = ctx["meta_attrs"]
    # The MAG / RES / DEP the talent priority hands out is Chummer's metatype
    # minimum, not something bought: written as `<base>`, Chummer charges it
    # to the special attribute points and they come out negative.
    floors = (ctx["derived"].get("attribute_karma") or {}).get("floors") or {}
    attrs = _sub(root, "attributes")
    for key in _ATTR_ORDER:
        spec = m_attr.get(key) or {}
        lo = int(spec.get("min", 0 if key in ("MAG", "RES", "DEP") else 1))
        if key in ("MAG", "RES", "DEP") and key in floors:
            lo = int(floors[key])
        val = int(state.attributes.get(key, lo))
        if key in ("MAG", "RES", "DEP"):
            # An attribute the character does not have is 0, below the
            # metatype minimum; Chummer writes that minimum as 0 too.
            lo = min(lo, val)
        attr_el = _sub(attrs, "attribute")
        _sub(attr_el, "name", key)
        _sub(attr_el, "metatypemin", lo)
        _sub(attr_el, "metatypemax", int(spec.get("max", 6)))
        _sub(attr_el, "metatypeaugmax", int(spec.get("aug", spec.get("max", 6))))
        # the top levels bought with karma at creation are Chummer's <karma>
        karma = 0 if state.career else max(0, min(int(state.attribute_karma.get(key, 0)), val - lo))
        _sub(attr_el, "base", max(val - lo - karma, 0))
        _sub(attr_el, "karma", karma)
        if key == "MAG":
            _export_magadept(attrs)
    ess = _sub(attrs, "attribute")
    _sub(ess, "name", "ESS")
    _sub(ess, "base", 6)
    _sub(ess, "karma", 0)
    if state.mystic_pp:
        # A Mystic Adept's MAG is split between spells and power points, and
        # the adept half is what this app calls `mystic_pp`.
        _sub(root, "magsplitadept", state.mystic_pp)
        _sub(root, "magsplitmagician", max(0, int(state.attributes.get("MAG", 0)) - int(state.mystic_pp)))


def _export_magadept(attrs: ET.Element) -> None:
    """Write the `MAGAdept` row Chummer expects between `MAG` and `RES`.

    Chummer loops over a fixed list of attribute names (`AttributeStrings`) and
    **rebuilds from scratch** any name the save does not carry, so leaving this
    row out is not fatal — but it is the one row missing from every file this
    app wrote, and it costs one element to stop making Chummer guess.

    The numbers are constants on purpose. `MAGAdept` is a second MAG attribute
    only under a house rule (`mysadeptsecondmagattribute`), which this app does
    not offer; with the rule off, Chummer leaves the attribute untouched and
    saves its defaults, which is why all 34 of Chummer's own test saves carry
    `1 / 6 / 10` here whatever the character's real MAG is. A Mystic Adept's
    split still rides on `<magsplitadept>` below, the field Chummer reads when
    the house rule is off."""
    el = _sub(attrs, "attribute")
    _sub(el, "name", "MAGAdept")
    _sub(el, "metatypemin", 1)
    _sub(el, "metatypemax", 6)
    _sub(el, "metatypeaugmax", 10)
    _sub(el, "base", 0)
    _sub(el, "karma", 0)


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
        if crow.free:
            _sub(el, "free", "True")
