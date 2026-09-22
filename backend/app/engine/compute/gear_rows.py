"""The rows `resolve_gear` builds straight from the state: worn armour,
weapons and commlinks. Each drops what the catalog no longer has, clamps what
the user typed, and returns the kept installs beside the public rows."""

from __future__ import annotations

from typing import Any

from ...data_loader import eval_formula
from ...improvements import substitute_rating
from ...models import ArmorInstall, CharacterState, CommlinkInstall, WeaponInstall
from ..formulas import parse_armor_value
from ..gear import _clamp_rating, _public_weapon
from ..gear._common import chosen_cost
from ..lookups import _item_by_id


def resolve_armor_rows(
    state: CharacterState,
) -> tuple[list[ArmorInstall], list[dict[str, Any]], int, list[tuple[str, list[dict[str, Any]]]]]:
    """(kept installs, armour rows, nuyen, bonus sources of what is worn)."""
    armor_items: list[dict[str, Any]] = []
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = []
    nuyen = 0
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
        picked = chosen_cost(spec, armor_inst.cost)
        armor_inst.cost = picked
        cost = picked if picked is not None else int(eval_formula(str(spec.get("cost") or "0"), rating, 0))
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
                "armoroverride": spec.get("armoroverride") or "",
                "rating": rating,
                "rating_max": int(spec.get("maxrating") or 0),
                "equipped": armor_inst.equipped,
                "wireless": armor_inst.wireless,
                "has_wireless": has_wireless,
                "nuyen": cost,
                "cost_range": spec.get("cost_range"),
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
    return kept_armor, armor_items, nuyen, bonus_sources


def resolve_weapon_rows(state: CharacterState) -> tuple[list[WeaponInstall], list[dict[str, Any]], int]:
    """(kept installs, weapon rows, nuyen)."""
    weapons: list[dict[str, Any]] = []
    nuyen = 0
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
    return kept_weapons, weapons, nuyen


def resolve_commlink_rows(state: CharacterState) -> tuple[list[CommlinkInstall], list[dict[str, Any]], int]:
    """(kept installs, commlink rows, nuyen)."""
    commlinks: list[dict[str, Any]] = []
    nuyen = 0
    kept_links: list[CommlinkInstall] = []
    for link_inst in state.commlinks:
        spec = _item_by_id("commlinks", link_inst.gear_id)
        if not spec:
            continue
        rating = _clamp_rating(spec, link_inst.rating)
        link_inst.rating = rating
        qty = max(1, int(link_inst.qty or 1))
        cost = int(eval_formula(str(spec.get("cost") or "0"), rating, 0)) * qty
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
                "qty": qty,
                "device_rating": device,
                "attack": int(eval_formula(str(spec.get("attack") or "0"), rating, 0)),
                "sleaze": int(eval_formula(str(spec.get("sleaze") or "0"), rating, 0)),
                "dataprocessing": processing,
                "firewall": firewall,
                "nuyen": cost,
                "avail": spec.get("avail") or "",
                "source": spec.get("source") or "",
                "page": spec.get("page") or "",
            }
        )
    return kept_links, commlinks, nuyen
