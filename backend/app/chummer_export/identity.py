"""Who the character is and how they were built: identity, the reward log,
priorities, attributes, skills and contacts.

The mirror of :mod:`app.chummer_import.identity`.
"""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from datetime import datetime

from ..data_loader import catalog
from ..engine import find_metatype
from ..engine.priority import heritage_cost, priority_value
from ..models import CharacterState
from ..rules import current_rules
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
    _export_settings_key(root, state)
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
    # `<mainmugshotindex>` is which portrait is the main one, and -1 is
    # Chummer's "none": a save without it is read as having a portrait at
    # index 0 that is not there.
    _sub(root, "mainmugshotindex", "0" if state.portrait else "-1")
    if state.portrait:
        b64 = state.portrait.split(",", 1)[-1] if state.portrait.startswith("data:") else state.portrait
        _sub(_sub(root, "mugshots"), "mugshot", b64)
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
    _sub(root, "nuyenbp", state.karma_nuyen)


def _export_settings_key(root: ET.Element, state: CharacterState) -> None:
    """Which settings the character was built under, in the terms Chummer
    looks them up by.

    `<settings>` is not the name on the pulldown: `Character.Load` takes it as
    a key into `SettingsManager.LoadedCharacterSettings`, whose keys are
    `CharacterSettings.DictionaryKey` — the `<id>` GUID for one of the shipped
    presets, the file name for a settings file of the player's own. Writing
    the display name (`Standard`) missed on both counts, and Chummer answered
    with "the settings file could not be loaded", naming a file the player
    could see in their own settings folder. Worse than the dialog: the
    settings it falls back to decide whether attribute `<base>` survives the
    load at all, so this is also what made the numbers come out negative.

    When the key does miss — a settings file that lives on another machine —
    Chummer scores every settings it has and substitutes the closest. It
    scores on the build method, the budget (`maxkarma` / `maxnuyen`, written
    next door), the custom data directories and the books, so `<sources>` and
    `<customdatadirectorynames>` are what point it at the right one.

    `<gameplayoption>` is the display name, where 5.202-era Chummer kept it —
    and where this app's own importer reads it from first.
    """
    settings = state.settings
    if not settings.name:
        return
    preset = next((p for p in catalog().get("settings_presets") or [] if p.get("name") == settings.name), None)
    # A settings file of the player's own is keyed by its file name, which a
    # .chum5 never carried and this app therefore does not hold. The name it
    # was saved under is the best guess available, and the scoring below is
    # what makes a miss land somewhere sensible.
    _sub(root, "settings", str(preset["id"]) if preset else f"{settings.name}.xml")
    _sub(root, "gameplayoption", settings.name)
    if settings.books:
        sources = _sub(root, "sources")
        for code in settings.books:
            _sub(sources, "source", code)
    if settings.customdata:
        directories = _sub(root, "customdatadirectorynames")
        for name in settings.customdata:
            _sub(directories, "directoryname", name)


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


def _export_build_points(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """The build's pools and prices, as figures rather than as a rule.

    Chummer stores these (`Character.Load` reads every one back) instead of
    recomputing them from the priority table, so a save that leaves them out
    is read as a character with nothing to spend — points paid for, no pool
    they came from. That is what made an export open in Chummer with negative
    attributes and negative special attribute points.

    `maxkarma` / `maxnuyen` are the exception: Chummer reads those only to
    score which settings file to substitute when the one the save names is not
    on that machine, so they are the *settings'* figures, not this
    character's (a Born Rich cap would make the character look like a
    different settings file). Current Chummer does not write them at all —
    they are a 5.202-era field it still reads — and the two Prime Runner test
    saves state a `maxkarma` of 35 and a contact multiplier today's
    `settings.xml` does not carry anywhere, so those two are the figures this
    app has rather than the ones those saves were written with.
    """
    derived = ctx["derived"]
    points = derived.get("points") or {}
    rules = current_rules()
    # `special` is what the metatype priority handed out, the same number as
    # `totalspecial`: Chummer tracks what was spent in the attributes
    # themselves, and never decrements this.
    special = int((points.get("special") or {}).get("max") or 0)
    _sub(root, "special", special)
    _sub(root, "totalspecial", special)
    _sub(root, "totalattributes", int((points.get("attributes") or {}).get("max") or 0))
    _sub(root, "contactpoints", int((derived.get("contact_points") or {}).get("free") or 0))
    _sub(root, "spelllimit", int((derived.get("spell_points") or {}).get("free") or 0))
    if state.build_method == "Karma":
        # No priority table to read: the metatype is bought with karma, and
        # every nuyen is converted from it.
        _sub(root, "metatypebp", int((derived.get("karma_chargen") or {}).get("metatype") or 0))
        _sub(root, "startingnuyen", 0)
    else:
        _sub(root, "metatypebp", heritage_cost(state.priorities.Heritage, state.metatype, state.metavariant)[1])
        _sub(root, "startingnuyen", int(priority_value("Resources", state.priorities.Resources).get("nuyen") or 0))
    _sub(root, "maxkarma", rules.chargen_karma)
    _sub(root, "maxnuyen", rules.priority_karma_nuyen_base)


def _flag(value: object) -> str:
    """Chummer's spelling of a boolean."""
    return "True" if value else "False"


def _export_flags(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """What the character *is*, as Chummer's `Load` asks it.

    Every one of these is a field `Character.Load` reads back, and each
    missing one is read as its default — which is how an adept arrived in
    Chummer mundane, with the Magic they paid for disallowed. They are
    written from `enabled_tabs`, the same answer this app's own tabs are
    drawn from, so the two readers cannot disagree about what the character
    is.

    `primaryarm` is the one figure here this app does not model: it has no
    handedness, so every character is Chummer's own default of `Right`.
    """
    derived = ctx["derived"]
    tabs = set(derived.get("enabled_tabs") or [])
    # The category is the *metatype's*, not the metavariant's: Chummer writes
    # `Metahuman` for a Nocturna, and `Shapeshifter` for a Vulpine's Human
    # form.
    base = find_metatype(state.metatype, None) or {}
    own = find_metatype(state.metatype, state.metavariant) or {}
    _sub(root, "gameedition", "SR5")
    _sub(root, "createdversion", "Chummer Web")
    _sub(root, "metatypecategory", base.get("category") or "Metahuman")
    _sub(root, "primaryarm", "Right")
    # The metatype's rates, not the metavariant's. A metavariant inherits
    # them in Chummer's own saves (a Minotaur sprints at the Troll's 1/1/0),
    # while this app's metavariant rows carry a generic 2/1/0 that no save
    # agrees with.
    for tag in ("walk", "run", "sprint"):
        rate = base.get(tag) or own.get(tag)
        if rate:
            _sub(root, tag, rate)
    _sub(root, "magenabled", _flag("MAG" in tabs))
    _sub(root, "resenabled", _flag("RES" in tabs))
    _sub(root, "depenabled", _flag("DEP" in tabs))
    _sub(root, "adept", _flag("adept" in tabs))
    _sub(root, "magician", _flag("magician" in tabs))
    _sub(root, "technomancer", _flag("technomancer" in tabs))
    # Chummer turns this on from an `<enabletab>` the metatype carries, which
    # this app does not apply to metatypes yet: its one shapeshifter test save
    # says True where this says False. Written all the same, so it follows
    # `enabled_tabs` the day it does.
    _sub(root, "critter", _flag("critter" in tabs))
    _sub(root, "initiategrade", int(derived.get("initiate_grade") or 0))
    _sub(root, "submersiongrade", int(derived.get("submersion_grade") or 0))
    if tabs & {"MAG", "RES", "DEP"}:
        # The essence the special attribute was granted at. This app has no
        # way to start a character below 6, so that is what it always is —
        # and a mundane character has no such moment, which Chummer's own
        # loader fills in for itself.
        _sub(root, "essenceatspecialstart", 6)
    _sub(root, "prototypetranshuman", int(derived.get("prototype_transhuman_ess") or 0))
    _sub(root, "cfplimit", int((derived.get("complex_form_points") or {}).get("free") or 0))
    # `<publicawareness>` is left out on purpose. Chummer keeps it as a
    # counter a GM moves and stores what it is told; this app works it out
    # from street cred and notoriety instead, and the two do not agree in
    # either direction in Chummer's own saves (`Serpent` stores 3 where this
    # computes 0, `Popstar` stores 0 where this computes 3). Writing a
    # computed figure into a stored field would make one of them up. It needs
    # a field of its own on the import side first.


def _export_attributes(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write each attribute as Chummer's base/karma pair, relative to the metatype minimum."""
    m_attr = ctx["meta_attrs"]
    attrs = _sub(root, "attributes")
    for key in _ATTR_ORDER:
        spec = m_attr.get(key) or {}
        lo = int(spec.get("min", 0 if key in ("MAG", "RES", "DEP") else 1))
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
    # The engine keeps a listed skill's type only when it was changed, so the
    # list is where an unchanged one's type comes from.
    # Street is what the engine takes a typeless unlisted one for.
    knowledge_cats = {str(row["name"]): str(row.get("category") or "") for row in data.get("knowledge") or []}
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
        category = state.knowledge_categories.get(name) or knowledge_cats.get(name) or "Street"
        knowledge(name, category, rating - karma, karma, False)

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
