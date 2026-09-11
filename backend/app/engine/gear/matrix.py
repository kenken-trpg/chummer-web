"""Matrix devices — cyberdecks and RCCs.

Their ASDF attribute array (Attack / Sleaze / Data Processing / Firewall) can be
reordered on a cyberdeck; :func:`_resolve_matrix_devices` prices each device and
publishes the resolved array. :func:`matrix_initiative` turns the persona a
character actually runs into the VR initiative that persona rolls.
"""

from __future__ import annotations

from typing import Any

from ...data_loader import eval_formula
from ...models import GearInstall
from ..bundle_types import MatrixInitiative
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


#: SR5 p.229: VR initiative rolls Data Processing + Intuition, with three dice
#: in cold sim and four in hot sim. In AR the character keeps their meat
#: initiative, so there is nothing extra to publish for it.
COLD_SIM_DICE = 3
HOT_SIM_DICE = 4


def matrix_initiative(
    personas: list[tuple[str, dict[str, Any] | None]],
    intuition: int,
    extra_dice: int = 0,
    offset: int = 0,
) -> MatrixInitiative | None:
    """The VR initiative of the best persona the character can run.

    ``personas`` is (label, row) in preference order — a technomancer's living
    persona, then the devices. The one with the highest Data Processing wins,
    because that is the one worth jacking into; ties keep the earlier entry.
    ``extra_dice`` is `<matrixinitiativedice>` (a Multidimensional Coprocessor,
    the Sourcerer echoes); ``offset`` is `<matrixinitiative>`, which moves the
    score rather than the dice — Delphi gives up two points of it (KC p.103).
    """
    best: tuple[str, int] | None = None
    for label, row in personas:
        if not row:
            continue
        processing = int(row.get("dataprocessing") or 0)
        if best is None or processing > best[1]:
            best = (label, processing)
    if best is None:
        return None
    label, processing = best
    return {
        "device": label,
        "dataprocessing": processing,
        "value": max(0, processing + int(intuition) + int(offset)),
        "cold_dice": COLD_SIM_DICE + int(extra_dice),
        "hot_dice": HOT_SIM_DICE + int(extra_dice),
    }


#: accessory field -> host ASDF key
_HOST_MODS = {
    "modattack": "attack",
    "modsleaze": "sleaze",
    "moddataprocessing": "dataprocessing",
    "modfirewall": "firewall",
}


def apply_host_matrix_mods(hosts: list[dict[str, Any]], gear_rows: list[dict[str, Any]]) -> None:
    """Add what a plugged-in accessory gives its host's ASDF: an Attack Dongle
    (DT p.61) turns a commlink into something that can hack — Attack equal to
    its Rating — and a Stealth Dongle does the same for Sleaze. The host row
    grows the keys it lacked (a commlink only publishes DP / Firewall)."""
    by_id = {str(row.get("id") or ""): row for row in hosts}
    for row in gear_rows:
        host = by_id.get(str(row.get("parent_id") or ""))
        if host is None:
            continue
        spec = _item_by_id("gear", str(row.get("gear_id") or ""))
        if not spec:
            continue
        rating = int(row.get("rating") or 1)
        for field, key in _HOST_MODS.items():
            raw = str(spec.get(field) or "").strip()
            if not raw:
                continue
            delta = int(eval_formula(raw, rating, 0))
            if delta:
                host[key] = int(host.get(key) or 0) + delta
