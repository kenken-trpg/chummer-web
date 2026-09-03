"""Quality resolution: gathering the chosen/free qualities, the
player-pick ("extra") inspectors, the bonus binders driven by ``compute``
(Matrix action dice pools, select-power slots, free-power grants), the
requirement-context builder and the quality-level selectside validators.

Imports only ``re`` / already-extracted engine modules / models — never
back into ``app.engine`` — so the import graph stays a DAG. ``app.engine``
re-exports the names ``characters.py`` / ``catalog_view.py`` need (``is_way_quality`` /
``sanitize_quality_ids``) plus everything ``compute`` calls.
"""

from __future__ import annotations

import re
from typing import Any

from ..improvements import EffectsDict, _as_int
from ..improvements.effect_rows import ActionDicePoolRow
from ..models import CharacterState
from .constants import (
    _SIDE_JA,
    _SLOT_JA,
    NEGATIVE_QUALITY_KARMA_CAP,
    POSITIVE_QUALITY_KARMA_CAP,
    QUALITY_ADDSPIRIT_EXTRA_MARKER,
    QUALITY_CONTACT_EXTRA_SUFFIX,
    QUALITY_SPIRIT_CATEGORY_EXTRA_SUFFIX,
    _normalize_side,
    quality_addspirit_extra_key,
    quality_spirit_category_extra_key,
)
from .lookups import _item_by_id, _power_by_name, _quality_by_id, _quality_by_name
from .priority import talent_special
from .requirements import requirement_tree_met


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
    effects: EffectsDict,
    qualities: list[dict[str, Any]],
    state: CharacterState,
) -> list[ActionDicePoolRow]:
    """Attach chosen Matrix action names from quality_extras onto actiondicepool rows."""
    by_name = {q["name"]: q for q in qualities}
    extras = state.quality_extras or {}
    out: list[ActionDicePoolRow] = []
    for row in effects.get("action_dice_pools") or []:
        item: ActionDicePoolRow = {
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
    effects: EffectsDict,
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
    effects: EffectsDict,
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
        if not side:
            if raw:
                errors.append(f"{spec['name']} の左右指定が不正です（Left / Right）")
            continue
        chosen[spec["id"]] = side
        limb_slot = _quality_limb_slot(spec)
        if not limb_slot:
            continue
        key = (limb_slot, side)
        if key in occupied:
            slot_ja = _SLOT_JA.get(limb_slot, limb_slot)
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


def gather_qualities(
    state: CharacterState, talent: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    qualities: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    free_ids: set[str] = set()
    state.quality_ids, dropped = sanitize_quality_ids(list(state.quality_ids))
    pending = list(state.quality_ids)
    talent_quality = _quality_by_name(talent.get("quality") or "")
    if talent_quality:
        pending.append(talent_quality["id"])
    extras = {key: str(value).strip() for key, value in (state.quality_extras or {}).items() if str(value).strip()}
    index = 0
    while index < len(pending):
        qid = pending[index]
        index += 1
        spec = _quality_by_id(qid)
        if not spec:
            continue
        max_takes = spec.get("max_takes")
        taken = counts.get(qid, 0)
        if max_takes is not None and taken >= int(max_takes):
            continue
        counts[qid] = taken + 1
        qualities.append(spec)
        for node in spec.get("bonus") or []:
            tag = node.get("tag")
            if tag == "freequality":
                child_id = str(node.get("value") or "").strip()
                if child_id and counts.get(child_id, 0) == 0:
                    free_ids.add(child_id)
                    pending.append(child_id)
            elif tag == "addqualities":
                raw = (node.get("fields") or {}).get("addquality") or node.get("value") or ""
                names = raw if isinstance(raw, list) else [raw]
                for name in names:
                    child = _quality_by_name(str(name).strip())
                    if child and counts.get(child["id"], 0) == 0:
                        free_ids.add(child["id"])
                        pending.append(child["id"])
            elif tag == "selectquality":
                raw = (node.get("fields") or {}).get("quality") or node.get("value") or []
                options = [str(item).strip() for item in (raw if isinstance(raw, list) else [raw]) if str(item).strip()]
                picked = extras.get(qid, "")
                if picked and picked in options:
                    child = _quality_by_name(picked)
                    if child and counts.get(child["id"], 0) == 0:
                        free_ids.add(child["id"])
                        pending.append(child["id"])
    return qualities, sorted(free_ids), dropped


def apply_quality_rules(
    state: CharacterState,
    qualities: list[dict[str, Any]],
    free_quality_ids: list[str],
    ctx: dict[str, Any],
    errors: list[str],
    *,
    career: bool = False,
    report: dict[str, Any] | None = None,
) -> int:
    owned = {item["id"] for item in qualities}
    extras = {
        key: str(value).strip()
        for key, value in (state.quality_extras or {}).items()
        if _quality_extra_key_owned(key, owned) and str(value).strip()
    }
    state.quality_extras = extras
    free_ids = set(free_quality_ids)
    negative_gain = 0
    positive_spend = 0
    for spec in qualities:
        is_free = bool(spec.get("onlyprioritygiven") or spec["id"] in free_ids)
        if not is_free and spec["karma"] < 0:
            negative_gain += -int(spec["karma"])
        if not is_free and spec["karma"] > 0:
            positive_spend += int(spec["karma"])
        if str(spec.get("extra_kind") or "") == "add_spirit":
            count = max(1, int(spec.get("add_spirit_count") or 1))
            if any(quality_addspirit_extra_key(spec["id"], idx) not in extras for idx in range(count)):
                errors.append(f"{spec['name']} の追加精霊を選んでください")
        elif quality_needs_extra(spec) and spec["id"] not in extras:
            if _quality_has_selectside(spec):
                errors.append(f"{spec['name']} の左右を選んでください")
            elif _quality_has_actiondicepool(spec):
                errors.append(f"{spec['name']} のマトリクスアクションを選んでください")
            elif _quality_needs_spell_category(spec):
                errors.append(f"{spec['name']} の呪文カテゴリを選んでください")
            elif _quality_needs_spirit_category(spec):
                errors.append(f"{spec['name']} の精霊を選んでください")
            elif str(spec.get("extra_kind") or "") == "weapon_skill":
                errors.append(f"{spec['name']} の武器技能を選んでください")
            else:
                errors.append(f"{spec['name']} の対象を入力してください")
        if _quality_needs_spirit_category(spec) and _quality_needs_spell_category(spec):
            spirit_key = quality_spirit_category_extra_key(spec["id"])
            if spirit_key not in extras:
                errors.append(f"{spec['name']} の精霊を選んでください")
        elif _quality_has_selectside(spec) and spec["id"] in extras and not _normalize_side(extras[spec["id"]]):
            errors.append(f"{spec['name']} の左右指定が不正です（Left / Right）")
        options = list(spec.get("select_options") or [])
        if not options:
            for node in spec.get("bonus") or []:
                if node.get("tag") != "selectquality":
                    continue
                raw = (node.get("fields") or {}).get("quality") or node.get("value") or []
                options = [str(item).strip() for item in (raw if isinstance(raw, list) else [raw]) if str(item).strip()]
        if options and spec["id"] in extras and extras[spec["id"]] not in options:
            if not _quality_has_actiondicepool(spec):
                errors.append(f"{spec['name']} の対象が不正です")
        if is_free:
            continue
        if spec.get("required_tree") and not requirement_tree_met(spec.get("required_tree"), ctx):
            errors.append(f"{spec['name']} の前提を満たしていません")
        forbidden = spec.get("forbidden_tree") or []
        if forbidden and requirement_tree_met(forbidden, ctx):
            errors.append(f"{spec['name']} は現在のキャラクターでは取れません")
    if negative_gain > NEGATIVE_QUALITY_KARMA_CAP and not career:
        errors.append(
            f"不利資質から得られるカルマが上限を超えています（{negative_gain} / {NEGATIVE_QUALITY_KARMA_CAP}）"
        )
    if positive_spend > POSITIVE_QUALITY_KARMA_CAP and not career:
        errors.append(
            f"有利資質に費やせるカルマが上限を超えています（{positive_spend} / {POSITIVE_QUALITY_KARMA_CAP}）"
        )

    # --- Metagenic / SURGE (Run Faster p.106) ------------------------------
    metagenic_limit = 0
    for spec in qualities:
        for node in spec.get("bonus") or []:
            if node.get("tag") == "metageniclimit":
                metagenic_limit = max(
                    metagenic_limit,
                    _as_int(node.get("value") or (node.get("fields") or {}).get("value")),
                )
    mg_specs = [spec for spec in qualities if spec.get("metagenic") and spec.get("contributes_to_metagenic_limit")]
    mg_pos = sum(int(spec["karma"]) for spec in mg_specs if int(spec["karma"]) > 0)
    mg_neg = sum(-int(spec["karma"]) for spec in mg_specs if int(spec["karma"]) < 0)
    mg_balanced = (not mg_pos) or mg_neg in (mg_pos, mg_pos - 1)
    if not career:
        if (mg_pos or mg_neg) and metagenic_limit <= 0:
            errors.append("メタジェネティック資質には Changeling（Class I／II／III SURGE）が必要です")
        elif metagenic_limit > 0:
            if mg_neg > metagenic_limit:
                errors.append(f"不利メタジェネティック資質のカルマが上限を超えています（{mg_neg} / {metagenic_limit}）")
            if mg_pos > metagenic_limit:
                errors.append(f"有利メタジェネティック資質のカルマが上限を超えています（{mg_pos} / {metagenic_limit}）")
            if mg_pos and not mg_balanced:
                errors.append(
                    "メタジェネティック資質のカルマ収支が不均衡です"
                    f"（不利 {mg_neg}、必要 {max(0, mg_pos - 1)}〜{mg_pos}）"
                )
    if report is not None:
        report["metagenic"] = {
            "limit": metagenic_limit,
            "positive": mg_pos,
            "negative": mg_neg,
            "balanced": bool(mg_balanced),
            "count": len(mg_specs),
        }
    return negative_gain
