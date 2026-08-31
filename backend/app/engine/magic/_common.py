"""Maths shared by two or more ``engine/magic/`` resolvers.

Force-scaled drain, tradition drain-resistance, the spellcasting summary, the
initiation/submersion grade discount, and the skill-rating lookup the free-spell
and add-spirit binders both need. Imports only ``catalog`` / ``eval_formula`` /
already-extracted engine modules / models — never back into ``app.engine``.
"""

from __future__ import annotations

import re
from typing import Any

from ...data_loader import catalog, eval_formula
from ...models import CharacterState
from ..constants import DRAIN_MINIMUM
from ..lookups import _spell_by_name

INITIATION_DISCOUNT_STEP = 0.1  # −10% Karma per group / ordeal / schooling (SR5 p.325)


def _magic_grade_discount(*, group: bool = False, ordeal: bool = False, schooling: bool = False) -> float:
    """Multiplier for a single initiation/submersion grade: discounts subtract."""
    steps = int(bool(group)) + int(bool(ordeal)) + int(bool(schooling))
    return max(0.0, 1.0 - INITIATION_DISCOUNT_STEP * steps)


def spell_drain_value(formula: str, force: int, *, mod: int = 0) -> int | None:
    raw = (formula or "").strip()
    if not raw or raw.lower() == "special":
        return None
    if re.fullmatch(r"\d+", raw):
        return int(raw) + int(mod)
    match = re.fullmatch(r"[FL]\s*([+-]\s*\d+)?", raw, re.I)
    if not match:
        return None
    formula_mod = int(re.sub(r"\s+", "", match.group(1))) if match.group(1) else 0
    return max(DRAIN_MINIMUM, int(force) + formula_mod + int(mod))


def tradition_resist(tradition: dict[str, Any] | None, attrs: dict[str, int]) -> tuple[int, str]:
    extras = {
        key: int(attrs.get(key) or 1) for key in ("WIL", "LOG", "INT", "CHA", "BOD", "AGI", "REA", "STR", "RES", "MAG")
    }
    formula = (tradition or {}).get("drain") or "{WIL} + {INT}"
    keys = [key.upper() for key in re.findall(r"\{([A-Za-z]+)\}", str(formula))]
    if not keys:
        keys = ["WIL", "INT"]
    value = int(eval_formula(formula, 1, sum(extras.get(k, 1) for k in keys), extras))
    return value, "+".join(keys)


def _active_skill_rating_from_state(
    state: CharacterState,
    skill_name: str,
    skills_data: dict[str, Any] | None = None,
) -> int:
    rating = int((state.skills or {}).get(skill_name) or 0)
    data = skills_data if skills_data is not None else catalog().get("skills") or {}
    for group, group_rating in (state.skill_groups or {}).items():
        for skill in data.get("skills") or []:
            if skill.get("name") == skill_name and (skill.get("skillgroup") or "") == group:
                rating = max(rating, int(group_rating or 0))
    return rating


def _spell_category_mod_total(effects: dict[str, Any] | None, key: str, category: str) -> int:
    if not effects or not category:
        return 0
    total = 0
    for row in effects.get(key) or []:
        if str(row.get("category") or "").strip() == category:
            total += int(row.get("value") or 0)
    return total


def _spell_descriptor_tokens(descriptor: str | None) -> set[str]:
    return {part.strip() for part in str(descriptor or "").split(",") if part.strip()}


def _spell_descriptor_pattern_matches(pattern: str, descriptors: set[str]) -> bool:
    """Match Chummer SpellDescriptorDrain/Damage ImprovedName (e.g. Direct,NOT(Area))."""
    if not descriptors:
        return False
    allow = False
    for part in str(pattern or "").split(","):
        token = part.strip()
        if not token:
            continue
        if token.startswith("NOT"):
            negated = token[3:].removeprefix("(").removesuffix(")").strip()
            if negated and negated in descriptors:
                return False
        else:
            allow = token in descriptors
    return allow


def _spell_descriptor_mod_total(effects: dict[str, Any] | None, key: str, descriptor: str | None) -> int:
    if not effects:
        return 0
    tokens = _spell_descriptor_tokens(descriptor)
    total = 0
    for row in effects.get(key) or []:
        pattern = str(row.get("descriptor") or "").strip()
        if pattern and _spell_descriptor_pattern_matches(pattern, tokens):
            total += int(row.get("value") or 0)
    return total


def spell_cast_info(
    spell_name: str,
    force: int | None,
    mag: int,
    resist: int,
    resist_attrs: str,
    effects: dict[str, Any] | None = None,
    *,
    barehanded: bool = False,
) -> dict[str, Any] | None:
    spec = _spell_by_name(spell_name)
    if not spec:
        return None
    mag = max(0, int(mag))
    if barehanded:
        force_max = max(1, (mag + 2) // 3) if mag else 1  # MAG/3 rounded up
    else:
        force_max = max(1, mag * 2) if mag else 1
    chosen = int(force) if force else (mag or 1)
    chosen = max(1, min(force_max, chosen))
    category = str(spec.get("category") or "")
    descriptor = str(spec.get("descriptor") or "")
    drain_mod = _spell_category_mod_total(effects, "spell_category_drain", category)
    drain_mod += _spell_descriptor_mod_total(effects, "spell_descriptor_drain", descriptor)
    drain_mod += int((effects or {}).get("drain_value") or 0)
    damage_mod = _spell_category_mod_total(effects, "spell_category_damage", category)
    damage_mod += _spell_descriptor_mod_total(effects, "spell_descriptor_damage", descriptor)
    value = spell_drain_value(str(spec.get("dv") or ""), chosen, mod=drain_mod)
    if barehanded and value is not None:
        value = max(4, int(value) * 2)
    physical = bool(mag) and chosen > mag
    damage = str(spec.get("damage") or "")
    return {
        "spell_id": spec["id"],
        "name": spec["name"],
        "category": spec.get("category"),
        "type": spec.get("type"),
        "range": spec.get("range"),
        "duration": spec.get("duration"),
        "descriptor": spec.get("descriptor"),
        "dv": spec.get("dv") or "",
        "damage": damage,
        "damage_mod": damage_mod,
        "drain_mod": drain_mod,
        "force": chosen,
        "force_min": 1,
        "force_max": force_max,
        "drain": value,
        "drain_code": None if value is None else ("P" if physical else "S"),
        "physical": physical,
        "resist": int(resist),
        "resist_attrs": resist_attrs,
        "barehanded_adept": barehanded,
    }
