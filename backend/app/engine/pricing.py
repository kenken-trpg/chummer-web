"""Availability & cost adjustments applied after gear is resolved: essence-
multiplier bioware/cyberware, Black Market Pipeline availability, dealer-
connection / used-gear / build-repair discounts, Overclocker.
"""

from __future__ import annotations

from collections.abc import Iterator
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from ..data_loader import DRUG_CATEGORIES, format_avail
from ..improvements import EffectsDict
from ..rules import current_rules
from .bundle_types import GearBundle
from .constants import (
    BLACK_MARKET_AVAIL_BONUS,
    BLACK_MARKET_CATEGORY_HINTS,
    DEALER_CONNECTION_MATCH,
    MATRIX_ARRAY_KEYS,
    TRUST_FUND_LIFESTYLE,
)


def apply_ware_essence_multipliers(
    cyber: list[dict[str, Any]],
    bio: list[dict[str, Any]],
    effects: EffectsDict,
) -> tuple[float, float]:
    """Each piece's essence, as Chummer works it out (`Cyberware.CalculatedESS`).

    The grade's multiplier and the character's (Biocompatibility's 90 takes
    0.1 off) are added, not multiplied: Used cyberware under Biocompatibility
    is 1.25 - 0.1 = 1.15. A total multiplier (Sensitive System's 200)
    multiplies what that gives. Each piece is then rounded to two places,
    away from zero, unless the settings say not to round essence; a piece
    that adds to its parent's essence is added after its own rounding.

    The `...nonretroactive` multipliers count the same way, from what a
    piece holds (`ess_extra_add` / `ess_extra_mult`, which career sets,
    `essence.py`) or, on a piece that holds none, from the live bonus.
    """
    _work_out_essence(
        cyber,
        int(effects.get("cyberware_ess_multiplier") or 100),
        int(effects.get("cyberware_total_ess_multiplier") or 100),
        nonretroactive_multipliers(effects, "cyberware"),
    )
    _work_out_essence(
        bio,
        int(effects.get("bioware_ess_multiplier") or 100),
        int(effects.get("bioware_total_ess_multiplier") or 100),
        nonretroactive_multipliers(effects, "bioware"),
    )
    free_bio = max(0.0, float(effects.get("prototype_transhuman_ess") or 0))
    if free_bio > 0:
        picked = _ticked_pieces(bio)
        for item in picked if picked is not None else _prototype_transhuman_pieces(bio, free_bio):
            item["prototype_ess"] = float(item.get("essence") or 0)
            item["essence"] = 0.0
            item["prototype_transhuman"] = True
    cyber_lost = round(sum(float(item.get("essence") or 0) for item in cyber), 4)
    bio_lost = round(sum(float(item.get("essence") or 0) for item in bio), 4)
    return cyber_lost, bio_lost


def _round_essence(value: float) -> float:
    if current_rules().dont_round_essence_internally:
        return round(value, 6)
    return float(Decimal(str(round(value, 6))).quantize(Decimal("0.01"), ROUND_HALF_UP))


def nonretroactive_multipliers(effects: EffectsDict, kind: str) -> tuple[float, float]:
    """What the `...nonretroactive` bonuses of `kind` ("cyberware" or
    "bioware") add to a piece's grade and multiply its essence by, as
    Chummer keeps them on it (`Cyberware.SaveNonRetroactiveEssenceModifiers`)."""
    if kind == "cyberware":
        add = int(effects.get("cyberware_ess_multiplier_nonretro") or 100)
        total = int(effects.get("cyberware_total_ess_multiplier_nonretro") or 100)
    else:
        add = int(effects.get("bioware_ess_multiplier_nonretro") or 100)
        total = int(effects.get("bioware_total_ess_multiplier_nonretro") or 100)
    return (add - 100) / 100.0, total / 100.0


def _work_out_essence(
    items: list[dict[str, Any]], mult_pct: int, total_pct: int, live: tuple[float, float] = (0.0, 1.0)
) -> None:
    own: dict[str, float] = {}
    for item in items:
        if "ess_raw" not in item:
            continue
        grade = float(item.get("ess_grade") or 1)
        if item.get("ess_multiplied", True):
            extra_add = float(item.get("ess_extra_add", live[0]))
            extra_mult = float(item.get("ess_extra_mult", live[1]))
            modifier = max(0.0, (grade + extra_add + mult_pct / 100.0 - 1.0) * total_pct / 100.0 * extra_mult)
        else:
            modifier = grade
        own[str(item["id"])] = _round_essence(float(item["ess_raw"] or 0) * modifier)
    for item in items:
        key = str(item.get("id"))
        if key not in own:
            continue
        item["ess_to_parent"] = own[key] if float(item.get("ess_to_parent") or 0) else 0.0
    to_parent: dict[str, float] = {}
    for item in items:
        if float(item.get("ess_to_parent") or 0) and item.get("parent_id"):
            parent = str(item["parent_id"])
            to_parent[parent] = to_parent.get(parent, 0.0) + float(item["ess_to_parent"])
    for item in items:
        key = str(item.get("id"))
        if key not in own:
            continue
        mine = own[key] if item.get("ess_self") else 0.0
        item["essence"] = round(mine + to_parent.get(key, 0.0), 4)


def _ticked_pieces(bio: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
    """The bioware the player ticked for Prototype Transhuman, with what sits
    in it (Chummer's `PrototypeTranshuman` setter ticks the children too);
    None when nothing has been ticked or unticked yet.

    Only a piece with no parent can be ticked (`CharacterCreate`'s
    `blnCanBePT`), so a child's own mark is not read. Whether the ticked
    pieces fit the allowance is the creation check's to say
    (`Message_OverPrototypeLimit`), not this one's.
    """
    if all(item.get("prototype_pick") is None for item in bio):
        return None
    ids = {str(item.get("id")) for item in bio}
    waived = {
        str(item.get("id"))
        for item in bio
        if item.get("prototype_pick") and str(item.get("parent_id") or "") not in ids
    }
    grew = True
    while grew:
        grew = False
        for item in bio:
            key = str(item.get("id"))
            if key not in waived and str(item.get("parent_id") or "") in waived:
                waived.add(key)
                grew = True
    return [item for item in bio if str(item.get("id")) in waived]


def _prototype_transhuman_pieces(bio: list[dict[str, Any]], allowance: float) -> list[dict[str, Any]]:
    """The bioware Prototype Transhuman's allowance waives.

    Chummer waives whole pieces: the player ticks a piece, and a ticked one
    counts no essence at all (`Cyberware.CalculatedESS`), so long as the
    ticked ones add up to no more than the allowance. A piece cannot be
    waived in part — that was this app's old reading, which let the
    allowance run into the last piece it reached. The player picks; this app
    picks the set a player would, the one that waives the most essence,
    smaller pieces first among equals. Thousandths, as essence is never finer.
    """
    pieces = sorted(
        (item for item in bio if float(item.get("essence") or 0) > 0),
        key=lambda item: float(item.get("essence") or 0),
    )
    budget = round(allowance * 1000)
    # best[w]: the pieces first reaching a waived total of exactly w
    best: dict[int, list[int]] = {0: []}
    for index, item in enumerate(pieces):
        cost = round(float(item.get("essence") or 0) * 1000)
        for total, chosen in sorted(best.items(), reverse=True):
            reached = total + cost
            if reached <= budget and reached not in best:
                best[reached] = [*chosen, index]
    return [pieces[index] for index in best[max(best)]]


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
        return str(row.get("category") or "") in DRUG_CATEGORIES
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


#: the gear lists a Black Market Pipeline pick may sit in, in the order they are priced
_BLACK_MARKET_GEAR_KEYS = (
    "vehicles",
    "drones",
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
)


def apply_purchase_discounts(
    gear: dict[str, Any],
    cyber_installed: list[dict[str, Any]],
    bio_installed: list[dict[str, Any]],
    effects: EffectsDict,
    *,
    black_market_category: str = "",
    discounted_ids: set[str] | None = None,
) -> None:
    """Mutate item nuyen in place; adjust gear["nuyen"] by discount savings only.

    A Dealer Connection applies on its own — Chummer takes 10% off every
    vehicle of the categories it names. The Black Market Pipeline does not:
    it lets the buyer take 10% off an item of its category, one item at a
    time (Chummer's `<discountedcost>`), so only what `discounted_ids` names
    is cheaper. On a vehicle that has both, the dealer's 10% comes first.
    """
    dealer = list(effects.get("dealer_connection_categories") or [])
    saved = 0
    for key in ("vehicles", "drones"):
        for row in gear.get(key) or []:
            if _dealer_matches(str(row.get("category") or ""), dealer):
                saved += _discount(row, 10)
    if effects.get("black_market_discount") and black_market_category:
        rows = _black_market_picks(gear, cyber_installed, bio_installed, black_market_category, discounted_ids or set())
        saved += sum(_discount(row, 10) for row in rows)
    saved += _trust_fund(gear, effects)
    if saved:
        gear["nuyen"] = max(0, int(gear.get("nuyen") or 0) - saved)


def _discount(row: dict[str, Any], pct: int) -> int:
    """Take ``pct`` percent off the row; return what that saved."""
    base = int(row.get("nuyen") or 0)
    if base <= 0 or pct <= 0:
        return 0
    new_cost = int(round(base * (100 - pct) / 100.0))
    row["nuyen"] = new_cost
    row["discount_pct"] = int(row.get("discount_pct") or 0) + pct
    return base - new_cost


def _black_market_picks(
    gear: dict[str, Any],
    cyber_installed: list[dict[str, Any]],
    bio_installed: list[dict[str, Any]],
    category: str,
    picked: set[str],
) -> Iterator[dict[str, Any]]:
    """The rows the player took the Black Market Pipeline's 10% on."""
    keys = set(BLACK_MARKET_CATEGORY_HINTS.get(category) or ())
    for key in _BLACK_MARKET_GEAR_KEYS:
        if key not in keys:
            continue
        for row in gear.get(key) or []:
            if str(row.get("id") or "") not in picked:
                continue
            if key == "gear" and category == "Drugs" and str(row.get("category") or "") not in DRUG_CATEGORIES:
                continue
            yield row
    ware = cyber_installed if category == "Cyberware" else bio_installed if category == "Bioware" else []
    yield from (row for row in ware if str(row.get("id") or "") in picked)


def _trust_fund(gear: dict[str, Any], effects: EffectsDict) -> int:
    """A Trust Fund pays for its lifestyle outright; return the nuyen that saved."""
    covered = TRUST_FUND_LIFESTYLE.get(int(effects.get("trustfund") or 0))
    if not covered:
        return 0
    saved = 0
    for row in gear.get("lifestyles") or []:
        base = int(row.get("nuyen") or 0)
        if str(row.get("name") or "") == covered and base:
            saved += base
            row["nuyen"] = 0
            row["trustfund"] = True
    return saved


def apply_overclocker(gear: GearBundle, enabled: bool) -> None:
    """Overclocker (RF p.148): +1 to the Matrix attribute picked on each deck.

    Chummer keeps the pick per deck (`Gear.Overclocked`) and adds it by name,
    so it follows the attribute wherever the array put it. Until a deck has a
    pick, the highest-rated deck's Attack gets it, as before there was one.
    The deck that got it says which attribute in ``overclocker``."""
    decks = list(gear.get("cyberdecks") or [])
    if not enabled or not decks:
        return
    picked = {str(deck["id"]): str(deck.get("overclocked")) for deck in decks if deck.get("overclocked")}
    if not picked:
        best = max(decks, key=lambda row: int(row.get("device_rating") or 0))
        picked = {str(best["id"]): next((key for key in MATRIX_ARRAY_KEYS if key in best), "none")}
    for deck in decks:
        key = picked.get(str(deck["id"]), "none")
        if key in MATRIX_ARRAY_KEYS and key in deck:
            deck[key] = int(deck.get(key) or 0) + 1
            deck["overclocker"] = key
