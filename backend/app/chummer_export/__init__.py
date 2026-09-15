"""Export a CharacterState to a Chummer5a-style ``.chum5`` (plain XML).

Not a byte-perfect Chummer save — Chummer recomputes most derived data — but a
structurally compatible ``<character>`` document that Chummer can open and that
round-trips through :func:`app.chummer_import.chum5_to_state`.

Split the same way :mod:`app.chummer_import` is, one module per area, so the
two halves of a round trip sit next to each other.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from xml.dom import minidom

from ..data_loader import catalog
from ..engine import find_metatype
from ..models import CharacterState
from ._common import _Ctx, _id_name
from .gear import _export_armor, _export_foci, _export_gear, _export_vehicles, _export_ware, _export_weapons
from .identity import (
    _export_attributes,
    _export_contacts,
    _export_identity,
    _export_priorities,
    _export_skills,
)
from .lifestyles import _export_custom_drugs, _export_lifestyles
from .magic import (
    _export_enhancements,
    _export_initiation,
    _export_magic_tradition,
    _export_spell_lists,
    _export_spirits,
)
from .qualities import _export_martial_arts, _export_qualities

__all__ = ["state_to_chum5"]


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
    _export_spell_lists,
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
    _export_magic_tradition,
    _export_spirits,
    _export_enhancements,
    _export_initiation,
)
