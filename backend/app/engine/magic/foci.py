"""Focus resolution: bonded foci, Qi foci, and the weapon-focus bridge.

``resolve_foci`` prices bonded foci (crafted vs. bought, formula + reagent
cost, bonding karma) and emits their bonus nodes; ``resolve_qi_foci`` does the
same for the adept Qi focus, converting Force into granted power ratings.
``attach_weapon_focus_dice`` wires a weapon focus onto its chosen weapon row,
``apply_focus_limits`` enforces the MAG count / Force caps, and
``attach_focus_tests`` builds the Artificing / Arcana crafting tests.

Imports only ``catalog`` / ``eval_formula`` / already-extracted engine modules
/ models — never back into ``app.engine``.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from ...data_loader import catalog, eval_formula
from ...improvements import substitute_rating
from ...models import CharacterState, FocusInstall, QiFocusInstall
from ..bundle_types import FociBundle, FocusLimits, QiFociBundle
from ..constants import ADEPT_TALENTS, FOCUS_FORCE_MULT, FOCUS_TALENTS, QI_FOCUS_NAME, SPIRIT_REAGENT_YEN
from ..dice import magic_opposed_test
from ..formulas import _ceil_div
from ..lookups import _focus_by_id, _power_by_id
from .powers import power_max_rating, power_point_cost, power_select_options


def focus_bind_karma(name: str, force: int, focus_binding: Sequence[Mapping[str, Any]]) -> int:
    bind = int(force)
    for mod in focus_binding:
        if (mod.get("name") or "") != name:
            continue
        bind += int(mod.get("val") or 0)
    return max(0, bind)


def qi_focus_granted_power_rating(
    spec: dict[str, Any],
    force: int,
    user_rating: int,
    mag: int,
    select_power: dict[str, Any] | None,
) -> int:
    cfg = select_power or {}
    if not cfg.get("ignore_rating"):
        cap = power_max_rating(spec, mag)
        return (
            max(1, min(cap, int(user_rating or 1)))
            if not spec.get("levels")
            else max(1, min(cap, int(user_rating or 1)))
        )
    points_per_level = float(cfg.get("points_per_level") or 0.25)
    pp_pool = max(0.0, force * points_per_level)
    if not spec.get("levels"):
        cost = power_point_cost(spec, 1, False)
        return 1 if pp_pool + 1e-9 >= cost else 0
    unit = power_point_cost(spec, 1, False)
    if unit <= 0:
        return 0
    granted = int(pp_pool / unit)
    if cfg.get("limit_expr") == "Rating":
        granted = min(granted, force)
    granted = min(granted, power_max_rating(spec, mag))
    if granted <= 0:
        return 0
    return min(max(1, int(user_rating or 1)), granted)


def resolve_qi_foci(
    state: CharacterState,
    talent_name: str,
    mag: int,
    skills_data: dict[str, Any],
    focus_binding: Sequence[Mapping[str, Any]],
) -> QiFociBundle:
    warnings: list[str] = []
    errors: list[str] = []
    public: list[dict[str, Any]] = []
    free_powers: list[dict[str, Any]] = []
    nuyen = 0
    karma = 0
    if talent_name not in ADEPT_TALENTS:
        state.qi_foci = []
        return {
            "warnings": warnings,
            "errors": errors,
            "public": public,
            "free_powers": free_powers,
            "nuyen": 0,
            "karma": 0,
        }
    gear = catalog().get("qi_focus") or {"maxrating": 6, "cost": "Rating * 3000"}
    max_force = int(gear.get("maxrating") or 6)
    select_power = gear.get("select_power") if isinstance(gear.get("select_power"), dict) else None
    points_per_level = float((select_power or {}).get("points_per_level") or gear.get("pointsperlevel") or 0.25)
    kept: list[QiFocusInstall] = []
    for inst in state.qi_foci:
        spec = _power_by_id(inst.power_id)
        if not spec:
            continue
        cap = power_max_rating(spec, mag)
        requested_rating = 1 if not spec.get("levels") else max(1, min(cap, int(inst.power_rating or 1)))
        extra = (inst.extra or "").strip()
        options = power_select_options(spec, skills_data)
        kind = spec.get("select")
        if kind and extra and extra not in options:
            warnings.append(f"気焦点の {spec['name']} の指定が無効です（{extra}）")
            extra = ""
            inst.extra = None
        if kind and not extra:
            warnings.append(f"気焦点の {spec['name']} の対象を選んでください")
        power_rating = qi_focus_granted_power_rating(spec, int(inst.rating or 1), requested_rating, mag, select_power)
        if select_power and select_power.get("ignore_rating") and power_rating <= 0:
            warnings.append(f"気焦点の Force が {spec['name']} に不足しています")
            continue
        needed = max(
            1,
            _ceil_div(power_point_cost(spec, max(1, requested_rating), False) / points_per_level),
        )
        force = max(needed, min(max_force, int(inst.rating or needed)))
        inst.rating = force
        power_rating = qi_focus_granted_power_rating(spec, force, requested_rating, mag, select_power)
        inst.power_rating = power_rating if power_rating > 0 else requested_rating
        label = spec["name"] + (f" ({extra})" if extra else "")
        bind = force
        for mod in focus_binding:
            if (mod.get("name") or "") != QI_FOCUS_NAME:
                continue
            contains = (mod.get("extracontains") or "").strip()
            if contains and contains not in {label, spec["name"]}:
                continue
            bind += int(mod.get("val") or 0)
        bind = max(0, bind)
        cost = force * 3000
        nuyen += cost
        karma += bind
        free_powers.append(
            {
                "power_id": spec["id"],
                "name": spec["name"],
                "rating": max(1, power_rating) if not spec.get("levels") else power_rating,
                "extra": extra,
                "source": f"Qi Focus F{force}",
            }
        )
        public.append(
            {
                "id": inst.id,
                "rating": force,
                "rating_min": needed,
                "rating_max": max_force,
                "power_id": spec["id"],
                "name": spec["name"],
                "power_rating": power_rating,
                "power_rating_max": cap,
                "extra": extra,
                "select": kind,
                "options": options,
                "nuyen": cost,
                "karma": bind,
                "source": gear.get("source"),
            }
        )
        kept.append(inst)
    state.qi_foci = kept
    return {
        "warnings": warnings,
        "errors": errors,
        "public": public,
        "free_powers": free_powers,
        "nuyen": nuyen,
        "karma": karma,
    }


def resolve_foci(
    state: CharacterState,
    talent_name: str,
    mag: int,
    focus_binding: Sequence[Mapping[str, Any]],
) -> FociBundle:
    warnings: list[str] = []
    public: list[dict[str, Any]] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    nuyen = 0
    karma = 0
    if talent_name not in FOCUS_TALENTS:
        state.foci = []
        return {
            "warnings": warnings,
            "public": public,
            "bonus_sources": bonus_sources,
            "nuyen": 0,
            "karma": 0,
        }
    kept: list[FocusInstall] = []
    max_force = max(1, int(mag or 0))
    for inst in state.foci:
        spec = _focus_by_id(inst.gear_id)
        if not spec:
            continue
        cap = min(int(spec.get("maxrating") or 6), max_force) if mag else 0
        if cap <= 0:
            warnings.append(f"{spec['name']} を結合するには魔力が必要です")
            continue
        force = max(1, min(cap, int(inst.force or 1)))
        inst.force = force
        crafted = bool(inst.crafted)
        formula_bought = bool(inst.formula_bought) if crafted else False
        inst.crafted = crafted
        inst.formula_bought = formula_bought
        extra = (inst.extra or "").strip()
        needs_weapon = bool(spec.get("needs_weapon"))
        weapon_type = str(spec.get("weapon_type") or "")
        if needs_weapon:
            inst.extra = extra or None
        else:
            inst.extra = None
            extra = ""
        formula = spec.get("formula") or {}
        if crafted:
            reagent = force * SPIRIT_REAGENT_YEN
            formula_cost = int(eval_formula(str(formula.get("cost") or "0"), force, 0)) if formula_bought else 0
            if formula_bought and not formula:
                warnings.append(f"{spec['name']} の術式データが見つからないため、術式代は0¥にしました")
            cost = formula_cost + reagent
        else:
            cost = int(eval_formula(str(spec.get("cost") or "0"), force, 0))
            formula_cost = 0
            reagent = 0
        bind = focus_bind_karma(spec["name"], force, focus_binding)
        nuyen += cost
        karma += bind
        nodes = [
            node
            for node in substitute_rating(list(spec.get("bonus") or []), force)
            if node.get("tag") != "weaponspecificdice"
        ]
        label = f"{spec['name']} F{force}"
        bonus_sources.append((label, nodes))
        public.append(
            {
                "id": inst.id,
                "gear_id": spec["id"],
                "name": spec["name"],
                "force": force,
                "force_max": cap,
                "nuyen": cost,
                "karma": bind,
                "crafted": crafted,
                "formula_bought": formula_bought,
                "formula_nuyen": formula_cost,
                "reagent_nuyen": reagent,
                "retail_nuyen": int(eval_formula(str(spec.get("cost") or "0"), force, 0)),
                "hits": inst.hits,
                "opposed_hits": inst.opposed_hits,
                "effect": spec.get("effect") or "",
                "avail": spec.get("avail") or "",
                "needs_weapon": needs_weapon,
                "weapon_type": weapon_type,
                "weapon_id": extra if needs_weapon else "",
                "weapon_name": "",
                "weapon_dice": force if needs_weapon else 0,
                "weapon_options": [],
                "formula": (
                    {
                        "id": formula.get("id"),
                        "name": formula.get("name"),
                        "cost": formula.get("cost") or "",
                    }
                    if formula
                    else None
                ),
                "source": spec.get("source"),
                "page": spec.get("page"),
            }
        )
        kept.append(inst)
    state.foci = kept
    return {
        "warnings": warnings,
        "public": public,
        "bonus_sources": bonus_sources,
        "nuyen": nuyen,
        "karma": karma,
    }


def attach_weapon_focus_dice(
    state: CharacterState,
    foci_public: list[dict[str, Any]],
    weapons: list[dict[str, Any]],
    warnings: list[str],
) -> None:
    by_id = {str(item.get("id") or ""): item for item in weapons if item.get("id")}
    for focus in foci_public:
        if not focus.get("needs_weapon"):
            continue
        weapon_type = str(focus.get("weapon_type") or "Melee")
        options = [
            {"id": str(item["id"]), "name": str(item.get("name") or "")}
            for item in weapons
            if str(item.get("type") or "") == weapon_type
        ]
        focus["weapon_options"] = options
        allowed = {opt["id"] for opt in options}
        weapon_id = str(focus.get("weapon_id") or "").strip()
        dice = int(focus.get("weapon_dice") or 0)
        if not weapon_id:
            warnings.append(f"{focus.get('name') or 'Weapon Focus'} の対象武器を選んでください")
            focus["weapon_id"] = ""
            focus["weapon_name"] = ""
            continue
        if weapon_id not in allowed:
            warnings.append(f"{focus.get('name') or 'Weapon Focus'} は{weapon_type}武器専用です")
            focus["weapon_id"] = ""
            focus["weapon_name"] = ""
            for inst in state.foci or []:
                if inst.id == focus.get("id"):
                    inst.extra = None
            continue
        weapon = by_id[weapon_id]
        focus["weapon_id"] = weapon_id
        focus["weapon_name"] = str(weapon.get("name") or "")
        weapon["focus_dice"] = int(weapon.get("focus_dice") or 0) + dice


def apply_focus_limits(
    mag: int,
    qi_public: list[dict[str, Any]],
    foci_public: list[dict[str, Any]],
    errors: list[str],
) -> FocusLimits:
    count = len(qi_public) + len(foci_public)
    force = sum(int(item.get("rating") or item.get("force") or 0) for item in qi_public + foci_public)
    count_max = max(0, int(mag or 0))
    force_max = count_max * FOCUS_FORCE_MULT
    if count_max and count > count_max:
        errors.append(f"結合できる収束具は魔力までです（{count}/{count_max}）")
    if force_max and force > force_max:
        errors.append(f"結合収束具のForce合計が上限を超えています（{force}/{force_max}）")
    return {"count": count, "count_max": count_max, "force": force, "force_max": force_max}


def attach_focus_tests(
    public: list[dict[str, Any]],
    mag: int,
    skill_totals: dict[str, int],
    skill_bonus: dict[str, int],
    attrs: dict[str, int],
    skills_data: dict[str, Any],
    mental_limit: int,
) -> list[str]:
    warnings: list[str] = []
    for item in public:
        if not item.get("crafted"):
            continue
        force = int(item.get("force") or 1)
        bonus = dict(skill_bonus)
        if "MAG skills" in (item.get("effect") or ""):
            bonus["Artificing"] = int(bonus.get("Artificing") or 0) - force
        test = magic_opposed_test(
            "Artificing",
            force,
            force * 2,
            mag,
            skill_totals,
            bonus,
            attrs,
            item.get("hits"),
            item.get("opposed_hits"),
            days=force,
            skills_data=skills_data,
        )
        item["test"] = test
        if test.get("missing"):
            warnings.append(f"{item['name']} の作成にはArtificingが必要です（未習得・デフォルト不可）")
        if test.get("net") is not None and int(test["net"]) <= 0:
            warnings.append(f"{item['name']} の作成に失敗しています（正味0）")
        if item.get("formula_bought"):
            continue
        design = magic_opposed_test(
            "Arcana",
            force,
            force * 2,
            mag,
            skill_totals,
            skill_bonus,
            attrs,
            limit=mental_limit,
            limit_name="Mental",
            days=force,
            skills_data=skills_data,
        )
        item["formula_test"] = design
        if design.get("missing"):
            warnings.append(f"{item['name']} の術式自作にはArcanaが必要です（未習得・デフォルト不可）")
    return warnings
