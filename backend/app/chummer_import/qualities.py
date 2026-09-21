"""Qualities, and the picks they were taken with."""

from __future__ import annotations

import xml.etree.ElementTree as ET  # the Element type only — parsing goes through parse_untrusted
from typing import Any

from ..data_loader import CatalogDict
from ..data_loader._xml import _text
from ..engine.constants import (
    quality_addspirit_extra_key,
    quality_contact_extra_key,
    quality_optional_power_extra_key,
    quality_spirit_category_extra_key,
)
from ..engine.lookups import critter_power_label
from ..engine.qualities import _quality_needs_spell_category, _quality_needs_spirit_category
from ..notices import Notice, notice, ui
from ._common import _by_name


def _import_qualities(root: ET.Element, cat: CatalogDict, st: dict[str, Any], warn: list[Notice]) -> None:
    """Read positive/negative qualities and the targets they were taken with."""
    q_by_name = _by_name(cat["qualities"])
    q_ids = {r["id"] for r in cat["qualities"]}
    quality_ids: list[str] = []
    quality_extras: dict[str, str] = {}
    picks: dict[str, str] = {}
    for q in root.findall("./qualities/quality"):
        src = _text(q.find("qualitysource")).lower()
        if src and src not in ("selected", "builtin", ""):
            continue  # metatype / life-module grants are re-derived by the engine
        # Chummer writes the data id to `<id>` (`<guid>` is this instance), and
        # this app writes it to `<sourceid>`. The name is the last resort, and a
        # lossy one: "College Education" is two qualities — SASS's is a limit
        # modifier, Run Faster's halves the Academic point cost — and matching
        # by name picked the first for saves that had the second.
        candidates = (_text(q.find("sourceid")), _text(q.find("id")), _text(q.find("guid")))
        qid = next((c for c in candidates if c in q_ids), None) or q_by_name.get(_text(q.find("name")).lower())
        if not qid:
            nm = _text(q.find("name"))
            if nm:
                warn.append(notice("engine.import.skippedUnknown", kind=ui("engine.kind.quality"), name=nm))
            continue
        # every take, not every kind: Chummer saves a quality taken twice
        # (Gremlins at 2, Favored against two targets) as two `<quality>`s,
        # and `quality_ids` holds a repeat the same way
        quality_ids.append(qid)
        extra = _text(q.find("extra"))
        quality_extras.update(_quality_extra_in(cat, qid, extra, _text(q.find("guid")), root))
        for pick in q.findall("./skillpicks/pick"):
            skill = _text(pick.find("skill"))
            if skill:
                picks[f"quality:{qid}:{_text(pick.find('index'))}"] = skill
    _import_selected_qualities(root, cat, quality_ids, quality_extras)
    _import_optional_powers(root, cat, quality_ids, quality_extras)
    st["quality_ids"] = quality_ids
    st["quality_extras"] = quality_extras
    # Merged rather than assigned: `_import_ware` fills in the implant picks,
    # and the two sections run in either order.
    st["skill_picks"] = {**(st.get("skill_picks") or {}), **picks}


def _import_selected_qualities(
    root: ET.Element, cat: CatalogDict, quality_ids: list[str], quality_extras: dict[str, str]
) -> None:
    """A `<selectquality>` pick (Prototype Transhuman's negative quality), back
    out of the quality it granted.

    Chummer leaves the granting quality's `<extra>` empty and adds the pick as
    a quality of its own, `<qualitysource>Improvement</qualitysource>` with the
    granting quality's name as `<sourcename>`. A file this app wrote before
    that has the pick in `<extra>` instead, already read by the caller.
    """
    granted: dict[str, list[str]] = {}
    rows: dict[str, ET.Element] = {}
    for q in root.findall("./qualities/quality"):
        if _text(q.find("qualitysource")).lower() == "improvement":
            granted.setdefault(_text(q.find("sourcename")).lower(), []).append(_text(q.find("name")))
            rows.setdefault(_text(q.find("name")), q)
    by_id = {str(row["id"]): row for row in cat["qualities"]}
    ids_by_name = {str(row["name"]): str(row["id"]) for row in cat["qualities"]}
    for qid in quality_ids:
        spec = by_id.get(qid) or {}
        if str(spec.get("extra_kind") or "") != "quality" or quality_extras.get(qid):
            continue
        options = list(spec.get("select_options") or [])
        # `<sourcename>` is the display name, so a save from a translated
        # Chummer names the granting quality in that language: fall back to
        # any granted quality the pick list allows.
        candidates = granted.get(str(spec["name"]).lower()) or [n for names in granted.values() for n in names]
        picked = next((name for name in candidates if name in options), None)
        if not picked:
            continue
        quality_extras[qid] = picked
        # the pick's own choice — Wanted's who and how much, Allergy's what
        child, child_id = rows[picked], ids_by_name.get(picked)
        if child_id and _text(child.find("extra")):
            quality_extras.update(
                _quality_extra_in(cat, child_id, _text(child.find("extra")), _text(child.find("guid")), root)
            )


def _import_optional_powers(
    root: ET.Element, cat: CatalogDict, quality_ids: list[str], quality_extras: dict[str, str]
) -> None:
    """An Infected quality's optional power, back out of `<critterpowers>`.

    The file lists every power the character has without saying which pick
    it was, so each quality first claims the powers it always grants and then
    the first remaining one on its optional list — by name and `<extra>`,
    because Immunity comes both ways (Grendel is granted Immunity (Toxins)
    and may pick it again).
    """
    pool = [
        critter_power_label({"name": _text(p.find("name")), "select": _text(p.find("extra"))})
        for p in root.findall("./critterpowers/critterpower")
        if _text(p.find("name"))
    ]
    by_id = {str(row["id"]): row for row in cat["qualities"]}
    for qid in quality_ids:
        spec = by_id.get(qid) or {}
        optional = [critter_power_label(row) for row in spec.get("optional_powers") or []]
        if not optional:
            continue
        for row in spec.get("critter_powers") or []:
            label = critter_power_label(row)
            if label in pool:
                pool.remove(label)
        picked = next((label for label in pool if label in optional), None)
        if picked is not None:
            pool.remove(picked)
            quality_extras[quality_optional_power_extra_key(qid)] = picked


def _quality_extra_in(cat: CatalogDict, qid: str, extra: str, guid: str, root: ET.Element) -> dict[str, str]:
    """The mirror of the export's `_quality_extra_out`: a quality's `<extra>`
    back into the keys the engine reads.

    Chain Breaker / Dark Ally: the `, `-joined spirits, one `:addspirit:N`
    slot each. Apprentice: `<extra>` is the spirit and the spell category is
    on the `LimitSpellCategory` improvement carrying the quality's guid — a
    file this app wrote before that has the category in `<extra>` instead,
    told apart by whether the text names a spirit.
    """
    spec = next((row for row in cat["qualities"] if row["id"] == qid), None) or {}
    if any(node.get("tag") == "selectcontact" for node in spec.get("bonus") or []):
        # Black Market Pipeline: `Category, Contact Name`. The name is swapped
        # for the contact's id once `_import_lifestyles` has read the contacts.
        category, _, contact = extra.partition(",")
        picked = {qid: category.strip()} if category.strip() else {}
        if contact.strip():
            picked[quality_contact_extra_key(qid)] = contact.strip()
        return picked
    if str(spec.get("extra_kind") or "") == "add_spirit":
        spirits = [part.strip() for part in extra.split(",") if part.strip()]
        return {quality_addspirit_extra_key(qid, idx): name for idx, name in enumerate(spirits)}
    if _quality_needs_spirit_category(spec) and _quality_needs_spell_category(spec):
        out: dict[str, str] = {}
        category = ""
        if guid:
            for imp in root.findall("./improvements/improvement"):
                if (
                    _text(imp.find("sourcename")) == guid
                    and _text(imp.find("improvementttype")) == "LimitSpellCategory"
                ):
                    category = _text(imp.find("improvedname"))
                    break
        spirit_names = {str(row.get("name") or "") for row in cat.get("spirits") or []}
        if category:
            out[qid] = category
            if extra:
                out[quality_spirit_category_extra_key(qid)] = extra
        elif extra in spirit_names:
            out[quality_spirit_category_extra_key(qid)] = extra
        elif extra:
            out[qid] = extra
        return out
    return {qid: _match_option(spec, extra)} if extra else {}


def _match_option(spec: dict[str, Any], extra: str) -> str:
    """The saved pick, spelled the way this app's option list spells it.

    Chummer stores what its own dropdown held, which is not always the catalog
    entry's name: Spirit Bane is saved as `Man` where the list this app builds
    from the critter data says `Spirit of Man`. Left alone the pick matches
    nothing and the quality is reported as holding an invalid choice. Only an
    exact match after the prefix is accepted — anything looser would quietly
    turn a genuinely unknown pick into a valid one.
    """
    options = [str(item) for item in (spec.get("select_options") or [])]
    if not options or extra in options:
        return extra
    prefixed = f"Spirit of {extra}"
    return prefixed if prefixed in options else extra
