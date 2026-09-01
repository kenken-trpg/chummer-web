"""Phase 9 — gear.

Hosts ``resolve_gear`` (the 200-line armour / weapons / matrix / drones /
lifestyle resolver, a plain function) and ``gear_phase(ctx)`` which runs it
then folds in lifestyle / erased / reach / weapon-DV mods, the Black Market
Pipeline pick, purchase discounts, Overclocker, the Trust Fund check,
active drugs, weapon-focus dice and the adept tab enable.
"""

from __future__ import annotations

from typing import Any, cast

from ...data_loader import eval_formula
from ...improvements import apply_bonus_nodes, substitute_rating
from ...models import ArmorInstall, CharacterState, CommlinkInstall, WeaponInstall
from ..bundle_types import GearBundle
from ..constants import ADEPT_TALENTS, quality_contact_extra_key
from ..contacts import apply_erased_lifestyle_cap
from ..formulas import parse_armor_value
from ..gear import (
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
    apply_smartlink_accuracy,
    apply_weapon_category_dice,
    apply_weapon_category_dv,
    apply_weapon_skill_accuracy,
    resolve_lifestyles,
)
from ..limits import _finalize_avail_tree
from ..lookups import _item_by_id
from ..magic import attach_weapon_focus_dice
from ..pricing import apply_black_market_avail, apply_overclocker, apply_purchase_discounts
from ..ware import _attach_ware_to_vehicle_mods
from .context import Ctx


def resolve_gear(
    state: CharacterState,
    ware_items: list[dict[str, Any]] | None = None,
    attr_totals: dict[str, int] | None = None,
    special_modification_limit: int = 0,
) -> GearBundle:
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


def gear_phase(ctx: Ctx) -> None:
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
    apply_weapon_category_dice(ctx.gear.get("weapons"), ctx.effects)
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
    # These two iterate gear[<category>] over a tuple of category names, so
    # they take a plain str-keyed dict rather than the GearBundle TypedDict.
    apply_purchase_discounts(
        cast("dict[str, Any]", ctx.gear),
        ctx.cyber_installed,
        ctx.bio_installed,
        ctx.effects,
        black_market_category=ctx.bmp_category if ctx.bmp_active else "",
    )
    if ctx.bmp_active:
        apply_black_market_avail(
            cast("dict[str, Any]", ctx.gear),
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
    # After every bonus source (ware folded in the effects phase, gear + drugs
    # just now) so a smartlink from any of them counts.
    apply_smartlink_accuracy(ctx.gear.get("weapons"), ctx.effects)
    attach_weapon_focus_dice(
        ctx.state, list(ctx.foci.get("public") or []), list(ctx.gear.get("weapons") or []), ctx.warnings
    )
    if ctx.talent["name"] in ADEPT_TALENTS:
        ctx.enabled.add("adept")
        ctx.effects["enabled_tabs"].add("adept")
    ctx.enabled.update(ctx.effects["enabled_tabs"])
