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

Covered so far: the character itself, skills and qualities. Items (gear,
weapons, spells, ...) are sections the importer skips when absent.
"""

from __future__ import annotations

import html
from typing import Any

from ..data_loader import catalog
from ..engine import compute
from ..models import CharacterState
from ..rules import rules_for, using_rules

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


def _translator(locale: str) -> Any:
    """English data name -> display name, the backend twin of the frontend's
    `makeTr` / `scopeTr`: a per-kind table first, then the flat one."""
    if locale != "ja":
        return lambda name, *kinds: name
    cat = catalog()
    flat = cat.get("translations") or {}
    by_kind = cat.get("translations_by_kind") or {}

    def tr(name: str, *kinds: str) -> str:
        for kind in kinds:
            hit = (by_kind.get(kind) or {}).get(name)
            if hit:
                return hit
        return flat.get(name) or name

    return tr


def _flag(on: object) -> str:
    return "True" if on else "False"


def _html(text: str | None) -> str | None:
    """Plain text as the HTML the importer expects (Chummer prints rich text):
    escaped, one paragraph per blank-line block, line breaks kept."""
    if not text or not text.strip():
        return None
    blocks = [b for b in text.replace("\r\n", "\n").split("\n\n") if b.strip()]
    return "".join(f"<p>{html.escape(b.strip()).replace(chr(10), '<br/>')}</p>" for b in blocks)


def _character(state: CharacterState, derived: dict[str, Any], tr: Any) -> dict[str, Any]:
    tabs = set(derived.get("enabled_tabs") or [])
    totals = derived.get("totals") or {}
    init = derived.get("initiative") or {}
    astral = derived.get("astral_initiative") or {}
    karma = derived.get("karma") or {}
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


def _tradition(derived: dict[str, Any]) -> dict[str, str] | None:
    """The drain attributes are all the importer takes: the one that is not
    WIL becomes the magic attribute."""
    trad = derived.get("tradition") or {}
    attrs = [str(a) for a in trad.get("drain_attrs") or []]
    if not attrs:
        return None
    drain = " + ".join(attrs)
    return {
        "sourceid": str(trad.get("id") or ""),
        "name": str(trad.get("name") or ""),
        "name_english": str(trad.get("name") or ""),
        "drainattributes": drain,
        "drainattributes_english": drain,
    }


def _initiation(derived: dict[str, Any]) -> dict[str, list[dict[str, str]]] | None:
    """One row per grade kind; the importer keeps the highest of each."""
    rows = [
        {"grade": str(grade), "technomancer": techno}
        for grade, techno in (
            (int(derived.get("initiate_grade") or 0), "False"),
            (int(derived.get("submersion_grade") or 0), "True"),
        )
        if grade
    ]
    return {"initiationgrade": rows} if rows else None


def _skills(state: CharacterState, derived: dict[str, Any], tr: Any) -> dict[str, list[dict[str, Any]]]:
    """Active skills matched by `name_english` (so it must be the data name),
    knowledge and language skills by `name`, groups by `name_english`.

    Only skills with a rating: the importer lays the system's default skill
    set down first, so an unrated skill is already there.
    """
    data = catalog()["skills"]
    active_rows = {str(r["name"]): r for r in data.get("skills") or []}
    specs = derived.get("skill_specializations") or {}
    out: list[dict[str, Any]] = []

    for name, rating in sorted((derived.get("skill_totals") or {}).items()):
        row = active_rows.get(name)
        if row is None or int(rating or 0) <= 0:
            continue
        out.append(
            {
                "suid": str(row.get("id") or ""),
                "name": tr(name, "skill"),
                "name_english": name,
                "skillgroup_english": str(row.get("skillgroup") or ""),
                "skillcategory_english": str(row.get("category") or ""),
                "attribute": str(row.get("attribute") or ""),
                "default": _flag(row.get("default")),
                "rating": str(int(rating)),
                "knowledge": "False",
                "islanguage": "False",
                "isnativelanguage": "False",
                "skillspecializations": _specs(specs.get(name), tr),
            }
        )

    for exotic in derived.get("exotic_skills") or []:
        name = str(exotic.get("skill_name") or exotic.get("name") or "")
        row = active_rows.get(name)
        if row is None or int(exotic.get("rating") or 0) <= 0:
            continue
        # One skill per weapon: the weapon rides along as the specialization,
        # which is where a Foundry exotic skill keeps it.
        out.append(
            {
                "suid": str(row.get("id") or ""),
                "name": tr(name, "skill"),
                "name_english": name,
                "skillgroup_english": "",
                "skillcategory_english": str(row.get("category") or ""),
                "attribute": str(row.get("attribute") or ""),
                "default": _flag(row.get("default")),
                "rating": str(int(exotic.get("rating") or 0)),
                "knowledge": "False",
                "islanguage": "False",
                "isnativelanguage": "False",
                "skillspecializations": _specs(exotic.get("extra"), tr),
            }
        )

    for row in derived.get("knowledge_skills") or []:
        name = str(row.get("name") or "")
        category = str(row.get("category") or "")
        language = category == "Language"
        native = bool(row.get("native"))
        if not name or (not native and int(row.get("rating") or 0) <= 0):
            continue
        out.append(
            {
                "name": tr(name, "knowledge_skill"),
                "name_english": name,
                "skillcategory_english": category,
                "attribute": str(row.get("attribute") or ""),
                "rating": str(int(row.get("rating") or 0)),
                "knowledge": "True",
                "islanguage": _flag(language),
                "isnativelanguage": _flag(native),
                "skillspecializations": _specs(specs.get(name), tr),
            }
        )

    groups = [
        {"name": tr(name), "name_english": name, "rating": str(int(rating)), "isbroken": "False"}
        for name, rating in sorted(state.skill_groups.items())
        if int(rating or 0) > 0
    ]
    return {"skill": out, "skillgroup": groups}


def _specs(spec: str | None, tr: Any) -> dict[str, list[dict[str, str]]] | None:
    if not spec:
        return None
    return {"skillspecialization": [{"name": tr(spec), "name_english": spec}]}


def _qualities(derived: dict[str, Any], tr: Any) -> list[dict[str, str]]:
    """The importer takes `bp` as the karma per level and `extra` as the
    rating, so a chosen extra that is text (Allergy's allergen) reads as 0."""
    out = []
    for row in derived.get("qualities") or []:
        name = str(row.get("name") or "")
        if not name:
            continue
        extra = str(row.get("extra") or "")
        out.append(
            {
                "sourceid": str(row.get("id") or ""),
                "name": tr(name),
                "name_english": name,
                "extra": extra or None,
                "qualitytype_english": str(row.get("category") or "Positive"),
                "bp": str(int(row.get("karma") or 0)),
                "source": str(row.get("source") or ""),
                "page": str(row.get("page") or ""),
            }
        )
    return out
