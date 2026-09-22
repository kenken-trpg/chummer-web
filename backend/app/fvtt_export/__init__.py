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
"""

from __future__ import annotations

import html
from typing import Any

from ..data_loader import catalog, catalog_list
from ..engine import compute
from ..engine.gear.weapons.bonuses import weapon_skill_dictionary_key
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


def _fullname(name: str, extra: str) -> str:
    """Chummer's `fullname`, the name the importer shows: the pick in brackets."""
    return f"{name} ({extra})" if extra else name


def _contacts(derived: dict[str, Any]) -> list[dict[str, str]]:
    """Free text on both sides, so nothing to translate. A group contact's
    connection goes out bare: the importer reads a number or `Group(n)` alike."""
    return [
        {
            "guid": str(row.get("id") or ""),
            "name": str(row.get("name") or ""),
            "role": str(row.get("role") or ""),
            "connection": str(int(row.get("connection") or 0)),
            "loyalty": str(int(row.get("loyalty") or 0)),
            "type": "Group" if row.get("group") else "Contact",
            "forcedloyalty": str(int(row.get("forced_loyalty") or 0)),
            "family": "False",
            "blackmail": "False",
        }
        for row in derived.get("contacts") or []
    ]


def _lifestyles(derived: dict[str, Any], tr: Any) -> list[dict[str, str]]:
    """`baselifestyle` lower-cased is the Foundry type ("medium", ...), so it
    stays the data name; the monthly cost is the finished one."""
    out = []
    for row in derived.get("lifestyles") or []:
        base = str(row.get("name") or "")
        out.append(
            {
                "guid": str(row.get("id") or ""),
                "sourceid": str(row.get("lifestyle_id") or ""),
                "name": tr(base),
                "baselifestyle": base,
                "baselifestyle_english": base,
                "totalmonthlycost": str(int(row.get("monthly") or 0)),
                "months": str(int(row.get("months") or 0)),
                "increment": str(row.get("increment") or "month"),
                "purchased": "False",
                "source": str(row.get("source") or ""),
                "page": str(row.get("page") or ""),
            }
        )
    return out


def _spells(derived: dict[str, Any], tr: Any) -> list[dict[str, str]]:
    """Every keyword field in its `_english` twin: the importer parses the
    category, range, duration, DV and descriptors from them (and calls
    string methods on them, so none may be missing). "Rituals" become
    Foundry rituals; alchemical ones it skips."""
    out = []
    for row in derived.get("spells") or []:
        name = str(row.get("name") or "")
        if not name:
            continue
        fields = {
            "category": str(row.get("category") or ""),
            "type": str(row.get("type") or ""),
            "range": str(row.get("range") or ""),
            "duration": str(row.get("duration") or ""),
            "dv": str(row.get("dv") or ""),
            "damage": str(row.get("damage") or ""),
            "descriptors": str(row.get("descriptor") or ""),
        }
        out.append(
            {
                "guid": str(row.get("id") or ""),
                "sourceid": str(row.get("spell_id") or ""),
                "name": tr(name),
                "name_english": name,
                **fields,
                **{f"{key}_english": value for key, value in fields.items()},
                "alchemy": _flag(row.get("alchemical")),
                "barehandedadept": _flag(row.get("barehanded_adept")),
                "source": str(row.get("source") or ""),
                "page": str(row.get("page") or ""),
            }
        )
    return out


def _powers(derived: dict[str, Any], tr: Any) -> list[dict[str, Any]]:
    """The importer takes the level and the power points spent, as they are."""
    out = []
    for row in derived.get("adept_powers") or []:
        name = str(row.get("name") or "")
        if not name:
            continue
        extra = str(row.get("extra") or "")
        out.append(
            {
                "guid": str(row.get("id") or ""),
                "sourceid": str(row.get("power_id") or ""),
                "name": tr(name, "power"),
                "name_english": name,
                "fullname": _fullname(tr(name, "power"), tr(extra) if extra else ""),
                "fullname_english": _fullname(name, extra),
                "extra": extra or None,
                "rating": str(int(row.get("total_rating") or row.get("rating") or 0)),
                "totalpoints": str(float(row.get("cost") or 0)),
                "source": str(row.get("source") or ""),
                "page": str(row.get("page") or ""),
            }
        )
    return out


def _complex_forms(derived: dict[str, Any], tr: Any) -> list[dict[str, str]]:
    """Fading as Chummer prints it ("L-2"): the importer drops the first
    character and reads the rest as the modifier."""
    out = []
    for row in derived.get("complex_forms") or []:
        name = str(row.get("name") or "")
        if not name:
            continue
        extra = str(row.get("extra") or "")
        fields = {
            "target": str(row.get("target") or ""),
            "duration": str(row.get("duration") or ""),
            "fv": str(row.get("fv") or ""),
        }
        out.append(
            {
                "guid": str(row.get("id") or ""),
                "sourceid": str(row.get("form_id") or ""),
                "name": tr(name),
                "name_english": name,
                "fullname": _fullname(tr(name), tr(extra) if extra else ""),
                "fullname_english": _fullname(name, extra),
                **fields,
                **{f"{key}_english": value for key, value in fields.items()},
                "source": str(row.get("source") or ""),
                "page": str(row.get("page") or ""),
            }
        )
    return out


def _money(value: object) -> str:
    return str(int(float(str(value or 0))))


def _armors(derived: dict[str, Any], tr: Any) -> list[dict[str, str]]:
    """The finished rating, "+n" for one that stacks: the importer marks an
    armor with a "+" in it as an accessory. Mods stay inside the value;
    Chummer nests them and the importer does not read them either."""
    out = []
    for row in derived.get("armor_items") or []:
        name = str(row.get("name") or "")
        if not name:
            continue
        value = int(row.get("armor_value") or 0)
        category = str(row.get("category") or "")
        out.append(
            {
                "guid": str(row.get("id") or ""),
                "sourceid": str(row.get("armor_id") or ""),
                "name": tr(name, "armor"),
                "name_english": name,
                "category": tr(category),
                "category_english": category,
                "armor": f"+{value}" if row.get("additive") else str(value),
                "rating": str(int(row.get("rating") or 0)),
                "avail": str(row.get("avail") or ""),
                "owncost": _money(row.get("nuyen")),
                "equipped": _flag(row.get("equipped")),
                "source": str(row.get("source") or ""),
                "page": str(row.get("page") or ""),
            }
        )
    return out


#: this app's grade -> the Foundry grade key (the importer lower-cases
#: `grade` and takes it as is). Used and the like have no Foundry grade.
_GRADES = {"Alphaware": "alpha", "Betaware": "beta", "Deltaware": "delta", "Gammaware": "gamma"}


def _wares(derived: dict[str, Any], tr: Any) -> list[dict[str, str]]:
    """Cyberware and bioware in one list, told apart by `improvementsource`.
    Foundry has no nesting, so a plugged-in part comes out as its own item
    (Chummer nests it, and the importer would drop it)."""
    out = []
    for source, key in (("Cyberware", "cyberware"), ("Bioware", "bioware")):
        for row in derived.get(key) or []:
            name = str(row.get("name") or "")
            if not name:
                continue
            extra = " ".join(str(x) for x in (row.get("extra"), row.get("side")) if x)
            category = str(row.get("category") or "")
            out.append(
                {
                    "guid": str(row.get("id") or ""),
                    "sourceid": str(row.get("ware_id") or ""),
                    "name": tr(name, "cyberware"),
                    "name_english": name,
                    "fullname": _fullname(tr(name, "cyberware"), tr(extra) if extra else ""),
                    "fullname_english": _fullname(name, extra),
                    "category": tr(category),
                    "category_english": category,
                    "improvementsource": source,
                    "ess": str(round(float(row.get("essence") or 0), 4)),
                    "capacity": str(float(row.get("capacity_max") or 0)),
                    "grade": _GRADES.get(str(row.get("grade") or ""), "standard"),
                    "rating": str(int(row.get("rating") or 0)),
                    "avail": str(row.get("avail") or ""),
                    "owncost": _money(row.get("nuyen")),
                    "source": str(row.get("source") or ""),
                    "page": str(row.get("page") or ""),
                }
            )
    return out


#: the buckets gear is split into, as the chum5 export walks them
_GEAR_BUCKETS = ("gear", "commlinks", "cyberdecks", "rccs", "sensors", "optics", "programs", "apps")
_DEVICE_BUCKETS = ("commlinks", "cyberdecks", "rccs")


def _is_sin(row: dict[str, Any]) -> bool:
    return row.get("category") == "ID/Credsticks" and "SIN" in str(row.get("name") or "").split()


def _gears(derived: dict[str, Any], tr: Any, owners: dict[str, str], owner: str = "") -> list[dict[str, Any]]:
    """Flags steer the importer's split: `iscommlink` makes a device (with
    its matrix attributes), `issin` a SIN, `isammo` ammunition, and the
    program categories a program; the rest is equipment. Foundry has no
    nesting, so a child comes out as its own item — except a license under a
    SIN, which the importer reads from the SIN's `children`. `owner` picks
    whose: the character's ("") or a vehicle's (see `_vehicle_owners`)."""
    cost_for = {
        str(row["id"]): int(row.get("costfor") or 0) for bucket in _GEAR_BUCKETS for row in catalog_list(bucket)
    }
    rows = [
        (bucket, row)
        for bucket in _GEAR_BUCKETS
        for row in derived.get(bucket) or []
        if owners.get(str(row.get("id") or ""), "") == owner
    ]
    sins = {str(row.get("id")) for _, row in rows if _is_sin(row)}

    def one(bucket: str, row: dict[str, Any]) -> dict[str, Any]:
        name = str(row.get("name") or "")
        custom = str(row.get("custom_name") or "")
        shown = custom or tr(name, "gear")
        extra = str(row.get("extra") or "")
        category = str(row.get("category") or "")
        # this app counts lots of `costfor` (a box of 10 rounds); Chummer the rounds
        qty = int(row.get("qty") or 1) * max(1, cost_for.get(str(row.get("gear_id")), 1))
        item: dict[str, Any] = {
            "guid": str(row.get("id") or ""),
            "sourceid": str(row.get("gear_id") or ""),
            "name": shown,
            "name_english": custom or name,
            "fullname": _fullname(shown, extra),
            "fullname_english": _fullname(custom or name, extra),
            "extra": extra or None,
            "category": tr(category),
            "category_english": category,
            "rating": str(int(row.get("rating") or 0)),
            "qty": str(qty),
            "avail": str(row.get("avail") or ""),
            "owncost": _money(row.get("nuyen")),
            "equipped": "True",
            "iscommlink": _flag(bucket in _DEVICE_BUCKETS),
            "issin": _flag(_is_sin(row)),
            "isammo": _flag(category == "Ammunition"),
            "source": str(row.get("source") or ""),
            "page": str(row.get("page") or ""),
        }
        if bucket in _DEVICE_BUCKETS:
            item["devicerating"] = str(int(row.get("device_rating") or 0))
            for key in ("attack", "sleaze", "dataprocessing", "firewall"):
                item[key] = str(int(row.get(key) or 0))
        return item

    out: list[dict[str, Any]] = []
    licenses: dict[str, list[dict[str, Any]]] = {}
    for bucket, row in rows:
        parent = str(row.get("parent_id") or "")
        if parent in sins and row.get("category") == "ID/Credsticks":
            licenses.setdefault(parent, []).append(one(bucket, row))
        else:
            out.append(one(bucket, row))
    for item in out:
        if item["guid"] in licenses:
            item["children"] = {"gear": licenses[item["guid"]]}
    return out


#: weapon categories with no ranges.xml entry of their own (the frontend's
#: `RANGE_CAT_ALIAS`)
_RANGE_ALIAS = {"Heavy Machine Guns": "Medium/Heavy Machinegun", "Medium Machine Guns": "Medium/Heavy Machinegun"}
_BANDS = ("short", "medium", "long", "extreme")


def _range_band(formula: object, strength: int) -> int | None:
    """A ranges.xml band ("5", "{STR}*10", "{STR}/2"; "-1" for none), the
    frontend's `evalRangeBand`."""
    text = str(formula or "").strip().replace("{STR}", str(strength))
    if not text or text == "-1":
        return None
    left, op, right = text.partition("*") if "*" in text else text.partition("/")
    try:
        value = float(left)
        if op == "*":
            value *= float(right)
        elif op == "/":
            value /= float(right)
    except ValueError:
        return None
    return int(value)


def _ranges(row: dict[str, Any], derived: dict[str, Any]) -> dict[str, str] | None:
    """The four bands as Chummer prints them ("0-5", "6-20", ...), with the
    STR the sheet uses: the importer reads the number after the dash, and
    only when all four are there."""
    category = str(row.get("category") or "")
    name = str(row.get("range") or "").strip() or _RANGE_ALIAS.get(category) or category
    bands = (catalog().get("weapon_ranges") or {}).get(name)
    if not bands:
        return None
    strength = int((derived.get("totals") or {}).get("STR") or 0)
    if row.get("useskill") == "Throwing Weapons":
        strength += int(derived.get("throw_range_str") or 0)
    highs = [_range_band(bands.get(key), strength) for key in _BANDS]
    if any(high is None for high in highs):
        return None
    tops = [int(high or 0) for high in highs]
    lows = [_range_band(bands.get("min"), strength) or 0, *(high + 1 for high in tops[:3])]
    return {key: f"{low}-{high}" for key, low, high in zip(_BANDS, lows, tops, strict=True)}


_PISTOLS = frozenset({"Tasers", "Holdouts", "Light Pistols", "Heavy Pistols"})


def _weapon_skill(row: dict[str, Any]) -> str | None:
    """The skill Chummer prints, which the importer lower-cases into the
    Foundry skill id ("Heavy Weapons" -> heavy_weapons). The engine's lookup
    falls back to Pistols; a category it does not know (exotic, laser) goes
    out blank instead, and the importer works those out from the category."""
    skill = weapon_skill_dictionary_key(row)
    if skill == "Pistols" and not row.get("useskill") and row.get("category") not in _PISTOLS:
        return None
    return skill


def _weapons(derived: dict[str, Any], tr: Any, owners: dict[str, str], owner: str = "") -> list[dict[str, Any]]:
    """The figures the sheet shows ({STR} already worked out by the engine).
    Those include what the accessories add, so the accessories go along
    with their own accuracy and RC at zero — Foundry would add a mod's on
    top."""
    out = []
    for row in derived.get("weapons") or []:
        if owners.get(str(row.get("id") or ""), "") != owner:
            continue
        name = str(row.get("name") or "")
        if not name:
            continue
        category = str(row.get("category") or "")
        raw_mode = str(row.get("mode") or "").strip()
        mode = None if raw_mode in ("", "0", "-") else raw_mode
        accessories = [
            {
                "guid": str(acc.get("id") or ""),
                "sourceid": str(acc.get("accessory_id") or ""),
                "name": tr(str(acc["name"])),
                "name_english": str(acc["name"]),
                "mount": str(acc.get("mount") or "None"),
                "rating": str(int(acc.get("rating") or 0)),
                "accuracy": "0",
                "rc": "0",
                "conceal": "0",
                "avail": str(acc.get("avail") or ""),
                "owncost": _money(acc.get("nuyen")),
                "source": str(acc.get("source") or ""),
                "page": str(acc.get("page") or ""),
            }
            for acc in row.get("accessories") or []
            if acc.get("name")
        ]
        out.append(
            {
                "guid": str(row.get("id") or ""),
                "sourceid": str(row.get("weapon_id") or ""),
                "name": tr(name),
                "name_english": name,
                "category": tr(category),
                "category_english": category,
                "type": str(row.get("type") or ""),
                "skill": _weapon_skill(row),
                "rawaccuracy": str(row.get("accuracy") or "0"),
                "rawap": str(row.get("ap") or "0"),
                "damage_noammo_english": str(row.get("damage") or ""),
                "rawrc": str(row.get("rc") or "0"),
                "rawreach": str(row.get("reach") or "0"),
                "mode": mode,
                "mode_noammo": mode,
                "mode_english_noammo": mode,
                "ammo_english": str(row.get("ammo") or ""),
                "ranges": _ranges(row, derived),
                "conceal": str(row.get("conceal") or "0"),
                "qty": str(int(row.get("qty") or 1)),
                "avail": str(row.get("avail") or ""),
                "owncost": _money(row.get("nuyen")),
                "equipped": "True",
                "accessories": {"accessory": accessories},
                "source": str(row.get("source") or ""),
                "page": str(row.get("page") or ""),
            }
        )
    return out


def _vehicle_owners(state: CharacterState, derived: dict[str, Any]) -> dict[str, str]:
    """Row id -> the vehicle or drone it sits in, for gear stowed in one (or
    in something stowed in one) and the gun on one of its weapon mounts.
    Foundry makes each vehicle an actor of its own, so these go on it rather
    than on the character."""
    vehicles = {str(row.get("id")) for key in ("vehicles", "drones") for row in derived.get(key) or []}
    parents: dict[str, str] = {}
    for bucket in _GEAR_BUCKETS:
        for row in derived.get(bucket) or []:
            parents[str(row.get("id"))] = str(row.get("parent_id") or "")
    for mod in state.vehicle_mods:
        parents[mod.id] = mod.parent_id or ""
    # set by the engine only for a gun its mount check let through
    for weapon in derived.get("weapons") or []:
        parents[str(weapon.get("id"))] = str(weapon.get("mounted_on") or "")

    def owner(row_id: str) -> str:
        seen: set[str] = set()
        while row_id and row_id not in seen:
            if row_id in vehicles:
                return row_id
            seen.add(row_id)
            row_id = parents.get(row_id, "")
        return ""

    found = {row_id: owner(row_id) for row_id in parents if row_id not in vehicles}
    return {row_id: vehicle for row_id, vehicle in found.items() if vehicle}


_VEHICLE_STATS = ("handling", "accel", "speed", "pilot", "body", "armor", "seats", "sensor")


def _vehicles(derived: dict[str, Any], tr: Any, owners: dict[str, str]) -> list[dict[str, Any]]:
    """Vehicles and drones with the stats the sheet shows (mods worked in).
    The importer makes each one a vehicle actor driven by the character and
    reads handling / speed / accel as "on-road/off-road"."""
    out = []
    for key in ("vehicles", "drones"):
        for row in derived.get(key) or []:
            vid = str(row.get("id") or "")
            name = str(row.get("name") or "")
            category = str(row.get("category") or "")
            mods = [
                {
                    "guid": str(mod.get("id") or ""),
                    "sourceid": str(mod.get("mod_id") or ""),
                    "name": tr(str(mod["name"])),
                    "name_english": str(mod["name"]),
                    "category": tr(str(mod.get("category") or "")),
                    "category_english": str(mod.get("category") or ""),
                    "rating": str(int(mod.get("rating") or 0)),
                    "included": _flag(mod.get("included")),
                    "avail": str(mod.get("avail") or ""),
                    "owncost": _money(mod.get("nuyen")),
                    "source": str(mod.get("source") or ""),
                    "page": str(mod.get("page") or ""),
                }
                for mod in row.get("mods") or []
                if mod.get("name")
            ]
            out.append(
                {
                    "guid": vid,
                    "sourceid": str(row.get("gear_id") or ""),
                    "name": tr(name),
                    "name_english": name,
                    "fullname": tr(name),
                    "fullname_english": name,
                    "category": tr(category),
                    "category_english": category,
                    "isdrone": _flag(key == "drones"),
                    **{stat: str(row.get(stat) or "0") for stat in _VEHICLE_STATS},
                    "avail": str(row.get("avail") or ""),
                    "owncost": _money(row.get("nuyen")),
                    "source": str(row.get("source") or ""),
                    "page": str(row.get("page") or ""),
                    "mods": {"mod": mods},
                    "gears": {"gear": _gears(derived, tr, owners, vid)},
                    "weapons": {"weapon": _weapons(derived, tr, owners, vid)},
                }
            )
    return out


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
