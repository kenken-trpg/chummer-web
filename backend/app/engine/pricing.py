"""Availability & cost adjustments applied after gear is resolved: essence-
multiplier bioware/cyberware, Black Market Pipeline availability, dealer-
connection / used-gear / build-repair discounts, Overclocker.
"""

from __future__ import annotations

from typing import Any

from ..data_loader import format_avail
from ..improvements import EffectsDict
from .bundle_types import GearBundle
from .constants import (
    BLACK_MARKET_AVAIL_BONUS,
    BLACK_MARKET_CATEGORY_HINTS,
    DEALER_CONNECTION_MATCH,
    MATRIX_ARRAY_KEYS,
    TRUST_FUND_LIFESTYLE,
)
from .karma import _floor_tenth


def apply_ware_essence_multipliers(
    cyber: list[dict[str, Any]],
    bio: list[dict[str, Any]],
    effects: EffectsDict,
) -> tuple[float, float]:
    cmult = int(effects.get("cyberware_ess_multiplier") or 100)
    bmult = int(effects.get("bioware_ess_multiplier") or 100)
    tmult = int(effects.get("cyberware_total_ess_multiplier") or 100)
    if cmult != 100:
        for item in cyber:
            ess = float(item.get("essence") or 0)
            if ess > 0:
                item["essence"] = _floor_tenth(ess * cmult / 100.0)
    if bmult != 100:
        for item in bio:
            ess = float(item.get("essence") or 0)
            if ess > 0:
                item["essence"] = _floor_tenth(ess * bmult / 100.0)
    free_bio = max(0.0, float(effects.get("prototype_transhuman_ess") or 0))
    if free_bio > 0:
        remaining = free_bio
        # Prefer waiving smaller essence pieces first so more items can be covered.
        ordered = sorted(bio, key=lambda row: float(row.get("essence") or 0))
        for item in ordered:
            ess = float(item.get("essence") or 0)
            if ess <= 0 or remaining <= 0:
                continue
            take = min(ess, remaining)
            item["essence"] = round(ess - take, 4)
            item["prototype_transhuman"] = True
            remaining = round(remaining - take, 4)
    cyber_lost = round(sum(float(item.get("essence") or 0) for item in cyber), 4)
    bio_lost = round(sum(float(item.get("essence") or 0) for item in bio), 4)
    if tmult != 100 and cyber_lost > 0:
        cyber_lost = round(_floor_tenth(cyber_lost * tmult / 100.0), 4)
    return cyber_lost, bio_lost


def _dealer_matches(category: str, dealer_cats: list[str]) -> bool:
    cat = str(category or "")
    for dealer in dealer_cats or []:
        prefixes = DEALER_CONNECTION_MATCH.get(dealer)
        if prefixes is None:
            if dealer.lower() in cat.lower():
                return True
            continue
        if dealer == "Drones" and cat.startswith("Drones"):
            return True
        if cat in prefixes:
            return True
    return False


def _bmp_row_matches(row: dict[str, Any], category: str, *, gear_key: str = "") -> bool:
    if not category:
        return False
    if category == "Cyberware":
        return True
    if category == "Bioware":
        return True
    keys = set(BLACK_MARKET_CATEGORY_HINTS.get(category) or ())
    if gear_key and gear_key not in keys:
        return False
    if gear_key == "gear" and category == "Drugs":
        return str(row.get("category") or "") in {"Drugs", "Toxins", "Chemicals"}
    return bool(gear_key)


def apply_black_market_avail(
    gear: dict[str, Any],
    cyber_installed: list[dict[str, Any]],
    bio_installed: list[dict[str, Any]],
    *,
    black_market_category: str = "",
    bonus: int = BLACK_MARKET_AVAIL_BONUS,
) -> None:
    """Lower effective Availability by ``bonus`` for BMP-matching gear (chargen limit / sheet)."""
    if not black_market_category or bonus <= 0:
        return

    def _apply(row: dict[str, Any]) -> None:
        raw = int(row.get("avail_value") or 0)
        if raw <= 0:
            return
        effective = max(0, raw - int(bonus))
        row["avail_base"] = raw
        row["avail_value"] = effective
        row["black_market_avail"] = True
        row["avail"] = format_avail(effective, str(row.get("avail_suffix") or ""))

    if black_market_category == "Cyberware":
        for row in cyber_installed:
            _apply(row)
        return
    if black_market_category == "Bioware":
        for row in bio_installed:
            _apply(row)
        return

    keys = set(BLACK_MARKET_CATEGORY_HINTS.get(black_market_category) or ())
    for key in keys:
        for row in gear.get(key) or []:
            if _bmp_row_matches(row, black_market_category, gear_key=key):
                _apply(row)


def apply_purchase_discounts(
    gear: dict[str, Any],
    cyber_installed: list[dict[str, Any]],
    bio_installed: list[dict[str, Any]],
    effects: EffectsDict,
    *,
    black_market_category: str = "",
) -> None:
    """Mutate item nuyen in place; adjust gear["nuyen"] by discount savings only."""
    dealer = list(effects.get("dealer_connection_categories") or [])
    made = bool(effects.get("made_man"))
    bmp = bool(effects.get("black_market_discount")) and bool(black_market_category)
    bmp_keys = set(BLACK_MARKET_CATEGORY_HINTS.get(black_market_category) or ())
    saved = 0

    def _discount(row: dict[str, Any], pct: int) -> None:
        nonlocal saved
        base = int(row.get("nuyen") or 0)
        if base <= 0 or pct <= 0:
            return
        new_cost = int(round(base * (100 - pct) / 100.0))
        saved += base - new_cost
        row["nuyen"] = new_cost
        row["discount_pct"] = int(row.get("discount_pct") or 0) + pct

    for key in ("vehicles", "drones"):
        for row in gear.get(key) or []:
            if _dealer_matches(str(row.get("category") or ""), dealer):
                _discount(row, 10)
            if bmp and key in bmp_keys:
                _discount(row, 10)
            if made and "R" in str(row.get("avail") or "").upper():
                _discount(row, 10)

    for key in (
        "weapons",
        "armor_items",
        "armor_mods",
        "weapon_accessories",
        "commlinks",
        "cyberdecks",
        "rccs",
        "optics",
        "sensors",
        "programs",
        "apps",
        "gear",
        "vehicle_mods",
        "weapon_mounts",
    ):
        for row in gear.get(key) or []:
            if bmp and key in bmp_keys:
                if key == "gear" and black_market_category == "Drugs":
                    if str(row.get("category") or "") not in {"Drugs", "Toxins", "Chemicals"}:
                        continue
                _discount(row, 10)
            if made and "R" in str(row.get("avail") or "").upper():
                _discount(row, 10)

    if bmp and black_market_category == "Cyberware":
        for row in cyber_installed:
            _discount(row, 10)
    if bmp and black_market_category == "Bioware":
        for row in bio_installed:
            _discount(row, 10)

    trust = int(effects.get("trustfund") or 0)
    covered = TRUST_FUND_LIFESTYLE.get(trust)
    if covered:
        for row in gear.get("lifestyles") or []:
            if str(row.get("name") or "") == covered:
                base = int(row.get("nuyen") or 0)
                if base:
                    saved += base
                    row["nuyen"] = 0
                    row["trustfund"] = True

    if saved:
        gear["nuyen"] = max(0, int(gear.get("nuyen") or 0) - saved)


def apply_overclocker(gear: GearBundle, enabled: bool) -> None:
    if not enabled:
        return
    decks = list(gear.get("cyberdecks") or [])
    if not decks:
        return
    deck = max(decks, key=lambda row: int(row.get("device_rating") or 0))
    # Prefer Attack, else first matrix attr.
    for key in MATRIX_ARRAY_KEYS:
        if key in deck:
            deck[key] = int(deck.get(key) or 0) + 1
            deck["overclocker"] = key
            break
