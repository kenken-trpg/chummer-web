"""Skill resolution: knowledge skills, specializations / expertise, exotic
skills, `<skillsoft>` autosofts, activesoft-driven skill picks, and the
`<skillcategory>` / dice-pool skill-bonus modifiers compute() applies.

Imports only ``catalog`` / already-extracted engine modules / models — never
back into ``app.engine``.
"""

from __future__ import annotations

from typing import Any

from ..data_loader import catalog
from ..improvements import EffectsDict, _as_int, substitute_rating
from ..models import CharacterState, ExoticSkillInstall
from .bundle_types import SkillMods, SkillPicks
from .constants import EXPERTISE_BONUS
from .lookups import _quality_by_id, _ware_by_id
from .selects import _skillsoft_kind, parse_selectskill_spec, selectskill_options, skillsoft_options

KNOWLEDGE_CATEGORIES = {"Academic", "Interest", "Language", "Professional", "Street"}
KNOWLEDGE_DEFAULT_ATTR = {
    "Academic": "LOG",
    "Professional": "LOG",
    "Street": "INT",
    "Interest": "INT",
    "Language": "INT",
}


def knowledge_pool(intuition: int, logic: int) -> int:
    return (max(1, int(intuition)) + max(1, int(logic))) * 2


def resolve_knowledge(
    state: CharacterState,
    skills_data: dict[str, Any],
    totals: dict[str, int],
    *,
    rating_cap: int = 6,
    native_limit: int = 1,
) -> dict[str, Any]:
    catalog_by_name = {skill["name"]: skill for skill in (skills_data.get("knowledge") or [])}
    warnings: list[str] = []
    ratings: dict[str, int] = {}
    for name, rating in (state.knowledge_skills or {}).items():
        name = str(name).strip()
        value = max(0, min(int(rating_cap), int(rating or 0)))
        if name and value > 0:
            ratings[name] = value

    natives: list[str] = []
    seen: set[str] = set()
    extras: list[str] = []
    limit = max(1, int(native_limit or 1))
    for name in state.native_languages or []:
        name = str(name).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        if len(natives) >= limit:
            extras.append(name)
            continue
        natives.append(name)
        ratings.pop(name, None)
    if extras:
        warnings.append(f"母語は{limit}つまでです（超過分は通常の言語として扱います）")

    extra_categories: dict[str, str] = {}
    owned = set(ratings) | set(natives)
    for name, category in (state.knowledge_categories or {}).items():
        name = str(name).strip()
        if name not in owned or name in catalog_by_name:
            continue
        category = str(category)
        extra_categories[name] = category if category in KNOWLEDGE_CATEGORIES else "Street"
    for name in natives:
        if name not in catalog_by_name:
            extra_categories.setdefault(name, "Language")

    public: list[dict[str, Any]] = []
    names = list(natives) + sorted(name for name in ratings if name not in natives)
    for name in names:
        spec = catalog_by_name.get(name) or {}
        native = name in natives
        category = str(spec.get("category") or extra_categories.get(name) or ("Language" if native else "Street"))
        if category not in KNOWLEDGE_CATEGORIES:
            category = "Street"
        attribute = str(spec.get("attribute") or KNOWLEDGE_DEFAULT_ATTR.get(category) or "INT").upper()
        public.append(
            {
                "name": name,
                "category": category,
                "attribute": attribute,
                "rating": 0 if native else ratings[name],
                "native": native,
            }
        )

    state.knowledge_skills = ratings
    state.native_languages = natives
    state.knowledge_categories = extra_categories
    return {
        "spent": sum(ratings.values()),
        "max": knowledge_pool(int(totals.get("INT") or 1), int(totals.get("LOG") or 1)),
        "public": public,
        "warnings": warnings,
        "native_limit": limit,
    }


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
    warnings: list[str] = []
    active_spent = 0
    knowledge_spent = 0
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
                warnings.append(f"{name} の専門化には知識技能が必要です")
                continue
            if name not in free_expertise:
                knowledge_spent += 1
        else:
            if name not in active_names:
                warnings.append(f"{name} の専門化は未知の技能です")
                continue
            rating = max(int(skill_totals.get(name) or 0), int((skillsoft_active or {}).get(name) or 0))
            if rating < 1:
                warnings.append(f"{name} の専門化には技能が必要です")
                continue
            if name not in free_expertise:
                active_spent += 1
        cleaned[name] = spec
    state.skill_specializations = cleaned
    return {
        "warnings": warnings,
        "active_spent": active_spent,
        "knowledge_spent": knowledge_spent,
        "specs": cleaned,
    }


def apply_select_expertise(
    state: CharacterState,
    effects: EffectsDict,
    qualities: list[dict[str, Any]],
    skill_totals: dict[str, int],
    skillsoft_active: dict[str, int],
    warnings: list[str],
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
            warnings.append(f"{source} の Expertise（専門化）を選んでください")
            continue
        rating = max(int(skill_totals.get(skill_name) or 0), int((skillsoft_active or {}).get(skill_name) or 0))
        if rating < 1:
            warnings.append(f"{source} には {skill_name} 技能（レーティング1以上）が必要です")
            continue
        limit_specs = [
            part.strip() for part in str(slot.get("limit_to_specialization") or "").split(",") if part.strip()
        ]
        if limit_specs and picked not in limit_specs:
            warnings.append(f"{source} の Expertise に {picked} は選べません")
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
    warnings: list[str] = []
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
            warnings.append(f"{exotic_skill_label(inst.skill_name, extra)} が重複しています")
            continue
        if extra:
            seen.add(key)
        else:
            warnings.append(f"{spec['name']} の対象を選んでください")
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


def resolve_skill_mods(
    skills_data: dict[str, Any],
    effects: EffectsDict,
    knowledge_ratings: dict[str, int],
    extra_categories: dict[str, str] | None = None,
) -> SkillMods:
    active = list(skills_data.get("skills") or [])
    knowledge = list(skills_data.get("knowledge") or [])
    catalog_names = {skill["name"] for skill in knowledge}
    for name, category in (extra_categories or {}).items():
        if not name or name in catalog_names:
            continue
        category = category if category in KNOWLEDGE_CATEGORIES else "Street"
        knowledge.append(
            {
                "name": name,
                "category": category,
                "attribute": KNOWLEDGE_DEFAULT_ATTR.get(category, "INT"),
                "knowledge": True,
            }
        )
    bought_knowledge = {name for name, rating in knowledge_ratings.items() if int(rating or 0) > 0}
    skill_bonus: dict[str, int] = {}
    skill_notes: dict[str, list[str]] = {}

    def add_bonus(skill_name: str, bonus: int, note: str) -> None:
        if not bonus:
            return
        skill_bonus[skill_name] = int(skill_bonus.get(skill_name, 0)) + int(bonus)
        if note:
            notes = skill_notes.setdefault(skill_name, [])
            if note not in notes:
                notes.append(note)

    by_group: dict[str, list[dict[str, Any]]] = {}
    by_category: dict[str, list[dict[str, Any]]] = {}
    for skill in active + knowledge:
        group = skill.get("skillgroup")
        if group:
            by_group.setdefault(group, []).append(skill)
        category = skill.get("category")
        if category:
            by_category.setdefault(category, []).append(skill)

    group_bonus: dict[str, int] = {}
    for mod in effects.get("skill_group_mods") or []:
        name = mod.get("name") or ""
        bonus = int(mod.get("bonus") or 0)
        if not name or not bonus:
            continue
        group_bonus[name] = int(group_bonus.get(name, 0)) + bonus
        exclude = mod.get("exclude") or ""
        for skill in by_group.get(name, []):
            if skill["name"] == exclude:
                continue
            add_bonus(skill["name"], bonus, mod.get("condition") or "")

    category_bonus: dict[str, int] = {}
    for mod in effects.get("skill_category_mods") or []:
        name = mod.get("name") or ""
        bonus = int(mod.get("bonus") or 0)
        if not name or not bonus:
            continue
        category_bonus[name] = int(category_bonus.get(name, 0)) + bonus
        exclude = mod.get("exclude") or ""
        for skill in by_category.get(name, []):
            if skill["name"] == exclude:
                continue
            if name in KNOWLEDGE_CATEGORIES and skill["name"] not in bought_knowledge:
                continue
            add_bonus(skill["name"], bonus, mod.get("condition") or "")

    for mod in effects.get("skill_specific_mods") or []:
        add_bonus(mod.get("name") or "", int(mod.get("bonus") or 0), mod.get("condition") or "")

    for mod in effects.get("skill_attribute_mods") or []:
        attr = (mod.get("name") or "").upper()
        bonus = int(mod.get("bonus") or 0)
        if not attr or not bonus:
            continue
        for skill in active + knowledge:
            if (skill.get("attribute") or "").upper() != attr:
                continue
            add_bonus(skill["name"], bonus, mod.get("condition") or "")

    return {
        "skill_bonus": skill_bonus,
        "skill_group_bonus": group_bonus,
        "skill_category_bonus": category_bonus,
        "skill_bonus_notes": skill_notes,
    }


def _skillsoft_value(node: dict[str, Any]) -> int:
    fields = node.get("fields") or {}
    return _as_int(fields.get("val") or fields.get("value") or node.get("value"))


def _merge_skill_ratings(base: dict[str, int], extra: dict[str, int]) -> dict[str, int]:
    out = dict(base)
    for name, rating in extra.items():
        name = str(name or "").strip()
        value = int(rating or 0)
        if not name or value <= 0:
            continue
        out[name] = max(int(out.get(name) or 0), value)
    return out


def resolve_skillsofts(
    gear_items: list[dict[str, Any]],
    skills_data: dict[str, Any],
    effects: EffectsDict,
    warnings: list[str],
) -> dict[str, Any]:
    wires = int(effects.get("skillwires") or 0)
    jack = int(effects.get("skilljack") or 0)
    specs = {item["id"]: item for item in catalog().get("gear") or []}
    active_names = {skill["name"] for skill in skills_data.get("skills") or []}
    knowledge_names = {skill["name"] for skill in skills_data.get("knowledge") or []}
    active: dict[str, int] = {}
    knowledge: dict[str, int] = {}

    def add_rating(bucket: dict[str, int], name: str, rating: int) -> None:
        if not name or rating <= 0:
            return
        bucket[name] = max(int(bucket.get(name) or 0), int(rating))

    for item in gear_items:
        spec = specs.get(str(item.get("gear_id") or ""))
        if not spec:
            continue
        extra = str(item.get("extra") or "").strip()
        nodes = substitute_rating(list(spec.get("bonus") or []), int(item.get("rating") or 1))
        for node in nodes:
            kind = _skillsoft_kind(node)
            if not kind:
                continue
            label = str(item.get("label") or spec.get("name") or "スキルソフト")
            value = _skillsoft_value(node)
            options = set(skillsoft_options(node, skills_data))
            if extra and extra not in options:
                continue
            if not extra:
                continue
            if kind == "active":
                if extra not in active_names:
                    continue
                if wires <= 0:
                    warnings.append(f"{label} を使うにはスキルワイヤが必要です")
                    continue
                if value > wires:
                    warnings.append(f"{label} がスキルワイヤを超えています（R{value} / スキルワイヤ R{wires}）")
                add_rating(active, extra, min(value, wires))
            else:
                if extra not in knowledge_names:
                    continue
                if jack <= 0:
                    warnings.append(f"{label} を使うにはスキルジャックが必要です")
                    continue
                if value > jack:
                    warnings.append(f"{label} がスキルジャックを超えています（R{value} / スキルジャック R{jack}）")
                add_rating(knowledge, extra, min(value, jack))
    return {
        "active": active,
        "knowledge": knowledge,
        "all": {**knowledge, **active},
        "skillwires": wires,
        "skilljack": jack,
    }


def _attach_skillsoft_knowledge(
    public: list[dict[str, Any]],
    skillsoft: dict[str, int],
    skills_data: dict[str, Any],
) -> None:
    catalog_by_name = {skill["name"]: skill for skill in skills_data.get("knowledge") or []}
    by_name = {row["name"]: row for row in public}
    for name, rating in skillsoft.items():
        spec = catalog_by_name.get(name)
        if not spec:
            continue
        row = by_name.get(name)
        if row:
            row["skillsoft"] = int(rating)
            continue
        public.append(
            {
                "name": name,
                "category": spec.get("category") or "Street",
                "attribute": str(
                    spec.get("attribute") or KNOWLEDGE_DEFAULT_ATTR.get(spec.get("category") or "", "INT")
                ).upper(),
                "rating": 0,
                "native": False,
                "skillsoft": int(rating),
            }
        )


def _extra_kind(spec: dict[str, Any]) -> str:
    return str(spec.get("extra_kind") or "")


def resolve_skill_picks(
    state: CharacterState,
    skills_data: dict[str, Any],
    skill_totals: dict[str, int],
) -> SkillPicks:
    slots: list[dict[str, Any]] = []
    warnings: list[str] = []
    skill_max: dict[str, int] = {}
    pick_bonus: dict[str, int] = {}
    pick_notes: dict[str, list[str]] = {}
    picks = state.skill_picks or {}

    def add_slot(key: str, source: str, source_kind: str, source_id: str, node: dict[str, Any]) -> None:
        spec = parse_selectskill_spec(node)
        options = selectskill_options(spec, skills_data, skill_totals)
        picked = picks.get(key) or ""
        if picked and picked not in options:
            warnings.append(f"{source} の技能指定が無効です（{picked}）")
            picked = ""
        if not picked:
            warnings.append(f"{source} の技能を選んでください")
        elif spec.get("bonus"):
            pick_bonus[picked] = int(pick_bonus.get(picked, 0)) + int(spec["bonus"])
            note = spec.get("condition") or ""
            if note:
                notes = pick_notes.setdefault(picked, [])
                if note not in notes:
                    notes.append(note)
        if picked and spec.get("max"):
            skill_max[picked] = int(skill_max.get(picked, 0)) + int(spec["max"])
        slots.append(
            {
                "key": key,
                "source": source,
                "source_kind": source_kind,
                "source_id": source_id,
                "picked": picked,
                "bonus": int(spec.get("bonus") or 0),
                "max": int(spec.get("max") or 0),
                "options": options,
                "knowledgeskills": bool(spec.get("knowledgeskills")),
            }
        )

    for qid in state.quality_ids:
        quality = _quality_by_id(qid)
        if not quality:
            continue
        index = 0
        for node in quality.get("bonus") or []:
            if node.get("tag") != "selectskill":
                continue
            add_slot(f"quality:{qid}:{index}", quality["name"], "quality", qid, node)
            index += 1

    for kind in ("cyberware", "bioware"):
        for inst in getattr(state, kind):
            ware = _ware_by_id(kind, inst.ware_id)
            if not ware:
                continue
            nodes = list(ware.get("bonus") or [])
            if inst.wireless:
                nodes.extend(ware.get("wirelessbonus") or [])
            nodes = substitute_rating(nodes, int(inst.rating or 1))
            index = 0
            for node in nodes:
                if node.get("tag") != "selectskill":
                    continue
                add_slot(f"ware:{inst.id}:{index}", ware["name"], kind, inst.id, node)
                index += 1

    return {
        "slots": slots,
        "warnings": warnings,
        "skill_max_bonus": skill_max,
        "skill_bonus": pick_bonus,
        "skill_bonus_notes": pick_notes,
    }
