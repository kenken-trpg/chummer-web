from __future__ import annotations

import json
import uuid
from pathlib import Path

from .data_loader import catalog
from .engine import (
    ADEPT_TALENTS,
    MAG_TALENTS,
    compute,
    default_attributes,
    find_metatype,
    is_way_quality,
    priority_value,
    resolve_talent,
    sanitize_quality_ids,
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
    state = CharacterState(
        id=str(uuid.uuid4()),
        name=payload.name,
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
    talent = resolve_talent(data["priorities"]["Talent"], data.get("talent"))
    data["talent"] = talent["name"]
    key, start = talent_special(talent)
    attrs = dict(data.get("attributes") or {})
    attrs["MAG"] = start if key == "MAG" else 0
    attrs["RES"] = start if key == "RES" else 0
    data["attributes"] = attrs


def update_character(cid: str, patch: CharacterPatch) -> CharacterState:
    state = get_character(cid)
    data = state.model_dump()
    old_letter = state.priorities.Talent
    old_talent = state.talent
    updates = patch.model_dump(exclude_unset=True)
    if "priorities" in updates and updates["priorities"] is not None:
        data["priorities"] = updates.pop("priorities")
    if "options" in updates and updates["options"] is not None:
        current = dict(data.get("options") or {})
        current.update(updates.pop("options"))
        data["options"] = current
    data.update({k: v for k, v in updates.items() if v is not None})
    if "quality_ids" in updates:
        data["quality_ids"], _ = sanitize_quality_ids(list(data.get("quality_ids") or []))
    if patch.metatype or patch.metavariant is not None:
        meta = find_metatype(data["metatype"], data.get("metavariant"))
        data["attributes"] = default_attributes(meta)
    talent = resolve_talent(data["priorities"]["Talent"], data.get("talent"))
    data["talent"] = talent["name"]
    if old_letter != data["priorities"]["Talent"] or old_talent != data["talent"] or patch.metatype:
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
                "source": s.get("source"),
                "page": s.get("page"),
            }
            for s in raw.get("spells") or []
        ],
        "qi_focus": raw.get("qi_focus"),
        "priority_table": table,
        "translations": raw["translations"],
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
                "limbslot": w.get("limbslot"),
                "selectside": bool(w.get("selectside")),
                "source": w.get("source"),
                "page": w.get("page"),
            }
        )
    return {"grades": grades, "items": items}
