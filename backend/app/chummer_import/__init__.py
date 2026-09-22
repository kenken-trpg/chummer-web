"""Import a Chummer5a save (``.chum5`` plain XML or ``.chum5lz`` LZMA-compressed)
into this app's ``CharacterState``.

Best-effort: identity / priorities / attributes / skills / qualities / spells /
adept powers / complex forms / martial arts / contacts / lifestyles / tradition /
mentor / initiation, plus id-resolved ware (nested), armor + mods, weapons +
accessories, gear (nested, routed to commlink/deck/sensor/program/… buckets),
vehicles + drones + vehicle mods. Anything the catalog can't resolve is skipped
and named in the returned warning list rather than failing the import.

One module per group of sections (`identity`, `skills`, `balance`,
`qualities`, `magic`, `ware`, `combat`, `gear`, `vehicles`, `lifestyles`), the
`.chum5lz` container in `container`, and the catalog lookups they all share in
`_common`.
"""

from __future__ import annotations

import json
import uuid
import xml.etree.ElementTree as ET  # the Element type only — parsing goes through parse_untrusted
from typing import Any, cast

from ..data_loader import catalog
from ..data_loader._xml import parse_untrusted
from ..models._common import clamp_input_ints
from ..notices import Notice, NoticeError, notice
from .balance import _import_balance
from .combat import _import_armor, _import_weapons
from .container import decompress_chum5lz
from .gear import _import_custom_drugs, _import_gear
from .identity import _import_attributes, _import_identity
from .lifestyles import _import_lifestyles
from .magic import _import_foci, _import_initiation, _import_magic, _import_spirits
from .qualities import _import_qualities
from .skills import _import_skills
from .vehicles import _import_vehicles
from .ware import _import_ware


def chum5_to_state(xml_bytes: bytes) -> tuple[dict[str, Any], list[Notice]]:
    """A Chummer5a save in, a `CharacterState` dict plus warnings out.

    Best-effort by design: anything the catalog cannot resolve becomes a
    warning, never an error, because a character that imports with three
    missing items is worth more to its owner than a refusal.

    Each `_import_*` below owns one section of the file. They are independent —
    each reads `root` and writes into `st` — which is why the 443-line function
    they came from could be cut along its own comment banners without moving a
    single line of logic.
    """
    xml_bytes = decompress_chum5lz(xml_bytes)
    try:
        root: ET.Element = parse_untrusted(xml_bytes)
    except ET.ParseError as exc:
        raise NoticeError(notice("api.xmlUnparsable", error=str(exc))) from exc
    if root.tag != "character":
        nested = root.find("character")
        root = nested if nested is not None else root
    if root.tag != "character":
        raise NoticeError(notice("api.notACharacterFile"))

    cat = catalog()
    warn: list[Notice] = []
    st: dict[str, Any] = {"id": str(uuid.uuid4())}

    for section in _SECTIONS:
        section(root, cat, st, warn)

    # collapse duplicate warnings, keep order. Notices are dicts, so dedupe on
    # a canonical rendering of each rather than on the object itself.
    seen: set[str] = set()
    unique: list[Notice] = []
    for item in warn:
        marker = json.dumps(item, sort_keys=True, ensure_ascii=False)
        if marker not in seen:
            seen.add(marker)
            unique.append(item)
    st["_warnings"] = unique
    # A hand-edited number survives the read composed into a rating or a
    # balance; the models refuse one past the cap, so hold them here.
    st = cast(dict[str, Any], clamp_input_ints(st))
    return st, st["_warnings"]


#: Applied in order. Order matters only where a later section reads what an
#: earlier one wrote into `st` — ware before gear, because a cyberdeck can hang
#: off a cyberlimb.
_SECTIONS = (
    _import_identity,
    _import_attributes,
    _import_skills,
    _import_qualities,
    _import_magic,
    _import_spirits,
    _import_initiation,
    _import_ware,
    _import_armor,
    _import_weapons,
    # vehicles first: `_import_gear` puts what is stowed in them in its buckets
    _import_vehicles,
    _import_gear,
    _import_lifestyles,
    _import_foci,
    _import_custom_drugs,
    # last: reads the whole character to turn a career balance into earnings
    _import_balance,
)

__all__ = ["chum5_to_state", "decompress_chum5lz"]
