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

from ..improvements import EffectsDict, _as_int, granted_quality_names
from ..improvements.effect_rows import ActionDicePoolRow
from ..models import CharacterState
from ..notices import Notice, notice, term, ui
from ..rules import current_rules
from .constants import (
    MAG_TALENTS,
    QUALITY_ADDSPIRIT_EXTRA_MARKER,
    QUALITY_CONTACT_EXTRA_SUFFIX,
    QUALITY_OPTIONAL_POWER_EXTRA_SUFFIX,
    QUALITY_SPIRIT_CATEGORY_EXTRA_SUFFIX,
    _normalize_side,
    quality_addspirit_extra_key,
    quality_optional_power_extra_key,
    quality_spirit_category_extra_key,
    slot_phrase,
)
from .lookups import (
    _item_by_id,
    _power_by_name,
    _quality_by_id,
    _quality_by_name,
    _tradition_by_id,
    critter_power_label,
)
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
        if _at_quality_limit(spec, counts):
            removed.append(spec["name"])
            continue
        taken = counts.get(qid, 0)
        counts[qid] = taken + 1
        limited.append(qid)
    return limited, removed


def _at_quality_limit(spec: dict[str, Any], counts: dict[str, int]) -> bool:
    """Would one more take of `spec` go over its limit? `<includeinlimit>`
    counts the named siblings too (Indomitable, SR5 p.75: Physical, Mental and
    Social share one limit of 3); `<limitwithinclusions>` sets that shared cap
    apart from the per-kind `limit` (Tough as Nails, RF p.150: 3 each, 4 in
    all)."""
    max_takes = spec.get("max_takes")
    own = counts.get(str(spec["id"]), 0)
    if max_takes is not None and own >= int(max_takes):
        return True
    siblings = set(spec.get("includeinlimit") or [])
    if not siblings:
        return False
    shared = own + sum(
        count
        for qid, count in counts.items()
        if qid != spec["id"] and ((_quality_by_id(qid) or {}).get("name") in siblings)
    )
    cap = int(spec.get("limitwithinclusions") or 0) or (int(max_takes) if max_takes is not None else 0)
    return bool(cap) and shared >= cap


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
    if key.endswith(QUALITY_OPTIONAL_POWER_EXTRA_SUFFIX):
        return key[: -len(QUALITY_OPTIONAL_POWER_EXTRA_SUFFIX)] in owned
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
    warnings: list[Notice],
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
            warnings.append(notice("engine.adept.powerPick", source=term(source)))
            continue
        if options and picked not in options:
            warnings.append(notice("engine.adept.powerNotAllowed", source=term(source), picked=term(picked)))
            continue
        if open_select and not _power_by_name(picked):
            warnings.append(notice("engine.adept.powerUnknown", source=term(source), power=term(picked)))
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
    warnings: list[Notice],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in effects.get("grant_powers") or []:
        name = str(row.get("name") or "").strip()
        source = str(row.get("source") or "").strip()
        spec = _power_by_name(name)
        if not spec:
            warnings.append(notice("engine.adept.powerUnknown", source=term(source), power=term(name)))
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
    errors: list[Notice],
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
            occupied[(slot, side)] = str(item.get("name") or "")

    extras = state.quality_extras or {}
    for spec in qualities:
        if not _quality_has_selectside(spec):
            continue
        raw = str(extras.get(spec["id"]) or "").strip()
        side = _normalize_side(raw)
        if not side:
            if raw:
                errors.append(notice("engine.qualities.sideInvalid", name=term(str(spec["name"]))))
            continue
        chosen[spec["id"]] = side
        limb_slot = _quality_limb_slot(spec)
        if not limb_slot:
            continue
        key = (limb_slot, side)
        if key in occupied:
            errors.append(
                notice(
                    "engine.qualities.sideDuplicate",
                    name=term(str(spec["name"])),
                    other=term(occupied[key]) if occupied[key] else ui("engine.term.ware"),
                    side=ui(f"engine.side.{side}"),
                    slot=slot_phrase(limb_slot),
                )
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


def tradition_quality_grants(state: CharacterState, talent: dict[str, Any]) -> list[tuple[str, str]]:
    """The qualities a tradition forces on its follower, each with its pick.

    A tradition belongs to the awakened alone — ``resolve_spells`` clears it
    for everyone else — so a mundane build is handed nothing. The grants ride
    the tradition's ``<bonus>`` either singly (Traditionalist Shaman's Code of
    Honor, FA p.74) or inside ``<addqualities>``.
    """
    if talent.get("name") not in MAG_TALENTS:
        return []
    tradition = _tradition_by_id(state.tradition_id)
    grants: list[tuple[str, str]] = []
    for node in (tradition or {}).get("bonus") or []:
        if node.get("tag") in ("addquality", "addqualities"):
            grants.extend(granted_quality_names(node))
    return grants


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
    # The tradition's own grants come free, like the ones a quality chains in
    # below: the follower never chose them, so they cost no karma either way.
    forced_extras: dict[str, str] = {}
    for name, select in tradition_quality_grants(state, talent):
        granted = _quality_by_name(name)
        if not granted or granted["id"] in pending:
            continue
        pending.append(granted["id"])
        free_ids.add(granted["id"])
        if select:
            forced_extras[granted["id"]] = select
    if forced_extras:
        state.quality_extras = {**(state.quality_extras or {}), **forced_extras}
    extras = {key: str(value).strip() for key, value in (state.quality_extras or {}).items() if str(value).strip()}
    index = 0
    while index < len(pending):
        qid = pending[index]
        index += 1
        spec = _quality_by_id(qid)
        if not spec:
            continue
        if _at_quality_limit(spec, counts):
            continue
        taken = counts.get(qid, 0)
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


def apply_cost_discounts(qualities: list[dict[str, Any]], req_ctx: dict[str, Any]) -> list[dict[str, Any]]:
    """`<costdiscount>`: a quality's karma moves by `value` when its tree is
    met. As Chummer reads it, `value` is added to a positive quality's cost
    and taken from a negative one's: The Beast's Way 20 → 17 with an Animal
    Familiar (SG p.176), Blind −15 → −5 for the astrally aware (RF p.153),
    Astral Hazing −5 → −15 for the Awakened (RF p.119). Returns copies — the
    specs are the catalog's own dicts — with the table value on `karma_base`."""
    out: list[dict[str, Any]] = []
    for spec in qualities:
        discount = spec.get("cost_discount") or {}
        value = int(discount.get("value") or 0)
        if value and requirement_tree_met(discount.get("required_tree"), req_ctx):
            karma = int(spec["karma"])
            spec = {**spec, "karma_base": karma, "karma": karma + value if karma > 0 else karma - value}
        out.append(spec)
    return out


def surge_metagenic_limit(qualities: list[dict[str, Any]]) -> int:
    """The karma a SURGE Changeling may put into metagenic qualities (RF p.106),
    or 0 for anyone else — the largest `<metageniclimit>` among `qualities`."""
    limit = 0
    for spec in qualities:
        for node in spec.get("bonus") or []:
            if node.get("tag") == "metageniclimit":
                limit = max(limit, _as_int(node.get("value") or (node.get("fields") or {}).get("value")))
    return limit


def counts_toward_quality_limit(spec: dict[str, Any], surge: bool) -> bool:
    """Chummer's `Quality.ContributeToLimit`, for the 25-karma limits both ways.

    `<contributetolimit>False` keeps a quality out (Infected, the talents).
    So does being metagenic on a SURGE Changeling: those answer to the SURGE
    limit instead ("Positive Metagenic Qualities are free if you're a
    Changeling"), and counting them twice would refuse a legal 30-karma build.
    """
    if not spec.get("contributes_to_limit", True):
        return False
    return not (surge and spec.get("metagenic"))


def apply_quality_rules(
    state: CharacterState,
    qualities: list[dict[str, Any]],
    free_quality_ids: list[str],
    ctx: dict[str, Any],
    errors: list[Notice],
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
    surge = surge_metagenic_limit(qualities) > 0
    negative_gain = 0
    positive_spend = 0
    for spec in qualities:
        is_free = bool(spec.get("onlyprioritygiven") or spec["id"] in free_ids)
        # Chummer's `PositiveQualityLimitKarma` / `NegativeQualityLimitKarma`
        counted = not is_free and counts_toward_quality_limit(spec, surge)
        if counted and spec["karma"] < 0:
            negative_gain += -int(spec["karma"])
        if counted and spec["karma"] > 0:
            positive_spend += int(spec["karma"])
        if str(spec.get("extra_kind") or "") == "add_spirit":
            count = max(1, int(spec.get("add_spirit_count") or 1))
            if any(quality_addspirit_extra_key(spec["id"], idx) not in extras for idx in range(count)):
                errors.append(notice("engine.qualities.pickAddSpirit", name=term(str(spec["name"]))))
        elif quality_needs_extra(spec) and spec["id"] not in extras:
            if _quality_has_selectside(spec):
                errors.append(notice("engine.qualities.pickSide", name=term(str(spec["name"]))))
            elif _quality_has_actiondicepool(spec):
                errors.append(notice("engine.qualities.pickMatrixAction", name=term(str(spec["name"]))))
            elif _quality_needs_spell_category(spec):
                errors.append(notice("engine.qualities.pickSpellCategory", name=term(str(spec["name"]))))
            elif _quality_needs_spirit_category(spec):
                errors.append(notice("engine.qualities.pickSpirit", name=term(str(spec["name"]))))
            elif str(spec.get("extra_kind") or "") == "weapon_skill":
                errors.append(notice("engine.qualities.pickWeaponSkill", name=term(str(spec["name"]))))
            else:
                errors.append(notice("engine.qualities.pickExtra", name=term(str(spec["name"]))))
        optional = [critter_power_label(row) for row in spec.get("optional_powers") or []]
        if optional:
            picked = extras.get(quality_optional_power_extra_key(spec["id"]))
            if not picked:
                errors.append(notice("engine.qualities.pickOptionalPower", name=term(str(spec["name"]))))
            elif picked not in optional:
                errors.append(notice("engine.qualities.extraInvalid", name=term(str(spec["name"]))))
        if _quality_needs_spirit_category(spec) and _quality_needs_spell_category(spec):
            spirit_key = quality_spirit_category_extra_key(spec["id"])
            if spirit_key not in extras:
                errors.append(notice("engine.qualities.pickSpirit", name=term(str(spec["name"]))))
        elif _quality_has_selectside(spec) and spec["id"] in extras and not _normalize_side(extras[spec["id"]]):
            errors.append(notice("engine.qualities.sideInvalid", name=term(str(spec["name"]))))
        options = list(spec.get("select_options") or [])
        if not options:
            for node in spec.get("bonus") or []:
                if node.get("tag") != "selectquality":
                    continue
                raw = (node.get("fields") or {}).get("quality") or node.get("value") or []
                options = [str(item).strip() for item in (raw if isinstance(raw, list) else [raw]) if str(item).strip()]
        if options and spec["id"] in extras and extras[spec["id"]] not in options:
            if not _quality_has_actiondicepool(spec):
                errors.append(notice("engine.qualities.extraInvalid", name=term(str(spec["name"]))))
        if is_free:
            continue
        if spec.get("required_tree") and not requirement_tree_met(spec.get("required_tree"), ctx):
            errors.append(notice("engine.qualities.prereq", name=term(str(spec["name"]))))
        forbidden = spec.get("forbidden_tree") or []
        if forbidden and requirement_tree_met(forbidden, ctx):
            errors.append(notice("engine.qualities.forbidden", name=term(str(spec["name"]))))
    rules = current_rules()
    if negative_gain > rules.quality_karma_cap_negative and not career and not rules.quality_exceed_negative:
        errors.append(
            notice(
                "engine.qualities.negativeCap", karma=negative_gain, limit=current_rules().quality_karma_cap_negative
            )
        )
    if positive_spend > current_rules().quality_karma_cap_positive and not career:
        errors.append(
            notice(
                "engine.qualities.positiveCap", karma=positive_spend, limit=current_rules().quality_karma_cap_positive
            )
        )

    # --- Metagenic / SURGE (Run Faster p.106) ------------------------------
    metagenic_limit = surge_metagenic_limit(qualities)
    mg_specs = [spec for spec in qualities if spec.get("metagenic") and spec.get("contributes_to_limit")]
    mg_pos = sum(int(spec["karma"]) for spec in mg_specs if int(spec["karma"]) > 0)
    mg_neg = sum(-int(spec["karma"]) for spec in mg_specs if int(spec["karma"]) < 0)
    mg_balanced = (not mg_pos) or mg_neg in (mg_pos, mg_pos - 1)
    if not career:
        if (mg_pos or mg_neg) and metagenic_limit <= 0:
            errors.append(notice("engine.qualities.metagenicNeedsChangeling"))
        elif metagenic_limit > 0:
            if mg_neg > metagenic_limit:
                errors.append(notice("engine.qualities.metagenicNegativeCap", karma=mg_neg, limit=metagenic_limit))
            if mg_pos > metagenic_limit:
                errors.append(notice("engine.qualities.metagenicPositiveCap", karma=mg_pos, limit=metagenic_limit))
            if mg_pos and not mg_balanced:
                errors.append(
                    notice(
                        "engine.qualities.metagenicUnbalanced",
                        negative=mg_neg,
                        min=max(0, mg_pos - 1),
                        max=mg_pos,
                    )
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
