"""Import a Foundry VTT shadowrun5e (0.34.5) character actor — the JSON its
"Export Data" writes — into this app's ``CharacterState``.

What comes over: identity, attributes, skills, qualities, spells, adept
powers, complex forms, armor (and its mods), weapons (and their accessories),
cyber- and bioware, gear (routed to its bucket: commlinks, decks, programs, ...),
contacts, lifestyles, the tradition and reputation. Items are matched on ``system.importFlags.sourceid``, the
Chummer GUID the system's own importers (Chummer and compendium) write on every
item they make, then on the English name they keep beside it, then on the
display name. What cannot be matched becomes a warning, as with a ``.chum5``.

Foundry keeps no priorities, so the character comes back as a Karma build
already in play (career), its karma and nuyen balance as Foundry had them.
"""

from __future__ import annotations

import json
import uuid
from typing import Any, cast

from ..data_loader import catalog
from ..models._common import clamp_input_ints
from ..models.character import MAX_GRADE
from ..notices import Notice, NoticeError, notice, ui
from ._common import _ATTRIBUTES, _base_name, _d, _l, _num, _paren
from .balance import _import_balance
from .combat import _import_combat
from .gear import _import_gear
from .identity import _plain, _talent
from .life import _import_life
from .magic import _import_items
from .skills import _import_skills

__all__ = ["_base_name", "_paren", "fvtt_to_state", "is_fvtt_actor"]


def fvtt_to_state(payload: dict[str, Any]) -> tuple[dict[str, Any], list[Notice]]:
    """A Foundry character actor in, a `CharacterState` dict plus warnings out."""
    if not is_fvtt_actor(payload):
        raise NoticeError(notice("api.notAnFvttActor"))
    cat = catalog()
    warn: list[Notice] = []
    system = _d(payload.get("system"))
    items = _l(payload.get("items"))
    metatypes = {str(m["name"]).lower(): str(m["name"]) for m in cat["metatypes"]}
    metatype = metatypes.get(str(system.get("metatype") or "").lower())
    if not metatype:
        warn.append(
            notice("engine.import.skippedUnknown", kind=ui("engine.kind.other"), name=str(system.get("metatype")))
        )
    attrs = _d(system.get("attributes"))
    st: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "name": str(payload.get("name") or "Imported Runner"),
        "build_method": "Karma",
        "priorities": {},
        "metatype": metatype or "Human",
        "talent": _talent(system, items),
        "career": True,
        "attributes": {
            key: max(1, _num(_d(attrs.get(fvtt)).get("base"), 1))
            for fvtt, key in _ATTRIBUTES.items()
            if fvtt in attrs and (key not in ("MAG", "RES") or _num(_d(attrs.get(fvtt)).get("base")) > 0)
        },
        "initiate_grade": min(MAX_GRADE, max(0, _num(_d(system.get("magic")).get("initiation")))),
        "submersion_grade": min(MAX_GRADE, max(0, _num(_d(system.get("technomancer")).get("submersion")))),
        "background": _plain(str(_d(system.get("description")).get("value") or "")),
    }
    _import_skills(items, cat, st, warn)
    _import_items(items, cat, st, warn)
    _import_combat(items, cat, st, warn)
    _import_gear(items, st, warn)
    _import_life(system, items, cat, st, warn)
    _import_balance(system, st)

    seen: set[str] = set()
    unique: list[Notice] = []
    for item in warn:
        marker = json.dumps(item, sort_keys=True, ensure_ascii=False)
        if marker not in seen:
            seen.add(marker)
            unique.append(item)
    # as the .chum5 read does: a hand-edited number comes through composed
    # into a rating, and the models refuse one past the cap.
    return cast(dict[str, Any], clamp_input_ints(st)), unique


def is_fvtt_actor(payload: Any) -> bool:
    """A Foundry character actor export: a `system` object and an `items` list."""
    return (
        isinstance(payload, dict)
        and payload.get("type") == "character"
        and isinstance(payload.get("system"), dict)
        and isinstance(payload.get("items"), list)
    )
