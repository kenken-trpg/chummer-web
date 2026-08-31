"""Primitives shared across the gear resolvers.

Kept tiny and dependency-light (``eval_formula`` + the ``GearInstall`` model)
so every ``gear/`` submodule and ``app.engine`` itself can import them without a
cycle. A couple of leaf helpers the ware pipeline also reaches for
(``_limb_attr_effect``) live here for the same reason.
"""

from __future__ import annotations

import re
from typing import Any

from ...data_loader import catalog, eval_formula
from ...models import GearInstall

SENSOR_DEVICE_CATEGORIES = {"Sensors"}


def _capacity_value(expr: str | None, rating: int) -> float:
    raw = (expr or "").strip()
    if not raw or raw == "*":
        return 0.0
    if "/" in raw:
        raw = raw.split("/", 1)[0].strip()
    return eval_formula(raw, rating, default=0.0)


def _cascade_optics(items: list[GearInstall], extra_parents: set[str] | None = None) -> list[GearInstall]:
    """Drop installs whose ``parent_id`` points at something no longer present,
    repeating until the set is stable (a removed parent can orphan a chain)."""
    ids = {item.id for item in items} | set(extra_parents or [])
    keep = [item for item in items if not item.parent_id or item.parent_id in ids]
    if len(keep) == len(items):
        return keep
    return _cascade_optics(keep, extra_parents)


def _program_label(spec: dict[str, Any], extra: str | None) -> str:
    """Display name for a program / app / autosoft, folding the chosen ``extra``
    into any ``[Model]`` / ``[Weapon]`` placeholder in the catalog name."""
    name = str(spec.get("name") or "")
    extra = (extra or "").strip()
    if extra:
        for token in ("[Model]", "[Weapon]"):
            if token in name:
                return f"{name.replace(token, '').strip()} ({extra})"
        return f"{name} ({extra})"
    return name


def _clamp_rating(spec: dict[str, Any], rating: int) -> int:
    max_rating = int(spec.get("maxrating") or 0)
    if max_rating <= 0:
        return 1
    min_rating = max(1, int(spec.get("minrating") or 1))
    return max(min_rating, min(max_rating, int(rating or min_rating)))


def _device_rating_of(spec: dict[str, Any] | None, rating: int) -> int:
    raw = str((spec or {}).get("devicerating") or "").strip()
    if raw and raw not in {"0", "-"}:
        return max(0, int(eval_formula(raw, rating, 0)))
    if str((spec or {}).get("category") or "") in SENSOR_DEVICE_CATEGORIES:
        return max(0, int(rating or 0))
    return 0


def _has_weapon_constraints(cons: dict[str, Any] | None) -> bool:
    if not cons:
        return False
    return bool(cons.get("names") or cons.get("categories") or cons.get("types") or cons.get("conceal_lte") is not None)


def _weapon_matches_or(weapon: dict[str, Any], cons: dict[str, Any] | None) -> bool:
    if not _has_weapon_constraints(cons):
        return False
    cons = cons or {}
    name = str(weapon.get("name") or "")
    category = str(weapon.get("category") or "")
    typ = str(weapon.get("type") or "")
    try:
        conceal = int(float(str(weapon.get("conceal") or "0")))
    except ValueError:
        conceal = 0
    if name in (cons.get("names") or []):
        return True
    if category in (cons.get("categories") or []):
        return True
    if typ in (cons.get("types") or []):
        return True
    if cons.get("conceal_lte") is not None and conceal <= int(cons["conceal_lte"]):
        return True
    return False


def accessory_fits_weapon(acc: dict[str, Any], weapon: dict[str, Any], installed_names: set[str]) -> bool:
    required = acc.get("required") or {}
    forbidden = acc.get("forbidden") or {}
    if _has_weapon_constraints(required) and not _weapon_matches_or(weapon, required):
        return False
    if _weapon_matches_or(weapon, forbidden):
        return False
    for name in forbidden.get("accessories") or []:
        if name in installed_names:
            return False
    mounts = list(acc.get("mounts") or [])
    weapon_mounts = set(weapon.get("mounts") or [])
    if mounts and not any(mount in weapon_mounts or mount == "Internal" for mount in mounts):
        return False
    return True


def _pick_accessory_mount(weapon_mounts: list[str], used: set[str], acc_mounts: list[str]) -> str | None:
    if not acc_mounts:
        return ""
    options = [mount for mount in acc_mounts if mount in weapon_mounts or mount == "Internal"]
    if not options:
        return None
    for mount in options:
        if mount not in used:
            return mount
    return None


def _find_mount_part(name: str, category: str, prefer_source: str = "") -> dict[str, Any] | None:
    parts = [item for item in catalog().get("weapon_mounts") or [] if item.get("category") == category]
    if prefer_source == "SR5":
        tagged = next((item for item in parts if item["name"] == f"{name} [SR5]"), None)
        if tagged:
            return tagged
    exact = next((item for item in parts if item["name"] == name), None)
    if exact:
        return exact
    return next((item for item in parts if item["name"] == f"{name} [SR5]"), None)


def _default_mount_parts(size: dict[str, Any]) -> dict[str, dict[str, Any] | None]:
    parts = catalog().get("weapon_mounts") or []

    def pick(category: str, names: list[str]) -> dict[str, Any] | None:
        for name in names:
            found = next((item for item in parts if item.get("category") == category and item["name"] == name), None)
            if found:
                return found
        return None

    required = size.get("required_parts") or {}
    if any(name == "None" for name in (required.get("control") or [])):
        return {
            "visibility": pick("Visibility", ["None"]),
            "flexibility": pick("Flexibility", ["None"]),
            "control": pick("Control", ["None"]),
        }
    if size.get("source") == "SR5":
        req_vis = list(required.get("visibility") or ["External [SR5]"])
        req_flex = list(required.get("flexibility") or ["Flexible [SR5]"])
        req_ctrl = list(required.get("control") or ["Remote [SR5]"])
        return {
            "visibility": pick("Visibility", req_vis),
            "flexibility": pick("Flexibility", req_flex),
            "control": pick("Control", req_ctrl),
        }
    return {
        "visibility": pick("Visibility", ["External", "External [SR5]"]),
        "flexibility": pick("Flexibility", ["Fixed", "Flexible [SR5]"]),
        "control": pick("Control", ["Remote", "Remote [SR5]"]),
    }


def _leading_vehicle_stat(raw: str | None) -> int:
    match = re.match(r"^([+-]?\d+)", str(raw or "").strip())
    if not match:
        return 0
    return int(match.group(1))


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
