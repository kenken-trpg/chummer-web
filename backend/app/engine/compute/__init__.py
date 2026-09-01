"""``compute(state)`` and its private resolver helpers.

Relocated verbatim from ``app.engine`` (commit 1 of the compute-phases
split). ``app.engine`` re-exports ``compute`` and the handful of helpers
``store.py`` / tests reference by name.
"""

from __future__ import annotations

import math
from typing import Any

from ...data_loader import (
    CHARGEN_AVAIL_MAX,
    CHARGEN_DEVICE_RATING_MAX,
    CHARGEN_WARE_ATTR_BONUS_MAX,
    PHYSICAL_ATTRS,
    catalog,
    eval_formula,
)
from ...improvements import (
    apply_bonus_nodes,
    compact_limit_modifiers,
    special_armor_totals,
    substitute_rating,
)
from ...models import (
    ArmorInstall,
    CareerBaseline,
    CharacterState,
    CommlinkInstall,
    WeaponInstall,
)
from ..constants import (
    ADEPT_TALENTS,
    BLACK_MARKET_AVAIL_BONUS,
    KARMA_ACTIVE_SKILL,
    KARMA_ATTRIBUTE,
    KARMA_CHARGEN_POOL,
    KARMA_KNOWLEDGE,
    KARMA_NUYEN_MAX,
    KARMA_SKILL_GROUP,
    KARMA_SPECIALIZATION,
    KARMA_TO_NUYEN,
    MARTIAL_ART_CHARGEN_STYLE_MAX,
    MARTIAL_ART_CHARGEN_TECHNIQUE_MAX,
    MYSTIC_PP_KARMA,
    NEGATIVE_QUALITY_KARMA_CAP,
    NUYEN_CHARGEN_KEEP_MAX,
    PRIORITY_KARMA_NUYEN_BASE,
    RES_TALENTS,
    SUM_TO_TEN_BUDGET,
    SUM_TO_TEN_COST,
    TRUST_FUND_STIPEND,
    _normalize_side,
    quality_contact_extra_key,
    quality_spirit_category_extra_key,
)
from ..contacts import (  # (contact network + Ex-Con / Erased caps)
    apply_erased_lifestyle_cap,
    resolve_contacts,
    sync_quality_contacts,
)
from ..formulas import (  # (stat-expression helpers)
    _add_leading_int,
    _ceil_div,
    _replace_leading_int,
    parse_armor_value,
)
from ..gear import (  # (gear pipeline clusters; see engine/gear/)
    _append_gear_weapons,
    _append_ware_weapons,
    _apply_recoil_totals,
    _clamp_rating,
    _ensure_drone_equipment,
    _public_weapon,
    _publish_drone_stats,
    _recompute_worn_armor,
    _resolve_apps,
    _resolve_armor_mods,
    _resolve_drones,
    _resolve_matrix_devices,
    _resolve_misc_gear,
    _resolve_optics,
    _resolve_programs,
    _resolve_sensors,
    _resolve_vehicle_mods,
    _resolve_weapon_accessories,
    _resolve_weapon_mounts,
    apply_active_drugs,
    apply_lifestyle_cost_mod,
    apply_reach_bonus,
    apply_unarmed_bonuses,
    apply_weapon_category_dv,
    apply_weapon_skill_accuracy,
    resolve_lifestyles,
)
from ..karma import (  # (cost maths)
    _active_karma_mults,
    _filter_karma_rules,
    _group_floor_map,
    _karma_cost_with_category_mods,
    _karma_raise_cost,
    _matching_karma_rules,
    _point_cost,
    _skill_category_map,
    _skill_group_category_map,
    attribute_karma_cost,
    knowledge_excess_karma,
    knowledge_points_spent,
    skill_karma_cost,
)
from ..limits import (  # (chargen avail / device-rating / ware-attr caps)
    _avail_entries,
    _check_avail_limit,
    _check_device_rating_limit,
    _device_rating_entries,
    _finalize_avail_tree,
)
from ..lookups import (  # catalog single-row accessors; see engine/lookups.py
    _item_by_id,
    find_metatype,  # noqa: F401  (re-exported for store.py / chummer_export.py / tests)
)
from ..magic import (  # (awakened/emerged pipeline clusters; see engine/magic/)
    attach_focus_tests,
    attach_spirit_tests,
    attach_weapon_focus_dice,
    spell_defense_pools,
    spell_karma_cost,
)
from ..martial_arts import (  # (style/technique resolution)
    resolve_martial_arts,
    sync_quality_martial_arts,
)
from ..pricing import (  # (post-resolve cost/avail adjustments)
    apply_black_market_avail,
    apply_overclocker,
    apply_purchase_discounts,
)
from ..priority import (
    heritage_options,
    priorities_are_unique,
    priority_value,
    sum_to_ten_spent,
)
from ..qualities import (  # (quality gather / extra-pick / binder pipeline; see engine/qualities.py)
    _quality_has_selectside,
    apply_quality_rules,
    quality_needs_extra,
    quality_requirement_context,
)
from ..resonance import (  # (technomancer pipeline; see engine/resonance.py)
    attach_complex_form_tests,
    attach_sprite_tests,
    living_persona,
)
from ..skills import (  # (knowledge / specialization / exotic / skillsoft resolution)
    _attach_skillsoft_knowledge,
    _attach_specializations,
    _copy_exotic_skill_bonuses,
    _merge_skill_ratings,
    apply_select_expertise,
    resolve_exotic_skills,
    resolve_knowledge,
    resolve_skill_mods,
    resolve_skill_picks,
    resolve_skillsofts,
    resolve_specializations,
)
from ..ware import (  # (cyberware/bioware pipeline clusters; see engine/ware/)
    _attach_ware_to_vehicle_mods,
    _public_installed,
    limb_attribute_replace,
    ware_ranges,
)
from .bootstrap import (
    bootstrap,
    sync_reward_totals,  # noqa: F401  (re-exported via app.engine)
)
from .context import Ctx
from .essence import essence
from .magic import awakened, spells
from .qualities import (
    effects_and_binders,
    gather,
    resolve_attribute_selects,  # noqa: F401  (re-exported via app.engine)
)
from .ware import ware


def snapshot_career_baseline(state: CharacterState) -> CareerBaseline:
    return CareerBaseline(
        attributes={str(k): int(v) for k, v in (state.attributes or {}).items()},
        skills={str(k): int(v) for k, v in (state.skills or {}).items()},
        skill_groups={str(k): int(v) for k, v in (state.skill_groups or {}).items()},
        knowledge_skills={str(k): int(v) for k, v in (state.knowledge_skills or {}).items()},
        skill_specializations=sorted(
            str(name) for name, spec in (state.skill_specializations or {}).items() if str(spec or "").strip()
        ),
        exotic_skills={
            str(row.id): int(row.rating or 0) for row in (state.exotic_skills or []) if getattr(row, "id", None)
        },
    )


def career_raise_karma(
    state: CharacterState,
    baseline: CareerBaseline,
    skill_totals: dict[str, int],
    skills_data: dict[str, Any],
    *,
    effects: dict[str, Any] | None = None,
) -> tuple[int, list[dict[str, Any]]]:
    """Karma to raise Priority/SumToTen characters from chargen snapshot to current ratings."""
    total = 0
    lines: list[dict[str, Any]] = []
    eff = effects or {}
    base_attrs = baseline.attributes or {}
    for key, rating in (state.attributes or {}).items():
        if key == "ESS":
            continue
        from_r = int(base_attrs.get(key, rating))
        to_r = int(rating or 0)
        cost = _karma_raise_cost(from_r, to_r, KARMA_ATTRIBUTE)
        if cost:
            lines.append({"kind": "attribute", "label": f"能力値 {key} {from_r}→{to_r}", "amount": cost})
            total += cost

    group_cat_map = _skill_group_category_map(skills_data)
    group_mults = _active_karma_mults(eff.get("skill_group_category_karma_cost_mult"), career=True)
    base_groups = baseline.skill_groups or {}
    for group, rating in (state.skill_groups or {}).items():
        from_r = int(base_groups.get(group, 0))
        to_r = int(rating or 0)
        cat = group_cat_map.get(group, "")
        mult = int(group_mults.get(cat, 100))
        cost = _karma_cost_with_category_mods(from_r, to_r, KARMA_SKILL_GROUP, mult_pct=mult)
        if cost:
            lines.append({"kind": "skill_group", "label": f"技能グループ {group} {from_r}→{to_r}", "amount": cost})
            total += cost

    base_floors = _group_floor_map(base_groups, skills_data)
    now_floors = _group_floor_map(dict(state.skill_groups or {}), skills_data)
    base_skills = baseline.skills or {}
    skill_cat_map = _skill_category_map(skills_data)
    karma_mults = _active_karma_mults(eff.get("skill_category_karma_cost_mult"), career=True)
    active_flat = _filter_karma_rules(eff.get("active_skill_karma_cost"), career=True)
    for name, rating in (skill_totals or {}).items():
        from_r = max(int(base_skills.get(name, 0)), int(base_floors.get(name, 0)))
        from_r = max(from_r, int(now_floors.get(name, 0)))
        to_r = int(rating or 0)
        cat = skill_cat_map.get(name, "")
        mult = int(karma_mults.get(cat, 100))
        cost = _karma_cost_with_category_mods(
            from_r,
            to_r,
            KARMA_ACTIVE_SKILL,
            mult_pct=mult,
            flat_rules=_matching_karma_rules(active_flat, cat),
        )
        if cost:
            lines.append({"kind": "skill", "label": f"技能 {name} {from_r}→{to_r}", "amount": cost})
            total += cost

    base_know = baseline.knowledge_skills or {}
    natives = set(state.native_languages or [])
    know_flat = _filter_karma_rules(
        list(eff.get("skill_category_karma_cost") or []) + list(eff.get("knowledge_skill_karma_cost") or []),
        career=True,
    )
    know_min = _filter_karma_rules(eff.get("knowledge_skill_karma_cost_min"), career=True)
    know_cats = dict(state.knowledge_categories or {})
    catalog_know = {
        str(s.get("name") or ""): str(s.get("category") or "") for s in (skills_data.get("knowledge") or [])
    }
    for name, rating in (state.knowledge_skills or {}).items():
        if name in natives:
            continue
        cat = str(know_cats.get(name) or catalog_know.get(name) or "Street")
        mult = int(karma_mults.get(cat, 100))
        from_r = int(base_know.get(name, 0))
        to_r = int(rating or 0)
        cost = _karma_cost_with_category_mods(
            from_r,
            to_r,
            KARMA_KNOWLEDGE,
            mult_pct=mult,
            flat_rules=_matching_karma_rules(know_flat, cat),
            min_rules=_matching_karma_rules(know_min, cat),
        )
        if cost:
            lines.append({"kind": "knowledge", "label": f"知識 {name} {from_r}→{to_r}", "amount": cost})
            total += cost

    spec_mults = _active_karma_mults(eff.get("skill_category_spec_karma_cost_mult"), career=True)
    base_specs = set(baseline.skill_specializations or [])
    for name, spec in (state.skill_specializations or {}).items():
        if str(spec or "").strip() and name not in base_specs:
            cat = skill_cat_map.get(name) or str(know_cats.get(name) or catalog_know.get(name) or "")
            mult = int(spec_mults.get(cat, 100))
            amount = max(1, int(math.ceil(KARMA_SPECIALIZATION * mult / 100.0)))
            lines.append({"kind": "specialization", "label": f"専門化 {name}（{spec}）", "amount": amount})
            total += amount

    base_exotic = baseline.exotic_skills or {}
    for row in state.exotic_skills or []:
        rid = str(getattr(row, "id", "") or "")
        if not rid:
            continue
        from_r = int(base_exotic.get(rid, 0))
        to_r = int(row.rating or 0)
        cost = _karma_cost_with_category_mods(
            from_r,
            to_r,
            KARMA_ACTIVE_SKILL,
            mult_pct=100,
            flat_rules=_matching_karma_rules(active_flat, ""),
        )
        if cost:
            label = str(getattr(row, "name", None) or getattr(row, "skill", None) or "Exotic")
            lines.append({"kind": "exotic", "label": f"特殊技能 {label} {from_r}→{to_r}", "amount": cost})
            total += cost
    return total, lines


def nuyen_spend_breakdown(
    cyber: list[dict[str, Any]],
    bio: list[dict[str, Any]],
    gear: dict[str, Any],
    *,
    qi_nuyen: int = 0,
    foci_nuyen: int = 0,
    spirits_nuyen: int = 0,
) -> list[dict[str, Any]]:
    buckets: list[tuple[str, int]] = [
        ("サイバーウェア", sum(int(item.get("nuyen") or 0) for item in cyber)),
        ("バイオウェア", sum(int(item.get("nuyen") or 0) for item in bio)),
        ("防具", sum(int(row.get("nuyen") or 0) for row in (gear.get("armor_items") or []))),
        ("防具改造", sum(int(row.get("nuyen") or 0) for row in (gear.get("armor_mods") or []))),
        ("武器", sum(int(row.get("nuyen") or 0) for row in (gear.get("weapons") or []))),
        ("武器アクセサリ", sum(int(row.get("nuyen") or 0) for row in (gear.get("weapon_accessories") or []))),
        ("通信機", sum(int(row.get("nuyen") or 0) for row in (gear.get("commlinks") or []))),
        ("サイバーデッキ", sum(int(row.get("nuyen") or 0) for row in (gear.get("cyberdecks") or []))),
        ("RCC", sum(int(row.get("nuyen") or 0) for row in (gear.get("rccs") or []))),
        ("光学／音響", sum(int(row.get("nuyen") or 0) for row in (gear.get("optics") or []))),
        ("センサー", sum(int(row.get("nuyen") or 0) for row in (gear.get("sensors") or []))),
        (
            "プログラム",
            sum(int(row.get("nuyen") or 0) for row in (gear.get("programs") or []) + (gear.get("apps") or [])),
        ),
        ("ドローン", sum(int(row.get("nuyen") or 0) for row in (gear.get("drones") or []))),
        ("車両", sum(int(row.get("nuyen") or 0) for row in (gear.get("vehicles") or []))),
        (
            "車両改造",
            sum(
                int(row.get("nuyen") or 0)
                for row in (gear.get("vehicle_mods") or []) + (gear.get("weapon_mounts") or [])
            ),
        ),
        ("その他ギア", sum(int(row.get("nuyen") or 0) for row in (gear.get("gear") or []))),
        ("ライフスタイル", sum(int(row.get("nuyen") or 0) for row in (gear.get("lifestyles") or []))),
        ("気フォーカス", int(qi_nuyen or 0)),
        ("フォーカス", int(foci_nuyen or 0)),
        ("精霊", int(spirits_nuyen or 0)),
    ]
    return [{"kind": "nuyen", "label": label, "amount": amount} for label, amount in buckets if amount]


def _effective_attr_spec(
    attrs_spec: dict[str, dict[str, int | float]],
    special_key: str | None,
    talent_start: int,
    mag_max_bonus: int = 0,
    res_max_bonus: int = 0,
) -> dict[str, dict[str, int | float]]:
    out = {key: dict(spec) for key, spec in attrs_spec.items()}
    if special_key == "MAG":
        out["MAG"]["min"] = max(talent_start, 1)
        out["MAG"]["max"] = int(out["MAG"].get("max") or 0) + max(0, int(mag_max_bonus))
        out["RES"]["min"] = 0
        out["RES"]["max"] = 0
    elif special_key == "RES":
        out["RES"]["min"] = max(talent_start, 1)
        out["RES"]["max"] = int(out["RES"].get("max") or 0) + max(0, int(res_max_bonus))
        out["MAG"]["min"] = 0
        out["MAG"]["max"] = 0
    else:
        out["MAG"]["min"] = 0
        out["MAG"]["max"] = 0
        out["RES"]["min"] = 0
        out["RES"]["max"] = 0
    return out


def default_attributes(meta: dict[str, Any]) -> dict[str, int]:
    out = {}
    for key, spec in meta["attributes"].items():
        if key == "ESS":
            out[key] = int(spec["max"] or 6)
        else:
            out[key] = int(spec["min"])
    return out


def resolve_movement(meta: dict[str, Any], effects: dict[str, Any]) -> dict[str, Any]:
    category = "Ground"
    walk = str(meta.get("walk") or "2/1/0")
    run = str(meta.get("run") or "4/0/0")
    sprint = str(meta.get("sprint") or "2/1/0")
    replace = effects.get("movement_replace") or {}
    if (category, "walk") in replace:
        walk = _replace_leading_int(walk, int(replace[(category, "walk")]))
    if (category, "run") in replace:
        run = _replace_leading_int(run, int(replace[(category, "run")]))
    walk = _add_leading_int(walk, int((effects.get("walk_multiplier") or {}).get(category) or 0))
    run = _add_leading_int(run, int((effects.get("run_multiplier") or {}).get(category) or 0))
    sprint_bonus = int((effects.get("sprint_bonus") or {}).get(category) or 0)
    return {
        "walk": walk,
        "run": run,
        "sprint": sprint,
        "sprint_bonus": sprint_bonus,
    }


def resolve_gear(
    state: CharacterState,
    ware_items: list[dict[str, Any]] | None = None,
    attr_totals: dict[str, int] | None = None,
    special_modification_limit: int = 0,
) -> dict[str, Any]:
    warnings: list[str] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    nuyen = 0
    armor_items: list[dict[str, Any]] = []
    weapons: list[dict[str, Any]] = []
    commlinks: list[dict[str, Any]] = []
    cyberdecks: list[dict[str, Any]] = []
    rccs: list[dict[str, Any]] = []
    errors: list[str] = []

    kept_armor: list[ArmorInstall] = []
    for armor_inst in state.armor:
        spec = _item_by_id("armor", armor_inst.armor_id)
        if not spec:
            continue
        rating = _clamp_rating(spec, armor_inst.rating)
        armor_inst.rating = rating
        armor_inst.equipped = bool(armor_inst.equipped)
        armor_inst.wireless = bool(armor_inst.wireless)
        has_wireless = bool(spec.get("wirelessbonus"))
        cost = int(eval_formula(str(spec.get("cost") or "0"), rating, 0))
        nuyen += cost
        value, additive = parse_armor_value(str(spec.get("armor") or "0"), rating)
        if armor_inst.equipped:
            nodes = substitute_rating(list(spec.get("bonus") or []), rating)
            if has_wireless and armor_inst.wireless:
                nodes = nodes + substitute_rating(list(spec.get("wirelessbonus") or []), rating)
            if nodes:
                bonus_sources.append((spec["name"], nodes))
        kept_armor.append(armor_inst)
        armor_items.append(
            {
                "id": armor_inst.id,
                "armor_id": spec["id"],
                "name": spec["name"],
                "category": spec.get("category") or "Armor",
                "armor": spec.get("armor") or "0",
                "armor_value": value,
                "additive": additive,
                "rating": rating,
                "rating_max": int(spec.get("maxrating") or 0),
                "equipped": armor_inst.equipped,
                "wireless": armor_inst.wireless,
                "has_wireless": has_wireless,
                "nuyen": cost,
                "avail": spec.get("avail") or "",
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
                "contributes": 0,
                "armorcapacity": spec.get("armorcapacity") or "",
                "addmodcategories": list(spec.get("addmodcategories") or []),
                "mods": [],
                "capacity_used": 0,
                "capacity_max": 0,
            }
        )
    state.armor = kept_armor
    armor_mods, mod_nuyen, mod_warns, mod_errors, mod_bonus = _resolve_armor_mods(state, armor_items)
    nuyen += mod_nuyen
    warnings.extend(mod_warns)
    errors.extend(mod_errors)
    bonus_sources.extend(mod_bonus)
    worn_armor, worn_name, worn_warns = _recompute_worn_armor(armor_items)
    warnings.extend(worn_warns)

    kept_weapons: list[WeaponInstall] = []
    for weapon_inst in state.weapons:
        spec = _item_by_id("weapons", weapon_inst.weapon_id)
        if not spec:
            continue
        qty = max(1, int(weapon_inst.qty or 1))
        weapon_inst.qty = qty
        unit = int(eval_formula(str(spec.get("cost") or "0"), 1, 0))
        cost = unit * qty
        nuyen += cost
        kept_weapons.append(weapon_inst)
        weapons.append(
            _public_weapon(
                spec,
                inst_id=weapon_inst.id,
                qty=qty,
                nuyen=cost,
                loaded_ammo_id=weapon_inst.loaded_ammo_id,
            )
        )
    state.weapons = kept_weapons
    _append_ware_weapons(weapons, ware_items or [], state, attr_totals)
    weapon_accessories, acc_nuyen, acc_warns, acc_errors, special_mod_used = _resolve_weapon_accessories(
        state, weapons, special_modification_limit=special_modification_limit
    )
    recoil_info = _apply_recoil_totals(weapons, attr_totals or {})
    nuyen += acc_nuyen
    warnings.extend(acc_warns)
    errors.extend(acc_errors)

    kept_links: list[CommlinkInstall] = []
    for link_inst in state.commlinks:
        spec = _item_by_id("commlinks", link_inst.gear_id)
        if not spec:
            continue
        rating = _clamp_rating(spec, link_inst.rating)
        link_inst.rating = rating
        cost = int(eval_formula(str(spec.get("cost") or "0"), rating, 0))
        nuyen += cost
        device = int(eval_formula(str(spec.get("devicerating") or "0"), rating, 0))
        processing = int(eval_formula(str(spec.get("dataprocessing") or "0"), rating, 0))
        firewall = int(eval_formula(str(spec.get("firewall") or "0"), rating, 0))
        kept_links.append(link_inst)
        commlinks.append(
            {
                "id": link_inst.id,
                "gear_id": spec["id"],
                "name": spec["name"],
                "category": spec.get("category") or "Commlinks",
                "rating": rating,
                "rating_max": int(spec.get("maxrating") or 0),
                "device_rating": device,
                "dataprocessing": processing,
                "firewall": firewall,
                "nuyen": cost,
                "avail": spec.get("avail") or "",
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
    state.commlinks = kept_links

    kept_decks, cyberdecks, deck_nuyen = _resolve_matrix_devices("cyberdecks", list(state.cyberdecks or []))
    state.cyberdecks = kept_decks
    nuyen += deck_nuyen
    kept_rccs, rccs, rcc_nuyen = _resolve_matrix_devices("rccs", list(state.rccs or []))
    state.rccs = kept_rccs
    nuyen += rcc_nuyen
    optics, optic_nuyen, optic_warns, optic_errors, optic_bonus = _resolve_optics(state)
    nuyen += optic_nuyen
    warnings.extend(optic_warns)
    errors.extend(optic_errors)
    bonus_sources.extend(optic_bonus)
    programs, prog_nuyen, prog_warns = _resolve_programs(state, cyberdecks, rccs)
    nuyen += prog_nuyen
    warnings.extend(prog_warns)
    apps, app_nuyen, app_warns = _resolve_apps(state, commlinks)
    nuyen += app_nuyen
    warnings.extend(app_warns)
    drones, drone_nuyen = _resolve_drones(state, "drones")
    nuyen += drone_nuyen
    vehicles, vehicle_nuyen = _resolve_drones(state, "vehicles")
    nuyen += vehicle_nuyen
    hosts = drones + vehicles
    _ensure_drone_equipment(state)
    vehicle_mods, mod_nuyen, mod_warns, mod_errors = _resolve_vehicle_mods(state, hosts)
    nuyen += mod_nuyen
    warnings.extend(mod_warns)
    errors.extend(mod_errors)
    weapon_mounts, mount_nuyen, mount_warns, mount_errors = _resolve_weapon_mounts(state, hosts, weapons)
    nuyen += mount_nuyen
    warnings.extend(mount_warns)
    errors.extend(mount_errors)
    sensors, sensor_nuyen, sensor_warns, sensor_errors, sensor_bonus = _resolve_sensors(state)
    nuyen += sensor_nuyen
    warnings.extend(sensor_warns)
    errors.extend(sensor_errors)
    bonus_sources.extend(sensor_bonus)
    _publish_drone_stats(hosts, sensors)
    gear_items, gear_nuyen, gear_warns, gear_errors, gear_bonus = _resolve_misc_gear(state, hosts, weapons)
    nuyen += gear_nuyen
    warnings.extend(gear_warns)
    errors.extend(gear_errors)
    bonus_sources.extend(gear_bonus)
    _append_gear_weapons(weapons, gear_items)

    lifestyles, lifestyle_nuyen, lifestyle_warns, lifestyle_bonus = resolve_lifestyles(state)
    nuyen += lifestyle_nuyen
    warnings.extend(lifestyle_warns)
    bonus_sources.extend(lifestyle_bonus)

    primary_link = max(commlinks, key=lambda row: int(row.get("device_rating") or 0)) if commlinks else None
    primary_deck = max(cyberdecks, key=lambda row: int(row.get("device_rating") or 0)) if cyberdecks else None
    primary_rcc = max(rccs, key=lambda row: int(row.get("device_rating") or 0)) if rccs else None
    primary_life = lifestyles[0] if lifestyles else None
    _finalize_avail_tree(armor_items + armor_mods)
    _finalize_avail_tree(weapons + weapon_accessories)
    _finalize_avail_tree(commlinks + apps)
    _finalize_avail_tree(cyberdecks + rccs + programs)
    _finalize_avail_tree(optics)
    _finalize_avail_tree(sensors)
    _finalize_avail_tree(drones + vehicles + vehicle_mods + weapon_mounts)
    _finalize_avail_tree(gear_items)
    _finalize_avail_tree(lifestyles)
    return {
        "warnings": warnings,
        "errors": errors,
        "bonus_sources": bonus_sources,
        "nuyen": nuyen,
        "armor": worn_armor,
        "worn_name": worn_name,
        "armor_items": armor_items,
        "armor_mods": armor_mods,
        "weapons": weapons,
        "weapon_accessories": weapon_accessories,
        "recoil": recoil_info,
        "special_modification_used": special_mod_used,
        "commlinks": commlinks,
        "cyberdecks": cyberdecks,
        "rccs": rccs,
        "optics": optics,
        "programs": programs,
        "apps": apps,
        "sensors": sensors,
        "drones": drones,
        "vehicles": vehicles,
        "vehicle_mods": vehicle_mods,
        "weapon_mounts": weapon_mounts,
        "gear": gear_items,
        "lifestyles": lifestyles,
        "commlink": primary_link,
        "cyberdeck": primary_deck,
        "rcc": primary_rcc,
        "lifestyle": primary_life,
    }


def compute(state: CharacterState) -> CharacterState:
    ctx = Ctx(state=state, data=catalog())
    bootstrap(ctx)
    gather(ctx)
    ware(ctx)
    effects_and_binders(ctx)
    essence(ctx)
    awakened(ctx)
    ctx.gear = resolve_gear(
        ctx.state,
        ctx.cyber_installed,
        ctx.attr_totals,
        special_modification_limit=int(ctx.effects.get("special_modification_limit") or 0),
    )
    ctx.warnings.extend(ctx.gear["warnings"])
    ctx.errors.extend(ctx.gear.get("errors") or [])
    apply_lifestyle_cost_mod(ctx.gear, int(ctx.effects.get("lifestyle_cost") or 0))
    apply_erased_lifestyle_cap(ctx.gear, bool(ctx.effects.get("erased")), ctx.warnings)
    apply_reach_bonus(ctx.gear.get("weapons"), int(ctx.effects.get("reach") or 0))
    apply_weapon_category_dv(ctx.gear.get("weapons"), ctx.effects)
    apply_weapon_skill_accuracy(ctx.gear.get("weapons"), ctx.effects)
    ctx.bmp_category = ""
    ctx.bmp_contact_id = ""
    ctx.bmp_active = False
    if ctx.effects.get("black_market_discount"):
        for q in ctx.qualities:
            if not any(node.get("tag") == "blackmarketdiscount" for node in (q.get("bonus") or [])):
                continue
            ctx.bmp_category = str((ctx.state.quality_extras or {}).get(q["id"]) or "").strip()
            ctx.bmp_contact_id = str(
                (ctx.state.quality_extras or {}).get(quality_contact_extra_key(q["id"])) or ""
            ).strip()
            contact_ids = {str(getattr(c, "id", "") or "") for c in (ctx.state.contacts or [])}
            if not ctx.bmp_category:
                ctx.warnings.append("Black Market Pipeline の商品カテゴリを選んでください")
            if not ctx.bmp_contact_id:
                ctx.warnings.append("Black Market Pipeline のコンタクトを選んでください")
            elif ctx.bmp_contact_id not in contact_ids:
                ctx.warnings.append("Black Market Pipeline のコンタクトが見つかりません")
                ctx.bmp_contact_id = ""
            ctx.bmp_active = bool(ctx.bmp_category and ctx.bmp_contact_id)
            break
    apply_purchase_discounts(
        ctx.gear,
        ctx.cyber_installed,
        ctx.bio_installed,
        ctx.effects,
        black_market_category=ctx.bmp_category if ctx.bmp_active else "",
    )
    if ctx.bmp_active:
        apply_black_market_avail(
            ctx.gear,
            ctx.cyber_installed,
            ctx.bio_installed,
            black_market_category=ctx.bmp_category,
        )
    apply_overclocker(ctx.gear, bool(ctx.effects.get("overclocker")))
    trust_level = int(ctx.effects.get("trustfund") or 0)
    if trust_level:
        sinner_ok = any(
            str(q.get("name") or "").startswith("SINner (National)")
            or str(q.get("name") or "").startswith("SINner (Corporate)")
            for q in ctx.qualities
        )
        if not sinner_ok:
            ctx.warnings.append("Trust Fund には SINner（National または Corporate）が必要です")
    ctx.errors.extend(_attach_ware_to_vehicle_mods(ctx.gear.get("vehicle_mods") or [], ctx.cyber_installed))
    for source, nodes in ctx.gear["bonus_sources"]:
        apply_bonus_nodes(nodes, ctx.effects, source)
    ctx.active_drugs = apply_active_drugs(ctx.state, ctx.attr_totals, ctx.effects)
    attach_weapon_focus_dice(
        ctx.state, list(ctx.foci.get("public") or []), list(ctx.gear.get("weapons") or []), ctx.warnings
    )
    if ctx.talent["name"] in ADEPT_TALENTS:
        ctx.enabled.add("adept")
        ctx.effects["enabled_tabs"].add("adept")
    ctx.enabled.update(ctx.effects["enabled_tabs"])

    if ctx.talent["name"] == "Adept":
        ctx.power_pool = float(ctx.ratings["MAG"]) + float(ctx.effects.get("adept_power_points") or 0)
    elif ctx.talent["name"] == "Mystic Adept":
        ctx.power_pool = float(ctx.state.mystic_pp) + float(ctx.effects.get("adept_power_points") or 0)
    else:
        ctx.power_pool = 0.0
    ctx.power_spent = float(ctx.adept["spent"])
    if ctx.power_spent > ctx.power_pool + 1e-9:
        ctx.errors.append(f"パワー点が不足しています（使用 {ctx.power_spent:g} / 上限 {ctx.power_pool:g}）")

    bonus = ctx.effects["attribute_bonus"]
    ctx.total = {k: ctx.ratings[k] + int(bonus.get(k, 0)) for k in ctx.ratings}
    # ESS is fractional; the attribute-total consumers only ever read integer
    # attrs (STR / AGI / …), so the dict[str, int] inference stays useful.
    ctx.total["ESS"] = ctx.ess  # type: ignore[assignment]
    ctx.limb_replace = limb_attribute_replace(
        ctx.cyber_installed, int(ctx.total["STR"]), int(ctx.total["AGI"]), ctx.attrs_spec
    )
    if ctx.limb_replace:
        ctx.total["STR"] = int(ctx.limb_replace["str"])
        ctx.total["AGI"] = int(ctx.limb_replace["agi"])

    spells(ctx)

    attr_row = priority_value("Attributes", ctx.state.priorities.Attributes)
    skill_row = priority_value("Skills", ctx.state.priorities.Skills)
    res_row = priority_value("Resources", ctx.state.priorities.Resources)
    her_row = priority_value("Heritage", ctx.state.priorities.Heritage)

    ctx.special_from_meta = 0
    extra_karma = 0
    for entry in her_row.get("metatypes") or []:
        if entry["name"] == ctx.state.metatype:
            ctx.special_from_meta = entry.get("special", 0)
            extra_karma += entry.get("karma", 0)
            if ctx.state.metavariant:
                for v in entry.get("variants") or []:
                    if v["name"] == ctx.state.metavariant:
                        ctx.special_from_meta = v.get("special", ctx.special_from_meta)
                        extra_karma += v.get("karma", 0)
            break

    ctx.spent_physical = 0
    for key in PHYSICAL_ATTRS:
        ctx.spent_physical += max(0, ctx.ratings[key] - int(ctx.attrs_spec[key]["min"]))
    ctx.spent_special = max(0, ctx.ratings["EDG"] - int(ctx.attrs_spec["EDG"]["min"]))
    if ctx.special_key == "MAG":
        ctx.spent_special += max(0, ctx.ratings["MAG"] - ctx.talent_start)
    elif ctx.special_key == "RES":
        ctx.spent_special += max(0, ctx.ratings["RES"] - ctx.talent_start)

    ctx.nuyen_karma_max = KARMA_NUYEN_MAX
    if ctx.is_karma:
        ctx.attr_points = 0
        ctx.skill_points = 0
        ctx.group_points = 0
        ctx.special_from_meta = 0
        ctx.nuyen_karma_max = KARMA_NUYEN_MAX
        ctx.state.karma_nuyen = max(0, min(ctx.nuyen_karma_max, int(ctx.state.karma_nuyen or 0)))
        ctx.nuyen_pool = int(ctx.state.karma_nuyen) * KARMA_TO_NUYEN
        ctx.metatype_karma_cost = max(0, int(ctx.meta.get("karma") or 0))
        ctx.heritage_karma_cost = 0
    else:
        ctx.attr_points = int(attr_row.get("attribute_points") or 0)
        ctx.skill_points = int(skill_row.get("skill_points") or 0)
        ctx.group_points = int(skill_row.get("skill_group_points") or 0)
        ctx.nuyen_pool = int(res_row.get("nuyen") or 0)
        ctx.metatype_karma_cost = 0
        # Priority chargen: metatypes.xml <karma> is for Karma/Sum-to-Ten, not Priority.
        # Heritage table <karma> is an extra cost for some metavariants / rare races.
        ctx.heritage_karma_cost = extra_karma
        # Leftover chargen karma may buy nuyen (SR5 p.94); Born Rich raises the cap.
        ctx.nuyen_karma_max = max(0, PRIORITY_KARMA_NUYEN_BASE + int(ctx.effects.get("nuyen_max_bp") or 0))
        ctx.state.karma_nuyen = max(0, min(ctx.nuyen_karma_max, int(ctx.state.karma_nuyen or 0)))
        ctx.nuyen_pool += int(ctx.state.karma_nuyen) * KARMA_TO_NUYEN

    ctx.nuyen_pool += int(ctx.state.nuyen_earned or 0)
    ctx.nuyen_pool += int(ctx.effects.get("nuyen_amt") or 0)
    ctx.nuyen_spent = (
        sum(int(item["nuyen"]) for item in ctx.installed)
        + int(ctx.qi.get("nuyen") or 0)
        + int(ctx.foci.get("nuyen") or 0)
        + int(ctx.spirits.get("nuyen") or 0)
        + int(ctx.gear.get("nuyen") or 0)
    )
    ctx.nuyen = ctx.nuyen_pool - ctx.nuyen_spent

    ctx.skill_spent = 0
    ctx.group_spent = 0
    ctx.skill_totals = {}
    exotic_names = {s["name"] for s in ctx.data["skills"]["skills"] if s.get("exotic")}
    if exotic_names:
        ctx.state.skills = {name: rating for name, rating in ctx.state.skills.items() if name not in exotic_names}
    for group, rating in ctx.state.skill_groups.items():
        rating = max(0, min(ctx.skill_group_cap, int(rating)))
        ctx.state.skill_groups[group] = rating
        ctx.group_spent += rating
        for s in ctx.data["skills"]["skills"]:
            if s.get("skillgroup") == group and not s.get("exotic"):
                ctx.skill_totals[s["name"]] = max(ctx.skill_totals.get(s["name"], 0), rating)
    tentative = dict(ctx.skill_totals)
    for name, rating in ctx.state.skills.items():
        tentative[name] = max(tentative.get(name, 0), max(0, min(ctx.skill_rating_cap + 1, int(rating))))
    ctx.skill_picks = resolve_skill_picks(ctx.state, ctx.data["skills"], tentative)
    ctx.warnings.extend(ctx.skill_picks["warnings"])
    skill_cat_map = _skill_category_map(ctx.data["skills"])
    point_mults = dict(ctx.effects.get("skill_category_point_cost_mult") or {})
    for name, rating in ctx.state.skills.items():
        cap = ctx.skill_rating_cap + int(ctx.skill_picks["skill_max_bonus"].get(name, 0))
        rating = max(0, min(cap, int(rating)))
        ctx.state.skills[name] = rating
        base = ctx.skill_totals.get(name, 0)
        extra = max(0, rating - base)
        cat = skill_cat_map.get(name, "")
        ctx.skill_spent += _point_cost(extra, int(point_mults.get(cat, 100)))
        ctx.skill_totals[name] = max(base, rating)
    ctx.exotic = resolve_exotic_skills(
        ctx.state,
        ctx.data["skills"],
        ctx.skill_picks["skill_max_bonus"],
        rating_cap=ctx.skill_rating_cap,
    )
    ctx.warnings.extend(ctx.exotic["warnings"])
    ctx.skill_spent += int(ctx.exotic["spent"])
    ctx.skill_totals.update(ctx.exotic["totals"])
    ctx.knowledge = resolve_knowledge(
        ctx.state,
        ctx.data["skills"],
        ctx.total,
        rating_cap=ctx.skill_rating_cap,
        native_limit=1 + int(ctx.effects.get("native_language_limit_bonus") or 0),
    )
    ctx.warnings.extend(ctx.knowledge["warnings"])
    ctx.know_spent = knowledge_points_spent(ctx.knowledge["public"], point_mults)
    ctx.know_max = int(ctx.knowledge["max"]) + int(ctx.effects.get("knowledge_skill_points") or 0)
    bought_knowledge = dict(ctx.state.knowledge_skills)
    for name in ctx.state.native_languages:
        bought_knowledge[name] = max(int(bought_knowledge.get(name) or 0), 1)
    ctx.skill_mods = resolve_skill_mods(
        ctx.data["skills"], ctx.effects, bought_knowledge, ctx.state.knowledge_categories
    )
    for name, bonus in ctx.skill_picks["skill_bonus"].items():
        ctx.skill_mods["skill_bonus"][name] = int(ctx.skill_mods["skill_bonus"].get(name, 0)) + int(bonus)
    for name, notes in ctx.skill_picks["skill_bonus_notes"].items():
        existing = ctx.skill_mods["skill_bonus_notes"].setdefault(name, [])
        for note in notes:
            if note not in existing:
                existing.append(note)
    _copy_exotic_skill_bonuses(ctx.skill_mods, ctx.exotic["public"])
    for name in ctx.effects.get("disabled_skills") or []:
        if int(ctx.skill_totals.get(name) or 0) > 0 or int(ctx.state.skills.get(name) or 0) > 0:
            ctx.warnings.append(f"{name} は無効化されている技能です")
    for group in ctx.effects.get("disabled_skill_groups") or []:
        if int(ctx.state.skill_groups.get(group) or 0) > 0:
            ctx.warnings.append(f"技能グループ {group} は無効化されています")
    blocked_defaults = list(ctx.effects.get("blocked_default_categories") or [])
    if blocked_defaults:
        ctx.warnings.append("デフォルト不可: " + "、".join(blocked_defaults))
    ctx.skillsofts = resolve_skillsofts(list(ctx.gear.get("gear") or []), ctx.data["skills"], ctx.effects, ctx.warnings)
    _attach_skillsoft_knowledge(ctx.knowledge["public"], ctx.skillsofts["knowledge"], ctx.data["skills"])
    ctx.expertises, free_expertise_skills = apply_select_expertise(
        ctx.state,
        ctx.effects,
        ctx.qualities,
        ctx.skill_totals,
        ctx.skillsofts["active"],
        ctx.warnings,
    )
    ctx.specs = resolve_specializations(
        ctx.state,
        ctx.data["skills"],
        ctx.skill_totals,
        ctx.skillsofts["active"],
        ctx.skillsofts["knowledge"],
        free_expertise_skills=free_expertise_skills,
    )
    ctx.warnings.extend(ctx.specs["warnings"])
    # Keep expertise picks even if resolve dropped a conflicting row.
    for row in ctx.expertises:
        skill_name = str(row.get("skill") or "")
        spec_name = str(row.get("spec") or "")
        if skill_name and spec_name:
            ctx.specs["specs"][skill_name] = spec_name
            ctx.state.skill_specializations[skill_name] = spec_name
    spec_active = int(ctx.specs["active_spent"])
    spec_knowledge = int(ctx.specs["knowledge_spent"])
    if ctx.is_karma:
        ctx.spec_karma = (spec_active + spec_knowledge) * KARMA_SPECIALIZATION
    elif ctx.career:
        # Priority career: new specs cost karma (baseline settles chargen specs).
        ctx.spec_karma = 0
    else:
        ctx.skill_spent += spec_active
        ctx.know_spent += spec_knowledge
        ctx.spec_karma = 0
    _attach_specializations(ctx.knowledge["public"], ctx.specs["specs"])
    ctx.effective_skills = _merge_skill_ratings(ctx.skill_totals, ctx.skillsofts["active"])
    ctx.effective_knowledge = _merge_skill_ratings(dict(ctx.state.knowledge_skills or {}), ctx.skillsofts["knowledge"])

    ctx.karma_from_q = sum(
        q["karma"] for q in ctx.qualities if not q.get("onlyprioritygiven") and q["id"] not in ctx.free_quality_ids
    )
    ctx.mystic_karma = int(ctx.state.mystic_pp) * MYSTIC_PP_KARMA
    ctx.extra_adept_karma = (
        int(ctx.enhancements.get("karma") or 0) + int(ctx.qi.get("karma") or 0) + int(ctx.foci.get("karma") or 0)
    )
    ctx.spell_karma = int(ctx.magic.get("karma") or 0) + int(ctx.resonance.get("karma") or 0)
    ctx.career_adv_karma = 0
    ctx.career_adv_lines = []
    if ctx.is_karma:
        ctx.attr_karma = attribute_karma_cost(ctx.ratings, ctx.attrs_spec, ctx.special_key)
        ctx.skill_buy_karma = skill_karma_cost(
            ctx.state.skill_groups, ctx.skill_totals, ctx.data["skills"], group_cap=ctx.skill_group_cap
        )
        know_cats = {
            str(row.get("name") or ""): str(row.get("category") or "")
            for row in (ctx.knowledge.get("public") or [])
            if row.get("name")
        }
        ctx.knowledge_karma = knowledge_excess_karma(
            dict(ctx.state.knowledge_skills or {}),
            ctx.know_max,
            categories=know_cats,
            karma_mults=_active_karma_mults(ctx.effects.get("skill_category_karma_cost_mult"), career=False),
        )
        nuyen_karma = int(ctx.state.karma_nuyen or 0)
        ctx.karma_pool = KARMA_CHARGEN_POOL + int(ctx.state.karma_earned or 0)
        ctx.karma_spent = (
            ctx.karma_from_q
            + ctx.metatype_karma_cost
            + ctx.mystic_karma
            + ctx.extra_adept_karma
            + ctx.spell_karma
            + ctx.attr_karma
            + ctx.skill_buy_karma
            + ctx.knowledge_karma
            + ctx.spec_karma
            + nuyen_karma
        )
    else:
        ctx.attr_karma = 0
        ctx.skill_buy_karma = 0
        ctx.knowledge_karma = 0
        nuyen_karma = 0
        ctx.karma_pool = 25 + int(ctx.state.karma_earned or 0)
        ctx.karma_spent = (
            ctx.karma_from_q
            + ctx.heritage_karma_cost
            + ctx.mystic_karma
            + ctx.extra_adept_karma
            + ctx.spell_karma
            + int(ctx.state.karma_nuyen or 0)
        )
        if ctx.career:
            baseline = ctx.state.career_baseline
            if baseline is None:
                baseline = snapshot_career_baseline(ctx.state)
                ctx.state.career_baseline = baseline
            ctx.career_adv_karma, ctx.career_adv_lines = career_raise_karma(
                ctx.state, baseline, ctx.skill_totals, ctx.data["skills"], effects=ctx.effects
            )
            ctx.karma_spent += ctx.career_adv_karma

    bod = ctx.total["BOD"]
    agi = ctx.total["AGI"]
    rea = ctx.total["REA"]
    stre = ctx.total["STR"]
    wil = ctx.total["WIL"]
    logi = ctx.total["LOG"]
    intuition = ctx.total["INT"]
    cha = ctx.total["CHA"]
    ctx.warnings.extend(sync_quality_contacts(ctx.state, ctx.effects, ctx.qualities))
    ctx.contacts = resolve_contacts(
        ctx.state,
        int(cha or 0),
        career=ctx.career,
        friends_in_high_places=bool(ctx.effects.get("friends_in_high_places")),
        black_market_contact_id=ctx.bmp_contact_id if ctx.bmp_active else "",
        contact_karma_adj=int(ctx.effects.get("contact_karma_adj") or 0),
        contact_karma_min=int(ctx.effects.get("contact_karma_min") or 0),
        excon=bool(ctx.effects.get("excon")),
    )
    ctx.warnings.extend(ctx.contacts["warnings"])
    ctx.karma_spent += int(ctx.contacts.get("karma") or 0)

    martial_ctx = quality_requirement_context(
        ctx.state,
        ctx.talent,
        ctx.qualities,
        ctx.meta,
        ctx.ess,
        ctx.ess_lost,
        ctx.effective_skills,
        set(ctx.adept.get("power_names") or []),
        {str(item.get("name") or "") for item in (ctx.magic.get("public") or []) if item.get("name")},
        str(
            ((ctx.magic.get("tradition") if isinstance(ctx.magic.get("tradition"), dict) else {}) or {}).get("name")
            or ""
        ),
        {item["name"] for item in ctx.cyber_installed},
        {item["name"] for item in ctx.bio_installed},
        ctx.effective_knowledge,
    )
    martial_ctx = {
        **martial_ctx,
        "qualities": set(martial_ctx.get("qualities") or []) | {ctx.talent["name"]},
    }
    ctx.warnings.extend(sync_quality_martial_arts(ctx.state, ctx.effects, ctx.qualities))
    ctx.martial = resolve_martial_arts(ctx.state, martial_ctx, ctx.errors, career=ctx.career)
    ctx.warnings.extend(ctx.martial["warnings"])
    for source, nodes in ctx.martial.get("bonus_sources") or []:
        apply_bonus_nodes(nodes, ctx.effects, source)
    apply_unarmed_bonuses(
        ctx.gear.get("weapons"),
        int(ctx.effects.get("unarmed_reach") or 0),
        int(ctx.effects.get("unarmed_ap") or 0),
    )
    ctx.karma_spent += int(ctx.martial.get("karma") or 0)
    ctx.karma_spent += int(ctx.initiation.get("karma") or 0)
    ctx.karma_spent += int(ctx.submersion.get("karma") or 0)
    ctx.karma_left = ctx.karma_pool - ctx.karma_spent

    ctx.karma_spend_lines = list(ctx.career_adv_lines)
    for label, amount in (
        ("資質", ctx.karma_from_q),
        ("メタ", ctx.metatype_karma_cost if ctx.is_karma else ctx.heritage_karma_cost),
        ("能力値（カルマ作成）", ctx.attr_karma if ctx.is_karma else 0),
        ("技能（カルマ作成）", ctx.skill_buy_karma if ctx.is_karma else 0),
        ("知識（カルマ作成）", ctx.knowledge_karma if ctx.is_karma else 0),
        ("専門化", ctx.spec_karma),
        ("ニューエン交換", int(ctx.state.karma_nuyen or 0)),
        ("ミスティックPP", ctx.mystic_karma),
        ("アデプト／気／フォーカス", ctx.extra_adept_karma),
        ("術式／複合体", ctx.spell_karma),
        ("コンタクト超過", int(ctx.contacts.get("karma") or 0)),
        ("武道", int(ctx.martial.get("karma") or 0)),
        ("イニシエーション", int(ctx.initiation.get("karma") or 0)),
        ("サブマージョン", int(ctx.submersion.get("karma") or 0)),
    ):
        if amount:
            ctx.karma_spend_lines.append({"kind": "other", "label": label, "amount": int(amount)})
    ctx.nuyen_spend_lines = nuyen_spend_breakdown(
        ctx.cyber_installed,
        ctx.bio_installed,
        ctx.gear,
        qi_nuyen=int(ctx.qi.get("nuyen") or 0),
        foci_nuyen=int(ctx.foci.get("nuyen") or 0),
        spirits_nuyen=int(ctx.spirits.get("nuyen") or 0),
    )

    ctx.quality_notoriety = int(ctx.effects.get("notoriety") or 0)
    ctx.notoriety_total = ctx.quality_notoriety + int(ctx.state.notoriety_bonus or 0)
    ctx.street_cred_total = int(ctx.state.street_cred or 0)
    quality_pa = int(ctx.effects.get("public_awareness") or 0)
    ctx.public_awareness_total = max(0, (ctx.street_cred_total + max(0, ctx.notoriety_total)) // 3 + quality_pa)
    if ctx.effects.get("erased") and ctx.public_awareness_total >= 1:
        ctx.public_awareness_total = 1

    ctx.physical_limit = _ceil_div((bod * 2 + agi + rea + stre) / 3) + int(ctx.effects.get("limit_physical") or 0)
    ctx.mental_limit = _ceil_div((logi * 2 + intuition + wil) / 3) + int(ctx.effects.get("limit_mental") or 0)
    ctx.social_limit = _ceil_div((cha * 2 + wil + ctx.ess) / 3) + int(ctx.effects.get("limit_social") or 0)
    ctx.cm_phys = 8 + _ceil_div(bod / 2) + ctx.effects["cm_physical"]
    ctx.cm_stun = 8 + _ceil_div(wil / 2) + ctx.effects["cm_stun"]
    ctx.initiative = rea + intuition + ctx.effects["initiative"]
    ctx.initiative_dice = 1 + int(ctx.effects.get("initiative_dice") or 0)
    ctx.warnings.extend(
        attach_spirit_tests(
            list(ctx.spirits.get("public") or []),
            int(ctx.total.get("MAG") or 0),
            ctx.effective_skills,
            ctx.skill_mods["skill_bonus"],
            ctx.total,
            ctx.data["skills"],
        )
    )
    ctx.warnings.extend(
        attach_focus_tests(
            list(ctx.foci.get("public") or []),
            int(ctx.total.get("MAG") or 0),
            ctx.effective_skills,
            ctx.skill_mods["skill_bonus"],
            ctx.total,
            ctx.data["skills"],
            ctx.mental_limit,
        )
    )
    ctx.warnings.extend(
        attach_complex_form_tests(
            list(ctx.resonance.get("public") or []),
            int(ctx.total.get("RES") or 0),
            ctx.effective_skills,
            ctx.skill_mods["skill_bonus"],
            ctx.total,
            ctx.data["skills"],
        )
    )
    ctx.warnings.extend(
        attach_sprite_tests(
            list(ctx.techno_sprites.get("public") or []),
            int(ctx.total.get("RES") or 0),
            ctx.effective_skills,
            ctx.skill_mods["skill_bonus"],
            ctx.total,
            ctx.data["skills"],
        )
    )

    ctx.movement = resolve_movement(ctx.meta, ctx.effects)

    tradition_info = ctx.magic.get("tradition") if isinstance(ctx.magic.get("tradition"), dict) else {}
    ctx.quality_report = {}
    ctx.negative_quality_karma = apply_quality_rules(
        ctx.state,
        ctx.qualities,
        ctx.free_quality_ids,
        quality_requirement_context(
            ctx.state,
            ctx.talent,
            ctx.qualities,
            ctx.meta,
            ctx.ess,
            ctx.ess_lost,
            ctx.effective_skills,
            set(ctx.adept.get("power_names") or []),
            {str(item.get("name") or "") for item in (ctx.magic.get("public") or []) if item.get("name")},
            str((tradition_info or {}).get("name") or ""),
            {item["name"] for item in ctx.cyber_installed},
            {item["name"] for item in ctx.bio_installed},
            ctx.effective_knowledge,
        ),
        ctx.errors,
        career=ctx.career,
        report=ctx.quality_report,
    )

    if not ctx.career:
        at_six = [n for n, r in ctx.skill_totals.items() if r >= 6]
        if len(at_six) > 1:
            ctx.errors.append("作成時にレーティング6の技能は1つまでです")
        # SR5 p.65: no more than one attribute at its natural maximum at
        # character creation (Edge / unused special attributes don't count).
        # Applies to every build method, not just Karma.
        at_natural_max = []
        for key, spec in ctx.attrs_spec.items():
            if key in {"ESS", "EDG", "MAG", "RES"} and key != ctx.special_key:
                continue
            if key not in ctx.ratings:
                continue
            racial_max = int(spec.get("max") or 0) + int(ctx.attr_max_bonus.get(key) or 0)
            if key == "MAG" and ctx.special_key == "MAG":
                racial_max = racial_max + int(ctx.initiation.get("mag_max_bonus") or 0)
            if key == "RES" and ctx.special_key == "RES":
                racial_max = racial_max + int(ctx.submersion.get("res_max_bonus") or 0)
            if racial_max > 0 and int(ctx.ratings.get(key) or 0) >= racial_max:
                at_natural_max.append(key)
        if len(at_natural_max) > 1:
            ctx.errors.append("作成時に自然上限の能力値は1つまでです")
        if not ctx.is_karma:
            if ctx.spent_physical > ctx.attr_points:
                ctx.errors.append(f"能力値点が不足しています（使用 {ctx.spent_physical} / 上限 {ctx.attr_points}）")
            if ctx.spent_special > ctx.special_from_meta:
                ctx.errors.append(
                    f"特殊能力値点が不足しています（使用 {ctx.spent_special} / 上限 {ctx.special_from_meta}）"
                )
            if ctx.skill_spent > ctx.skill_points:
                ctx.errors.append(f"技能点が不足しています（使用 {ctx.skill_spent} / 上限 {ctx.skill_points}）")
            if ctx.group_spent > ctx.group_points:
                ctx.errors.append(f"技能グループ点が不足しています（使用 {ctx.group_spent} / 上限 {ctx.group_points}）")
            if ctx.know_spent > ctx.know_max:
                ctx.errors.append(f"知識技能点が不足しています（使用 {ctx.know_spent} / 上限 {ctx.know_max}）")
    if ctx.karma_left < 0:
        ctx.errors.append(f"カルマが不足しています（残り {ctx.karma_left}）")
    if ctx.nuyen < 0:
        ctx.errors.append(f"ニューエンが不足しています（残り {ctx.nuyen}¥）")
    # SR5 p.98: at Standard power level only 5,000¥ of unspent resources
    # carry over into play (Street 200¥ / Prime 20,000¥). Surface it as a
    # chargen notice rather than silently deleting nuyen, matching Chummer.
    if not ctx.career:
        chargen_leftover = ctx.nuyen - int(ctx.state.nuyen_earned or 0)
        if chargen_leftover > NUYEN_CHARGEN_KEEP_MAX:
            lost = chargen_leftover - NUYEN_CHARGEN_KEEP_MAX
            ctx.warnings.append(
                f"未使用ニューエン {chargen_leftover:,}¥：Standard レベルでは "
                f"{NUYEN_CHARGEN_KEEP_MAX:,}¥ までしか持ち越せません（超過分 {lost:,}¥ は原則失われます）"
            )
    if ctx.ess <= 0:
        ctx.errors.append("エッセンスが0以下です")
    for item in ctx.installed:
        cap_max = float(item.get("capacity_max") or 0)
        if cap_max <= 0:
            continue
        used = float(item.get("capacity_used") or 0)
        if used > cap_max + 1e-9:
            ctx.errors.append(f"{item['name']} の容量超過（{used:g}/{cap_max:g}）")

    if not ctx.is_karma:
        allowed = {e["name"] for e in heritage_options(ctx.state.priorities.Heritage)}
        if allowed and ctx.state.metatype not in allowed:
            ctx.errors.append(f"{ctx.state.metatype} はこの優先度のメタに含まれません")
    if not ctx.career:
        _check_avail_limit(
            _avail_entries(
                ctx.cyber_installed,
                ctx.bio_installed,
                ctx.gear.get("armor_items"),
                ctx.gear.get("armor_mods"),
                ctx.gear.get("weapons"),
                ctx.gear.get("weapon_accessories"),
                ctx.gear.get("commlinks"),
                ctx.gear.get("cyberdecks"),
                ctx.gear.get("rccs"),
                ctx.gear.get("optics"),
                ctx.gear.get("programs"),
                ctx.gear.get("apps"),
                ctx.gear.get("sensors"),
                ctx.gear.get("drones"),
                ctx.gear.get("vehicles"),
                ctx.gear.get("vehicle_mods"),
                ctx.gear.get("weapon_mounts"),
                ctx.gear.get("gear"),
                ctx.gear.get("lifestyles"),
                ctx.foci.get("public"),
            ),
            ctx.effects,
            ctx.errors,
        )
        _check_device_rating_limit(
            _device_rating_entries(
                ctx.cyber_installed,
                ctx.bio_installed,
                ctx.gear.get("commlinks"),
                ctx.gear.get("cyberdecks"),
                ctx.gear.get("rccs"),
                ctx.gear.get("optics"),
                ctx.gear.get("sensors"),
                ctx.gear.get("gear"),
            ),
            ctx.errors,
        )

    ctx.state.attributes = ctx.ratings
    sum_spent = sum_to_ten_spent(ctx.state.priorities)
    ctx.state.derived = {
        "errors": ctx.errors,
        "warnings": ctx.warnings,
        "build_method": ctx.state.build_method,
        "sum_to_ten": {
            "used": sum_spent,
            "max": SUM_TO_TEN_BUDGET,
            "costs": dict(SUM_TO_TEN_COST),
            "unique": priorities_are_unique(ctx.state.priorities),
        },
        "karma_chargen": {
            "enabled": ctx.is_karma,
            "pool": ctx.karma_pool if ctx.is_karma else 0,
            "nuyen_karma": int(ctx.state.karma_nuyen or 0),
            "nuyen_karma_max": int(ctx.nuyen_karma_max),
            "nuyen_per_karma": KARMA_TO_NUYEN,
            "metatype": ctx.metatype_karma_cost if ctx.is_karma else 0,
            "attributes": ctx.attr_karma if ctx.is_karma else 0,
            "skills": ctx.skill_buy_karma if ctx.is_karma else 0,
            "knowledge": ctx.knowledge_karma if ctx.is_karma else 0,
            "specializations": ctx.spec_karma if ctx.is_karma else 0,
            "qualities": ctx.karma_from_q,
            "other": ctx.mystic_karma
            + ctx.extra_adept_karma
            + ctx.spell_karma
            + int(ctx.contacts.get("karma") or 0)
            + int(ctx.martial.get("karma") or 0)
            + int(ctx.initiation.get("karma") or 0)
            + int(ctx.submersion.get("karma") or 0),
        },
        "totals": ctx.total,
        "limits": {
            "physical": ctx.physical_limit,
            "mental": ctx.mental_limit,
            "social": ctx.social_limit,
        },
        "limit_modifiers": compact_limit_modifiers(ctx.effects),
        "condition_monitor": {"physical": ctx.cm_phys, "stun": ctx.cm_stun},
        "initiative": {"value": ctx.initiative, "dice": ctx.initiative_dice},
        "movement": ctx.movement,
        "essence": ctx.ess,
        "essence_lost": ctx.ess_lost,
        "essence_lost_cyber": ctx.ess_lost_cyber,
        "essence_lost_bio": ctx.ess_lost_bio,
        "armor": int(ctx.effects["armor"]) + int(ctx.gear.get("armor") or 0),
        "special_armor": special_armor_totals(ctx.effects),
        "worn_armor": ctx.gear.get("worn_name") or "",
        "armor_items": ctx.gear.get("armor_items") or [],
        "armor_mods": ctx.gear.get("armor_mods") or [],
        "weapons": ctx.gear.get("weapons") or [],
        "weapon_accessories": ctx.gear.get("weapon_accessories") or [],
        "recoil": ctx.gear.get("recoil") or {"str": 0, "str_rc": 0, "free": 1},
        "active_drugs": ctx.active_drugs,
        "commlinks": ctx.gear.get("commlinks") or [],
        "cyberdecks": ctx.gear.get("cyberdecks") or [],
        "rccs": ctx.gear.get("rccs") or [],
        "optics": ctx.gear.get("optics") or [],
        "programs": ctx.gear.get("programs") or [],
        "apps": ctx.gear.get("apps") or [],
        "sensors": ctx.gear.get("sensors") or [],
        "drones": ctx.gear.get("drones") or [],
        "vehicles": ctx.gear.get("vehicles") or [],
        "vehicle_mods": ctx.gear.get("vehicle_mods") or [],
        "weapon_mounts": ctx.gear.get("weapon_mounts") or [],
        "gear": ctx.gear.get("gear") or [],
        "lifestyles": ctx.gear.get("lifestyles") or [],
        "commlink": ctx.gear.get("commlink"),
        "cyberdeck": ctx.gear.get("cyberdeck"),
        "rcc": ctx.gear.get("rcc"),
        "lifestyle": ctx.gear.get("lifestyle"),
        "nuyen": ctx.nuyen,
        "nuyen_spent": ctx.nuyen_spent,
        "nuyen_pool": ctx.nuyen_pool,
        "nuyen_earned": int(ctx.state.nuyen_earned or 0),
        "karma_earned": int(ctx.state.karma_earned or 0),
        "career": ctx.career,
        "career_advancement_karma": int(ctx.career_adv_karma),
        "career_advancement_lines": ctx.career_adv_lines,
        "nuyen_amt": int(ctx.effects.get("nuyen_amt") or 0),
        "nuyen_karma_max": int(ctx.nuyen_karma_max),
        "trustfund": int(ctx.effects.get("trustfund") or 0),
        "trustfund_label": TRUST_FUND_STIPEND.get(int(ctx.effects.get("trustfund") or 0), ""),
        "ambidextrous": bool(ctx.effects.get("ambidextrous")),
        "overclocker": bool(ctx.effects.get("overclocker")),
        "special_modification_limit": {
            "used": int(ctx.gear.get("special_modification_used") or 0),
            "max": int(ctx.effects.get("special_modification_limit") or 0),
        },
        "friends_in_high_places": bool(ctx.effects.get("friends_in_high_places")),
        "made_man": bool(ctx.effects.get("made_man")),
        "black_market_discount": bool(ctx.effects.get("black_market_discount")),
        "black_market_category": ctx.bmp_category if ctx.bmp_active else "",
        "black_market_contact_id": ctx.bmp_contact_id if ctx.bmp_active else "",
        "black_market_avail_bonus": BLACK_MARKET_AVAIL_BONUS if ctx.bmp_active else 0,
        "dealer_connection_categories": list(ctx.effects.get("dealer_connection_categories") or []),
        "cyberware_ess_multiplier": int(ctx.effects.get("cyberware_ess_multiplier") or 100),
        "bioware_ess_multiplier": int(ctx.effects.get("bioware_ess_multiplier") or 100),
        "skill_rating_max": ctx.skill_rating_cap,
        "skill_group_max": ctx.skill_group_cap,
        "avail_limit": None if ctx.career else CHARGEN_AVAIL_MAX,
        "device_rating_limit": None if ctx.career else CHARGEN_DEVICE_RATING_MAX,
        "ware_attr_limit": None if ctx.career else CHARGEN_WARE_ATTR_BONUS_MAX,
        "ware_attr_bonus": ctx.ware_attr_bonus,
        "karma": {
            "pool": ctx.karma_pool,
            "spent": ctx.karma_spent,
            "remaining": ctx.karma_left,
            "negative": {
                "used": ctx.negative_quality_karma,
                "max": None if ctx.career else NEGATIVE_QUALITY_KARMA_CAP,
            },
        },
        "power_points": {"used": ctx.power_spent, "max": ctx.power_pool},
        "metagenic": ctx.quality_report.get("metagenic"),
        "adept_powers": ctx.adept["public"],
        "mystic_pp": ctx.state.mystic_pp,
        "way_discount": {"used": ctx.adept.get("discount_used") or 0, "max": ctx.adept.get("discount_max") or 0},
        "mentor": ctx.mentor.get("public"),
        "needs_mentor": ctx.needs_mentor,
        "qi_foci": ctx.qi.get("public") or [],
        "foci": ctx.foci.get("public") or [],
        "focus_limits": ctx.focus_limits,
        "spirits": ctx.spirits.get("public") or [],
        "enhancements": ctx.enhancements.get("public") or [],
        "damage_resistance": int(ctx.effects.get("damage_resistance") or 0),
        "unarmed_dv": int(ctx.effects.get("unarmed_dv") or 0),
        "unarmed_physical": bool(ctx.effects.get("unarmed_physical")),
        "unlock_skills": list(ctx.effects.get("unlock_skills") or []),
        "spells": ctx.magic.get("public") or [],
        "spell_points": {
            "used": ctx.magic.get("used") or 0,
            "free": ctx.magic.get("free_max") or 0,
            "paid": ctx.magic.get("paid") or 0,
            "karma": ctx.magic.get("karma") or 0,
            "spell_karma": spell_karma_cost("spell", ctx.effects),
        },
        "tradition": ctx.magic.get("tradition"),
        "drain_resist": {"pool": ctx.magic.get("resist") or 0, "attrs": ctx.magic.get("resist_attrs") or "WIL+INT"},
        "complex_forms": ctx.resonance.get("public") or [],
        "complex_form_points": {
            "used": ctx.resonance.get("used") or 0,
            "free": ctx.resonance.get("free_max") or 0,
            "paid": ctx.resonance.get("paid") or 0,
        },
        "sprites": ctx.techno_sprites.get("public") or [],
        "stream": ctx.resonance.get("stream"),
        "fade_resist": {
            "pool": ctx.resonance.get("resist") or 0,
            "attrs": ctx.resonance.get("resist_attrs") or "WIL+RES",
        },
        "living_persona": (
            living_persona(
                ctx.total,
                int(ctx.total.get("RES") or 0),
                ctx.effects.get("living_persona") if isinstance(ctx.effects.get("living_persona"), dict) else None,
                int(ctx.effects.get("matrix_initiative_dice") or 0),
            )
            if ctx.talent["name"] in RES_TALENTS
            else None
        ),
        "points": {
            "attributes": {"used": ctx.spent_physical, "max": ctx.attr_points},
            "special": {"used": ctx.spent_special, "max": ctx.special_from_meta},
            "skills": {"used": ctx.skill_spent, "max": ctx.skill_points},
            "skill_groups": {"used": ctx.group_spent, "max": ctx.group_points},
            "knowledge": {"used": ctx.know_spent, "max": ctx.know_max},
            "contacts": {"used": ctx.contacts.get("used") or 0, "max": ctx.contacts.get("free") or 0},
        },
        "knowledge_skills": ctx.knowledge["public"],
        "contacts": ctx.contacts.get("public") or [],
        "contact_points": {
            "used": ctx.contacts.get("used") or 0,
            "free": ctx.contacts.get("free") or 0,
            "paid": ctx.contacts.get("paid") or 0,
            "karma": int(ctx.contacts.get("karma") or 0),
            "karma_per_point": int(ctx.contacts.get("karma_per_point", 1)),
        },
        "martial_arts": ctx.martial.get("public") or [],
        "martial_art_points": {
            "styles": ctx.martial.get("style_count") or 0,
            "style_max": ctx.martial.get("style_max") or MARTIAL_ART_CHARGEN_STYLE_MAX,
            "techniques": ctx.martial.get("technique_count") or 0,
            "technique_max": ctx.martial.get("technique_max") or MARTIAL_ART_CHARGEN_TECHNIQUE_MAX,
            "karma": ctx.martial.get("karma") or 0,
        },
        "martial_spec_options": ctx.martial.get("spec_extras") or {},
        "unarmed_reach": int(ctx.effects.get("unarmed_reach") or 0) + int(ctx.effects.get("reach") or 0),
        "unarmed_ap": int(ctx.effects.get("unarmed_ap") or 0),
        "reach": int(ctx.effects.get("reach") or 0),
        "lifestyle_cost_mod": int(ctx.effects.get("lifestyle_cost") or 0),
        "street_cred": ctx.street_cred_total,
        "notoriety": ctx.notoriety_total,
        "notoriety_quality": ctx.quality_notoriety,
        "notoriety_bonus": int(ctx.state.notoriety_bonus or 0),
        "fame": int(ctx.effects.get("fame") or 0),
        "public_awareness": ctx.public_awareness_total,
        "erased": bool(ctx.effects.get("erased")),
        "excon": bool(ctx.effects.get("excon")),
        "reward_log": [
            {"id": row.id, "label": row.label, "karma": int(row.karma or 0), "nuyen": int(row.nuyen or 0)}
            for row in (ctx.state.reward_log or [])
        ],
        "karma_spend_breakdown": ctx.karma_spend_lines,
        "nuyen_spend_breakdown": ctx.nuyen_spend_lines,
        "fatigue_resist": int(ctx.effects.get("fatigue_resist") or 0),
        "spell_resistance": int(ctx.effects.get("spell_resistance") or 0),
        "spell_defense": spell_defense_pools(ctx.effects),
        "spell_dice_pool": list(ctx.effects.get("spell_dice_pool") or []),
        "action_dice_pools": list(ctx.effects.get("action_dice_pools") or []),
        "test_mods": dict(ctx.effects.get("test_mods") or {}),
        "cm_recovery": {
            "physical": int(ctx.effects.get("cm_recovery_physical") or 0)
            + (int(ctx.ess) if ctx.effects.get("cm_recovery_physical_add_ess") else 0),
            "stun": int(ctx.effects.get("cm_recovery_stun") or 0)
            + (int(ctx.ess) if ctx.effects.get("cm_recovery_stun_add_ess") else 0),
        },
        "essence_penalty": round(float(ctx.effects.get("essence_penalty") or 0), 4),
        "attribute_max_bonus": dict(ctx.attr_max_bonus),
        "disabled_skills": list(ctx.effects.get("disabled_skills") or []),
        "disabled_skill_groups": list(ctx.effects.get("disabled_skill_groups") or []),
        "blocked_default_categories": list(ctx.effects.get("blocked_default_categories") or []),
        "native_language_limit": int(ctx.knowledge.get("native_limit") or 1),
        "prototype_transhuman_ess": float(ctx.effects.get("prototype_transhuman_ess") or 0),
        "burnout_way": bool(ctx.effects.get("burnout_way")),
        "disabled_cyberware_grades": list(ctx.effects.get("disabled_cyberware_grades") or []),
        "disabled_bioware_grades": list(ctx.effects.get("disabled_bioware_grades") or []),
        "limit_spell_categories": list(ctx.effects.get("limit_spell_categories") or []),
        "limit_spirit_categories": list(ctx.effects.get("limit_spirit_categories") or []),
        "allow_spell_categories": list(ctx.effects.get("allow_spell_categories") or []),
        "allow_spell_ranges": list(ctx.effects.get("allow_spell_ranges") or []),
        "spell_range_gated": bool(ctx.magic.get("range_gated")),
        "block_spell_descriptors": list(ctx.effects.get("block_spell_descriptors") or []),
        "extra_spirits": list(ctx.effects.get("extra_spirits") or []),
        "add_spirit_picks": list(ctx.effects.get("add_spirit_picks") or []),
        "initiate_grade": int(ctx.initiation.get("grade") or 0),
        "initiation": {
            "grade": int(ctx.initiation.get("grade") or 0),
            "karma": int(ctx.initiation.get("karma") or 0),
            "choices": ctx.initiation.get("choices") or [],
            "metamagics": ctx.initiation.get("metamagics") or [],
            "arts": ctx.initiation.get("arts") or [],
        },
        "submersion_grade": int(ctx.submersion.get("grade") or 0),
        "submersion": {
            "grade": int(ctx.submersion.get("grade") or 0),
            "karma": int(ctx.submersion.get("karma") or 0),
            "choices": ctx.submersion.get("choices") or [],
            "echoes": ctx.submersion.get("echoes") or [],
        },
        "skill_totals": ctx.skill_totals,
        "skill_specializations": ctx.specs["specs"],
        "skill_expertises": ctx.expertises,
        "exotic_skills": ctx.exotic["public"],
        "skillsoft": ctx.skillsofts["all"],
        "skillwires": ctx.skillsofts["skillwires"],
        "skilljack": ctx.skillsofts["skilljack"],
        "skill_bonus": ctx.skill_mods["skill_bonus"],
        "skill_group_bonus": ctx.skill_mods["skill_group_bonus"],
        "skill_category_bonus": ctx.skill_mods["skill_category_bonus"],
        "skill_bonus_notes": ctx.skill_mods["skill_bonus_notes"],
        "skill_max_bonus": ctx.skill_picks["skill_max_bonus"],
        "skill_pick_slots": ctx.skill_picks["slots"],
        "enabled_tabs": sorted(ctx.enabled),
        "unimplemented_bonuses": ctx.effects["unimplemented"],
        "qualities": [
            {
                "id": q["id"],
                "name": q["name"],
                "karma": 0 if q["id"] in ctx.free_quality_ids else q["karma"],
                "category": q["category"],
                "source": q["source"],
                "needs_extra": quality_needs_extra(q),
                "extra": ctx.state.quality_extras.get(q["id"]) or "",
                "spirit_extra": ctx.state.quality_extras.get(quality_spirit_category_extra_key(q["id"])) or "",
                "extra_kind": q.get("extra_kind"),
                "select_options": list(q.get("select_options") or []),
                "spirit_options": list(q.get("spirit_options") or []),
                "expertise_skill": q.get("expertise_skill") or "",
                "add_spirit_count": int(q.get("add_spirit_count") or 0),
                "selectside": _quality_has_selectside(q),
                "side": _normalize_side(ctx.state.quality_extras.get(q["id"])) if _quality_has_selectside(q) else None,
                "free": q["id"] in ctx.free_quality_ids or bool(q.get("onlyprioritygiven")),
            }
            for q in ctx.qualities
        ],
        "cyberware": [_public_installed(item) for item in ctx.cyber_installed],
        "bioware": [_public_installed(item) for item in ctx.bio_installed],
        "ware_ranges": ware_ranges(ctx.attrs_spec),
        "limb_replace": ctx.limb_replace,
        "limb_quality": ctx.limb_quality,
        "talent": ctx.talent,
        "metatype_info": {
            "name": ctx.meta["name"],
            "parent": ctx.meta.get("parent"),
            "attributes": {
                key: {
                    **spec,
                    "max": int(spec.get("max") or 0) + int(ctx.attr_max_bonus.get(key) or 0),
                    "aug": int(spec.get("aug") or 0) + int(ctx.attr_max_bonus.get(key) or 0),
                }
                for key, spec in _effective_attr_spec(
                    ctx.attrs_spec,
                    ctx.special_key,
                    ctx.talent_start,
                    int(ctx.initiation.get("mag_max_bonus") or 0),
                    int(ctx.submersion.get("res_max_bonus") or 0),
                ).items()
            },
            "source": ctx.meta.get("source"),
        },
        "translations": {
            k: ctx.data["translations"].get(k, k) for k in [ctx.state.metatype, ctx.state.metavariant or ""]
        },
    }
    return ctx.state
