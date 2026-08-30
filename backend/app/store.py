from __future__ import annotations

import json
import uuid
from pathlib import Path

from .data_loader import catalog
from .engine import (
    ADEPT_TALENTS,
    BUILD_METHOD_KARMA,
    COMPLEX_FORM_TALENTS,
    FOCUS_TALENTS,
    MAG_TALENTS,
    RES_TALENTS,
    SPELL_TALENTS,
    SPIRIT_TALENTS,
    SPRITE_TALENTS,
    all_talent_options,
    compute,
    default_attributes,
    find_metatype,
    gear_extra_options,
    is_way_quality,
    normalize_build_method,
    priority_value,
    resolve_talent_for_method,
    sanitize_quality_ids,
    snapshot_career_baseline,
    talent_options,
    talent_special,
)
from .models import CharacterCreate, CharacterPatch, CharacterState, Priorities

SAVE_DIR = Path(__file__).resolve().parents[1] / "saves"
_MEMORY: dict[str, CharacterState] = {}


def _persist(state: CharacterState) -> None:
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    (SAVE_DIR / f"{state.id}.json").write_text(
        json.dumps(state.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _new_state(payload: CharacterCreate) -> CharacterState:
    meta = find_metatype(payload.metatype, None)
    method = normalize_build_method(payload.build_method)
    state = CharacterState(
        id=str(uuid.uuid4()),
        name=payload.name,
        build_method=method,
        priorities=payload.priorities or Priorities(),
        metatype=payload.metatype,
        attributes=default_attributes(meta),
    )
    return compute(state)


def create_character(payload: CharacterCreate | None = None) -> CharacterState:
    state = _new_state(payload or CharacterCreate())
    _MEMORY[state.id] = state
    _persist(state)
    return state


def get_character(cid: str) -> CharacterState:
    if cid in _MEMORY:
        return _MEMORY[cid]
    path = SAVE_DIR / f"{cid}.json"
    if path.exists():
        state = compute(CharacterState.model_validate(json.loads(path.read_text(encoding="utf-8"))))
        _MEMORY[cid] = state
        return state
    raise KeyError(cid)


def _apply_talent_ratings(data: dict) -> None:
    talent = resolve_talent_for_method(data["priorities"]["Talent"], data.get("talent"), data.get("build_method"))
    data["talent"] = talent["name"]
    key, start = talent_special(talent)
    if normalize_build_method(data.get("build_method")) == BUILD_METHOD_KARMA and key:
        start = 1
    attrs = dict(data.get("attributes") or {})
    attrs["MAG"] = start if key == "MAG" else 0
    attrs["RES"] = start if key == "RES" else 0
    data["attributes"] = attrs


def update_character(cid: str, patch: CharacterPatch) -> CharacterState:
    state = get_character(cid)
    data = state.model_dump()
    old_letter = state.priorities.Talent
    old_talent = state.talent
    old_method = normalize_build_method(state.build_method)
    was_career = bool(state.career)
    updates = patch.model_dump(exclude_unset=True)
    if "priorities" in updates and updates["priorities"] is not None:
        data["priorities"] = updates.pop("priorities")
    if "options" in updates and updates["options"] is not None:
        current = dict(data.get("options") or {})
        current.update(updates.pop("options"))
        data["options"] = current
    data.update({k: v for k, v in updates.items() if v is not None})
    if "career" in updates:
        now_career = bool(updates["career"])
        data["career"] = now_career
        if now_career and not was_career:
            data["career_baseline"] = snapshot_career_baseline(state).model_dump()
            # Seed reward ledger from existing earned totals so history stays coherent.
            if not (data.get("reward_log") or []) and (
                int(data.get("karma_earned") or 0) or int(data.get("nuyen_earned") or 0)
            ):
                data["reward_log"] = [
                    {
                        "id": str(uuid.uuid4()),
                        "label": "キャリア開始時の報酬合計",
                        "karma": max(0, int(data.get("karma_earned") or 0)),
                        "nuyen": max(0, int(data.get("nuyen_earned") or 0)),
                    }
                ]
        elif not now_career:
            data["career_baseline"] = None
    if "reward_log" in updates and updates["reward_log"] is not None:
        log = list(updates["reward_log"] or [])
        data["reward_log"] = log
        data["karma_earned"] = sum(max(0, int(row.get("karma") or 0)) for row in log if isinstance(row, dict))
        data["nuyen_earned"] = sum(max(0, int(row.get("nuyen") or 0)) for row in log if isinstance(row, dict))
    if "tradition_id" in updates:
        data["tradition_id"] = updates.pop("tradition_id") or None
    if "stream_id" in updates:
        data["stream_id"] = updates.pop("stream_id") or None
    if "quality_ids" in updates:
        data["quality_ids"], _ = sanitize_quality_ids(list(data.get("quality_ids") or []))
    if patch.metatype or patch.metavariant is not None:
        meta = find_metatype(data["metatype"], data.get("metavariant"))
        data["attributes"] = default_attributes(meta)
    data["build_method"] = normalize_build_method(data.get("build_method"))
    talent = resolve_talent_for_method(data["priorities"]["Talent"], data.get("talent"), data.get("build_method"))
    data["talent"] = talent["name"]
    method_changed = old_method != data["build_method"]
    if (
        old_letter != data["priorities"]["Talent"]
        or old_talent != data["talent"]
        or patch.metatype
        or method_changed
    ):
        _apply_talent_ratings(data)
        if data["talent"] not in ADEPT_TALENTS:
            data["adept_powers"] = []
            data["mystic_pp"] = 0
            data["qi_foci"] = []
            data["adept_enhancements"] = []
        if data["talent"] not in MAG_TALENTS:
            data["mentor_id"] = None
            data["mentor_choices"] = []
            data["mentor_extras"] = {}
            data["initiate_grade"] = 0
            data["initiations"] = []
        if data["talent"] not in SPELL_TALENTS:
            data["spells"] = []
            data["tradition_id"] = None
        if data["talent"] not in SPIRIT_TALENTS:
            data["spirits"] = []
        if data["talent"] not in FOCUS_TALENTS:
            data["foci"] = []
        if data["talent"] not in COMPLEX_FORM_TALENTS and data["talent"] not in RES_TALENTS:
            data["complex_forms"] = []
            data["stream_id"] = None
        if data["talent"] not in RES_TALENTS:
            data["submersion_grade"] = 0
            data["submersions"] = []
        if data["talent"] not in SPRITE_TALENTS:
            data["sprites"] = []
    state = compute(CharacterState.model_validate(data))
    _MEMORY[cid] = state
    _persist(state)
    return state


def export_character(cid: str) -> dict:
    return get_character(cid).model_dump()


def import_character(payload: dict) -> CharacterState:
    payload = dict(payload)
    payload["id"] = str(uuid.uuid4())
    state = compute(CharacterState.model_validate(payload))
    _MEMORY[state.id] = state
    _persist(state)
    return state


CORE_METATYPES = {"Human", "Elf", "Dwarf", "Ork", "Troll"}


def public_catalog() -> dict:
    raw = catalog()
    qualities = [
        {
            "id": q["id"],
            "name": q["name"],
            "karma": q["karma"],
            "category": q["category"],
            "source": q["source"],
            "page": q["page"],
            "bonus_tags": [n["tag"] for n in q.get("bonus") or []],
            "forbidden_qualities": list((q.get("forbidden") or {}).get("quality") or []),
            "is_way": is_way_quality(q["name"]),
            "needs_extra": bool(q.get("needs_extra")),
            "extra_kind": q.get("extra_kind") or "",
            "select_options": list(q.get("select_options") or []),
            "spirit_options": list(q.get("spirit_options") or []),
            "expertise_skill": q.get("expertise_skill") or "",
            "max_takes": q.get("max_takes"),
            "required_tree": q.get("required_tree") or [],
            "forbidden_tree": q.get("forbidden_tree") or [],
        }
        for q in raw["qualities"]
        if not q.get("onlyprioritygiven")
    ]
    table: dict[str, dict[str, dict]] = {}
    for cat in ("Heritage", "Attributes", "Talent", "Skills", "Resources"):
        table[cat] = {}
        for letter in "ABCDE":
            row = priority_value(cat, letter)
            mets = [m for m in (row.get("metatypes") or []) if m["name"] in CORE_METATYPES]
            table[cat][letter] = {
                "name": row.get("name"),
                "attribute_points": row.get("attribute_points"),
                "skill_points": row.get("skill_points"),
                "skill_group_points": row.get("skill_group_points"),
                "nuyen": row.get("nuyen"),
                "metatypes": mets,
                "talents": talent_options(letter) if cat == "Talent" else row.get("talents") or [],
            }
    return {
        "metatypes": raw["metatypes"],
        "skills": raw["skills"],
        "qualities": qualities,
        "cyberware": _public_ware(raw.get("cyberware") or {"grades": [], "items": []}),
        "bioware": _public_ware(raw.get("bioware") or {"grades": [], "items": []}),
        "powers": [
            {
                "id": p["id"],
                "name": p["name"],
                "points": p["points"],
                "levels": p["levels"],
                "maxlevels": p["maxlevels"],
                "extrapointcost": p["extrapointcost"],
                "source": p["source"],
                "page": p["page"],
                "select": p.get("select"),
                "required": list(p.get("required") or []),
                "adeptway": p.get("adeptway") or 0,
                "adeptwayrequires": list(p.get("adeptwayrequires") or []),
            }
            for p in raw.get("powers") or []
            if not p.get("hidden")
        ],
        "enhancements": [
            {
                "id": e["id"],
                "name": e["name"],
                "power": e.get("power"),
                "source": e.get("source"),
                "page": e.get("page"),
                "required": e.get("required") or {},
            }
            for e in raw.get("enhancements") or []
        ],
        "mentors": [
            {
                "id": m["id"],
                "name": m["name"],
                "source": m.get("source"),
                "page": m.get("page"),
                "advantage": m.get("advantage") or "",
            }
            for m in raw.get("mentors") or []
        ],
        "spells": [
            {
                "id": s["id"],
                "name": s["name"],
                "category": s.get("category"),
                "dv": s.get("dv"),
                "type": s.get("type"),
                "range": s.get("range"),
                "duration": s.get("duration"),
                "descriptor": s.get("descriptor"),
                "kind": s.get("kind") or "spell",
                "useskill": s.get("useskill") or "Spellcasting",
                "learnable": bool(s.get("learnable")),
                "required": [
                    name
                    for names in (s.get("required") or {}).values()
                    for name in names
                ],
                "source": s.get("source"),
                "page": s.get("page"),
            }
            for s in raw.get("spells") or []
        ],
        "traditions": [
            {
                "id": t["id"],
                "name": t["name"],
                "drain": t.get("drain") or "",
                "drain_attrs": list(t.get("drain_attrs") or []),
                "spirits": dict(t.get("spirits") or {}),
                "source": t.get("source"),
                "page": t.get("page"),
            }
            for t in raw.get("traditions") or []
        ],
        "spirits": [
            {
                "id": s["id"],
                "name": s["name"],
                "attributes": dict(s.get("attributes") or {}),
                "powers": list(s.get("powers") or []),
                "optionalpowers": list(s.get("optionalpowers") or []),
                "skills": list(s.get("skills") or []),
                "weaknesses": list(s.get("weaknesses") or []),
                "source": s.get("source"),
                "page": s.get("page"),
            }
            for s in raw.get("spirits") or []
        ],
        "complex_forms": [
            {
                "id": f["id"],
                "name": f["name"],
                "target": f.get("target") or "",
                "duration": f.get("duration") or "",
                "fv": f.get("fv") or "",
                "needs_extra": bool(f.get("needs_extra")),
                "required": [
                    name
                    for names in (f.get("required") or {}).values()
                    for name in names
                ],
                "source": f.get("source"),
                "page": f.get("page"),
            }
            for f in raw.get("complex_forms") or []
        ],
        "streams": [
            {
                "id": s["id"],
                "name": s["name"],
                "drain": s.get("drain") or "",
                "drain_attrs": list(s.get("drain_attrs") or []),
                "sprites": list(s.get("sprites") or []),
                "source": s.get("source"),
                "page": s.get("page"),
            }
            for s in raw.get("streams") or []
        ],
        "sprites": [
            {
                "id": s["id"],
                "name": s["name"],
                "attributes": dict(s.get("attributes") or {}),
                "powers": list(s.get("powers") or []),
                "skills": list(s.get("skills") or []),
                "source": s.get("source"),
                "page": s.get("page"),
            }
            for s in raw.get("sprites") or []
        ],
        "foci": [
            {
                "id": f["id"],
                "name": f["name"],
                "maxrating": f.get("maxrating") or 6,
                "cost": f.get("cost") or "",
                "effect": f.get("effect") or "",
                "formula": (
                    {
                        "id": (f.get("formula") or {}).get("id"),
                        "name": (f.get("formula") or {}).get("name"),
                        "cost": (f.get("formula") or {}).get("cost") or "",
                    }
                    if f.get("formula")
                    else None
                ),
                "source": f.get("source"),
                "page": f.get("page"),
            }
            for f in raw.get("foci") or []
        ],
        "qi_focus": raw.get("qi_focus"),
        "armor": [
            {
                "id": a["id"],
                "name": a["name"],
                "category": a.get("category") or "Armor",
                "armor": a.get("armor") or "0",
                "armorcapacity": a.get("armorcapacity") or "",
                "avail": a.get("avail") or "",
                "cost": a.get("cost") or "0",
                "minrating": int(a.get("minrating") or 0),
                "maxrating": int(a.get("maxrating") or 0),
                "additive": bool(a.get("additive")),
                "addmodcategories": list(a.get("addmodcategories") or []),
                "source": a.get("source") or "",
                "page": a.get("page") or "",
            }
            for a in raw.get("armor") or []
        ],
        "armor_mods": [
            {
                "id": a["id"],
                "name": a["name"],
                "category": a.get("category") or "General",
                "armor": a.get("armor") or "0",
                "armorcapacity": a.get("armorcapacity") or "",
                "avail": a.get("avail") or "",
                "cost": a.get("cost") or "0",
                "minrating": int(a.get("minrating") or 0),
                "maxrating": int(a.get("maxrating") or 0),
                "purchasable": bool(a.get("purchasable")),
                "unique": a.get("unique") or "",
                "required_names": list(a.get("required_names") or []),
                "required_mods": list(a.get("required_mods") or []),
                "source": a.get("source") or "",
                "page": a.get("page") or "",
            }
            for a in raw.get("armor_mods") or []
            if a.get("purchasable")
        ],
        "weapons": [
            {
                "id": w["id"],
                "name": w["name"],
                "category": w.get("category") or "",
                "type": w.get("type") or "",
                "weapon_type": w.get("weapon_type") or "",
                "accuracy": w.get("accuracy") or "",
                "reach": w.get("reach") or "",
                "damage": w.get("damage") or "",
                "ap": w.get("ap") or "",
                "mode": w.get("mode") or "",
                "ammo": w.get("ammo") or "",
                "conceal": w.get("conceal") or "",
                "mounts": list(w.get("mounts") or []),
                "avail": w.get("avail") or "",
                "cost": w.get("cost") or "0",
                "source": w.get("source") or "",
                "page": w.get("page") or "",
                "from_gear": bool(w.get("from_gear")),
                "add_gear_id": w.get("add_gear_id") or "",
            }
            for w in raw.get("weapons") or []
            if not w.get("hidden")
        ],
        "weapon_accessories": [
            {
                "id": a["id"],
                "name": a["name"],
                "mounts": list(a.get("mounts") or []),
                "avail": a.get("avail") or "",
                "cost": a.get("cost") or "0",
                "purchasable": bool(a.get("purchasable")),
                "accuracy": a.get("accuracy") or "",
                "rc": a.get("rc") or "",
                "minrating": int(a.get("minrating") or 0),
                "maxrating": int(a.get("maxrating") or 0),
                "required": a.get("required") or {},
                "forbidden": a.get("forbidden") or {},
                "specialmodification": bool(a.get("specialmodification")),
                "special_modification_cost": int(a.get("special_modification_cost") or 0),
                "source": a.get("source") or "",
                "page": a.get("page") or "",
            }
            for a in raw.get("weapon_accessories") or []
        ],
        "commlinks": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "Commlinks",
                "cost": c.get("cost") or "0",
                "avail": c.get("avail") or "",
                "minrating": int(c.get("minrating") or 0),
                "maxrating": int(c.get("maxrating") or 0),
                "devicerating": c.get("devicerating") or "0",
                "dataprocessing": c.get("dataprocessing") or "0",
                "firewall": c.get("firewall") or "0",
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("commlinks") or []
        ],
        "cyberdecks": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "Cyberdecks",
                "cost": c.get("cost") or "0",
                "avail": c.get("avail") or "",
                "minrating": int(c.get("minrating") or 0),
                "maxrating": int(c.get("maxrating") or 0),
                "devicerating": c.get("devicerating") or "0",
                "attack": c.get("attack") or "0",
                "sleaze": c.get("sleaze") or "0",
                "dataprocessing": c.get("dataprocessing") or "0",
                "firewall": c.get("firewall") or "0",
                "attributearray": c.get("attributearray") or "",
                "programs": c.get("programs") or "0",
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("cyberdecks") or []
        ],
        "rccs": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "Rigger Command Consoles",
                "cost": c.get("cost") or "0",
                "avail": c.get("avail") or "",
                "minrating": int(c.get("minrating") or 0),
                "maxrating": int(c.get("maxrating") or 0),
                "devicerating": c.get("devicerating") or "0",
                "dataprocessing": c.get("dataprocessing") or "0",
                "firewall": c.get("firewall") or "0",
                "programs": c.get("programs") or "0",
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("rccs") or []
        ],
        "optics": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "",
                "cost": c.get("cost") or "0",
                "avail": c.get("avail") or "",
                "minrating": int(c.get("minrating") or 0),
                "maxrating": int(c.get("maxrating") or 0),
                "capacity": c.get("capacity") or "",
                "plugin": bool(c.get("plugin")),
                "requireparent": bool(c.get("requireparent")),
                "addoncategories": list(c.get("addoncategories") or []),
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("optics") or []
        ],
        "programs": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "",
                "cost": c.get("cost") or "0",
                "avail": c.get("avail") or "",
                "minrating": int(c.get("minrating") or 0),
                "maxrating": int(c.get("maxrating") or 0),
                "requireparent": True,
                "program_host": c.get("program_host") or "cyberdecks",
                "needs_extra": bool(c.get("needs_extra")),
                "extra_kind": c.get("extra_kind") or "",
                "extra_options": gear_extra_options(c, raw.get("skills")),
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("programs") or []
        ],
        "apps": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "",
                "cost": c.get("cost") or "0",
                "avail": c.get("avail") or "",
                "minrating": int(c.get("minrating") or 0),
                "maxrating": int(c.get("maxrating") or 0),
                "requireparent": True,
                "needs_extra": bool(c.get("needs_extra")),
                "extra_kind": c.get("extra_kind") or "",
                "extra_options": gear_extra_options(c, raw.get("skills")),
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("apps") or []
        ],
        "sensors": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "",
                "cost": c.get("cost") or "0",
                "avail": c.get("avail") or "",
                "minrating": int(c.get("minrating") or 0),
                "maxrating": int(c.get("maxrating") or 0),
                "capacity": c.get("capacity") or "",
                "plugin": bool(c.get("plugin")),
                "requireparent": bool(c.get("requireparent")),
                "addoncategories": list(c.get("addoncategories") or []),
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("sensors") or []
        ],
        "gear": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "",
                "cost": c.get("cost") or "0",
                "avail": c.get("avail") or "",
                "minrating": int(c.get("minrating") or 0),
                "maxrating": int(c.get("maxrating") or 0),
                "capacity": c.get("capacity") or "",
                "plugin": bool(c.get("plugin")),
                "requireparent": bool(c.get("requireparent")),
                "addoncategories": list(c.get("addoncategories") or []),
                "required_names": list(c.get("required_names") or []),
                "required_categories": list(c.get("required_categories") or []),
                "ammo_weapon_types": list(c.get("ammo_weapon_types") or []),
                "costfor": int(c.get("costfor") or 0),
                "weapon_details": c.get("weapon_details") or "",
                "add_weapon": c.get("add_weapon") or "",
                "add_weapon_id": c.get("add_weapon_id") or "",
                "needs_extra": bool(c.get("needs_extra")),
                "extra_kind": c.get("extra_kind") or "",
                "extra_options": gear_extra_options(c, raw.get("skills")),
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("gear") or []
        ],
        "drones": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "",
                "handling": c.get("handling") or "",
                "speed": c.get("speed") or "",
                "accel": c.get("accel") or "",
                "body": c.get("body") or "",
                "armor": c.get("armor") or "",
                "pilot": c.get("pilot") or "",
                "sensor": c.get("sensor") or "",
                "seats": c.get("seats") or "",
                "avail": c.get("avail") or "",
                "cost": c.get("cost") or "0",
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("drones") or []
        ],
        "vehicles": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "",
                "handling": c.get("handling") or "",
                "speed": c.get("speed") or "",
                "accel": c.get("accel") or "",
                "body": c.get("body") or "",
                "armor": c.get("armor") or "",
                "pilot": c.get("pilot") or "",
                "sensor": c.get("sensor") or "",
                "seats": c.get("seats") or "",
                "avail": c.get("avail") or "",
                "cost": c.get("cost") or "0",
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("vehicles") or []
        ],
        "vehicle_mods": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "",
                "cost": c.get("cost") or "0",
                "slots": c.get("slots") or "0",
                "avail": c.get("avail") or "",
                "minrating": int(c.get("minrating") or 0),
                "maxrating": int(c.get("maxrating") or 0),
                "purchasable": bool(c.get("purchasable")),
                "required": c.get("required") or {},
                "forbidden": c.get("forbidden") or {},
                "capacity": c.get("capacity") or "",
                "subsystems": list(c.get("subsystems") or []),
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("vehicle_mods") or []
            if c.get("purchasable")
        ],
        "weapon_mounts": [
            {
                "id": c["id"],
                "name": c["name"],
                "category": c.get("category") or "",
                "cost": c.get("cost") or "0",
                "slots": c.get("slots") or "0",
                "avail": c.get("avail") or "",
                "required": c.get("required") or {},
                "source": c.get("source") or "",
                "page": c.get("page") or "",
            }
            for c in raw.get("weapon_mounts") or []
        ],
        "lifestyles": [
            {
                "id": ls["id"],
                "name": ls["name"],
                "cost": int(ls.get("cost") or 0),
                "dice": int(ls.get("dice") or 0),
                "lp": int(ls.get("lp") or 0),
                "multiplier": int(ls.get("multiplier") or 100),
                "increment": ls.get("increment") or "month",
                "freegrids": [
                    {"name": str(g.get("name") or ""), "select": str(g.get("select") or "")}
                    for g in (ls.get("freegrids") or [])
                ],
                "source": ls.get("source") or "",
                "page": ls.get("page") or "",
            }
            for ls in raw.get("lifestyles") or []
        ],
        "lifestyle_qualities": [
            {
                "id": q["id"],
                "name": q["name"],
                "category": q.get("category") or "",
                "lp": int(q.get("lp") or 0),
                "cost": int(q.get("cost") or 0),
                "multiplier": int(q.get("multiplier") or 0),
                "allowed": list(q.get("allowed") or []),
                "allow_multiple": bool(q.get("allow_multiple")),
                "needs_extra": bool(q.get("needs_extra")),
                "source": q.get("source") or "",
                "page": q.get("page") or "",
            }
            for q in raw.get("lifestyle_qualities") or []
        ],
        "drugs": [
            {
                "id": item["id"],
                "name": item["name"],
                "category": item.get("category") or "",
                "cost": item.get("cost") or "0",
                "avail": item.get("avail") or "",
                "addoncategories": list(item.get("addoncategories") or []),
                "source": item.get("source") or "",
                "page": item.get("page") or "",
            }
            for item in raw.get("drugs") or []
        ],
        "drug_grades": [
            {
                "id": item["id"],
                "name": item["name"],
                "cost": item.get("cost") or "0",
                "avail": item.get("avail") or "",
                "required_categories": list(item.get("required_categories") or []),
                "source": item.get("source") or "",
                "page": item.get("page") or "",
            }
            for item in raw.get("drug_grades") or []
        ],
        "martial_arts": [
            {
                "id": art["id"],
                "name": art["name"],
                "cost": int(art.get("cost") or 7),
                "techniques": list(art.get("techniques") or []),
                "source": art.get("source") or "",
                "page": art.get("page") or "",
                "is_quality": bool(art.get("is_quality")),
                "all_techniques": bool(art.get("all_techniques")),
                "spec_options": [
                    {"skill": skill, "spec": spec}
                    for node in (art.get("bonus") or [])
                    if node.get("tag") == "addskillspecializationoption"
                    for skill in [str((node.get("fields") or {}).get("skill") or "").strip()]
                    for spec in [str((node.get("fields") or {}).get("spec") or "").strip()]
                    if skill and spec
                ],
            }
            for art in raw.get("martial_arts") or []
            if not art.get("is_quality")
        ],
        "martial_art_techniques": [
            {
                "id": tech["id"],
                "name": tech["name"],
                "source": tech.get("source") or "",
                "page": tech.get("page") or "",
            }
            for tech in raw.get("martial_art_techniques") or []
        ],
        "metamagics": [
            {
                "id": item["id"],
                "name": item["name"],
                "adept": bool(item.get("adept")),
                "magician": bool(item.get("magician")),
                "repeatable": bool(item.get("repeatable")),
                "required": [
                    name
                    for names in (item.get("required") or {}).values()
                    for name in names
                ],
                "source": item.get("source") or "",
                "page": item.get("page") or "",
            }
            for item in raw.get("metamagics") or []
        ],
        "magic_arts": [
            {
                "id": item["id"],
                "name": item["name"],
                "source": item.get("source") or "",
                "page": item.get("page") or "",
            }
            for item in raw.get("magic_arts") or []
        ],
        "echoes": [
            {
                "id": item["id"],
                "name": item["name"],
                "max_takes": item.get("max_takes"),
                "needs_extra": bool(item.get("needs_extra")),
                "source": item.get("source") or "",
                "page": item.get("page") or "",
            }
            for item in raw.get("echoes") or []
        ],
        "priority_table": table,
        "karma_talents": [
            {
                "name": t["name"],
                "label": t.get("label") or t["name"],
                "magic": int(t.get("magic") or 0),
                "resonance": int(t.get("resonance") or 0),
            }
            for t in all_talent_options()
        ],
        "translations": raw["translations"],
        "ui_strings": raw["ui_strings"],
    }


def _public_ware(block: dict) -> dict:
    grades = [g for g in block.get("grades") or [] if g.get("core")]
    items = []
    for w in block.get("items") or []:
        items.append(
            {
                "id": w["id"],
                "name": w["name"],
                "category": w["category"],
                "ess": w["ess"],
                "cost": w["cost"],
                "capacity": w.get("capacity") or "",
                "minrating": w["minrating"],
                "maxrating": w["maxrating"],
                "minrating_expr": w.get("minrating_expr") or str(w["minrating"]),
                "maxrating_expr": w.get("maxrating_expr") or str(w["maxrating"]),
                "forcegrade": w.get("forcegrade"),
                "plugin": w.get("plugin", False),
                "requireparent": bool(w.get("requireparent")),
                "addtoparentess": bool(w.get("addtoparentess")),
                "formula_rating": bool(w.get("formula_rating")),
                "allow_subsystems": list(w.get("allow_subsystems") or []),
                "has_wireless": bool(w.get("wirelessbonus")),
                "bannedgrades": list(w.get("bannedgrades") or []),
                "required": w.get("required") or {"bioware": [], "cyberware": [], "metatype": [], "quality": []},
                "required_parent_names": list(w.get("required_parent_names") or []),
                "limbslot": w.get("limbslot"),
                "selectside": bool(w.get("selectside")),
                "source": w.get("source"),
                "page": w.get("page"),
            }
        )
    return {"grades": grades, "items": items}
