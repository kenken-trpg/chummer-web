"""What a character loses on the way through a .chum5.

Writes the character out, reads the file back with this app's own importer,
and lists what came back different — a whole section's worth of rows at a
time, since the rows' ids are new on every import and the catalog names are
the front end's to translate. Most of what Chummer.exe itself would make of
the file is `scripts/chum5_reconcile.py --fidelity`'s job; what this catches
is the half of the round trip this app owns, plus the one thing every file
loses in Chummer — the settings, which Chummer keeps in its own settings file
rather than in the character (`chummer_settings_losses`).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from ..characters import import_character
from ..chummer_import import chum5_to_state
from ..data_loader._xml import parse_untrusted
from ..export_check import differences
from ..models import CharacterState
from ..notices import Notice, notice
from ..rules import rules_for
from . import state_to_chum5
from .build import chummer_settings_preset


def roundtrip_differences(state: CharacterState) -> list[Notice]:
    """What the character would look like after an export and a re-import,
    as notices. Empty when it comes back the same."""
    first = import_character(state.model_dump())
    again = import_character(chum5_to_state(state_to_chum5(first))[0])
    return _app_differences(first, again) + chummer_settings_losses(again)


def _app_differences(first: CharacterState, again: CharacterState) -> list[Notice]:
    """What this app's own writer and reader lose between them."""
    if first.build_method == "LifeModule":
        return [notice("engine.export.chum5LifeModuleSetup")] + differences(first, again)
    growth = int(first.derived.get("career_advancement_karma") or 0) - int(
        again.derived.get("career_advancement_karma") or 0
    )
    # Chummer stores current ratings and the balance, not this app's original
    # baseline. Name the verified accounting conversion instead of calling its
    # adjustment an unspecified "other" change. Any mismatch still goes through
    # the ordinary comparison, including an actual change to the balance.
    if (
        first.career
        and again.career
        and growth > 0
        and again.karma_adjust == first.karma_adjust - growth
        and (first.derived.get("karma") or {}).get("remaining") == (again.derived.get("karma") or {}).get("remaining")
    ):
        return [notice("engine.export.chum5CareerBaseline", amount=growth)] + differences(
            first, again, skip=frozenset({"karma_adjust"})
        )
    return differences(first, again)


def _as_chummer_saves_it(xml: bytes, preset: dict) -> bytes:
    """`xml` as Chummer 5.226 writes it back after opening it under `preset`.

    Chummer keeps the rules, the books and the availability limit in the
    settings file, not in the character: `Character.Save` writes the
    settings' own books as `<sources>` (`Settings.Books`), and no
    `<gameplayoption>` or `<maxavail>`. At creation it also cuts the karma
    spent on nuyen to the settings' cap on load. Verified on a real Chummer
    with six characters (2026-11-04).
    """
    root = parse_untrusted(xml)
    for tag in ("gameplayoption", "maxavail", "sources"):
        for node in root.findall(tag):
            root.remove(node)
    sources = ET.SubElement(root, "sources")
    for code in preset.get("books") or []:
        ET.SubElement(sources, "source").text = code
    nuyen_bp = root.find("nuyenbp")
    created = (root.findtext("created") or "").lower() == "true"
    if nuyen_bp is not None and not created:
        cap = int(preset.get("nuyen_max_bp") or 10)
        nuyen_bp.text = str(min(int(nuyen_bp.text or 0), cap))
    return ET.tostring(root)


def chummer_settings_losses(state: CharacterState) -> list[Notice]:
    """What opening the file in Chummer and saving it again changes, because
    Chummer holds the character to the shipped preset `<settings>` names
    rather than to the settings it carries: that preset's name, books,
    availability limit and rules. Empty when they are the character's own.

    `state` is the character as this app reads its own export back, so what
    is reported here is Chummer's half alone."""
    preset = chummer_settings_preset(state)
    if preset is None:
        return []
    back = import_character(chum5_to_state(_as_chummer_saves_it(state_to_chum5(state), preset))[0])
    before, after = state.settings, back.settings
    out: list[Notice] = []
    rules, kept = rules_for(before), rules_for(after)
    # the keys spelled out, so the orphaned-key check can see them emitted
    for key, field in (
        ("engine.export.chum5QualityCap", "quality_karma_cap_positive"),
        ("engine.export.chum5AvailMax", "chargen_avail_max"),
        ("engine.export.chum5NuyenCap", "priority_karma_nuyen_base"),
    ):
        if getattr(rules, field) != getattr(kept, field):
            out.append(notice(key, before=getattr(rules, field), after=getattr(kept, field)))
    if rules.priority_table != kept.priority_table:
        out.append(notice("engine.export.chum5PriorityTable", before=rules.priority_table, after=kept.priority_table))
    # The name alone is no loss: Standard built by Sum-to-Ten opens as the
    # Sum-to-Ten preset, which plays the same. Say it with the rules it moves.
    if out and before.name != after.name:
        out.insert(0, notice("engine.export.chum5SettingsAs", before=before.name, after=after.name or ""))
    lost = sorted(set(before.books) - set(after.books))
    if not before.books and after.books:
        out.append(notice("engine.export.chum5BooksAll", books=", ".join(after.books)))
    elif lost:
        out.append(notice("engine.export.chum5Books", lost=", ".join(lost), books=", ".join(after.books)))
    nuyen = (state.derived.get("nuyen"), back.derived.get("nuyen"))
    if nuyen[0] != nuyen[1]:
        out.append(notice("engine.export.chum5Nuyen", before=nuyen[0] or 0, after=nuyen[1] or 0))
    return out
