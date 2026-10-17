"""Priority / Sum-to-Ten / Karma build-method resolution: which options each
priority letter unlocks, talent (Magic/Resonance) selection, and priority-table
validation. Depends only on the catalog, the constants module and the
``Priorities`` model.
"""

from __future__ import annotations

from typing import Any

from ..data_loader import catalog
from ..models import Priorities
from ..notices import Notice, notice
from ..rules import DEFAULT_PRIORITY_TABLE, current_rules
from .constants import (
    AI_TALENTS,
    BUILD_METHOD_KARMA,
    BUILD_METHOD_PRIORITY,
    BUILD_METHOD_SUM_TO_TEN,
    MAG_TALENTS,
    RES_TALENTS,
    SUM_TO_TEN_COST,
)


def _priority_rows(category: str) -> list[dict[str, Any]]:
    """The rows of the settings file's priority table, for one category.

    `priorities.xml` holds several tables — Standard, Prime Runner, Street
    Level, and whatever custom data adds — distinguished by
    `<prioritytable>`. A row that names none belongs to every table: that is
    how the vendored file writes the core rows.

    Falls back to Standard when the named table has nothing in this category,
    so a settings file naming a table this data does not have still builds a
    character instead of an empty one.
    """
    wanted = current_rules().priority_table
    rows = [r for r in catalog()["priorities"] if r["category"] == category and _in_table(r, wanted)]
    if not rows and wanted != DEFAULT_PRIORITY_TABLE:
        return [
            r for r in catalog()["priorities"] if r["category"] == category and _in_table(r, DEFAULT_PRIORITY_TABLE)
        ]
    return rows


def _in_table(row: dict[str, Any], table: str) -> bool:
    gp = (row.get("gameplay") or "").strip()
    return gp == "" or gp == table


def priority_value(category: str, letter: str) -> dict[str, Any]:
    letter = letter.upper()
    matches = [r for r in _priority_rows(category) if r["value"] == letter]
    if not matches:
        matches = [r for r in catalog()["priorities"] if r["category"] == category and r["value"] == letter]
    if not matches:
        return {}
    # Prefer the shortest / core-looking row when duplicates exist.
    return sorted(matches, key=lambda r: len(r.get("name") or ""))[0]


def heritage_options(letter: str) -> list[dict[str, Any]]:
    row = priority_value("Heritage", letter)
    return row.get("metatypes") or []


def heritage_cost(letter: str, metatype: str, metavariant: str | None) -> tuple[int, int]:
    """What the Heritage priority hands this metatype: its special attribute
    points, and the karma it charges on top (`(special, karma)`).

    A metavariant's row **replaces** the metatype's, both numbers: it already
    states the whole price. `Shapeshifter: Vulpine` costs 5 karma at priority
    C and its Human variant costs 5 — the same 5, not another one. Adding the
    two charged such a character twice for their heritage (Chummer writes the
    result as `<metatypebp>`, and `Mittens Chargen` says 5 where this said
    10).
    """
    special = 0
    karma = 0
    for entry in priority_value("Heritage", letter).get("metatypes") or []:
        if entry["name"] != metatype:
            continue
        special = entry.get("special", 0)
        karma = entry.get("karma", 0)
        if metavariant:
            for variant in entry.get("variants") or []:
                if variant["name"] == metavariant:
                    special = variant.get("special", special)
                    karma = variant.get("karma", karma)
        break
    return special, karma


def talent_options(letter: str) -> list[dict[str, Any]]:
    row = priority_value("Talent", letter)
    talents = list(row.get("talents") or [])
    if letter.upper() == "E" and not any(t.get("name") == "Mundane" for t in talents):
        talents.insert(
            0,
            {
                "name": "Mundane",
                "label": "Mundane",
                "value": 0,
                "magic": 0,
                "resonance": 0,
                "quality": "",
                "spells": 0,
                "cfp": 0,
            },
        )
    return talents


def talent_allowed(talent: dict[str, Any], metatype: str | None) -> bool:
    """Whether a character of this metatype may take this talent.

    The talent's `<forbidden>` and `<required>` name a metatype or the
    metatype's category — the base metatype's, as Chummer's
    `MetatypeCategory` is: an Elf's Nocturna is a Metahuman. A talent read
    without the lists (a custom row, the synthesized Mundane) allows anyone.
    """
    name = metatype or ""
    base = catalog()["all_metatypes"].get(name) or {}
    category = str(base.get("category") or "")

    def hits(term: dict[str, str]) -> bool:
        if term.get("kind") == "metatypecategory":
            return term.get("name") == category
        return term.get("name") == name

    if any(hits(term) for term in talent.get("forbidden") or []):
        return False
    required = talent.get("required") or []
    return not required or any(hits(term) for term in required)


def talent_special(talent: dict[str, Any] | None) -> tuple[str | None, int]:
    if not talent:
        return None, 0
    name = talent.get("name") or ""
    if name in AI_TALENTS:
        return "DEP", int(talent.get("depth") or 1)
    magic = int(talent.get("magic") or 0)
    resonance = int(talent.get("resonance") or 0)
    if name in MAG_TALENTS or (magic and name not in RES_TALENTS):
        return "MAG", magic or int(talent.get("value") or 0)
    if name in RES_TALENTS or resonance:
        return "RES", resonance or int(talent.get("value") or 0)
    return None, 0


def resolve_talent(letter: str, current: str | None, metatype: str | None = None) -> dict[str, Any]:
    """The talent named `current` at this letter, or a default.

    `current` is kept even when the metatype may not take it — the check
    reports that as an error rather than swapping the talent behind the
    player's back. The default is chosen among the talents `metatype` may
    take (all of them when no metatype is given), so a new A.I. starts on
    the A.I. talent.
    """
    options = talent_options(letter)
    if not options:
        return {"name": "Mundane", "label": "Mundane", "value": 0, "magic": 0, "resonance": 0, "spells": 0, "cfp": 0}
    found = next((t for t in options if t["name"] == current), None)
    if found:
        return found
    allowed = [t for t in options if metatype is None or talent_allowed(t, metatype)] or options
    return next((t for t in allowed if t["name"] != "Mundane"), allowed[0])


def all_talent_options() -> list[dict[str, Any]]:
    by_name: dict[str, dict[str, Any]] = {}
    for letter in "ABCDE":
        for talent in talent_options(letter):
            name = talent.get("name") or ""
            if not name:
                continue
            prev = by_name.get(name)
            score = int(talent.get("magic") or 0) + int(talent.get("resonance") or 0)
            prev_score = int((prev or {}).get("magic") or 0) + int((prev or {}).get("resonance") or 0)
            if prev is None or score > prev_score:
                by_name[name] = dict(talent)
    out: list[dict[str, Any]] = []
    for talent in by_name.values():
        row = dict(talent)
        # a Karma build buys every skill; the free ones are a priority's
        row["free_skills"] = None
        name = row.get("name") or ""
        if name in MAG_TALENTS or int(row.get("magic") or 0) > 0:
            if name not in RES_TALENTS:
                row["magic"] = 1
                row["value"] = 1
                row["resonance"] = 0
                row["spells"] = 0
                row["cfp"] = 0
        if name in RES_TALENTS or int(row.get("resonance") or 0) > 0:
            if name not in MAG_TALENTS:
                row["resonance"] = 1
                row["value"] = 1
                row["magic"] = 0
                row["spells"] = 0
                row["cfp"] = 0
        if name == "Mundane" or (
            not row.get("magic") and not row.get("resonance") and name not in MAG_TALENTS | RES_TALENTS
        ):
            row["magic"] = 0
            row["resonance"] = 0
            row["value"] = 0
            row["spells"] = 0
            row["cfp"] = 0
        if name in AI_TALENTS:
            # Karma buys Depth from the metatype's minimum, as it does Magic.
            row["depth"] = 1
        out.append(row)
    if not any(t.get("name") == "Mundane" for t in out):
        out.append(
            {
                "name": "Mundane",
                "label": "Mundane",
                "value": 0,
                "magic": 0,
                "resonance": 0,
                "quality": "",
                "spells": 0,
                "cfp": 0,
            }
        )
    return sorted(out, key=lambda item: str(item.get("name") or ""))


def resolve_talent_for_method(
    letter: str, current: str | None, build_method: str | None, metatype: str | None = None
) -> dict[str, Any]:
    if normalize_build_method(build_method) in {BUILD_METHOD_KARMA, "LifeModule"}:
        options = all_talent_options()
        found = next((t for t in options if t["name"] == current), None)
        if found:
            return found
        allowed = [t for t in options if metatype is None or talent_allowed(t, metatype)]
        mundane = next((t for t in allowed if t["name"] == "Mundane"), None)
        if mundane is None and allowed and metatype is not None:
            # An A.I. may not be Mundane; its one talent is A.I.
            return allowed[0]
        return mundane or {
            "name": "Mundane",
            "label": "Mundane",
            "value": 0,
            "magic": 0,
            "resonance": 0,
            "spells": 0,
            "cfp": 0,
        }
    return resolve_talent(letter, current, metatype)


def normalize_build_method(raw: str | None) -> str:
    value = str(raw or BUILD_METHOD_PRIORITY).strip().lower().replace(" ", "").replace("_", "").replace("-", "")
    if value in {"sumtoten", "sum10", "sumtotenpriority"}:
        return BUILD_METHOD_SUM_TO_TEN
    if value in {"lifemodule", "lifemodules"}:
        return "LifeModule"
    if value in {"karma", "pointbuy", "point-buy", "bp"}:
        return BUILD_METHOD_KARMA
    return BUILD_METHOD_PRIORITY


def priority_letter_cost(letter: str) -> int:
    return int(SUM_TO_TEN_COST.get(str(letter or "").upper(), -1))


def sum_to_ten_spent(p: Priorities) -> int:
    return sum(
        max(0, priority_letter_cost(letter)) for letter in (p.Heritage, p.Attributes, p.Talent, p.Skills, p.Resources)
    )


def priorities_are_unique(p: Priorities) -> bool:
    letters = [str(x or "").upper() for x in (p.Heritage, p.Attributes, p.Talent, p.Skills, p.Resources)]
    return sorted(letters) == ["A", "B", "C", "D", "E"]


def validate_priorities(p: Priorities, build_method: str | None = None) -> list[Notice]:
    method = normalize_build_method(build_method)
    if method in {BUILD_METHOD_KARMA, "LifeModule"}:
        return []
    letters = [str(x or "").upper() for x in (p.Heritage, p.Attributes, p.Talent, p.Skills, p.Resources)]
    errors: list[Notice] = []
    if any(letter not in SUM_TO_TEN_COST for letter in letters):
        errors.append(notice("engine.priority.letters"))
        return errors
    if method == BUILD_METHOD_SUM_TO_TEN:
        spent = sum(priority_letter_cost(letter) for letter in letters)
        if spent != current_rules().sum_to_ten_budget:
            errors.append(notice("engine.priority.sumToTen", budget=current_rules().sum_to_ten_budget, spent=spent))
        return errors
    if sorted(letters) != ["A", "B", "C", "D", "E"]:
        errors.append(notice("engine.priority.oneEach"))
    return errors
