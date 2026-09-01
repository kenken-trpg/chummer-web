from __future__ import annotations

import math
from typing import Any

from ..data_loader import (
    CHARGEN_AVAIL_MAX,
    CHARGEN_DEVICE_RATING_MAX,
    CHARGEN_WARE_ATTR_BONUS_MAX,
    PHYSICAL_ATTRS,
    catalog,
    eval_formula,
)
from ..improvements import (
    ATTR_ALIASES,
    apply_bonus_nodes,
    collect_effects,
    compact_limit_modifiers,
    special_armor_totals,
    substitute_rating,
)
from ..models import (
    ArmorInstall,
    CareerBaseline,
    CharacterState,
    CommlinkInstall,
    LifestyleInstall,
    RewardEntry,
    WeaponInstall,
)
from .constants import (
    ADEPT_TALENTS,
    BLACK_MARKET_AVAIL_BONUS,
    BUILD_METHOD_KARMA,
    CAREER_SKILL_GROUP_MAX,
    CAREER_SKILL_MAX,
    COMPLEX_FORM_TALENTS,
    FOCUS_TALENTS,
    KARMA_ACTIVE_SKILL,
    KARMA_ATTRIBUTE,
    KARMA_CHARGEN_POOL,
    KARMA_KNOWLEDGE,
    KARMA_NUYEN_MAX,
    KARMA_SKILL_GROUP,
    KARMA_SPECIALIZATION,
    KARMA_TO_NUYEN,
    MAG_TALENTS,
    MARTIAL_ART_CHARGEN_STYLE_MAX,
    MARTIAL_ART_CHARGEN_TECHNIQUE_MAX,
    MENTOR_SPIRIT_ID,
    MYSTIC_PP_KARMA,
    NEGATIVE_QUALITY_KARMA_CAP,
    NUYEN_CHARGEN_KEEP_MAX,
    PRIORITY_KARMA_NUYEN_BASE,
    RES_TALENTS,
    SPELL_TALENTS,
    SPIRIT_TALENTS,
    SPRITE_TALENTS,
    SUM_TO_TEN_BUDGET,
    SUM_TO_TEN_COST,
    TRUST_FUND_STIPEND,
    _normalize_side,
    quality_addspirit_extra_key,  # noqa: F401  (re-exported for tests)
    quality_contact_extra_key,
    quality_spirit_category_extra_key,
)
from .contacts import (  # (contact network + Ex-Con / Erased caps)
    apply_erased_lifestyle_cap,
    apply_excon_ware_ban,
    resolve_contacts,
    sync_quality_contacts,
)
from .formulas import (  # (stat-expression helpers)
    _add_leading_int,
    _ceil_div,
    _replace_leading_int,
    parse_armor_value,
)
from .gear import (  # (gear pipeline clusters; see engine/gear/)
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
    apply_reach_bonus,
    apply_unarmed_bonuses,
    apply_weapon_category_dv,
    apply_weapon_skill_accuracy,
    bind_weapon_category_dv,
    bind_weapon_skill_accuracy,
)
from .karma import (  # (cost maths)
    _active_karma_mults,
    _filter_karma_rules,
    _group_floor_map,
    _karma_cost_with_category_mods,
    _karma_raise_cost,
    _matching_karma_rules,
    _point_cost,
    _skill_category_map,
    _skill_group_category_map,
    _skill_groups_for_category,
    attribute_karma_cost,
    knowledge_excess_karma,
    knowledge_points_spent,
    skill_karma_cost,
)
from .limits import (  # (chargen avail / device-rating / ware-attr caps)
    _avail_entries,
    _check_avail_limit,
    _check_device_rating_limit,
    _check_ware_attribute_cap,
    _device_rating_entries,
    _finalize_avail_tree,
    _ware_attribute_bonuses,
)
from .lookups import (  # catalog single-row accessors; see engine/lookups.py
    _item_by_id,
    _tradition_by_id,
    find_metatype,  # noqa: F401  (re-exported for store.py / chummer_export.py / tests)
)
from .magic import (  # (awakened/emerged pipeline clusters; see engine/magic/)
    apply_focus_limits,
    apply_free_metamagics,
    apply_granted_spells,
    apply_tradition_bonuses,
    attach_focus_tests,
    attach_spirit_tests,
    attach_weapon_focus_dice,
    bind_extra_spirits,
    bind_spell_category_drain_damage,
    bind_spell_spirit_limits,
    resolve_adept_powers,
    resolve_enhancements,
    resolve_foci,
    resolve_initiation,
    resolve_mentor,
    resolve_qi_foci,
    resolve_spells,
    resolve_spirits,
    resolve_submersion,
    spell_cast_info,
    spell_defense_pools,
    spell_drain_value,  # noqa: F401  (re-exported for tests)
    spell_karma_cost,
    tradition_resist,  # noqa: F401  (re-exported for tests)
)
from .martial_arts import (  # (style/technique resolution)
    resolve_martial_arts,
    sync_quality_martial_arts,
)
from .pricing import (  # (post-resolve cost/avail adjustments)
    apply_black_market_avail,
    apply_overclocker,
    apply_purchase_discounts,
    apply_ware_essence_multipliers,
)
from .priority import (  # noqa: F401  (re-exported for store.py)
    all_talent_options,
    heritage_options,
    normalize_build_method,
    priorities_are_unique,
    priority_letter_cost,
    priority_value,
    resolve_talent,
    resolve_talent_for_method,
    sum_to_ten_spent,
    talent_options,
    talent_special,
    validate_priorities,
)
from .qualities import (  # (quality gather / extra-pick / binder pipeline; see engine/qualities.py)
    _quality_has_selectside,
    apply_quality_rules,
    bind_action_dice_pools,
    bind_select_powers,
    free_powers_from_grants,
    gather_qualities,
    is_way_quality,  # noqa: F401  (re-exported for store.py)
    quality_needs_extra,
    quality_requirement_context,
    resolve_quality_sides,
    sanitize_quality_ids,  # noqa: F401  (re-exported for store.py)
)
from .resonance import (  # (technomancer pipeline; see engine/resonance.py)
    _cyberadept_res_penalty_reduction,
    apply_granted_echoes,
    attach_complex_form_tests,
    attach_sprite_tests,
    living_persona,
    resolve_complex_forms,
    resolve_sprites,
)
from .selects import (  # (select-node option enumeration)
    gear_extra_options,  # noqa: F401  (re-exported for store.py)
    selectskill_options,  # noqa: F401  (re-exported for tests)
)
from .skills import (  # (knowledge / specialization / exotic / skillsoft resolution)
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
from .ware import (  # (cyberware/bioware pipeline clusters; see engine/ware/)
    _attach_ware_to_vehicle_mods,
    _clamp_ware_grades,
    _drop_invalid_vehicle_ware,
    _installed_ware_names,
    _public_installed,
    _required_warnings,
    _side_conflicts,
    _vehicle_hosted_ware_ids,
    _vehicle_mod_hosts,
    _zero_vehicle_hosted_essence,
    apply_cyberseeker,
    ensure_subsystems,
    limb_attribute_replace,
    redliner_incompat_warnings,
    resolve_ware,
    ware_ranges,
)


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


def sync_reward_totals(state: CharacterState) -> None:
    """Keep earned pools aligned with reward_log when the ledger has rows."""
    log = list(getattr(state, "reward_log", None) or [])
    cleaned: list[RewardEntry] = []
    for raw in log:
        if isinstance(raw, RewardEntry):
            entry = raw
        elif isinstance(raw, dict):
            entry = RewardEntry.model_validate(raw)
        else:
            continue
        entry.karma = max(0, int(entry.karma or 0))
        entry.nuyen = max(0, int(entry.nuyen or 0))
        entry.label = str(entry.label or "").strip() or "報酬"
        cleaned.append(entry)
    state.reward_log = cleaned
    if cleaned:
        state.karma_earned = sum(int(row.karma or 0) for row in cleaned)
        state.nuyen_earned = sum(int(row.nuyen or 0) for row in cleaned)


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


def resolve_attribute_selects(
    state: CharacterState,
    effects: dict[str, Any],
    qualities: list[dict[str, Any]],
) -> tuple[dict[str, int], list[str]]:
    warnings: list[str] = []
    bonus: dict[str, int] = {}
    extras = state.quality_extras or {}
    by_name = {q["name"]: q for q in qualities}
    for sel in effects.get("attribute_selects") or []:
        source = str(sel.get("source") or "")
        spec = by_name.get(source)
        if not spec:
            continue
        picked = ATTR_ALIASES.get(str(extras.get(spec["id"]) or "").strip().upper())
        exclude = {str(item) for item in (sel.get("exclude") or [])}
        max_bonus = max(1, int(sel.get("max") or 1))
        if not picked:
            warnings.append(f"{source} の能力値を選んでください")
            continue
        if picked in exclude or picked in {"ESS"}:
            warnings.append(f"{source} に {picked} は選べません")
            continue
        bonus[picked] = int(bonus.get(picked) or 0) + max_bonus
    return bonus, warnings


def apply_lifestyle_cost_mod(gear: dict[str, Any], percent: int) -> None:
    if not percent:
        return
    factor = (100 + int(percent)) / 100.0
    delta = 0
    for row in gear.get("lifestyles") or []:
        before = int(row.get("nuyen") or 0)
        monthly = int(row.get("monthly") or 0)
        after = int(round(before * factor))
        row["monthly"] = int(round(monthly * factor))
        row["nuyen"] = after
        row["lifestyle_cost_mod"] = int(percent)
        delta += after - before
    if gear.get("lifestyle") and (gear.get("lifestyles") or []):
        gear["lifestyle"] = (gear.get("lifestyles") or [])[0]
    gear["nuyen"] = int(gear.get("nuyen") or 0) + delta


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
    lifestyles: list[dict[str, Any]] = []
    errors: list[str] = []

    kept_armor: list[ArmorInstall] = []
    for inst in state.armor:
        spec = _item_by_id("armor", inst.armor_id)
        if not spec:
            continue
        rating = _clamp_rating(spec, inst.rating)
        inst.rating = rating
        inst.equipped = bool(inst.equipped)
        inst.wireless = bool(inst.wireless)
        has_wireless = bool(spec.get("wirelessbonus"))
        cost = int(eval_formula(str(spec.get("cost") or "0"), rating, 0))
        nuyen += cost
        value, additive = parse_armor_value(str(spec.get("armor") or "0"), rating)
        if inst.equipped:
            nodes = substitute_rating(list(spec.get("bonus") or []), rating)
            if has_wireless and inst.wireless:
                nodes = nodes + substitute_rating(list(spec.get("wirelessbonus") or []), rating)
            if nodes:
                bonus_sources.append((spec["name"], nodes))
        kept_armor.append(inst)
        armor_items.append(
            {
                "id": inst.id,
                "armor_id": spec["id"],
                "name": spec["name"],
                "category": spec.get("category") or "Armor",
                "armor": spec.get("armor") or "0",
                "armor_value": value,
                "additive": additive,
                "rating": rating,
                "rating_max": int(spec.get("maxrating") or 0),
                "equipped": inst.equipped,
                "wireless": inst.wireless,
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
    for inst in state.weapons:
        spec = _item_by_id("weapons", inst.weapon_id)
        if not spec:
            continue
        qty = max(1, int(inst.qty or 1))
        inst.qty = qty
        unit = int(eval_formula(str(spec.get("cost") or "0"), 1, 0))
        cost = unit * qty
        nuyen += cost
        kept_weapons.append(inst)
        weapons.append(
            _public_weapon(
                spec,
                inst_id=inst.id,
                qty=qty,
                nuyen=cost,
                loaded_ammo_id=inst.loaded_ammo_id,
            )
        )
    state.weapons = kept_weapons
    _append_ware_weapons(weapons, ware_items or [], state, attr_totals)
    weapon_accessories, acc_nuyen, acc_warns, acc_errors, special_mod_used = _resolve_weapon_accessories(
        state, weapons, special_modification_limit=special_modification_limit
    )
    recoil_info = _apply_recoil_totals(weapons, attr_totals)
    nuyen += acc_nuyen
    warnings.extend(acc_warns)
    errors.extend(acc_errors)

    kept_links: list[CommlinkInstall] = []
    for inst in state.commlinks:
        spec = _item_by_id("commlinks", inst.gear_id)
        if not spec:
            continue
        rating = _clamp_rating(spec, inst.rating)
        inst.rating = rating
        cost = int(eval_formula(str(spec.get("cost") or "0"), rating, 0))
        nuyen += cost
        device = int(eval_formula(str(spec.get("devicerating") or "0"), rating, 0))
        processing = int(eval_formula(str(spec.get("dataprocessing") or "0"), rating, 0))
        firewall = int(eval_formula(str(spec.get("firewall") or "0"), rating, 0))
        kept_links.append(inst)
        commlinks.append(
            {
                "id": inst.id,
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

    kept_lifestyles: list[LifestyleInstall] = []
    quality_specs = {item["id"]: item for item in catalog().get("lifestyle_qualities") or []}
    quality_by_name = {item["name"]: item for item in quality_specs.values()}
    for inst in state.lifestyles:
        spec = _item_by_id("lifestyles", inst.lifestyle_id)
        if not spec:
            continue
        months = max(1, int(inst.months or 1))
        inst.months = months
        lifestyle_name = str(spec.get("name") or "")
        base_monthly = int(spec.get("cost") or 0)
        lp_max = int(spec.get("lp") or 0)
        quality_ids = list(inst.quality_ids or [])
        extras = dict(inst.quality_extras or {})

        def _append_lifestyle_quality(
            qid: str,
            *,
            extra: str = "",
            from_freegrid: bool = False,
        ) -> None:
            nonlocal lp_used, quality_monthly, multiplier_pct
            qspec = quality_specs.get(qid)
            if not qspec:
                return
            if qid in seen_quality and not qspec.get("allow_multiple"):
                return
            seen_quality.add(qid)
            allowed = [str(name) for name in (qspec.get("allowed") or [])]
            free = bool(from_freegrid) or (bool(allowed) and lifestyle_name in allowed)
            if allowed and lifestyle_name not in allowed and not from_freegrid:
                warnings.append(f"{qspec['name']} は {lifestyle_name} では取得できません")
                return
            lp_cost = int(qspec.get("lp") or 0)
            lp_used += lp_cost
            add_cost = 0 if free else int(qspec.get("cost") or 0)
            quality_monthly += add_cost
            multiplier_pct += int(qspec.get("multiplier") or 0)
            extra_val = str(extra or extras.get(qid) or "").strip()
            if qspec.get("needs_extra") and not extra_val:
                warnings.append(f"{qspec['name']} の対象を入力してください")
            nodes = list(qspec.get("bonus") or [])
            bonus_nodes = [node for node in nodes if node.get("tag") != "selecttext"]
            if bonus_nodes:
                bonus_sources.append((f"{lifestyle_name}:{qspec['name']}", bonus_nodes))
            kept_qualities.append(
                {
                    "id": f"{qid}:{len(kept_qualities)}",
                    "quality_id": qid,
                    "name": qspec["name"],
                    "category": qspec.get("category") or "",
                    "lp": lp_cost,
                    "cost": add_cost,
                    "free": free,
                    "from_freegrid": from_freegrid,
                    "multiplier": int(qspec.get("multiplier") or 0),
                    "extra": extra_val,
                    "needs_extra": bool(qspec.get("needs_extra")),
                    "source": qspec.get("source") or "",
                    "page": qspec.get("page") or "",
                }
            )

        kept_qualities: list[dict[str, Any]] = []
        seen_quality: set[str] = set()
        lp_used = 0
        quality_monthly = 0
        multiplier_pct = 0

        # Freegrids are always derived from the lifestyle (may repeat with different selects).
        for grid in spec.get("freegrids") or []:
            grid_name = str(grid.get("name") or "Grid Subscription")
            grid_spec = quality_by_name.get(grid_name)
            if not grid_spec:
                continue
            # allow_multiple freegrids share one quality id; clear seen for each instance.
            if grid_spec.get("allow_multiple"):
                seen_quality.discard(grid_spec["id"])
            _append_lifestyle_quality(
                grid_spec["id"],
                extra=str(grid.get("select") or "").strip(),
                from_freegrid=True,
            )

        for qid in quality_ids:
            _append_lifestyle_quality(qid)

        if lp_max > 0 and lp_used > lp_max:
            warnings.append(f"{lifestyle_name} のライフスタイルポイント超過（使用 {lp_used} / 上限 {lp_max}）")

        monthly = int(round(base_monthly * (100 + multiplier_pct) / 100.0)) + quality_monthly
        cost = monthly * months
        nuyen += cost
        # Persist user picks only; freegrids are re-derived each compute.
        inst.quality_ids = [row["quality_id"] for row in kept_qualities if not row.get("from_freegrid")]
        inst.quality_extras = {
            row["quality_id"]: row["extra"]
            for row in kept_qualities
            if row.get("extra") and not row.get("from_freegrid")
        }
        kept_lifestyles.append(inst)
        lifestyles.append(
            {
                "id": inst.id,
                "lifestyle_id": spec["id"],
                "name": lifestyle_name,
                "months": months,
                "increment": spec.get("increment") or "month",
                "monthly": monthly,
                "base_monthly": base_monthly,
                "quality_monthly": quality_monthly,
                "multiplier_pct": multiplier_pct,
                "nuyen": cost,
                "lp_used": lp_used,
                "lp_max": lp_max,
                "dice": int(spec.get("dice") or 0),
                "qualities": kept_qualities,
                "avail": spec.get("avail") or "",
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
    state.lifestyles = kept_lifestyles

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
    data = catalog()
    state.build_method = normalize_build_method(getattr(state, "build_method", None))
    is_karma = state.build_method == BUILD_METHOD_KARMA
    career = bool(getattr(state, "career", False))
    state.career = career
    state.street_cred = max(0, int(getattr(state, "street_cred", 0) or 0))
    state.notoriety_bonus = int(getattr(state, "notoriety_bonus", 0) or 0)
    sync_reward_totals(state)
    state.karma_earned = max(0, int(getattr(state, "karma_earned", 0) or 0))
    state.nuyen_earned = max(0, int(getattr(state, "nuyen_earned", 0) or 0))
    skill_rating_cap = CAREER_SKILL_MAX if career else 6
    skill_group_cap = CAREER_SKILL_GROUP_MAX if career else 6
    errors = validate_priorities(state.priorities, state.build_method)
    meta = find_metatype(state.metatype, state.metavariant)
    attrs_spec = meta["attributes"]
    warnings = _drop_invalid_vehicle_ware(state)
    ensure_subsystems(state)
    errors.extend(_side_conflicts("cyberware", state.cyberware))
    errors.extend(_side_conflicts("bioware", state.bioware))
    installed_names = {
        "cyberware": _installed_ware_names("cyberware", state.cyberware),
        "bioware": _installed_ware_names("bioware", state.bioware),
    }
    warnings.extend(
        _required_warnings("cyberware", state.cyberware, installed_names, state.metatype, state.metavariant)
    )
    warnings.extend(_required_warnings("bioware", state.bioware, installed_names, state.metatype, state.metavariant))

    talent = resolve_talent_for_method(state.priorities.Talent, state.talent, state.build_method)
    state.talent = talent["name"]
    sources: list[tuple[str, list[dict[str, Any]]]] = [(meta["name"], meta.get("bonus") or [])]
    qualities, free_quality_ids, dropped_qualities = gather_qualities(state, talent)
    for name in dropped_qualities:
        warnings.append(f"{name} は他の資質と両立しないため外しました")
    quality_grade_effects = collect_effects([(q["name"], q.get("bonus") or []) for q in qualities])
    disabled_cyber_grades = set(quality_grade_effects.get("disabled_cyberware_grades") or [])
    disabled_bio_grades = set(quality_grade_effects.get("disabled_bioware_grades") or [])
    warnings.extend(_clamp_ware_grades("cyberware", state.cyberware, disabled_cyber_grades))
    warnings.extend(_clamp_ware_grades("bioware", state.bioware, disabled_bio_grades))
    for q in qualities:
        sources.append((q["name"], q.get("bonus") or []))
    needs_mentor = any(q["id"] == MENTOR_SPIRIT_ID for q in qualities)
    mentor = resolve_mentor(state, talent["name"], needs_mentor, data["skills"])
    warnings.extend(mentor["warnings"])
    errors.extend(mentor["errors"])
    sources.extend(mentor["bonus_sources"])
    vehicle_hosts = set(_vehicle_mod_hosts(state))
    cyber_installed = resolve_ware("cyberware", state.cyberware, attrs_spec)
    bio_installed = resolve_ware("bioware", state.bioware, attrs_spec)
    resolve_quality_sides(qualities, state, cyber_installed, bio_installed, errors)
    _finalize_avail_tree(cyber_installed, grade_kind="cyberware")
    _finalize_avail_tree(bio_installed, grade_kind="bioware")
    _zero_vehicle_hosted_essence(cyber_installed, vehicle_hosts)
    installed = cyber_installed + bio_installed
    hosted_ids = _vehicle_hosted_ware_ids(cyber_installed, vehicle_hosts)
    for item in installed:
        if item.get("id") in hosted_ids:
            continue
        sources.append((item["name"], item.get("bonus") or []))
    ware_attr_bonus = _ware_attribute_bonuses([item for item in installed if item.get("id") not in hosted_ids])
    if not career:
        _check_ware_attribute_cap(ware_attr_bonus, errors)
    effects = collect_effects(sources)
    apply_excon_ware_ban(cyber_installed + bio_installed, bool(effects.get("excon")), errors)
    bind_action_dice_pools(effects, qualities, state)
    bind_spell_spirit_limits(effects, qualities, state, errors)
    bind_spell_category_drain_damage(effects, qualities, state)
    bind_weapon_category_dv(effects, qualities, state, warnings)
    bind_weapon_skill_accuracy(effects, qualities, state, warnings, data["skills"])
    apply_granted_spells(state, effects, qualities, warnings)
    bind_select_powers(
        effects,
        qualities,
        state,
        warnings,
        str((mentor.get("public") or {}).get("name") or ""),
    )
    for category in effects.get("disabled_skill_group_categories") or []:
        for group in _skill_groups_for_category(data["skills"], str(category)):
            if group not in effects["disabled_skill_groups"]:
                effects["disabled_skill_groups"].append(group)
    for q in qualities:
        if not any(node.get("tag") == "skillgroupdisablechoice" for node in (q.get("bonus") or [])):
            continue
        picked = str((state.quality_extras or {}).get(q["id"]) or "").strip()
        if picked and picked not in effects["disabled_skill_groups"]:
            effects["disabled_skill_groups"].append(picked)
    attr_max_bonus, attr_select_warnings = resolve_attribute_selects(state, effects, qualities)
    warnings.extend(attr_select_warnings)
    attr_max_mods = {
        key: int(value) for key, value in (effects.get("attribute_max_mods") or {}).items() if int(value or 0)
    }
    for key, value in attr_max_mods.items():
        attr_max_bonus[key] = int(attr_max_bonus.get(key) or 0) + int(value)
    seeker_targets = effects.get("cyberseeker") or []
    limb_quality = apply_cyberseeker(cyber_installed, seeker_targets, attrs_spec, state.options)
    warnings.extend(redliner_incompat_warnings(installed, seeker_targets))
    if limb_quality:
        for key, value in (limb_quality.get("attribute_bonus") or {}).items():
            if key in {"STR", "AGI"}:
                continue
            effects["attribute_bonus"][key] = int(effects["attribute_bonus"].get(key, 0)) + int(value)
        effects["cm_physical"] += int(limb_quality.get("cm_physical") or 0)

    special_key, talent_start = talent_special(talent)
    if is_karma and special_key:
        talent_start = 1
    enabled = set(effects["enabled_tabs"])
    if special_key:
        enabled.add(special_key)

    ess_start = float(attrs_spec.get("ESS", {}).get("max") or 6) + float(effects.get("essence_max_mod") or 0)
    ess_lost_cyber, ess_lost_bio = apply_ware_essence_multipliers(cyber_installed, bio_installed, effects)
    ess_lost = round(ess_lost_cyber + ess_lost_bio, 4)
    if effects.get("disable_bioware") and bio_installed:
        errors.append("Sensitive System などによりバイオウェアは装着できません")
    ess_penalty = float(effects.get("essence_penalty") or 0)
    ess_penalty_mag_exempt = float(effects.get("essence_penalty_mag_exempt") or 0)
    ess = max(0.0, round(ess_start - ess_lost - ess_penalty, 2))
    mag_relevant_loss = ess_lost + max(0.0, ess_penalty - ess_penalty_mag_exempt)
    mag_penalty = int(math.ceil(mag_relevant_loss - 1e-9)) if mag_relevant_loss > 0 else 0
    cyberadept_res_reduction = 0
    if effects.get("cyberadept_daemon") and talent["name"] in RES_TALENTS:
        cyberadept_res_reduction = _cyberadept_res_penalty_reduction(
            max(0, int(state.submersion_grade or 0)),
            ess_lost_cyber,
            ess_lost_bio,
        )

    initiate_grade = max(0, int(state.initiate_grade or 0)) if talent["name"] in MAG_TALENTS else 0
    submersion_grade = max(0, int(state.submersion_grade or 0)) if talent["name"] in RES_TALENTS else 0
    ratings: dict[str, int] = {}
    for key, spec in attrs_spec.items():
        racial_min = int(spec["min"])
        racial_max = int(spec["max"]) + int(attr_max_bonus.get(key) or 0)
        raw = int(state.attributes.get(key, racial_min))
        if key == "MAG":
            if special_key == "MAG":
                floor = max(talent_start, 1)
                mag_cap = racial_max + initiate_grade
                raw = max(floor, min(mag_cap, raw))
                raw = max(0, raw - mag_penalty)
            else:
                raw = 0
        elif key == "RES":
            if special_key == "RES":
                floor = max(talent_start, 1)
                res_cap = racial_max + submersion_grade
                raw = max(floor, min(res_cap, raw))
                res_penalty = max(0, mag_penalty - cyberadept_res_reduction)
                raw = max(0, raw - res_penalty)
            else:
                raw = 0
        elif key == "ESS":
            raw = int(ess)
        else:
            raw = max(racial_min, min(racial_max, raw))
        ratings[key] = raw

    quality_names = {q["name"] for q in qualities}
    initiation = resolve_initiation(
        state,
        talent["name"],
        int(ratings.get("MAG") or 0),
        quality_names,
        errors,
    )
    apply_free_metamagics(effects, initiation, talent["name"], warnings)
    warnings.extend(initiation["warnings"])
    for source, nodes in initiation["bonus_sources"]:
        apply_bonus_nodes(nodes, effects, source)
    if talent["name"] in MAG_TALENTS:
        enabled.add("initiation")
    submersion = resolve_submersion(
        state,
        talent["name"],
        int(ratings.get("RES") or 0),
        quality_names,
        errors,
    )
    apply_granted_echoes(effects, submersion, qualities, warnings)
    warnings.extend(submersion["warnings"])
    for source, nodes in submersion["bonus_sources"]:
        apply_bonus_nodes(nodes, effects, source)
    if talent["name"] in RES_TALENTS:
        enabled.add("submersion")
    qi = resolve_qi_foci(
        state,
        talent["name"],
        int(ratings.get("MAG") or 0),
        data["skills"],
        list(effects.get("focus_binding") or []),
    )
    warnings.extend(qi["warnings"])
    errors.extend(qi["errors"])
    foci = resolve_foci(
        state,
        talent["name"],
        int(ratings.get("MAG") or 0),
        list(effects.get("focus_binding") or []),
    )
    warnings.extend(foci["warnings"])
    _finalize_avail_tree(list(foci.get("public") or []), rating_key="force")
    for source, nodes in foci["bonus_sources"]:
        apply_bonus_nodes(nodes, effects, source)
    focus_limits = apply_focus_limits(
        int(ratings.get("MAG") or 0),
        list(qi.get("public") or []),
        list(foci.get("public") or []),
        errors,
    )
    apply_tradition_bonuses(effects, _tradition_by_id(state.tradition_id))
    granted_powers = free_powers_from_grants(effects, warnings)
    adept = resolve_adept_powers(
        state,
        talent["name"],
        int(ratings.get("MAG") or 0),
        data["skills"],
        quality_names,
        bool(effects.get("magicians_way")),
        list(mentor.get("free_powers") or []) + list(qi.get("free_powers") or []) + granted_powers,
        int(ratings.get("WIL") or 1),
        int(ratings.get("INT") or 1),
    )
    warnings.extend(adept["warnings"])
    errors.extend(adept["errors"])
    state.mystic_pp = int(adept["mystic_pp"])
    enhancements = resolve_enhancements(state, talent["name"], quality_names, set(adept.get("power_names") or []))
    warnings.extend(enhancements["warnings"])
    effects["enabled_tabs"] = set(effects["enabled_tabs"])
    for source, nodes in adept["bonus_sources"] + enhancements["bonus_sources"]:
        apply_bonus_nodes(nodes, effects, source)
    attr_totals = {
        key: int(ratings.get(key) or 0) + int((effects.get("attribute_bonus") or {}).get(key, 0)) for key in ratings
    }
    gear = resolve_gear(
        state,
        cyber_installed,
        attr_totals,
        special_modification_limit=int(effects.get("special_modification_limit") or 0),
    )
    warnings.extend(gear["warnings"])
    errors.extend(gear.get("errors") or [])
    apply_lifestyle_cost_mod(gear, int(effects.get("lifestyle_cost") or 0))
    apply_erased_lifestyle_cap(gear, bool(effects.get("erased")), warnings)
    apply_reach_bonus(gear.get("weapons"), int(effects.get("reach") or 0))
    apply_weapon_category_dv(gear.get("weapons"), effects)
    apply_weapon_skill_accuracy(gear.get("weapons"), effects)
    bmp_category = ""
    bmp_contact_id = ""
    bmp_active = False
    if effects.get("black_market_discount"):
        for q in qualities:
            if not any(node.get("tag") == "blackmarketdiscount" for node in (q.get("bonus") or [])):
                continue
            bmp_category = str((state.quality_extras or {}).get(q["id"]) or "").strip()
            bmp_contact_id = str((state.quality_extras or {}).get(quality_contact_extra_key(q["id"])) or "").strip()
            contact_ids = {str(getattr(c, "id", "") or "") for c in (state.contacts or [])}
            if not bmp_category:
                warnings.append("Black Market Pipeline の商品カテゴリを選んでください")
            if not bmp_contact_id:
                warnings.append("Black Market Pipeline のコンタクトを選んでください")
            elif bmp_contact_id not in contact_ids:
                warnings.append("Black Market Pipeline のコンタクトが見つかりません")
                bmp_contact_id = ""
            bmp_active = bool(bmp_category and bmp_contact_id)
            break
    apply_purchase_discounts(
        gear,
        cyber_installed,
        bio_installed,
        effects,
        black_market_category=bmp_category if bmp_active else "",
    )
    if bmp_active:
        apply_black_market_avail(
            gear,
            cyber_installed,
            bio_installed,
            black_market_category=bmp_category,
        )
    apply_overclocker(gear, bool(effects.get("overclocker")))
    trust_level = int(effects.get("trustfund") or 0)
    if trust_level:
        sinner_ok = any(
            str(q.get("name") or "").startswith("SINner (National)")
            or str(q.get("name") or "").startswith("SINner (Corporate)")
            for q in qualities
        )
        if not sinner_ok:
            warnings.append("Trust Fund には SINner（National または Corporate）が必要です")
    errors.extend(_attach_ware_to_vehicle_mods(gear.get("vehicle_mods") or [], cyber_installed))
    for source, nodes in gear["bonus_sources"]:
        apply_bonus_nodes(nodes, effects, source)
    active_drugs = apply_active_drugs(state, attr_totals, effects)
    attach_weapon_focus_dice(state, list(foci.get("public") or []), list(gear.get("weapons") or []), warnings)
    if talent["name"] in ADEPT_TALENTS:
        enabled.add("adept")
        effects["enabled_tabs"].add("adept")
    enabled.update(effects["enabled_tabs"])

    if talent["name"] == "Adept":
        power_pool = float(ratings["MAG"]) + float(effects.get("adept_power_points") or 0)
    elif talent["name"] == "Mystic Adept":
        power_pool = float(state.mystic_pp) + float(effects.get("adept_power_points") or 0)
    else:
        power_pool = 0.0
    power_spent = float(adept["spent"])
    if power_spent > power_pool + 1e-9:
        errors.append(f"パワー点が不足しています（使用 {power_spent:g} / 上限 {power_pool:g}）")

    bonus = effects["attribute_bonus"]
    total = {k: ratings[k] + int(bonus.get(k, 0)) for k in ratings}
    total["ESS"] = ess
    limb_replace = limb_attribute_replace(cyber_installed, int(total["STR"]), int(total["AGI"]), attrs_spec)
    if limb_replace:
        total["STR"] = int(limb_replace["str"])
        total["AGI"] = int(limb_replace["agi"])

    owned_magic_names = set(initiation.get("art_names") or set()) | set(initiation.get("metamagic_names") or set())
    magic = resolve_spells(state, talent, int(total.get("MAG") or 0), total, owned_magic_names, effects)
    warnings.extend(magic["warnings"])
    spell_focus = {mod["name"]: int(mod.get("bonus") or 0) for mod in (effects.get("spell_category_mods") or [])}
    for item in magic.get("public") or []:
        bonus = int(spell_focus.get(item.get("category") or "", 0))
        if bonus:
            item["focus_bonus"] = bonus
    bind_extra_spirits(effects, qualities, state, warnings, data["skills"])
    spirits = resolve_spirits(
        state,
        talent["name"],
        int(total.get("MAG") or 0),
        _tradition_by_id(state.tradition_id),
        limit_spirits=list(effects.get("limit_spirit_categories") or []),
        extra_spirits=list(effects.get("extra_spirits") or []),
    )
    warnings.extend(spirits["warnings"])
    if talent["name"] in SPELL_TALENTS or (effects.get("allow_spell_ranges") or []):
        enabled.add("spells")
    if talent["name"] in SPIRIT_TALENTS:
        enabled.add("spirits")
    resonance = resolve_complex_forms(
        state,
        talent["name"],
        int(total.get("RES") or 0),
        total,
        quality_names,
        effects,
    )
    warnings.extend(resonance["warnings"])
    techno_sprites = resolve_sprites(
        state,
        talent["name"],
        int(total.get("RES") or 0),
        resonance.get("stream"),
    )
    warnings.extend(techno_sprites["warnings"])
    errors.extend(techno_sprites["errors"])
    if talent["name"] in COMPLEX_FORM_TALENTS:
        enabled.add("complexforms")
    if talent["name"] in SPRITE_TALENTS:
        enabled.add("sprites")
    if talent["name"] in FOCUS_TALENTS:
        enabled.add("foci")
    for item in adept.get("public") or []:
        extra = item.get("extra")
        if item.get("select") != "spell" or not extra:
            continue
        force = (item.get("spell") or {}).get("force")
        item["spell"] = spell_cast_info(
            extra,
            force,
            int(total.get("MAG") or 0),
            int(magic["resist"]),
            str(magic["resist_attrs"]),
            effects=effects,
        )

    attr_row = priority_value("Attributes", state.priorities.Attributes)
    skill_row = priority_value("Skills", state.priorities.Skills)
    res_row = priority_value("Resources", state.priorities.Resources)
    her_row = priority_value("Heritage", state.priorities.Heritage)

    special_from_meta = 0
    extra_karma = 0
    for entry in her_row.get("metatypes") or []:
        if entry["name"] == state.metatype:
            special_from_meta = entry.get("special", 0)
            extra_karma += entry.get("karma", 0)
            if state.metavariant:
                for v in entry.get("variants") or []:
                    if v["name"] == state.metavariant:
                        special_from_meta = v.get("special", special_from_meta)
                        extra_karma += v.get("karma", 0)
            break

    spent_physical = 0
    for key in PHYSICAL_ATTRS:
        spent_physical += max(0, ratings[key] - int(attrs_spec[key]["min"]))
    spent_special = max(0, ratings["EDG"] - int(attrs_spec["EDG"]["min"]))
    if special_key == "MAG":
        spent_special += max(0, ratings["MAG"] - talent_start)
    elif special_key == "RES":
        spent_special += max(0, ratings["RES"] - talent_start)

    nuyen_karma_max = KARMA_NUYEN_MAX
    if is_karma:
        attr_points = 0
        skill_points = 0
        group_points = 0
        special_from_meta = 0
        nuyen_karma_max = KARMA_NUYEN_MAX
        state.karma_nuyen = max(0, min(nuyen_karma_max, int(state.karma_nuyen or 0)))
        nuyen_pool = int(state.karma_nuyen) * KARMA_TO_NUYEN
        metatype_karma_cost = max(0, int(meta.get("karma") or 0))
        heritage_karma_cost = 0
    else:
        attr_points = int(attr_row.get("attribute_points") or 0)
        skill_points = int(skill_row.get("skill_points") or 0)
        group_points = int(skill_row.get("skill_group_points") or 0)
        nuyen_pool = int(res_row.get("nuyen") or 0)
        metatype_karma_cost = 0
        # Priority chargen: metatypes.xml <karma> is for Karma/Sum-to-Ten, not Priority.
        # Heritage table <karma> is an extra cost for some metavariants / rare races.
        heritage_karma_cost = extra_karma
        # Leftover chargen karma may buy nuyen (SR5 p.94); Born Rich raises the cap.
        nuyen_karma_max = max(0, PRIORITY_KARMA_NUYEN_BASE + int(effects.get("nuyen_max_bp") or 0))
        state.karma_nuyen = max(0, min(nuyen_karma_max, int(state.karma_nuyen or 0)))
        nuyen_pool += int(state.karma_nuyen) * KARMA_TO_NUYEN

    nuyen_pool += int(state.nuyen_earned or 0)
    nuyen_pool += int(effects.get("nuyen_amt") or 0)
    nuyen_spent = (
        sum(int(item["nuyen"]) for item in installed)
        + int(qi.get("nuyen") or 0)
        + int(foci.get("nuyen") or 0)
        + int(spirits.get("nuyen") or 0)
        + int(gear.get("nuyen") or 0)
    )
    nuyen = nuyen_pool - nuyen_spent

    skill_spent = 0
    group_spent = 0
    skill_totals: dict[str, int] = {}
    exotic_names = {s["name"] for s in data["skills"]["skills"] if s.get("exotic")}
    if exotic_names:
        state.skills = {name: rating for name, rating in state.skills.items() if name not in exotic_names}
    for group, rating in state.skill_groups.items():
        rating = max(0, min(skill_group_cap, int(rating)))
        state.skill_groups[group] = rating
        group_spent += rating
        for s in data["skills"]["skills"]:
            if s.get("skillgroup") == group and not s.get("exotic"):
                skill_totals[s["name"]] = max(skill_totals.get(s["name"], 0), rating)
    tentative = dict(skill_totals)
    for name, rating in state.skills.items():
        tentative[name] = max(tentative.get(name, 0), max(0, min(skill_rating_cap + 1, int(rating))))
    skill_picks = resolve_skill_picks(state, data["skills"], tentative)
    warnings.extend(skill_picks["warnings"])
    skill_cat_map = _skill_category_map(data["skills"])
    point_mults = dict(effects.get("skill_category_point_cost_mult") or {})
    for name, rating in state.skills.items():
        cap = skill_rating_cap + int(skill_picks["skill_max_bonus"].get(name, 0))
        rating = max(0, min(cap, int(rating)))
        state.skills[name] = rating
        base = skill_totals.get(name, 0)
        extra = max(0, rating - base)
        cat = skill_cat_map.get(name, "")
        skill_spent += _point_cost(extra, int(point_mults.get(cat, 100)))
        skill_totals[name] = max(base, rating)
    exotic = resolve_exotic_skills(
        state,
        data["skills"],
        skill_picks["skill_max_bonus"],
        rating_cap=skill_rating_cap,
    )
    warnings.extend(exotic["warnings"])
    skill_spent += int(exotic["spent"])
    skill_totals.update(exotic["totals"])
    knowledge = resolve_knowledge(
        state,
        data["skills"],
        total,
        rating_cap=skill_rating_cap,
        native_limit=1 + int(effects.get("native_language_limit_bonus") or 0),
    )
    warnings.extend(knowledge["warnings"])
    know_spent = knowledge_points_spent(knowledge["public"], point_mults)
    know_max = int(knowledge["max"]) + int(effects.get("knowledge_skill_points") or 0)
    bought_knowledge = dict(state.knowledge_skills)
    for name in state.native_languages:
        bought_knowledge[name] = max(int(bought_knowledge.get(name) or 0), 1)
    skill_mods = resolve_skill_mods(data["skills"], effects, bought_knowledge, state.knowledge_categories)
    for name, bonus in skill_picks["skill_bonus"].items():
        skill_mods["skill_bonus"][name] = int(skill_mods["skill_bonus"].get(name, 0)) + int(bonus)
    for name, notes in skill_picks["skill_bonus_notes"].items():
        existing = skill_mods["skill_bonus_notes"].setdefault(name, [])
        for note in notes:
            if note not in existing:
                existing.append(note)
    _copy_exotic_skill_bonuses(skill_mods, exotic["public"])
    for name in effects.get("disabled_skills") or []:
        if int(skill_totals.get(name) or 0) > 0 or int(state.skills.get(name) or 0) > 0:
            warnings.append(f"{name} は無効化されている技能です")
    for group in effects.get("disabled_skill_groups") or []:
        if int(state.skill_groups.get(group) or 0) > 0:
            warnings.append(f"技能グループ {group} は無効化されています")
    blocked_defaults = list(effects.get("blocked_default_categories") or [])
    if blocked_defaults:
        warnings.append("デフォルト不可: " + "、".join(blocked_defaults))
    skillsofts = resolve_skillsofts(list(gear.get("gear") or []), data["skills"], effects, warnings)
    _attach_skillsoft_knowledge(knowledge["public"], skillsofts["knowledge"], data["skills"])
    expertises, free_expertise_skills = apply_select_expertise(
        state,
        effects,
        qualities,
        skill_totals,
        skillsofts["active"],
        warnings,
    )
    specs = resolve_specializations(
        state,
        data["skills"],
        skill_totals,
        skillsofts["active"],
        skillsofts["knowledge"],
        free_expertise_skills=free_expertise_skills,
    )
    warnings.extend(specs["warnings"])
    # Keep expertise picks even if resolve dropped a conflicting row.
    for row in expertises:
        skill_name = str(row.get("skill") or "")
        spec_name = str(row.get("spec") or "")
        if skill_name and spec_name:
            specs["specs"][skill_name] = spec_name
            state.skill_specializations[skill_name] = spec_name
    spec_active = int(specs["active_spent"])
    spec_knowledge = int(specs["knowledge_spent"])
    if is_karma:
        spec_karma = (spec_active + spec_knowledge) * KARMA_SPECIALIZATION
    elif career:
        # Priority career: new specs cost karma (baseline settles chargen specs).
        spec_karma = 0
    else:
        skill_spent += spec_active
        know_spent += spec_knowledge
        spec_karma = 0
    _attach_specializations(knowledge["public"], specs["specs"])
    effective_skills = _merge_skill_ratings(skill_totals, skillsofts["active"])
    effective_knowledge = _merge_skill_ratings(dict(state.knowledge_skills or {}), skillsofts["knowledge"])

    karma_from_q = sum(
        q["karma"] for q in qualities if not q.get("onlyprioritygiven") and q["id"] not in free_quality_ids
    )
    mystic_karma = int(state.mystic_pp) * MYSTIC_PP_KARMA
    extra_adept_karma = int(enhancements.get("karma") or 0) + int(qi.get("karma") or 0) + int(foci.get("karma") or 0)
    spell_karma = int(magic.get("karma") or 0) + int(resonance.get("karma") or 0)
    career_adv_karma = 0
    career_adv_lines: list[dict[str, Any]] = []
    if is_karma:
        attr_karma = attribute_karma_cost(ratings, attrs_spec, special_key)
        skill_buy_karma = skill_karma_cost(state.skill_groups, skill_totals, data["skills"], group_cap=skill_group_cap)
        know_cats = {
            str(row.get("name") or ""): str(row.get("category") or "")
            for row in (knowledge.get("public") or [])
            if row.get("name")
        }
        knowledge_karma = knowledge_excess_karma(
            dict(state.knowledge_skills or {}),
            know_max,
            categories=know_cats,
            karma_mults=_active_karma_mults(effects.get("skill_category_karma_cost_mult"), career=False),
        )
        nuyen_karma = int(state.karma_nuyen or 0)
        karma_pool = KARMA_CHARGEN_POOL + int(state.karma_earned or 0)
        karma_spent = (
            karma_from_q
            + metatype_karma_cost
            + mystic_karma
            + extra_adept_karma
            + spell_karma
            + attr_karma
            + skill_buy_karma
            + knowledge_karma
            + spec_karma
            + nuyen_karma
        )
    else:
        attr_karma = 0
        skill_buy_karma = 0
        knowledge_karma = 0
        nuyen_karma = 0
        karma_pool = 25 + int(state.karma_earned or 0)
        karma_spent = (
            karma_from_q
            + heritage_karma_cost
            + mystic_karma
            + extra_adept_karma
            + spell_karma
            + int(state.karma_nuyen or 0)
        )
        if career:
            baseline = state.career_baseline
            if baseline is None:
                baseline = snapshot_career_baseline(state)
                state.career_baseline = baseline
            career_adv_karma, career_adv_lines = career_raise_karma(
                state, baseline, skill_totals, data["skills"], effects=effects
            )
            karma_spent += career_adv_karma

    bod = total["BOD"]
    agi = total["AGI"]
    rea = total["REA"]
    stre = total["STR"]
    wil = total["WIL"]
    logi = total["LOG"]
    intuition = total["INT"]
    cha = total["CHA"]
    warnings.extend(sync_quality_contacts(state, effects, qualities))
    contacts = resolve_contacts(
        state,
        int(cha or 0),
        career=career,
        friends_in_high_places=bool(effects.get("friends_in_high_places")),
        black_market_contact_id=bmp_contact_id if bmp_active else "",
        contact_karma_adj=int(effects.get("contact_karma_adj") or 0),
        contact_karma_min=int(effects.get("contact_karma_min") or 0),
        excon=bool(effects.get("excon")),
    )
    warnings.extend(contacts["warnings"])
    karma_spent += int(contacts.get("karma") or 0)

    martial_ctx = quality_requirement_context(
        state,
        talent,
        qualities,
        meta,
        ess,
        ess_lost,
        effective_skills,
        set(adept.get("power_names") or []),
        {str(item.get("name") or "") for item in (magic.get("public") or []) if item.get("name")},
        str(((magic.get("tradition") if isinstance(magic.get("tradition"), dict) else {}) or {}).get("name") or ""),
        {item["name"] for item in cyber_installed},
        {item["name"] for item in bio_installed},
        effective_knowledge,
    )
    martial_ctx = {
        **martial_ctx,
        "qualities": set(martial_ctx.get("qualities") or []) | {talent["name"]},
    }
    warnings.extend(sync_quality_martial_arts(state, effects, qualities))
    martial = resolve_martial_arts(state, martial_ctx, errors, career=career)
    warnings.extend(martial["warnings"])
    for source, nodes in martial.get("bonus_sources") or []:
        apply_bonus_nodes(nodes, effects, source)
    apply_unarmed_bonuses(
        gear.get("weapons"),
        int(effects.get("unarmed_reach") or 0),
        int(effects.get("unarmed_ap") or 0),
    )
    karma_spent += int(martial.get("karma") or 0)
    karma_spent += int(initiation.get("karma") or 0)
    karma_spent += int(submersion.get("karma") or 0)
    karma_left = karma_pool - karma_spent

    karma_spend_lines: list[dict[str, Any]] = list(career_adv_lines)
    for label, amount in (
        ("資質", karma_from_q),
        ("メタ", metatype_karma_cost if is_karma else heritage_karma_cost),
        ("能力値（カルマ作成）", attr_karma if is_karma else 0),
        ("技能（カルマ作成）", skill_buy_karma if is_karma else 0),
        ("知識（カルマ作成）", knowledge_karma if is_karma else 0),
        ("専門化", spec_karma),
        ("ニューエン交換", int(state.karma_nuyen or 0)),
        ("ミスティックPP", mystic_karma),
        ("アデプト／気／フォーカス", extra_adept_karma),
        ("術式／複合体", spell_karma),
        ("コンタクト超過", int(contacts.get("karma") or 0)),
        ("武道", int(martial.get("karma") or 0)),
        ("イニシエーション", int(initiation.get("karma") or 0)),
        ("サブマージョン", int(submersion.get("karma") or 0)),
    ):
        if amount:
            karma_spend_lines.append({"kind": "other", "label": label, "amount": int(amount)})
    nuyen_spend_lines = nuyen_spend_breakdown(
        cyber_installed,
        bio_installed,
        gear,
        qi_nuyen=int(qi.get("nuyen") or 0),
        foci_nuyen=int(foci.get("nuyen") or 0),
        spirits_nuyen=int(spirits.get("nuyen") or 0),
    )

    quality_notoriety = int(effects.get("notoriety") or 0)
    notoriety_total = quality_notoriety + int(state.notoriety_bonus or 0)
    street_cred_total = int(state.street_cred or 0)
    quality_pa = int(effects.get("public_awareness") or 0)
    public_awareness_total = max(0, (street_cred_total + max(0, notoriety_total)) // 3 + quality_pa)
    if effects.get("erased") and public_awareness_total >= 1:
        public_awareness_total = 1

    physical_limit = _ceil_div((bod * 2 + agi + rea + stre) / 3) + int(effects.get("limit_physical") or 0)
    mental_limit = _ceil_div((logi * 2 + intuition + wil) / 3) + int(effects.get("limit_mental") or 0)
    social_limit = _ceil_div((cha * 2 + wil + ess) / 3) + int(effects.get("limit_social") or 0)
    cm_phys = 8 + _ceil_div(bod / 2) + effects["cm_physical"]
    cm_stun = 8 + _ceil_div(wil / 2) + effects["cm_stun"]
    initiative = rea + intuition + effects["initiative"]
    initiative_dice = 1 + int(effects.get("initiative_dice") or 0)
    warnings.extend(
        attach_spirit_tests(
            list(spirits.get("public") or []),
            int(total.get("MAG") or 0),
            effective_skills,
            skill_mods["skill_bonus"],
            total,
            data["skills"],
        )
    )
    warnings.extend(
        attach_focus_tests(
            list(foci.get("public") or []),
            int(total.get("MAG") or 0),
            effective_skills,
            skill_mods["skill_bonus"],
            total,
            data["skills"],
            mental_limit,
        )
    )
    warnings.extend(
        attach_complex_form_tests(
            list(resonance.get("public") or []),
            int(total.get("RES") or 0),
            effective_skills,
            skill_mods["skill_bonus"],
            total,
            data["skills"],
        )
    )
    warnings.extend(
        attach_sprite_tests(
            list(techno_sprites.get("public") or []),
            int(total.get("RES") or 0),
            effective_skills,
            skill_mods["skill_bonus"],
            total,
            data["skills"],
        )
    )

    movement = resolve_movement(meta, effects)

    tradition_info = magic.get("tradition") if isinstance(magic.get("tradition"), dict) else {}
    quality_report: dict[str, Any] = {}
    negative_quality_karma = apply_quality_rules(
        state,
        qualities,
        free_quality_ids,
        quality_requirement_context(
            state,
            talent,
            qualities,
            meta,
            ess,
            ess_lost,
            effective_skills,
            set(adept.get("power_names") or []),
            {str(item.get("name") or "") for item in (magic.get("public") or []) if item.get("name")},
            str((tradition_info or {}).get("name") or ""),
            {item["name"] for item in cyber_installed},
            {item["name"] for item in bio_installed},
            effective_knowledge,
        ),
        errors,
        career=career,
        report=quality_report,
    )

    if not career:
        at_six = [n for n, r in skill_totals.items() if r >= 6]
        if len(at_six) > 1:
            errors.append("作成時にレーティング6の技能は1つまでです")
        # SR5 p.65: no more than one attribute at its natural maximum at
        # character creation (Edge / unused special attributes don't count).
        # Applies to every build method, not just Karma.
        at_natural_max = []
        for key, spec in attrs_spec.items():
            if key in {"ESS", "EDG", "MAG", "RES"} and key != special_key:
                continue
            if key not in ratings:
                continue
            racial_max = int(spec.get("max") or 0) + int(attr_max_bonus.get(key) or 0)
            if key == "MAG" and special_key == "MAG":
                racial_max = racial_max + int(initiation.get("mag_max_bonus") or 0)
            if key == "RES" and special_key == "RES":
                racial_max = racial_max + int(submersion.get("res_max_bonus") or 0)
            if racial_max > 0 and int(ratings.get(key) or 0) >= racial_max:
                at_natural_max.append(key)
        if len(at_natural_max) > 1:
            errors.append("作成時に自然上限の能力値は1つまでです")
        if not is_karma:
            if spent_physical > attr_points:
                errors.append(f"能力値点が不足しています（使用 {spent_physical} / 上限 {attr_points}）")
            if spent_special > special_from_meta:
                errors.append(f"特殊能力値点が不足しています（使用 {spent_special} / 上限 {special_from_meta}）")
            if skill_spent > skill_points:
                errors.append(f"技能点が不足しています（使用 {skill_spent} / 上限 {skill_points}）")
            if group_spent > group_points:
                errors.append(f"技能グループ点が不足しています（使用 {group_spent} / 上限 {group_points}）")
            if know_spent > know_max:
                errors.append(f"知識技能点が不足しています（使用 {know_spent} / 上限 {know_max}）")
    if karma_left < 0:
        errors.append(f"カルマが不足しています（残り {karma_left}）")
    if nuyen < 0:
        errors.append(f"ニューエンが不足しています（残り {nuyen}¥）")
    # SR5 p.98: at Standard power level only 5,000¥ of unspent resources
    # carry over into play (Street 200¥ / Prime 20,000¥). Surface it as a
    # chargen notice rather than silently deleting nuyen, matching Chummer.
    if not career:
        chargen_leftover = nuyen - int(state.nuyen_earned or 0)
        if chargen_leftover > NUYEN_CHARGEN_KEEP_MAX:
            lost = chargen_leftover - NUYEN_CHARGEN_KEEP_MAX
            warnings.append(
                f"未使用ニューエン {chargen_leftover:,}¥：Standard レベルでは "
                f"{NUYEN_CHARGEN_KEEP_MAX:,}¥ までしか持ち越せません（超過分 {lost:,}¥ は原則失われます）"
            )
    if ess <= 0:
        errors.append("エッセンスが0以下です")
    for item in installed:
        cap_max = float(item.get("capacity_max") or 0)
        if cap_max <= 0:
            continue
        used = float(item.get("capacity_used") or 0)
        if used > cap_max + 1e-9:
            errors.append(f"{item['name']} の容量超過（{used:g}/{cap_max:g}）")

    if not is_karma:
        allowed = {e["name"] for e in heritage_options(state.priorities.Heritage)}
        if allowed and state.metatype not in allowed:
            errors.append(f"{state.metatype} はこの優先度のメタに含まれません")
    if not career:
        _check_avail_limit(
            _avail_entries(
                cyber_installed,
                bio_installed,
                gear.get("armor_items"),
                gear.get("armor_mods"),
                gear.get("weapons"),
                gear.get("weapon_accessories"),
                gear.get("commlinks"),
                gear.get("cyberdecks"),
                gear.get("rccs"),
                gear.get("optics"),
                gear.get("programs"),
                gear.get("apps"),
                gear.get("sensors"),
                gear.get("drones"),
                gear.get("vehicles"),
                gear.get("vehicle_mods"),
                gear.get("weapon_mounts"),
                gear.get("gear"),
                gear.get("lifestyles"),
                foci.get("public"),
            ),
            effects,
            errors,
        )
        _check_device_rating_limit(
            _device_rating_entries(
                cyber_installed,
                bio_installed,
                gear.get("commlinks"),
                gear.get("cyberdecks"),
                gear.get("rccs"),
                gear.get("optics"),
                gear.get("sensors"),
                gear.get("gear"),
            ),
            errors,
        )

    state.attributes = ratings
    sum_spent = sum_to_ten_spent(state.priorities)
    state.derived = {
        "errors": errors,
        "warnings": warnings,
        "build_method": state.build_method,
        "sum_to_ten": {
            "used": sum_spent,
            "max": SUM_TO_TEN_BUDGET,
            "costs": dict(SUM_TO_TEN_COST),
            "unique": priorities_are_unique(state.priorities),
        },
        "karma_chargen": {
            "enabled": is_karma,
            "pool": karma_pool if is_karma else 0,
            "nuyen_karma": int(state.karma_nuyen or 0),
            "nuyen_karma_max": int(nuyen_karma_max),
            "nuyen_per_karma": KARMA_TO_NUYEN,
            "metatype": metatype_karma_cost if is_karma else 0,
            "attributes": attr_karma if is_karma else 0,
            "skills": skill_buy_karma if is_karma else 0,
            "knowledge": knowledge_karma if is_karma else 0,
            "specializations": spec_karma if is_karma else 0,
            "qualities": karma_from_q,
            "other": mystic_karma
            + extra_adept_karma
            + spell_karma
            + int(contacts.get("karma") or 0)
            + int(martial.get("karma") or 0)
            + int(initiation.get("karma") or 0)
            + int(submersion.get("karma") or 0),
        },
        "totals": total,
        "limits": {
            "physical": physical_limit,
            "mental": mental_limit,
            "social": social_limit,
        },
        "limit_modifiers": compact_limit_modifiers(effects),
        "condition_monitor": {"physical": cm_phys, "stun": cm_stun},
        "initiative": {"value": initiative, "dice": initiative_dice},
        "movement": movement,
        "essence": ess,
        "essence_lost": ess_lost,
        "essence_lost_cyber": ess_lost_cyber,
        "essence_lost_bio": ess_lost_bio,
        "armor": int(effects["armor"]) + int(gear.get("armor") or 0),
        "special_armor": special_armor_totals(effects),
        "worn_armor": gear.get("worn_name") or "",
        "armor_items": gear.get("armor_items") or [],
        "armor_mods": gear.get("armor_mods") or [],
        "weapons": gear.get("weapons") or [],
        "weapon_accessories": gear.get("weapon_accessories") or [],
        "recoil": gear.get("recoil") or {"str": 0, "str_rc": 0, "free": 1},
        "active_drugs": active_drugs,
        "commlinks": gear.get("commlinks") or [],
        "cyberdecks": gear.get("cyberdecks") or [],
        "rccs": gear.get("rccs") or [],
        "optics": gear.get("optics") or [],
        "programs": gear.get("programs") or [],
        "apps": gear.get("apps") or [],
        "sensors": gear.get("sensors") or [],
        "drones": gear.get("drones") or [],
        "vehicles": gear.get("vehicles") or [],
        "vehicle_mods": gear.get("vehicle_mods") or [],
        "weapon_mounts": gear.get("weapon_mounts") or [],
        "gear": gear.get("gear") or [],
        "lifestyles": gear.get("lifestyles") or [],
        "commlink": gear.get("commlink"),
        "cyberdeck": gear.get("cyberdeck"),
        "rcc": gear.get("rcc"),
        "lifestyle": gear.get("lifestyle"),
        "nuyen": nuyen,
        "nuyen_spent": nuyen_spent,
        "nuyen_pool": nuyen_pool,
        "nuyen_earned": int(state.nuyen_earned or 0),
        "karma_earned": int(state.karma_earned or 0),
        "career": career,
        "career_advancement_karma": int(career_adv_karma),
        "career_advancement_lines": career_adv_lines,
        "nuyen_amt": int(effects.get("nuyen_amt") or 0),
        "nuyen_karma_max": int(nuyen_karma_max),
        "trustfund": int(effects.get("trustfund") or 0),
        "trustfund_label": TRUST_FUND_STIPEND.get(int(effects.get("trustfund") or 0), ""),
        "ambidextrous": bool(effects.get("ambidextrous")),
        "overclocker": bool(effects.get("overclocker")),
        "special_modification_limit": {
            "used": int(gear.get("special_modification_used") or 0),
            "max": int(effects.get("special_modification_limit") or 0),
        },
        "friends_in_high_places": bool(effects.get("friends_in_high_places")),
        "made_man": bool(effects.get("made_man")),
        "black_market_discount": bool(effects.get("black_market_discount")),
        "black_market_category": bmp_category if bmp_active else "",
        "black_market_contact_id": bmp_contact_id if bmp_active else "",
        "black_market_avail_bonus": BLACK_MARKET_AVAIL_BONUS if bmp_active else 0,
        "dealer_connection_categories": list(effects.get("dealer_connection_categories") or []),
        "cyberware_ess_multiplier": int(effects.get("cyberware_ess_multiplier") or 100),
        "bioware_ess_multiplier": int(effects.get("bioware_ess_multiplier") or 100),
        "skill_rating_max": skill_rating_cap,
        "skill_group_max": skill_group_cap,
        "avail_limit": None if career else CHARGEN_AVAIL_MAX,
        "device_rating_limit": None if career else CHARGEN_DEVICE_RATING_MAX,
        "ware_attr_limit": None if career else CHARGEN_WARE_ATTR_BONUS_MAX,
        "ware_attr_bonus": ware_attr_bonus,
        "karma": {
            "pool": karma_pool,
            "spent": karma_spent,
            "remaining": karma_left,
            "negative": {
                "used": negative_quality_karma,
                "max": None if career else NEGATIVE_QUALITY_KARMA_CAP,
            },
        },
        "power_points": {"used": power_spent, "max": power_pool},
        "metagenic": quality_report.get("metagenic"),
        "adept_powers": adept["public"],
        "mystic_pp": state.mystic_pp,
        "way_discount": {"used": adept.get("discount_used") or 0, "max": adept.get("discount_max") or 0},
        "mentor": mentor.get("public"),
        "needs_mentor": needs_mentor,
        "qi_foci": qi.get("public") or [],
        "foci": foci.get("public") or [],
        "focus_limits": focus_limits,
        "spirits": spirits.get("public") or [],
        "enhancements": enhancements.get("public") or [],
        "damage_resistance": int(effects.get("damage_resistance") or 0),
        "unarmed_dv": int(effects.get("unarmed_dv") or 0),
        "unarmed_physical": bool(effects.get("unarmed_physical")),
        "unlock_skills": list(effects.get("unlock_skills") or []),
        "spells": magic.get("public") or [],
        "spell_points": {
            "used": magic.get("used") or 0,
            "free": magic.get("free_max") or 0,
            "paid": magic.get("paid") or 0,
            "karma": magic.get("karma") or 0,
            "spell_karma": spell_karma_cost("spell", effects),
        },
        "tradition": magic.get("tradition"),
        "drain_resist": {"pool": magic.get("resist") or 0, "attrs": magic.get("resist_attrs") or "WIL+INT"},
        "complex_forms": resonance.get("public") or [],
        "complex_form_points": {
            "used": resonance.get("used") or 0,
            "free": resonance.get("free_max") or 0,
            "paid": resonance.get("paid") or 0,
        },
        "sprites": techno_sprites.get("public") or [],
        "stream": resonance.get("stream"),
        "fade_resist": {"pool": resonance.get("resist") or 0, "attrs": resonance.get("resist_attrs") or "WIL+RES"},
        "living_persona": (
            living_persona(
                total,
                int(total.get("RES") or 0),
                effects.get("living_persona") if isinstance(effects.get("living_persona"), dict) else None,
                int(effects.get("matrix_initiative_dice") or 0),
            )
            if talent["name"] in RES_TALENTS
            else None
        ),
        "points": {
            "attributes": {"used": spent_physical, "max": attr_points},
            "special": {"used": spent_special, "max": special_from_meta},
            "skills": {"used": skill_spent, "max": skill_points},
            "skill_groups": {"used": group_spent, "max": group_points},
            "knowledge": {"used": know_spent, "max": know_max},
            "contacts": {"used": contacts.get("used") or 0, "max": contacts.get("free") or 0},
        },
        "knowledge_skills": knowledge["public"],
        "contacts": contacts.get("public") or [],
        "contact_points": {
            "used": contacts.get("used") or 0,
            "free": contacts.get("free") or 0,
            "paid": contacts.get("paid") or 0,
            "karma": int(contacts.get("karma") or 0),
            "karma_per_point": int(contacts.get("karma_per_point", 1)),
        },
        "martial_arts": martial.get("public") or [],
        "martial_art_points": {
            "styles": martial.get("style_count") or 0,
            "style_max": martial.get("style_max") or MARTIAL_ART_CHARGEN_STYLE_MAX,
            "techniques": martial.get("technique_count") or 0,
            "technique_max": martial.get("technique_max") or MARTIAL_ART_CHARGEN_TECHNIQUE_MAX,
            "karma": martial.get("karma") or 0,
        },
        "martial_spec_options": martial.get("spec_extras") or {},
        "unarmed_reach": int(effects.get("unarmed_reach") or 0) + int(effects.get("reach") or 0),
        "unarmed_ap": int(effects.get("unarmed_ap") or 0),
        "reach": int(effects.get("reach") or 0),
        "lifestyle_cost_mod": int(effects.get("lifestyle_cost") or 0),
        "street_cred": street_cred_total,
        "notoriety": notoriety_total,
        "notoriety_quality": quality_notoriety,
        "notoriety_bonus": int(state.notoriety_bonus or 0),
        "fame": int(effects.get("fame") or 0),
        "public_awareness": public_awareness_total,
        "erased": bool(effects.get("erased")),
        "excon": bool(effects.get("excon")),
        "reward_log": [
            {"id": row.id, "label": row.label, "karma": int(row.karma or 0), "nuyen": int(row.nuyen or 0)}
            for row in (state.reward_log or [])
        ],
        "karma_spend_breakdown": karma_spend_lines,
        "nuyen_spend_breakdown": nuyen_spend_lines,
        "fatigue_resist": int(effects.get("fatigue_resist") or 0),
        "spell_resistance": int(effects.get("spell_resistance") or 0),
        "spell_defense": spell_defense_pools(effects),
        "spell_dice_pool": list(effects.get("spell_dice_pool") or []),
        "action_dice_pools": list(effects.get("action_dice_pools") or []),
        "test_mods": dict(effects.get("test_mods") or {}),
        "cm_recovery": {
            "physical": int(effects.get("cm_recovery_physical") or 0)
            + (int(ess) if effects.get("cm_recovery_physical_add_ess") else 0),
            "stun": int(effects.get("cm_recovery_stun") or 0)
            + (int(ess) if effects.get("cm_recovery_stun_add_ess") else 0),
        },
        "essence_penalty": round(float(effects.get("essence_penalty") or 0), 4),
        "attribute_max_bonus": dict(attr_max_bonus),
        "disabled_skills": list(effects.get("disabled_skills") or []),
        "disabled_skill_groups": list(effects.get("disabled_skill_groups") or []),
        "blocked_default_categories": list(effects.get("blocked_default_categories") or []),
        "native_language_limit": int(knowledge.get("native_limit") or 1),
        "prototype_transhuman_ess": float(effects.get("prototype_transhuman_ess") or 0),
        "burnout_way": bool(effects.get("burnout_way")),
        "disabled_cyberware_grades": list(effects.get("disabled_cyberware_grades") or []),
        "disabled_bioware_grades": list(effects.get("disabled_bioware_grades") or []),
        "limit_spell_categories": list(effects.get("limit_spell_categories") or []),
        "limit_spirit_categories": list(effects.get("limit_spirit_categories") or []),
        "allow_spell_categories": list(effects.get("allow_spell_categories") or []),
        "allow_spell_ranges": list(effects.get("allow_spell_ranges") or []),
        "spell_range_gated": bool(magic.get("range_gated")),
        "block_spell_descriptors": list(effects.get("block_spell_descriptors") or []),
        "extra_spirits": list(effects.get("extra_spirits") or []),
        "add_spirit_picks": list(effects.get("add_spirit_picks") or []),
        "initiate_grade": int(initiation.get("grade") or 0),
        "initiation": {
            "grade": int(initiation.get("grade") or 0),
            "karma": int(initiation.get("karma") or 0),
            "choices": initiation.get("choices") or [],
            "metamagics": initiation.get("metamagics") or [],
            "arts": initiation.get("arts") or [],
        },
        "submersion_grade": int(submersion.get("grade") or 0),
        "submersion": {
            "grade": int(submersion.get("grade") or 0),
            "karma": int(submersion.get("karma") or 0),
            "choices": submersion.get("choices") or [],
            "echoes": submersion.get("echoes") or [],
        },
        "skill_totals": skill_totals,
        "skill_specializations": specs["specs"],
        "skill_expertises": expertises,
        "exotic_skills": exotic["public"],
        "skillsoft": skillsofts["all"],
        "skillwires": skillsofts["skillwires"],
        "skilljack": skillsofts["skilljack"],
        "skill_bonus": skill_mods["skill_bonus"],
        "skill_group_bonus": skill_mods["skill_group_bonus"],
        "skill_category_bonus": skill_mods["skill_category_bonus"],
        "skill_bonus_notes": skill_mods["skill_bonus_notes"],
        "skill_max_bonus": skill_picks["skill_max_bonus"],
        "skill_pick_slots": skill_picks["slots"],
        "enabled_tabs": sorted(enabled),
        "unimplemented_bonuses": effects["unimplemented"],
        "qualities": [
            {
                "id": q["id"],
                "name": q["name"],
                "karma": 0 if q["id"] in free_quality_ids else q["karma"],
                "category": q["category"],
                "source": q["source"],
                "needs_extra": quality_needs_extra(q),
                "extra": state.quality_extras.get(q["id"]) or "",
                "spirit_extra": state.quality_extras.get(quality_spirit_category_extra_key(q["id"])) or "",
                "extra_kind": q.get("extra_kind"),
                "select_options": list(q.get("select_options") or []),
                "spirit_options": list(q.get("spirit_options") or []),
                "expertise_skill": q.get("expertise_skill") or "",
                "add_spirit_count": int(q.get("add_spirit_count") or 0),
                "selectside": _quality_has_selectside(q),
                "side": _normalize_side(state.quality_extras.get(q["id"])) if _quality_has_selectside(q) else None,
                "free": q["id"] in free_quality_ids or bool(q.get("onlyprioritygiven")),
            }
            for q in qualities
        ],
        "cyberware": [_public_installed(item) for item in cyber_installed],
        "bioware": [_public_installed(item) for item in bio_installed],
        "ware_ranges": ware_ranges(attrs_spec),
        "limb_replace": limb_replace,
        "limb_quality": limb_quality,
        "talent": talent,
        "metatype_info": {
            "name": meta["name"],
            "parent": meta.get("parent"),
            "attributes": {
                key: {
                    **spec,
                    "max": int(spec.get("max") or 0) + int(attr_max_bonus.get(key) or 0),
                    "aug": int(spec.get("aug") or 0) + int(attr_max_bonus.get(key) or 0),
                }
                for key, spec in _effective_attr_spec(
                    attrs_spec,
                    special_key,
                    talent_start,
                    int(initiation.get("mag_max_bonus") or 0),
                    int(submersion.get("res_max_bonus") or 0),
                ).items()
            },
            "source": meta.get("source"),
        },
        "translations": {k: data["translations"].get(k, k) for k in [state.metatype, state.metavariant or ""]},
    }
    return state
