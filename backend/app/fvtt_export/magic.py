"""The magic and resonance sections: tradition, initiation and submersion,
spells, adept powers, complex forms, metamagics and echoes, and critter
powers."""

from __future__ import annotations

from typing import Any

from ..data_loader import catalog
from ..engine.constants import quality_optional_power_extra_key
from ..engine.lookups import critter_power_label
from ..models import CharacterState
from ._common import _flag, _fullname


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
        extra = str(row.get("extra") or "")
        out.append(
            {
                "guid": str(row.get("id") or ""),
                "sourceid": str(row.get("spell_id") or ""),
                "name": tr(name),
                "name_english": name,
                # what Increase [Attribute] picked, in brackets, as
                # `Spell.Print` writes it beside the bare name
                "fullname": _fullname(tr(name), tr(extra) if extra else ""),
                "fullname_english": _fullname(name, extra),
                "extra": extra or None,
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


def _metamagics(derived: dict[str, Any], tr: Any) -> list[dict[str, str]]:
    """Metamagics and echoes in one list, told apart by `improvementsource`;
    the importer reads the shared fields only."""
    out = []
    for source, rows, id_key in (
        ("Metamagic", (derived.get("initiation") or {}).get("metamagics") or [], "metamagic_id"),
        ("Echo", (derived.get("submersion") or {}).get("echoes") or [], "echo_id"),
    ):
        for row in rows:
            name = str(row.get("name") or "")
            if not name:
                continue
            extra = str(row.get("extra") or "")
            out.append(
                {
                    "guid": str(row.get("id") or ""),
                    "sourceid": str(row.get(id_key) or ""),
                    "name": tr(name),
                    "name_english": name,
                    "fullname": _fullname(tr(name), tr(extra) if extra else ""),
                    "fullname_english": _fullname(name, extra),
                    "grade": str(int(row.get("grade") or 0)),
                    "improvementsource": source,
                    "source": str(row.get("source") or ""),
                    "page": str(row.get("page") or ""),
                }
            )
    return out


#: The importer keys a power's duration off one letter (I, S, P). Chummer's
#: print sheet shortens only Sustained to "S" and leaves Instant and
#: Permanent spelled out, which the importer then drops; all three go short.
_DURATIONS = {"Instant": "I", "Sustained": "S", "Permanent": "P"}


def _critter_powers(state: CharacterState, derived: dict[str, Any], tr: Any) -> list[dict[str, str]]:
    """What the metatype gives, what each quality gives (with the optional
    power picked) and what was bought on the Critter Powers tab — the three
    places Chummer's `<critterpowers>` gathers.

    The importer reads `extra_english` as the rating (`parseFloat`), so only
    a rating goes there; a pick such as Immunity's "Age" stays in `extra` and
    the full name."""
    specs: dict[str, dict[str, Any]] = {}
    for row in catalog().get("critter_powers") or []:
        specs.setdefault(str(row.get("name") or ""), row)  # the first definition, as the engine
    qualities = {str(row["id"]): row for row in catalog()["qualities"]}
    rows: list[tuple[str, dict[str, Any], str, str, str]] = []  # (guid, spec, pick, rating, karma)
    for index, power in enumerate((derived.get("metatype_info") or {}).get("powers") or []):
        spec = {**specs.get(str(power.get("name") or ""), {}), **power}
        rows.append((f"metatype:{index}", spec, str(power.get("select") or ""), str(power.get("rating") or ""), "0"))
    for qid in state.quality_ids:
        quality = qualities.get(qid) or {}
        picked = state.quality_extras.get(quality_optional_power_extra_key(qid), "")
        refs = [
            *(quality.get("critter_powers") or []),
            *(ref for ref in quality.get("optional_powers") or [] if critter_power_label(ref) == picked),
        ]
        for index, ref in enumerate(refs):
            spec = specs.get(str(ref.get("name") or "")) or {"name": ref.get("name")}
            rows.append(
                (f"quality:{qid}:{index}", spec, str(ref.get("select") or ""), str(ref.get("rating") or ""), "0")
            )
    for power in derived.get("critter_powers") or []:
        spec = {**specs.get(str(power.get("name") or ""), {}), **power, "id": power.get("power_id")}
        rows.append(
            (
                str(power.get("id") or ""),
                spec,
                str(power.get("extra") or ""),
                str(power.get("rating") or ""),
                str(int(power.get("karma") or 0)),
            )
        )
    return [
        _critter_power(guid, spec, pick, rating, karma, tr)
        for guid, spec, pick, rating, karma in rows
        if spec.get("name")
    ]


def _critter_power(guid: str, spec: dict[str, Any], pick: str, rating: str, karma: str, tr: Any) -> dict[str, str]:
    name = str(spec["name"])
    shown = tr(name, "critter_power")
    extra = " ".join(x for x in (pick, rating) if x)
    category = str(spec.get("category") or "")
    fields = {key: str(spec.get(key) or "") for key in ("type", "action", "range")}
    duration = str(spec.get("duration") or "")
    return {
        "guid": guid,
        "sourceid": str(spec.get("id") or ""),
        "name": shown,
        "name_english": name,
        "fullname": _fullname(shown, tr(extra) if extra else ""),
        "fullname_english": _fullname(name, extra),
        "extra": extra or None,
        "extra_english": rating if rating.lstrip("-").replace(".", "", 1).isdigit() else None,
        "category": tr(category),
        "category_english": category,
        **fields,
        **{f"{key}_english": value for key, value in fields.items()},
        "duration": duration,
        "duration_english": _DURATIONS.get(duration, duration),
        "karma": karma,
        "source": str(spec.get("source") or ""),
        "page": str(spec.get("page") or ""),
    }
