"""Contact resolution, plus the Ex-Con / Erased quality consequences that ride
alongside it.

``sync_quality_contacts`` keeps quality-granted contacts in sync;
``resolve_contacts`` prices the contact network (free points, chargen cost cap,
Ex-Con loyalty floors). ``apply_erased_lifestyle_cap`` and
``apply_excon_ware_ban`` enforce the two quality caps that touch lifestyles and
'ware.

Imports only ``catalog`` / already-extracted engine modules / models — never
back into ``app.engine``.
"""

from __future__ import annotations

from typing import Any

from ..data_loader import catalog
from ..improvements import EffectsDict
from ..models import CharacterState, ContactInstall
from .bundle_types import ContactsBundle, GearBundle
from .constants import (
    CONTACT_CHARGEN_COST_MAX,
    CONTACT_FREE_MULT,
    CONTACT_RATING_MAX,
    CONTACT_RATING_MIN,
    ERASED_LIFESTYLE_FORBIDDEN,
    EXCON_CORP_ROLE_HINTS,
    EXCON_LAW_ROLE_HINTS,
)


def sync_quality_contacts(
    state: CharacterState,
    effects: EffectsDict,
    qualities: list[dict[str, Any]],
) -> list[str]:
    """Create/update free contacts granted by addcontact qualities; drop orphans."""
    warnings: list[str] = []
    by_name = {q["name"]: q for q in qualities}
    specs: list[dict[str, Any]] = []
    for entry in effects.get("add_contacts") or []:
        q = by_name.get(str(entry.get("source") or "").strip())
        if not q:
            continue
        specs.append({**entry, "quality_id": q["id"], "quality_name": q["name"]})
    wanted = {str(s["quality_id"]) for s in specs}

    remaining: list[ContactInstall] = []
    for inst in state.contacts or []:
        sq = str(inst.source_quality_id or "").strip()
        if sq and sq not in wanted:
            continue
        remaining.append(inst)

    existing = {str(inst.source_quality_id): inst for inst in remaining if str(inst.source_quality_id or "").strip()}
    for spec in specs:
        qid = str(spec["quality_id"])
        connection = max(CONTACT_RATING_MIN, min(CONTACT_RATING_MAX, int(spec.get("connection") or 1)))
        loyalty = max(CONTACT_RATING_MIN, min(CONTACT_RATING_MAX, int(spec.get("loyalty") or 1)))
        forced = spec.get("forced_loyalty")
        forced_i = int(forced) if forced is not None else None
        if forced_i is not None:
            loyalty = max(loyalty, max(CONTACT_RATING_MIN, min(CONTACT_RATING_MAX, forced_i)))
        is_free = bool(spec.get("free"))
        is_group = bool(spec.get("group") or spec.get("force_group"))
        force_group = bool(spec.get("force_group"))
        if qid in existing:
            inst = existing[qid]
            if forced_i is not None:
                inst.forced_loyalty = forced_i
                inst.loyalty = max(int(inst.loyalty or 1), forced_i)
            if force_group or is_group:
                inst.group = True
            inst.force_group = force_group or bool(inst.force_group)
            inst.free = is_free or bool(inst.free)
            if is_free:
                inst.free_connection = max(int(inst.free_connection or 0), connection)
                inst.free_loyalty = max(int(inst.free_loyalty or 0), loyalty)
                inst.connection = max(int(inst.connection or 1), connection)
                inst.loyalty = max(int(inst.loyalty or 1), loyalty)
            continue
        remaining.append(
            ContactInstall(
                name=str(spec.get("quality_name") or ""),
                connection=connection,
                loyalty=loyalty,
                group=is_group,
                free=is_free,
                forced_loyalty=forced_i,
                force_group=force_group,
                source_quality_id=qid,
                free_connection=connection if is_free else 0,
                free_loyalty=loyalty if is_free else 0,
            )
        )
    state.contacts = remaining
    return warnings


def _contact_billable_points(inst: ContactInstall, connection: int, loyalty: int) -> int:
    total = connection + loyalty
    if not inst.free and not int(inst.free_connection or 0) and not int(inst.free_loyalty or 0):
        return total
    baseline = max(0, int(inst.free_connection or 0)) + max(0, int(inst.free_loyalty or 0))
    return max(0, total - baseline)


def _excon_contact_loyalty_min(role: str) -> int:
    text = (role or "").strip().lower()
    if not text:
        return CONTACT_RATING_MIN
    if any(hint in text for hint in EXCON_LAW_ROLE_HINTS):
        return 5
    if any(hint in text for hint in EXCON_CORP_ROLE_HINTS):
        return 4
    return CONTACT_RATING_MIN


def _erased_lifestyle_too_high(name: str, cost: int, medium_cost: int) -> bool:
    if name in ERASED_LIFESTYLE_FORBIDDEN:
        return True
    return int(cost or 0) > int(medium_cost)


def apply_erased_lifestyle_cap(gear: GearBundle, erased: bool, warnings: list[str]) -> None:
    if not erased:
        return
    medium = next((row for row in (catalog().get("lifestyles") or []) if row.get("name") == "Medium"), None)
    medium_cost = int((medium or {}).get("cost") or 5000)
    for row in gear.get("lifestyles") or []:
        name = str(row.get("name") or "")
        base = int(row.get("base_monthly") or row.get("monthly") or row.get("cost") or 0)
        if _erased_lifestyle_too_high(name, base, medium_cost):
            warnings.append(f"Erased は Medium より高いライフスタイルを維持できません（{name}）")


def apply_excon_ware_ban(ware_items: list[dict[str, Any]], excon: bool, errors: list[str]) -> None:
    if not excon:
        return
    for item in ware_items or []:
        suffix = str(item.get("avail_suffix") or "").upper()
        if suffix in {"R", "F"}:
            label = "制限" if suffix == "R" else "禁止"
            errors.append(f"Ex-Con は{label}ウェアを装着できません（{item.get('name') or 'ウェア'}）")


def resolve_contacts(
    state: CharacterState,
    cha: int,
    *,
    career: bool = False,
    friends_in_high_places: bool = False,
    black_market_contact_id: str = "",
    contact_karma_adj: int = 0,
    contact_karma_min: int = 0,
    excon: bool = False,
) -> ContactsBundle:
    warnings: list[str] = []
    public: list[dict[str, Any]] = []
    kept: list[ContactInstall] = []
    used = 0
    free_max = max(0, int(cha or 0) * CONTACT_FREE_MULT)
    bmp_id = str(black_market_contact_id or "").strip()
    for inst in state.contacts or []:
        name = (inst.name or "").strip()
        role = (inst.role or "").strip()
        connection = max(CONTACT_RATING_MIN, min(CONTACT_RATING_MAX, int(inst.connection or 1)))
        loyalty = max(CONTACT_RATING_MIN, min(CONTACT_RATING_MAX, int(inst.loyalty or 1)))
        forced = inst.forced_loyalty
        if forced is not None:
            loyalty = max(loyalty, max(CONTACT_RATING_MIN, min(CONTACT_RATING_MAX, int(forced))))
        if inst.force_group:
            inst.group = True
        chargen_pair_max = 12 if friends_in_high_places else CONTACT_CHARGEN_COST_MAX
        quality_granted = bool(inst.source_quality_id) or bool(inst.free)
        if not career and not quality_granted and connection + loyalty > chargen_pair_max:
            loyalty = max(CONTACT_RATING_MIN, chargen_pair_max - connection)
            if forced is not None and loyalty < int(forced):
                # Prefer keeping forced loyalty; clamp connection instead.
                loyalty = max(CONTACT_RATING_MIN, min(CONTACT_RATING_MAX, int(forced)))
                connection = max(CONTACT_RATING_MIN, chargen_pair_max - loyalty)
            warnings.append(f"{name or 'コンタクト'} は作成時 Connection+Loyalty が{chargen_pair_max}までです")
        excon_loy_min = _excon_contact_loyalty_min(role) if excon else CONTACT_RATING_MIN
        if excon and loyalty < excon_loy_min:
            warnings.append(
                f"Ex-Con の {name or 'コンタクト'}（{role or '役割なし'}）は Loyalty {excon_loy_min} 以上が必要です"
            )
            loyalty = excon_loy_min
            if not career and not quality_granted and connection + loyalty > chargen_pair_max:
                connection = max(CONTACT_RATING_MIN, chargen_pair_max - loyalty)
        inst.name = name
        inst.role = role or None
        inst.connection = connection
        inst.loyalty = loyalty
        billable = _contact_billable_points(inst, connection, loyalty)
        cost = connection + loyalty
        if not name:
            warnings.append("名前のないコンタクトがあります")
        kept.append(inst)
        used += billable
        if quality_granted:
            conn_max = 12 if friends_in_high_places or career else CONTACT_RATING_MAX
            loy_max = CONTACT_RATING_MAX
        elif career or friends_in_high_places:
            conn_max = 12 if friends_in_high_places else CONTACT_RATING_MAX
            loy_max = (
                CONTACT_RATING_MAX
                if career
                else min(CONTACT_RATING_MAX, (12 if friends_in_high_places else CONTACT_CHARGEN_COST_MAX) - connection)
            )
            if friends_in_high_places and not career:
                conn_max = min(12, (12 - loyalty))
                loy_max = min(CONTACT_RATING_MAX, 12 - connection)
        else:
            conn_max = min(CONTACT_RATING_MAX, CONTACT_CHARGEN_COST_MAX - loyalty)
            loy_max = min(CONTACT_RATING_MAX, CONTACT_CHARGEN_COST_MAX - connection)
        if forced is not None:
            loy_min = max(CONTACT_RATING_MIN, int(forced))
        else:
            loy_min = CONTACT_RATING_MIN
        loy_min = max(loy_min, excon_loy_min)
        public.append(
            {
                "id": inst.id,
                "name": name,
                "role": role,
                "connection": connection,
                "loyalty": loyalty,
                "cost": cost,
                "billable": billable,
                "connection_max": conn_max,
                "loyalty_max": loy_max,
                "loyalty_min": loy_min,
                "group": bool(inst.group),
                "free": bool(inst.free),
                "forced_loyalty": int(forced) if forced is not None else None,
                "source_quality_id": inst.source_quality_id,
                "locked": bool(inst.source_quality_id),
                "black_market_pipeline": bool(bmp_id and inst.id == bmp_id),
            }
        )
    state.contacts = kept
    paid_points = max(0, used - free_max)
    per_point = max(int(contact_karma_min), 1 + int(contact_karma_adj))
    karma = paid_points * max(0, per_point)
    return {
        "warnings": warnings,
        "public": public,
        "used": used,
        "free": free_max,
        "paid": paid_points,
        "karma": karma,
        "karma_per_point": per_point,
    }
