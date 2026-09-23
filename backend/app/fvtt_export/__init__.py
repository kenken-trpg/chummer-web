"""Export a CharacterState for Foundry VTT's shadowrun5e system (0.34.5).

Not a Foundry actor: the system ships a Chummer importer ("Chummer/Data
Import", `src/module/apps/itemImport/apps/ActorImporter.ts`) and this writes
what it reads — Chummer's *File > Export > JSON*, the print XML as JSON
(`ActorFile` in `src/module/apps/actorImport/ActorSchema.ts`). Letting the
system build the actor keeps its skill sets, compendium matching and data
model on its side of the line.

That format is the print sheet, not the save: every figure is finished
(`total` beside `base`), so it comes from `derived` rather than from what
the chum5 export writes. Values are strings and flags are "True" / "False",
as Chummer prints them. The field map is `docs/plans/fvtt-export-plan.md`.

Covered so far: the character itself, skills, qualities, contacts,
lifestyles, spells, adept powers, complex forms, armor, cyberware and
bioware, gear, weapons, vehicles and drones (with their mods, what is
stowed in them and the guns on their mounts) and the portraits.

This module holds the entry point and the character block it fills; each
section lives beside it, as on the import side: `skills`, `life`
(qualities, contacts, lifestyles), `magic`, `combat` (armor and weapons),
`gear` (ware and gear) and `vehicles`, over `_common`.
"""

from __future__ import annotations

from typing import Any

from ..engine import compute
from ..models import CharacterState
from ..rules import rules_for, using_rules
from ._common import _flag, _html, _translator
from .combat import _armors, _weapons
from .gear import _gears, _wares
from .life import _contacts, _lifestyles, _qualities
from .magic import _complex_forms, _initiation, _powers, _spells, _tradition
from .skills import _skills
from .vehicles import _vehicle_owners, _vehicles

__all__ = ["state_to_fvtt"]

#: The order Chummer prints them in. ESS is left out: the importer maps only
#: these names to a Foundry attribute and skips the rest.
_ATTRS = ("BOD", "AGI", "REA", "STR", "CHA", "INT", "LOG", "WIL", "EDG", "MAG", "RES")

#: The dice the importer takes back off each pool (it stores only the extra).
_MEAT_DICE, _ASTRAL_DICE = 1, 2


def state_to_fvtt(state: CharacterState, locale: str = "ja") -> dict[str, Any]:
    """A computed character as Chummer's JSON export, one character long.

    `locale` picks the display `name`s: Japanese from the catalog's
    translations, or the English data names. Every `*_english` field stays
    English whatever it is — the importer matches skills and parses keywords
    from them.
    """
    with using_rules(rules_for(state.settings)):
        derived = state.derived or compute(state.model_copy(deep=True)).derived
        character = _character(state, derived, _translator(locale))
    return {"?xml": {"@version": "1.0", "@encoding": "utf-8"}, "characters": {"character": character}}


def _character(state: CharacterState, derived: dict[str, Any], tr: Any) -> dict[str, Any]:
    tabs = set(derived.get("enabled_tabs") or [])
    totals = derived.get("totals") or {}
    init = derived.get("initiative") or {}
    astral = derived.get("astral_initiative") or {}
    karma = derived.get("karma") or {}
    owners = _vehicle_owners(state, derived)
    return {
        "name": state.name,
        "alias": None,
        "metatype": tr(state.metatype),
        "metatype_english": state.metatype,
        "metavariant": tr(state.metavariant) if state.metavariant else None,
        "metavariant_english": state.metavariant or None,
        "gender": state.sex or None,
        "age": state.age or None,
        "eyes": state.eyes or None,
        "height": state.height or None,
        "weight": state.weight or None,
        "skin": state.skin or None,
        "hair": state.hair or None,
        "description": _html(state.appearance),
        "background": _html(state.background),
        "concept": _html(state.concept),
        "notes": _html(state.notes),
        "karma": str(int(karma.get("remaining") or 0)),
        "totalkarma": str(int(derived.get("karma_earned") or 0)),
        "nuyen": str(int(derived.get("nuyen") or 0)),
        "calculatedstreetcred": str(int(derived.get("street_cred") or 0)),
        "calculatednotoriety": str(int(derived.get("notoriety") or 0)),
        "calculatedpublicawareness": str(int(derived.get("public_awareness") or 0)),
        "adept": _flag("adept" in tabs),
        "magician": _flag("magician" in tabs),
        "technomancer": _flag("technomancer" in tabs),
        "critter": "False",
        "tradition": _tradition(derived),
        "initiationgrade": _initiation(derived),
        "attributes": [None, {"attributecategory_english": "Standard", "attribute": _attributes(state, totals, tr)}],
        # The importer reads these as the part above the base: Chummer's
        # `initbonus` is the flat bonus over REA + INT, and each `*initdice`
        # the whole pool, from which it takes the rules' own dice back off.
        "initbonus": str(int(init.get("value") or 0) - int(totals.get("REA") or 0) - int(totals.get("INT") or 0)),
        "initdice": str(int(init.get("dice") or _MEAT_DICE)),
        "astralinitdice": str(int(astral.get("dice") or _ASTRAL_DICE)) if astral else None,
        "skills": _skills(state, derived, tr),
        "qualities": {"quality": _qualities(derived, tr)},
        "contacts": {"contact": _contacts(derived)},
        "lifestyles": {"lifestyle": _lifestyles(derived, tr)},
        "spells": {"spell": _spells(derived, tr)},
        "powers": {"power": _powers(derived, tr)},
        "complexforms": {"complexform": _complex_forms(derived, tr)},
        "armors": {"armor": _armors(derived, tr)},
        "cyberwares": {"cyberware": _wares(derived, tr)},
        "gears": {"gear": _gears(derived, tr, owners)},
        "weapons": {"weapon": _weapons(derived, tr, owners)},
        "vehicles": {"vehicle": _vehicles(derived, tr, owners)},
        **_mugshots(state),
    }


def _attributes(state: CharacterState, totals: dict[str, Any], tr: Any) -> list[dict[str, str]]:
    """`base` unaugmented, `total` finished. The importer sets the base and
    then covers any gap to the total with one ActiveEffect."""
    rows = []
    for key in _ATTRS:
        base = int(state.attributes.get(key) or 0)
        total = int(totals.get(key, base) or 0)
        if key in ("MAG", "RES") and not base and not total:
            continue
        rows.append({"name_english": key, "name": key, "base": str(base), "total": str(total)})
    return rows


def _mugshots(state: CharacterState) -> dict[str, Any]:
    """The portraits as bare base64, the main one apart. The importer uploads
    them into the world and makes the first the actor's image (it names them
    .jpg whatever they are; browsers go by the bytes)."""
    pics = [pic.split(",", 1)[-1] for pic in (state.portrait, *state.extra_portraits) if pic]
    if not pics:
        return {}
    out: dict[str, Any] = {"mainmugshotbase64": pics[0]}
    if pics[1:]:
        out["othermugshots"] = {"mugshot": [{"stringbase64": pic} for pic in pics[1:]]}
    return out
