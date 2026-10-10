"""Cyberlimb attributes, Redliner slot accounting, and Cyberseeker.

Resolves each cyberlimb's Strength / Agility / Armor from its enhancement
mods (``_apply_limb_attributes``), the average-limb attribute replacement
(``limb_attribute_replace``), and the Redliner / Cyberseeker quality bonuses
driven off how many XML limb slots the installed ware occupies.

Imports only ``_limb_attr_effect`` (``.gear``), ``_normalize_side``
(``.constants``) and ``CharacterOptions`` (models) — never back into
``app.engine``.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
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
_MUSCLE_WARE = re.compile(r"\bmuscle (replacement|toner|augmentation)\b", re.I)


def _apply_limb_attributes(resolved: list[dict[str, Any]], attrs_spec: dict[str, dict[str, int | float]]) -> None:
    """Resolve each cyberlimb's Strength/Agility/Armor from its enhancement mods.

    SR5 p.456: an empty cyberlimb has Strength 3 and Agility 3. A
    "Customized" mod sets the base and the best "Enhanced" mod adds on top,
    held to `<cyberlimbattributebonuscap>` (Chummer's
    `GetAttributeTotalValue`); the per-limb total is capped at the
    character's augmented maximum for that attribute. The base and bonus are
    kept so Redliner / Cyberseeker can add to the bonus under the same cap.
    """
    children: dict[str, list[dict[str, Any]]] = {}
    for item in resolved:
        if item.get("parent_id"):
            children.setdefault(item["parent_id"], []).append(item)
    cap = current_rules().cyberlimb_attribute_bonus_cap
    for item in resolved:
        if item.get("category") != "Cyberlimb" and not item.get("limbslot"):
            continue
        base = {"STR": CYBERLIMB_BASE_ATTR, "AGI": CYBERLIMB_BASE_ATTR}
        bonus = {"STR": 0, "AGI": 0}
        limb_armor = 0
        for kid in children.get(item["id"]) or []:
            if (kid.get("name") or "") == "Armor":
                limb_armor += int(kid.get("rating") or 0)
                continue
            effect = _limb_attr_effect(kid.get("name") or "")
            if not effect:
                continue
            attr, mode = effect
            if mode == "set":
                base[attr] = int(kid["rating"])
            else:
                bonus[attr] = max(bonus[attr], int(kid["rating"]))
        for attr in ("STR", "AGI"):
            key = attr.lower()
            item[f"limb_{key}_base"] = base[attr]
            item[f"limb_{key}_bonus"] = bonus[attr]
            item[f"limb_{key}"] = _limb_total(base[attr], bonus[attr], cap, attrs_spec, attr)
        item["limb_armor"] = limb_armor
    _inherit_limb_attributes(resolved)


def _inherit_limb_attributes(resolved: list[dict[str, Any]]) -> None:
    """Cyberware.GetAttributeTotalValue averages positive child values,
    rounding down, instead of using the connector's own base/enhancements.
    Resolve descendants first even when installs are stored child-first.
    """
    children: dict[str, list[dict[str, Any]]] = {}
    for item in resolved:
        if item.get("parent_id"):
            children.setdefault(str(item["parent_id"]), []).append(item)
    done: set[str] = set()
    visiting: set[str] = set()

    def inherit(item: dict[str, Any]) -> None:
        key = str(item["id"])
        if key in done or key in visiting:
            return
        visiting.add(key)
        kids = children.get(key) or []
        for child in kids:
            inherit(child)
        if item.get("inherit_attributes"):
            for attr in ("str", "agi"):
                values = [int(child.get(f"limb_{attr}") or 0) for child in kids]
                values = [value for value in values if value > 0]
                item[f"limb_{attr}"] = sum(values) // len(values) if values else 0
        visiting.remove(key)
        done.add(key)

    for item in resolved:
        inherit(item)


def _limb_total(base: int, bonus: int, cap: int, attrs_spec: dict[str, dict[str, int | float]], attr: str) -> int:
    aug = int(attrs_spec.get(attr, {}).get("aug") or 9)
    return min(aug, base + min(bonus, cap))


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


def redliner_slot_caps(
    options: CharacterOptions | None = None, extra_limbs: dict[str, int] | None = None
) -> dict[str, int]:
    """The limb slots Redliner counts: arms and legs, plus torso and skull
    unless `<redlinerexclusion>` leaves them out (Chummer's default does) —
    the character options can still add those two back."""
    opts = options or CharacterOptions()
    excludes = set(current_rules().redliner_excludes)
    body = body_limb_slots(extra_limbs)
    slots = {slot: body[slot] for slot in REDLINER_BASE_SLOTS if slot not in excludes}
    if opts.redliner_torso or "torso" not in excludes:
        slots["torso"] = 1
    if opts.redliner_skull or "skull" not in excludes:
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


def side_slot_capacity(slot: str, extra_limbs: dict[str, int] | None = None) -> int:
    """Chummer SelectSide allocates half the body's limbs to each side."""
    return max(1, body_limb_slots(extra_limbs).get(slot, 2) // 2)


def _take_limb_slots(
    item: dict[str, Any],
    slots: dict[str, int],
    used: dict[str, int],
    side_used: dict[tuple[str, str], int],
    taken: set[tuple[str, str, str]],
) -> int:
    """Count distinct installs within the body and each side's capacity."""
    slot = (item.get("limbslot") or "").lower()
    side = _normalize_side(item.get("side"))
    identity = (slot, side or "", str(item.get("id") or item.get("name") or ""))
    if identity in taken or slot not in slots:
        return 0
    add = min(slots[slot] - used[slot], _limb_slot_count(item, slots))
    if side:
        key = (slot, side)
        add = min(add, max(1, slots[slot] // 2) - side_used.get(key, 0))
    if add <= 0:
        return 0
    taken.add(identity)
    used[slot] += add
    if side:
        side_used[(slot, side)] = side_used.get((slot, side), 0) + add
    return add


def _is_full_limb(item: dict[str, Any]) -> bool:
    # The XML's slot, rather than an English name, distinguishes a full
    # replacement/connector from a foot, lower leg or partial skull.
    return not item.get("parent_id") and bool(item.get("limbslot"))


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


def _limb_rows(
    resolved: list[dict[str, Any]], slots: dict[str, int], *, descend_excluded: bool = False
) -> Iterator[dict[str, Any]]:
    """Count a slotted parent once; visit children of other containers.

    GetCyberlimbCount descends into excluded slots, whereas attribute
    averaging skips the entire excluded limb. Keep that distinction.
    """
    children: dict[str, list[dict[str, Any]]] = {}
    for item in resolved:
        if item.get("parent_id"):
            children.setdefault(str(item["parent_id"]), []).append(item)
    seen: set[str] = set()

    def visit(item: dict[str, Any]) -> Iterator[dict[str, Any]]:
        key = str(item.get("id") or "")
        if key in seen:
            return
        seen.add(key)
        slot = str(item.get("limbslot") or "").lower()
        if slot in slots:
            yield item
            return
        if slot and not descend_excluded:
            return
        for child in children.get(key) or []:
            yield from visit(child)

    for item in resolved:
        if not item.get("parent_id"):
            yield from visit(item)


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
    taken: set[tuple[str, str, str]] = set()
    side_used: dict[tuple[str, str], int] = {}
    limb_str: list[int] = []
    limb_agi: list[int] = []
    for item in _limb_rows(resolved, slots):
        slot = (item.get("limbslot") or "").lower()
        if slot not in slots:
            continue
        add = _take_limb_slots(item, slots, used, side_used, taken)
        if add <= 0:
            continue
        for _ in range(add):
            limb_str.append(int(item["limb_str"]) if item.get("limb_str") is not None else meat_str)
            limb_agi.append(int(item["limb_agi"]) if item.get("limb_agi") is not None else meat_agi)
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
    slots = redliner_slot_caps() if slots is None else slots
    taken: set[tuple[str, str, str]] = set()
    side_used: dict[tuple[str, str], int] = {}
    total = 0
    used = dict.fromkeys(slots, 0)
    for item in _limb_rows(resolved, slots, descend_excluded=True):
        total += _take_limb_slots(item, slots, used, side_used, taken)
    return total


def apply_cyberseeker(
    resolved: list[dict[str, Any]],
    targets: list[str],
    attrs_spec: dict[str, dict[str, int | float]],
    options: CharacterOptions | None = None,
    extra_limbs: dict[str, int] | None = None,
) -> dict[str, Any] | None:
    if not targets:
        return None
    slots = redliner_slot_caps(options, extra_limbs)
    count = count_redliner_limbs(resolved, slots)
    # Character.RedlinerBonus / RefreshRedlinerImprovements cap both
    # Redliner and Cyber Singularity Seeker at two, even with extra limbs.
    pairs = min(count // 2, 2)
    attr_bonus = dict.fromkeys(("STR", "AGI", "WIL", "BOD", "REA", "CHA", "INT", "LOG"), 0)
    cm_physical = 0
    limb_bonus = 0
    for target in targets:
        if target in {"STR", "AGI"}:
            attr_bonus[target] = pairs
            limb_bonus = pairs
        elif target == "BOX":
            # The XML's BOX target is three physical boxes per bonus point.
            cm_physical -= pairs * 3
        elif target in attr_bonus:
            attr_bonus[target] = pairs
    if limb_bonus:
        cap = current_rules().cyberlimb_attribute_bonus_cap
        for item in resolved:
            if (item.get("category") != "Cyberlimb" and not item.get("limbslot")) or item.get("inherit_attributes"):
                continue
            for attr in ("STR", "AGI"):
                key = attr.lower()
                if item.get(f"limb_{key}") is None:
                    continue
                base = int(item.get(f"limb_{key}_base") or CYBERLIMB_BASE_ATTR)
                bonus = int(item.get(f"limb_{key}_bonus") or 0) + limb_bonus
                item[f"limb_{key}"] = _limb_total(base, bonus, cap, attrs_spec, attr)
        _inherit_limb_attributes(resolved)
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
