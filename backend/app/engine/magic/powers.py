"""Adept power resolution.

``resolve_adept_powers`` prices the character's chosen powers (levels, Way
discounts, Mystic Adept power points) and emits the bonus nodes each power
grants. The ``power_*`` helpers (cost, max rating, select options, bonus
binding) are also used by the mentor and Qi-focus resolvers.

Imports only ``catalog`` / ``eval_formula`` / already-extracted engine modules
/ models — never back into ``app.engine``.
"""

from __future__ import annotations

from typing import Any

from ...data_loader import SPELL_CAST_CATEGORIES, catalog
from ...improvements import substitute_rating
from ...models import CharacterState
from ..constants import ADEPT_TALENTS, ENHANCEMENT_KARMA
from ..formulas import _ceil_div
from ..lookups import _enhancement_by_id, _power_by_id, _power_by_name
from ..selects import parse_selectskill_spec, selectskill_options
from ._common import spell_cast_info


def power_point_cost(spec: dict[str, Any], rating: int, discounted: bool = False) -> float:
    points = float(spec.get("points") or 0)
    extra = float(spec.get("extrapointcost") or 0)
    rating = max(1, int(rating))
    if spec.get("levels"):
        cost = points * rating
        if extra:
            cost += extra
    else:
        cost = points
    if discounted:
        cost = max(0.0, cost - float(spec.get("adeptway") or 0))
    return round(cost, 4)


def way_discount_cap(mag: int) -> float:
    return float(_ceil_div(max(int(mag), 0) / 4))


def way_discount_eligible(spec: dict[str, Any], quality_names: set[str], magicians_way: bool) -> bool:
    if not float(spec.get("adeptway") or 0):
        return False
    if magicians_way and not spec.get("magicianswayforbids"):
        return True
    return any(name in quality_names for name in (spec.get("adeptwayrequires") or []))


def power_max_rating(spec: dict[str, Any], mag: int) -> int:
    if not spec.get("levels"):
        return 1
    if spec.get("maxlevels"):
        return int(spec["maxlevels"])
    if str(spec.get("name") or "").startswith("Improved Ability"):
        return max(1, _ceil_div(max(int(mag), 1) / 2))
    return max(1, int(mag))


def _field_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if value:
        return [str(value)]
    return []


def bind_power_bonus(nodes: list[dict[str, Any]], extra: str, rating: int) -> list[dict[str, Any]]:
    bound: list[dict[str, Any]] = []
    for node in substitute_rating(nodes, rating):
        tag = node.get("tag")
        fields = dict(node.get("fields") or {})
        if tag == "selectskill":
            if not extra:
                continue
            fields["name"] = extra
            bound.append({"tag": "specificskill", "fields": fields})
            continue
        if tag == "selectattribute":
            bonus = fields.get("val") or fields.get("bonus") or fields.get("value")
            if not extra or bonus in (None, ""):
                continue
            bound.append({"tag": "specificattribute", "fields": {"name": extra, "bonus": bonus}})
            continue
        if tag == "selectspell":
            continue
        bound.append(node)
    return bound


def power_select_options(spec: dict[str, Any], skills_data: dict[str, Any]) -> list[str]:
    kind = spec.get("select")
    if kind == "skill":
        node = next((item for item in (spec.get("bonus") or []) if item.get("tag") == "selectskill"), None)
        if not node:
            return []
        parsed = parse_selectskill_spec(node)
        parsed["minimumrating"] = 0
        return selectskill_options(parsed, skills_data, {})
    if kind == "attribute":
        node = next((item for item in (spec.get("bonus") or []) if item.get("tag") == "selectattribute"), None)
        if not node:
            return []
        return _field_list((node.get("fields") or {}).get("attribute"))
    if kind == "spell":
        return [item["name"] for item in catalog().get("spells") or [] if item.get("category") in SPELL_CAST_CATEGORIES]
    return []


def resolve_adept_powers(
    state: CharacterState,
    talent_name: str,
    mag: int,
    skills_data: dict[str, Any],
    quality_names: set[str],
    magicians_way: bool,
    free_powers: list[dict[str, Any]] | None = None,
    wil: int = 1,
    intuition: int = 1,
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    public: list[dict[str, Any]] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    spent = 0.0
    discount_used = 0.0
    if talent_name not in ADEPT_TALENTS:
        return {
            "warnings": warnings,
            "errors": errors,
            "public": public,
            "bonus_sources": bonus_sources,
            "spent": 0.0,
            "discount_used": 0.0,
            "discount_max": 0.0,
            "mystic_pp": 0,
            "power_names": set(),
        }

    free_by_key: dict[tuple[str, str], int] = {}
    free_notes: dict[tuple[str, str], list[str]] = {}
    for gift in free_powers or []:
        spec = _power_by_id(gift["power_id"]) or _power_by_name(gift.get("name") or "")
        if not spec:
            continue
        extra = (gift.get("extra") or "").strip()
        key = (spec["id"], extra)
        free_by_key[key] = free_by_key.get(key, 0) + max(1, int(gift.get("rating") or 1))
        free_notes.setdefault(key, []).append(gift.get("source") or "無料")

    installed_names = set()
    for inst in state.adept_powers:
        spec = _power_by_id(inst.power_id)
        if spec:
            installed_names.add(spec["name"])
    for key, _rating in free_by_key.items():
        spec = _power_by_id(key[0])
        if spec:
            installed_names.add(spec["name"])

    seen_keys: set[tuple[str, str]] = set()
    cap_limit = way_discount_cap(mag)
    for inst in state.adept_powers:
        spec = _power_by_id(inst.power_id)
        if not spec:
            continue
        cap = power_max_rating(spec, mag)
        extra = (inst.extra or "").strip()
        key = (spec["id"], extra)
        free_levels = free_by_key.get(key, 0)
        paid_max = max(1, cap - free_levels) if spec.get("levels") else 1
        rating = 1 if not spec.get("levels") else max(1, min(paid_max, int(inst.rating or 1)))
        inst.rating = rating
        options = power_select_options(spec, skills_data)
        kind = spec.get("select")
        select_label = {"skill": "技能", "attribute": "能力値", "spell": "呪文"}.get(kind or "", "対象")
        if kind and extra and extra not in options:
            warnings.append(f"{spec['name']} の指定が無効です（{extra}）")
            extra = ""
            inst.extra = None
            key = (spec["id"], extra)
            free_levels = free_by_key.get(key, 0)
        if kind and not extra:
            warnings.append(f"{spec['name']} の{select_label}を選んでください")
        spell = (
            spell_cast_info(extra, inst.force, mag, wil + intuition, "WIL+INT") if kind == "spell" and extra else None
        )
        if spell:
            inst.force = int(spell["force"])
        if kind and extra and key in seen_keys:
            warnings.append(f"{spec['name']}（{extra}）が重複しています")
        seen_keys.add(key)
        for needed in spec.get("required") or []:
            if needed not in installed_names:
                warnings.append(f"{spec['name']} には {needed} が必要です")
        eligible = way_discount_eligible(spec, quality_names, magicians_way)
        discounted = bool(inst.discounted) and eligible
        if discounted and discount_used + float(spec.get("adeptway") or 0) > cap_limit + 1e-9:
            discounted = False
            warnings.append(f"{spec['name']} の Way 割引は上限（MAG/4）を超えるため無効です")
        inst.discounted = discounted
        if discounted:
            discount_used += float(spec.get("adeptway") or 0)
        full_cost = power_point_cost(spec, rating, False)
        cost = 0.0 if (not spec.get("levels") and free_levels) else power_point_cost(spec, rating, discounted)
        spent += cost
        total_rating = rating if not spec.get("levels") else min(cap, rating + free_levels)
        if not spec.get("levels") and free_levels:
            total_rating = 1
        bonus_sources.append((spec["name"], bind_power_bonus(spec.get("bonus") or [], extra, total_rating)))
        public.append(
            {
                "id": inst.id,
                "power_id": spec["id"],
                "name": spec["name"],
                "rating": rating,
                "total_rating": total_rating,
                "free_levels": free_levels,
                "rating_min": 1,
                "rating_max": paid_max,
                "extra": extra,
                "cost": cost,
                "full_cost": full_cost,
                "discounted": discounted,
                "can_discount": eligible,
                "select": kind,
                "options": options,
                "source": spec.get("source"),
                "page": spec.get("page"),
                "notes": list(free_notes.get(key) or []),
                "spell": spell,
            }
        )
        free_by_key.pop(key, None)

    for key, free_levels in free_by_key.items():
        spec = _power_by_id(key[0])
        if not spec:
            continue
        extra = key[1]
        cap = power_max_rating(spec, mag)
        total_rating = 1 if not spec.get("levels") else min(cap, free_levels)
        options = power_select_options(spec, skills_data)
        bonus_sources.append((spec["name"], bind_power_bonus(spec.get("bonus") or [], extra, total_rating)))
        public.append(
            {
                "id": f"free:{spec['id']}:{extra}",
                "power_id": spec["id"],
                "name": spec["name"],
                "rating": 0,
                "total_rating": total_rating,
                "free_levels": free_levels,
                "rating_min": 0,
                "rating_max": 0,
                "extra": extra,
                "cost": 0.0,
                "full_cost": 0.0,
                "discounted": False,
                "can_discount": False,
                "select": spec.get("select"),
                "options": options,
                "source": spec.get("source"),
                "page": spec.get("page"),
                "notes": list(free_notes.get(key) or []),
                "free_only": True,
            }
        )

    if discount_used > cap_limit + 1e-9:
        errors.append(f"Way割引が上限を超えています（使用 {discount_used:g} / 上限 {cap_limit:g}）")

    return {
        "warnings": warnings,
        "errors": errors,
        "public": public,
        "bonus_sources": bonus_sources,
        "spent": round(spent, 4),
        "discount_used": round(discount_used, 4),
        "discount_max": cap_limit,
        "mystic_pp": max(0, min(int(mag), int(state.mystic_pp or 0))) if talent_name == "Mystic Adept" else 0,
        "power_names": installed_names,
    }


def resolve_enhancements(
    state: CharacterState,
    talent_name: str,
    quality_names: set[str],
    power_names: set[str],
) -> dict[str, Any]:
    warnings: list[str] = []
    public: list[dict[str, Any]] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    kept: list[str] = []
    if talent_name not in ADEPT_TALENTS:
        state.adept_enhancements = []
        return {"warnings": warnings, "public": public, "bonus_sources": bonus_sources, "karma": 0}
    for eid in state.adept_enhancements:
        spec = _enhancement_by_id(eid)
        if not spec:
            continue
        req = spec.get("required") or {}
        missing_quality = [name for name in (req.get("quality") or []) if name not in quality_names]
        missing_power = [name for name in (req.get("power") or []) if name not in power_names]
        if spec.get("power") and spec["power"] not in power_names and spec["power"] not in missing_power:
            missing_power.append(spec["power"])
        if missing_quality:
            warnings.append(f"{spec['name']} は {' / '.join(missing_quality)} が外れたため削除しました")
            continue
        missing = missing_power
        if missing:
            warnings.append(f"{spec['name']} には {' / '.join(missing)} が必要です")
        kept.append(spec["id"])
        bonus_sources.append((spec["name"], spec.get("bonus") or []))
        public.append(
            {
                "id": spec["id"],
                "name": spec["name"],
                "power": spec.get("power"),
                "karma": ENHANCEMENT_KARMA,
                "source": spec.get("source"),
                "page": spec.get("page"),
                "ok": not missing,
            }
        )
    state.adept_enhancements = kept
    return {
        "warnings": warnings,
        "public": public,
        "bonus_sources": bonus_sources,
        "karma": ENHANCEMENT_KARMA * len(kept),
    }
