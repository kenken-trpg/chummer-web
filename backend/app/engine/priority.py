"""Priority / Sum-to-Ten / Karma build-method resolution: which options each
priority letter unlocks, talent (Magic/Resonance) selection, and priority-table
validation. Depends only on the catalog, the constants module and the
``Priorities`` model.
"""

from __future__ import annotations

from typing import Any

from ..data_loader import catalog
from ..models import Priorities
from .constants import (
    BUILD_METHOD_KARMA,
    BUILD_METHOD_PRIORITY,
    BUILD_METHOD_SUM_TO_TEN,
    MAG_TALENTS,
    RES_TALENTS,
    SKIP_TALENTS,
    SUM_TO_TEN_BUDGET,
    SUM_TO_TEN_COST,
)


def _priority_rows(category: str) -> list[dict[str, Any]]:
    rows = [r for r in catalog()["priorities"] if r["category"] == category and _is_standard(r)]
    return rows


def _is_standard(row: dict[str, Any]) -> bool:
    gp = (row.get("gameplay") or "").strip()
    return gp == "" or gp == "Standard"


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


def talent_options(letter: str) -> list[dict[str, Any]]:
    row = priority_value("Talent", letter)
    talents = [t for t in (row.get("talents") or []) if t.get("name") not in SKIP_TALENTS]
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


def talent_special(talent: dict[str, Any] | None) -> tuple[str | None, int]:
    if not talent:
        return None, 0
    name = talent.get("name") or ""
    magic = int(talent.get("magic") or 0)
    resonance = int(talent.get("resonance") or 0)
    if name in MAG_TALENTS or (magic and name not in RES_TALENTS):
        return "MAG", magic or int(talent.get("value") or 0)
    if name in RES_TALENTS or resonance:
        return "RES", resonance or int(talent.get("value") or 0)
    return None, 0


def resolve_talent(letter: str, current: str | None) -> dict[str, Any]:
    options = talent_options(letter)
    if not options:
        return {"name": "Mundane", "label": "Mundane", "value": 0, "magic": 0, "resonance": 0, "spells": 0, "cfp": 0}
    found = next((t for t in options if t["name"] == current), None)
    if found:
        return found
    return next((t for t in options if t["name"] != "Mundane"), options[0])


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


def resolve_talent_for_method(letter: str, current: str | None, build_method: str | None) -> dict[str, Any]:
    if normalize_build_method(build_method) == BUILD_METHOD_KARMA:
        options = all_talent_options()
        found = next((t for t in options if t["name"] == current), None)
        if found:
            return found
        mundane = next((t for t in options if t["name"] == "Mundane"), None)
        return mundane or {
            "name": "Mundane",
            "label": "Mundane",
            "value": 0,
            "magic": 0,
            "resonance": 0,
            "spells": 0,
            "cfp": 0,
        }
    return resolve_talent(letter, current)


def normalize_build_method(raw: str | None) -> str:
    value = str(raw or BUILD_METHOD_PRIORITY).strip().lower().replace(" ", "").replace("_", "").replace("-", "")
    if value in {"sumtoten", "sum10", "sumtotenpriority"}:
        return BUILD_METHOD_SUM_TO_TEN
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


def validate_priorities(p: Priorities, build_method: str | None = None) -> list[str]:
    method = normalize_build_method(build_method)
    if method == BUILD_METHOD_KARMA:
        return []
    letters = [str(x or "").upper() for x in (p.Heritage, p.Attributes, p.Talent, p.Skills, p.Resources)]
    errors: list[str] = []
    if any(letter not in SUM_TO_TEN_COST for letter in letters):
        errors.append("優先度は A〜E のみ割り当てできます")
        return errors
    if method == BUILD_METHOD_SUM_TO_TEN:
        spent = sum(priority_letter_cost(letter) for letter in letters)
        if spent != SUM_TO_TEN_BUDGET:
            errors.append(f"Sum to Ten の合計が {SUM_TO_TEN_BUDGET} になるように割り当ててください（現在 {spent}）")
        return errors
    if sorted(letters) != ["A", "B", "C", "D", "E"]:
        errors.append("優先度 A〜E を各カテゴリに1つずつ割り当ててください")
    return errors
