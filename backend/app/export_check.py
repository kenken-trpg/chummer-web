"""What a character loses on the way out of this app and back in.

Every export this app has is lossier than the character it writes: a .chum5
cannot hold what Chummer has no field for, and the Japanese character-sheet
template is a fixed grid with one free-text column for all the equipment. The
honest way to say what a given file would cost is not a table of rules but the
round trip itself — write it, read it back, compute both, and report what
changed.

So this holds the comparison, and each export's own `check` module supplies the
two characters. What it reports is a section's worth of rows at a time, because
the rows' instance ids are new on every import and the catalog names are the
front end's to translate.
"""

from __future__ import annotations

import collections
from typing import Any

from .models import CharacterState
from .notices import Notice, notice, ui

#: Fields that say nothing about the character: identity, bookkeeping, and the
#: computed block (checked separately, by the two totals a player reads).
_SKIP = frozenset(
    {"id", "name", "derived", "portrait", "extra_portraits", "created_at", "updated_at", "career_baseline"}
)

#: Which UI label a field is reported under. Anything unlisted is "other".
_KIND = {
    "attributes": "attribute",
    "attribute_karma": "attribute",
    "skills": "skill",
    "skill_karma": "skill",
    "skill_groups": "skill",
    "skill_group_karma": "skill",
    "skill_specializations": "skill",
    "skill_specs_karma": "skill",
    "exotic_skills": "skill",
    "skill_picks": "skill",
    "knowledge_skills": "knowledgeSkill",
    "knowledge_categories": "knowledgeSkill",
    "native_languages": "knowledgeSkill",
    "quality_ids": "quality",
    "quality_extras": "quality",
    "cyberware": "cyberware",
    "bioware": "bioware",
    "adept_powers": "adeptPower",
    "adept_enhancements": "enhancement",
    "mentor_id": "mentor",
    "mentor_choices": "mentor",
    "mentor_extras": "mentor",
    "spells": "spell",
    "spirits": "spirit",
    "complex_forms": "complexForm",
    "sprites": "sprite",
    "foci": "focus",
    "qi_foci": "focus",
    "armor": "armor",
    "armor_mods": "armorMod",
    "weapons": "weapon",
    "weapon_accessories": "weaponAccessory",
    "weapon_mounts": "weaponMount",
    "drones": "drone",
    "vehicles": "vehicle",
    "vehicle_mods": "vehicleMod",
    "lifestyles": "lifestyle",
    "contacts": "contact",
    "martial_arts": "martialArt",
    "initiations": "metamagic",
}


#: Row fields that point at another row by its instance id. They stay as
#: "has one", because the id they point at is new too.
_LINKS = frozenset({"parent_id", "weapon_install_id", "loaded_ammo_id"})


def _row(value: Any) -> Any:
    """A row with its instance ids dropped."""
    if isinstance(value, dict):
        return tuple(sorted((k, bool(v) if k in _LINKS else _row(v)) for k, v in value.items() if k != "id"))
    if isinstance(value, list):
        return tuple(_row(v) for v in value)
    return value


def _field_changes(field: str, before: Any, after: Any) -> tuple[int, int] | None:
    """(lost, gained) for a list field, (0, 0) for any other kind of change,
    None when the field survived."""
    if field == "knowledge_categories" and isinstance(before, dict):
        # The importer files every knowledge skill under a category; one the
        # app never categorised comes back as Street. Only a change counts.
        after = {k: v for k, v in (after or {}).items() if k in before}
    if isinstance(before, list) and isinstance(after, list):
        a, b = collections.Counter(map(_row, before)), collections.Counter(map(_row, after))
        if a == b:
            return None
        return sum((a - b).values()), sum((b - a).values())
    return None if before == after else (0, 0)


def differences(first: CharacterState, again: CharacterState) -> list[Notice]:
    """What `again` — `first` written out and read back — came back missing.

    Empty when the character survived the round trip whole.
    """
    before, after = first.model_dump(), again.model_dump()

    by_kind: dict[str, list[int]] = {}
    for field, value in before.items():
        if field in _SKIP:
            continue
        change = _field_changes(field, value, after.get(field))
        if change is None:
            continue
        tally = by_kind.setdefault(_KIND.get(field, "other"), [0, 0, 0])
        tally[0] += change[0]
        tally[1] += change[1]
        tally[2] += change == (0, 0)

    out: list[Notice] = []
    for kind, (lost, gained, changed) in by_kind.items():
        label = ui(f"engine.kind.{kind}")
        if lost:
            out.append(notice("engine.export.lost", kind=label, count=lost))
        if gained:
            out.append(notice("engine.export.gained", kind=label, count=gained))
        if changed and not (lost or gained):
            out.append(notice("engine.export.changed", kind=label))

    karma = ((first.derived.get("karma") or {}).get("remaining"), (again.derived.get("karma") or {}).get("remaining"))
    if karma[0] != karma[1]:
        out.append(notice("engine.export.karma", before=karma[0] or 0, after=karma[1] or 0))
    nuyen = (first.derived.get("nuyen"), again.derived.get("nuyen"))
    if nuyen[0] != nuyen[1]:
        out.append(notice("engine.export.nuyen", before=nuyen[0] or 0, after=nuyen[1] or 0))
    return out
