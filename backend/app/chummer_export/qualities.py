"""Qualities, what they grant, and martial arts.

The mirror of :mod:`app.chummer_import.qualities`.
"""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from typing import Any

from ..data_loader import catalog
from ..engine.constants import (
    QUALITY_ADDSPIRIT_EXTRA_MARKER,
    quality_contact_extra_key,
    quality_optional_power_extra_key,
    quality_spirit_category_extra_key,
)
from ..engine.lookups import critter_power_label
from ..engine.qualities import _quality_needs_spell_category, _quality_needs_spirit_category
from ..models import CharacterState
from ._common import _Ctx, _Names, _sub, improvements_of


def _export_qualities(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write qualities, spells, adept powers and complex forms."""
    quals = _sub(root, "qualities")
    specs = {str(row["id"]): row for row in catalog()["qualities"]}
    ids_by_name = {str(row["name"]): str(row["id"]) for row in catalog()["qualities"]}
    spell_limits: list[tuple[str, str]] = []
    granted: list[tuple[str, str]] = []  # (granting quality id, granted quality's guid)
    for qid in state.quality_ids:
        q = _sub(quals, "quality")
        _sub(q, "sourceid", qid)
        _sub(q, "name", names["quality"].get(qid, ""))
        extra, spell_category = _quality_extra_out(
            specs.get(qid) or {}, qid, state.quality_extras, {c.id: c.name for c in state.contacts}
        )
        if spell_category:
            _sub(q, "guid", qid)
            spell_limits.append((qid, spell_category))
        _sub(q, "extra", extra)
        _sub(q, "qualitysource", "Selected")
        # A quality with a `<selectskill>` bonus carries the skill picked for
        # it. Unlike the implant picks in `_export_ware`, these are keyed by
        # the quality's catalog id, which survives an import unchanged.
        prefix = f"quality:{qid}:"
        picks = sorted(
            (key[len(prefix) :], value) for key, value in state.skill_picks.items() if key.startswith(prefix)
        )
        if picks:
            picks_el = _sub(q, "skillpicks")
            for index, skill in picks:
                pick = _sub(picks_el, "pick")
                _sub(pick, "index", index)
                _sub(pick, "skill", skill)
        # `<selectquality>` (Prototype Transhuman): Chummer adds the pick as a
        # quality of its own, sourced from this one, and ties the two with a
        # SpecificQuality improvement so removing this one removes the pick.
        picked = state.quality_extras.get(qid, "")
        if str((specs.get(qid) or {}).get("extra_kind") or "") == "quality" and picked in ids_by_name:
            if q.find("guid") is None:
                _sub(q, "guid", qid)
            child_guid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{qid}:selectquality"))
            child_id = ids_by_name[picked]
            child = _sub(quals, "quality")
            _sub(child, "guid", child_guid)
            _sub(child, "sourceid", child_id)
            _sub(child, "name", picked)
            _sub(child, "extra", state.quality_extras.get(child_id, ""))
            _sub(child, "qualitysource", "Improvement")
            _sub(child, "sourcename", names["quality"].get(qid, ""))
            granted.append((qid, child_guid))
        # a contact the quality added (Made Man): Chummer ties it to the
        # quality with an AddContact improvement, which the import follows back
        if any(c.source_quality_id == qid for c in state.contacts) and q.find("guid") is None:
            _sub(q, "guid", qid)

    _export_quality_critter_powers(root, state)
    # Chummer keeps a picked spell category only on the improvement
    # `<limitspellcategory />` made, tied to the quality by its guid
    links = [(category, qid, "LimitSpellCategory") for qid, category in spell_limits]
    links += [(child_guid, qid, "SpecificQuality") for qid, child_guid in granted]
    links += [(c.id, c.source_quality_id, "AddContact") for c in state.contacts if c.source_quality_id]
    if links:
        imps = improvements_of(root)
        for improved, qid, kind in links:
            imp = _sub(imps, "improvement")
            _sub(imp, "improvedname", improved)
            _sub(imp, "sourcename", qid)
            _sub(imp, "improvementttype", kind)
            _sub(imp, "improvementsource", "Quality")


def _export_quality_critter_powers(root: ET.Element, state: CharacterState) -> None:
    """`<critterpowers>`: what an Infected quality grants, plus its one
    optional power — where Chummer's `critterpowers` / `optionalpowers`
    improvements put them (`grade` −1 marks a power a quality gave). The
    optional pick has nowhere else to live in a `.chum5`, so without this it
    is lost on the way out."""
    by_id = {str(row["id"]): row for row in catalog()["qualities"]}
    power_ids = {str(row.get("name") or ""): str(row.get("id") or "") for row in catalog().get("critter_powers") or []}
    refs: list[dict[str, Any]] = []
    for qid in state.quality_ids:
        spec = by_id.get(qid) or {}
        refs.extend(spec.get("critter_powers") or [])
        picked = state.quality_extras.get(quality_optional_power_extra_key(qid), "")
        refs.extend(row for row in spec.get("optional_powers") or [] if critter_power_label(row) == picked)
    if not refs:
        return
    powers = _sub(root, "critterpowers")
    for ref in refs:
        el = _sub(powers, "critterpower")
        _sub(el, "sourceid", power_ids.get(str(ref["name"]), ""))
        _sub(el, "name", ref["name"])
        _sub(el, "extra", ref.get("select") or "")
        _sub(el, "rating", ref.get("rating") or 0)
        _sub(el, "grade", -1)


def _quality_extra_out(
    spec: dict[str, Any], qid: str, extras: dict[str, str], contact_names: dict[str, str]
) -> tuple[str, str]:
    """A quality's `<extra>` as Chummer writes it, and a spell category that
    has to go on an improvement instead.

    Chummer's `AddSpiritOrSprite` appends every spirit it is given to the
    quality's selected value, `, `-joined: Chain Breaker's two `<addspirit>`
    picks, or Apprentice's `<limitspiritcategory>` spirit — whose
    `<limitspellcategory>` pick is not added, so it rides an improvement.
    `<selectcontact>` appends the contact's name the same way, after Black
    Market Pipeline's category.
    """
    if str(spec.get("extra_kind") or "") == "add_spirit":
        marker = f"{qid}{QUALITY_ADDSPIRIT_EXTRA_MARKER}"
        picks = sorted(
            (int(key[len(marker) :]), value)
            for key, value in extras.items()
            if key.startswith(marker) and key[len(marker) :].isdigit() and value
        )
        return ", ".join(value for _, value in picks), ""
    if _quality_needs_spirit_category(spec) and _quality_needs_spell_category(spec):
        return extras.get(quality_spirit_category_extra_key(qid), ""), extras.get(qid, "")
    if str(spec.get("extra_kind") or "") == "quality":
        # the pick is a quality of its own; see `_export_qualities`
        return "", ""
    if _quality_selects_contact(spec):
        contact = contact_names.get(extras.get(quality_contact_extra_key(qid), ""), "")
        return ", ".join(part for part in (extras.get(qid, ""), contact) if part), ""
    return extras.get(qid, ""), ""


def _quality_selects_contact(spec: dict[str, Any]) -> bool:
    return any(node.get("tag") == "selectcontact" for node in spec.get("bonus") or [])


def _export_martial_arts(root: ET.Element, state: CharacterState, names: _Names, ctx: _Ctx) -> None:
    """Write martial arts and their techniques."""
    marts = _sub(root, "martialarts")
    for row in state.martial_arts:
        el = _sub(marts, "martialart")
        _sub(el, "sourceid", row.art_id)
        _sub(el, "name", names["martialart"].get(row.art_id, ""))
        techs = _sub(el, "martialarttechniques")
        for tn in row.techniques:
            _sub(_sub(techs, "martialarttechnique"), "name", tn)
