"""Cyberlimb attributes, Redliner slot accounting, and Cyberseeker.

Resolves each cyberlimb's Strength / Agility / Armor from its enhancement
mods (``_apply_limb_attributes``), the average-limb attribute replacement
(``limb_attribute_replace``), and the Redliner / Cyberseeker quality bonuses
driven off how many full limbs occupy the redliner slots.

Imports only ``_limb_attr_effect`` (``.gear``), ``_normalize_side``
(``.constants``) and ``CharacterOptions`` (models) — never back into
``app.engine``.
"""

from __future__ import annotations

import re
from typing import Any

from ...models import CharacterOptions
from ...notices import Notice, notice, terms
from ...rules import current_rules
from ..constants import _normalize_side
from ..gear import _limb_attr_effect

# Chummer's default `<limbcount>` 6: the skull counts as one of the limbs a
# cyberlimb's STR / AGI is averaged across, next to the torso.
LIMB_BODY_SLOTS = {"arm": 2, "leg": 2, "torso": 1, "skull": 1}
LIMB_BODY_PARTS = 6
CYBERLIMB_BASE_ATTR = 3  # SR5 p.456: an empty cyberlimb has STR 3 / AGI 3
REDLINER_BASE_SLOTS = {"arm": 2, "leg": 2}
_PARTIAL_LIMB = re.compile(r"\b(hand|foot|lower|modular connector)\b", re.I)
_MUSCLE_WARE = re.compile(r"\bmuscle (replacement|toner|augmentation)\b", re.I)


def _apply_limb_attributes(resolved: list[dict[str, Any]], attrs_spec: dict[str, dict[str, int | float]]) -> None:
    """Resolve each cyberlimb's Strength/Agility/Armor from its enhancement mods.

    SR5 p.456: an empty cyberlimb has Strength 3 and Agility 3. "Customized"
    mods set the base, "Enhanced" mods add on top, and the per-limb total is
    capped at the character's augmented maximum for that attribute.
    """
    children: dict[str, list[dict[str, Any]]] = {}
    for item in resolved:
        if item.get("parent_id"):
            children.setdefault(item["parent_id"], []).append(item)
    str_aug = int(attrs_spec.get("STR", {}).get("aug") or 9)
    agi_aug = int(attrs_spec.get("AGI", {}).get("aug") or 9)
    for item in resolved:
        if item.get("category") != "Cyberlimb":
            continue
        str_val = agi_val = CYBERLIMB_BASE_ATTR
        limb_armor = 0
        for kid in children.get(item["id"]) or []:
            if (kid.get("name") or "") == "Armor":
                limb_armor += int(kid.get("rating") or 0)
                continue
            effect = _limb_attr_effect(kid.get("name") or "")
            if not effect:
                continue
            attr, mode = effect
            if attr == "STR":
                str_val = kid["rating"] if mode == "set" else str_val + int(kid["rating"])
            else:
                agi_val = kid["rating"] if mode == "set" else agi_val + int(kid["rating"])
        item["limb_str"] = min(str_aug, str_val)
        item["limb_agi"] = min(agi_aug, agi_val)
        item["limb_armor"] = limb_armor


def cyberleg_movement_agi(resolved: list[dict[str, Any]], extra_limbs: dict[str, int] | None = None) -> int | None:
    """The AGI movement runs off under `<cyberlegmovement>`, or `None`.

    Chummer's `CalculatedMovement`: every installed ware in the `leg` slot
    counts its limb slots, and once there are two the lowest of their AGIs
    replaces the character's own.
    """
    slots = body_limb_slots(extra_limbs)
    legs = [
        item
        for item in resolved
        if not item.get("parent_id")
        and (item.get("limbslot") or "").lower() == "leg"
        and item.get("limb_agi") is not None
    ]
    if sum(_limb_slot_count(item, slots) for item in legs) < 2:
        return None
    return min(int(item["limb_agi"]) for item in legs)


def redliner_slot_caps(options: CharacterOptions | None = None) -> dict[str, int]:
    opts = options or CharacterOptions()
    slots = dict(REDLINER_BASE_SLOTS)
    if opts.redliner_torso:
        slots["torso"] = 1
    if opts.redliner_skull:
        slots["skull"] = 1
        slots["head"] = 1
    return slots


def body_limb_slots(extra_limbs: dict[str, int] | None = None) -> dict[str, int]:
    """How many of each limb slot this body has, after ``<addlimb>``.

    Two arms, two legs and a torso unless something added to them: Shiva Arms
    is a second pair of arms (RF p.118), a Centaur has four legs.
    """
    slots = dict(LIMB_BODY_SLOTS)
    for slot, count in (extra_limbs or {}).items():
        key = str(slot).strip().lower()
        if key in slots and int(count or 0) > 0:
            slots[key] += int(count)
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


def _limb_slot_count(item: dict[str, Any], slots: dict[str, int] | None = None) -> int:
    raw = str(item.get("limbslotcount") or "1").strip()
    if raw.lower() == "all":
        slot = (item.get("limbslot") or "").lower()
        return (slots or LIMB_BODY_SLOTS).get(slot, 1)
    try:
        return max(1, int(float(raw)))
    except ValueError:
        return 1


def limb_attribute_replace(
    resolved: list[dict[str, Any]],
    meat_str: int,
    meat_agi: int,
    attrs_spec: dict[str, dict[str, int | float]],
    extra_limbs: dict[str, int] | None = None,
) -> dict[str, Any] | None:
    slots = body_limb_slots(extra_limbs)
    # `<excludelimbslot>` (Neon Anarchy: skull) takes a slot out of the
    # average; `<limbcount>` is the divisor, plus whatever `<addlimb>` added
    rules = current_rules()
    excluded = rules.exclude_limb_slot.strip().lower()
    slots = {slot: n for slot, n in slots.items() if slot != excluded}
    added = sum(max(0, int(n or 0)) for n in (extra_limbs or {}).values())
    parts = max(1, rules.limb_count + added)
    used = dict.fromkeys(slots, 0)
    taken: set[tuple[str, str]] = set()
    limb_str: list[int] = []
    limb_agi: list[int] = []
    for item in resolved:
        if not _is_body_limb(item):
            continue
        slot = (item.get("limbslot") or "").lower()
        if slot not in slots:
            continue
        side = _normalize_side(item.get("side")) or ""
        key = (slot, side or item.get("id") or item.get("name") or "")
        if key in taken:
            continue
        if used[slot] >= slots[slot]:
            continue
        add = min(slots[slot] - used[slot], _limb_slot_count(item, slots))
        if add <= 0:
            continue
        taken.add(key)
        used[slot] += add
        for _ in range(add):
            limb_str.append(int(item.get("limb_str") or meat_str))
            limb_agi.append(int(item.get("limb_agi") or meat_agi))
    count = min(parts, sum(used.values()))
    if count == 0:
        return None
    meat_parts = parts - count
    # Chummer's `CalculatedTotalValue`: the average rounds up
    str_avg = -(-(sum(limb_str) + meat_str * meat_parts) // parts)
    agi_avg = -(-(sum(limb_agi) + meat_agi * meat_parts) // parts)
    str_avg = min(int(attrs_spec.get("STR", {}).get("aug") or 9), str_avg)
    agi_avg = min(int(attrs_spec.get("AGI", {}).get("aug") or 9), agi_avg)
    return {
        "count": count,
        "parts": parts,
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
    used = dict.fromkeys(slots, 0)
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
    attr_bonus = dict.fromkeys(("STR", "AGI", "WIL", "BOD", "REA", "CHA", "INT", "LOG"), 0)
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


def redliner_incompat_warnings(installed: list[dict[str, Any]], targets: list[str]) -> list[Notice]:
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
    return [notice("engine.ware.redlinerIncompatible", needed=terms(names))]
