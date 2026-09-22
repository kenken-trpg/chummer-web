"""Phase 9 — gear.

Hosts ``resolve_gear`` (the armour / weapons / matrix / drones / lifestyle
resolver, a plain function; the armour, weapon and commlink rows are built in
``gear_rows``) and ``gear_phase(ctx)`` which runs it
then folds in lifestyle / erased / reach / weapon-DV mods, the Black Market
Pipeline pick (``gear_market``), purchase discounts, Overclocker, the Trust Fund check,
active drugs, weapon-focus dice and the adept tab enable.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, cast

from ...improvements import apply_bonus_nodes
from ...improvements.effect_rows import GrantGearRow
from ...models import CharacterState
from ...notices import Notice
from ..bundle_types import GearBundle
from ..constants import ADEPT_TALENTS
from ..contacts import apply_erased_lifestyle_cap
from ..gear import (
    _append_armor_weapons,
    _append_gear_weapons,
    _append_granted_weapons,
    _append_natural_weapons,
    _append_quality_weapons,
    _append_ware_weapons,
    _apply_recoil_totals,
    _ensure_drone_equipment,
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
    apply_active_custom_drugs,
    apply_active_drugs,
    apply_armor_gear,
    apply_lifestyle_cost_mod,
    apply_reach_bonus,
    apply_smartlink_accuracy,
    apply_weapon_category_dice,
    apply_weapon_category_dv,
    apply_weapon_skill_accuracy,
    lifestyle_cost_factor,
    resolve_custom_drugs,
    resolve_lifestyles,
)
from ..gear.matrix import apply_host_matrix_mods
from ..limits import _finalize_avail_tree
from ..magic import attach_weapon_focus_dice
from ..pricing import apply_black_market_avail, apply_overclocker, apply_purchase_discounts
from ..ware import _attach_ware_to_vehicle_mods
from .context import Ctx
from .gear_market import discounted_ids, pick_black_market
from .gear_rows import resolve_armor_rows, resolve_commlink_rows, resolve_weapon_rows


def resolve_gear(
    state: CharacterState,
    ware_items: list[dict[str, Any]] | None = None,
    attr_totals: dict[str, int] | None = None,
    special_modification_limit: int = 0,
    granted_gear: list[GrantGearRow] | None = None,
) -> GearBundle:
    warnings: list[Notice] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    # What each line of the sidebar's spending breakdown is responsible for.
    # Kept here rather than re-added from the public rows later: a thing bolted
    # onto something else has its price folded into the row it is bolted to (a
    # cyberspur into the implant, ammunition into the gun, a plate into the
    # jacket), so adding those rows up counts the same money twice — which is
    # what the breakdown used to do, on 29 of Chummer's 34 test saves.
    spend: defaultdict[str, int] = defaultdict(int)
    cyberdecks: list[dict[str, Any]] = []
    rccs: list[dict[str, Any]] = []
    errors: list[Notice] = []

    state.armor, armor_items, armor_nuyen, armor_bonus = resolve_armor_rows(state)
    spend["armor"] += armor_nuyen
    bonus_sources.extend(armor_bonus)
    armor_mods, mod_nuyen, mod_warns, mod_errors, mod_bonus = _resolve_armor_mods(state, armor_items)
    spend["armorMods"] += mod_nuyen
    warnings.extend(mod_warns)
    errors.extend(mod_errors)
    bonus_sources.extend(mod_bonus)
    worn_armor, worn_name, worn_warns, encumbrance = _recompute_worn_armor(
        armor_items, int(attr_totals["STR"]) if attr_totals and "STR" in attr_totals else None
    )
    warnings.extend(worn_warns)

    state.weapons, weapons, weapon_nuyen = resolve_weapon_rows(state)
    spend["weapons"] += weapon_nuyen
    _append_armor_weapons(weapons, armor_items)
    _append_ware_weapons(weapons, ware_items or [], state, attr_totals)
    weapon_accessories, acc_nuyen, acc_warns, acc_errors, special_mod_used = _resolve_weapon_accessories(
        state, weapons, special_modification_limit=special_modification_limit
    )
    recoil_info = _apply_recoil_totals(weapons, attr_totals or {})
    spend["weaponAccessories"] += acc_nuyen
    warnings.extend(acc_warns)
    errors.extend(acc_errors)

    state.commlinks, commlinks, link_nuyen = resolve_commlink_rows(state)
    spend["commlinks"] += link_nuyen

    kept_decks, cyberdecks, deck_nuyen = _resolve_matrix_devices("cyberdecks", list(state.cyberdecks or []))
    state.cyberdecks = kept_decks
    spend["cyberdecks"] += deck_nuyen
    kept_rccs, rccs, rcc_nuyen = _resolve_matrix_devices("rccs", list(state.rccs or []))
    state.rccs = kept_rccs
    spend["rccs"] += rcc_nuyen
    optics, optic_nuyen, optic_warns, optic_errors, optic_bonus = _resolve_optics(state)
    spend["optics"] += optic_nuyen
    warnings.extend(optic_warns)
    errors.extend(optic_errors)
    bonus_sources.extend(optic_bonus)
    programs, prog_nuyen, prog_warns = _resolve_programs(state, cyberdecks, rccs)
    spend["programs"] += prog_nuyen
    warnings.extend(prog_warns)
    # a deck or an RCC runs apps too (BLUE's RCC carries Swarm)
    apps, app_nuyen, app_warns = _resolve_apps(state, [*commlinks, *cyberdecks, *rccs])
    spend["programs"] += app_nuyen
    warnings.extend(app_warns)
    drones, drone_nuyen = _resolve_drones(state, "drones")
    spend["drones"] += drone_nuyen
    vehicles, vehicle_nuyen = _resolve_drones(state, "vehicles")
    spend["vehicles"] += vehicle_nuyen
    hosts = drones + vehicles
    _ensure_drone_equipment(state)
    vehicle_mods, mod_nuyen, mod_warns, mod_errors = _resolve_vehicle_mods(state, hosts)
    spend["vehicleMods"] += mod_nuyen
    warnings.extend(mod_warns)
    errors.extend(mod_errors)
    weapon_mounts, mount_nuyen, mount_warns, mount_errors = _resolve_weapon_mounts(state, hosts, weapons)
    spend["vehicleMods"] += mount_nuyen
    warnings.extend(mount_warns)
    errors.extend(mount_errors)
    sensors, sensor_nuyen, sensor_warns, sensor_errors, sensor_bonus = _resolve_sensors(state)
    spend["sensors"] += sensor_nuyen
    warnings.extend(sensor_warns)
    errors.extend(sensor_errors)
    bonus_sources.extend(sensor_bonus)
    _publish_drone_stats(hosts, sensors)
    gear_items, gear_nuyen, gear_warns, gear_errors, gear_bonus = _resolve_misc_gear(
        state, hosts, weapons, granted_gear
    )
    spend["otherGear"] += gear_nuyen
    warnings.extend(gear_warns)
    errors.extend(gear_errors)
    bonus_sources.extend(gear_bonus)
    _append_gear_weapons(weapons, gear_items)
    # decks and RCCs take the same accessories a commlink does, and the DT
    # p.66 modifications are soldered into all three
    apply_host_matrix_mods([*commlinks, *cyberdecks, *rccs], gear_items)
    apply_armor_gear(armor_items, {"gear": gear_items, "optics": optics, "sensors": sensors}, errors)

    custom_drugs, custom_drug_nuyen, custom_drug_warns, custom_drug_errors = resolve_custom_drugs(state)
    spend["customDrugs"] += custom_drug_nuyen
    warnings.extend(custom_drug_warns)
    errors.extend(custom_drug_errors)

    lifestyles, lifestyle_nuyen, lifestyle_warns, lifestyle_bonus = resolve_lifestyles(state)
    spend["lifestyles"] += lifestyle_nuyen
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
        "nuyen": sum(spend.values()),
        "nuyen_by_bucket": dict(spend),
        "armor": worn_armor,
        "worn_name": worn_name,
        "armor_encumbrance": encumbrance,
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
        "custom_drugs": custom_drugs,
        "lifestyles": lifestyles,
        "commlink": primary_link,
        "cyberdeck": primary_deck,
        "rcc": primary_rcc,
        "lifestyle": primary_life,
    }


def gear_phase(ctx: Ctx) -> None:
    ctx.gear = resolve_gear(
        ctx.state,
        # Bioware grants weapons too — claws and tusks (CF p.72) are `<addweapon>`
        # implants exactly like a cyberspur.
        [*ctx.cyber_installed, *ctx.bio_installed],
        ctx.attr_totals,
        special_modification_limit=int(ctx.effects.get("special_modification_limit") or 0),
        granted_gear=list(ctx.effects["grant_gear"]),
    )
    ctx.warnings.extend(ctx.gear["warnings"])
    ctx.errors.extend(ctx.gear.get("errors") or [])
    # SR5 p.169 armor encumbrance: an augmented malus on AGI and REA, folded in
    # before `totals` sums the attributes
    for key in ("AGI", "REA"):
        ctx.effects["attribute_bonus"][key] = int(ctx.effects["attribute_bonus"].get(key, 0)) + int(
            ctx.gear.get("armor_encumbrance") or 0
        )
    # Before the weapon modifiers below: a natural weapon is an Unarmed Combat
    # attack, so a reach or unarmed-AP bonus has to reach it too.
    _append_natural_weapons(ctx.gear["weapons"], ctx.effects)
    _append_quality_weapons(ctx.gear["weapons"], ctx.qualities)
    _append_granted_weapons(ctx.gear["weapons"], ctx.effects)
    metatype_sources = {str(ctx.meta.get("name") or "")} - {""}
    apply_lifestyle_cost_mod(
        ctx.gear,
        int(ctx.effects.get("lifestyle_cost") or 0),
        lifestyle_cost_factor(list(ctx.effects.get("lifestyle_cost_mods") or []), metatype_sources),
    )
    for row in ctx.gear.get("lifestyles") or []:
        row.pop("_pre_mod", None)
        row.pop("_after_mod", None)
    # what a piece of ware holds (a Chemical Gland's chemical) is listed on it
    for item in [*ctx.cyber_installed, *ctx.bio_installed]:
        if item.get("allow_gear"):
            item["gear"] = [
                {**row, "bucket": "gear"} for row in ctx.gear.get("gear") or [] if row.get("parent_id") == item["id"]
            ]
    apply_erased_lifestyle_cap(ctx.gear, bool(ctx.effects.get("erased")), ctx.warnings)
    apply_reach_bonus(ctx.gear.get("weapons"), int(ctx.effects.get("reach") or 0))
    apply_weapon_category_dv(ctx.gear.get("weapons"), ctx.effects)
    apply_weapon_category_dice(ctx.gear.get("weapons"), ctx.effects)
    apply_weapon_skill_accuracy(ctx.gear.get("weapons"), ctx.effects)
    pick_black_market(ctx)
    # These two iterate gear[<category>] over a tuple of category names, so
    # they take a plain str-keyed dict rather than the GearBundle TypedDict.
    apply_purchase_discounts(
        cast("dict[str, Any]", ctx.gear),
        ctx.cyber_installed,
        ctx.bio_installed,
        ctx.effects,
        black_market_category=ctx.bmp_category if ctx.bmp_active else "",
        discounted_ids=discounted_ids(ctx.state),
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
            ctx.warn("engine.gear.trustFundNeedsSinner")
    ctx.errors.extend(_attach_ware_to_vehicle_mods(ctx.gear.get("vehicle_mods") or [], ctx.cyber_installed))
    for source, nodes in ctx.gear["bonus_sources"]:
        apply_bonus_nodes(nodes, ctx.effects, source)
    ctx.active_drugs = apply_active_drugs(ctx.state, ctx.attr_totals, ctx.effects)
    ctx.active_drugs.extend(apply_active_custom_drugs(ctx.gear.get("custom_drugs") or [], ctx.effects))
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
