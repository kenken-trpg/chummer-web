"""The magic and resonance sections: tradition, initiation and submersion,
spells, adept powers and complex forms."""

from __future__ import annotations

from typing import Any

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
