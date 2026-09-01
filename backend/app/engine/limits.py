"""Chargen validation: availability, device rating, and augmentation-bonus caps.

``_finalize_avail_tree`` rolls each install's own + children availability into a
tree total (grade-aware); the ``_check_*`` helpers raise the SR5 chargen errors
when a total exceeds CHARGEN_AVAIL_MAX / CHARGEN_DEVICE_RATING_MAX /
CHARGEN_WARE_ATTR_BONUS_MAX. Career characters skip these.

Imports only ``format_avail`` etc. / already-extracted engine modules — never
back into ``app.engine``.
"""

from __future__ import annotations

from typing import Any

from ..data_loader import (
    CHARGEN_AVAIL_MAX,
    CHARGEN_DEVICE_RATING_MAX,
    CHARGEN_WARE_ATTR_BONUS_MAX,
    PHYSICAL_ATTRS,
    format_avail,
    parse_avail,
    sum_avail,
)
from ..improvements import ATTR_ALIASES, EffectsDict, _as_int
from .lookups import _grade_by_name


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
        value, suffix = sum_avail([(int(item.get("avail_value") or 0), str(item.get("avail_suffix") or ""))] + adds)
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


def _restricted_gear_slots(effects: EffectsDict) -> list[int]:
    slots: list[int] = []
    for row in effects.get("restricted_gear") or []:
        cap = max(0, int(row.get("availability") or 0))
        amount = max(1, int(row.get("amount") or 1))
        slots.extend([cap] * amount)
    slots.sort(reverse=True)
    return slots


def _check_avail_limit(items: list[dict[str, Any]], effects: EffectsDict, errors: list[str]) -> None:
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
    totals: dict[str, int] = dict.fromkeys(PHYSICAL_ATTRS, 0)
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
