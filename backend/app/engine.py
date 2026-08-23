from __future__ import annotations

import math
import re
from typing import Any

from .data_loader import PHYSICAL_ATTRS, catalog, eval_formula
from .improvements import _as_int, apply_bonus_nodes, collect_effects, substitute_rating
from .models import CharacterOptions, CharacterState, CyberwareInstall, Priorities, QiFocusInstall

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
MENTOR_SPIRIT_ID = "ced3fecf-2277-4b20-b1e0-894162ca9ae2"
QI_FOCUS_NAME = "Qi Focus"
DRAIN_MINIMUM = 2


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
            {"name": "Mundane", "label": "Mundane", "value": 0, "magic": 0, "resonance": 0, "quality": ""},
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
        return {"name": "Mundane", "label": "Mundane", "value": 0, "magic": 0, "resonance": 0}
    found = next((t for t in options if t["name"] == current), None)
    if found:
        return found
    return next((t for t in options if t["name"] != "Mundane"), options[0])


def _effective_attr_spec(
    attrs_spec: dict[str, dict[str, int | float]],
    special_key: str | None,
    talent_start: int,
) -> dict[str, dict[str, int | float]]:
    out = {key: dict(spec) for key, spec in attrs_spec.items()}
    if special_key == "MAG":
        out["MAG"]["min"] = max(talent_start, 1)
        out["RES"]["min"] = 0
        out["RES"]["max"] = 0
    elif special_key == "RES":
        out["RES"]["min"] = max(talent_start, 1)
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


def spell_drain_value(formula: str, force: int) -> int | None:
    raw = (formula or "").strip()
    if not raw or raw.lower() == "special":
        return None
    if re.fullmatch(r"\d+", raw):
        return int(raw)
    match = re.fullmatch(r"F\s*([+-]\s*\d+)?", raw, re.I)
    if not match:
        return None
    mod = int(re.sub(r"\s+", "", match.group(1))) if match.group(1) else 0
    return max(DRAIN_MINIMUM, int(force) + mod)


def spell_cast_info(
    spell_name: str,
    force: int | None,
    mag: int,
    wil: int,
    intuition: int,
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
        "resist": int(wil) + int(intuition),
        "resist_attrs": "WIL+INT",
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
    return eval_formula(raw, rating, default=0.0)


def _cascade_orphans(items: list[CyberwareInstall]) -> list[CyberwareInstall]:
    ids = {item.id for item in items}
    keep = [item for item in items if not item.parent_id or item.parent_id in ids]
    if len(keep) == len(items):
        return keep
    return _cascade_orphans(keep)


def ensure_subsystems(state: CharacterState) -> CharacterState:
    state.cyberware = ensure_sides("cyberware", _ensure_kind_subsystems("cyberware", state.cyberware))
    state.bioware = ensure_sides("bioware", _ensure_kind_subsystems("bioware", state.bioware))
    return state


def _ensure_kind_subsystems(kind: str, items: list[CyberwareInstall]) -> list[CyberwareInstall]:
    items = _cascade_orphans(list(items))
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
                "source": ware.get("source"),
                "bonus": nodes,
                "ess_to_parent": ess_base if add_to_parent else 0.0,
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
        "source": item.get("source"),
    }


KNOWLEDGE_CATEGORIES = {"Academic", "Interest", "Language", "Professional", "Street"}


def resolve_skill_mods(
    skills_data: dict[str, Any],
    effects: dict[str, Any],
    knowledge_ratings: dict[str, int],
) -> dict[str, Any]:
    active = list(skills_data.get("skills") or [])
    knowledge = list(skills_data.get("knowledge") or [])
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
        return [item["name"] for item in catalog().get("spells") or []]
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
            if node.get("tag") != "freequality":
                continue
            child_id = str(node.get("value") or "").strip()
            if child_id and child_id not in seen:
                free_ids.add(child_id)
                pending.append(child_id)
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
        spell = spell_cast_info(extra, inst.force, mag, wil, intuition) if kind == "spell" and extra else None
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


def validate_priorities(p: Priorities) -> list[str]:
    letters = [p.Heritage, p.Attributes, p.Talent, p.Skills, p.Resources]
    errors = []
    if sorted(x.upper() for x in letters) != ["A", "B", "C", "D", "E"]:
        errors.append("優先度 A〜E を各カテゴリに1つずつ割り当ててください")
    return errors


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


def compute(state: CharacterState) -> CharacterState:
    data = catalog()
    errors = validate_priorities(state.priorities)
    meta = find_metatype(state.metatype, state.metavariant)
    attrs_spec = meta["attributes"]
    ensure_subsystems(state)
    errors.extend(_side_conflicts("cyberware", state.cyberware))
    errors.extend(_side_conflicts("bioware", state.bioware))
    warnings = _clamp_ware_grades("cyberware", state.cyberware)
    warnings.extend(_clamp_ware_grades("bioware", state.bioware))
    installed_names = {
        "cyberware": _installed_ware_names("cyberware", state.cyberware),
        "bioware": _installed_ware_names("bioware", state.bioware),
    }
    warnings.extend(_required_warnings("cyberware", state.cyberware, installed_names, state.metatype, state.metavariant))
    warnings.extend(_required_warnings("bioware", state.bioware, installed_names, state.metatype, state.metavariant))

    talent = resolve_talent(state.priorities.Talent, state.talent)
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
    cyber_installed = resolve_ware("cyberware", state.cyberware, attrs_spec)
    bio_installed = resolve_ware("bioware", state.bioware, attrs_spec)
    installed = cyber_installed + bio_installed
    for item in installed:
        sources.append((item["name"], item.get("bonus") or []))
    effects = collect_effects(sources)
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
    enabled = set(effects["enabled_tabs"])
    if special_key:
        enabled.add(special_key)

    ess_start = float(attrs_spec.get("ESS", {}).get("max") or 6)
    ess_lost_cyber = round(sum(float(item["essence"]) for item in cyber_installed), 4)
    ess_lost_bio = round(sum(float(item["essence"]) for item in bio_installed), 4)
    ess_lost = round(ess_lost_cyber + ess_lost_bio, 4)
    ess = max(0.0, round(ess_start - ess_lost, 2))
    mag_penalty = int(math.ceil(ess_lost - 1e-9)) if ess_lost > 0 else 0

    ratings: dict[str, int] = {}
    for key, spec in attrs_spec.items():
        racial_min = int(spec["min"])
        racial_max = int(spec["max"])
        raw = int(state.attributes.get(key, racial_min))
        if key == "MAG":
            if special_key == "MAG":
                floor = max(talent_start, 1)
                raw = max(floor, min(racial_max, raw))
                raw = max(0, raw - mag_penalty)
            else:
                raw = 0
        elif key == "RES":
            if special_key == "RES":
                floor = max(talent_start, 1)
                raw = max(floor, min(racial_max, raw))
                raw = max(0, raw - mag_penalty)
            else:
                raw = 0
        elif key == "ESS":
            raw = int(ess)
        else:
            raw = max(racial_min, min(racial_max, raw))
        ratings[key] = raw

    quality_names = {q["name"] for q in qualities}
    qi = resolve_qi_foci(
        state,
        talent["name"],
        int(ratings.get("MAG") or 0),
        data["skills"],
        list(effects.get("focus_binding") or []),
    )
    warnings.extend(qi["warnings"])
    errors.extend(qi["errors"])
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

    attr_points = int(attr_row.get("attribute_points") or 0)
    skill_points = int(skill_row.get("skill_points") or 0)
    group_points = int(skill_row.get("skill_group_points") or 0)
    nuyen_pool = int(res_row.get("nuyen") or 0)
    nuyen_spent = sum(int(item["nuyen"]) for item in installed) + int(qi.get("nuyen") or 0)
    nuyen = nuyen_pool - nuyen_spent

    skill_spent = 0
    group_spent = 0
    skill_totals: dict[str, int] = {}
    for group, rating in state.skill_groups.items():
        rating = max(0, min(6, int(rating)))
        group_spent += rating
        for s in data["skills"]["skills"]:
            if s.get("skillgroup") == group:
                skill_totals[s["name"]] = max(skill_totals.get(s["name"], 0), rating)
    tentative = dict(skill_totals)
    for name, rating in state.skills.items():
        tentative[name] = max(tentative.get(name, 0), max(0, min(7, int(rating))))
    skill_picks = resolve_skill_picks(state, data["skills"], tentative)
    warnings.extend(skill_picks["warnings"])
    for name, rating in state.skills.items():
        cap = 6 + int(skill_picks["skill_max_bonus"].get(name, 0))
        rating = max(0, min(cap, int(rating)))
        base = skill_totals.get(name, 0)
        extra = max(0, rating - base)
        skill_spent += extra
        skill_totals[name] = max(base, rating)
    know_spent = sum(max(0, min(6, int(v))) for v in state.knowledge_skills.values())
    skill_mods = resolve_skill_mods(data["skills"], effects, state.knowledge_skills)
    for name, bonus in skill_picks["skill_bonus"].items():
        skill_mods["skill_bonus"][name] = int(skill_mods["skill_bonus"].get(name, 0)) + int(bonus)
    for name, notes in skill_picks["skill_bonus_notes"].items():
        existing = skill_mods["skill_bonus_notes"].setdefault(name, [])
        for note in notes:
            if note not in existing:
                existing.append(note)

    karma_from_q = sum(
        q["karma"]
        for q in qualities
        if not q.get("onlyprioritygiven") and q["id"] not in free_quality_ids
    )
    mystic_karma = int(state.mystic_pp) * MYSTIC_PP_KARMA
    extra_adept_karma = int(enhancements.get("karma") or 0) + int(qi.get("karma") or 0)
    # Priority chargen: metatypes.xml <karma> is for Karma/Sum-to-Ten, not Priority.
    # Heritage table <karma> is an extra cost for some metavariants / rare races.
    heritage_karma_cost = extra_karma
    karma_pool = 25
    karma_spent = karma_from_q + heritage_karma_cost + mystic_karma + extra_adept_karma
    karma_left = karma_pool - karma_spent

    bod = total["BOD"]
    agi = total["AGI"]
    rea = total["REA"]
    stre = total["STR"]
    wil = total["WIL"]
    logi = total["LOG"]
    intuition = total["INT"]
    cha = total["CHA"]

    physical_limit = _ceil_div((bod * 2 + agi + rea + stre) / 3) + int(effects.get("limit_physical") or 0)
    mental_limit = _ceil_div((logi * 2 + intuition + wil) / 3) + int(effects.get("limit_mental") or 0)
    social_limit = _ceil_div((cha * 2 + wil + ess) / 3) + int(effects.get("limit_social") or 0)
    cm_phys = 8 + _ceil_div(bod / 2) + effects["cm_physical"]
    cm_stun = 8 + _ceil_div(wil / 2) + effects["cm_stun"]
    initiative = rea + intuition + effects["initiative"]
    initiative_dice = 1 + int(effects.get("initiative_dice") or 0)

    walk = meta.get("walk") or "2/1/0"
    run = meta.get("run") or "4/0/0"

    at_six = [n for n, r in skill_totals.items() if r >= 6]
    if len(at_six) > 1:
        errors.append("作成時にレーティング6のスキルは1つまでです")
    if spent_physical > attr_points:
        errors.append(f"属性点が不足しています（使用 {spent_physical} / 上限 {attr_points}）")
    if spent_special > special_from_meta:
        errors.append(f"特殊属性点が不足しています（使用 {spent_special} / 上限 {special_from_meta}）")
    if skill_spent > skill_points:
        errors.append(f"スキル点が不足しています（使用 {skill_spent} / 上限 {skill_points}）")
    if group_spent > group_points:
        errors.append(f"スキルグループ点が不足しています（使用 {group_spent} / 上限 {group_points}）")
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

    allowed = {e["name"] for e in heritage_options(state.priorities.Heritage)}
    if allowed and state.metatype not in allowed:
        errors.append(f"{state.metatype} はこの優先度のメタタイプに含まれません")

    state.attributes = ratings
    state.derived = {
        "errors": errors,
        "warnings": warnings,
        "totals": total,
        "limits": {
            "physical": physical_limit,
            "mental": mental_limit,
            "social": social_limit,
        },
        "condition_monitor": {"physical": cm_phys, "stun": cm_stun},
        "initiative": {"value": initiative, "dice": initiative_dice},
        "movement": {"walk": walk, "run": run, "sprint": meta.get("sprint") or "2/1/0"},
        "essence": ess,
        "essence_lost": ess_lost,
        "essence_lost_cyber": ess_lost_cyber,
        "essence_lost_bio": ess_lost_bio,
        "armor": effects["armor"],
        "nuyen": nuyen,
        "nuyen_spent": nuyen_spent,
        "karma": {"pool": karma_pool, "spent": karma_spent, "remaining": karma_left},
        "power_points": {"used": power_spent, "max": power_pool},
        "adept_powers": adept["public"],
        "mystic_pp": state.mystic_pp,
        "way_discount": {"used": adept.get("discount_used") or 0, "max": adept.get("discount_max") or 0},
        "mentor": mentor.get("public"),
        "needs_mentor": needs_mentor,
        "qi_foci": qi.get("public") or [],
        "enhancements": enhancements.get("public") or [],
        "damage_resistance": int(effects.get("damage_resistance") or 0),
        "unarmed_dv": int(effects.get("unarmed_dv") or 0),
        "unarmed_physical": bool(effects.get("unarmed_physical")),
        "unlock_skills": list(effects.get("unlock_skills") or []),
        "points": {
            "attributes": {"used": spent_physical, "max": attr_points},
            "special": {"used": spent_special, "max": special_from_meta},
            "skills": {"used": skill_spent, "max": skill_points},
            "skill_groups": {"used": group_spent, "max": group_points},
            "knowledge": {"used": know_spent, "max": max(intuition, 1) * 2 + logi},
        },
        "skill_totals": skill_totals,
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
            "attributes": _effective_attr_spec(attrs_spec, special_key, talent_start),
            "source": meta.get("source"),
        },
        "translations": {k: data["translations"].get(k, k) for k in [state.metatype, state.metavariant or ""]},
    }
    return state
