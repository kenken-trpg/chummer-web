"""Specializations, and the expertise a `<selectexpertise>` bonus grants."""

from __future__ import annotations

from typing import Any

from ...improvements import EffectsDict
from ...models import CharacterState
from ...notices import Notice, notice, term
from ..constants import EXPERTISE_BONUS


def resolve_specializations(
    state: CharacterState,
    skills_data: dict[str, Any],
    skill_totals: dict[str, int],
    skillsoft_active: dict[str, int],
    skillsoft_knowledge: dict[str, int],
    free_expertise_skills: set[str] | None = None,
) -> dict[str, Any]:
    active_names = {skill["name"] for skill in skills_data.get("skills") or []}
    knowledge_names = {skill["name"] for skill in skills_data.get("knowledge") or []}
    exotic_names = {skill["name"] for skill in skills_data.get("skills") or [] if skill.get("exotic")}
    natives = {str(name).strip() for name in (state.native_languages or []) if str(name).strip()}
    knowledge_owned = (
        {str(name).strip() for name in (state.knowledge_skills or {}) if str(name).strip()}
        | natives
        | {str(name).strip() for name in (skillsoft_knowledge or {}) if str(name).strip()}
    )
    free_expertise = {str(name).strip() for name in (free_expertise_skills or set()) if str(name).strip()}
    cleaned: dict[str, str] = {}
    warnings: list[Notice] = []
    # Skills whose specialization is paid for with a point. Kept per skill, not
    # as a count: a point-cost multiplier applies to a skill's points and its
    # specialization together (Chummer's `CurrentSpCost`), so the caller needs
    # to know which skill each one belongs to.
    active_paid: set[str] = set()
    knowledge_paid: set[str] = set()
    for raw_name, raw_spec in (state.skill_specializations or {}).items():
        name = str(raw_name).strip()
        spec = str(raw_spec or "").strip()
        if not name or not spec or name in exotic_names:
            continue
        is_knowledge = name in knowledge_names or (name not in active_names and name in knowledge_owned)
        if is_knowledge:
            native = name in natives
            rating = 0 if native else int((state.knowledge_skills or {}).get(name) or 0)
            rating = max(rating, int((skillsoft_knowledge or {}).get(name) or 0))
            if not native and rating < 1:
                warnings.append(notice("engine.skills.specNeedsKnowledge", name=term(name)))
                continue
            if name not in free_expertise:
                knowledge_paid.add(name)
        else:
            if name not in active_names:
                warnings.append(notice("engine.skills.specUnknownSkill", name=term(name)))
                continue
            rating = max(int(skill_totals.get(name) or 0), int((skillsoft_active or {}).get(name) or 0))
            if rating < 1:
                warnings.append(notice("engine.skills.specNeedsSkill", name=term(name)))
                continue
            if name not in free_expertise:
                active_paid.add(name)
        cleaned[name] = spec
    state.skill_specializations = cleaned
    return {
        "warnings": warnings,
        "active_spent": len(active_paid),
        "knowledge_spent": len(knowledge_paid),
        "active_paid": active_paid,
        "knowledge_paid": knowledge_paid,
        "specs": cleaned,
    }


def apply_select_expertise(
    state: CharacterState,
    effects: EffectsDict,
    qualities: list[dict[str, Any]],
    skill_totals: dict[str, int],
    skillsoft_active: dict[str, int],
    warnings: list[Notice],
) -> tuple[list[dict[str, Any]], set[str]]:
    """Grant free Expertise (+3) specializations from selectexpertise qualities."""
    by_name = {q["name"]: q for q in qualities}
    extras = state.quality_extras or {}
    specs = dict(state.skill_specializations or {})
    public: list[dict[str, Any]] = []
    free_skills: set[str] = set()
    for slot in effects.get("expertise_slots") or []:
        source = str(slot.get("source") or "")
        skills = [str(name).strip() for name in (slot.get("skills") or []) if str(name).strip()]
        skill_name = skills[0] if skills else ""
        spec_q = by_name.get(source)
        if not spec_q or not skill_name:
            continue
        picked = str(extras.get(spec_q["id"]) or "").strip()
        if not picked:
            warnings.append(notice("engine.skills.pickExpertise", source=term(source)))
            continue
        rating = max(int(skill_totals.get(skill_name) or 0), int((skillsoft_active or {}).get(skill_name) or 0))
        if rating < 1:
            warnings.append(notice("engine.skills.expertiseNeedsSkill", source=term(source), skill=term(skill_name)))
            continue
        limit_specs = [
            part.strip() for part in str(slot.get("limit_to_specialization") or "").split(",") if part.strip()
        ]
        if limit_specs and picked not in limit_specs:
            warnings.append(notice("engine.skills.expertiseNotAllowed", source=term(source), picked=term(picked)))
            continue
        specs[skill_name] = picked
        free_skills.add(skill_name)
        public.append(
            {
                "skill": skill_name,
                "spec": picked,
                "bonus": EXPERTISE_BONUS,
                "free": True,
                "source": source,
            }
        )
    state.skill_specializations = specs
    return public, free_skills


def _attach_specializations(public: list[dict[str, Any]], specs: dict[str, str]) -> None:
    for row in public:
        spec = specs.get(str(row.get("name") or ""))
        if spec:
            row["spec"] = spec
