"""Exotic skills — one per weapon — and the bonuses aimed at them."""

from __future__ import annotations

from typing import Any

from ...models import CharacterState, ExoticSkillInstall
from ...notices import Notice, notice, term
from ..bundle_types import SkillMods


def exotic_skill_label(skill_name: str, extra: str) -> str:
    extra = (extra or "").strip()
    return f"{skill_name} ({extra})" if extra else skill_name


def resolve_exotic_skills(
    state: CharacterState,
    skills_data: dict[str, Any],
    skill_max_bonus: dict[str, int],
    *,
    rating_cap: int = 6,
) -> dict[str, Any]:
    catalog_by_name = {skill["name"]: skill for skill in skills_data.get("skills") or [] if skill.get("exotic")}
    warnings: list[Notice] = []
    public: list[dict[str, Any]] = []
    kept: list[ExoticSkillInstall] = []
    totals: dict[str, int] = {}
    spent = 0
    seen: set[tuple[str, str]] = set()
    for inst in state.exotic_skills or []:
        spec = catalog_by_name.get(inst.skill_name)
        if not spec:
            continue
        extra = (inst.extra or "").strip()
        cap = int(rating_cap) + int(skill_max_bonus.get(inst.skill_name) or 0)
        rating = max(1, min(cap, int(inst.rating or 1)))
        inst.extra = extra
        inst.rating = rating
        key = (inst.skill_name, extra.lower())
        if extra and key in seen:
            warnings.append(
                notice("engine.skills.exoticDuplicate", name=term(exotic_skill_label(inst.skill_name, extra)))
            )
            continue
        if extra:
            seen.add(key)
        else:
            warnings.append(notice("engine.skills.pickExoticTarget", name=term(str(spec["name"]))))
        kept.append(inst)
        spent += rating
        label = exotic_skill_label(inst.skill_name, extra)
        if extra:
            totals[label] = rating
        public.append(
            {
                "id": inst.id,
                "skill_name": inst.skill_name,
                "extra": extra,
                "label": label,
                "rating": rating,
                "rating_max": cap,
                "attribute": spec.get("attribute") or "AGI",
                "category": spec.get("category") or "",
                "options": list(spec.get("specs") or []),
                "source": spec.get("source"),
            }
        )
    state.exotic_skills = kept
    return {
        "warnings": warnings,
        "public": public,
        "spent": spent,
        "totals": totals,
    }


def _copy_exotic_skill_bonuses(skill_mods: SkillMods, public: list[dict[str, Any]]) -> None:
    bonus_map: dict[str, int] = skill_mods.setdefault("skill_bonus", {})
    notes_map: dict[str, list[str]] = skill_mods.setdefault("skill_bonus_notes", {})
    for row in public:
        extra = str(row.get("extra") or "").strip()
        if not extra:
            continue
        label = str(row.get("label") or "")
        base = str(row.get("skill_name") or "")
        if not label or not base or label == base:
            continue
        bonus = int(bonus_map.get(base) or 0)
        if bonus:
            bonus_map[label] = int(bonus_map.get(label) or 0) + bonus
        notes = list(notes_map.get(base) or [])
        if notes:
            existing = notes_map.setdefault(label, [])
            for note in notes:
                if note not in existing:
                    existing.append(note)
