"""Quality resolution: gathering the chosen/free qualities, the
player-pick ("extra") inspectors, the bonus binders driven by ``compute``
(Matrix action dice pools, select-power slots, free-power grants), the
requirement-context builder and the quality-level selectside validators.

Imports only ``re`` / already-extracted engine modules / models — never
back into ``app.engine`` — so the import graph stays a DAG. ``app.engine``
re-exports the names ``store.py`` needs (``is_way_quality`` /
``sanitize_quality_ids``) plus everything ``compute`` calls.
"""

from __future__ import annotations

import re
from typing import Any

from ..models import CharacterState
from .constants import (
    _SIDE_JA,
    _SLOT_JA,
    QUALITY_ADDSPIRIT_EXTRA_MARKER,
    QUALITY_CONTACT_EXTRA_SUFFIX,
    QUALITY_SPIRIT_CATEGORY_EXTRA_SUFFIX,
    _normalize_side,
)
from .lookups import _item_by_id, _power_by_name, _quality_by_id
from .priority import talent_special


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
    counts: dict[str, int] = {}
    limited: list[str] = []
    for qid in kept:
        spec = _quality_by_id(qid)
        if not spec:
            continue
        max_takes = spec.get("max_takes")
        taken = counts.get(qid, 0)
        if max_takes is not None and taken >= int(max_takes):
            removed.append(spec["name"])
            continue
        counts[qid] = taken + 1
        limited.append(qid)
    return limited, removed


def quality_needs_extra(spec: dict[str, Any]) -> bool:
    return bool(spec.get("needs_extra")) or any(
        node.get("tag")
        in {
            "selecttext",
            "selectattributes",
            "skillgroupdisablechoice",
            "selectquality",
            "selectside",
            "actiondicepool",
            "selectexpertise",
        }
        or (
            node.get("tag") == "weaponcategorydv"
            and bool(str(((node.get("field_attrs") or {}).get("selectskill") or {}).get("limittoskill") or "").strip())
        )
        or (
            node.get("tag") == "weaponskillaccuracy"
            and (
                "selectskill" in (node.get("fields") or {}) or bool((node.get("field_attrs") or {}).get("selectskill"))
            )
            and not str((node.get("fields") or {}).get("name") or "").strip()
        )
        for node in (spec.get("bonus") or [])
    )


def _quality_has_actiondicepool(spec: dict[str, Any]) -> bool:
    return any(node.get("tag") == "actiondicepool" for node in (spec.get("bonus") or []))


def _quality_needs_spell_category(spec: dict[str, Any]) -> bool:
    return any(
        node.get("tag") == "limitspellcategory" and not str(node.get("value") or "").strip()
        for node in (spec.get("bonus") or [])
    )


def _quality_needs_spirit_category(spec: dict[str, Any]) -> bool:
    for node in spec.get("bonus") or []:
        if node.get("tag") != "limitspiritcategory":
            continue
        fields = node.get("fields") or {}
        if fields.get("spirit"):
            continue
        if not str(node.get("value") or "").strip():
            return True
    return False


def _quality_has_selectside(spec: dict[str, Any]) -> bool:
    return any(node.get("tag") == "selectside" for node in (spec.get("bonus") or []))


def _quality_limb_slot(spec: dict[str, Any]) -> str | None:
    """Infer limb slot for quality-level selectside (e.g. Crystal Limb)."""
    if not _quality_has_selectside(spec):
        return None
    name = str(spec.get("name") or "").lower()
    if "arm" in name:
        return "arm"
    if "leg" in name:
        return "leg"
    if "hand" in name:
        return "hand"
    if "foot" in name:
        return "foot"
    return None


def _quality_extra_key_owned(key: str, owned: set[str]) -> bool:
    if key in owned:
        return True
    if key.endswith(QUALITY_CONTACT_EXTRA_SUFFIX):
        return key[: -len(QUALITY_CONTACT_EXTRA_SUFFIX)] in owned
    if key.endswith(QUALITY_SPIRIT_CATEGORY_EXTRA_SUFFIX):
        return key[: -len(QUALITY_SPIRIT_CATEGORY_EXTRA_SUFFIX)] in owned
    if QUALITY_ADDSPIRIT_EXTRA_MARKER in key:
        return key.split(QUALITY_ADDSPIRIT_EXTRA_MARKER, 1)[0] in owned
    return False


def bind_action_dice_pools(
    effects: dict[str, Any],
    qualities: list[dict[str, Any]],
    state: CharacterState,
) -> list[dict[str, Any]]:
    """Attach chosen Matrix action names from quality_extras onto actiondicepool rows."""
    by_name = {q["name"]: q for q in qualities}
    extras = state.quality_extras or {}
    out: list[dict[str, Any]] = []
    for row in effects.get("action_dice_pools") or []:
        item = {
            "category": str(row.get("category") or ""),
            "name": str(row.get("name") or "").strip(),
            "bonus": int(row.get("bonus") or 0),
            "source": str(row.get("source") or ""),
        }
        if not item["name"] and row.get("needs_action"):
            spec = by_name.get(item["source"])
            if spec:
                item["name"] = str(extras.get(spec["id"]) or "").strip()
        if item["bonus"] and item["name"]:
            out.append(item)
    effects["action_dice_pools"] = out
    return out


def bind_select_powers(
    effects: dict[str, Any],
    qualities: list[dict[str, Any]],
    state: CharacterState,
    warnings: list[str],
    mentor_name: str = "",
) -> None:
    by_name = {q["name"]: q for q in qualities}
    mentor_extras = state.mentor_extras or {}
    quality_extras = state.quality_extras or {}
    mentor_prefix = f"{mentor_name}: " if mentor_name else ""

    for slot in effects.get("select_power_slots") or []:
        source = str(slot.get("source") or "").strip()
        options = list(slot.get("options") or [])
        rating = max(1, int(slot.get("rating") or 1))
        open_select = bool(slot.get("open_select"))
        if not options and not open_select:
            continue
        picked = ""
        if mentor_prefix and source.startswith(mentor_prefix):
            choice_name = source[len(mentor_prefix) :]
            picked = str(mentor_extras.get(choice_name) or "").strip()
        elif open_select:
            for inst in state.gear or []:
                spec = _item_by_id("gear", inst.gear_id)
                if not spec or str(spec.get("name") or "") != source:
                    continue
                picked = str(inst.extra or "").strip()
                rating = max(1, int(inst.rating or 1))
                break
        else:
            spec = by_name.get(source)
            if spec:
                picked = str(quality_extras.get(spec["id"]) or "").strip()
        if not picked:
            warnings.append(f"{source} のパワーを選んでください")
            continue
        if options and picked not in options:
            warnings.append(f"{source} に {picked} は選べません")
            continue
        if open_select and not _power_by_name(picked):
            warnings.append(f"{source} のパワー {picked} が見つかりません")
            continue
        effects["grant_powers"].append(
            {
                "source": source,
                "name": picked,
                "rating": rating,
                "extra": "",
            }
        )


def free_powers_from_grants(
    effects: dict[str, Any],
    warnings: list[str],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in effects.get("grant_powers") or []:
        name = str(row.get("name") or "").strip()
        source = str(row.get("source") or "").strip()
        spec = _power_by_name(name)
        if not spec:
            warnings.append(f"{source} のパワー {name} が見つかりません")
            continue
        out.append(
            {
                "power_id": spec["id"],
                "name": spec["name"],
                "rating": max(1, int(row.get("rating") or 1)),
                "extra": str(row.get("extra") or "").strip(),
                "source": source,
            }
        )
    return out


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


def resolve_quality_sides(
    qualities: list[dict[str, Any]],
    state: CharacterState,
    cyber_installed: list[dict[str, Any]],
    bio_installed: list[dict[str, Any]],
    errors: list[str],
) -> dict[str, str]:
    """Validate quality selectside extras; return quality_id → Left/Right."""
    chosen: dict[str, str] = {}
    occupied: dict[tuple[str, str], str] = {}
    for item in list(cyber_installed) + list(bio_installed):
        if item.get("parent_id") or not item.get("selectside"):
            continue
        side = _normalize_side(str(item.get("side") or ""))
        slot = str(item.get("limbslot") or "").lower()
        if side and slot:
            occupied[(slot, side)] = str(item.get("name") or "ウェア")

    extras = state.quality_extras or {}
    for spec in qualities:
        if not _quality_has_selectside(spec):
            continue
        raw = str(extras.get(spec["id"]) or "").strip()
        side = _normalize_side(raw)
        if raw and not side:
            errors.append(f"{spec['name']} の左右指定が不正です（Left / Right）")
            continue
        if not side:
            continue
        chosen[spec["id"]] = side
        slot = _quality_limb_slot(spec)
        if not slot:
            continue
        key = (slot, side)
        if key in occupied:
            slot_ja = _SLOT_JA.get(slot, slot)
            errors.append(
                f"{spec['name']}（{_SIDE_JA.get(side, side)}）は"
                f"{occupied[key]}と{_SIDE_JA.get(side, side)}の{slot_ja}が重複しています"
            )
            continue
        occupied[key] = spec["name"]
    # Normalize valid sides back into extras for persistence.
    if chosen:
        next_extras = dict(state.quality_extras or {})
        for qid, side in chosen.items():
            next_extras[qid] = side
        state.quality_extras = next_extras
    return chosen
