from __future__ import annotations

import math
import re
from typing import Any

from .data_loader import (
    CHARGEN_AVAIL_MAX,
    CHARGEN_DEVICE_RATING_MAX,
    CHARGEN_WARE_ATTR_BONUS_MAX,
    MATRIX_ATTRIBUTES,
    PHYSICAL_ATTRS,
    PROGRAM_HOSTS,
    SPELL_CAST_CATEGORIES,
    SPELL_CATEGORIES,
    catalog,
    eval_formula,
    format_avail,
    parse_avail,
    parse_capacity,
    sum_avail,
)
from .improvements import (
    ATTR_ALIASES,
    _as_int,
    apply_bonus_nodes,
    collect_effects,
    compact_limit_modifiers,
    limit_modifiers_from_nodes,
    special_armor_from_nodes,
    special_armor_totals,
    substitute_rating,
)
from .models import (
    ArmorInstall,
    ArmorModInstall,
    CareerBaseline,
    CharacterOptions,
    CharacterState,
    CommlinkInstall,
    ComplexFormInstall,
    ContactInstall,
    CyberwareInstall,
    ExoticSkillInstall,
    FocusInstall,
    GearInstall,
    LifestyleInstall,
    MartialArtInstall,
    InitiationChoice,
    SubmersionChoice,
    Priorities,
    QiFocusInstall,
    SpellInstall,
    SpiritInstall,
    SpriteInstall,
    WeaponAccessoryInstall,
    WeaponInstall,
    VehicleModInstall,
    WeaponMountInstall,
)

STANDARD_GAMEPLAY = "Standard"

MAG_TALENTS = {
    "Magician",
    "Aspected Magician",
    "Adept",
    "Mystic Adept",
    "Explorer",
    "Enchanter",
    "Apprentice",
}
RES_TALENTS = {"Technomancer"}
ADEPT_TALENTS = {"Adept", "Mystic Adept"}
SKIP_TALENTS = {"A.I."}
MYSTIC_PP_KARMA = 5
ENHANCEMENT_KARMA = 2
SPELL_KARMA = 5
COMPLEX_FORM_KARMA = 4
CONTACT_FREE_MULT = 3
CONTACT_RATING_MIN = 1
CONTACT_RATING_MAX = 6
CONTACT_CHARGEN_COST_MAX = 7
NEGATIVE_QUALITY_KARMA_CAP = 25
MARTIAL_ART_STYLE_KARMA = 7
MARTIAL_ART_TECHNIQUE_KARMA = 5
MARTIAL_ART_CHARGEN_STYLE_MAX = 1
MARTIAL_ART_CHARGEN_TECHNIQUE_MAX = 5
INITIATION_KARMA_FLAT = 10
INITIATION_KARMA_PER_GRADE = 3
SUBMERSION_KARMA_FLAT = 10
SUBMERSION_KARMA_PER_GRADE = 3
MENTOR_SPIRIT_ID = "ced3fecf-2277-4b20-b1e0-894162ca9ae2"
QI_FOCUS_NAME = "Qi Focus"
DRAIN_MINIMUM = 2
BUILD_METHOD_PRIORITY = "Priority"
BUILD_METHOD_SUM_TO_TEN = "SumToTen"
BUILD_METHOD_KARMA = "Karma"
SUM_TO_TEN_BUDGET = 10
SUM_TO_TEN_COST = {"A": 4, "B": 3, "C": 2, "D": 1, "E": 0}
KARMA_CHARGEN_POOL = 800
KARMA_ATTRIBUTE = 5
KARMA_ACTIVE_SKILL = 2
KARMA_SKILL_GROUP = 5
KARMA_KNOWLEDGE = 1
KARMA_SPECIALIZATION = 7
KARMA_TO_NUYEN = 2000
KARMA_NUYEN_MAX = 235
CAREER_SKILL_MAX = 12
CAREER_SKILL_GROUP_MAX = 12
SPELL_TALENTS = {"Magician", "Mystic Adept", "Aspected Magician", "Apprentice", "Enchanter"}
SPIRIT_TALENTS = {"Magician", "Mystic Adept", "Aspected Magician", "Apprentice"}
SPRITE_TALENTS = set(RES_TALENTS)
COMPLEX_FORM_TALENTS = set(RES_TALENTS)
FOCUS_TALENTS = set(MAG_TALENTS)
DEFAULT_STREAM_NAME = "Default"
SPRITE_MATRIX_KEYS = {
    "CHA": "attack",
    "INT": "sleaze",
    "LOG": "dataprocessing",
    "WIL": "firewall",
}
SPIRIT_REAGENT_YEN = 20
FOCUS_FORCE_MULT = 5
SPIRIT_ROLE_LABELS = {
    "combat": "戦闘",
    "detection": "探知",
    "health": "健康",
    "illusion": "幻影",
    "manipulation": "操作",
}


def _ceil_div(n: float) -> int:
    return int(math.ceil(n))


def find_metatype(name: str, variant: str | None) -> dict[str, Any]:
    data = catalog()
    by_name = data["all_metatypes"]
    if variant:
        for base in data["metatypes"]:
            if base["name"] != name:
                continue
            for mv in base.get("metavariants", []):
                if mv["name"] == variant:
                    return mv
        if variant in by_name:
            return by_name[variant]
    if name in by_name:
        return by_name[name]
    raise KeyError(f"Unknown metatype: {name}/{variant}")


def _priority_rows(category: str) -> list[dict[str, Any]]:
    rows = [
        r
        for r in catalog()["priorities"]
        if r["category"] == category and _is_standard(r)
    ]
    return rows


def _is_standard(row: dict[str, Any]) -> bool:
    gp = (row.get("gameplay") or "").strip()
    return gp == "" or gp == "Standard"


def priority_value(category: str, letter: str) -> dict[str, Any]:
    letter = letter.upper()
    matches = [r for r in _priority_rows(category) if r["value"] == letter]
    if not matches:
        matches = [
            r
            for r in catalog()["priorities"]
            if r["category"] == category and r["value"] == letter
        ]
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
            {"name": "Mundane", "label": "Mundane", "value": 0, "magic": 0, "resonance": 0, "quality": "", "spells": 0, "cfp": 0},
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
        if name == "Mundane" or (not row.get("magic") and not row.get("resonance") and name not in MAG_TALENTS | RES_TALENTS):
            row["magic"] = 0
            row["resonance"] = 0
            row["value"] = 0
            row["spells"] = 0
            row["cfp"] = 0
        out.append(row)
    if not any(t.get("name") == "Mundane" for t in out):
        out.append(
            {"name": "Mundane", "label": "Mundane", "value": 0, "magic": 0, "resonance": 0, "quality": "", "spells": 0, "cfp": 0}
        )
    return sorted(out, key=lambda item: str(item.get("name") or ""))


def resolve_talent_for_method(letter: str, current: str | None, build_method: str | None) -> dict[str, Any]:
    if normalize_build_method(build_method) == BUILD_METHOD_KARMA:
        options = all_talent_options()
        found = next((t for t in options if t["name"] == current), None)
        if found:
            return found
        mundane = next((t for t in options if t["name"] == "Mundane"), None)
        return mundane or {"name": "Mundane", "label": "Mundane", "value": 0, "magic": 0, "resonance": 0, "spells": 0, "cfp": 0}
    return resolve_talent(letter, current)


def _karma_raise_cost(from_rating: int, to_rating: int, per_rating: int) -> int:
    low = max(0, int(from_rating))
    high = max(0, int(to_rating))
    if high <= low or per_rating <= 0:
        return 0
    return sum(level * int(per_rating) for level in range(low + 1, high + 1))


def attribute_karma_cost(
    ratings: dict[str, int],
    attrs_spec: dict[str, dict[str, int | float]],
    special_key: str | None,
) -> int:
    total = 0
    for key in (*PHYSICAL_ATTRS, "EDG"):
        spec = attrs_spec.get(key) or {}
        racial_min = int(spec.get("min") or 1)
        total += _karma_raise_cost(racial_min, int(ratings.get(key) or racial_min), KARMA_ATTRIBUTE)
    if special_key == "MAG":
        total += _karma_raise_cost(1, int(ratings.get("MAG") or 0), KARMA_ATTRIBUTE)
    elif special_key == "RES":
        total += _karma_raise_cost(1, int(ratings.get("RES") or 0), KARMA_ATTRIBUTE)
    return total


def skill_karma_cost(
    skill_groups: dict[str, int],
    skill_totals: dict[str, int],
    skills_data: dict[str, Any],
    *,
    group_cap: int = 6,
) -> int:
    total = 0
    group_floor: dict[str, int] = {}
    for group, rating in (skill_groups or {}).items():
        grade = max(0, min(int(group_cap), int(rating or 0)))
        total += _karma_raise_cost(0, grade, KARMA_SKILL_GROUP)
        for skill in skills_data.get("skills") or []:
            if skill.get("skillgroup") == group and not skill.get("exotic"):
                name = skill.get("name") or ""
                if name:
                    group_floor[name] = max(group_floor.get(name, 0), grade)
    for name, rating in (skill_totals or {}).items():
        floor = int(group_floor.get(name) or 0)
        total += _karma_raise_cost(floor, int(rating or 0), KARMA_ACTIVE_SKILL)
    return total


def snapshot_career_baseline(state: CharacterState) -> CareerBaseline:
    return CareerBaseline(
        attributes={str(k): int(v) for k, v in (state.attributes or {}).items()},
        skills={str(k): int(v) for k, v in (state.skills or {}).items()},
        skill_groups={str(k): int(v) for k, v in (state.skill_groups or {}).items()},
        knowledge_skills={str(k): int(v) for k, v in (state.knowledge_skills or {}).items()},
        skill_specializations=sorted(
            str(name)
            for name, spec in (state.skill_specializations or {}).items()
            if str(spec or "").strip()
        ),
        exotic_skills={
            str(row.id): int(row.rating or 0)
            for row in (state.exotic_skills or [])
            if getattr(row, "id", None)
        },
    )


def _group_floor_map(skill_groups: dict[str, int], skills_data: dict[str, Any]) -> dict[str, int]:
    floors: dict[str, int] = {}
    for group, rating in (skill_groups or {}).items():
        grade = max(0, int(rating or 0))
        for skill in skills_data.get("skills") or []:
            if skill.get("skillgroup") == group and not skill.get("exotic"):
                name = str(skill.get("name") or "")
                if name:
                    floors[name] = max(floors.get(name, 0), grade)
    return floors


def career_raise_karma(
    state: CharacterState,
    baseline: CareerBaseline,
    skill_totals: dict[str, int],
    skills_data: dict[str, Any],
) -> int:
    """Karma to raise Priority/SumToTen characters from chargen snapshot to current ratings."""
    total = 0
    base_attrs = baseline.attributes or {}
    for key, rating in (state.attributes or {}).items():
        if key == "ESS":
            continue
        total += _karma_raise_cost(int(base_attrs.get(key, rating)), int(rating or 0), KARMA_ATTRIBUTE)

    base_groups = baseline.skill_groups or {}
    for group, rating in (state.skill_groups or {}).items():
        total += _karma_raise_cost(int(base_groups.get(group, 0)), int(rating or 0), KARMA_SKILL_GROUP)

    base_floors = _group_floor_map(base_groups, skills_data)
    now_floors = _group_floor_map(dict(state.skill_groups or {}), skills_data)
    base_skills = baseline.skills or {}
    for name, rating in (skill_totals or {}).items():
        from_r = max(int(base_skills.get(name, 0)), int(base_floors.get(name, 0)))
        from_r = max(from_r, int(now_floors.get(name, 0)))
        total += _karma_raise_cost(from_r, int(rating or 0), KARMA_ACTIVE_SKILL)

    base_know = baseline.knowledge_skills or {}
    natives = set(state.native_languages or [])
    for name, rating in (state.knowledge_skills or {}).items():
        if name in natives:
            continue
        total += _karma_raise_cost(int(base_know.get(name, 0)), int(rating or 0), KARMA_KNOWLEDGE)

    base_specs = set(baseline.skill_specializations or [])
    for name, spec in (state.skill_specializations or {}).items():
        if str(spec or "").strip() and name not in base_specs:
            total += KARMA_SPECIALIZATION

    base_exotic = baseline.exotic_skills or {}
    for row in state.exotic_skills or []:
        rid = str(getattr(row, "id", "") or "")
        if not rid:
            continue
        total += _karma_raise_cost(int(base_exotic.get(rid, 0)), int(row.rating or 0), KARMA_ACTIVE_SKILL)
    return total


def knowledge_excess_karma(ratings: dict[str, int], free_points: int) -> int:
    levels: list[int] = []
    for rating in (ratings or {}).values():
        for level in range(1, max(0, int(rating or 0)) + 1):
            levels.append(level * KARMA_KNOWLEDGE)
    levels.sort()
    free = max(0, int(free_points))
    if free >= len(levels):
        return 0
    return sum(levels[free:])


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
    return sum(max(0, priority_letter_cost(letter)) for letter in (p.Heritage, p.Attributes, p.Talent, p.Skills, p.Resources))


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


def _effective_attr_spec(
    attrs_spec: dict[str, dict[str, int | float]],
    special_key: str | None,
    talent_start: int,
    mag_max_bonus: int = 0,
    res_max_bonus: int = 0,
) -> dict[str, dict[str, int | float]]:
    out = {key: dict(spec) for key, spec in attrs_spec.items()}
    if special_key == "MAG":
        out["MAG"]["min"] = max(talent_start, 1)
        out["MAG"]["max"] = int(out["MAG"].get("max") or 0) + max(0, int(mag_max_bonus))
        out["RES"]["min"] = 0
        out["RES"]["max"] = 0
    elif special_key == "RES":
        out["RES"]["min"] = max(talent_start, 1)
        out["RES"]["max"] = int(out["RES"].get("max") or 0) + max(0, int(res_max_bonus))
        out["MAG"]["min"] = 0
        out["MAG"]["max"] = 0
    else:
        out["MAG"]["min"] = 0
        out["MAG"]["max"] = 0
        out["RES"]["min"] = 0
        out["RES"]["max"] = 0
    return out


def default_attributes(meta: dict[str, Any]) -> dict[str, int]:
    out = {}
    for key, spec in meta["attributes"].items():
        if key == "ESS":
            out[key] = int(spec["max"] or 6)
        else:
            out[key] = int(spec["min"])
    return out


def _quality_by_id(qid: str) -> dict[str, Any] | None:
    for q in catalog()["qualities"]:
        if q["id"] == qid:
            return q
    return None


def _quality_by_name(name: str) -> dict[str, Any] | None:
    for q in catalog()["qualities"]:
        if q["name"] == name:
            return q
    return None


def _power_by_id(pid: str) -> dict[str, Any] | None:
    for item in catalog().get("powers") or []:
        if item["id"] == pid:
            return item
    return None


def _power_by_name(name: str) -> dict[str, Any] | None:
    for item in catalog().get("powers") or []:
        if item["name"] == name:
            return item
    return None


def _mentor_by_id(mid: str) -> dict[str, Any] | None:
    for item in catalog().get("mentors") or []:
        if item["id"] == mid:
            return item
    return None


def _spell_by_name(name: str) -> dict[str, Any] | None:
    for item in catalog().get("spells") or []:
        if item["name"] == name:
            return item
    return None


def _spell_by_id(sid: str) -> dict[str, Any] | None:
    for item in catalog().get("spells") or []:
        if item["id"] == sid:
            return item
    return None


def _tradition_by_id(tid: str | None) -> dict[str, Any] | None:
    if not tid:
        return None
    for item in catalog().get("traditions") or []:
        if item["id"] == tid:
            return item
    return None


def _spirit_by_id(sid: str) -> dict[str, Any] | None:
    for item in catalog().get("spirits") or []:
        if item["id"] == sid:
            return item
    return None


def _stream_by_id(sid: str | None) -> dict[str, Any] | None:
    if not sid:
        return None
    for item in catalog().get("streams") or []:
        if item["id"] == sid:
            return item
    return None


def _default_stream() -> dict[str, Any] | None:
    for item in catalog().get("streams") or []:
        if item["name"] == DEFAULT_STREAM_NAME:
            return item
    streams = catalog().get("streams") or []
    return streams[0] if streams else None


def _complex_form_by_id(fid: str) -> dict[str, Any] | None:
    for item in catalog().get("complex_forms") or []:
        if item["id"] == fid:
            return item
    return None


def _sprite_by_id(sid: str) -> dict[str, Any] | None:
    for item in catalog().get("sprites") or []:
        if item["id"] == sid:
            return item
    return None


def _focus_by_id(gid: str) -> dict[str, Any] | None:
    for item in catalog().get("foci") or []:
        if item["id"] == gid:
            return item
    return None


def _item_by_id(kind: str, item_id: str) -> dict[str, Any] | None:
    for item in catalog().get(kind) or []:
        if item["id"] == item_id:
            return item
    return None


def parse_armor_value(raw: str, rating: int = 1) -> tuple[int, bool]:
    text = (raw or "0").strip()
    additive = text.startswith("+") or text.startswith("-")
    if text.lower() == "rating":
        return int(rating), False
    try:
        return int(float(text)), additive
    except ValueError:
        return int(eval_formula(text, rating, 0)), additive


def armor_plugin_capacity(
    expr: str | None,
    rating: int,
    extras: dict[str, int | float] | None = None,
) -> float:
    raw = (expr or "").strip()
    if not raw:
        return 0.0
    fixed = re.fullmatch(r"FixedValues\((.+)\)", raw, re.I)
    if fixed:
        parts = [p.strip() for p in fixed.group(1).split(",")]
        idx = max(0, min(len(parts) - 1, int(rating) - 1))
        return armor_plugin_capacity(parts[idx], rating, extras)
    if raw.startswith("[") and raw.endswith("]") and "/" not in raw:
        inner = raw[1:-1]
        return eval_formula(inner, rating, 0.0, extras)
    return eval_formula(raw, rating, 0.0, extras)


def armor_mod_fits(
    spec: dict[str, Any],
    armor: dict[str, Any],
    installed_names: set[str] | None = None,
) -> bool:
    names = {str(n) for n in (installed_names or set())}
    required_names = [str(n) for n in (spec.get("required_names") or []) if n]
    if required_names and armor.get("name") not in required_names:
        return False
    required_mods = [str(n) for n in (spec.get("required_mods") or []) if n]
    if required_mods and any(name not in names for name in required_mods):
        return False
    category = str(spec.get("category") or "General")
    allowed = {str(c) for c in (armor.get("addmodcategories") or []) if c}
    if category == "General":
        return True
    if category in allowed:
        return True
    return category == str(armor.get("category") or "")


def _ensure_armor_mods(state: CharacterState) -> list[str]:
    warnings: list[str] = []
    specs = {item["id"]: item for item in catalog().get("armor_mods") or []}
    by_name = {item["name"]: item for item in specs.values()}
    armors = {item.id: item for item in state.armor}
    armor_specs = {item["id"]: item for item in catalog().get("armor") or []}
    kept: list[ArmorModInstall] = []
    for inst in list(state.armor_mods or []):
        spec = specs.get(inst.mod_id)
        parent = armors.get(inst.parent_id or "")
        if not spec or not parent:
            if spec:
                warnings.append(f"{spec['name']} は防具に装着してください")
            continue
        kept.append(inst)
    have = {(row.parent_id, (specs.get(row.mod_id) or {}).get("name")) for row in kept}
    extra: list[ArmorModInstall] = []
    for armor in state.armor:
        aspec = armor_specs.get(armor.armor_id) or {}
        for gift in aspec.get("included_mods") or []:
            child = by_name.get(gift.get("name"))
            if not child or (armor.id, child["name"]) in have:
                continue
            extra.append(
                ArmorModInstall(
                    mod_id=child["id"],
                    parent_id=armor.id,
                    included=True,
                    rating=int(gift.get("rating") or 1),
                )
            )
            have.add((armor.id, child["name"]))
    state.armor_mods = kept + extra
    return warnings


def _resolve_armor_mods(
    state: CharacterState,
    armor_items: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int, list[str], list[str], list[tuple[str, list[dict[str, Any]]]]]:
    warnings = _ensure_armor_mods(state)
    errors: list[str] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    specs = {item["id"]: item for item in catalog().get("armor_mods") or []}
    armor_specs = {item["id"]: item for item in catalog().get("armor") or []}
    public: list[dict[str, Any]] = []
    kept: list[ArmorModInstall] = []
    nuyen = 0
    children: dict[str, list[ArmorModInstall]] = {}
    for inst in list(state.armor_mods or []):
        children.setdefault(inst.parent_id or "", []).append(inst)

    for item in armor_items:
        used = 0.0
        cap_bonus = 0.0
        seen_names: set[str] = set()
        seen_unique: set[str] = set()
        item["mod_armor"] = 0
        cap_max_base = eval_formula(str(item.get("armorcapacity") or "0"), int(item.get("rating") or 1), 0)
        parent_unit = int(
            eval_formula(
                str((armor_specs.get(str(item.get("armor_id") or "")) or {}).get("cost") or "0"),
                int(item.get("rating") or 1),
                0,
            )
        )
        for inst in children.get(item["id"]) or []:
            spec = specs.get(inst.mod_id)
            if not spec:
                continue
            if inst.included:
                rating = max(1, int(inst.rating or 1))
            else:
                rating = _clamp_rating(spec, inst.rating)
            inst.rating = rating
            if spec["name"] in seen_names or (spec.get("unique") and spec["unique"] in seen_unique):
                warnings.append(f"{spec['name']} は {item['name']} に重複して装着できません")
                continue
            names_without = seen_names - {spec["name"]}
            if not armor_mod_fits(spec, item, names_without):
                warnings.append(f"{spec['name']} は {item['name']} に装着できません")
                continue
            cap_cost = 0.0 if inst.included else armor_plugin_capacity(
                str(spec.get("armorcapacity") or ""),
                rating,
                extras={"Capacity": cap_max_base},
            )
            extra, _additive = parse_armor_value(str(spec.get("armor") or "0"), rating)
            cost = 0 if inst.included else int(
                eval_formula(str(spec.get("cost") or "0"), rating, 0, extras={"Armor Cost": parent_unit})
            )
            nuyen += cost
            if cap_cost < 0:
                cap_bonus += -cap_cost
            else:
                used += cap_cost
            if extra:
                item["mod_armor"] = int(item.get("mod_armor") or 0) + extra
            item["nuyen"] = int(item.get("nuyen") or 0) + cost
            seen_names.add(spec["name"])
            if spec.get("unique"):
                seen_unique.add(str(spec["unique"]))
            if item.get("equipped"):
                nodes = substitute_rating(list(spec.get("bonus") or []), rating)
                if nodes:
                    bonus_sources.append((spec["name"], nodes))
            kept.append(inst)
            row: dict[str, Any] = {
                "id": inst.id,
                "mod_id": spec["id"],
                "name": spec["name"],
                "category": spec.get("category") or "General",
                "parent_id": inst.parent_id,
                "included": bool(inst.included),
                "rating": rating,
                "rating_max": int(spec.get("maxrating") or 0),
                "nuyen": cost,
                "capacity_cost": int(cap_cost) if cap_cost == int(cap_cost) else cap_cost,
                "armor": spec.get("armor") or "0",
                "unique": spec.get("unique") or "",
                "avail": spec.get("avail") or "",
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
            special = special_armor_from_nodes(list(spec.get("bonus") or []), rating)
            if special:
                row["special_armor"] = special
            limits = limit_modifiers_from_nodes(list(spec.get("bonus") or []), rating)
            if limits:
                row["limit_modifiers"] = limits
            public.append(row)
        cap_max = cap_max_base + cap_bonus
        item["capacity_used"] = int(used) if used == int(used) else used
        item["capacity_max"] = int(cap_max) if cap_max == int(cap_max) else cap_max
        item["mods"] = [row for row in public if row.get("parent_id") == item["id"]]
        extra = int(item.get("mod_armor") or 0)
        if extra:
            item["armor_value"] = int(item.get("armor_value") or 0) + extra
        if used > cap_max + 1e-9:
            errors.append(f"{item['name']} の容量超過（{item['capacity_used']:g}/{item['capacity_max']:g}）")
    state.armor_mods = kept
    return public, nuyen, warnings, errors, bonus_sources


def _recompute_worn_armor(armor_items: list[dict[str, Any]]) -> tuple[int, str, list[str]]:
    warnings: list[str] = []
    base_values: list[tuple[str, int]] = []
    add_total = 0
    for item in armor_items:
        if not item.get("equipped"):
            item["contributes"] = 0
            continue
        value = int(item.get("armor_value") or 0)
        if item.get("additive"):
            add_total += value
            item["contributes"] = value
        else:
            base_values.append((str(item.get("name") or ""), value))
    worn_name = ""
    worn_base = 0
    if base_values:
        worn_name, worn_base = max(base_values, key=lambda row: row[1])
        if len(base_values) > 1:
            warnings.append("防具本体は一番高い1着だけをアーマーに加算しています")
    for item in armor_items:
        if not item.get("equipped"):
            item["contributes"] = 0
        elif item.get("additive"):
            item["contributes"] = int(item.get("armor_value") or 0)
        else:
            item["contributes"] = int(item.get("armor_value") or 0) if item.get("name") == worn_name else 0
    return worn_base + add_total, worn_name, warnings



def _clamp_rating(spec: dict[str, Any], rating: int) -> int:
    max_rating = int(spec.get("maxrating") or 0)
    if max_rating <= 0:
        return 1
    min_rating = max(1, int(spec.get("minrating") or 1))
    return max(min_rating, min(max_rating, int(rating or min_rating)))


MATRIX_ARRAY_KEYS = ("attack", "sleaze", "dataprocessing", "firewall")
MATRIX_ARRAY_ALIASES = {
    "atk": "attack",
    "slz": "sleaze",
    "dp": "dataprocessing",
    "data processing": "dataprocessing",
    "fw": "firewall",
}


def _normalize_array_order(raw: list[str] | None) -> list[str]:
    seen: set[str] = set()
    order: list[str] = []
    for item in raw or []:
        key = MATRIX_ARRAY_ALIASES.get(str(item).strip().lower(), str(item).strip().lower())
        if key in MATRIX_ARRAY_KEYS and key not in seen:
            order.append(key)
            seen.add(key)
    for key in MATRIX_ARRAY_KEYS:
        if key not in seen:
            order.append(key)
    return order


def _matrix_base_array(spec: dict[str, Any], rating: int) -> list[int]:
    raw = str(spec.get("attributearray") or "").strip()
    if raw:
        nums: list[int] = []
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            nums.append(int(eval_formula(part, rating, 0)))
        return nums
    return [int(eval_formula(str(spec.get(key) or "0"), rating, 0)) for key in MATRIX_ARRAY_KEYS]


def _matrix_stats(
    spec: dict[str, Any],
    rating: int,
    array_order: list[str] | None = None,
    *,
    reorder: bool = False,
) -> dict[str, Any]:
    device = int(eval_formula(str(spec.get("devicerating") or "0"), rating, 0))
    programs = int(eval_formula(str(spec.get("programs") or "0"), rating, 0))
    nums = _matrix_base_array(spec, rating)
    can_reorder = bool(reorder and len(nums) == 4)
    order = _normalize_array_order(array_order if can_reorder else None)
    stats = {key: 0 for key in MATRIX_ARRAY_KEYS}
    for key, value in zip(order, nums):
        stats[key] = value
    return {
        "device_rating": device,
        "programs": programs,
        **stats,
        "array": nums,
        "array_order": order,
        "can_reorder": can_reorder,
    }


SENSOR_DEVICE_CATEGORIES = {"Sensors"}


def _device_rating_of(spec: dict[str, Any] | None, rating: int) -> int:
    raw = str((spec or {}).get("devicerating") or "").strip()
    if raw and raw not in {"0", "-"}:
        return max(0, int(eval_formula(raw, rating, 0)))
    if str((spec or {}).get("category") or "") in SENSOR_DEVICE_CATEGORIES:
        return max(0, int(rating or 0))
    return 0


def _resolve_matrix_devices(kind: str, installs: list[GearInstall]) -> tuple[list[GearInstall], list[dict[str, Any]], int]:
    kept: list[GearInstall] = []
    public: list[dict[str, Any]] = []
    nuyen = 0
    reorder = kind == "cyberdecks"
    for inst in installs:
        spec = _item_by_id(kind, inst.gear_id)
        if not spec:
            continue
        rating = _clamp_rating(spec, inst.rating)
        inst.rating = rating
        cost = int(eval_formula(str(spec.get("cost") or "0"), rating, 0))
        nuyen += cost
        stats = _matrix_stats(spec, rating, inst.array_order, reorder=reorder)
        if stats["can_reorder"]:
            inst.array_order = list(stats["array_order"])
        else:
            inst.array_order = []
        kept.append(inst)
        public.append(
            {
                "id": inst.id,
                "gear_id": spec["id"],
                "name": spec["name"],
                "category": spec.get("category") or "",
                "rating": rating,
                "rating_max": int(spec.get("maxrating") or 0),
                "nuyen": cost,
                "avail": spec.get("avail") or "",
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
                **stats,
            }
        )
    return kept, public, nuyen


def _cascade_optics(items: list[GearInstall], extra_parents: set[str] | None = None) -> list[GearInstall]:
    ids = {item.id for item in items} | set(extra_parents or [])
    keep = [item for item in items if not item.parent_id or item.parent_id in ids]
    if len(keep) == len(items):
        return keep
    return _cascade_optics(keep, extra_parents)


def _ensure_optics(state: CharacterState) -> list[str]:
    warnings: list[str] = []
    specs = {item["id"]: item for item in catalog().get("optics") or []}
    by_name = {(item["name"], item.get("category") or ""): item for item in specs.values()}
    items = _cascade_optics(list(state.optics or []))
    kept: list[GearInstall] = []
    for inst in items:
        spec = specs.get(inst.gear_id)
        if not spec:
            continue
        if spec.get("requireparent") and not inst.parent_id:
            warnings.append(f"{spec['name']} は本体に装着してください")
            continue
        if inst.parent_id:
            parent = next((row for row in items if row.id == inst.parent_id), None)
            parent_spec = specs.get(parent.gear_id) if parent else None
            allowed = set(parent_spec.get("addoncategories") or []) if parent_spec else set()
            if allowed and spec.get("category") not in allowed:
                warnings.append(f"{spec['name']} は {parent_spec.get('name') if parent_spec else '本体'} に装着できません")
                continue
        kept.append(inst)
    have = {(row.parent_id, (specs.get(row.gear_id) or {}).get("name")) for row in kept}
    extra: list[GearInstall] = []
    for inst in kept:
        if inst.parent_id:
            continue
        spec = specs.get(inst.gear_id) or {}
        for gift in spec.get("included") or []:
            child = by_name.get((gift.get("name"), gift.get("category") or "")) or next(
                (item for item in specs.values() if item["name"] == gift.get("name")),
                None,
            )
            if not child or (inst.id, child["name"]) in have:
                continue
            override = str(gift.get("capacity") or "").strip()
            plugin, expr = parse_capacity(override) if override else (False, "")
            extra.append(
                GearInstall(
                    gear_id=child["id"],
                    parent_id=inst.id,
                    included=True,
                    rating=int(gift.get("rating") or 1),
                    capacity_override=expr if override else None,
                )
            )
            have.add((inst.id, child["name"]))
    state.optics = kept + extra
    return warnings


def _resolve_optics(state: CharacterState) -> tuple[list[dict[str, Any]], int, list[str], list[str], list[tuple[str, list[dict[str, Any]]]]]:
    warnings = _ensure_optics(state)
    errors: list[str] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    specs = {item["id"]: item for item in catalog().get("optics") or []}
    public: list[dict[str, Any]] = []
    kept: list[GearInstall] = []
    nuyen = 0
    for inst in state.optics:
        spec = specs.get(inst.gear_id)
        if not spec:
            continue
        rating = _clamp_rating(spec, inst.rating)
        inst.rating = rating
        cost = 0 if inst.included else int(eval_formula(str(spec.get("cost") or "0"), rating, 0))
        nuyen += cost
        plugin = bool(spec.get("plugin"))
        cap_expr = inst.capacity_override if inst.capacity_override is not None else str(spec.get("capacity") or "")
        if inst.capacity_override is not None:
            plugin = True
        cap_cost = _capacity_value(cap_expr, rating) if plugin else 0.0
        cap_max = 0.0 if plugin else _capacity_value(str(spec.get("capacity") or ""), rating)
        nodes = substitute_rating(list(spec.get("bonus") or []), rating)
        if nodes:
            bonus_sources.append((spec["name"], nodes))
        kept.append(inst)
        public.append(
            {
                "id": inst.id,
                "gear_id": spec["id"],
                "name": spec["name"],
                "category": spec.get("category") or "",
                "rating": rating,
                "rating_max": int(spec.get("maxrating") or 0),
                "parent_id": inst.parent_id,
                "included": bool(inst.included),
                "plugin": plugin,
                "nuyen": cost,
                "capacity_cost": cap_cost,
                "capacity_used": 0.0,
                "capacity_max": cap_max,
                "addoncategories": list(spec.get("addoncategories") or []),
                "requireparent": bool(spec.get("requireparent")),
                "device_rating": _device_rating_of(spec, rating),
                "avail": spec.get("avail") or "",
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
    children: dict[str, list[dict[str, Any]]] = {}
    for item in public:
        if item["parent_id"]:
            children.setdefault(item["parent_id"], []).append(item)
    for item in public:
        kids = children.get(item["id"]) or []
        used = round(sum(float(kid.get("capacity_cost") or 0) for kid in kids), 4)
        item["capacity_used"] = int(used) if used == int(used) else used
        cap_max = float(item.get("capacity_max") or 0)
        if cap_max == int(cap_max):
            item["capacity_max"] = int(cap_max)
        if cap_max > 0 and float(item["capacity_used"]) > cap_max + 1e-9:
            errors.append(f"{item['name']} の容量超過（{item['capacity_used']:g}/{cap_max:g}）")
    state.optics = kept
    return public, nuyen, warnings, errors, bonus_sources


VEHICLE_INTERIOR_CATEGORIES = [
    "Commlink Accessories",
    "Electronics Accessories",
    "Communications and Countermeasures",
]


def _vehicle_interior_parent_spec(spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": spec.get("name") or "",
        "category": "Commlinks",
        "addoncategories": list(VEHICLE_INTERIOR_CATEGORIES),
    }


def _commlink_accessory_parent_spec(spec: dict[str, Any]) -> dict[str, Any]:
    addons = ["Commlink Accessories"]
    if spec.get("category") == "PI-Tac":
        addons.append("PI-Tac Programs")
    return {
        "name": spec.get("name") or "",
        "category": "Commlinks",
        "addoncategories": addons,
    }


def _weapon_details_match(weapon: dict[str, Any], expr: str) -> bool:
    raw = (expr or "").strip()
    if not raw:
        return True
    ammo = str(weapon.get("ammo") or "")
    name = str(weapon.get("name") or "")

    def _contains_ammo(match: re.Match[str]) -> str:
        return "True" if match.group(1) in ammo else "False"

    text = re.sub(r"contains\(\s*ammo\s*,\s*'([^']*)'\s*\)", _contains_ammo, raw)
    text = re.sub(r'contains\(\s*ammo\s*,\s*"([^"]*)"\s*\)', _contains_ammo, text)
    text = re.sub(r"name\s*!=\s*'([^']*)'", lambda m: "True" if name != m.group(1) else "False", text)
    text = re.sub(r"name\s*=\s*'([^']*)'", lambda m: "True" if name == m.group(1) else "False", text)
    text = re.sub(r"\band\b", "and", text)
    text = re.sub(r"\bor\b", "or", text)
    if not re.fullmatch(r"(?:True|False|and|or|\(|\)|\s)+", text):
        return False
    try:
        return bool(eval(text, {"__builtins__": {}}, {}))
    except Exception:
        return False


def ammo_fits_weapon(ammo: dict[str, Any], weapon: dict[str, Any]) -> bool:
    if (ammo.get("category") or "") != "Ammunition":
        return False
    details = str(ammo.get("weapon_details") or "").strip()
    if details:
        return _weapon_details_match(weapon, details)
    types = [part for part in (ammo.get("ammo_weapon_types") or []) if part]
    if not types:
        return False
    weapon_type = str(weapon.get("weapon_type") or "")
    return weapon_type in types


def _add_signed_stat(raw: str | None, delta: int) -> str:
    text = str(raw or "").strip()
    if not delta:
        return text
    match = re.match(r"^([+-]?\d+)(.*)$", text)
    if match:
        return f"{int(match.group(1)) + delta}{match.group(2)}"
    if text in {"", "-", "—"}:
        return str(delta)
    return text


def _set_damage_type(damage: str, dtype: str) -> str:
    match = re.match(r"^([+-]?\d+)(.*)$", str(damage or "").strip())
    if not match:
        return dtype
    return f"{match.group(1)}{dtype}"


def _apply_ammo_bonus(weapon: dict[str, Any], bonus: dict[str, Any] | None) -> None:
    if not bonus:
        return
    if bonus.get("apreplace"):
        weapon["ap"] = str(bonus["apreplace"])
    elif bonus.get("ap"):
        weapon["ap"] = _add_signed_stat(str(weapon.get("ap") or ""), _leading_int(str(bonus.get("ap"))) or 0)
    if bonus.get("damagereplace"):
        weapon["damage"] = str(bonus["damagereplace"])
    elif bonus.get("damage"):
        weapon["damage"] = _add_signed_stat(str(weapon.get("damage") or ""), _leading_int(str(bonus.get("damage"))) or 0)
    if bonus.get("damagetype"):
        weapon["damage"] = _set_damage_type(str(weapon.get("damage") or ""), str(bonus["damagetype"]))
    if bonus.get("modereplace"):
        weapon["mode"] = str(bonus["modereplace"])


def _apply_loaded_ammo(weapon: dict[str, Any], ammo: dict[str, Any] | None) -> None:
    if not ammo:
        return
    add_id = str(ammo.get("add_weapon_id") or "")
    if add_id:
        spec = _item_by_id("weapons", add_id)
        if spec:
            if spec.get("damage"):
                weapon["damage"] = str(spec.get("damage") or "")
            if spec.get("ap"):
                weapon["ap"] = str(spec.get("ap") or "")
    _apply_ammo_bonus(weapon, ammo.get("weaponbonus"))


def _pick_loaded_ammo(kids: list[dict[str, Any]], loaded_id: str | None) -> dict[str, Any] | None:
    loadable = [kid for kid in kids if kid.get("ammo_weapon_types")]
    if not loadable:
        return None
    if loaded_id:
        for kid in loadable:
            if kid.get("id") == loaded_id:
                return kid
    return loadable[0]


def _public_weapon(
    spec: dict[str, Any],
    *,
    inst_id: str,
    qty: int,
    nuyen: int,
    loaded_ammo_id: str | None = None,
    from_gear: bool = False,
    source_gear_id: str | None = None,
    from_ware: bool = False,
    source_ware_id: str | None = None,
) -> dict[str, Any]:
    return {
        "id": inst_id,
        "weapon_id": spec["id"],
        "name": spec["name"],
        "category": spec.get("category") or "",
        "type": spec.get("type") or "",
        "weapon_type": spec.get("weapon_type") or "",
        "accuracy": spec.get("accuracy") or "",
        "reach": spec.get("reach") or "",
        "damage": spec.get("damage") or "",
        "ap": spec.get("ap") or "",
        "mode": spec.get("mode") or "",
        "rc": spec.get("rc") or "",
        "ammo": spec.get("ammo") or "",
        "conceal": spec.get("conceal") or "",
        "mounts": list(spec.get("mounts") or []),
        "qty": qty,
        "nuyen": nuyen,
        "accessories": [],
        "ammo_gear": [],
        "loaded_ammo_id": loaded_ammo_id or "",
        "from_gear": from_gear,
        "source_gear_id": source_gear_id or "",
        "from_ware": from_ware,
        "source_ware_id": source_ware_id or "",
        "useskill": spec.get("useskill") or "",
        "avail": spec.get("avail") or "",
        "source": spec.get("source") or "",
        "page": spec.get("page") or "",
        "limb_str": None,
        "limb_agi": None,
    }


def _append_gear_weapons(weapons: list[dict[str, Any]], gear_items: list[dict[str, Any]]) -> None:
    taken = {str(row.get("id") or "") for row in weapons}
    for item in gear_items:
        if item.get("parent_id"):
            continue
        spec_id = str(item.get("add_weapon_id") or "")
        if not spec_id:
            continue
        spec = _item_by_id("weapons", spec_id)
        if not spec:
            continue
        gear_id = str(item.get("id") or "")
        if not gear_id or gear_id in taken:
            continue
        weapons.append(
            _public_weapon(
                spec,
                inst_id=gear_id,
                qty=max(1, int(item.get("qty") or 1)),
                nuyen=int(item.get("nuyen") or 0),
                from_gear=True,
                source_gear_id=gear_id,
            )
        )
        taken.add(gear_id)


_ATTR_TOKEN = re.compile(r"\{(STR|AGI)(?:Unaug|Base)?\}", re.I)


def _eval_attr_stat(raw: str, attrs: dict[str, int]) -> str:
    text = str(raw or "")
    if "{" not in text:
        return text
    values = {key.upper(): int(val) for key, val in attrs.items()}

    def _token(match: re.Match[str]) -> str:
        return str(values.get(match.group(1).upper(), 0))

    replaced = _ATTR_TOKEN.sub(_token, text)
    if "{" in replaced:
        return text

    def _try_eval(expr: str) -> str | None:
        compact = expr.replace(" ", "")
        if not re.fullmatch(r"[0-9+\-*/().]+", compact):
            return None
        try:
            return str(int(eval(compact, {"__builtins__": {}}, {})))
        except Exception:
            return None

    out = replaced
    while True:
        def _inner(match: re.Match[str]) -> str:
            value = _try_eval(match.group(1))
            return value if value is not None else match.group(0)

        nxt = re.sub(r"\(([0-9+\-*/. ]+)\)", _inner, out)
        if nxt == out:
            break
        out = nxt
    return out


def _drone_mod_limb_attrs(
    mod_id: str,
    ware_by_id: dict[str, dict[str, Any]],
    state: CharacterState,
) -> tuple[int, int]:
    inst = next((row for row in list(state.vehicle_mods or []) if row.id == mod_id), None)
    if not inst:
        return 0, 0
    spec = _item_by_id("vehicle_mods", inst.mod_id)
    if not spec:
        return 0, 0
    name = (spec.get("name") or "").lower()
    if "arm" not in name and "leg" not in name:
        return 0, 0
    body = 0
    pilot = 0
    parent_id = inst.parent_id or ""
    for kind in ("drones", "vehicles"):
        host = next((row for row in list(getattr(state, kind) or []) if row.id == parent_id), None)
        if not host:
            continue
        host_spec = _item_by_id(kind, host.gear_id)
        if not host_spec:
            continue
        body = _leading_vehicle_stat(host_spec.get("body"))
        pilot = _leading_vehicle_stat(host_spec.get("pilot"))
        break
    str_val = max(body, 0)
    agi_val = max(pilot, 0)
    str_bonus = 0
    agi_bonus = 0
    for kid in ware_by_id.values():
        if kid.get("parent_id") != mod_id:
            continue
        effect = _limb_attr_effect(kid.get("name") or "")
        if not effect:
            continue
        attr, mode = effect
        rating = int(kid.get("rating") or 1)
        if attr == "STR":
            if mode == "set":
                str_val = rating
            else:
                str_bonus = rating
        else:
            if mode == "set":
                agi_val = rating
            else:
                agi_bonus = rating
    return (
        min(str_val + str_bonus, max(body * 2, 1)),
        min(agi_val + agi_bonus, max(pilot * 2, 1)),
    )


def _ware_weapon_attr_values(
    ware: dict[str, Any],
    ware_by_id: dict[str, dict[str, Any]],
    state: CharacterState,
    attr_totals: dict[str, int] | None,
) -> tuple[int, int, bool]:
    node: dict[str, Any] | None = ware
    seen: set[str] = set()
    while node:
        nid = str(node.get("id") or "")
        if nid in seen:
            break
        seen.add(nid)
        if node.get("limb_str") is not None:
            return int(node.get("limb_str") or 0), int(node.get("limb_agi") or 0), True
        parent_id = str(node.get("parent_id") or "")
        if not parent_id:
            break
        nxt = ware_by_id.get(parent_id)
        if nxt:
            node = nxt
            continue
        str_val, agi_val = _drone_mod_limb_attrs(parent_id, ware_by_id, state)
        if str_val or agi_val:
            return str_val, agi_val, True
        break
    totals = attr_totals or {}
    raw = state.attributes or {}
    return (
        int(totals.get("STR") or raw.get("STR") or 1),
        int(totals.get("AGI") or raw.get("AGI") or 1),
        False,
    )


def _apply_ware_weapon_attrs(
    weapon: dict[str, Any],
    ware: dict[str, Any],
    ware_by_id: dict[str, dict[str, Any]],
    state: CharacterState,
    attr_totals: dict[str, int] | None,
) -> None:
    str_val, agi_val, from_limb = _ware_weapon_attr_values(ware, ware_by_id, state, attr_totals)
    attrs = {"STR": str_val, "AGI": agi_val}
    for key in ("damage", "ap", "accuracy", "reach"):
        weapon[key] = _eval_attr_stat(str(weapon.get(key) or ""), attrs)
    if from_limb:
        weapon["limb_str"] = str_val
        weapon["limb_agi"] = agi_val


def _append_ware_weapons(
    weapons: list[dict[str, Any]],
    ware_items: list[dict[str, Any]],
    state: CharacterState,
    attr_totals: dict[str, int] | None = None,
) -> None:
    taken = {str(row.get("id") or "") for row in weapons}
    ware_by_id = {str(item.get("id") or ""): item for item in ware_items if item.get("id")}
    for item in ware_items:
        spec_id = str(item.get("add_weapon_id") or "")
        if not spec_id:
            continue
        spec = _item_by_id("weapons", spec_id)
        if not spec:
            continue
        ware_id = str(item.get("id") or "")
        if not ware_id or ware_id in taken:
            continue
        row = _public_weapon(
            spec,
            inst_id=ware_id,
            qty=1,
            nuyen=int(item.get("nuyen") or 0),
            from_ware=True,
            source_ware_id=ware_id,
        )
        _apply_ware_weapon_attrs(row, item, ware_by_id, state, attr_totals)
        weapons.append(row)
        taken.add(ware_id)


def _misc_external_hosts(state: CharacterState) -> dict[str, tuple[str, dict[str, Any]]]:
    hosts: dict[str, tuple[str, dict[str, Any]]] = {}
    for inst in list(state.commlinks or []):
        spec = _item_by_id("commlinks", inst.gear_id)
        if spec:
            hosts[inst.id] = ("commlink", _commlink_accessory_parent_spec(spec))
    for inst, spec in _iter_vehicle_hosts(state):
        hosts[inst.id] = ("vehicle", _vehicle_interior_parent_spec(spec))
    for inst in list(state.weapons or []):
        spec = _item_by_id("weapons", inst.weapon_id)
        if spec:
            hosts[inst.id] = (
                "weapon",
                {
                    "name": spec.get("name") or "",
                    "category": spec.get("category") or "",
                    "ammo": spec.get("ammo") or "",
                    "weapon_type": spec.get("weapon_type") or "",
                    "type": spec.get("type") or "",
                },
            )
    return hosts


def _misc_child_fits(parent_spec: dict[str, Any], child_spec: dict[str, Any]) -> bool:
    parent_name = parent_spec.get("name") or ""
    parent_cat = parent_spec.get("category") or ""
    child_cat = child_spec.get("category") or ""
    allowed = [c for c in (parent_spec.get("addoncategories") or []) if c and c != "Custom"]
    req_names = [n for n in (child_spec.get("required_names") or []) if n]
    req_cats = [c for c in (child_spec.get("required_categories") or []) if c and c != "Custom"]
    if req_names or req_cats:
        return parent_name in req_names or parent_cat in req_cats
    if allowed:
        return child_cat in allowed
    if child_spec.get("requireparent"):
        return child_cat == parent_cat
    return False


def _misc_slot_stats(spec: dict[str, Any], inst: GearInstall, rating: int) -> tuple[bool, float, float]:
    if inst.capacity_override is not None:
        return True, _capacity_value(inst.capacity_override, rating), 0.0
    if spec.get("plugin"):
        expr = str(spec.get("plugin_capacity") or spec.get("capacity") or "")
        return True, _capacity_value(expr, rating), 0.0
    plugin_expr = str(spec.get("plugin_capacity") or "")
    host_expr = str(spec.get("host_capacity") or spec.get("capacity") or "")
    if plugin_expr:
        return False, 0.0, _capacity_value(host_expr, rating)
    return False, 0.0, 0.0


def _ensure_misc_gear(state: CharacterState) -> list[str]:
    warnings: list[str] = []
    specs = {item["id"]: item for item in catalog().get("gear") or []}
    by_name = {(item["name"], item.get("category") or ""): item for item in specs.values()}
    external = _misc_external_hosts(state)
    items = _cascade_optics(list(state.gear or []), set(external))
    kept: list[GearInstall] = []
    for inst in items:
        spec = specs.get(inst.gear_id)
        if not spec:
            continue
        if spec.get("requireparent") and not inst.parent_id:
            warnings.append(f"{spec['name']} は本体に装着してください")
            continue
        if inst.parent_id:
            parent = next((row for row in items if row.id == inst.parent_id), None)
            parent_spec = specs.get(parent.gear_id) if parent else None
            host = external.get(inst.parent_id)
            if parent_spec:
                fits = _misc_child_fits(parent_spec, spec)
                label = parent_spec.get("name") or "本体"
            elif host:
                kind, host_spec = host
                if kind == "weapon":
                    fits = ammo_fits_weapon(spec, host_spec)
                else:
                    fits = bool(inst.included) or _misc_child_fits(host_spec, spec)
                label = host_spec.get("name") or "本体"
            else:
                fits = False
                label = "本体"
            if not fits:
                warnings.append(f"{spec['name']} は {label} に装着できません")
                continue
        kept.append(inst)
    have = {(row.parent_id, (specs.get(row.gear_id) or {}).get("name")) for row in kept}
    extra: list[GearInstall] = []
    for inst in kept:
        if inst.parent_id:
            continue
        spec = specs.get(inst.gear_id) or {}
        for gift in spec.get("included") or []:
            child = by_name.get((gift.get("name"), gift.get("category") or "")) or next(
                (item for item in specs.values() if item["name"] == gift.get("name")),
                None,
            )
            if not child or (inst.id, child["name"]) in have:
                continue
            override = str(gift.get("capacity") or "").strip()
            _plugin, expr = parse_capacity(override) if override else (False, "")
            extra.append(
                GearInstall(
                    gear_id=child["id"],
                    parent_id=inst.id,
                    included=True,
                    rating=int(gift.get("rating") or 1),
                    capacity_override=expr if override else None,
                )
            )
            have.add((inst.id, child["name"]))
    state.gear = kept + extra
    return warnings


def _resolve_misc_gear(
    state: CharacterState,
    vehicles: list[dict[str, Any]] | None = None,
    weapons: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], int, list[str], list[str], list[tuple[str, list[dict[str, Any]]]]]:
    warnings = _ensure_misc_gear(state)
    errors: list[str] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    specs = {item["id"]: item for item in catalog().get("gear") or []}
    public: list[dict[str, Any]] = []
    kept: list[GearInstall] = []
    nuyen = 0
    by_id = {row.id: row for row in state.gear}
    unit_costs: dict[str, int] = {}
    # Parents first so children can reference Parent Cost.
    ordered = sorted(state.gear, key=lambda row: 1 if row.parent_id else 0)
    for inst in ordered:
        spec = specs.get(inst.gear_id)
        if not spec:
            continue
        extra_kind = str(spec.get("extra_kind") or "")
        extra = (inst.extra or "").strip()
        options = gear_extra_options(spec)
        if extra_kind == "skill":
            if extra and extra not in options:
                warnings.append(f"{spec['name']} のスキル指定が無効です（{extra}）")
                extra = ""
            if not extra:
                warnings.append(f"{spec['name']} のスキルを選んでください")
        elif extra_kind == "group":
            if extra and extra not in options:
                warnings.append(f"{spec['name']} のスキルグループ指定が無効です（{extra}）")
                extra = ""
            if not extra:
                warnings.append(f"{spec['name']} のスキルグループを選んでください")
        elif extra_kind == "text" and not extra:
            warnings.append(f"{spec['name']} の対象を入力してください")
        inst.extra = extra or None
        rating = _clamp_rating(spec, inst.rating)
        inst.rating = rating
        qty = max(1, min(99, int(inst.qty or 1)))
        inst.qty = qty
        cost_expr = str(spec.get("cost") or "0")
        extras: dict[str, int | float] = {}
        if inst.parent_id and "Parent Cost" in cost_expr:
            parent_unit = unit_costs.get(inst.parent_id)
            if parent_unit is None:
                parent = by_id.get(inst.parent_id)
                parent_spec = specs.get(parent.gear_id) if parent else None
                parent_unit = (
                    0
                    if not parent or not parent_spec or parent.included
                    else int(eval_formula(str(parent_spec.get("cost") or "0"), int(parent.rating or 1), 0))
                )
            extras["Parent Cost"] = int(parent_unit)
            extras["ParentCost"] = int(parent_unit)
        unit = 0 if inst.included else int(eval_formula(cost_expr, rating, 0, extras))
        unit_costs[inst.id] = unit
        cost = unit * qty
        nuyen += cost
        plugin, cap_cost, cap_max = _misc_slot_stats(spec, inst, rating)
        nodes = substitute_rating(list(spec.get("bonus") or []), rating)
        if nodes:
            bonus_sources.append((_program_label(spec, extra), nodes))
        kept.append(inst)
        public.append(
            {
                "id": inst.id,
                "gear_id": spec["id"],
                "name": spec["name"],
                "label": _program_label(spec, extra),
                "category": spec.get("category") or "",
                "rating": rating,
                "rating_max": int(spec.get("maxrating") or 0),
                "qty": qty,
                "parent_id": inst.parent_id,
                "included": bool(inst.included),
                "plugin": plugin,
                "extra": extra,
                "needs_extra": bool(extra_kind),
                "extra_kind": extra_kind,
                "extra_options": options,
                "nuyen": cost,
                "capacity_cost": cap_cost,
                "capacity_used": 0.0,
                "capacity_max": cap_max,
                "addoncategories": list(spec.get("addoncategories") or []),
                "requireparent": bool(spec.get("requireparent")),
                "required_names": list(spec.get("required_names") or []),
                "required_categories": list(spec.get("required_categories") or []),
                "ammo_weapon_types": list(spec.get("ammo_weapon_types") or []),
                "costfor": int(spec.get("costfor") or 0),
                "add_weapon": spec.get("add_weapon") or "",
                "add_weapon_id": spec.get("add_weapon_id") or "",
                "weaponbonus": dict(spec.get("weaponbonus") or {}),
                "loaded": False,
                "device_rating": _device_rating_of(spec, rating),
                "avail": spec.get("avail") or "",
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
    children: dict[str, list[dict[str, Any]]] = {}
    for item in public:
        if item["parent_id"]:
            children.setdefault(item["parent_id"], []).append(item)
    for item in public:
        kids = children.get(item["id"]) or []
        used = round(sum(float(kid.get("capacity_cost") or 0) for kid in kids), 4)
        item["capacity_used"] = int(used) if used == int(used) else used
        cap_max = float(item.get("capacity_max") or 0)
        if cap_max == int(cap_max):
            item["capacity_max"] = int(cap_max)
        if cap_max > 0 and float(item["capacity_used"]) > cap_max + 1e-9:
            errors.append(f"{item['name']} の容量超過（{item['capacity_used']:g}/{cap_max:g}）")
    for row in vehicles or []:
        kids = children.get(str(row.get("id") or "")) or []
        row["gear"] = kids
        extra_cost = sum(int(kid.get("nuyen") or 0) for kid in kids)
        row["nuyen"] = int(row.get("nuyen") or 0) + extra_cost
    for row in weapons or []:
        kids = children.get(str(row.get("id") or "")) or []
        row["ammo_gear"] = kids
        extra_cost = sum(int(kid.get("nuyen") or 0) for kid in kids)
        row["nuyen"] = int(row.get("nuyen") or 0) + extra_cost
        loaded = _pick_loaded_ammo(kids, str(row.get("loaded_ammo_id") or "") or None)
        if loaded:
            loaded["loaded"] = True
            row["loaded_ammo_id"] = loaded["id"]
            _apply_loaded_ammo(row, loaded)
        else:
            row["loaded_ammo_id"] = ""
    state.gear = kept
    return public, nuyen, warnings, errors, bonus_sources


def _resolve_programs(
    state: CharacterState,
    cyberdecks: list[dict[str, Any]],
    rccs: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int, list[str]]:
    warnings: list[str] = []
    specs = {item["id"]: item for item in catalog().get("programs") or []}
    hosts: dict[str, tuple[str, dict[str, Any]]] = {}
    for row in cyberdecks:
        hosts[str(row.get("id") or "")] = ("cyberdecks", row)
    for row in rccs:
        hosts[str(row.get("id") or "")] = ("rccs", row)
    kept: list[GearInstall] = []
    public: list[dict[str, Any]] = []
    nuyen = 0
    for inst in list(state.programs or []):
        spec = specs.get(inst.gear_id)
        if not spec:
            continue
        want_kind = PROGRAM_HOSTS.get(str(spec.get("category") or ""), "cyberdecks")
        host = hosts.get(inst.parent_id or "")
        if not inst.parent_id or not host:
            warnings.append(f"{spec['name']} は本体に装着してください")
            continue
        kind, _parent = host
        if kind != want_kind:
            label = "サイバーデッキ" if want_kind == "cyberdecks" else "RCC"
            warnings.append(f"{spec['name']} は{label}に装着してください")
            continue
        extra_kind = str(spec.get("extra_kind") or "")
        extra = (inst.extra or "").strip()
        options = gear_extra_options(spec)
        if extra_kind == "skill":
            if extra and extra not in options:
                warnings.append(f"{spec['name']} のスキル指定が無効です（{extra}）")
                extra = ""
            if not extra:
                warnings.append(f"{spec['name']} のスキルを選んでください")
        elif extra_kind == "group":
            if extra and extra not in options:
                warnings.append(f"{spec['name']} のスキルグループ指定が無効です（{extra}）")
                extra = ""
            if not extra:
                warnings.append(f"{spec['name']} のスキルグループを選んでください")
        elif extra_kind == "text" and not extra:
            warnings.append(f"{spec['name']} の対象を入力してください")
        inst.extra = extra or None
        rating = _clamp_rating(spec, inst.rating)
        inst.rating = rating
        cost = int(eval_formula(str(spec.get("cost") or "0"), rating, 0))
        nuyen += cost
        kept.append(inst)
        public.append(
            {
                "id": inst.id,
                "gear_id": spec["id"],
                "name": spec["name"],
                "label": _program_label(spec, extra),
                "category": spec.get("category") or "",
                "rating": rating,
                "rating_max": int(spec.get("maxrating") or 0),
                "parent_id": inst.parent_id,
                "extra": extra,
                "needs_extra": bool(extra_kind),
                "extra_kind": extra_kind,
                "extra_options": options,
                "nuyen": cost,
                "program_host": spec.get("program_host") or want_kind,
                "avail": spec.get("avail") or "",
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
    children: dict[str, list[dict[str, Any]]] = {}
    for item in public:
        children.setdefault(str(item.get("parent_id") or ""), []).append(item)
    for row in list(cyberdecks) + list(rccs):
        kids = children.get(str(row.get("id") or "")) or []
        row["program_used"] = len(kids)
        row["program_max"] = int(row.get("programs") or 0)
        if row["program_max"] > 0 and len(kids) > row["program_max"]:
            warnings.append(f"{row['name']} のプログラムが上限超過（{len(kids)}/{row['program_max']}）")
        keys = [f"{kid['name']}|{kid.get('extra') or ''}" for kid in kids]
        if len(keys) != len(set(keys)):
            warnings.append(f"{row['name']} に同じプログラムが重複しています")
    state.programs = kept
    return public, nuyen, warnings


def _ensure_sensors(state: CharacterState) -> list[str]:
    warnings: list[str] = []
    specs = {item["id"]: item for item in catalog().get("sensors") or []}
    by_name = {(item["name"], item.get("category") or ""): item for item in specs.values()}
    drone_ids = {row.id for row in state.drones or []}
    vehicle_ids = {row.id for row in state.vehicles or []}
    host_ids = drone_ids | vehicle_ids
    items = _cascade_optics(list(state.sensors or []), host_ids)
    kept: list[GearInstall] = []
    for inst in items:
        spec = specs.get(inst.gear_id)
        if not spec:
            continue
        if spec.get("requireparent") and not inst.parent_id:
            warnings.append(f"{spec['name']} は本体に装着してください")
            continue
        if inst.parent_id:
            parent = next((row for row in items if row.id == inst.parent_id), None)
            if parent:
                parent_spec = specs.get(parent.gear_id) if parent else None
                allowed = set(parent_spec.get("addoncategories") or []) if parent_spec else set()
                if allowed and spec.get("category") not in allowed:
                    warnings.append(f"{spec['name']} は {parent_spec.get('name') if parent_spec else '本体'} に装着できません")
                    continue
            elif inst.parent_id in host_ids:
                if spec.get("category") not in {"Sensors", "Sensor Housings"}:
                    warnings.append(f"{spec['name']} は車両に装着できません")
                    continue
            else:
                warnings.append(f"{spec['name']} は本体に装着してください")
                continue
        kept.append(inst)
    have = {(row.parent_id, (specs.get(row.gear_id) or {}).get("name")) for row in kept}
    extra: list[GearInstall] = []
    for inst in kept:
        if inst.parent_id:
            continue
        spec = specs.get(inst.gear_id) or {}
        for gift in spec.get("included") or []:
            child = by_name.get((gift.get("name"), gift.get("category") or "")) or next(
                (item for item in specs.values() if item["name"] == gift.get("name")),
                None,
            )
            if not child or (inst.id, child["name"]) in have:
                continue
            override = str(gift.get("capacity") or "").strip()
            _plugin, expr = parse_capacity(override) if override else (False, "")
            extra.append(
                GearInstall(
                    gear_id=child["id"],
                    parent_id=inst.id,
                    included=True,
                    rating=int(gift.get("rating") or 1),
                    capacity_override=expr if override else None,
                )
            )
            have.add((inst.id, child["name"]))
    state.sensors = kept + extra
    return warnings


def _plugin_capacity_expr(spec: dict[str, Any], inst: GearInstall, host_ids: set[str] | None = None) -> tuple[bool, str, float]:
    rating = int(inst.rating or 1)
    if inst.capacity_override is not None:
        return True, str(inst.capacity_override), _capacity_value(inst.capacity_override, rating)
    if inst.parent_id and inst.parent_id in (host_ids or set()):
        expr = str(spec.get("host_capacity") or spec.get("capacity") or "")
        return False, expr, _capacity_value(expr, rating)
    if inst.parent_id:
        expr = str(spec.get("plugin_capacity") or spec.get("capacity") or "")
        return True, expr, _capacity_value(expr, rating)
    if spec.get("plugin"):
        expr = str(spec.get("capacity") or "")
        return True, expr, _capacity_value(expr, rating)
    expr = str(spec.get("host_capacity") or spec.get("capacity") or "")
    return False, expr, _capacity_value(expr, rating)


def _resolve_sensors(state: CharacterState) -> tuple[list[dict[str, Any]], int, list[str], list[str], list[tuple[str, list[dict[str, Any]]]]]:
    warnings = _ensure_sensors(state)
    errors: list[str] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    specs = {item["id"]: item for item in catalog().get("sensors") or []}
    public: list[dict[str, Any]] = []
    kept: list[GearInstall] = []
    nuyen = 0
    for inst in state.sensors:
        spec = specs.get(inst.gear_id)
        if not spec:
            continue
        rating = _clamp_rating(spec, inst.rating)
        inst.rating = rating
        cost = 0 if inst.included else int(eval_formula(str(spec.get("cost") or "0"), rating, 0))
        nuyen += cost
        plugin, _expr, cap_value = _plugin_capacity_expr(
            spec,
            inst,
            {row.id for row in list(state.drones or []) + list(state.vehicles or [])},
        )
        cap_cost = cap_value if plugin else 0.0
        cap_max = 0.0 if plugin else cap_value
        nodes = substitute_rating(list(spec.get("bonus") or []), rating)
        if nodes:
            bonus_sources.append((spec["name"], nodes))
        kept.append(inst)
        public.append(
            {
                "id": inst.id,
                "gear_id": spec["id"],
                "name": spec["name"],
                "category": spec.get("category") or "",
                "rating": rating,
                "rating_max": int(spec.get("maxrating") or 0),
                "parent_id": inst.parent_id,
                "included": bool(inst.included),
                "plugin": plugin,
                "nuyen": cost,
                "capacity_cost": cap_cost,
                "capacity_used": 0.0,
                "capacity_max": cap_max,
                "addoncategories": list(spec.get("addoncategories") or []),
                "requireparent": bool(spec.get("requireparent")),
                "device_rating": _device_rating_of(spec, rating),
                "avail": spec.get("avail") or "",
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
    children: dict[str, list[dict[str, Any]]] = {}
    for item in public:
        if item["parent_id"]:
            children.setdefault(item["parent_id"], []).append(item)
    for item in public:
        kids = children.get(item["id"]) or []
        used = round(sum(float(kid.get("capacity_cost") or 0) for kid in kids), 4)
        item["capacity_used"] = int(used) if used == int(used) else used
        cap_max = float(item.get("capacity_max") or 0)
        if cap_max == int(cap_max):
            item["capacity_max"] = int(cap_max)
        if cap_max > 0 and float(item["capacity_used"]) > cap_max + 1e-9:
            errors.append(f"{item['name']} の容量超過（{item['capacity_used']:g}/{cap_max:g}）")
    state.sensors = kept
    return public, nuyen, warnings, errors, bonus_sources


def _has_weapon_constraints(cons: dict[str, Any] | None) -> bool:
    if not cons:
        return False
    return bool(
        cons.get("names")
        or cons.get("categories")
        or cons.get("types")
        or cons.get("conceal_lte") is not None
    )


def _weapon_matches_or(weapon: dict[str, Any], cons: dict[str, Any] | None) -> bool:
    if not _has_weapon_constraints(cons):
        return False
    cons = cons or {}
    name = str(weapon.get("name") or "")
    category = str(weapon.get("category") or "")
    typ = str(weapon.get("type") or "")
    try:
        conceal = int(float(str(weapon.get("conceal") or "0")))
    except ValueError:
        conceal = 0
    if name in (cons.get("names") or []):
        return True
    if category in (cons.get("categories") or []):
        return True
    if typ in (cons.get("types") or []):
        return True
    if cons.get("conceal_lte") is not None and conceal <= int(cons["conceal_lte"]):
        return True
    return False


def accessory_fits_weapon(acc: dict[str, Any], weapon: dict[str, Any], installed_names: set[str]) -> bool:
    required = acc.get("required") or {}
    forbidden = acc.get("forbidden") or {}
    if _has_weapon_constraints(required) and not _weapon_matches_or(weapon, required):
        return False
    if _weapon_matches_or(weapon, forbidden):
        return False
    for name in forbidden.get("accessories") or []:
        if name in installed_names:
            return False
    mounts = list(acc.get("mounts") or [])
    weapon_mounts = set(weapon.get("mounts") or [])
    if mounts and not any(mount in weapon_mounts or mount == "Internal" for mount in mounts):
        return False
    return True


def _pick_accessory_mount(weapon_mounts: list[str], used: set[str], acc_mounts: list[str]) -> str | None:
    if not acc_mounts:
        return ""
    options = [mount for mount in acc_mounts if mount in weapon_mounts or mount == "Internal"]
    if not options:
        return None
    for mount in options:
        if mount not in used:
            return mount
    return None


def _leading_int(raw: str | None) -> int | None:
    match = re.match(r"^([+-]?\d+)", str(raw or "").strip())
    if not match:
        return None
    return int(match.group(1))


def _add_leading_int(raw: str | None, delta: int) -> str:
    text = str(raw or "").strip()
    if not delta:
        return text
    match = re.match(r"^([+-]?\d+)(.*)$", text)
    if not match:
        return text
    return f"{int(match.group(1)) + delta}{match.group(2)}"


def _replace_leading_int(raw: str | None, value: int) -> str:
    text = str(raw or "").strip()
    match = re.match(r"^([+-]?\d+)(.*)$", text)
    if not match:
        return str(value)
    return f"{int(value)}{match.group(2)}"


def resolve_attribute_selects(
    state: CharacterState,
    effects: dict[str, Any],
    qualities: list[dict[str, Any]],
) -> tuple[dict[str, int], list[str]]:
    warnings: list[str] = []
    bonus: dict[str, int] = {}
    extras = state.quality_extras or {}
    by_name = {q["name"]: q for q in qualities}
    for sel in effects.get("attribute_selects") or []:
        source = str(sel.get("source") or "")
        spec = by_name.get(source)
        if not spec:
            continue
        picked = ATTR_ALIASES.get(str(extras.get(spec["id"]) or "").strip().upper())
        exclude = {str(item) for item in (sel.get("exclude") or [])}
        max_bonus = max(1, int(sel.get("max") or 1))
        if not picked:
            warnings.append(f"{source} の属性を選んでください")
            continue
        if picked in exclude or picked in {"ESS"}:
            warnings.append(f"{source} に {picked} は選べません")
            continue
        bonus[picked] = int(bonus.get(picked) or 0) + max_bonus
    return bonus, warnings


def apply_lifestyle_cost_mod(gear: dict[str, Any], percent: int) -> None:
    if not percent:
        return
    factor = (100 + int(percent)) / 100.0
    delta = 0
    for row in gear.get("lifestyles") or []:
        before = int(row.get("nuyen") or 0)
        monthly = int(row.get("monthly") or 0)
        after = int(round(before * factor))
        row["monthly"] = int(round(monthly * factor))
        row["nuyen"] = after
        row["lifestyle_cost_mod"] = int(percent)
        delta += after - before
    if gear.get("lifestyle") and (gear.get("lifestyles") or []):
        gear["lifestyle"] = (gear.get("lifestyles") or [])[0]
    gear["nuyen"] = int(gear.get("nuyen") or 0) + delta


def resolve_movement(meta: dict[str, Any], effects: dict[str, Any]) -> dict[str, Any]:
    category = "Ground"
    walk = str(meta.get("walk") or "2/1/0")
    run = str(meta.get("run") or "4/0/0")
    sprint = str(meta.get("sprint") or "2/1/0")
    replace = effects.get("movement_replace") or {}
    if (category, "walk") in replace:
        walk = _replace_leading_int(walk, int(replace[(category, "walk")]))
    if (category, "run") in replace:
        run = _replace_leading_int(run, int(replace[(category, "run")]))
    walk = _add_leading_int(walk, int((effects.get("walk_multiplier") or {}).get(category) or 0))
    run = _add_leading_int(run, int((effects.get("run_multiplier") or {}).get(category) or 0))
    sprint_bonus = int((effects.get("sprint_bonus") or {}).get(category) or 0)
    return {
        "walk": walk,
        "run": run,
        "sprint": sprint,
        "sprint_bonus": sprint_bonus,
    }


def apply_reach_bonus(weapons: list[dict[str, Any]] | None, reach: int) -> None:
    if not reach:
        return
    for weapon in weapons or []:
        if str(weapon.get("type") or "") != "Melee":
            continue
        weapon["reach"] = _add_leading_int(str(weapon.get("reach") or "0"), int(reach))


def _ensure_weapon_accessories(state: CharacterState) -> list[str]:
    warnings: list[str] = []
    specs = {item["id"]: item for item in catalog().get("weapon_accessories") or []}
    by_name = {item["name"]: item for item in specs.values()}
    weapons = {item.id: item for item in state.weapons}
    weapon_specs = {item["id"]: item for item in catalog().get("weapons") or []}
    kept: list[WeaponAccessoryInstall] = []
    for inst in list(state.weapon_accessories or []):
        spec = specs.get(inst.accessory_id)
        parent = weapons.get(inst.parent_id or "")
        if not spec or not parent:
            if spec:
                warnings.append(f"{spec['name']} は武器に装着してください")
            continue
        kept.append(inst)
    have_included = {
        (row.parent_id, (specs.get(row.accessory_id) or {}).get("name"))
        for row in kept
        if row.included
    }
    extra: list[WeaponAccessoryInstall] = []
    for weapon in state.weapons:
        wspec = weapon_specs.get(weapon.weapon_id) or {}
        for gift_name in wspec.get("included") or []:
            child = by_name.get(gift_name)
            if not child or (weapon.id, child["name"]) in have_included:
                continue
            extra.append(
                WeaponAccessoryInstall(
                    accessory_id=child["id"],
                    parent_id=weapon.id,
                    included=True,
                )
            )
            have_included.add((weapon.id, child["name"]))
    preferred: dict[tuple[str, str], WeaponAccessoryInstall] = {}
    for inst in kept + extra:
        key = (inst.parent_id or "", inst.accessory_id)
        prev = preferred.get(key)
        if prev is None or (inst.included and not prev.included):
            preferred[key] = inst
    state.weapon_accessories = list(preferred.values())
    return warnings


def _resolve_weapon_accessories(
    state: CharacterState,
    weapons: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int, list[str], list[str]]:
    warnings = _ensure_weapon_accessories(state)
    errors: list[str] = []
    specs = {item["id"]: item for item in catalog().get("weapon_accessories") or []}
    weapon_specs = {item["id"]: item for item in catalog().get("weapons") or []}
    qty_by_id = {item.id: max(1, int(item.qty or 1)) for item in state.weapons}
    public: list[dict[str, Any]] = []
    kept: list[WeaponAccessoryInstall] = []
    nuyen = 0
    children: dict[str, list[WeaponAccessoryInstall]] = {}
    for inst in list(state.weapon_accessories or []):
        children.setdefault(inst.parent_id or "", []).append(inst)

    for weapon in weapons:
        used_mounts: set[str] = set()
        installed_names = {
            str((specs.get(row.accessory_id) or {}).get("name") or "")
            for row in children.get(weapon["id"]) or []
        }
        for inst in children.get(weapon["id"]) or []:
            spec = specs.get(inst.accessory_id)
            if not spec:
                continue
            rating = _clamp_rating(spec, inst.rating)
            inst.rating = rating
            names_without = installed_names - {spec["name"]}
            if not accessory_fits_weapon(spec, weapon, names_without):
                warnings.append(f"{spec['name']} は {weapon['name']} に装着できません")
                continue
            mount = _pick_accessory_mount(list(weapon.get("mounts") or []), used_mounts, list(spec.get("mounts") or []))
            if mount is None:
                errors.append(f"{weapon['name']} のマウントが足りません（{spec['name']}）")
                mount = ""
            elif mount:
                used_mounts.add(mount)
            inst.mount = mount
            parent_unit = int(eval_formula(str((weapon_specs.get(str(weapon.get("weapon_id") or "")) or {}).get("cost") or "0"), 1, 0))
            cost = 0 if inst.included else int(
                eval_formula(str(spec.get("cost") or "0"), rating, 0, extras={"Weapon Cost": parent_unit})
            )
            cost *= int(qty_by_id.get(weapon["id"]) or 1)
            nuyen += cost
            acc_bonus = {
                "accuracy": _leading_int(spec.get("accuracy")) or 0,
                "rc": _leading_int(spec.get("rc")) or 0,
                "conceal": _leading_int(spec.get("conceal")) or 0,
                "damage": _leading_int(spec.get("damage")) or 0,
                "ap": _leading_int(spec.get("ap")) or 0,
                "reach": _leading_int(spec.get("reach")) or 0,
            }
            weapon["accuracy"] = _add_leading_int(str(weapon.get("accuracy") or ""), acc_bonus["accuracy"])
            weapon["rc"] = _add_leading_int(str(weapon.get("rc") or "0") or "0", acc_bonus["rc"])
            weapon["conceal"] = _add_leading_int(str(weapon.get("conceal") or "0") or "0", acc_bonus["conceal"])
            weapon["damage"] = _add_leading_int(str(weapon.get("damage") or ""), acc_bonus["damage"])
            weapon["ap"] = _add_leading_int(str(weapon.get("ap") or ""), acc_bonus["ap"])
            if acc_bonus["reach"]:
                weapon["reach"] = _add_leading_int(str(weapon.get("reach") or "0") or "0", acc_bonus["reach"])
            weapon["nuyen"] = int(weapon.get("nuyen") or 0) + cost
            kept.append(inst)
            public.append(
                {
                    "id": inst.id,
                    "accessory_id": spec["id"],
                    "name": spec["name"],
                    "parent_id": inst.parent_id,
                    "included": bool(inst.included),
                    "mount": mount,
                    "rating": rating,
                    "rating_max": int(spec.get("maxrating") or 0),
                    "nuyen": cost,
                    "accuracy": spec.get("accuracy") or "",
                    "rc": spec.get("rc") or "",
                    "avail": spec.get("avail") or "",
                    "source": spec.get("source") or "",
                    "page": spec.get("page") or "",
                }
            )
        weapon["accessories"] = [item for item in public if item.get("parent_id") == weapon["id"]]
        weapon["mounts_used"] = sorted(used_mounts)

    state.weapon_accessories = kept
    return public, nuyen, warnings, errors


def _resolve_apps(state: CharacterState, commlinks: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int, list[str]]:
    warnings: list[str] = []
    specs = {item["id"]: item for item in catalog().get("apps") or []}
    hosts = {str(row.get("id") or ""): row for row in commlinks}
    kept: list[GearInstall] = []
    public: list[dict[str, Any]] = []
    nuyen = 0
    for inst in list(state.apps or []):
        spec = specs.get(inst.gear_id)
        if not spec:
            continue
        host = hosts.get(inst.parent_id or "")
        if not inst.parent_id or not host:
            warnings.append(f"{spec['name']} は通信機に装着してください")
            continue
        extra_kind = str(spec.get("extra_kind") or "")
        extra = (inst.extra or "").strip()
        options = gear_extra_options(spec)
        if extra_kind == "skill":
            if extra and extra not in options:
                warnings.append(f"{spec['name']} のスキル指定が無効です（{extra}）")
                extra = ""
            if not extra:
                warnings.append(f"{spec['name']} のスキルを選んでください")
        elif extra_kind == "group":
            if extra and extra not in options:
                warnings.append(f"{spec['name']} のスキルグループ指定が無効です（{extra}）")
                extra = ""
            if not extra:
                warnings.append(f"{spec['name']} のスキルグループを選んでください")
        elif extra_kind == "text" and not extra:
            warnings.append(f"{spec['name']} の対象を入力してください")
        inst.extra = extra or None
        rating = _clamp_rating(spec, inst.rating)
        inst.rating = rating
        cost = int(eval_formula(str(spec.get("cost") or "0"), rating, 0))
        nuyen += cost
        kept.append(inst)
        public.append(
            {
                "id": inst.id,
                "gear_id": spec["id"],
                "name": spec["name"],
                "label": _program_label(spec, extra),
                "category": spec.get("category") or "",
                "rating": rating,
                "rating_max": int(spec.get("maxrating") or 0),
                "parent_id": inst.parent_id,
                "extra": extra,
                "needs_extra": bool(extra_kind),
                "extra_kind": extra_kind,
                "extra_options": options,
                "nuyen": cost,
                "avail": spec.get("avail") or "",
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
    children: dict[str, list[dict[str, Any]]] = {}
    for item in public:
        children.setdefault(str(item.get("parent_id") or ""), []).append(item)
    for row in commlinks:
        kids = children.get(str(row.get("id") or "")) or []
        row["apps"] = kids
        keys = [f"{kid['name']}|{kid.get('extra') or ''}" for kid in kids]
        if len(keys) != len(set(keys)):
            warnings.append(f"{row['name']} に同じアプリが重複しています")
    state.apps = kept
    return public, nuyen, warnings


def _leading_vehicle_stat(raw: str | None) -> int:
    match = re.match(r"^([+-]?\d+)", str(raw or "").strip())
    if not match:
        return 0
    return int(match.group(1))


def _format_vehicle_stat(base: str, current: int, offroad: int | None = None) -> str:
    parts = str(base or "").split("/")
    if len(parts) > 1 or offroad is not None:
        off = offroad if offroad is not None else _leading_vehicle_stat(parts[1] if len(parts) > 1 else "")
        return f"{current}/{off}"
    return str(current)


def _vehicle_extras(spec: dict[str, Any], stats: dict[str, int], cost: int) -> dict[str, int | float]:
    return {
        "Body": stats.get("body") or 0,
        "body": stats.get("body") or 0,
        "Armor": stats.get("armor") or 0,
        "Handling": stats.get("handling") or 0,
        "Speed": stats.get("speed") or 0,
        "Acceleration": stats.get("accel") or 0,
        "Sensor": stats.get("sensor") or 0,
        "Pilot": stats.get("pilot") or 0,
        "Seats": stats.get("seats") or 0,
        "Vehicle Cost": cost,
    }


def vehicle_matches(vehicle: dict[str, Any], cons: dict[str, Any] | None) -> bool:
    cons = cons or {}
    names = list(cons.get("names") or [])
    contains = list(cons.get("category_contains") or [])
    equals = list(cons.get("category_equals") or [])
    body_lte = cons.get("body_lte")
    body_gte = cons.get("body_gte")
    if not names and not contains and not equals and body_lte is None and body_gte is None:
        return True
    name = str(vehicle.get("name") or "")
    category = str(vehicle.get("category") or "")
    body = _leading_vehicle_stat(str(vehicle.get("body") or "0"))
    if names and name not in names:
        return False
    if contains and not any(part in category for part in contains):
        return False
    if equals and category not in equals:
        return False
    if body_lte is not None and body > int(body_lte):
        return False
    if body_gte is not None and body < int(body_gte):
        return False
    return True


def mod_fits_vehicle(mod: dict[str, Any], vehicle: dict[str, Any]) -> bool:
    if not vehicle_matches(vehicle, mod.get("required")):
        return False
    forbidden = mod.get("forbidden") or {}
    has_forbidden = bool(
        forbidden.get("names")
        or forbidden.get("category_contains")
        or forbidden.get("category_equals")
        or forbidden.get("body_lte") is not None
        or forbidden.get("body_gte") is not None
    )
    if has_forbidden and vehicle_matches(vehicle, forbidden):
        return False
    return True


def _apply_vehicle_bonus(stats: dict[str, int], nodes: list[dict[str, Any]], rating: int) -> None:
    aliases = {
        "handling": "handling",
        "offroadhandling": "offroadhandling",
        "speed": "speed",
        "accel": "accel",
        "offroadaccel": "offroadaccel",
        "body": "body",
        "armor": "armor",
        "pilot": "pilot",
        "sensor": "sensor",
        "seats": "seats",
    }
    for node in substitute_rating(list(nodes or []), rating):
        tag = str(node.get("tag") or "")
        key = aliases.get(tag)
        if not key:
            continue
        raw = str(node.get("value") or "").strip()
        if raw.lower() == "rating":
            stats[key] = int(rating)
            continue
        delta = int(eval_formula(raw, rating, 0))
        if raw.startswith("+") or raw.startswith("-"):
            stats[key] = int(stats.get(key) or 0) + delta
        else:
            stats[key] = delta


def _clamp_vehicle_rating(spec: dict[str, Any], rating: int, extras: dict[str, int | float]) -> int:
    max_expr = str(spec.get("maxrating_expr") or spec.get("maxrating") or "0")
    min_expr = str(spec.get("minrating_expr") or spec.get("minrating") or "0")
    max_rating = int(eval_formula(max_expr, rating or 1, 0, extras)) if max_expr else int(spec.get("maxrating") or 0)
    if max_rating <= 0:
        return 1
    min_rating = int(eval_formula(min_expr, rating or 1, 1, extras)) if min_expr else 1
    min_rating = max(1, min_rating)
    return max(min_rating, min(max_rating, int(rating or min_rating)))


def _find_mount_part(name: str, category: str, prefer_source: str = "") -> dict[str, Any] | None:
    parts = [item for item in catalog().get("weapon_mounts") or [] if item.get("category") == category]
    if prefer_source == "SR5":
        tagged = next((item for item in parts if item["name"] == f"{name} [SR5]"), None)
        if tagged:
            return tagged
    exact = next((item for item in parts if item["name"] == name), None)
    if exact:
        return exact
    return next((item for item in parts if item["name"] == f"{name} [SR5]"), None)


def _default_mount_parts(size: dict[str, Any]) -> dict[str, dict[str, Any] | None]:
    parts = catalog().get("weapon_mounts") or []

    def pick(category: str, names: list[str]) -> dict[str, Any] | None:
        for name in names:
            found = next((item for item in parts if item.get("category") == category and item["name"] == name), None)
            if found:
                return found
        return None

    required = size.get("required_parts") or {}
    if any(name == "None" for name in (required.get("control") or [])):
        return {
            "visibility": pick("Visibility", ["None"]),
            "flexibility": pick("Flexibility", ["None"]),
            "control": pick("Control", ["None"]),
        }
    if size.get("source") == "SR5":
        req_vis = list(required.get("visibility") or ["External [SR5]"])
        req_flex = list(required.get("flexibility") or ["Flexible [SR5]"])
        req_ctrl = list(required.get("control") or ["Remote [SR5]"])
        return {
            "visibility": pick("Visibility", req_vis),
            "flexibility": pick("Flexibility", req_flex),
            "control": pick("Control", req_ctrl),
        }
    return {
        "visibility": pick("Visibility", ["External", "External [SR5]"]),
        "flexibility": pick("Flexibility", ["Fixed", "Flexible [SR5]"]),
        "control": pick("Control", ["Remote", "Remote [SR5]"]),
    }


R5_MOD_SLOT_CATEGORIES = (
    "Powertrain",
    "Protection",
    "Weapons",
    "Body",
    "Electromagnetic",
    "Cosmetic",
)
R5_SLOT_LABELS = {
    "Powertrain": "パワートレイン",
    "Protection": "防護",
    "Weapons": "武器",
    "Body": "ボディ",
    "Electromagnetic": "電磁",
    "Cosmetic": "外装",
}
R5_SLOT_ADD_KEYS = {
    "Powertrain": "powertrainmodslots",
    "Protection": "protectionmodslots",
    "Weapons": "weaponmodslots",
    "Body": "bodymodslots",
    "Electromagnetic": "electromagneticmodslots",
    "Cosmetic": "cosmeticmodslots",
}


def _host_is_drone(row: dict[str, Any]) -> bool:
    return str(row.get("category") or "").startswith("Drones")


def _add_vehicle_slot_use(parent: dict[str, Any], slots: int, category: str, included: bool) -> None:
    if included:
        return
    used = max(0, int(slots))
    if _host_is_drone(parent):
        parent["slots_used"] = int(parent.get("slots_used") or 0) + used
        return
    if category not in R5_SLOT_ADD_KEYS:
        return
    tracks = parent.setdefault("_slot_used", {})
    tracks[category] = int(tracks.get(category) or 0) + used


def _finalize_vehicle_slots(hosts: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for row in hosts:
        body = int((row.get("stats") or {}).get("body") or _leading_vehicle_stat(str(row.get("body") or "0")))
        if _host_is_drone(row):
            listed = row.get("modslots")
            maximum = int(listed) if listed is not None else body
            used = int(row.get("slots_used") or 0)
            row["slots_max"] = maximum
            row["slot_tracks"] = []
            if used > maximum:
                errors.append(f"{row['name']} の改造スロット超過（{used}/{maximum}）")
            continue
        used_map = row.pop("_slot_used", None) or {}
        tracks: list[dict[str, Any]] = []
        total_used = 0
        for category in R5_MOD_SLOT_CATEGORIES:
            extra = int(row.get(R5_SLOT_ADD_KEYS[category]) or 0)
            maximum = max(0, body + extra)
            used = int(used_map.get(category) or 0)
            total_used += used
            tracks.append(
                {
                    "category": category,
                    "label": R5_SLOT_LABELS[category],
                    "used": used,
                    "max": maximum,
                }
            )
            if used > maximum:
                errors.append(
                    f"{row['name']} の{R5_SLOT_LABELS[category]}スロット超過（{used}/{maximum}）"
                )
        row["slot_tracks"] = tracks
        row["slots_used"] = total_used
        row["slots_max"] = body
    return errors


def _iter_vehicle_hosts(state: CharacterState) -> list[tuple[GearInstall, dict[str, Any]]]:
    drones = {item["id"]: item for item in catalog().get("drones") or []}
    vehicles = {item["id"]: item for item in catalog().get("vehicles") or []}
    out: list[tuple[GearInstall, dict[str, Any]]] = []
    for inst in list(state.drones or []):
        spec = drones.get(inst.gear_id)
        if spec:
            out.append((inst, spec))
    for inst in list(state.vehicles or []):
        spec = vehicles.get(inst.gear_id)
        if spec:
            out.append((inst, spec))
    return out


def _ensure_drone_equipment(state: CharacterState) -> None:
    sensors = {item["id"]: item for item in catalog().get("sensors") or []}
    sensors_by_name = {item["name"]: item for item in sensors.values()}
    gear = {item["id"]: item for item in catalog().get("gear") or []}
    gear_by_name = {item["name"]: item for item in gear.values()}
    mods = {item["id"]: item for item in catalog().get("vehicle_mods") or []}
    mods_by_name = {item["name"]: item for item in mods.values()}
    have_sensors = {(row.parent_id, (sensors.get(row.gear_id) or {}).get("name")) for row in state.sensors or []}
    extra_sensors: list[GearInstall] = []
    have_gear = {(row.parent_id, (gear.get(row.gear_id) or {}).get("name")) for row in state.gear or []}
    extra_gear: list[GearInstall] = []
    for host, spec in _iter_vehicle_hosts(state):
        for gift in spec.get("included_gears") or []:
            name = gift.get("name") or ""
            child = sensors_by_name.get(name)
            if child:
                if (host.id, child["name"]) in have_sensors:
                    continue
                extra_sensors.append(
                    GearInstall(
                        gear_id=child["id"],
                        parent_id=host.id,
                        included=True,
                        rating=int(gift.get("rating") or 1),
                    )
                )
                have_sensors.add((host.id, child["name"]))
                continue
            child = gear_by_name.get(name)
            if not child or (host.id, child["name"]) in have_gear:
                continue
            extra_gear.append(
                GearInstall(
                    gear_id=child["id"],
                    parent_id=host.id,
                    included=True,
                    rating=int(gift.get("rating") or 1),
                )
            )
            have_gear.add((host.id, child["name"]))
    if extra_sensors:
        state.sensors = list(state.sensors or []) + extra_sensors
    if extra_gear:
        state.gear = list(state.gear or []) + extra_gear

    have_mods = {(row.parent_id, (mods.get(row.mod_id) or {}).get("name")) for row in state.vehicle_mods or []}
    extra_mods: list[VehicleModInstall] = []
    for host, spec in _iter_vehicle_hosts(state):
        for name in spec.get("included_mods") or []:
            child = mods_by_name.get(name)
            if not child or (host.id, child["name"]) in have_mods:
                continue
            extra_mods.append(VehicleModInstall(mod_id=child["id"], parent_id=host.id, included=True))
            have_mods.add((host.id, child["name"]))
    if extra_mods:
        state.vehicle_mods = list(state.vehicle_mods or []) + extra_mods

    have_mounts = {
        (row.parent_id, row.size_id, row.visibility_id, row.flexibility_id, row.control_id)
        for row in state.weapon_mounts or []
    }
    extra_mounts: list[WeaponMountInstall] = []
    for host, spec in _iter_vehicle_hosts(state):
        source = str(spec.get("source") or "")
        for gift in spec.get("included_weaponmounts") or []:
            size = _find_mount_part(gift.get("size") or "", "Size", source)
            vis = _find_mount_part(gift.get("visibility") or "", "Visibility", source)
            flex = _find_mount_part(gift.get("flexibility") or "", "Flexibility", source)
            ctrl = _find_mount_part(gift.get("control") or "", "Control", source)
            if not size:
                continue
            key = (host.id, size["id"], vis["id"] if vis else "", flex["id"] if flex else "", ctrl["id"] if ctrl else "")
            if key in have_mounts:
                continue
            extra_mounts.append(
                WeaponMountInstall(
                    parent_id=host.id,
                    size_id=size["id"],
                    visibility_id=vis["id"] if vis else "",
                    flexibility_id=flex["id"] if flex else "",
                    control_id=ctrl["id"] if ctrl else "",
                    included=True,
                    allowedweapons=gift.get("allowedweapons") or "",
                )
            )
            have_mounts.add(key)
    if extra_mounts:
        state.weapon_mounts = list(state.weapon_mounts or []) + extra_mounts


def _resolve_vehicle_mods(
    state: CharacterState,
    drones: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int, list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    specs = {item["id"]: item for item in catalog().get("vehicle_mods") or []}
    by_drone = {str(row.get("id") or ""): row for row in drones}
    kept: list[VehicleModInstall] = []
    public: list[dict[str, Any]] = []
    nuyen = 0
    for inst in list(state.vehicle_mods or []):
        spec = specs.get(inst.mod_id)
        parent = by_drone.get(inst.parent_id or "")
        if not spec or not parent:
            if spec:
                warnings.append(f"{spec['name']} は車両に装着してください")
            continue
        if not inst.included and not mod_fits_vehicle(spec, parent):
            warnings.append(f"{spec['name']} は {parent['name']} に装着できません")
            continue
        extras = _vehicle_extras(parent, parent.get("stats") or {}, int(parent.get("base_nuyen") or parent.get("nuyen") or 0))
        rating = _clamp_vehicle_rating(spec, inst.rating, extras) if int(spec.get("maxrating") or 0) > 0 or spec.get("maxrating_expr") else 1
        inst.rating = rating
        cost = 0 if inst.included else int(eval_formula(str(spec.get("cost") or "0"), rating, 0, extras))
        slots = int(eval_formula(str(spec.get("slots") or "0"), rating, 0, extras))
        nuyen += cost
        if spec.get("bonus"):
            _apply_vehicle_bonus(parent.setdefault("stats", {}), list(spec.get("bonus") or []), rating)
        parent["nuyen"] = int(parent.get("nuyen") or 0) + cost
        _add_vehicle_slot_use(parent, slots, str(spec.get("category") or ""), bool(inst.included))
        kept.append(inst)
        public.append(
            {
                "id": inst.id,
                "mod_id": spec["id"],
                "name": spec["name"],
                "category": spec.get("category") or "",
                "parent_id": inst.parent_id,
                "included": bool(inst.included),
                "rating": rating,
                "rating_max": int(spec.get("maxrating") or 0),
                "slots": slots,
                "nuyen": cost,
                "avail": spec.get("avail") or "",
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
                "capacity_max": _capacity_value(spec.get("capacity"), rating),
                "capacity_used": 0.0,
                "subsystems": list(spec.get("subsystems") or []),
                "cyberware": [],
            }
        )
    children: dict[str, list[dict[str, Any]]] = {}
    for item in public:
        children.setdefault(str(item.get("parent_id") or ""), []).append(item)
    for row in drones:
        row["mods"] = children.get(str(row.get("id") or "")) or []
    state.vehicle_mods = kept
    return public, nuyen, warnings, errors


def _resolve_weapon_mounts(
    state: CharacterState,
    drones: list[dict[str, Any]],
    weapons: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int, list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []
    parts = {item["id"]: item for item in catalog().get("weapon_mounts") or []}
    by_drone = {str(row.get("id") or ""): row for row in drones}
    weapons_by_id = {str(row.get("id") or ""): row for row in weapons}
    kept: list[WeaponMountInstall] = []
    public: list[dict[str, Any]] = []
    nuyen = 0
    used_weapons: set[str] = set()
    for inst in list(state.weapon_mounts or []):
        parent = by_drone.get(inst.parent_id or "")
        size = parts.get(inst.size_id)
        if not parent or not size or size.get("category") != "Size":
            if size:
                warnings.append(f"{size['name']} は車両に装着してください")
            continue
        if not inst.included and not vehicle_matches(parent, size.get("required")):
            warnings.append(f"{size['name']} は {parent['name']} に装着できません")
            continue
        defaults = _default_mount_parts(size)
        vis = parts.get(inst.visibility_id) or defaults.get("visibility")
        flex = parts.get(inst.flexibility_id) or defaults.get("flexibility")
        ctrl = parts.get(inst.control_id) or defaults.get("control")
        inst.visibility_id = str((vis or {}).get("id") or "")
        inst.flexibility_id = str((flex or {}).get("id") or "")
        inst.control_id = str((ctrl or {}).get("id") or "")
        bundle = [part for part in (size, vis, flex, ctrl) if part]
        extras = _vehicle_extras(parent, parent.get("stats") or {}, int(parent.get("base_nuyen") or 0))
        cost = 0 if inst.included else sum(int(eval_formula(str(part.get("cost") or "0"), 1, 0, extras)) for part in bundle)
        slots = sum(int(eval_formula(str(part.get("slots") or "0"), 1, 0, extras)) for part in bundle)
        nuyen += cost
        parent["nuyen"] = int(parent.get("nuyen") or 0) + cost
        _add_vehicle_slot_use(parent, slots, "Weapons", bool(inst.included))
        weapon = weapons_by_id.get(inst.weapon_install_id or "")
        if inst.weapon_install_id and not weapon:
            warnings.append(f"{parent['name']} の武器マウントに武器がありません")
            inst.weapon_install_id = None
        elif weapon and weapon["id"] in used_weapons:
            warnings.append(f"{weapon['name']} は既に搭載されています")
            weapon = None
            inst.weapon_install_id = None
        elif weapon:
            allowed = (inst.allowedweapons or "").strip()
            if allowed and weapon["name"] not in {part.strip() for part in allowed.split(",") if part.strip()}:
                warnings.append(f"{weapon['name']} は {parent['name']} のマウントに搭載できません")
                weapon = None
                inst.weapon_install_id = None
            else:
                used_weapons.add(weapon["id"])
                weapon["mounted_on"] = parent["id"]
                weapon["mounted_label"] = parent["name"]
        kept.append(inst)
        public.append(
            {
                "id": inst.id,
                "parent_id": inst.parent_id,
                "size_id": inst.size_id,
                "visibility_id": inst.visibility_id,
                "flexibility_id": inst.flexibility_id,
                "control_id": inst.control_id,
                "included": bool(inst.included),
                "name": size["name"],
                "label": " / ".join(part["name"] for part in bundle),
                "slots": slots,
                "nuyen": cost,
                "weapon_install_id": inst.weapon_install_id,
                "weapon_name": weapon["name"] if weapon else "",
                "allowedweapons": inst.allowedweapons or "",
                "source": size.get("source") or "",
                "page": size.get("page") or "",
            }
        )
    children: dict[str, list[dict[str, Any]]] = {}
    for item in public:
        children.setdefault(str(item.get("parent_id") or ""), []).append(item)
    for row in drones:
        row["weapon_mounts"] = children.get(str(row.get("id") or "")) or []
    errors.extend(_finalize_vehicle_slots(drones))
    state.weapon_mounts = kept
    return public, nuyen, warnings, errors


def _resolve_drones(state: CharacterState, kind: str = "drones") -> tuple[list[dict[str, Any]], int]:
    kept: list[GearInstall] = []
    public: list[dict[str, Any]] = []
    nuyen = 0
    for inst in list(getattr(state, kind) or []):
        spec = _item_by_id(kind, inst.gear_id)
        if not spec:
            continue
        cost = int(eval_formula(str(spec.get("cost") or "0"), 1, 0))
        nuyen += cost
        stats = {
            "handling": _leading_vehicle_stat(spec.get("handling")),
            "speed": _leading_vehicle_stat(spec.get("speed")),
            "accel": _leading_vehicle_stat(spec.get("accel")),
            "body": _leading_vehicle_stat(spec.get("body")),
            "armor": _leading_vehicle_stat(spec.get("armor")),
            "pilot": _leading_vehicle_stat(spec.get("pilot")),
            "sensor": _leading_vehicle_stat(spec.get("sensor")),
            "seats": _leading_vehicle_stat(spec.get("seats")),
        }
        kept.append(inst)
        public.append(
            {
                "id": inst.id,
                "gear_id": spec["id"],
                "name": spec["name"],
                "category": spec.get("category") or "",
                "handling": spec.get("handling") or "",
                "speed": spec.get("speed") or "",
                "accel": spec.get("accel") or "",
                "body": spec.get("body") or "",
                "armor": spec.get("armor") or "",
                "pilot": spec.get("pilot") or "",
                "sensor": spec.get("sensor") or "",
                "seats": spec.get("seats") or "",
                "stats": stats,
                "base_nuyen": cost,
                "nuyen": cost,
                "slots_used": 0,
                "slots_max": stats["body"],
                "slot_tracks": [],
                "modslots": spec.get("modslots"),
                "powertrainmodslots": int(spec.get("powertrainmodslots") or 0),
                "protectionmodslots": int(spec.get("protectionmodslots") or 0),
                "weaponmodslots": int(spec.get("weaponmodslots") or 0),
                "bodymodslots": int(spec.get("bodymodslots") or 0),
                "electromagneticmodslots": int(spec.get("electromagneticmodslots") or 0),
                "cosmeticmodslots": int(spec.get("cosmeticmodslots") or 0),
                "mods": [],
                "weapon_mounts": [],
                "sensors": [],
                "gear": [],
                "avail": spec.get("avail") or "",
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
    setattr(state, kind, kept)
    return public, nuyen


def _publish_drone_stats(drones: list[dict[str, Any]], sensors: list[dict[str, Any]]) -> None:
    children: dict[str, list[dict[str, Any]]] = {}
    for item in sensors:
        if item.get("parent_id"):
            children.setdefault(str(item.get("parent_id") or ""), []).append(item)
    for row in drones:
        stats = row.get("stats") or {}
        row["handling"] = _format_vehicle_stat(str(row.get("handling") or ""), int(stats.get("handling") or 0))
        row["speed"] = str(stats.get("speed") or row.get("speed") or "")
        row["accel"] = str(stats.get("accel") or row.get("accel") or "")
        row["body"] = str(stats.get("body") or row.get("body") or "")
        row["armor"] = str(stats.get("armor") or row.get("armor") or "")
        row["pilot"] = str(stats.get("pilot") or row.get("pilot") or "")
        row["sensor"] = str(stats.get("sensor") or row.get("sensor") or "")
        row["seats"] = str(stats.get("seats") or row.get("seats") or "")
        row["sensors"] = children.get(str(row.get("id") or "")) or []
        row.pop("stats", None)
        row.pop("base_nuyen", None)
        row.pop("modslots", None)
        row.pop("powertrainmodslots", None)
        row.pop("protectionmodslots", None)
        row.pop("weaponmodslots", None)
        row.pop("bodymodslots", None)
        row.pop("electromagneticmodslots", None)
        row.pop("cosmeticmodslots", None)


def _finalize_avail_tree(
    items: list[dict[str, Any]],
    *,
    grade_kind: str | None = None,
    rating_key: str = "rating",
) -> None:
    for item in items:
        rating = int(item.get(rating_key) or item.get("rating") or item.get("force") or 1)
        extras: dict[str, int | float] = {}
        if item.get("rating_min") is not None:
            extras["MinRating"] = int(item.get("rating_min") or 1)
        value, suffix, additive = parse_avail(str(item.get("avail") or ""), rating, extras or None)
        if grade_kind and not additive:
            grade = _grade_by_name(grade_kind, str(item.get("grade") or "Standard"))
            gval, gsuf, _gadd = parse_avail(str(grade.get("avail") or ""), 1)
            value, suffix = sum_avail([(value, suffix), (gval, gsuf)])
        value = max(0, value)
        item["avail_value"] = value
        item["avail_suffix"] = suffix
        item["avail_additive"] = additive
        item["avail_folded"] = False
        item["avail"] = format_avail(value, suffix)
    children: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        parent_id = str(item.get("parent_id") or "")
        if parent_id:
            children.setdefault(parent_id, []).append(item)
    for item in items:
        adds: list[tuple[int, str]] = []
        for kid in children.get(str(item.get("id") or ""), []):
            if not kid.get("avail_additive"):
                continue
            adds.append((int(kid.get("avail_value") or 0), str(kid.get("avail_suffix") or "")))
            kid["avail_folded"] = True
        if not adds:
            continue
        value, suffix = sum_avail(
            [(int(item.get("avail_value") or 0), str(item.get("avail_suffix") or ""))] + adds
        )
        item["avail_value"] = value
        item["avail_suffix"] = suffix
        item["avail"] = format_avail(value, suffix)


def _avail_entries(*groups: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for group in groups:
        for item in group or []:
            item_id = str(item.get("id") or "")
            if item_id and item_id in seen:
                continue
            if item_id:
                seen.add(item_id)
            if item.get("avail_folded") or item.get("from_ware") or item.get("from_gear"):
                continue
            if int(item.get("avail_value") or 0) <= 0:
                continue
            out.append(item)
    return out


def _restricted_gear_slots(effects: dict[str, Any]) -> list[int]:
    slots: list[int] = []
    for row in effects.get("restricted_gear") or []:
        cap = max(0, int(row.get("availability") or 0))
        amount = max(1, int(row.get("amount") or 1))
        slots.extend([cap] * amount)
    slots.sort(reverse=True)
    return slots


def _check_avail_limit(items: list[dict[str, Any]], effects: dict[str, Any], errors: list[str]) -> None:
    limit = CHARGEN_AVAIL_MAX
    slots = _restricted_gear_slots(effects)
    over = sorted(items, key=lambda row: int(row.get("avail_value") or 0), reverse=True)
    for item in over:
        value = int(item.get("avail_value") or 0)
        shown = str(item.get("avail") or format_avail(value, str(item.get("avail_suffix") or "")))
        name = str(item.get("label") or item.get("name") or "ギア")
        if value <= limit:
            continue
        used = False
        for idx, cap in enumerate(slots):
            if value <= cap:
                slots.pop(idx)
                used = True
                item["restricted_gear"] = True
                break
        if used:
            continue
        errors.append(f"{name} の入手制限超過（{shown} / 上限{limit}）")


def _device_rating_entries(*groups: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for group in groups:
        for item in group or []:
            item_id = str(item.get("id") or "")
            if item_id and item_id in seen:
                continue
            if item_id:
                seen.add(item_id)
            if item.get("from_ware") or item.get("from_gear"):
                continue
            if int(item.get("device_rating") or 0) <= 0:
                continue
            out.append(item)
    return out


def _check_device_rating_limit(items: list[dict[str, Any]], errors: list[str]) -> None:
    limit = CHARGEN_DEVICE_RATING_MAX
    for item in items:
        value = int(item.get("device_rating") or 0)
        if value <= limit:
            continue
        name = str(item.get("label") or item.get("name") or "ギア")
        errors.append(f"{name} のデバイスレーティング超過（{value} / 上限{limit}）")


def _ware_attribute_bonuses(items: list[dict[str, Any]]) -> dict[str, int]:
    totals: dict[str, int] = {key: 0 for key in PHYSICAL_ATTRS}
    for item in items:
        for node in item.get("bonus") or []:
            if node.get("tag") != "specificattribute":
                continue
            fields = node.get("fields") or {}
            name = ATTR_ALIASES.get(str(fields.get("name") or "").upper())
            if name not in totals:
                continue
            totals[name] += _as_int(fields.get("bonus") or fields.get("val") or fields.get("value"), 0)
    return {key: value for key, value in totals.items() if value}


def _check_ware_attribute_cap(bonuses: dict[str, int], errors: list[str]) -> None:
    limit = CHARGEN_WARE_ATTR_BONUS_MAX
    for attr in PHYSICAL_ATTRS:
        value = int(bonuses.get(attr) or 0)
        if value <= limit:
            continue
        errors.append(f"{attr} のウェア強化超過（+{value} / 上限+{limit}）")


def resolve_gear(
    state: CharacterState,
    ware_items: list[dict[str, Any]] | None = None,
    attr_totals: dict[str, int] | None = None,
) -> dict[str, Any]:
    warnings: list[str] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    nuyen = 0
    armor_items: list[dict[str, Any]] = []
    weapons: list[dict[str, Any]] = []
    commlinks: list[dict[str, Any]] = []
    cyberdecks: list[dict[str, Any]] = []
    rccs: list[dict[str, Any]] = []
    lifestyles: list[dict[str, Any]] = []
    errors: list[str] = []

    kept_armor: list[ArmorInstall] = []
    for inst in state.armor:
        spec = _item_by_id("armor", inst.armor_id)
        if not spec:
            continue
        rating = _clamp_rating(spec, inst.rating)
        inst.rating = rating
        inst.equipped = bool(inst.equipped)
        cost = int(eval_formula(str(spec.get("cost") or "0"), rating, 0))
        nuyen += cost
        value, additive = parse_armor_value(str(spec.get("armor") or "0"), rating)
        if inst.equipped:
            nodes = substitute_rating(list(spec.get("bonus") or []), rating)
            if nodes:
                bonus_sources.append((spec["name"], nodes))
        kept_armor.append(inst)
        armor_items.append(
            {
                "id": inst.id,
                "armor_id": spec["id"],
                "name": spec["name"],
                "category": spec.get("category") or "Armor",
                "armor": spec.get("armor") or "0",
                "armor_value": value,
                "additive": additive,
                "rating": rating,
                "rating_max": int(spec.get("maxrating") or 0),
                "equipped": inst.equipped,
                "nuyen": cost,
                "avail": spec.get("avail") or "",
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
                "contributes": 0,
                "armorcapacity": spec.get("armorcapacity") or "",
                "addmodcategories": list(spec.get("addmodcategories") or []),
                "mods": [],
                "capacity_used": 0,
                "capacity_max": 0,
            }
        )
    state.armor = kept_armor
    armor_mods, mod_nuyen, mod_warns, mod_errors, mod_bonus = _resolve_armor_mods(state, armor_items)
    nuyen += mod_nuyen
    warnings.extend(mod_warns)
    errors.extend(mod_errors)
    bonus_sources.extend(mod_bonus)
    worn_armor, worn_name, worn_warns = _recompute_worn_armor(armor_items)
    warnings.extend(worn_warns)

    kept_weapons: list[WeaponInstall] = []
    for inst in state.weapons:
        spec = _item_by_id("weapons", inst.weapon_id)
        if not spec:
            continue
        qty = max(1, int(inst.qty or 1))
        inst.qty = qty
        unit = int(eval_formula(str(spec.get("cost") or "0"), 1, 0))
        cost = unit * qty
        nuyen += cost
        kept_weapons.append(inst)
        weapons.append(
            _public_weapon(
                spec,
                inst_id=inst.id,
                qty=qty,
                nuyen=cost,
                loaded_ammo_id=inst.loaded_ammo_id,
            )
        )
    state.weapons = kept_weapons
    _append_ware_weapons(weapons, ware_items or [], state, attr_totals)
    weapon_accessories, acc_nuyen, acc_warns, acc_errors = _resolve_weapon_accessories(state, weapons)
    nuyen += acc_nuyen
    warnings.extend(acc_warns)
    errors.extend(acc_errors)

    kept_links: list[CommlinkInstall] = []
    for inst in state.commlinks:
        spec = _item_by_id("commlinks", inst.gear_id)
        if not spec:
            continue
        rating = _clamp_rating(spec, inst.rating)
        inst.rating = rating
        cost = int(eval_formula(str(spec.get("cost") or "0"), rating, 0))
        nuyen += cost
        device = int(eval_formula(str(spec.get("devicerating") or "0"), rating, 0))
        processing = int(eval_formula(str(spec.get("dataprocessing") or "0"), rating, 0))
        firewall = int(eval_formula(str(spec.get("firewall") or "0"), rating, 0))
        kept_links.append(inst)
        commlinks.append(
            {
                "id": inst.id,
                "gear_id": spec["id"],
                "name": spec["name"],
                "category": spec.get("category") or "Commlinks",
                "rating": rating,
                "rating_max": int(spec.get("maxrating") or 0),
                "device_rating": device,
                "dataprocessing": processing,
                "firewall": firewall,
                "nuyen": cost,
                "avail": spec.get("avail") or "",
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
    state.commlinks = kept_links

    kept_decks, cyberdecks, deck_nuyen = _resolve_matrix_devices("cyberdecks", list(state.cyberdecks or []))
    state.cyberdecks = kept_decks
    nuyen += deck_nuyen
    kept_rccs, rccs, rcc_nuyen = _resolve_matrix_devices("rccs", list(state.rccs or []))
    state.rccs = kept_rccs
    nuyen += rcc_nuyen
    optics, optic_nuyen, optic_warns, optic_errors, optic_bonus = _resolve_optics(state)
    nuyen += optic_nuyen
    warnings.extend(optic_warns)
    errors.extend(optic_errors)
    bonus_sources.extend(optic_bonus)
    programs, prog_nuyen, prog_warns = _resolve_programs(state, cyberdecks, rccs)
    nuyen += prog_nuyen
    warnings.extend(prog_warns)
    apps, app_nuyen, app_warns = _resolve_apps(state, commlinks)
    nuyen += app_nuyen
    warnings.extend(app_warns)
    drones, drone_nuyen = _resolve_drones(state, "drones")
    nuyen += drone_nuyen
    vehicles, vehicle_nuyen = _resolve_drones(state, "vehicles")
    nuyen += vehicle_nuyen
    hosts = drones + vehicles
    _ensure_drone_equipment(state)
    vehicle_mods, mod_nuyen, mod_warns, mod_errors = _resolve_vehicle_mods(state, hosts)
    nuyen += mod_nuyen
    warnings.extend(mod_warns)
    errors.extend(mod_errors)
    weapon_mounts, mount_nuyen, mount_warns, mount_errors = _resolve_weapon_mounts(state, hosts, weapons)
    nuyen += mount_nuyen
    warnings.extend(mount_warns)
    errors.extend(mount_errors)
    sensors, sensor_nuyen, sensor_warns, sensor_errors, sensor_bonus = _resolve_sensors(state)
    nuyen += sensor_nuyen
    warnings.extend(sensor_warns)
    errors.extend(sensor_errors)
    bonus_sources.extend(sensor_bonus)
    _publish_drone_stats(hosts, sensors)
    gear_items, gear_nuyen, gear_warns, gear_errors, gear_bonus = _resolve_misc_gear(state, hosts, weapons)
    nuyen += gear_nuyen
    warnings.extend(gear_warns)
    errors.extend(gear_errors)
    bonus_sources.extend(gear_bonus)
    _append_gear_weapons(weapons, gear_items)

    kept_lifestyles: list[LifestyleInstall] = []
    quality_specs = {item["id"]: item for item in catalog().get("lifestyle_qualities") or []}
    quality_by_name = {item["name"]: item for item in quality_specs.values()}
    for inst in state.lifestyles:
        spec = _item_by_id("lifestyles", inst.lifestyle_id)
        if not spec:
            continue
        months = max(1, int(inst.months or 1))
        inst.months = months
        lifestyle_name = str(spec.get("name") or "")
        base_monthly = int(spec.get("cost") or 0)
        lp_max = int(spec.get("lp") or 0)
        quality_ids = list(inst.quality_ids or [])
        extras = dict(inst.quality_extras or {})

        def _append_lifestyle_quality(
            qid: str,
            *,
            extra: str = "",
            from_freegrid: bool = False,
        ) -> None:
            nonlocal lp_used, quality_monthly, multiplier_pct
            qspec = quality_specs.get(qid)
            if not qspec:
                return
            if qid in seen_quality and not qspec.get("allow_multiple"):
                return
            seen_quality.add(qid)
            allowed = [str(name) for name in (qspec.get("allowed") or [])]
            free = bool(from_freegrid) or (bool(allowed) and lifestyle_name in allowed)
            if allowed and lifestyle_name not in allowed and not from_freegrid:
                warnings.append(f"{qspec['name']} は {lifestyle_name} では取得できません")
                return
            lp_cost = int(qspec.get("lp") or 0)
            lp_used += lp_cost
            add_cost = 0 if free else int(qspec.get("cost") or 0)
            quality_monthly += add_cost
            multiplier_pct += int(qspec.get("multiplier") or 0)
            extra_val = str(extra or extras.get(qid) or "").strip()
            if qspec.get("needs_extra") and not extra_val:
                warnings.append(f"{qspec['name']} の対象を入力してください")
            nodes = list(qspec.get("bonus") or [])
            bonus_nodes = [node for node in nodes if node.get("tag") != "selecttext"]
            if bonus_nodes:
                bonus_sources.append((f"{lifestyle_name}:{qspec['name']}", bonus_nodes))
            kept_qualities.append(
                {
                    "id": f"{qid}:{len(kept_qualities)}",
                    "quality_id": qid,
                    "name": qspec["name"],
                    "category": qspec.get("category") or "",
                    "lp": lp_cost,
                    "cost": add_cost,
                    "free": free,
                    "from_freegrid": from_freegrid,
                    "multiplier": int(qspec.get("multiplier") or 0),
                    "extra": extra_val,
                    "needs_extra": bool(qspec.get("needs_extra")),
                    "source": qspec.get("source") or "",
                    "page": qspec.get("page") or "",
                }
            )

        kept_qualities: list[dict[str, Any]] = []
        seen_quality: set[str] = set()
        lp_used = 0
        quality_monthly = 0
        multiplier_pct = 0

        # Freegrids are always derived from the lifestyle (may repeat with different selects).
        for grid in spec.get("freegrids") or []:
            grid_name = str(grid.get("name") or "Grid Subscription")
            grid_spec = quality_by_name.get(grid_name)
            if not grid_spec:
                continue
            # allow_multiple freegrids share one quality id; clear seen for each instance.
            if grid_spec.get("allow_multiple"):
                seen_quality.discard(grid_spec["id"])
            _append_lifestyle_quality(
                grid_spec["id"],
                extra=str(grid.get("select") or "").strip(),
                from_freegrid=True,
            )

        for qid in quality_ids:
            _append_lifestyle_quality(qid)

        if lp_max > 0 and lp_used > lp_max:
            warnings.append(
                f"{lifestyle_name} のライフスタイルポイント超過（使用 {lp_used} / 上限 {lp_max}）"
            )

        monthly = int(round(base_monthly * (100 + multiplier_pct) / 100.0)) + quality_monthly
        cost = monthly * months
        nuyen += cost
        # Persist user picks only; freegrids are re-derived each compute.
        inst.quality_ids = [
            row["quality_id"] for row in kept_qualities if not row.get("from_freegrid")
        ]
        inst.quality_extras = {
            row["quality_id"]: row["extra"]
            for row in kept_qualities
            if row.get("extra") and not row.get("from_freegrid")
        }
        kept_lifestyles.append(inst)
        lifestyles.append(
            {
                "id": inst.id,
                "lifestyle_id": spec["id"],
                "name": lifestyle_name,
                "months": months,
                "increment": spec.get("increment") or "month",
                "monthly": monthly,
                "base_monthly": base_monthly,
                "quality_monthly": quality_monthly,
                "multiplier_pct": multiplier_pct,
                "nuyen": cost,
                "lp_used": lp_used,
                "lp_max": lp_max,
                "dice": int(spec.get("dice") or 0),
                "qualities": kept_qualities,
                "avail": spec.get("avail") or "",
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
    state.lifestyles = kept_lifestyles

    primary_link = max(commlinks, key=lambda row: int(row.get("device_rating") or 0)) if commlinks else None
    primary_deck = max(cyberdecks, key=lambda row: int(row.get("device_rating") or 0)) if cyberdecks else None
    primary_rcc = max(rccs, key=lambda row: int(row.get("device_rating") or 0)) if rccs else None
    primary_life = lifestyles[0] if lifestyles else None
    _finalize_avail_tree(armor_items + armor_mods)
    _finalize_avail_tree(weapons + weapon_accessories)
    _finalize_avail_tree(commlinks + apps)
    _finalize_avail_tree(cyberdecks + rccs + programs)
    _finalize_avail_tree(optics)
    _finalize_avail_tree(sensors)
    _finalize_avail_tree(drones + vehicles + vehicle_mods + weapon_mounts)
    _finalize_avail_tree(gear_items)
    _finalize_avail_tree(lifestyles)
    return {
        "warnings": warnings,
        "errors": errors,
        "bonus_sources": bonus_sources,
        "nuyen": nuyen,
        "armor": worn_armor,
        "worn_name": worn_name,
        "armor_items": armor_items,
        "armor_mods": armor_mods,
        "weapons": weapons,
        "weapon_accessories": weapon_accessories,
        "commlinks": commlinks,
        "cyberdecks": cyberdecks,
        "rccs": rccs,
        "optics": optics,
        "programs": programs,
        "apps": apps,
        "sensors": sensors,
        "drones": drones,
        "vehicles": vehicles,
        "vehicle_mods": vehicle_mods,
        "weapon_mounts": weapon_mounts,
        "gear": gear_items,
        "lifestyles": lifestyles,
        "commlink": primary_link,
        "cyberdeck": primary_deck,
        "rcc": primary_rcc,
        "lifestyle": primary_life,
    }


def _tradition_public(tradition: dict[str, Any] | None) -> dict[str, Any] | None:
    if not tradition:
        return None
    return {
        "id": tradition["id"],
        "name": tradition["name"],
        "drain": tradition.get("drain") or "",
        "drain_attrs": list(tradition.get("drain_attrs") or []),
        "spirits": dict(tradition.get("spirits") or {}),
        "source": tradition.get("source"),
        "page": tradition.get("page"),
    }


def spirit_attributes(spec: dict[str, Any], force: int) -> dict[str, int]:
    extras = {"F": int(force)}
    out: dict[str, int] = {}
    for key, expr in (spec.get("attributes") or {}).items():
        value = int(eval_formula(str(expr or "F"), force, force, extras))
        out[key] = value if key == "INI" else max(1, value)
    return out


def sprite_attributes(spec: dict[str, Any], level: int) -> dict[str, Any]:
    extras = {"F": int(level)}
    raw: dict[str, int] = {}
    for key, expr in (spec.get("attributes") or {}).items():
        value = int(eval_formula(str(expr or "F"), level, level, extras))
        if key == "INI":
            raw[key] = value
        elif key in {"BOD", "AGI", "REA", "STR"}:
            raw[key] = value
        else:
            raw[key] = max(1, value)
    matrix = {
        "attack": int(raw.get("CHA") or 0),
        "sleaze": int(raw.get("INT") or 0),
        "dataprocessing": int(raw.get("LOG") or 0),
        "firewall": int(raw.get("WIL") or 0),
        "initiative": int(raw.get("INI") or 0),
    }
    return {"attributes": raw, "matrix": matrix}


def focus_bind_karma(name: str, force: int, focus_binding: list[dict[str, Any]]) -> int:
    bind = int(force)
    for mod in focus_binding:
        if (mod.get("name") or "") != name:
            continue
        bind += int(mod.get("val") or 0)
    return max(0, bind)


def tradition_resist(tradition: dict[str, Any] | None, attrs: dict[str, int]) -> tuple[int, str]:
    extras = {
        key: int(attrs.get(key) or 1)
        for key in ("WIL", "LOG", "INT", "CHA", "BOD", "AGI", "REA", "STR", "RES", "MAG")
    }
    formula = (tradition or {}).get("drain") or "{WIL} + {INT}"
    keys = [key.upper() for key in re.findall(r"\{([A-Za-z]+)\}", str(formula))]
    if not keys:
        keys = ["WIL", "INT"]
    value = int(eval_formula(formula, 1, sum(extras.get(k, 1) for k in keys), extras))
    return value, "+".join(keys)


def is_way_quality(name: str) -> bool:
    return bool(re.fullmatch(r"The .+ Way", (name or "").strip()))


def sanitize_quality_ids(quality_ids: list[str]) -> tuple[list[str], list[str]]:
    kept: list[str] = []
    removed: list[str] = []
    for qid in quality_ids:
        spec = _quality_by_id(qid)
        if not spec:
            continue
        incoming_forbid = set((spec.get("forbidden") or {}).get("quality") or [])
        next_kept: list[str] = []
        for existing_id in kept:
            existing = _quality_by_id(existing_id)
            if not existing:
                continue
            existing_forbid = set((existing.get("forbidden") or {}).get("quality") or [])
            if spec["name"] in existing_forbid or existing["name"] in incoming_forbid:
                removed.append(existing["name"])
                continue
            next_kept.append(existing_id)
        next_kept.append(qid)
        kept = next_kept
    return kept, removed


def quality_needs_extra(spec: dict[str, Any]) -> bool:
    return bool(spec.get("needs_extra")) or any(
        node.get("tag") in {"selecttext", "selectattributes"} for node in (spec.get("bonus") or [])
    )


def _requirement_item_met(node: dict[str, Any], ctx: dict[str, Any]) -> bool:
    tag = node.get("tag") or ""
    children = list(node.get("children") or [])
    if tag == "oneof":
        return any(_requirement_item_met(child, ctx) for child in children) if children else True
    if tag in {"allof", "group"}:
        return all(_requirement_item_met(child, ctx) for child in children) if children else True
    name = str(node.get("name") or "")
    if tag == "quality":
        return name in ctx["qualities"]
    if tag == "metatype":
        return name in ctx["metatypes"]
    if tag == "metatypecategory":
        return name in ctx["metatype_categories"]
    if tag == "magenabled":
        return bool(ctx["magenabled"])
    if tag == "resenabled":
        return bool(ctx["resenabled"])
    if tag == "power":
        return name in ctx["powers"]
    if tag == "art":
        return name in (ctx.get("arts") or set())
    if tag == "metamagic":
        return name in (ctx.get("metamagics") or set())
    if tag == "cyberware":
        return name in ctx["cyberware"]
    if tag == "bioware":
        return name in ctx["bioware"]
    if tag == "spell":
        return name in ctx["spells"]
    if tag == "tradition":
        return name == ctx["tradition"]
    if tag == "skill":
        rating = int(node.get("val") or 1)
        pool = ctx["knowledge"] if str(node.get("type") or "").lower() == "knowledge" else ctx["skills"]
        return _pool_rating(pool, name) >= rating
    if tag == "ess":
        value = float(node.get("value") or 0)
        if value < 0:
            return float(ctx["ess_lost"]) + 1e-9 >= abs(value)
        return float(ctx["essence"]) + 1e-9 >= value
    if tag == "gameplayoption":
        return False
    return False


def _pool_rating(pool: dict[str, int], name: str) -> int:
    best = int(pool.get(name) or 0)
    prefix = f"{name} ("
    for key, value in pool.items():
        if str(key).startswith(prefix):
            best = max(best, int(value or 0))
    return best


def requirement_tree_met(tree: list[dict[str, Any]] | None, ctx: dict[str, Any]) -> bool:
    nodes = list(tree or [])
    if not nodes:
        return True
    return all(_requirement_item_met(node, ctx) for node in nodes)


def quality_requirement_context(
    state: CharacterState,
    talent: dict[str, Any],
    qualities: list[dict[str, Any]],
    meta: dict[str, Any],
    ess: float,
    ess_lost: float,
    skill_totals: dict[str, int],
    power_names: set[str],
    spell_names: set[str],
    tradition_name: str,
    cyber_names: set[str],
    bio_names: set[str],
    knowledge_ratings: dict[str, int] | None = None,
) -> dict[str, Any]:
    special_key, _ = talent_special(talent)
    metatypes = {state.metatype}
    if state.metavariant:
        metatypes.add(state.metavariant)
    parent = meta.get("parent")
    if parent:
        metatypes.add(str(parent))
    categories = {str(meta.get("category") or "")}
    return {
        "qualities": {item["name"] for item in qualities},
        "metatypes": metatypes,
        "metatype_categories": {name for name in categories if name},
        "magenabled": special_key == "MAG",
        "resenabled": special_key == "RES",
        "powers": power_names,
        "cyberware": cyber_names,
        "bioware": bio_names,
        "spells": spell_names,
        "tradition": tradition_name,
        "skills": skill_totals,
        "knowledge": dict(knowledge_ratings if knowledge_ratings is not None else state.knowledge_skills or {}),
        "essence": ess,
        "ess_lost": ess_lost,
    }


def apply_quality_rules(
    state: CharacterState,
    qualities: list[dict[str, Any]],
    free_quality_ids: list[str],
    ctx: dict[str, Any],
    errors: list[str],
    *,
    career: bool = False,
) -> int:
    owned = {item["id"] for item in qualities}
    extras = {
        key: str(value).strip()
        for key, value in (state.quality_extras or {}).items()
        if key in owned and str(value).strip()
    }
    state.quality_extras = extras
    free_ids = set(free_quality_ids)
    negative_gain = 0
    for spec in qualities:
        if spec.get("onlyprioritygiven") or spec["id"] in free_ids:
            continue
        if spec["karma"] < 0:
            negative_gain += -int(spec["karma"])
        if spec.get("required_tree") and not requirement_tree_met(spec.get("required_tree"), ctx):
            errors.append(f"{spec['name']} の前提を満たしていません")
        forbidden = spec.get("forbidden_tree") or []
        if forbidden and requirement_tree_met(forbidden, ctx):
            errors.append(f"{spec['name']} は現在のキャラクターでは取れません")
        if quality_needs_extra(spec) and spec["id"] not in extras:
            errors.append(f"{spec['name']} の対象を入力してください")
    if negative_gain > NEGATIVE_QUALITY_KARMA_CAP and not career:
        errors.append(
            f"不利クオリティから得られるカルマが上限を超えています（{negative_gain} / {NEGATIVE_QUALITY_KARMA_CAP}）"
        )
    return negative_gain


def spell_drain_value(formula: str, force: int) -> int | None:
    raw = (formula or "").strip()
    if not raw or raw.lower() == "special":
        return None
    if re.fullmatch(r"\d+", raw):
        return int(raw)
    match = re.fullmatch(r"[FL]\s*([+-]\s*\d+)?", raw, re.I)
    if not match:
        return None
    mod = int(re.sub(r"\s+", "", match.group(1))) if match.group(1) else 0
    return max(DRAIN_MINIMUM, int(force) + mod)


def spell_cast_info(
    spell_name: str,
    force: int | None,
    mag: int,
    resist: int,
    resist_attrs: str,
) -> dict[str, Any] | None:
    spec = _spell_by_name(spell_name)
    if not spec:
        return None
    mag = max(0, int(mag))
    force_max = max(1, mag * 2) if mag else 1
    chosen = int(force) if force else (mag or 1)
    chosen = max(1, min(force_max, chosen))
    value = spell_drain_value(str(spec.get("dv") or ""), chosen)
    physical = bool(mag) and chosen > mag
    return {
        "spell_id": spec["id"],
        "name": spec["name"],
        "category": spec.get("category"),
        "type": spec.get("type"),
        "range": spec.get("range"),
        "duration": spec.get("duration"),
        "descriptor": spec.get("descriptor"),
        "dv": spec.get("dv") or "",
        "force": chosen,
        "force_min": 1,
        "force_max": force_max,
        "drain": value,
        "drain_code": None if value is None else ("P" if physical else "S"),
        "physical": physical,
        "resist": int(resist),
        "resist_attrs": resist_attrs,
    }


def _skill_spec(name: str, skills_data: dict[str, Any] | None = None) -> dict[str, Any] | None:
    data = skills_data if skills_data is not None else catalog().get("skills") or {}
    for item in data.get("skills") or []:
        if item["name"] == name:
            return item
    return None


def skill_dice_pool(
    skill_name: str,
    skill_totals: dict[str, int],
    skill_bonus: dict[str, int],
    attrs: dict[str, int],
    skills_data: dict[str, Any] | None = None,
    attr_override: str | None = None,
) -> dict[str, Any]:
    spec = _skill_spec(skill_name, skills_data)
    attr_name = attr_override or (spec or {}).get("attribute") or "MAG"
    rating = int(skill_totals.get(skill_name) or 0)
    bonus = int(skill_bonus.get(skill_name) or 0)
    attr_value = int(attrs.get(attr_name) or 0)
    can_default = bool((spec or {}).get("default"))
    if rating <= 0:
        if can_default:
            pool = max(0, attr_value - 1) + bonus
            return {
                "skill": skill_name,
                "rating": 0,
                "attr": attr_name,
                "attr_value": attr_value,
                "bonus": bonus,
                "pool": pool,
                "defaulted": True,
                "missing": False,
            }
        return {
            "skill": skill_name,
            "rating": 0,
            "attr": attr_name,
            "attr_value": attr_value,
            "bonus": bonus,
            "pool": 0,
            "defaulted": False,
            "missing": True,
        }
    return {
        "skill": skill_name,
        "rating": rating,
        "attr": attr_name,
        "attr_value": attr_value,
        "bonus": bonus,
        "pool": rating + attr_value + bonus,
        "defaulted": False,
        "missing": False,
    }


def magic_opposed_test(
    skill_name: str,
    force: int,
    vs: int,
    mag: int,
    skill_totals: dict[str, int],
    skill_bonus: dict[str, int],
    attrs: dict[str, int],
    hits: int | None = None,
    opposed_hits: int | None = None,
    limit: int | None = None,
    limit_name: str = "Force",
    days: int | None = None,
    skills_data: dict[str, Any] | None = None,
    attr_override: str | None = None,
) -> dict[str, Any]:
    dice = skill_dice_pool(skill_name, skill_totals, skill_bonus, attrs, skills_data, attr_override=attr_override)
    used_limit = int(limit if limit is not None else force)
    my_hits = None if hits is None else max(0, int(hits))
    their_hits = None if opposed_hits is None else max(0, int(opposed_hits))
    net = None if my_hits is None or their_hits is None else my_hits - their_hits
    drain = None if their_hits is None else max(DRAIN_MINIMUM, their_hits * 2)
    physical = bool(mag) and int(force) > int(mag)
    return {
        **dice,
        "force": int(force),
        "limit": used_limit,
        "limit_name": limit_name,
        "vs": int(vs),
        "hits": my_hits,
        "opposed_hits": their_hits,
        "net": net,
        "drain": drain,
        "drain_code": None if drain is None else ("P" if physical else "S"),
        "physical": physical,
        "days": days,
    }


def _enhancement_by_id(eid: str) -> dict[str, Any] | None:
    for item in catalog().get("enhancements") or []:
        if item["id"] == eid:
            return item
    return None


def _ware_by_id(kind: str, wid: str) -> dict[str, Any] | None:
    for item in catalog().get(kind, {}).get("items") or []:
        if item["id"] == wid:
            return item
    return None


def _ware_by_name(kind: str, name: str) -> dict[str, Any] | None:
    for item in catalog().get(kind, {}).get("items") or []:
        if item["name"] == name:
            return item
    return None


def _grade_by_name(kind: str, name: str) -> dict[str, Any]:
    grades = catalog().get(kind, {}).get("grades") or []
    for g in grades:
        if g["name"] == name:
            return g
    other = "bioware" if kind == "cyberware" else "cyberware"
    for g in catalog().get(other, {}).get("grades") or []:
        if g["name"] == name:
            return g
    return next((g for g in grades if g["name"] == "Standard"), {"name": "Standard", "ess": 1.0, "cost": 1.0})


def racial_formula_extras(attrs_spec: dict[str, dict[str, int | float]]) -> dict[str, int]:
    extras: dict[str, int] = {}
    for key, spec in attrs_spec.items():
        extras[f"{key}Minimum"] = int(spec.get("min") or 1)
        extras[f"{key}Maximum"] = int(spec.get("max") or 6)
    return extras


def ware_rating_bounds(
    ware: dict[str, Any],
    extras: dict[str, int | float] | None = None,
) -> tuple[int, int]:
    extras = extras or {}
    lo = int(eval_formula(ware.get("minrating_expr") or str(ware.get("minrating") or 1), 1, default=1, extras=extras))
    hi = int(eval_formula(ware.get("maxrating_expr") or str(ware.get("maxrating") or 1), 1, default=1, extras=extras))
    if hi < lo:
        hi = lo
    return lo, hi


def _clamp_rating(ware: dict[str, Any], rating: int, extras: dict[str, int | float] | None = None) -> int:
    lo, hi = ware_rating_bounds(ware, extras)
    return max(lo, min(hi, int(rating or lo)))


def _limb_attr_effect(name: str) -> tuple[str, str] | None:
    lower = name.lower()
    if "customized strength" in lower or "customization, strength" in lower:
        return "STR", "set"
    if "customized agility" in lower or "customization, agility" in lower:
        return "AGI", "set"
    if "enhanced strength" in lower or "augmentation, strength" in lower:
        return "STR", "add"
    if "enhanced agility" in lower or "augmentation, agility" in lower:
        return "AGI", "add"
    return None


def _apply_limb_attributes(resolved: list[dict[str, Any]], attrs_spec: dict[str, dict[str, int | float]]) -> None:
    children: dict[str, list[dict[str, Any]]] = {}
    for item in resolved:
        if item.get("parent_id"):
            children.setdefault(item["parent_id"], []).append(item)
    for item in resolved:
        if item.get("category") != "Cyberlimb":
            continue
        str_val = int(attrs_spec.get("STR", {}).get("min") or 1)
        agi_val = int(attrs_spec.get("AGI", {}).get("min") or 1)
        for kid in children.get(item["id"]) or []:
            effect = _limb_attr_effect(kid.get("name") or "")
            if not effect:
                continue
            attr, mode = effect
            if attr == "STR":
                str_val = kid["rating"] if mode == "set" else str_val + int(kid["rating"])
            else:
                agi_val = kid["rating"] if mode == "set" else agi_val + int(kid["rating"])
        item["limb_str"] = str_val
        item["limb_agi"] = agi_val


LIMB_BODY_SLOTS = {"arm": 2, "leg": 2, "torso": 1}
LIMB_BODY_PARTS = 5
REDLINER_BASE_SLOTS = {"arm": 2, "leg": 2}
SIDES = ("Left", "Right")
_PARTIAL_LIMB = re.compile(r"\b(hand|foot|lower|modular connector)\b", re.I)
_MUSCLE_WARE = re.compile(r"\bmuscle (replacement|toner|augmentation)\b", re.I)
_SLOT_JA = {"arm": "腕", "leg": "脚", "torso": "胴", "skull": "頭蓋", "head": "頭蓋"}
_SIDE_JA = {"Left": "左", "Right": "右"}


def redliner_slot_caps(options: CharacterOptions | None = None) -> dict[str, int]:
    opts = options or CharacterOptions()
    slots = dict(REDLINER_BASE_SLOTS)
    if opts.redliner_torso:
        slots["torso"] = 1
    if opts.redliner_skull:
        slots["skull"] = 1
        slots["head"] = 1
    return slots


def _is_full_limb(item: dict[str, Any]) -> bool:
    if item.get("parent_id") or item.get("category") != "Cyberlimb":
        return False
    return _PARTIAL_LIMB.search(item.get("name") or "") is None


def _is_body_limb(item: dict[str, Any]) -> bool:
    if not _is_full_limb(item):
        return False
    slot = (item.get("limbslot") or "").lower()
    return slot in LIMB_BODY_SLOTS


def _is_redliner_limb(item: dict[str, Any], slots: dict[str, int]) -> bool:
    if not _is_full_limb(item):
        return False
    return (item.get("limbslot") or "").lower() in slots


def _limb_slot_count(item: dict[str, Any]) -> int:
    raw = str(item.get("limbslotcount") or "1").strip()
    if raw.lower() == "all":
        slot = (item.get("limbslot") or "").lower()
        return LIMB_BODY_SLOTS.get(slot, 1)
    try:
        return max(1, int(float(raw)))
    except ValueError:
        return 1


def _normalize_side(value: str | None) -> str | None:
    raw = (value or "").strip()
    if raw in SIDES:
        return raw
    lower = raw.lower()
    if lower in {"left", "l", "左"}:
        return "Left"
    if lower in {"right", "r", "右"}:
        return "Right"
    return None


def _occupied_sides(items: list[CyberwareInstall], kind: str, slot: str, skip_id: str | None = None) -> set[str]:
    used: set[str] = set()
    for inst in items:
        if inst.id == skip_id or inst.parent_id:
            continue
        ware = _ware_by_id(kind, inst.ware_id)
        if not ware or not ware.get("selectside"):
            continue
        if (ware.get("limbslot") or ware.get("id") or "").lower() != slot:
            continue
        side = _normalize_side(inst.side)
        if side:
            used.add(side)
    return used


def _next_free_side(items: list[CyberwareInstall], kind: str, ware: dict[str, Any], skip_id: str | None = None) -> str:
    slot = (ware.get("limbslot") or ware.get("id") or "").lower()
    used = _occupied_sides(items, kind, slot, skip_id=skip_id)
    if "Left" not in used:
        return "Left"
    if "Right" not in used:
        return "Right"
    return "Left"


def ensure_sides(kind: str, items: list[CyberwareInstall]) -> list[CyberwareInstall]:
    by_id = {inst.id: inst for inst in items}
    for inst in items:
        ware = _ware_by_id(kind, inst.ware_id)
        if not ware:
            continue
        if inst.parent_id:
            parent = by_id.get(inst.parent_id)
            if parent and parent.side:
                inst.side = parent.side
            continue
        if not ware.get("selectside"):
            inst.side = None
            continue
        inst.side = _normalize_side(inst.side) or _next_free_side(items, kind, ware, skip_id=inst.id)
    return items


def _side_conflicts(kind: str, items: list[CyberwareInstall]) -> list[str]:
    seen: set[tuple[str, str]] = set()
    dups: set[tuple[str, str]] = set()
    for inst in items:
        if inst.parent_id:
            continue
        ware = _ware_by_id(kind, inst.ware_id)
        if not ware or not ware.get("selectside"):
            continue
        side = _normalize_side(inst.side)
        if not side:
            continue
        slot = (ware.get("limbslot") or ware.get("id") or "").lower()
        key = (slot, side)
        if key in seen:
            dups.add(key)
        else:
            seen.add(key)
    errors: list[str] = []
    for slot, side in sorted(dups):
        slot_ja = _SLOT_JA.get(slot, slot)
        errors.append(f"{_SIDE_JA.get(side, side)}の{slot_ja}が重複しています")
    return errors


def limb_attribute_replace(
    resolved: list[dict[str, Any]],
    meat_str: int,
    meat_agi: int,
    attrs_spec: dict[str, dict[str, int | float]],
) -> dict[str, Any] | None:
    used = {slot: 0 for slot in LIMB_BODY_SLOTS}
    taken: set[tuple[str, str]] = set()
    limb_str: list[int] = []
    limb_agi: list[int] = []
    for item in resolved:
        if not _is_body_limb(item):
            continue
        slot = (item.get("limbslot") or "").lower()
        side = _normalize_side(item.get("side")) or ""
        key = (slot, side or item.get("id") or item.get("name") or "")
        if key in taken:
            continue
        if used[slot] >= LIMB_BODY_SLOTS[slot]:
            continue
        add = min(LIMB_BODY_SLOTS[slot] - used[slot], _limb_slot_count(item))
        if add <= 0:
            continue
        taken.add(key)
        used[slot] += add
        for _ in range(add):
            limb_str.append(int(item.get("limb_str") or meat_str))
            limb_agi.append(int(item.get("limb_agi") or meat_agi))
    count = min(LIMB_BODY_PARTS, sum(used.values()))
    if count == 0:
        return None
    meat_parts = LIMB_BODY_PARTS - count
    str_avg = (sum(limb_str) + meat_str * meat_parts) // LIMB_BODY_PARTS
    agi_avg = (sum(limb_agi) + meat_agi * meat_parts) // LIMB_BODY_PARTS
    str_avg = min(int(attrs_spec.get("STR", {}).get("aug") or 9), str_avg)
    agi_avg = min(int(attrs_spec.get("AGI", {}).get("aug") or 9), agi_avg)
    return {
        "count": count,
        "parts": LIMB_BODY_PARTS,
        "slots": used,
        "str": str_avg,
        "agi": agi_avg,
        "meat_str": meat_str,
        "meat_agi": meat_agi,
    }


def count_redliner_limbs(resolved: list[dict[str, Any]], slots: dict[str, int] | None = None) -> int:
    slots = slots or redliner_slot_caps()
    taken: set[tuple[str, str]] = set()
    total = 0
    used = {slot: 0 for slot in slots}
    for item in resolved:
        if not _is_redliner_limb(item, slots):
            continue
        slot = (item.get("limbslot") or "").lower()
        side = _normalize_side(item.get("side")) or ""
        key = (slot, side or item.get("id") or item.get("name") or "")
        if key in taken:
            continue
        cap = slots.get(slot, 0)
        if used[slot] >= cap:
            continue
        taken.add(key)
        add = min(cap - used[slot], _limb_slot_count(item))
        used[slot] += add
        total += add
    return total


def apply_cyberseeker(
    resolved: list[dict[str, Any]],
    targets: list[str],
    attrs_spec: dict[str, dict[str, int | float]],
    options: CharacterOptions | None = None,
) -> dict[str, Any] | None:
    if not targets:
        return None
    slots = redliner_slot_caps(options)
    count = count_redliner_limbs(resolved, slots)
    pairs = count // 2
    attr_bonus = {k: 0 for k in ("STR", "AGI", "WIL", "BOD", "REA", "CHA", "INT", "LOG")}
    cm_physical = 0
    limb_bonus = 0
    for target in targets:
        if target in {"STR", "AGI"}:
            attr_bonus[target] = pairs
            limb_bonus = pairs
        elif target == "BOX":
            cm_physical -= pairs
        elif target in attr_bonus:
            attr_bonus[target] = pairs
    if limb_bonus:
        str_aug = int(attrs_spec.get("STR", {}).get("aug") or 9)
        agi_aug = int(attrs_spec.get("AGI", {}).get("aug") or 9)
        for item in resolved:
            if item.get("category") != "Cyberlimb" or item.get("parent_id"):
                continue
            if item.get("limb_str") is not None:
                item["limb_str"] = min(str_aug, int(item["limb_str"]) + limb_bonus)
            if item.get("limb_agi") is not None:
                item["limb_agi"] = min(agi_aug, int(item["limb_agi"]) + limb_bonus)
    included = [slot for slot in ("arm", "leg", "torso", "skull") if slot in slots]
    return {
        "count": count,
        "pairs": pairs,
        "limb_bonus": limb_bonus,
        "attribute_bonus": {k: v for k, v in attr_bonus.items() if v},
        "cm_physical": cm_physical,
        "include": included,
    }


def redliner_incompat_warnings(installed: list[dict[str, Any]], targets: list[str]) -> list[str]:
    if not any(tag in {"STR", "AGI"} for tag in targets):
        return []
    names: list[str] = []
    seen: set[str] = set()
    for item in installed:
        if item.get("parent_id"):
            continue
        name = item.get("name") or ""
        if not _MUSCLE_WARE.search(name) or name in seen:
            continue
        seen.add(name)
        names.append(name)
    if not names:
        return []
    joined = " / ".join(names)
    return [f"Redliner は {joined} と併用できません（肢の特注・強化は可）"]


def ware_ranges(attrs_spec: dict[str, dict[str, int | float]]) -> dict[str, dict[str, int]]:
    extras = racial_formula_extras(attrs_spec)
    out: dict[str, dict[str, int]] = {}
    for kind in ("cyberware", "bioware"):
        for ware in catalog().get(kind, {}).get("items") or []:
            if not ware.get("formula_rating"):
                continue
            lo, hi = ware_rating_bounds(ware, extras)
            out[ware["id"]] = {"min": lo, "max": hi}
    return out


def _capacity_value(expr: str | None, rating: int) -> float:
    raw = (expr or "").strip()
    if not raw or raw == "*":
        return 0.0
    if "/" in raw:
        raw = raw.split("/", 1)[0].strip()
    return eval_formula(raw, rating, default=0.0)


def _cascade_orphans(
    items: list[CyberwareInstall],
    extra_parent_ids: set[str] | None = None,
) -> list[CyberwareInstall]:
    ids = {item.id for item in items} | (extra_parent_ids or set())
    keep = [item for item in items if not item.parent_id or item.parent_id in ids]
    if len(keep) == len(items):
        return keep
    return _cascade_orphans(keep, extra_parent_ids)


def _vehicle_mod_hosts(state: CharacterState) -> dict[str, dict[str, Any]]:
    specs = {item["id"]: item for item in catalog().get("vehicle_mods") or []}
    parents = {inst.id: spec for inst, spec in _iter_vehicle_hosts(state)}
    hosts: dict[str, dict[str, Any]] = {}
    for inst in state.vehicle_mods or []:
        spec = specs.get(inst.mod_id)
        parent = parents.get(inst.parent_id or "")
        if not spec or not spec.get("subsystems") or not parent:
            continue
        if not inst.included and not mod_fits_vehicle(spec, parent):
            continue
        hosts[inst.id] = spec
    return hosts


def _ware_fits_vehicle_mod(ware: dict[str, Any], spec: dict[str, Any]) -> bool:
    if ware.get("category") not in (spec.get("subsystems") or []):
        return False
    if not (ware.get("plugin") or ware.get("requireparent")):
        return False
    names = ware.get("required_parent_names") or []
    if not names:
        return True
    parent_name = spec.get("name") or ""
    return any(name in parent_name for name in names)


def _drop_invalid_vehicle_ware(state: CharacterState) -> list[str]:
    hosts = _vehicle_mod_hosts(state)
    cyber_ids = {item.id for item in state.cyberware}
    warnings: list[str] = []
    kept: list[CyberwareInstall] = []
    for inst in state.cyberware:
        parent_id = inst.parent_id
        if not parent_id or parent_id in cyber_ids:
            kept.append(inst)
            continue
        spec = hosts.get(parent_id)
        ware = _ware_by_id("cyberware", inst.ware_id)
        if not spec or not ware:
            continue
        if not _ware_fits_vehicle_mod(ware, spec):
            warnings.append(f"{ware['name']} は {spec['name']} に装着できません")
            continue
        kept.append(inst)
    state.cyberware = _cascade_orphans(kept, set(hosts))
    return warnings


def _vehicle_hosted_ware_ids(resolved: list[dict[str, Any]], vehicle_hosts: set[str]) -> set[str]:
    hosted: set[str] = set()
    by_id = {str(item.get("id") or ""): item for item in resolved}

    def is_hosted(item: dict[str, Any]) -> bool:
        parent_id = item.get("parent_id") or ""
        seen: set[str] = set()
        while parent_id:
            if parent_id in vehicle_hosts:
                return True
            if parent_id in seen:
                return False
            seen.add(parent_id)
            parent = by_id.get(parent_id)
            if not parent:
                return False
            parent_id = parent.get("parent_id") or ""
        return False

    for item in resolved:
        if is_hosted(item):
            hosted.add(str(item.get("id") or ""))
    return hosted


def _zero_vehicle_hosted_essence(resolved: list[dict[str, Any]], vehicle_hosts: set[str]) -> None:
    hosted = _vehicle_hosted_ware_ids(resolved, vehicle_hosts)
    for item in resolved:
        if item.get("id") in hosted:
            item["essence"] = 0.0
            item["ess_to_parent"] = 0.0


def _attach_ware_to_vehicle_mods(mods: list[dict[str, Any]], ware: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    by_id = {str(mod.get("id") or ""): mod for mod in mods}
    for mod in mods:
        mod["cyberware"] = []
        mod["capacity_used"] = 0.0
    for item in ware:
        parent = by_id.get(str(item.get("parent_id") or ""))
        if not parent:
            continue
        parent["cyberware"].append(_public_installed(item))
        parent["capacity_used"] = round(
            float(parent.get("capacity_used") or 0) + float(item.get("capacity_cost") or 0),
            4,
        )
    for mod in mods:
        cap_max = float(mod.get("capacity_max") or 0)
        used = float(mod.get("capacity_used") or 0)
        if cap_max > 0 and used > cap_max + 1e-9:
            errors.append(f"{mod['name']} の容量超過（{used:g}/{cap_max:g}）")
    return errors


def ensure_subsystems(state: CharacterState) -> CharacterState:
    extra = set(_vehicle_mod_hosts(state))
    state.cyberware = ensure_sides("cyberware", _ensure_kind_subsystems("cyberware", state.cyberware, extra))
    state.bioware = ensure_sides("bioware", _ensure_kind_subsystems("bioware", state.bioware))
    return state


def _ensure_kind_subsystems(
    kind: str,
    items: list[CyberwareInstall],
    extra_parent_ids: set[str] | None = None,
) -> list[CyberwareInstall]:
    items = _cascade_orphans(list(items), extra_parent_ids)
    existing = {(item.parent_id, item.ware_id) for item in items}
    extra: list[CyberwareInstall] = []
    for inst in items:
        if inst.parent_id:
            continue
        ware = _ware_by_id(kind, inst.ware_id)
        if not ware:
            continue
        for name in ware.get("subsystems") or []:
            sub = _ware_by_name(kind, name)
            if not sub or (inst.id, sub["id"]) in existing:
                continue
            extra.append(
                CyberwareInstall(
                    ware_id=sub["id"],
                    rating=_clamp_rating(sub, int(sub.get("minrating") or 1)),
                    grade=ware.get("forcegrade") or inst.grade or "Standard",
                    wireless=inst.wireless,
                    parent_id=inst.id,
                    included=True,
                )
            )
            existing.add((inst.id, sub["id"]))
    return items + extra if extra else items


def resolve_ware(
    kind: str,
    installs: list[CyberwareInstall],
    attrs_spec: dict[str, dict[str, int | float]] | None = None,
) -> list[dict[str, Any]]:
    extras = racial_formula_extras(attrs_spec) if attrs_spec else {}
    resolved: list[dict[str, Any]] = []
    for inst in installs:
        ware = _ware_by_id(kind, inst.ware_id)
        if not ware:
            continue
        lo, hi = ware_rating_bounds(ware, extras)
        rating = max(lo, min(hi, int(inst.rating or lo)))
        grade_name = ware.get("forcegrade") or inst.grade or "Standard"
        grade = _grade_by_name(kind, grade_name)
        slotted = bool(inst.parent_id)
        included = bool(inst.included)
        plugin = bool(ware.get("plugin"))
        add_to_parent = bool(ware.get("addtoparentess")) and slotted and not included
        formula_extras = {**extras, "MinRating": lo}
        ess_base = round(
            eval_formula(ware.get("ess"), rating, extras=formula_extras) * float(grade.get("ess") or 1), 4
        )
        ess = 0.0 if included or (slotted and (plugin or add_to_parent)) else ess_base
        cost = 0 if included else int(
            round(eval_formula(ware.get("cost"), rating, extras=formula_extras) * float(grade.get("cost") or 1))
        )
        nodes = substitute_rating(ware.get("bonus") or [], rating)
        if inst.wireless:
            nodes = nodes + substitute_rating(ware.get("wirelessbonus") or [], rating)
        resolved.append(
            {
                "id": inst.id,
                "ware_id": ware["id"],
                "name": ware["name"],
                "category": ware["category"],
                "rating": rating,
                "rating_min": lo,
                "rating_max": hi,
                "grade": grade["name"],
                "wireless": bool(inst.wireless),
                "parent_id": inst.parent_id,
                "included": included,
                "plugin": plugin,
                "essence": ess,
                "nuyen": cost,
                "capacity_cost": _capacity_value(ware.get("capacity"), rating) if plugin else 0.0,
                "capacity_used": 0.0,
                "capacity_max": 0.0 if plugin else _capacity_value(ware.get("capacity"), rating),
                "allow_subsystems": list(ware.get("allow_subsystems") or []),
                "limbslot": ware.get("limbslot"),
                "limbslotcount": ware.get("limbslotcount") or "1",
                "selectside": bool(ware.get("selectside")),
                "side": _normalize_side(inst.side),
                "avail": ware.get("avail") or "",
                "source": ware.get("source"),
                "bonus": nodes,
                "ess_to_parent": ess_base if add_to_parent else 0.0,
                "add_weapon": ware.get("add_weapon") or "",
                "add_weapon_id": ware.get("add_weapon_id") or "",
                "device_rating": _device_rating_of(ware, rating),
            }
        )
    children: dict[str, list[dict[str, Any]]] = {}
    for item in resolved:
        if item["parent_id"]:
            children.setdefault(item["parent_id"], []).append(item)
    for item in resolved:
        kids = children.get(item["id"]) or []
        item["capacity_used"] = round(sum(float(kid["capacity_cost"]) for kid in kids), 4)
        extra_ess = sum(float(kid.get("ess_to_parent") or 0) for kid in kids)
        if extra_ess:
            item["essence"] = round(float(item["essence"]) + extra_ess, 4)
    if attrs_spec:
        _apply_limb_attributes(resolved, attrs_spec)
    return resolved


def resolve_cyberware(state: CharacterState) -> list[dict[str, Any]]:
    meta = find_metatype(state.metatype, state.metavariant)
    return resolve_ware("cyberware", state.cyberware, meta["attributes"])


def _public_installed(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": item["id"],
        "ware_id": item["ware_id"],
        "name": item["name"],
        "category": item["category"],
        "rating": item["rating"],
        "grade": item["grade"],
        "wireless": item["wireless"],
        "parent_id": item.get("parent_id"),
        "included": bool(item.get("included")),
        "essence": item["essence"],
        "nuyen": item["nuyen"],
        "capacity_used": item.get("capacity_used") or 0,
        "capacity_max": item.get("capacity_max") or 0,
        "rating_min": item.get("rating_min") or 1,
        "rating_max": item.get("rating_max") or 1,
        "limb_str": item.get("limb_str"),
        "limb_agi": item.get("limb_agi"),
        "selectside": bool(item.get("selectside")),
        "side": item.get("side"),
        "avail": item.get("avail") or "",
        "avail_value": int(item.get("avail_value") or 0),
        "restricted_gear": bool(item.get("restricted_gear")),
        "device_rating": int(item.get("device_rating") or 0),
        "source": item.get("source"),
    }


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
    for name in state.native_languages or []:
        name = str(name).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        if natives:
            extras.append(name)
            continue
        natives.append(name)
        ratings.pop(name, None)
    if extras:
        warnings.append("母語は1つまでです（2つ目以降は通常の言語として扱います）")

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
    }


def resolve_specializations(
    state: CharacterState,
    skills_data: dict[str, Any],
    skill_totals: dict[str, int],
    skillsoft_active: dict[str, int],
    skillsoft_knowledge: dict[str, int],
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
                warnings.append(f"{name} の専門化には知識スキルが必要です")
                continue
            knowledge_spent += 1
        else:
            if name not in active_names:
                warnings.append(f"{name} の専門化は未知のスキルです")
                continue
            rating = max(int(skill_totals.get(name) or 0), int((skillsoft_active or {}).get(name) or 0))
            if rating < 1:
                warnings.append(f"{name} の専門化にはスキルが必要です")
                continue
            active_spent += 1
        cleaned[name] = spec
    state.skill_specializations = cleaned
    return {
        "warnings": warnings,
        "active_spent": active_spent,
        "knowledge_spent": knowledge_spent,
        "specs": cleaned,
    }


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
    catalog_by_name = {
        skill["name"]: skill for skill in skills_data.get("skills") or [] if skill.get("exotic")
    }
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


def _copy_exotic_skill_bonuses(skill_mods: dict[str, Any], public: list[dict[str, Any]]) -> None:
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


def resolve_contacts(state: CharacterState, cha: int, *, career: bool = False) -> dict[str, Any]:
    warnings: list[str] = []
    public: list[dict[str, Any]] = []
    kept: list[ContactInstall] = []
    used = 0
    free_max = max(0, int(cha or 0) * CONTACT_FREE_MULT)
    for inst in state.contacts or []:
        name = (inst.name or "").strip()
        role = (inst.role or "").strip()
        connection = max(CONTACT_RATING_MIN, min(CONTACT_RATING_MAX, int(inst.connection or 1)))
        loyalty = max(CONTACT_RATING_MIN, min(CONTACT_RATING_MAX, int(inst.loyalty or 1)))
        if not career and connection + loyalty > CONTACT_CHARGEN_COST_MAX:
            loyalty = max(CONTACT_RATING_MIN, CONTACT_CHARGEN_COST_MAX - connection)
            warnings.append(f"{name or 'コネクト'} は作成時 Connection+Loyalty が{CONTACT_CHARGEN_COST_MAX}までです")
        inst.name = name
        inst.role = role or None
        inst.connection = connection
        inst.loyalty = loyalty
        cost = connection + loyalty
        if not name:
            warnings.append("名前のないコネクトがあります")
        kept.append(inst)
        used += cost
        if career:
            conn_max = CONTACT_RATING_MAX
            loy_max = CONTACT_RATING_MAX
        else:
            conn_max = min(CONTACT_RATING_MAX, CONTACT_CHARGEN_COST_MAX - loyalty)
            loy_max = min(CONTACT_RATING_MAX, CONTACT_CHARGEN_COST_MAX - connection)
        public.append(
            {
                "id": inst.id,
                "name": name,
                "role": role,
                "connection": connection,
                "loyalty": loyalty,
                "cost": cost,
                "connection_max": conn_max,
                "loyalty_max": loy_max,
            }
        )
    state.contacts = kept
    paid = max(0, used - free_max)
    return {
        "warnings": warnings,
        "public": public,
        "used": used,
        "free": free_max,
        "paid": paid,
        "karma": paid,
    }


def _martial_art_by_id(art_id: str) -> dict[str, Any] | None:
    for item in catalog().get("martial_arts") or []:
        if item["id"] == art_id:
            return item
    return None


def _martial_technique_by_name(name: str) -> dict[str, Any] | None:
    for item in catalog().get("martial_art_techniques") or []:
        if item["name"] == name:
            return item
    return None


def _martial_art_spec_options(bonus_nodes: list[dict[str, Any]] | None) -> list[tuple[str, str]]:
    options: list[tuple[str, str]] = []
    for node in bonus_nodes or []:
        if node.get("tag") != "addskillspecializationoption":
            continue
        fields = node.get("fields") or {}
        skill = str(fields.get("skill") or "").strip()
        spec = str(fields.get("spec") or "").strip()
        if skill and spec:
            options.append((skill, spec))
    return options


def resolve_martial_arts(
    state: CharacterState,
    ctx: dict[str, Any],
    errors: list[str],
    *,
    career: bool = False,
) -> dict[str, Any]:
    warnings: list[str] = []
    public: list[dict[str, Any]] = []
    kept: list[MartialArtInstall] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    spec_extras: dict[str, list[str]] = {}
    unarmed_reach = 0
    karma = 0
    technique_total = 0

    for inst in state.martial_arts or []:
        spec = _martial_art_by_id(inst.art_id)
        if not spec:
            warnings.append("未知の武道を外しました")
            continue
        if spec.get("is_quality"):
            warnings.append(f"{spec['name']} はクオリティ経由のみです")
            continue
        if spec.get("required_tree") and not requirement_tree_met(spec.get("required_tree"), ctx):
            errors.append(f"{spec['name']} の前提を満たしていません")
            continue

        allowed = set(spec.get("techniques") or [])
        if spec.get("all_techniques"):
            allowed = {item["name"] for item in catalog().get("martial_art_techniques") or []}
        picked: list[str] = []
        seen: set[str] = set()
        for raw in inst.techniques or []:
            name = str(raw or "").strip()
            if not name or name in seen:
                continue
            if name not in allowed:
                warnings.append(f"{spec['name']} に {name} は選べません")
                continue
            seen.add(name)
            picked.append(name)
        if not picked:
            warnings.append(f"{spec['name']} の技を1つ選んでください")
            continue

        style_cost = int(spec.get("cost") or MARTIAL_ART_STYLE_KARMA)
        paid_techniques = max(0, len(picked) - 1)
        art_karma = style_cost + paid_techniques * MARTIAL_ART_TECHNIQUE_KARMA
        karma += art_karma
        technique_total += len(picked)

        tech_public: list[dict[str, Any]] = []
        for idx, name in enumerate(picked):
            tech = _martial_technique_by_name(name) or {"id": "", "name": name, "bonus": [], "source": "", "page": ""}
            free = idx == 0
            tech_public.append(
                {
                    "id": tech.get("id") or "",
                    "name": name,
                    "free": free,
                    "karma": 0 if free else MARTIAL_ART_TECHNIQUE_KARMA,
                    "source": tech.get("source") or "",
                    "page": tech.get("page") or "",
                }
            )
            for node in tech.get("bonus") or []:
                if node.get("tag") == "unarmedreach":
                    unarmed_reach += _as_int(node.get("value") or 0)
                else:
                    bonus_sources.append((f"{spec['name']}:{name}", [node]))

        for skill_name, spec_name in _martial_art_spec_options(spec.get("bonus") or []):
            bucket = spec_extras.setdefault(skill_name, [])
            if spec_name not in bucket:
                bucket.append(spec_name)
        # Still collect other art bonuses (none today besides addskillspecializationoption)
        other_nodes = [
            node
            for node in (spec.get("bonus") or [])
            if node.get("tag") != "addskillspecializationoption"
        ]
        if other_nodes:
            bonus_sources.append((spec["name"], other_nodes))

        inst.techniques = picked
        kept.append(inst)
        public.append(
            {
                "id": inst.id,
                "art_id": spec["id"],
                "name": spec["name"],
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
                "style_karma": style_cost,
                "karma": art_karma,
                "techniques": tech_public,
                "technique_options": sorted(allowed),
            }
        )

    state.martial_arts = kept
    style_max = 99 if career else MARTIAL_ART_CHARGEN_STYLE_MAX
    tech_max = 99 if career else MARTIAL_ART_CHARGEN_TECHNIQUE_MAX
    if not career and len(kept) > MARTIAL_ART_CHARGEN_STYLE_MAX:
        errors.append(
            f"作成時の武道流派は{MARTIAL_ART_CHARGEN_STYLE_MAX}つまでです（現在 {len(kept)}）"
        )
    if not career and technique_total > MARTIAL_ART_CHARGEN_TECHNIQUE_MAX:
        errors.append(
            f"作成時の武道技は合計{MARTIAL_ART_CHARGEN_TECHNIQUE_MAX}つまでです（現在 {technique_total}）"
        )

    return {
        "warnings": warnings,
        "public": public,
        "karma": karma,
        "style_count": len(kept),
        "technique_count": technique_total,
        "style_max": style_max,
        "technique_max": tech_max,
        "spec_extras": spec_extras,
        "unarmed_reach": unarmed_reach,
        "bonus_sources": bonus_sources,
    }


def resolve_skill_mods(
    skills_data: dict[str, Any],
    effects: dict[str, Any],
    knowledge_ratings: dict[str, int],
    extra_categories: dict[str, str] | None = None,
) -> dict[str, Any]:
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


def parse_selectskill_spec(node: dict[str, Any]) -> dict[str, Any]:
    fields = node.get("fields") or {}
    attrs = node.get("attrs") or {}
    knowledge = str(attrs.get("knowledgeskills") or "False").lower() == "true"
    return {
        "bonus": _as_int(fields.get("val") or fields.get("bonus") or fields.get("value") or node.get("value")),
        "max": _as_int(fields.get("max")),
        "applytorating": str(fields.get("applytorating") or "").lower() == "true",
        "limittoattribute": attrs.get("limittoattribute") or "",
        "limittoskill": attrs.get("limittoskill") or "",
        "limittoskillgroup": attrs.get("limittoskillgroup") or "",
        "limittocategory": attrs.get("limittocategory")
        or attrs.get("skillcategory")
        or ", ".join((node.get("nested") or {}).get("skillcategories") or []),
        "excludecategory": attrs.get("excludecategory") or "",
        "knowledgeskills": knowledge,
        "minimumrating": _as_int(attrs.get("minimumrating")),
        "condition": (fields.get("condition") or "").strip(),
    }


def selectskill_options(
    spec: dict[str, Any],
    skills_data: dict[str, Any],
    skill_totals: dict[str, int],
) -> list[str]:
    if spec.get("knowledgeskills"):
        pool = list(skills_data.get("knowledge") or [])
    else:
        pool = [skill for skill in (skills_data.get("skills") or []) if not skill.get("exotic")]
    attrs = {part.strip().upper() for part in (spec.get("limittoattribute") or "").split(",") if part.strip()}
    names = {part.strip() for part in (spec.get("limittoskill") or "").split(",") if part.strip()}
    groups = {part.strip() for part in (spec.get("limittoskillgroup") or "").split(",") if part.strip()}
    cats = {part.strip() for part in (spec.get("limittocategory") or "").split(",") if part.strip()}
    exclude_cats = {part.strip() for part in (spec.get("excludecategory") or "").split(",") if part.strip()}
    minimum = int(spec.get("minimumrating") or 0)
    out: list[str] = []
    for skill in pool:
        if attrs and (skill.get("attribute") or "").upper() not in attrs:
            continue
        if names and skill["name"] not in names:
            continue
        if groups and (skill.get("skillgroup") or "") not in groups:
            continue
        if cats and (skill.get("category") or "") not in cats:
            continue
        if exclude_cats and (skill.get("category") or "") in exclude_cats:
            continue
        if minimum and int(skill_totals.get(skill["name"], 0)) < minimum:
            continue
        out.append(skill["name"])
    return sorted(set(out))


def gear_extra_options(spec: dict[str, Any], skills_data: dict[str, Any] | None = None) -> list[str]:
    data = skills_data if skills_data is not None else catalog().get("skills") or {}
    extra_kind = str(spec.get("extra_kind") or "")
    if extra_kind == "group" or str(spec.get("name") or "").startswith("Group Autosoft"):
        return list(data.get("groups") or [])
    for node in spec.get("bonus") or []:
        tag = node.get("tag")
        if tag == "selectskill":
            return selectskill_options(parse_selectskill_spec(node), data, {})
        if tag == "selecttext":
            return selecttext_options(node.get("attrs") or {})
        if tag in {"activesoft", "skillsoft", "knowsoft", "linguasoft"}:
            return skillsoft_options(node, data)
        if tag == "selecttradition":
            return [t["name"] for t in catalog().get("traditions") or []]
    return []


def _csv_names(value: Any) -> set[str]:
    if isinstance(value, list):
        parts = [str(item).strip() for item in value]
    else:
        parts = [part.strip() for part in str(value or "").split(",")]
    return {part for part in parts if part}


def skillsoft_options(node: dict[str, Any], skills_data: dict[str, Any]) -> list[str]:
    kind = _skillsoft_kind(node)
    if kind == "active":
        return [skill["name"] for skill in skills_data.get("skills") or []]
    knowledge = list(skills_data.get("knowledge") or [])
    fields = node.get("fields") or {}
    attrs = node.get("attrs") or {}
    cats = _csv_names(fields.get("skillcategory") or attrs.get("skillcategory"))
    exclude = _csv_names(fields.get("excludecategory") or attrs.get("excludecategory"))
    if kind == "language":
        cats = cats or {"Language"}
    out: list[str] = []
    for skill in knowledge:
        category = str(skill.get("category") or "")
        if cats and category not in cats:
            continue
        if category in exclude:
            continue
        out.append(skill["name"])
    return out


def _skillsoft_kind(node: dict[str, Any]) -> str:
    tag = str(node.get("tag") or "")
    fields = node.get("fields") or {}
    attrs = node.get("attrs") or {}
    cats = _csv_names(fields.get("skillcategory") or attrs.get("skillcategory"))
    exclude = _csv_names(fields.get("excludecategory") or attrs.get("excludecategory"))
    if tag == "activesoft":
        return "active"
    if tag == "linguasoft" or "Language" in cats:
        return "language"
    if tag in {"skillsoft", "knowsoft"}:
        if "Language" in exclude:
            return "knowledge"
        if "Language" in cats:
            return "language"
        return "knowledge"
    return ""


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
    effects: dict[str, Any],
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
                "attribute": str(spec.get("attribute") or KNOWLEDGE_DEFAULT_ATTR.get(spec.get("category") or "", "INT")).upper(),
                "rating": 0,
                "native": False,
                "skillsoft": int(rating),
            }
        )


def selecttext_options(attrs: dict[str, Any]) -> list[str]:
    xml = str(attrs.get("xml") or "")
    xpath = str(attrs.get("xpath") or "")
    if "vehicles.xml" in xml:
        names = list(catalog().get("vehicle_names") or [])
        if not names:
            names = [item["name"] for item in catalog().get("drones") or []]
        return names
    if "weapons.xml" in xml:
        weapons = catalog().get("weapons") or []
        if "Melee" in xpath:
            return [item["name"] for item in weapons if item.get("type") == "Melee"]
        if "Ranged" in xpath:
            return [item["name"] for item in weapons if item.get("type") == "Ranged"]
        return [item["name"] for item in weapons]
    if "skills.xml" in xml:
        skills = catalog().get("skills") or {}
        names = [s["name"] for s in skills.get("skills") or []]
        if "knowledge" in xpath.lower():
            names += [s["name"] for s in skills.get("knowledge") or []]
        return names
    return []


def _extra_kind(spec: dict[str, Any]) -> str:
    return str(spec.get("extra_kind") or "")


def _program_label(spec: dict[str, Any], extra: str | None) -> str:
    name = str(spec.get("name") or "")
    extra = (extra or "").strip()
    if extra:
        for token in ("[Model]", "[Weapon]"):
            if token in name:
                return f"{name.replace(token, '').strip()} ({extra})"
        return f"{name} ({extra})"
    return name


def resolve_skill_picks(
    state: CharacterState,
    skills_data: dict[str, Any],
    skill_totals: dict[str, int],
) -> dict[str, Any]:
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
            warnings.append(f"{source} のスキル指定が無効です（{picked}）")
            picked = ""
        if not picked:
            warnings.append(f"{source} のスキルを選んでください")
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


def power_point_cost(spec: dict[str, Any], rating: int, discounted: bool = False) -> float:
    points = float(spec.get("points") or 0)
    extra = float(spec.get("extrapointcost") or 0)
    rating = max(1, int(rating))
    if spec.get("levels"):
        cost = points * rating
        if extra:
            cost += extra
    else:
        cost = points
    if discounted:
        cost = max(0.0, cost - float(spec.get("adeptway") or 0))
    return round(cost, 4)


def way_discount_cap(mag: int) -> float:
    return float(_ceil_div(max(int(mag), 0) / 4))


def way_discount_eligible(spec: dict[str, Any], quality_names: set[str], magicians_way: bool) -> bool:
    if not float(spec.get("adeptway") or 0):
        return False
    if magicians_way and not spec.get("magicianswayforbids"):
        return True
    return any(name in quality_names for name in (spec.get("adeptwayrequires") or []))


def power_max_rating(spec: dict[str, Any], mag: int) -> int:
    if not spec.get("levels"):
        return 1
    if spec.get("maxlevels"):
        return int(spec["maxlevels"])
    if str(spec.get("name") or "").startswith("Improved Ability"):
        return max(1, _ceil_div(max(int(mag), 1) / 2))
    return max(1, int(mag))


def _field_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if value:
        return [str(value)]
    return []


def bind_power_bonus(nodes: list[dict[str, Any]], extra: str, rating: int) -> list[dict[str, Any]]:
    bound: list[dict[str, Any]] = []
    for node in substitute_rating(nodes, rating):
        tag = node.get("tag")
        fields = dict(node.get("fields") or {})
        if tag == "selectskill":
            if not extra:
                continue
            fields["name"] = extra
            bound.append({"tag": "specificskill", "fields": fields})
            continue
        if tag == "selectattribute":
            bonus = fields.get("val") or fields.get("bonus") or fields.get("value")
            if not extra or bonus in (None, ""):
                continue
            bound.append({"tag": "specificattribute", "fields": {"name": extra, "bonus": bonus}})
            continue
        if tag == "selectspell":
            continue
        bound.append(node)
    return bound


def power_select_options(spec: dict[str, Any], skills_data: dict[str, Any]) -> list[str]:
    kind = spec.get("select")
    if kind == "skill":
        node = next((item for item in (spec.get("bonus") or []) if item.get("tag") == "selectskill"), None)
        if not node:
            return []
        parsed = parse_selectskill_spec(node)
        parsed["minimumrating"] = 0
        return selectskill_options(parsed, skills_data, {})
    if kind == "attribute":
        node = next((item for item in (spec.get("bonus") or []) if item.get("tag") == "selectattribute"), None)
        if not node:
            return []
        return _field_list((node.get("fields") or {}).get("attribute"))
    if kind == "spell":
        return [
            item["name"]
            for item in catalog().get("spells") or []
            if item.get("category") in SPELL_CAST_CATEGORIES
        ]
    return []


def _choice_allowed(audience: str, talent_name: str) -> bool:
    if audience == "all":
        return True
    if audience == "adept":
        return talent_name in ADEPT_TALENTS
    if audience == "magician":
        return talent_name in MAG_TALENTS and talent_name != "Adept"
    return False


def gather_qualities(state: CharacterState, talent: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    qualities: list[dict[str, Any]] = []
    seen: set[str] = set()
    free_ids: set[str] = set()
    state.quality_ids, dropped = sanitize_quality_ids(list(state.quality_ids))
    pending = list(state.quality_ids)
    talent_quality = _quality_by_name(talent.get("quality") or "")
    if talent_quality:
        pending.append(talent_quality["id"])
    index = 0
    while index < len(pending):
        qid = pending[index]
        index += 1
        if qid in seen:
            continue
        spec = _quality_by_id(qid)
        if not spec:
            continue
        seen.add(qid)
        qualities.append(spec)
        for node in spec.get("bonus") or []:
            tag = node.get("tag")
            if tag == "freequality":
                child_id = str(node.get("value") or "").strip()
                if child_id and child_id not in seen:
                    free_ids.add(child_id)
                    pending.append(child_id)
            elif tag == "addqualities":
                raw = (node.get("fields") or {}).get("addquality") or node.get("value") or ""
                names = raw if isinstance(raw, list) else [raw]
                for name in names:
                    child = _quality_by_name(str(name).strip())
                    if child and child["id"] not in seen:
                        free_ids.add(child["id"])
                        pending.append(child["id"])
    return qualities, sorted(free_ids), dropped


def resolve_mentor(
    state: CharacterState,
    talent_name: str,
    needs_mentor: bool,
    skills_data: dict[str, Any],
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    free_powers: list[dict[str, Any]] = []
    public: dict[str, Any] | None = None
    if not needs_mentor:
        state.mentor_id = None
        state.mentor_choices = []
        state.mentor_extras = {}
        return {
            "warnings": warnings,
            "errors": errors,
            "bonus_sources": bonus_sources,
            "free_powers": free_powers,
            "public": None,
        }
    spec = _mentor_by_id(state.mentor_id or "")
    if not spec:
        warnings.append("メンタースピリットを選んでください")
        return {
            "warnings": warnings,
            "errors": errors,
            "bonus_sources": bonus_sources,
            "free_powers": free_powers,
            "public": None,
        }
    bonus_sources.append((spec["name"], spec.get("bonus") or []))
    allowed = [choice for choice in spec.get("choices") or [] if _choice_allowed(choice.get("audience") or "all", talent_name)]
    groups: dict[str, list[dict[str, Any]]] = {}
    for choice in allowed:
        audience = choice.get("audience") or "all"
        raw_set = str(choice.get("set") or "")
        if raw_set:
            key = f"set:{raw_set}"
        elif audience == "all":
            key = "all"
        else:
            key = f"solo:{choice['name']}"
        groups.setdefault(key, []).append(choice)
    selected: list[str] = []
    wanted = {name for name in (state.mentor_choices or []) if name}
    for key, choices in groups.items():
        names = [choice["name"] for choice in choices]
        picked = next((name for name in names if name in wanted), "")
        if not picked:
            picked = names[0]
        selected.append(picked)
        choice = next(item for item in choices if item["name"] == picked)
        extra = (state.mentor_extras or {}).get(picked, "")
        choice_nodes = [node for node in (choice.get("bonus") or []) if node.get("tag") != "specificpower"]
        bonus_sources.append((f"{spec['name']}: {picked}", choice_nodes))
        for power in choice.get("powers") or []:
            power_spec = _power_by_name(power["name"])
            if not power_spec:
                continue
            options = power_select_options(power_spec, skills_data)
            bound_extra = extra if extra in options else ""
            if power_spec.get("select") and not bound_extra:
                warnings.append(f"{spec['name']} の {power_spec['name']} の対象を選んでください")
            free_powers.append(
                {
                    "power_id": power_spec["id"],
                    "name": power_spec["name"],
                    "rating": int(power.get("rating") or 1),
                    "extra": bound_extra,
                    "source": spec["name"],
                }
            )
    state.mentor_choices = selected
    public_choices = []
    for choice in allowed:
        extras = []
        for power in choice.get("powers") or []:
            power_spec = _power_by_name(power["name"])
            if power_spec:
                extras = power_select_options(power_spec, skills_data)
        public_choices.append(
            {
                "name": choice["name"],
                "set": choice.get("set") or "",
                "audience": choice.get("audience") or "all",
                "selected": choice["name"] in selected,
                "extra": (state.mentor_extras or {}).get(choice["name"], ""),
                "extra_options": extras,
            }
        )
    public = {
        "id": spec["id"],
        "name": spec["name"],
        "advantage": spec.get("advantage") or "",
        "disadvantage": spec.get("disadvantage") or "",
        "source": spec.get("source"),
        "choices": public_choices,
    }
    return {
        "warnings": warnings,
        "errors": errors,
        "bonus_sources": bonus_sources,
        "free_powers": free_powers,
        "public": public,
    }


def resolve_qi_foci(
    state: CharacterState,
    talent_name: str,
    mag: int,
    skills_data: dict[str, Any],
    focus_binding: list[dict[str, Any]],
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    public: list[dict[str, Any]] = []
    free_powers: list[dict[str, Any]] = []
    nuyen = 0
    karma = 0
    if talent_name not in ADEPT_TALENTS:
        state.qi_foci = []
        return {
            "warnings": warnings,
            "errors": errors,
            "public": public,
            "free_powers": free_powers,
            "nuyen": 0,
            "karma": 0,
        }
    gear = catalog().get("qi_focus") or {"maxrating": 6, "cost": "Rating * 3000"}
    max_force = int(gear.get("maxrating") or 6)
    kept: list[QiFocusInstall] = []
    for inst in state.qi_foci:
        spec = _power_by_id(inst.power_id)
        if not spec:
            continue
        cap = power_max_rating(spec, mag)
        power_rating = 1 if not spec.get("levels") else max(1, min(cap, int(inst.power_rating or 1)))
        extra = (inst.extra or "").strip()
        options = power_select_options(spec, skills_data)
        kind = spec.get("select")
        if kind and extra and extra not in options:
            warnings.append(f"気焦点の {spec['name']} の指定が無効です（{extra}）")
            extra = ""
            inst.extra = None
        if kind and not extra:
            warnings.append(f"気焦点の {spec['name']} の対象を選んでください")
        needed = max(1, _ceil_div(power_point_cost(spec, power_rating) / 0.25))
        force = max(needed, min(max_force, int(inst.rating or needed)))
        inst.rating = force
        inst.power_rating = power_rating
        label = spec["name"] + (f" ({extra})" if extra else "")
        bind = force
        for mod in focus_binding:
            if (mod.get("name") or "") != QI_FOCUS_NAME:
                continue
            contains = (mod.get("extracontains") or "").strip()
            if contains and contains not in {label, spec["name"]}:
                continue
            bind += int(mod.get("val") or 0)
        bind = max(0, bind)
        cost = force * 3000
        nuyen += cost
        karma += bind
        free_powers.append(
            {
                "power_id": spec["id"],
                "name": spec["name"],
                "rating": power_rating,
                "extra": extra,
                "source": f"Qi Focus F{force}",
            }
        )
        public.append(
            {
                "id": inst.id,
                "rating": force,
                "rating_min": needed,
                "rating_max": max_force,
                "power_id": spec["id"],
                "name": spec["name"],
                "power_rating": power_rating,
                "power_rating_max": cap,
                "extra": extra,
                "select": kind,
                "options": options,
                "nuyen": cost,
                "karma": bind,
                "source": gear.get("source"),
            }
        )
        kept.append(inst)
    state.qi_foci = kept
    return {
        "warnings": warnings,
        "errors": errors,
        "public": public,
        "free_powers": free_powers,
        "nuyen": nuyen,
        "karma": karma,
    }


def resolve_foci(
    state: CharacterState,
    talent_name: str,
    mag: int,
    focus_binding: list[dict[str, Any]],
) -> dict[str, Any]:
    warnings: list[str] = []
    public: list[dict[str, Any]] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    nuyen = 0
    karma = 0
    if talent_name not in FOCUS_TALENTS:
        state.foci = []
        return {
            "warnings": warnings,
            "public": public,
            "bonus_sources": bonus_sources,
            "nuyen": 0,
            "karma": 0,
        }
    kept: list[FocusInstall] = []
    max_force = max(1, int(mag or 0))
    for inst in state.foci:
        spec = _focus_by_id(inst.gear_id)
        if not spec:
            continue
        cap = min(int(spec.get("maxrating") or 6), max_force) if mag else 0
        if cap <= 0:
            warnings.append(f"{spec['name']} を結合するには魔力が必要です")
            continue
        force = max(1, min(cap, int(inst.force or 1)))
        inst.force = force
        crafted = bool(inst.crafted)
        formula_bought = bool(inst.formula_bought) if crafted else False
        inst.crafted = crafted
        inst.formula_bought = formula_bought
        extra = (inst.extra or "").strip()
        needs_weapon = bool(spec.get("needs_weapon"))
        weapon_type = str(spec.get("weapon_type") or "")
        if needs_weapon:
            inst.extra = extra or None
        else:
            inst.extra = None
            extra = ""
        formula = spec.get("formula") or {}
        if crafted:
            reagent = force * SPIRIT_REAGENT_YEN
            formula_cost = int(eval_formula(str(formula.get("cost") or "0"), force, 0)) if formula_bought else 0
            if formula_bought and not formula:
                warnings.append(f"{spec['name']} の術式データが見つからないため、術式代は0¥にしました")
            cost = formula_cost + reagent
        else:
            cost = int(eval_formula(str(spec.get("cost") or "0"), force, 0))
            formula_cost = 0
            reagent = 0
        bind = focus_bind_karma(spec["name"], force, focus_binding)
        nuyen += cost
        karma += bind
        nodes = [
            node
            for node in substitute_rating(list(spec.get("bonus") or []), force)
            if node.get("tag") != "weaponspecificdice"
        ]
        label = f"{spec['name']} F{force}"
        bonus_sources.append((label, nodes))
        public.append(
            {
                "id": inst.id,
                "gear_id": spec["id"],
                "name": spec["name"],
                "force": force,
                "force_max": cap,
                "nuyen": cost,
                "karma": bind,
                "crafted": crafted,
                "formula_bought": formula_bought,
                "formula_nuyen": formula_cost,
                "reagent_nuyen": reagent,
                "retail_nuyen": int(eval_formula(str(spec.get("cost") or "0"), force, 0)),
                "hits": inst.hits,
                "opposed_hits": inst.opposed_hits,
                "effect": spec.get("effect") or "",
                "avail": spec.get("avail") or "",
                "needs_weapon": needs_weapon,
                "weapon_type": weapon_type,
                "weapon_id": extra if needs_weapon else "",
                "weapon_name": "",
                "weapon_dice": force if needs_weapon else 0,
                "weapon_options": [],
                "formula": (
                    {
                        "id": formula.get("id"),
                        "name": formula.get("name"),
                        "cost": formula.get("cost") or "",
                    }
                    if formula
                    else None
                ),
                "source": spec.get("source"),
                "page": spec.get("page"),
            }
        )
        kept.append(inst)
    state.foci = kept
    return {
        "warnings": warnings,
        "public": public,
        "bonus_sources": bonus_sources,
        "nuyen": nuyen,
        "karma": karma,
    }


def attach_weapon_focus_dice(
    state: CharacterState,
    foci_public: list[dict[str, Any]],
    weapons: list[dict[str, Any]],
    warnings: list[str],
) -> None:
    by_id = {str(item.get("id") or ""): item for item in weapons if item.get("id")}
    for focus in foci_public:
        if not focus.get("needs_weapon"):
            continue
        weapon_type = str(focus.get("weapon_type") or "Melee")
        options = [
            {"id": str(item["id"]), "name": str(item.get("name") or "")}
            for item in weapons
            if str(item.get("type") or "") == weapon_type
        ]
        focus["weapon_options"] = options
        allowed = {opt["id"] for opt in options}
        weapon_id = str(focus.get("weapon_id") or "").strip()
        dice = int(focus.get("weapon_dice") or 0)
        if not weapon_id:
            warnings.append(f"{focus.get('name') or 'Weapon Focus'} の対象武器を選んでください")
            focus["weapon_id"] = ""
            focus["weapon_name"] = ""
            continue
        if weapon_id not in allowed:
            warnings.append(f"{focus.get('name') or 'Weapon Focus'} は{weapon_type}武器専用です")
            focus["weapon_id"] = ""
            focus["weapon_name"] = ""
            for inst in state.foci or []:
                if inst.id == focus.get("id"):
                    inst.extra = None
            continue
        weapon = by_id[weapon_id]
        focus["weapon_id"] = weapon_id
        focus["weapon_name"] = str(weapon.get("name") or "")
        weapon["focus_dice"] = int(weapon.get("focus_dice") or 0) + dice


def apply_focus_limits(
    mag: int,
    qi_public: list[dict[str, Any]],
    foci_public: list[dict[str, Any]],
    errors: list[str],
) -> dict[str, int]:
    count = len(qi_public) + len(foci_public)
    force = sum(int(item.get("rating") or item.get("force") or 0) for item in qi_public + foci_public)
    count_max = max(0, int(mag or 0))
    force_max = count_max * FOCUS_FORCE_MULT
    if count_max and count > count_max:
        errors.append(f"結合できるフォーカスは魔力までです（{count}/{count_max}）")
    if force_max and force > force_max:
        errors.append(f"結合フォーカスのForce合計が上限を超えています（{force}/{force_max}）")
    return {"count": count, "count_max": count_max, "force": force, "force_max": force_max}


def resolve_spirits(
    state: CharacterState,
    talent_name: str,
    mag: int,
    tradition: dict[str, Any] | None,
) -> dict[str, Any]:
    warnings: list[str] = []
    public: list[dict[str, Any]] = []
    nuyen = 0
    if talent_name not in SPIRIT_TALENTS:
        state.spirits = []
        return {"warnings": warnings, "public": public, "nuyen": 0}
    allowed = {name: role for role, name in (tradition.get("spirits") or {}).items()} if tradition else {}
    if not tradition:
        warnings.append("精霊を召喚するには伝統を選んでください")
    kept: list[SpiritInstall] = []
    mag = max(0, int(mag or 0))
    for inst in state.spirits:
        spec = _spirit_by_id(inst.spirit_id)
        if not spec:
            continue
        role = allowed.get(spec["name"])
        if not tradition or not role:
            warnings.append(f"{spec['name']} はこの伝統では召喚できません")
            continue
        if mag <= 0:
            warnings.append(f"{spec['name']} を召喚するには魔力が必要です")
            continue
        bound = bool(inst.bound)
        inst.bound = bound
        cap = mag if bound else max(1, mag * 2)
        force = max(1, min(cap, int(inst.force or 1)))
        inst.force = force
        if inst.hits is not None and inst.opposed_hits is not None:
            services = max(0, int(inst.hits) - int(inst.opposed_hits))
        elif bound:
            services = max(1, min(mag, int(inst.services or 1)))
        else:
            services = max(0, int(inst.services or 0))
        inst.services = services
        cost = force * SPIRIT_REAGENT_YEN if bound else 0
        nuyen += cost
        if bound is False and inst.hits is not None and inst.opposed_hits is not None and services <= 0:
            warnings.append(f"{spec['name']} の召喚に失敗しています（正味0）")
        attrs = spirit_attributes(spec, force)
        kept.append(inst)
        public.append(
            {
                "id": inst.id,
                "spirit_id": spec["id"],
                "name": spec["name"],
                "role": role,
                "role_label": SPIRIT_ROLE_LABELS.get(role, role),
                "force": force,
                "force_max": cap,
                "services": services,
                "nuyen": cost,
                "bound": bound,
                "hits": inst.hits,
                "opposed_hits": inst.opposed_hits,
                "attributes": attrs,
                "powers": list(spec.get("powers") or []),
                "optionalpowers": list(spec.get("optionalpowers") or []),
                "skills": [
                    {"name": row["name"], "attribute": row.get("attribute") or "", "rating": force}
                    for row in (spec.get("skills") or [])
                ],
                "weaknesses": list(spec.get("weaknesses") or []),
                "source": spec.get("source"),
                "page": spec.get("page"),
            }
        )
    state.spirits = kept
    return {"warnings": warnings, "public": public, "nuyen": nuyen}


def _required_names(spec: dict[str, Any]) -> list[str]:
    return [name for names in (spec.get("required") or {}).values() for name in names]


def resolve_complex_forms(
    state: CharacterState,
    talent_name: str,
    res: int,
    attrs: dict[str, int],
    quality_names: set[str],
) -> dict[str, Any]:
    warnings: list[str] = []
    public: list[dict[str, Any]] = []
    stream = _stream_by_id(state.stream_id) or (_default_stream() if talent_name in COMPLEX_FORM_TALENTS else None)
    if talent_name in COMPLEX_FORM_TALENTS and stream:
        state.stream_id = stream["id"]
    resist, resist_attrs = tradition_resist(stream, attrs)
    if talent_name not in COMPLEX_FORM_TALENTS:
        state.complex_forms = []
        if talent_name not in RES_TALENTS:
            state.stream_id = None
        return {
            "warnings": warnings,
            "public": public,
            "free_max": 0,
            "used": 0,
            "paid": 0,
            "karma": 0,
            "stream": None,
            "resist": resist,
            "resist_attrs": resist_attrs,
        }
    talent = resolve_talent(state.priorities.Talent, talent_name)
    free_max = int(talent.get("cfp") or 0)
    seen: set[str] = set()
    kept: list[ComplexFormInstall] = []
    res = max(0, int(res or 0))
    for inst in state.complex_forms:
        spec = _complex_form_by_id(inst.form_id)
        if not spec:
            continue
        if spec["id"] in seen:
            warnings.append(f"{spec['name']} は重複しているため外しました")
            continue
        missing = [name for name in _required_names(spec) if name not in quality_names]
        if missing:
            warnings.append(f"{spec['name']} には {' / '.join(missing)} が必要です")
            continue
        extra = (inst.extra or "").strip()
        if spec.get("needs_extra") and extra not in MATRIX_ATTRIBUTES:
            warnings.append(f"{spec['name']} はマトリクス属性を選んでください")
            extra = extra if extra in MATRIX_ATTRIBUTES else ""
            inst.extra = extra or None
        seen.add(spec["id"])
        level_max = max(1, res * 2) if res else 1
        chosen = int(inst.level) if inst.level else (res or 1)
        chosen = max(1, min(level_max, chosen))
        inst.level = chosen
        fade = spell_drain_value(str(spec.get("fv") or ""), chosen)
        physical = bool(res) and chosen > res
        free = len(kept) < free_max
        kept.append(inst)
        label = spec["name"]
        if extra:
            label = spec["name"].replace("[Matrix Attribute]", extra)
        public.append(
            {
                "id": inst.id,
                "form_id": spec["id"],
                "name": spec["name"],
                "label": label,
                "target": spec.get("target") or "",
                "duration": spec.get("duration") or "",
                "fv": spec.get("fv") or "",
                "extra": extra,
                "needs_extra": bool(spec.get("needs_extra")),
                "options": list(MATRIX_ATTRIBUTES) if spec.get("needs_extra") else [],
                "level": chosen,
                "level_min": 1,
                "level_max": level_max,
                "fade": fade,
                "fade_code": None if fade is None else ("P" if physical else "S"),
                "physical": physical,
                "resist": int(resist),
                "resist_attrs": resist_attrs,
                "free": free,
                "karma": 0 if free else COMPLEX_FORM_KARMA,
                "source": spec.get("source"),
                "page": spec.get("page"),
            }
        )
    state.complex_forms = kept
    paid = max(0, len(public) - free_max)
    return {
        "warnings": warnings,
        "public": public,
        "free_max": free_max,
        "used": len(public),
        "paid": paid,
        "karma": paid * COMPLEX_FORM_KARMA,
        "stream": (
            {
                "id": stream["id"],
                "name": stream["name"],
                "drain": stream.get("drain") or "",
                "drain_attrs": list(stream.get("drain_attrs") or []),
                "sprites": list(stream.get("sprites") or []),
                "source": stream.get("source"),
                "page": stream.get("page"),
            }
            if stream
            else None
        ),
        "resist": resist,
        "resist_attrs": resist_attrs,
    }


def resolve_sprites(
    state: CharacterState,
    talent_name: str,
    res: int,
    stream: dict[str, Any] | None,
) -> dict[str, Any]:
    warnings: list[str] = []
    public: list[dict[str, Any]] = []
    errors: list[str] = []
    if talent_name not in SPRITE_TALENTS:
        state.sprites = []
        return {"warnings": warnings, "errors": errors, "public": public}
    allowed = set(stream.get("sprites") or []) if stream else set()
    kept: list[SpriteInstall] = []
    res = max(0, int(res or 0))
    registered_count = 0
    for inst in state.sprites:
        spec = _sprite_by_id(inst.sprite_id)
        if not spec:
            continue
        if allowed and spec["name"] not in allowed:
            warnings.append(f"{spec['name']} はこのストリームではコンパイルできません")
            continue
        if res <= 0:
            warnings.append(f"{spec['name']} をコンパイルするには共振力が必要です")
            continue
        registered = bool(inst.registered)
        inst.registered = registered
        cap = res if registered else max(1, res * 2)
        level = max(1, min(cap, int(inst.level or 1)))
        inst.level = level
        if inst.hits is not None and inst.opposed_hits is not None:
            services = max(0, int(inst.hits) - int(inst.opposed_hits))
        elif registered:
            services = max(1, min(res, int(inst.services or 1)))
        else:
            services = max(0, int(inst.services or 0))
        inst.services = services
        if registered:
            registered_count += 1
        if registered is False and inst.hits is not None and inst.opposed_hits is not None and services <= 0:
            warnings.append(f"{spec['name']} のコンパイルに失敗しています（正味0）")
        stats = sprite_attributes(spec, level)
        kept.append(inst)
        public.append(
            {
                "id": inst.id,
                "sprite_id": spec["id"],
                "name": spec["name"],
                "level": level,
                "level_max": cap,
                "services": services,
                "registered": registered,
                "hits": inst.hits,
                "opposed_hits": inst.opposed_hits,
                "attributes": stats["attributes"],
                "matrix": stats["matrix"],
                "powers": list(spec.get("powers") or []),
                "skills": [
                    {"name": row["name"], "attribute": row.get("attribute") or "", "rating": level}
                    for row in (spec.get("skills") or [])
                ],
                "source": spec.get("source"),
                "page": spec.get("page"),
            }
        )
    state.sprites = kept
    if registered_count > res:
        errors.append(f"登録できるスプライトは共振力までです（{registered_count}/{res}）")
    return {"warnings": warnings, "errors": errors, "public": public}


def attach_complex_form_tests(
    public: list[dict[str, Any]],
    res: int,
    skill_totals: dict[str, int],
    skill_bonus: dict[str, int],
    attrs: dict[str, int],
    skills_data: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    for item in public:
        level = int(item.get("level") or 1)
        dice = skill_dice_pool("Software", skill_totals, skill_bonus, attrs, skills_data, attr_override="RES")
        item["test"] = {
            **dice,
            "force": level,
            "limit": level,
            "limit_name": "Level",
            "vs": 0,
            "drain": item.get("fade"),
            "drain_code": item.get("fade_code"),
            "physical": bool(item.get("physical")),
        }
        if dice.get("missing"):
            warnings.append(f"{item['label'] or item['name']} のスレッディングにはSoftwareが必要です（未習得・デフォルト不可）")
    return warnings


def attach_sprite_tests(
    public: list[dict[str, Any]],
    res: int,
    skill_totals: dict[str, int],
    skill_bonus: dict[str, int],
    attrs: dict[str, int],
    skills_data: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    for item in public:
        registered = bool(item.get("registered"))
        level = int(item.get("level") or 1)
        skill = "Registering" if registered else "Compiling"
        test = magic_opposed_test(
            skill,
            level,
            level * 2,
            res,
            skill_totals,
            skill_bonus,
            attrs,
            item.get("hits"),
            item.get("opposed_hits"),
            limit_name="Level",
            days=level if registered else None,
            skills_data=skills_data,
        )
        item["test"] = test
        if test.get("missing"):
            warnings.append(f"{item['name']} の{('登録' if registered else 'コンパイル')}判定に{skill}が必要です（未習得・デフォルト不可）")
    return warnings


def living_persona(
    attrs: dict[str, int],
    res: int,
    persona_bonus: dict[str, int] | None = None,
    matrix_initiative_dice: int = 0,
) -> dict[str, int]:
    bonus = persona_bonus or {}
    return {
        "device_rating": int(res),
        "attack": int(attrs.get("CHA") or 0) + int(bonus.get("attack") or 0),
        "sleaze": int(attrs.get("INT") or 0) + int(bonus.get("sleaze") or 0),
        "dataprocessing": int(attrs.get("LOG") or 0) + int(bonus.get("dataprocessing") or 0),
        "firewall": int(attrs.get("WIL") or 0) + int(bonus.get("firewall") or 0),
        "matrix_initiative_dice": max(0, int(matrix_initiative_dice or 0)),
    }


def attach_spirit_tests(
    public: list[dict[str, Any]],
    mag: int,
    skill_totals: dict[str, int],
    skill_bonus: dict[str, int],
    attrs: dict[str, int],
    skills_data: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    for item in public:
        bound = bool(item.get("bound"))
        force = int(item.get("force") or 1)
        skill = "Binding" if bound else "Summoning"
        vs = force * 2 if bound else force
        test = magic_opposed_test(
            skill,
            force,
            vs,
            mag,
            skill_totals,
            skill_bonus,
            attrs,
            item.get("hits"),
            item.get("opposed_hits"),
            skills_data=skills_data,
        )
        item["test"] = test
        if test.get("missing"):
            warnings.append(f"{item['name']} の{('結合' if bound else '召喚')}判定に{skill}が必要です（未習得・デフォルト不可）")
    return warnings


def attach_focus_tests(
    public: list[dict[str, Any]],
    mag: int,
    skill_totals: dict[str, int],
    skill_bonus: dict[str, int],
    attrs: dict[str, int],
    skills_data: dict[str, Any],
    mental_limit: int,
) -> list[str]:
    warnings: list[str] = []
    for item in public:
        if not item.get("crafted"):
            continue
        force = int(item.get("force") or 1)
        bonus = dict(skill_bonus)
        if "MAG skills" in (item.get("effect") or ""):
            bonus["Artificing"] = int(bonus.get("Artificing") or 0) - force
        test = magic_opposed_test(
            "Artificing",
            force,
            force * 2,
            mag,
            skill_totals,
            bonus,
            attrs,
            item.get("hits"),
            item.get("opposed_hits"),
            days=force,
            skills_data=skills_data,
        )
        item["test"] = test
        if test.get("missing"):
            warnings.append(f"{item['name']} の作成にはArtificingが必要です（未習得・デフォルト不可）")
        if test.get("net") is not None and int(test["net"]) <= 0:
            warnings.append(f"{item['name']} の作成に失敗しています（正味0）")
        if item.get("formula_bought"):
            continue
        design = magic_opposed_test(
            "Arcana",
            force,
            force * 2,
            mag,
            skill_totals,
            skill_bonus,
            attrs,
            limit=mental_limit,
            limit_name="Mental",
            days=force,
            skills_data=skills_data,
        )
        item["formula_test"] = design
        if design.get("missing"):
            warnings.append(f"{item['name']} の術式自作にはArcanaが必要です（未習得・デフォルト不可）")
    return warnings


def resolve_enhancements(
    state: CharacterState,
    talent_name: str,
    quality_names: set[str],
    power_names: set[str],
) -> dict[str, Any]:
    warnings: list[str] = []
    public: list[dict[str, Any]] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    kept: list[str] = []
    if talent_name not in ADEPT_TALENTS:
        state.adept_enhancements = []
        return {"warnings": warnings, "public": public, "bonus_sources": bonus_sources, "karma": 0}
    for eid in state.adept_enhancements:
        spec = _enhancement_by_id(eid)
        if not spec:
            continue
        req = spec.get("required") or {}
        missing_quality = [name for name in (req.get("quality") or []) if name not in quality_names]
        missing_power = [name for name in (req.get("power") or []) if name not in power_names]
        if spec.get("power") and spec["power"] not in power_names and spec["power"] not in missing_power:
            missing_power.append(spec["power"])
        if missing_quality:
            warnings.append(f"{spec['name']} は {' / '.join(missing_quality)} が外れたため削除しました")
            continue
        missing = missing_power
        if missing:
            warnings.append(f"{spec['name']} には {' / '.join(missing)} が必要です")
        kept.append(spec["id"])
        bonus_sources.append((spec["name"], spec.get("bonus") or []))
        public.append(
            {
                "id": spec["id"],
                "name": spec["name"],
                "power": spec.get("power"),
                "karma": ENHANCEMENT_KARMA,
                "source": spec.get("source"),
                "page": spec.get("page"),
                "ok": not missing,
            }
        )
    state.adept_enhancements = kept
    return {
        "warnings": warnings,
        "public": public,
        "bonus_sources": bonus_sources,
        "karma": ENHANCEMENT_KARMA * len(kept),
    }


def resolve_adept_powers(
    state: CharacterState,
    talent_name: str,
    mag: int,
    skills_data: dict[str, Any],
    quality_names: set[str],
    magicians_way: bool,
    free_powers: list[dict[str, Any]] | None = None,
    wil: int = 1,
    intuition: int = 1,
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    public: list[dict[str, Any]] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    spent = 0.0
    discount_used = 0.0
    if talent_name not in ADEPT_TALENTS:
        return {
            "warnings": warnings,
            "errors": errors,
            "public": public,
            "bonus_sources": bonus_sources,
            "spent": 0.0,
            "discount_used": 0.0,
            "discount_max": 0.0,
            "mystic_pp": 0,
            "power_names": set(),
        }

    free_by_key: dict[tuple[str, str], int] = {}
    free_notes: dict[tuple[str, str], list[str]] = {}
    for gift in free_powers or []:
        spec = _power_by_id(gift["power_id"]) or _power_by_name(gift.get("name") or "")
        if not spec:
            continue
        extra = (gift.get("extra") or "").strip()
        key = (spec["id"], extra)
        free_by_key[key] = free_by_key.get(key, 0) + max(1, int(gift.get("rating") or 1))
        free_notes.setdefault(key, []).append(gift.get("source") or "無料")

    installed_names = set()
    for inst in state.adept_powers:
        spec = _power_by_id(inst.power_id)
        if spec:
            installed_names.add(spec["name"])
    for key, rating in free_by_key.items():
        spec = _power_by_id(key[0])
        if spec:
            installed_names.add(spec["name"])

    seen_keys: set[tuple[str, str]] = set()
    cap_limit = way_discount_cap(mag)
    for inst in state.adept_powers:
        spec = _power_by_id(inst.power_id)
        if not spec:
            continue
        cap = power_max_rating(spec, mag)
        extra = (inst.extra or "").strip()
        key = (spec["id"], extra)
        free_levels = free_by_key.get(key, 0)
        paid_max = max(1, cap - free_levels) if spec.get("levels") else 1
        rating = 1 if not spec.get("levels") else max(1, min(paid_max, int(inst.rating or 1)))
        inst.rating = rating
        options = power_select_options(spec, skills_data)
        kind = spec.get("select")
        select_label = {"skill": "スキル", "attribute": "属性", "spell": "呪文"}.get(kind or "", "対象")
        if kind and extra and extra not in options:
            warnings.append(f"{spec['name']} の指定が無効です（{extra}）")
            extra = ""
            inst.extra = None
            key = (spec["id"], extra)
            free_levels = free_by_key.get(key, 0)
        if kind and not extra:
            warnings.append(f"{spec['name']} の{select_label}を選んでください")
        spell = spell_cast_info(extra, inst.force, mag, wil + intuition, "WIL+INT") if kind == "spell" and extra else None
        if spell:
            inst.force = int(spell["force"])
        if kind and extra and key in seen_keys:
            warnings.append(f"{spec['name']}（{extra}）が重複しています")
        seen_keys.add(key)
        for needed in spec.get("required") or []:
            if needed not in installed_names:
                warnings.append(f"{spec['name']} には {needed} が必要です")
        eligible = way_discount_eligible(spec, quality_names, magicians_way)
        discounted = bool(inst.discounted) and eligible
        if discounted and discount_used + float(spec.get("adeptway") or 0) > cap_limit + 1e-9:
            discounted = False
            warnings.append(f"{spec['name']} の Way 割引は上限（MAG/4）を超えるため無効です")
        inst.discounted = discounted
        if discounted:
            discount_used += float(spec.get("adeptway") or 0)
        full_cost = power_point_cost(spec, rating, False)
        cost = 0.0 if (not spec.get("levels") and free_levels) else power_point_cost(spec, rating, discounted)
        spent += cost
        total_rating = rating if not spec.get("levels") else min(cap, rating + free_levels)
        if not spec.get("levels") and free_levels:
            total_rating = 1
        bonus_sources.append((spec["name"], bind_power_bonus(spec.get("bonus") or [], extra, total_rating)))
        public.append(
            {
                "id": inst.id,
                "power_id": spec["id"],
                "name": spec["name"],
                "rating": rating,
                "total_rating": total_rating,
                "free_levels": free_levels,
                "rating_min": 1,
                "rating_max": paid_max,
                "extra": extra,
                "cost": cost,
                "full_cost": full_cost,
                "discounted": discounted,
                "can_discount": eligible,
                "select": kind,
                "options": options,
                "source": spec.get("source"),
                "page": spec.get("page"),
                "notes": list(free_notes.get(key) or []),
                "spell": spell,
            }
        )
        free_by_key.pop(key, None)

    for key, free_levels in free_by_key.items():
        spec = _power_by_id(key[0])
        if not spec:
            continue
        extra = key[1]
        cap = power_max_rating(spec, mag)
        total_rating = 1 if not spec.get("levels") else min(cap, free_levels)
        options = power_select_options(spec, skills_data)
        bonus_sources.append((spec["name"], bind_power_bonus(spec.get("bonus") or [], extra, total_rating)))
        public.append(
            {
                "id": f"free:{spec['id']}:{extra}",
                "power_id": spec["id"],
                "name": spec["name"],
                "rating": 0,
                "total_rating": total_rating,
                "free_levels": free_levels,
                "rating_min": 0,
                "rating_max": 0,
                "extra": extra,
                "cost": 0.0,
                "full_cost": 0.0,
                "discounted": False,
                "can_discount": False,
                "select": spec.get("select"),
                "options": options,
                "source": spec.get("source"),
                "page": spec.get("page"),
                "notes": list(free_notes.get(key) or []),
                "free_only": True,
            }
        )

    if discount_used > cap_limit + 1e-9:
        errors.append(f"Way割引が上限を超えています（使用 {discount_used:g} / 上限 {cap_limit:g}）")

    return {
        "warnings": warnings,
        "errors": errors,
        "public": public,
        "bonus_sources": bonus_sources,
        "spent": round(spent, 4),
        "discount_used": round(discount_used, 4),
        "discount_max": cap_limit,
        "mystic_pp": max(0, min(int(mag), int(state.mystic_pp or 0))) if talent_name == "Mystic Adept" else 0,
        "power_names": installed_names,
    }


def _clamp_ware_grades(kind: str, items: list[CyberwareInstall]) -> list[str]:
    warnings: list[str] = []
    for inst in items:
        ware = _ware_by_id(kind, inst.ware_id)
        if not ware:
            continue
        force = ware.get("forcegrade")
        if force:
            inst.grade = force
            continue
        grade = inst.grade or "Standard"
        banned = set(ware.get("bannedgrades") or [])
        if grade in banned:
            warnings.append(f"{ware['name']} は {grade} グレードを使えません（Standard に変更）")
            inst.grade = "Standard"
    return warnings


def _installed_ware_names(kind: str, items: list[CyberwareInstall]) -> set[str]:
    names: set[str] = set()
    for inst in items:
        ware = _ware_by_id(kind, inst.ware_id)
        if ware:
            names.add(ware["name"])
    return names


def _required_warnings(
    kind: str,
    items: list[CyberwareInstall],
    names: dict[str, set[str]],
    metatype: str,
    metavariant: str | None,
) -> list[str]:
    warnings: list[str] = []
    have_meta = {metatype}
    if metavariant:
        have_meta.add(metavariant)
    for inst in items:
        ware = _ware_by_id(kind, inst.ware_id)
        if not ware:
            continue
        req = ware.get("required") or {}
        for other in ("bioware", "cyberware"):
            needed = req.get(other) or []
            if needed and not any(name in names.get(other, set()) for name in needed):
                label = needed[0] if len(needed) == 1 else " / ".join(needed)
                warnings.append(f"{ware['name']} には {label} が必要です")
        needed_meta = req.get("metatype") or []
        if needed_meta and not any(name in have_meta for name in needed_meta):
            warnings.append(f"{ware['name']} は {' / '.join(needed_meta)} 専用です")
    return warnings


def resolve_spells(
    state: CharacterState,
    talent: dict[str, Any],
    mag: int,
    attrs: dict[str, int],
    owned_magic_names: set[str] | None = None,
) -> dict[str, Any]:
    warnings: list[str] = []
    public: list[dict[str, Any]] = []
    owned = set(owned_magic_names or [])
    tradition = _tradition_by_id(state.tradition_id)
    if state.tradition_id and not tradition:
        warnings.append("選んだ伝統が見つからないため外しました")
        state.tradition_id = None
    resist, resist_attrs = tradition_resist(tradition, attrs)
    if talent["name"] not in SPELL_TALENTS:
        state.spells = []
        if talent["name"] not in MAG_TALENTS:
            state.tradition_id = None
        return {
            "warnings": warnings,
            "public": public,
            "free_max": 0,
            "used": 0,
            "paid": 0,
            "karma": 0,
            "tradition": None,
            "resist": resist,
            "resist_attrs": resist_attrs,
        }

    if not tradition:
        warnings.append("伝統を選んでください")
    free_max = int(talent.get("spells") or 0)
    seen: set[str] = set()
    kept: list[SpellInstall] = []
    for inst in state.spells:
        spec = _spell_by_id(inst.spell_id)
        if not spec:
            continue
        if spec.get("category") not in SPELL_CATEGORIES:
            warnings.append(f"{spec['name']} はこの段階では扱えません")
            continue
        if spec["id"] in seen:
            warnings.append(f"{spec['name']} は重複しているため外しました")
            continue
        seen.add(spec["id"])
        kind = spec.get("kind") or "spell"
        has_force = kind != "enchantment"
        info = spell_cast_info(spec["name"], inst.force if has_force else None, mag, resist, resist_attrs)
        if info and has_force:
            inst.force = int(info["force"])
        missing = [
            name
            for names in (spec.get("required") or {}).values()
            for name in names
            if name and name not in owned
        ]
        if missing:
            warnings.append(f"{spec['name']} には {' / '.join(missing)} が必要です")
        free = len(kept) < free_max
        kept.append(inst)
        public.append(
            {
                "id": inst.id,
                "spell_id": spec["id"],
                "name": spec["name"],
                "category": spec.get("category"),
                "kind": kind,
                "useskill": spec.get("useskill") or "Spellcasting",
                "has_force": has_force,
                "type": spec.get("type"),
                "range": spec.get("range"),
                "duration": spec.get("duration"),
                "descriptor": spec.get("descriptor"),
                "dv": spec.get("dv") or "",
                "required": missing,
                "source": spec.get("source"),
                "page": spec.get("page"),
                "free": free,
                "karma": 0 if free else SPELL_KARMA,
                "spell": info if has_force else None,
            }
        )
    state.spells = kept
    paid = max(0, len(public) - free_max)
    return {
        "warnings": warnings,
        "public": public,
        "free_max": free_max,
        "used": len(public),
        "paid": paid,
        "karma": paid * SPELL_KARMA,
        "tradition": _tradition_public(tradition),
        "resist": resist,
        "resist_attrs": resist_attrs,
    }


def initiation_karma_for_grade(grade: int) -> int:
    return INITIATION_KARMA_FLAT + int(grade) * INITIATION_KARMA_PER_GRADE


def initiation_karma_total(grade: int) -> int:
    return sum(initiation_karma_for_grade(g) for g in range(1, max(0, int(grade)) + 1))


def _metamagic_by_id(mid: str) -> dict[str, Any] | None:
    for item in catalog().get("metamagics") or []:
        if item["id"] == mid:
            return item
    return None


def _magic_art_by_id(art_id: str) -> dict[str, Any] | None:
    for item in catalog().get("magic_arts") or []:
        if item["id"] == art_id:
            return item
    return None


def resolve_initiation(
    state: CharacterState,
    talent_name: str,
    mag: int,
    quality_names: set[str],
    errors: list[str],
) -> dict[str, Any]:
    warnings: list[str] = []
    empty = {
        "warnings": warnings,
        "grade": 0,
        "karma": 0,
        "choices": [],
        "metamagics": [],
        "arts": [],
        "art_names": set(),
        "metamagic_names": set(),
        "bonus_sources": [],
        "mag_max_bonus": 0,
    }
    if talent_name not in MAG_TALENTS:
        state.initiate_grade = 0
        state.initiations = []
        return empty

    can_adept = talent_name in {"Adept", "Mystic Adept"}
    can_magician = talent_name in MAG_TALENTS and talent_name != "Adept"
    grade = max(0, int(state.initiate_grade or 0))
    by_grade: dict[int, InitiationChoice] = {}
    for inst in state.initiations or []:
        g = int(inst.grade or 0)
        if g >= 1:
            by_grade[g] = InitiationChoice(
                id=inst.id,
                grade=g,
                kind=inst.kind or "metamagic",
                option_id=inst.option_id or "",
            )

    kept_choices: list[InitiationChoice] = []
    for g in range(1, grade + 1):
        choice = by_grade.get(g) or InitiationChoice(grade=g, kind="metamagic", option_id="")
        choice.grade = g
        kept_choices.append(choice)
    state.initiate_grade = grade
    state.initiations = kept_choices

    art_names: set[str] = set()
    metamagic_names: set[str] = set()
    public_choices: list[dict[str, Any]] = []
    public_metas: list[dict[str, Any]] = []
    public_arts: list[dict[str, Any]] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    seen_meta: set[str] = set()
    seen_art: set[str] = set()

    for choice in kept_choices:
        g = choice.grade
        kind = "art" if choice.kind == "art" else "metamagic"
        choice.kind = kind
        option_id = (choice.option_id or "").strip()
        row = {
            "id": choice.id,
            "grade": g,
            "kind": kind,
            "option_id": option_id,
            "name": "",
            "karma": initiation_karma_for_grade(g),
            "source": "",
            "page": "",
        }
        if not option_id:
            warnings.append(f"イニシエーション等級 {g} の Art／メタマジックを選んでください")
            public_choices.append(row)
            continue

        if kind == "art":
            spec = _magic_art_by_id(option_id)
            if not spec:
                warnings.append(f"未知の Art を等級 {g} から外しました")
                choice.option_id = ""
                row["option_id"] = ""
                public_choices.append(row)
                continue
            if spec["name"] in seen_art:
                warnings.append(f"{spec['name']} は重複しているため外しました")
                choice.option_id = ""
                row["option_id"] = ""
                public_choices.append(row)
                continue
            seen_art.add(spec["name"])
            art_names.add(spec["name"])
            public_arts.append(
                {
                    "id": choice.id,
                    "art_id": spec["id"],
                    "name": spec["name"],
                    "grade": g,
                    "source": spec.get("source") or "",
                    "page": spec.get("page") or "",
                }
            )
            if spec.get("bonus"):
                bonus_sources.append((spec["name"], list(spec.get("bonus") or [])))
            row.update(
                {
                    "option_id": spec["id"],
                    "name": spec["name"],
                    "source": spec.get("source") or "",
                    "page": spec.get("page") or "",
                }
            )
            public_choices.append(row)
            continue

        spec = _metamagic_by_id(option_id)
        if not spec:
            warnings.append(f"未知のメタマジックを等級 {g} から外しました")
            choice.option_id = ""
            row["option_id"] = ""
            public_choices.append(row)
            continue
        if not spec.get("repeatable") and spec["name"] in seen_meta:
            warnings.append(f"{spec['name']} は重複しているため外しました")
            choice.option_id = ""
            row["option_id"] = ""
            public_choices.append(row)
            continue
        if can_adept and not can_magician and not spec.get("adept"):
            warnings.append(f"{spec['name']} はアデプト向けではありません")
            choice.option_id = ""
            row["option_id"] = ""
            public_choices.append(row)
            continue
        if can_magician and not can_adept and not spec.get("magician"):
            warnings.append(f"{spec['name']} は魔術師向けではありません")
            choice.option_id = ""
            row["option_id"] = ""
            public_choices.append(row)
            continue

        ctx = {
            "qualities": set(quality_names) | {talent_name},
            "arts": set(art_names),
            "metamagics": set(metamagic_names),
            "powers": set(),
            "metatypes": set(),
            "metatype_categories": set(),
            "magenabled": True,
            "resenabled": False,
            "cyberware": set(),
            "bioware": set(),
            "spells": set(),
            "tradition": "",
            "skills": {},
            "knowledge": {},
            "essence": 6.0,
            "ess_lost": 0.0,
        }
        if spec.get("required_tree") and not requirement_tree_met(spec.get("required_tree"), ctx):
            needed = [name for names in (spec.get("required") or {}).values() for name in names]
            label = " / ".join(needed) if needed else "前提"
            warnings.append(f"{spec['name']} には {label} が必要です")

        seen_meta.add(spec["name"])
        metamagic_names.add(spec["name"])
        public_metas.append(
            {
                "id": choice.id,
                "metamagic_id": spec["id"],
                "name": spec["name"],
                "grade": g,
                "adept": bool(spec.get("adept")),
                "magician": bool(spec.get("magician")),
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
        if spec.get("bonus"):
            bonus_sources.append((spec["name"], list(spec.get("bonus") or [])))
        row.update(
            {
                "option_id": spec["id"],
                "name": spec["name"],
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
        public_choices.append(row)

    if grade > 0 and mag <= 0:
        errors.append("イニシエーションには魔力が必要です")
    elif grade > mag:
        errors.append(f"イニシエーション等級は魔力以下です（等級 {grade} / MAG {mag}）")

    return {
        "warnings": warnings,
        "grade": grade,
        "karma": initiation_karma_total(grade),
        "choices": public_choices,
        "metamagics": public_metas,
        "arts": public_arts,
        "art_names": art_names,
        "metamagic_names": metamagic_names,
        "bonus_sources": bonus_sources,
        "mag_max_bonus": grade,
    }


def submersion_karma_for_grade(grade: int) -> int:
    return SUBMERSION_KARMA_FLAT + int(grade) * SUBMERSION_KARMA_PER_GRADE


def submersion_karma_total(grade: int) -> int:
    return sum(submersion_karma_for_grade(g) for g in range(1, max(0, int(grade)) + 1))


def _echo_by_id(echo_id: str) -> dict[str, Any] | None:
    for item in catalog().get("echoes") or []:
        if item["id"] == echo_id:
            return item
    return None


def resolve_submersion(
    state: CharacterState,
    talent_name: str,
    res: int,
    quality_names: set[str],
    errors: list[str],
) -> dict[str, Any]:
    warnings: list[str] = []
    empty = {
        "warnings": warnings,
        "grade": 0,
        "karma": 0,
        "choices": [],
        "echoes": [],
        "echo_names": [],
        "bonus_sources": [],
        "res_max_bonus": 0,
    }
    if talent_name not in RES_TALENTS:
        state.submersion_grade = 0
        state.submersions = []
        return empty

    grade = max(0, int(state.submersion_grade or 0))
    by_grade: dict[int, SubmersionChoice] = {}
    for inst in state.submersions or []:
        g = int(inst.grade or 0)
        if g >= 1:
            by_grade[g] = SubmersionChoice(
                id=inst.id,
                grade=g,
                echo_id=inst.echo_id or "",
                extra=inst.extra,
            )

    kept_choices: list[SubmersionChoice] = []
    for g in range(1, grade + 1):
        choice = by_grade.get(g) or SubmersionChoice(grade=g, echo_id="")
        choice.grade = g
        kept_choices.append(choice)
    state.submersion_grade = grade
    state.submersions = kept_choices

    public_choices: list[dict[str, Any]] = []
    public_echoes: list[dict[str, Any]] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    taken_counts: dict[str, int] = {}
    echo_names: list[str] = []

    for choice in kept_choices:
        g = choice.grade
        echo_id = (choice.echo_id or "").strip()
        extra = (choice.extra or "").strip() or None
        choice.extra = extra
        row = {
            "id": choice.id,
            "grade": g,
            "echo_id": echo_id,
            "name": "",
            "extra": extra,
            "karma": submersion_karma_for_grade(g),
            "needs_extra": False,
            "source": "",
            "page": "",
        }
        if not echo_id:
            warnings.append(f"サブマージョン等級 {g} のエコーを選んでください")
            public_choices.append(row)
            continue

        spec = _echo_by_id(echo_id)
        if not spec:
            warnings.append(f"未知のエコーを等級 {g} から外しました")
            choice.echo_id = ""
            choice.extra = None
            row["echo_id"] = ""
            row["extra"] = None
            public_choices.append(row)
            continue

        count = taken_counts.get(spec["id"], 0)
        max_takes = spec.get("max_takes")
        if max_takes is not None and count >= int(max_takes):
            warnings.append(f"{spec['name']} は最大 {max_takes} 回までです（等級 {g} から外しました）")
            choice.echo_id = ""
            choice.extra = None
            row["echo_id"] = ""
            row["extra"] = None
            public_choices.append(row)
            continue

        if spec.get("needs_extra") and not extra:
            warnings.append(f"{spec['name']} の対象（プログラム名など）を入力してください")

        taken_counts[spec["id"]] = count + 1
        echo_names.append(spec["name"])
        public_echoes.append(
            {
                "id": choice.id,
                "echo_id": spec["id"],
                "name": spec["name"],
                "grade": g,
                "extra": extra,
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
        if spec.get("bonus"):
            bonus_sources.append((spec["name"], list(spec.get("bonus") or [])))
        row.update(
            {
                "echo_id": spec["id"],
                "name": spec["name"],
                "extra": extra,
                "needs_extra": bool(spec.get("needs_extra")),
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
        public_choices.append(row)

    if grade > 0 and res <= 0:
        errors.append("サブマージョンにはレゾナンスが必要です")
    elif grade > res:
        errors.append(f"サブマージョン等級はレゾナンス以下です（等級 {grade} / RES {res}）")

    return {
        "warnings": warnings,
        "grade": grade,
        "karma": submersion_karma_total(grade),
        "choices": public_choices,
        "echoes": public_echoes,
        "echo_names": echo_names,
        "bonus_sources": bonus_sources,
        "res_max_bonus": grade,
    }


def compute(state: CharacterState) -> CharacterState:
    data = catalog()
    state.build_method = normalize_build_method(getattr(state, "build_method", None))
    is_karma = state.build_method == BUILD_METHOD_KARMA
    career = bool(getattr(state, "career", False))
    state.career = career
    state.karma_earned = max(0, int(getattr(state, "karma_earned", 0) or 0))
    state.nuyen_earned = max(0, int(getattr(state, "nuyen_earned", 0) or 0))
    skill_rating_cap = CAREER_SKILL_MAX if career else 6
    skill_group_cap = CAREER_SKILL_GROUP_MAX if career else 6
    errors = validate_priorities(state.priorities, state.build_method)
    meta = find_metatype(state.metatype, state.metavariant)
    attrs_spec = meta["attributes"]
    warnings = _drop_invalid_vehicle_ware(state)
    ensure_subsystems(state)
    errors.extend(_side_conflicts("cyberware", state.cyberware))
    errors.extend(_side_conflicts("bioware", state.bioware))
    warnings.extend(_clamp_ware_grades("cyberware", state.cyberware))
    warnings.extend(_clamp_ware_grades("bioware", state.bioware))
    installed_names = {
        "cyberware": _installed_ware_names("cyberware", state.cyberware),
        "bioware": _installed_ware_names("bioware", state.bioware),
    }
    warnings.extend(_required_warnings("cyberware", state.cyberware, installed_names, state.metatype, state.metavariant))
    warnings.extend(_required_warnings("bioware", state.bioware, installed_names, state.metatype, state.metavariant))

    talent = resolve_talent_for_method(state.priorities.Talent, state.talent, state.build_method)
    state.talent = talent["name"]
    sources: list[tuple[str, list[dict[str, Any]]]] = [(meta["name"], meta.get("bonus") or [])]
    qualities, free_quality_ids, dropped_qualities = gather_qualities(state, talent)
    for name in dropped_qualities:
        warnings.append(f"{name} は他のクオリティと両立しないため外しました")
    for q in qualities:
        sources.append((q["name"], q.get("bonus") or []))
    needs_mentor = any(q["id"] == MENTOR_SPIRIT_ID for q in qualities)
    mentor = resolve_mentor(state, talent["name"], needs_mentor, data["skills"])
    warnings.extend(mentor["warnings"])
    errors.extend(mentor["errors"])
    sources.extend(mentor["bonus_sources"])
    vehicle_hosts = set(_vehicle_mod_hosts(state))
    cyber_installed = resolve_ware("cyberware", state.cyberware, attrs_spec)
    bio_installed = resolve_ware("bioware", state.bioware, attrs_spec)
    _finalize_avail_tree(cyber_installed, grade_kind="cyberware")
    _finalize_avail_tree(bio_installed, grade_kind="bioware")
    _zero_vehicle_hosted_essence(cyber_installed, vehicle_hosts)
    installed = cyber_installed + bio_installed
    hosted_ids = _vehicle_hosted_ware_ids(cyber_installed, vehicle_hosts)
    for item in installed:
        if item.get("id") in hosted_ids:
            continue
        sources.append((item["name"], item.get("bonus") or []))
    ware_attr_bonus = _ware_attribute_bonuses(
        [item for item in installed if item.get("id") not in hosted_ids]
    )
    if not career:
        _check_ware_attribute_cap(ware_attr_bonus, errors)
    effects = collect_effects(sources)
    attr_max_bonus, attr_select_warnings = resolve_attribute_selects(state, effects, qualities)
    warnings.extend(attr_select_warnings)
    seeker_targets = effects.get("cyberseeker") or []
    limb_quality = apply_cyberseeker(cyber_installed, seeker_targets, attrs_spec, state.options)
    warnings.extend(redliner_incompat_warnings(installed, seeker_targets))
    if limb_quality:
        for key, value in (limb_quality.get("attribute_bonus") or {}).items():
            if key in {"STR", "AGI"}:
                continue
            effects["attribute_bonus"][key] = int(effects["attribute_bonus"].get(key, 0)) + int(value)
        effects["cm_physical"] += int(limb_quality.get("cm_physical") or 0)

    special_key, talent_start = talent_special(talent)
    if is_karma and special_key:
        talent_start = 1
    enabled = set(effects["enabled_tabs"])
    if special_key:
        enabled.add(special_key)

    ess_start = float(attrs_spec.get("ESS", {}).get("max") or 6)
    ess_lost_cyber = round(sum(float(item["essence"]) for item in cyber_installed), 4)
    ess_lost_bio = round(sum(float(item["essence"]) for item in bio_installed), 4)
    ess_lost = round(ess_lost_cyber + ess_lost_bio, 4)
    ess_penalty = float(effects.get("essence_penalty") or 0)
    ess_penalty_mag_exempt = float(effects.get("essence_penalty_mag_exempt") or 0)
    ess = max(0.0, round(ess_start - ess_lost - ess_penalty, 2))
    mag_relevant_loss = ess_lost + max(0.0, ess_penalty - ess_penalty_mag_exempt)
    mag_penalty = int(math.ceil(mag_relevant_loss - 1e-9)) if mag_relevant_loss > 0 else 0

    initiate_grade = max(0, int(state.initiate_grade or 0)) if talent["name"] in MAG_TALENTS else 0
    submersion_grade = max(0, int(state.submersion_grade or 0)) if talent["name"] in RES_TALENTS else 0
    ratings: dict[str, int] = {}
    for key, spec in attrs_spec.items():
        racial_min = int(spec["min"])
        racial_max = int(spec["max"]) + int(attr_max_bonus.get(key) or 0)
        raw = int(state.attributes.get(key, racial_min))
        if key == "MAG":
            if special_key == "MAG":
                floor = max(talent_start, 1)
                mag_cap = racial_max + initiate_grade
                raw = max(floor, min(mag_cap, raw))
                raw = max(0, raw - mag_penalty)
            else:
                raw = 0
        elif key == "RES":
            if special_key == "RES":
                floor = max(talent_start, 1)
                res_cap = racial_max + submersion_grade
                raw = max(floor, min(res_cap, raw))
                raw = max(0, raw - mag_penalty)
            else:
                raw = 0
        elif key == "ESS":
            raw = int(ess)
        else:
            raw = max(racial_min, min(racial_max, raw))
        ratings[key] = raw

    quality_names = {q["name"] for q in qualities}
    initiation = resolve_initiation(
        state,
        talent["name"],
        int(ratings.get("MAG") or 0),
        quality_names,
        errors,
    )
    warnings.extend(initiation["warnings"])
    for source, nodes in initiation["bonus_sources"]:
        apply_bonus_nodes(nodes, effects, source)
    if talent["name"] in MAG_TALENTS:
        enabled.add("initiation")
    submersion = resolve_submersion(
        state,
        talent["name"],
        int(ratings.get("RES") or 0),
        quality_names,
        errors,
    )
    warnings.extend(submersion["warnings"])
    for source, nodes in submersion["bonus_sources"]:
        apply_bonus_nodes(nodes, effects, source)
    if talent["name"] in RES_TALENTS:
        enabled.add("submersion")
    qi = resolve_qi_foci(
        state,
        talent["name"],
        int(ratings.get("MAG") or 0),
        data["skills"],
        list(effects.get("focus_binding") or []),
    )
    warnings.extend(qi["warnings"])
    errors.extend(qi["errors"])
    foci = resolve_foci(
        state,
        talent["name"],
        int(ratings.get("MAG") or 0),
        list(effects.get("focus_binding") or []),
    )
    warnings.extend(foci["warnings"])
    _finalize_avail_tree(list(foci.get("public") or []), rating_key="force")
    for source, nodes in foci["bonus_sources"]:
        apply_bonus_nodes(nodes, effects, source)
    focus_limits = apply_focus_limits(
        int(ratings.get("MAG") or 0),
        list(qi.get("public") or []),
        list(foci.get("public") or []),
        errors,
    )
    adept = resolve_adept_powers(
        state,
        talent["name"],
        int(ratings.get("MAG") or 0),
        data["skills"],
        quality_names,
        bool(effects.get("magicians_way")),
        list(mentor.get("free_powers") or []) + list(qi.get("free_powers") or []),
        int(ratings.get("WIL") or 1),
        int(ratings.get("INT") or 1),
    )
    warnings.extend(adept["warnings"])
    errors.extend(adept["errors"])
    state.mystic_pp = int(adept["mystic_pp"])
    enhancements = resolve_enhancements(state, talent["name"], quality_names, set(adept.get("power_names") or []))
    warnings.extend(enhancements["warnings"])
    effects["enabled_tabs"] = set(effects["enabled_tabs"])
    for source, nodes in adept["bonus_sources"] + enhancements["bonus_sources"]:
        apply_bonus_nodes(nodes, effects, source)
    attr_totals = {
        key: int(ratings.get(key) or 0) + int((effects.get("attribute_bonus") or {}).get(key, 0))
        for key in ratings
    }
    gear = resolve_gear(state, cyber_installed, attr_totals)
    warnings.extend(gear["warnings"])
    errors.extend(gear.get("errors") or [])
    apply_lifestyle_cost_mod(gear, int(effects.get("lifestyle_cost") or 0))
    apply_reach_bonus(gear.get("weapons"), int(effects.get("reach") or 0))
    errors.extend(_attach_ware_to_vehicle_mods(gear.get("vehicle_mods") or [], cyber_installed))
    for source, nodes in gear["bonus_sources"]:
        apply_bonus_nodes(nodes, effects, source)
    attach_weapon_focus_dice(state, list(foci.get("public") or []), list(gear.get("weapons") or []), warnings)
    if talent["name"] in ADEPT_TALENTS:
        enabled.add("adept")
        effects["enabled_tabs"].add("adept")
    enabled.update(effects["enabled_tabs"])

    if talent["name"] == "Adept":
        power_pool = float(ratings["MAG"]) + float(effects.get("adept_power_points") or 0)
    elif talent["name"] == "Mystic Adept":
        power_pool = float(state.mystic_pp) + float(effects.get("adept_power_points") or 0)
    else:
        power_pool = 0.0
    power_spent = float(adept["spent"])
    if power_spent > power_pool + 1e-9:
        errors.append(f"パワー点が不足しています（使用 {power_spent:g} / 上限 {power_pool:g}）")

    bonus = effects["attribute_bonus"]
    total = {k: ratings[k] + int(bonus.get(k, 0)) for k in ratings}
    total["ESS"] = ess
    limb_replace = limb_attribute_replace(cyber_installed, int(total["STR"]), int(total["AGI"]), attrs_spec)
    if limb_replace:
        total["STR"] = int(limb_replace["str"])
        total["AGI"] = int(limb_replace["agi"])

    owned_magic_names = set(initiation.get("art_names") or set()) | set(initiation.get("metamagic_names") or set())
    magic = resolve_spells(state, talent, int(total.get("MAG") or 0), total, owned_magic_names)
    warnings.extend(magic["warnings"])
    spell_focus = {mod["name"]: int(mod.get("bonus") or 0) for mod in (effects.get("spell_category_mods") or [])}
    for item in magic.get("public") or []:
        bonus = int(spell_focus.get(item.get("category") or "", 0))
        if bonus:
            item["focus_bonus"] = bonus
    spirits = resolve_spirits(
        state,
        talent["name"],
        int(total.get("MAG") or 0),
        _tradition_by_id(state.tradition_id),
    )
    warnings.extend(spirits["warnings"])
    if talent["name"] in SPELL_TALENTS:
        enabled.add("spells")
    if talent["name"] in SPIRIT_TALENTS:
        enabled.add("spirits")
    resonance = resolve_complex_forms(
        state,
        talent["name"],
        int(total.get("RES") or 0),
        total,
        quality_names,
    )
    warnings.extend(resonance["warnings"])
    techno_sprites = resolve_sprites(
        state,
        talent["name"],
        int(total.get("RES") or 0),
        resonance.get("stream"),
    )
    warnings.extend(techno_sprites["warnings"])
    errors.extend(techno_sprites["errors"])
    if talent["name"] in COMPLEX_FORM_TALENTS:
        enabled.add("complexforms")
    if talent["name"] in SPRITE_TALENTS:
        enabled.add("sprites")
    if talent["name"] in FOCUS_TALENTS:
        enabled.add("foci")
    for item in adept.get("public") or []:
        extra = item.get("extra")
        if item.get("select") != "spell" or not extra:
            continue
        force = (item.get("spell") or {}).get("force")
        item["spell"] = spell_cast_info(
            extra,
            force,
            int(total.get("MAG") or 0),
            int(magic["resist"]),
            str(magic["resist_attrs"]),
        )

    attr_row = priority_value("Attributes", state.priorities.Attributes)
    skill_row = priority_value("Skills", state.priorities.Skills)
    res_row = priority_value("Resources", state.priorities.Resources)
    her_row = priority_value("Heritage", state.priorities.Heritage)

    special_from_meta = 0
    extra_karma = 0
    for entry in her_row.get("metatypes") or []:
        if entry["name"] == state.metatype:
            special_from_meta = entry.get("special", 0)
            extra_karma += entry.get("karma", 0)
            if state.metavariant:
                for v in entry.get("variants") or []:
                    if v["name"] == state.metavariant:
                        special_from_meta = v.get("special", special_from_meta)
                        extra_karma += v.get("karma", 0)
            break

    spent_physical = 0
    for key in PHYSICAL_ATTRS:
        spent_physical += max(0, ratings[key] - int(attrs_spec[key]["min"]))
    spent_special = max(0, ratings["EDG"] - int(attrs_spec["EDG"]["min"]))
    if special_key == "MAG":
        spent_special += max(0, ratings["MAG"] - talent_start)
    elif special_key == "RES":
        spent_special += max(0, ratings["RES"] - talent_start)

    if is_karma:
        attr_points = 0
        skill_points = 0
        group_points = 0
        special_from_meta = 0
        state.karma_nuyen = max(0, min(KARMA_NUYEN_MAX, int(state.karma_nuyen or 0)))
        nuyen_pool = int(state.karma_nuyen) * KARMA_TO_NUYEN
        metatype_karma_cost = max(0, int(meta.get("karma") or 0))
        heritage_karma_cost = 0
    else:
        attr_points = int(attr_row.get("attribute_points") or 0)
        skill_points = int(skill_row.get("skill_points") or 0)
        group_points = int(skill_row.get("skill_group_points") or 0)
        nuyen_pool = int(res_row.get("nuyen") or 0)
        metatype_karma_cost = 0
        # Priority chargen: metatypes.xml <karma> is for Karma/Sum-to-Ten, not Priority.
        # Heritage table <karma> is an extra cost for some metavariants / rare races.
        heritage_karma_cost = extra_karma
        state.karma_nuyen = 0

    nuyen_pool += int(state.nuyen_earned or 0)
    nuyen_spent = (
        sum(int(item["nuyen"]) for item in installed)
        + int(qi.get("nuyen") or 0)
        + int(foci.get("nuyen") or 0)
        + int(spirits.get("nuyen") or 0)
        + int(gear.get("nuyen") or 0)
    )
    nuyen = nuyen_pool - nuyen_spent

    skill_spent = 0
    group_spent = 0
    skill_totals: dict[str, int] = {}
    exotic_names = {s["name"] for s in data["skills"]["skills"] if s.get("exotic")}
    if exotic_names:
        state.skills = {name: rating for name, rating in state.skills.items() if name not in exotic_names}
    for group, rating in state.skill_groups.items():
        rating = max(0, min(skill_group_cap, int(rating)))
        state.skill_groups[group] = rating
        group_spent += rating
        for s in data["skills"]["skills"]:
            if s.get("skillgroup") == group and not s.get("exotic"):
                skill_totals[s["name"]] = max(skill_totals.get(s["name"], 0), rating)
    tentative = dict(skill_totals)
    for name, rating in state.skills.items():
        tentative[name] = max(tentative.get(name, 0), max(0, min(skill_rating_cap + 1, int(rating))))
    skill_picks = resolve_skill_picks(state, data["skills"], tentative)
    warnings.extend(skill_picks["warnings"])
    for name, rating in state.skills.items():
        cap = skill_rating_cap + int(skill_picks["skill_max_bonus"].get(name, 0))
        rating = max(0, min(cap, int(rating)))
        state.skills[name] = rating
        base = skill_totals.get(name, 0)
        extra = max(0, rating - base)
        skill_spent += extra
        skill_totals[name] = max(base, rating)
    exotic = resolve_exotic_skills(
        state,
        data["skills"],
        skill_picks["skill_max_bonus"],
        rating_cap=skill_rating_cap,
    )
    warnings.extend(exotic["warnings"])
    skill_spent += int(exotic["spent"])
    skill_totals.update(exotic["totals"])
    knowledge = resolve_knowledge(state, data["skills"], total, rating_cap=skill_rating_cap)
    warnings.extend(knowledge["warnings"])
    know_spent = int(knowledge["spent"])
    know_max = int(knowledge["max"])
    bought_knowledge = dict(state.knowledge_skills)
    for name in state.native_languages:
        bought_knowledge[name] = max(int(bought_knowledge.get(name) or 0), 1)
    skill_mods = resolve_skill_mods(data["skills"], effects, bought_knowledge, state.knowledge_categories)
    for name, bonus in skill_picks["skill_bonus"].items():
        skill_mods["skill_bonus"][name] = int(skill_mods["skill_bonus"].get(name, 0)) + int(bonus)
    for name, notes in skill_picks["skill_bonus_notes"].items():
        existing = skill_mods["skill_bonus_notes"].setdefault(name, [])
        for note in notes:
            if note not in existing:
                existing.append(note)
    _copy_exotic_skill_bonuses(skill_mods, exotic["public"])
    for name in effects.get("disabled_skills") or []:
        if int(skill_totals.get(name) or 0) > 0 or int(state.skills.get(name) or 0) > 0:
            warnings.append(f"{name} は無効化されているスキルです")
    for group in effects.get("disabled_skill_groups") or []:
        if int(state.skill_groups.get(group) or 0) > 0:
            warnings.append(f"スキルグループ {group} は無効化されています")
    skillsofts = resolve_skillsofts(list(gear.get("gear") or []), data["skills"], effects, warnings)
    _attach_skillsoft_knowledge(knowledge["public"], skillsofts["knowledge"], data["skills"])
    specs = resolve_specializations(
        state,
        data["skills"],
        skill_totals,
        skillsofts["active"],
        skillsofts["knowledge"],
    )
    warnings.extend(specs["warnings"])
    spec_active = int(specs["active_spent"])
    spec_knowledge = int(specs["knowledge_spent"])
    if is_karma:
        spec_karma = (spec_active + spec_knowledge) * KARMA_SPECIALIZATION
    elif career:
        # Priority career: new specs cost karma (baseline settles chargen specs).
        spec_karma = 0
    else:
        skill_spent += spec_active
        know_spent += spec_knowledge
        spec_karma = 0
    _attach_specializations(knowledge["public"], specs["specs"])
    effective_skills = _merge_skill_ratings(skill_totals, skillsofts["active"])
    effective_knowledge = _merge_skill_ratings(dict(state.knowledge_skills or {}), skillsofts["knowledge"])

    karma_from_q = sum(
        q["karma"]
        for q in qualities
        if not q.get("onlyprioritygiven") and q["id"] not in free_quality_ids
    )
    mystic_karma = int(state.mystic_pp) * MYSTIC_PP_KARMA
    extra_adept_karma = int(enhancements.get("karma") or 0) + int(qi.get("karma") or 0) + int(foci.get("karma") or 0)
    spell_karma = int(magic.get("karma") or 0) + int(resonance.get("karma") or 0)
    career_adv_karma = 0
    if is_karma:
        attr_karma = attribute_karma_cost(ratings, attrs_spec, special_key)
        skill_buy_karma = skill_karma_cost(
            state.skill_groups, skill_totals, data["skills"], group_cap=skill_group_cap
        )
        knowledge_karma = knowledge_excess_karma(dict(state.knowledge_skills or {}), know_max)
        nuyen_karma = int(state.karma_nuyen or 0)
        karma_pool = KARMA_CHARGEN_POOL + int(state.karma_earned or 0)
        karma_spent = (
            karma_from_q
            + metatype_karma_cost
            + mystic_karma
            + extra_adept_karma
            + spell_karma
            + attr_karma
            + skill_buy_karma
            + knowledge_karma
            + spec_karma
            + nuyen_karma
        )
    else:
        attr_karma = 0
        skill_buy_karma = 0
        knowledge_karma = 0
        nuyen_karma = 0
        karma_pool = 25 + int(state.karma_earned or 0)
        karma_spent = karma_from_q + heritage_karma_cost + mystic_karma + extra_adept_karma + spell_karma
        if career:
            baseline = state.career_baseline
            if baseline is None:
                baseline = snapshot_career_baseline(state)
                state.career_baseline = baseline
            career_adv_karma = career_raise_karma(state, baseline, skill_totals, data["skills"])
            karma_spent += career_adv_karma

    bod = total["BOD"]
    agi = total["AGI"]
    rea = total["REA"]
    stre = total["STR"]
    wil = total["WIL"]
    logi = total["LOG"]
    intuition = total["INT"]
    cha = total["CHA"]
    contacts = resolve_contacts(state, int(cha or 0), career=career)
    warnings.extend(contacts["warnings"])
    karma_spent += int(contacts.get("karma") or 0)

    martial_ctx = quality_requirement_context(
        state,
        talent,
        qualities,
        meta,
        ess,
        ess_lost,
        effective_skills,
        set(adept.get("power_names") or []),
        {str(item.get("name") or "") for item in (magic.get("public") or []) if item.get("name")},
        str(((magic.get("tradition") if isinstance(magic.get("tradition"), dict) else {}) or {}).get("name") or ""),
        {item["name"] for item in cyber_installed},
        {item["name"] for item in bio_installed},
        effective_knowledge,
    )
    martial_ctx = {
        **martial_ctx,
        "qualities": set(martial_ctx.get("qualities") or []) | {talent["name"]},
    }
    martial = resolve_martial_arts(state, martial_ctx, errors, career=career)
    warnings.extend(martial["warnings"])
    karma_spent += int(martial.get("karma") or 0)
    karma_spent += int(initiation.get("karma") or 0)
    karma_spent += int(submersion.get("karma") or 0)
    karma_left = karma_pool - karma_spent

    physical_limit = _ceil_div((bod * 2 + agi + rea + stre) / 3) + int(effects.get("limit_physical") or 0)
    mental_limit = _ceil_div((logi * 2 + intuition + wil) / 3) + int(effects.get("limit_mental") or 0)
    social_limit = _ceil_div((cha * 2 + wil + ess) / 3) + int(effects.get("limit_social") or 0)
    cm_phys = 8 + _ceil_div(bod / 2) + effects["cm_physical"]
    cm_stun = 8 + _ceil_div(wil / 2) + effects["cm_stun"]
    initiative = rea + intuition + effects["initiative"]
    initiative_dice = 1 + int(effects.get("initiative_dice") or 0)
    warnings.extend(
        attach_spirit_tests(
            list(spirits.get("public") or []),
            int(total.get("MAG") or 0),
            effective_skills,
            skill_mods["skill_bonus"],
            total,
            data["skills"],
        )
    )
    warnings.extend(
        attach_focus_tests(
            list(foci.get("public") or []),
            int(total.get("MAG") or 0),
            effective_skills,
            skill_mods["skill_bonus"],
            total,
            data["skills"],
            mental_limit,
        )
    )
    warnings.extend(
        attach_complex_form_tests(
            list(resonance.get("public") or []),
            int(total.get("RES") or 0),
            effective_skills,
            skill_mods["skill_bonus"],
            total,
            data["skills"],
        )
    )
    warnings.extend(
        attach_sprite_tests(
            list(techno_sprites.get("public") or []),
            int(total.get("RES") or 0),
            effective_skills,
            skill_mods["skill_bonus"],
            total,
            data["skills"],
        )
    )

    movement = resolve_movement(meta, effects)

    tradition_info = magic.get("tradition") if isinstance(magic.get("tradition"), dict) else {}
    negative_quality_karma = apply_quality_rules(
        state,
        qualities,
        free_quality_ids,
        quality_requirement_context(
            state,
            talent,
            qualities,
            meta,
            ess,
            ess_lost,
            effective_skills,
            set(adept.get("power_names") or []),
            {str(item.get("name") or "") for item in (magic.get("public") or []) if item.get("name")},
            str((tradition_info or {}).get("name") or ""),
            {item["name"] for item in cyber_installed},
            {item["name"] for item in bio_installed},
            effective_knowledge,
        ),
        errors,
        career=career,
    )

    if not career:
        at_six = [n for n, r in skill_totals.items() if r >= 6]
        if len(at_six) > 1:
            errors.append("作成時にレーティング6のスキルは1つまでです")
        if is_karma:
            at_natural_max = []
            for key, spec in attrs_spec.items():
                if key in {"ESS", "MAG", "RES"} and key != special_key:
                    continue
                if key not in ratings:
                    continue
                racial_max = int(spec.get("max") or 0) + int(attr_max_bonus.get(key) or 0)
                if key == "MAG" and special_key == "MAG":
                    racial_max = racial_max + int(initiation.get("mag_max_bonus") or 0)
                if key == "RES" and special_key == "RES":
                    racial_max = racial_max + int(submersion.get("res_max_bonus") or 0)
                if racial_max > 0 and int(ratings.get(key) or 0) >= racial_max:
                    at_natural_max.append(key)
            if len(at_natural_max) > 1:
                errors.append("作成時に自然上限の属性は1つまでです")
        else:
            if spent_physical > attr_points:
                errors.append(f"属性点が不足しています（使用 {spent_physical} / 上限 {attr_points}）")
            if spent_special > special_from_meta:
                errors.append(f"特殊属性点が不足しています（使用 {spent_special} / 上限 {special_from_meta}）")
            if skill_spent > skill_points:
                errors.append(f"スキル点が不足しています（使用 {skill_spent} / 上限 {skill_points}）")
            if group_spent > group_points:
                errors.append(f"スキルグループ点が不足しています（使用 {group_spent} / 上限 {group_points}）")
            if know_spent > know_max:
                errors.append(f"知識スキル点が不足しています（使用 {know_spent} / 上限 {know_max}）")
    if karma_left < 0:
        errors.append(f"カルマが不足しています（残り {karma_left}）")
    if nuyen < 0:
        errors.append(f"ニューエンが不足しています（残り {nuyen}¥）")
    if ess <= 0:
        errors.append("エッセンスが0以下です")
    for item in installed:
        cap_max = float(item.get("capacity_max") or 0)
        if cap_max <= 0:
            continue
        used = float(item.get("capacity_used") or 0)
        if used > cap_max + 1e-9:
            errors.append(f"{item['name']} の容量超過（{used:g}/{cap_max:g}）")

    if not is_karma:
        allowed = {e["name"] for e in heritage_options(state.priorities.Heritage)}
        if allowed and state.metatype not in allowed:
            errors.append(f"{state.metatype} はこの優先度のメタタイプに含まれません")
    if not career:
        _check_avail_limit(
            _avail_entries(
                cyber_installed,
                bio_installed,
                gear.get("armor_items"),
                gear.get("armor_mods"),
                gear.get("weapons"),
                gear.get("weapon_accessories"),
                gear.get("commlinks"),
                gear.get("cyberdecks"),
                gear.get("rccs"),
                gear.get("optics"),
                gear.get("programs"),
                gear.get("apps"),
                gear.get("sensors"),
                gear.get("drones"),
                gear.get("vehicles"),
                gear.get("vehicle_mods"),
                gear.get("weapon_mounts"),
                gear.get("gear"),
                gear.get("lifestyles"),
                foci.get("public"),
            ),
            effects,
            errors,
        )
        _check_device_rating_limit(
            _device_rating_entries(
                cyber_installed,
                bio_installed,
                gear.get("commlinks"),
                gear.get("cyberdecks"),
                gear.get("rccs"),
                gear.get("optics"),
                gear.get("sensors"),
                gear.get("gear"),
            ),
            errors,
        )

    state.attributes = ratings
    sum_spent = sum_to_ten_spent(state.priorities)
    state.derived = {
        "errors": errors,
        "warnings": warnings,
        "build_method": state.build_method,
        "sum_to_ten": {
            "used": sum_spent,
            "max": SUM_TO_TEN_BUDGET,
            "costs": dict(SUM_TO_TEN_COST),
            "unique": priorities_are_unique(state.priorities),
        },
        "karma_chargen": {
            "enabled": is_karma,
            "pool": karma_pool if is_karma else 0,
            "nuyen_karma": int(state.karma_nuyen or 0) if is_karma else 0,
            "nuyen_karma_max": KARMA_NUYEN_MAX,
            "nuyen_per_karma": KARMA_TO_NUYEN,
            "metatype": metatype_karma_cost if is_karma else 0,
            "attributes": attr_karma if is_karma else 0,
            "skills": skill_buy_karma if is_karma else 0,
            "knowledge": knowledge_karma if is_karma else 0,
            "specializations": spec_karma if is_karma else 0,
            "qualities": karma_from_q,
            "other": mystic_karma + extra_adept_karma + spell_karma + int(contacts.get("karma") or 0) + int(martial.get("karma") or 0) + int(initiation.get("karma") or 0) + int(submersion.get("karma") or 0),
        },
        "totals": total,
        "limits": {
            "physical": physical_limit,
            "mental": mental_limit,
            "social": social_limit,
        },
        "limit_modifiers": compact_limit_modifiers(effects),
        "condition_monitor": {"physical": cm_phys, "stun": cm_stun},
        "initiative": {"value": initiative, "dice": initiative_dice},
        "movement": movement,
        "essence": ess,
        "essence_lost": ess_lost,
        "essence_lost_cyber": ess_lost_cyber,
        "essence_lost_bio": ess_lost_bio,
        "armor": int(effects["armor"]) + int(gear.get("armor") or 0),
        "special_armor": special_armor_totals(effects),
        "worn_armor": gear.get("worn_name") or "",
        "armor_items": gear.get("armor_items") or [],
        "armor_mods": gear.get("armor_mods") or [],
        "weapons": gear.get("weapons") or [],
        "weapon_accessories": gear.get("weapon_accessories") or [],
        "commlinks": gear.get("commlinks") or [],
        "cyberdecks": gear.get("cyberdecks") or [],
        "rccs": gear.get("rccs") or [],
        "optics": gear.get("optics") or [],
        "programs": gear.get("programs") or [],
        "apps": gear.get("apps") or [],
        "sensors": gear.get("sensors") or [],
        "drones": gear.get("drones") or [],
        "vehicles": gear.get("vehicles") or [],
        "vehicle_mods": gear.get("vehicle_mods") or [],
        "weapon_mounts": gear.get("weapon_mounts") or [],
        "gear": gear.get("gear") or [],
        "lifestyles": gear.get("lifestyles") or [],
        "commlink": gear.get("commlink"),
        "cyberdeck": gear.get("cyberdeck"),
        "rcc": gear.get("rcc"),
        "lifestyle": gear.get("lifestyle"),
        "nuyen": nuyen,
        "nuyen_spent": nuyen_spent,
        "nuyen_pool": nuyen_pool,
        "nuyen_earned": int(state.nuyen_earned or 0),
        "karma_earned": int(state.karma_earned or 0),
        "career": career,
        "career_advancement_karma": int(career_adv_karma),
        "skill_rating_max": skill_rating_cap,
        "skill_group_max": skill_group_cap,
        "avail_limit": None if career else CHARGEN_AVAIL_MAX,
        "device_rating_limit": None if career else CHARGEN_DEVICE_RATING_MAX,
        "ware_attr_limit": None if career else CHARGEN_WARE_ATTR_BONUS_MAX,
        "ware_attr_bonus": ware_attr_bonus,
        "karma": {
            "pool": karma_pool,
            "spent": karma_spent,
            "remaining": karma_left,
            "negative": {
                "used": negative_quality_karma,
                "max": None if career else NEGATIVE_QUALITY_KARMA_CAP,
            },
        },
        "power_points": {"used": power_spent, "max": power_pool},
        "adept_powers": adept["public"],
        "mystic_pp": state.mystic_pp,
        "way_discount": {"used": adept.get("discount_used") or 0, "max": adept.get("discount_max") or 0},
        "mentor": mentor.get("public"),
        "needs_mentor": needs_mentor,
        "qi_foci": qi.get("public") or [],
        "foci": foci.get("public") or [],
        "focus_limits": focus_limits,
        "spirits": spirits.get("public") or [],
        "enhancements": enhancements.get("public") or [],
        "damage_resistance": int(effects.get("damage_resistance") or 0),
        "unarmed_dv": int(effects.get("unarmed_dv") or 0),
        "unarmed_physical": bool(effects.get("unarmed_physical")),
        "unlock_skills": list(effects.get("unlock_skills") or []),
        "spells": magic.get("public") or [],
        "spell_points": {"used": magic.get("used") or 0, "free": magic.get("free_max") or 0, "paid": magic.get("paid") or 0},
        "tradition": magic.get("tradition"),
        "drain_resist": {"pool": magic.get("resist") or 0, "attrs": magic.get("resist_attrs") or "WIL+INT"},
        "complex_forms": resonance.get("public") or [],
        "complex_form_points": {"used": resonance.get("used") or 0, "free": resonance.get("free_max") or 0, "paid": resonance.get("paid") or 0},
        "sprites": techno_sprites.get("public") or [],
        "stream": resonance.get("stream"),
        "fade_resist": {"pool": resonance.get("resist") or 0, "attrs": resonance.get("resist_attrs") or "WIL+RES"},
        "living_persona": (
            living_persona(
                total,
                int(total.get("RES") or 0),
                effects.get("living_persona") if isinstance(effects.get("living_persona"), dict) else None,
                int(effects.get("matrix_initiative_dice") or 0),
            )
            if talent["name"] in RES_TALENTS
            else None
        ),
        "points": {
            "attributes": {"used": spent_physical, "max": attr_points},
            "special": {"used": spent_special, "max": special_from_meta},
            "skills": {"used": skill_spent, "max": skill_points},
            "skill_groups": {"used": group_spent, "max": group_points},
            "knowledge": {"used": know_spent, "max": know_max},
            "contacts": {"used": contacts.get("used") or 0, "max": contacts.get("free") or 0},
        },
        "knowledge_skills": knowledge["public"],
        "contacts": contacts.get("public") or [],
        "contact_points": {
            "used": contacts.get("used") or 0,
            "free": contacts.get("free") or 0,
            "paid": contacts.get("paid") or 0,
        },
        "martial_arts": martial.get("public") or [],
        "martial_art_points": {
            "styles": martial.get("style_count") or 0,
            "style_max": martial.get("style_max") or MARTIAL_ART_CHARGEN_STYLE_MAX,
            "techniques": martial.get("technique_count") or 0,
            "technique_max": martial.get("technique_max") or MARTIAL_ART_CHARGEN_TECHNIQUE_MAX,
            "karma": martial.get("karma") or 0,
        },
        "martial_spec_options": martial.get("spec_extras") or {},
        "unarmed_reach": int(martial.get("unarmed_reach") or 0) + int(effects.get("reach") or 0),
        "reach": int(effects.get("reach") or 0),
        "lifestyle_cost_mod": int(effects.get("lifestyle_cost") or 0),
        "notoriety": int(effects.get("notoriety") or 0),
        "fame": int(effects.get("fame") or 0),
        "public_awareness": int(effects.get("public_awareness") or 0),
        "fatigue_resist": int(effects.get("fatigue_resist") or 0),
        "spell_resistance": int(effects.get("spell_resistance") or 0),
        "spell_dice_pool": list(effects.get("spell_dice_pool") or []),
        "test_mods": dict(effects.get("test_mods") or {}),
        "cm_recovery": {
            "physical": int(effects.get("cm_recovery_physical") or 0),
            "stun": int(effects.get("cm_recovery_stun") or 0),
        },
        "essence_penalty": round(float(effects.get("essence_penalty") or 0), 4),
        "attribute_max_bonus": dict(attr_max_bonus),
        "disabled_skills": list(effects.get("disabled_skills") or []),
        "disabled_skill_groups": list(effects.get("disabled_skill_groups") or []),
        "initiate_grade": int(initiation.get("grade") or 0),
        "initiation": {
            "grade": int(initiation.get("grade") or 0),
            "karma": int(initiation.get("karma") or 0),
            "choices": initiation.get("choices") or [],
            "metamagics": initiation.get("metamagics") or [],
            "arts": initiation.get("arts") or [],
        },
        "submersion_grade": int(submersion.get("grade") or 0),
        "submersion": {
            "grade": int(submersion.get("grade") or 0),
            "karma": int(submersion.get("karma") or 0),
            "choices": submersion.get("choices") or [],
            "echoes": submersion.get("echoes") or [],
        },
        "skill_totals": skill_totals,
        "skill_specializations": specs["specs"],
        "exotic_skills": exotic["public"],
        "skillsoft": skillsofts["all"],
        "skillwires": skillsofts["skillwires"],
        "skilljack": skillsofts["skilljack"],
        "skill_bonus": skill_mods["skill_bonus"],
        "skill_group_bonus": skill_mods["skill_group_bonus"],
        "skill_category_bonus": skill_mods["skill_category_bonus"],
        "skill_bonus_notes": skill_mods["skill_bonus_notes"],
        "skill_max_bonus": skill_picks["skill_max_bonus"],
        "skill_pick_slots": skill_picks["slots"],
        "enabled_tabs": sorted(enabled),
        "unimplemented_bonuses": effects["unimplemented"],
        "qualities": [
            {
                "id": q["id"],
                "name": q["name"],
                "karma": q["karma"],
                "category": q["category"],
                "source": q["source"],
                "needs_extra": quality_needs_extra(q),
                "extra": state.quality_extras.get(q["id"]) or "",
            }
            for q in qualities
        ],
        "cyberware": [_public_installed(item) for item in cyber_installed],
        "bioware": [_public_installed(item) for item in bio_installed],
        "ware_ranges": ware_ranges(attrs_spec),
        "limb_replace": limb_replace,
        "limb_quality": limb_quality,
        "talent": talent,
        "metatype_info": {
            "name": meta["name"],
            "parent": meta.get("parent"),
            "attributes": {
                key: {
                    **spec,
                    "max": int(spec.get("max") or 0) + int(attr_max_bonus.get(key) or 0),
                    "aug": int(spec.get("aug") or 0) + int(attr_max_bonus.get(key) or 0),
                }
                for key, spec in _effective_attr_spec(
                    attrs_spec,
                    special_key,
                    talent_start,
                    int(initiation.get("mag_max_bonus") or 0),
                    int(submersion.get("res_max_bonus") or 0),
                ).items()
            },
            "source": meta.get("source"),
        },
        "translations": {k: data["translations"].get(k, k) for k in [state.metatype, state.metavariant or ""]},
    }
    return state
