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
from ..engine import compute, find_metatype
from ..models import CharacterState
from ..rules import rules_for, using_rules
from ._common import _Ctx, _id_name
from .ai_programs import _export_ai_programs
from .build import _export_build_points, _export_flags, _export_priorities
from .gear import _export_armor, _export_foci, _export_gear, _export_vehicles, _export_ware, _export_weapons
from .identity import _export_attributes, _export_contacts, _export_identity
from .life_modules import _export_life_module_choices
from .lifestyles import _export_custom_drugs, _export_lifestyles
from .magic import (
    _export_enhancements,
    _export_free_power_rows,
    _export_initiation,
    _export_magic_tradition,
    _export_spell_lists,
    _export_spirits,
)
from .qualities import _export_martial_arts, _export_qualities
from .skills import _export_skills

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
    with using_rules(rules_for(state.settings)):
        return _write(state)


def _write(state: CharacterState) -> bytes:
    """`state_to_chum5` with the character's own settings in scope.

    The priority table a letter is read against, and the karma and nuyen
    figures Chummer scores a settings file by, both come from the settings —
    so the sections below need them bound the way `compute()` binds them.
    """
    if state.build_method == "LifeModule" and state.life_module_rules_version == 2:
        state = compute(state)
    cat = catalog()
    meta = find_metatype(state.metatype, state.metavariant) or {"attributes": {}}
    m_attr = meta.get("attributes") or {}
    # Several sections write a figure the engine already worked out. An export
    # is handed a computed character (the docstring above), so this is that
    # bundle; computing it is the fallback for a state built by hand.
    derived = state.derived or compute(state.model_copy(deep=True)).derived

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

    ctx: _Ctx = {"meta_attrs": m_attr, "derived": derived, "meta": meta}
    for section in _SECTIONS:
        if section is _export_skills and state.build_method == "LifeModule" and state.life_module_rules_version == 2:
            projection = state.model_copy(deep=True)
            active_names = {s["name"] for s in cat["skills"]["skills"] if not s.get("exotic")}
            projection.skills = {
                name: rating for name, rating in derived["skill_totals"].items() if name in active_names
            }
            projection.skill_groups = {}
            from ..models import ExoticSkillInstall

            projection.exotic_skills = [
                ExoticSkillInstall(**{k: row[k] for k in ("id", "skill_name", "extra", "rating")})
                for row in derived.get("exotic_skills") or []
            ]
            projection.knowledge_skills = {
                row["name"]: row["rating"] for row in derived.get("knowledge_skills") or [] if not row.get("native")
            }
            projection.native_languages = [
                row["name"] for row in derived.get("knowledge_skills") or [] if row.get("native")
            ]
            section(root, projection, names, ctx)
        else:
            section(root, state, names, ctx)

    xml = ET.tostring(root, encoding="utf-8")
    # our own serialisation, not input
    return minidom.parseString(xml).toprettyxml(indent="  ", encoding="utf-8")  # noqa: S318


#: Written in this order, which is the order Chummer's own files use. Nothing
#: here reads what an earlier section wrote — the order is for the reader (and
#: for a diff against a real .chum5), not for correctness — but the last: the
#: power rows free levels land on, which every section's improvements name.
_SECTIONS = (
    _export_identity,
    _export_priorities,
    _export_build_points,
    _export_flags,
    _export_attributes,
    _export_skills,
    _export_qualities,
    _export_spell_lists,
    _export_ai_programs,
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
    _export_life_module_choices,
    _export_free_power_rows,
)
