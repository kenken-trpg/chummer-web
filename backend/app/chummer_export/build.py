"""How the character was built: the settings they were built under, the reward
log, the priorities, the build-point budget and the creation flags.

The mirror of :mod:`app.chummer_import.identity`'s build half — what Chummer
needs to reopen the save in the right build method rather than on defaults.
"""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from datetime import datetime

from .. import ja_default
from ..data_loader import catalog
from ..engine import find_metatype
from ..engine.priority import heritage_cost, priority_value
from ..models import CharacterState
from ..rules import current_rules
from ._common import _Ctx, _Names, _sub


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
    if state.build_method == "LifeModule":
        from .life_module_settings import life_module_settings

        key, _ = life_module_settings(state)
        _sub(root, "settings", key)
        _sub(root, "gameplayoption", settings.name)
        sources = _sub(root, "sources")
        for code in settings.books or [book["code"] for book in catalog()["books"]]:
            _sub(sources, "source", code)
        return
    if not settings.name:
        return
    presets = catalog().get("settings_presets") or []
    # 日本語環境 is this app's own preset, which no Chummer has: point it at
    # Standard, the shipped preset it builds by, with its books in `<sources>`.
    wanted = "Standard" if settings.name == ja_default.NAME else settings.name
    preset = next((p for p in presets if p.get("name") == wanted), None)
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
    # the talent's free skills by name, beside the Heritage improvements
    # `_export_skills` writes; Chummer lists them here after the talent
    talent_skills = ctx["derived"].get("talent_skills") or {}
    if talent_skills.get("picked") and not talent_skills.get("group"):
        picks = _sub(root, "priorityskills")
        for name in talent_skills["picked"]:
            _sub(picks, "priorityskill", name)


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
