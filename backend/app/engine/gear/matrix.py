"""Matrix devices — cyberdecks and RCCs.

Their ASDF attribute array (Attack / Sleaze / Data Processing / Firewall) can be
reordered on a cyberdeck; :func:`_resolve_matrix_devices` prices each device and
publishes the resolved array.
"""

from __future__ import annotations

from typing import Any

from ...data_loader import eval_formula
from ...models import GearInstall
from ..constants import MATRIX_ARRAY_KEYS
from ..lookups import _item_by_id
from ._common import _clamp_rating

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
    stats = dict.fromkeys(MATRIX_ARRAY_KEYS, 0)
    for key, value in zip(order, nums, strict=False):
        stats[key] = value
    return {
        "device_rating": device,
        "programs": programs,
        **stats,
        "array": nums,
        "array_order": order,
        "can_reorder": can_reorder,
    }


def _resolve_matrix_devices(
    kind: str, installs: list[GearInstall]
) -> tuple[list[GearInstall], list[dict[str, Any]], int]:
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
