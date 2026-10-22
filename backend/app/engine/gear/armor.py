"""Armor modifications and the worn-armor total.

``_resolve_armor_mods`` walks each armor's plugins — capacity accounting,
fit rules, cost, armor bonus, wireless — and collects their ``<bonus>`` nodes;
``_recompute_worn_armor`` then folds equipped pieces into a single armor rating
(highest body + additive layers, per SR5 p.169).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from ...data_loader import catalog, eval_formula
from ...improvements import (
    limit_modifiers_from_nodes,
    special_armor_from_nodes,
    substitute_rating,
)
from ...models import ArmorModInstall, CharacterState
from ...notices import Notice, notice, term
from ...rules import current_rules
from ..formulas import parse_armor_value
from ._common import _clamp_rating


def armor_plugin_capacity(
    expr: str | None,
    rating: int,
    extras: dict[str, int | float] | None = None,
) -> float:
    raw = (expr or "").strip()
    if not raw:
        return 0.0
    fixed = re.fullmatch(r"FixedValues\((.+)\)", raw, re.I)
    if fixed:
        parts = [p.strip() for p in fixed.group(1).split(",")]
        idx = max(0, min(len(parts) - 1, int(rating) - 1))
        return armor_plugin_capacity(parts[idx], rating, extras)
    if raw.startswith("[") and raw.endswith("]") and "/" not in raw:
        inner = raw[1:-1]
        return eval_formula(inner, rating, 0.0, extras)
    return eval_formula(raw, rating, 0.0, extras)


def armor_mod_fits(
    spec: dict[str, Any],
    armor: dict[str, Any],
    installed_names: set[str] | None = None,
) -> bool:
    names = {str(n) for n in (installed_names or set())}
    required_names = [str(n) for n in (spec.get("required_names") or []) if n]
    if required_names and armor.get("name") not in required_names:
        return False
    required_mods = [str(n) for n in (spec.get("required_mods") or []) if n]
    if required_mods and any(name not in names for name in required_mods):
        return False
    category = str(spec.get("category") or "General")
    allowed = {str(c) for c in (armor.get("addmodcategories") or []) if c}
    if category == "General":
        return True
    if category in allowed:
        return True
    return category == str(armor.get("category") or "")


def _ensure_armor_mods(state: CharacterState) -> list[Notice]:
    warnings: list[Notice] = []
    specs = {item["id"]: item for item in catalog().get("armor_mods") or []}
    by_name = {item["name"]: item for item in specs.values()}
    armors = {item.id: item for item in state.armor}
    armor_specs = {item["id"]: item for item in catalog().get("armor") or []}
    kept: list[ArmorModInstall] = []
    for inst in list(state.armor_mods or []):
        spec = specs.get(inst.mod_id)
        parent = armors.get(inst.parent_id or "")
        if not spec or not parent:
            if spec:
                warnings.append(notice("engine.gear.mountOnArmor", name=term(str(spec["name"]))))
            continue
        kept.append(inst)
    have = {(row.parent_id, (specs.get(row.mod_id) or {}).get("name")) for row in kept}
    extra: list[ArmorModInstall] = []
    for armor in state.armor:
        aspec = armor_specs.get(armor.armor_id) or {}
        for gift in aspec.get("included_mods") or []:
            child = by_name.get(gift.get("name"))
            if not child or (armor.id, child["name"]) in have:
                continue
            extra.append(
                ArmorModInstall(
                    mod_id=child["id"],
                    parent_id=armor.id,
                    included=True,
                    rating=int(gift.get("rating") or 1),
                )
            )
            have.add((armor.id, child["name"]))
    state.armor_mods = kept + extra
    return warnings


def _resolve_armor_mods(
    state: CharacterState,
    armor_items: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int, list[Notice], list[Notice], list[tuple[str, list[dict[str, Any]]]]]:
    mods = _ArmorMods(warnings=_ensure_armor_mods(state))
    children: dict[str, list[ArmorModInstall]] = {}
    for inst in list(state.armor_mods or []):
        children.setdefault(inst.parent_id or "", []).append(inst)
    for item in armor_items:
        mods.armor(item, children.get(item["id"]) or [])
    state.armor_mods = mods.kept
    return mods.public, mods.nuyen, mods.warnings, mods.errors, mods.bonus_sources


@dataclass
class _Fit:
    """What one armor's mods take up so far."""

    cap_max_base: float
    parent_unit: int
    used: float = 0.0
    cap_bonus: float = 0.0
    seen_names: set[str] = field(default_factory=set)
    seen_unique: set[str] = field(default_factory=set)


@dataclass
class _ArmorMods:
    """The mod rows of every armor, and what they cost and grant."""

    warnings: list[Notice]
    errors: list[Notice] = field(default_factory=list)
    bonus_sources: list[tuple[str, list[dict[str, Any]]]] = field(default_factory=list)
    public: list[dict[str, Any]] = field(default_factory=list)
    kept: list[ArmorModInstall] = field(default_factory=list)
    nuyen: int = 0
    specs: dict[str, dict[str, Any]] = field(
        default_factory=lambda: {item["id"]: item for item in catalog().get("armor_mods") or []}
    )
    armor_specs: dict[str, dict[str, Any]] = field(
        default_factory=lambda: {item["id"]: item for item in catalog().get("armor") or []}
    )

    def armor(self, item: dict[str, Any], mods: list[ArmorModInstall]) -> None:
        """Fit one armor's mods, then total its capacity and armor value."""
        item["mod_armor"] = 0
        item.pop("stack_with", None)
        rating = int(item.get("rating") or 1)
        armor_cost = str((self.armor_specs.get(str(item.get("armor_id") or "")) or {}).get("cost") or "0")
        fit = _Fit(
            cap_max_base=eval_formula(str(item.get("armorcapacity") or "0"), rating, 0),
            parent_unit=int(eval_formula(armor_cost, rating, 0)),
        )
        for inst in mods:
            spec = self.specs.get(inst.mod_id)
            if spec:
                self._mod(item, inst, spec, fit)
        cap_max = fit.cap_max_base + fit.cap_bonus
        used = fit.used
        item["capacity_used"] = int(used) if used == int(used) else used
        item["capacity_max"] = int(cap_max) if cap_max == int(cap_max) else cap_max
        item["mods"] = [row for row in self.public if row.get("parent_id") == item["id"]]
        extra = int(item.get("mod_armor") or 0)
        if extra:
            item["armor_value"] = int(item.get("armor_value") or 0) + extra
        if current_rules().enforce_capacity and used > cap_max + 1e-9:
            self.errors.append(
                notice(
                    "engine.gear.capacityOver",
                    name=term(str(item["name"])),
                    used=f"{item['capacity_used']:g}",
                    max=f"{item['capacity_max']:g}",
                )
            )

    def _mod(self, item: dict[str, Any], inst: ArmorModInstall, spec: dict[str, Any], fit: _Fit) -> None:
        rating = max(1, int(inst.rating or 1)) if inst.included else _clamp_rating(spec, inst.rating)
        inst.rating = rating
        refusal = self._refusal(item, inst, spec, fit)
        if refusal:
            self.warnings.append(notice(refusal, name=term(str(spec["name"])), host=term(str(item["name"]))))
            return
        cap_cost = (
            0.0
            if inst.included
            else armor_plugin_capacity(
                str(spec.get("armorcapacity") or ""), rating, extras={"Capacity": fit.cap_max_base}
            )
        )
        extra, _additive = parse_armor_value(str(spec.get("armor") or "0"), rating)
        cost = (
            0
            if inst.included
            else int(eval_formula(str(spec.get("cost") or "0"), rating, 0, extras={"Armor Cost": fit.parent_unit}))
        )
        self.nuyen += cost
        if cap_cost < 0:
            fit.cap_bonus += -cap_cost
        else:
            fit.used += cap_cost
        if extra:
            item["mod_armor"] = int(item.get("mod_armor") or 0) + extra
        item["nuyen"] = int(item.get("nuyen") or 0) + cost
        fit.seen_names.add(spec["name"])
        if spec.get("unique"):
            fit.seen_unique.add(str(spec["unique"]))
        inst.wireless = bool(inst.wireless)
        display_nodes = list(spec.get("bonus") or [])
        if spec.get("wirelessbonus") and inst.wireless:
            display_nodes = display_nodes + list(spec.get("wirelessbonus") or [])
        if item.get("equipped"):
            nodes = substitute_rating(display_nodes, rating)
            if nodes:
                self.bonus_sources.append((spec["name"], nodes))
        self.kept.append(inst)
        self.public.append(_mod_row(item, inst, spec, rating, cost, cap_cost, display_nodes))

    @staticmethod
    def _refusal(item: dict[str, Any], inst: ArmorModInstall, spec: dict[str, Any], fit: _Fit) -> str:
        """The warning that keeps the mod off this armor, or "" when it fits."""
        if spec["name"] in fit.seen_names or (spec.get("unique") and spec["unique"] in fit.seen_unique):
            return "engine.gear.duplicateMod"
        # what the armor came with (a Victory liner picked at purchase)
        # is on it, whatever its category says
        if not inst.included and not armor_mod_fits(spec, item, fit.seen_names - {spec["name"]}):
            return "engine.gear.doesNotFit"
        return ""


def _mod_row(
    item: dict[str, Any],
    inst: ArmorModInstall,
    spec: dict[str, Any],
    rating: int,
    cost: int,
    cap_cost: float,
    display_nodes: list[dict[str, Any]],
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": inst.id,
        "mod_id": spec["id"],
        "name": spec["name"],
        "category": spec.get("category") or "General",
        "parent_id": inst.parent_id,
        "included": bool(inst.included),
        "rating": rating,
        "rating_max": int(spec.get("maxrating") or 0),
        "nuyen": cost,
        "capacity_cost": int(cap_cost) if cap_cost == int(cap_cost) else cap_cost,
        "armor": spec.get("armor") or "0",
        "unique": spec.get("unique") or "",
        "wireless": inst.wireless,
        "has_wireless": bool(spec.get("wirelessbonus")),
        "avail": spec.get("avail") or "",
        "source": spec.get("source") or "",
        "page": spec.get("page") or "",
    }
    if any(node.get("tag") == "selectarmor" for node in spec.get("bonus") or []):
        inst.stack_with = str(inst.stack_with or "")
        row["select_armor"] = True
        row["stack_with"] = inst.stack_with
        if inst.stack_with:
            item["stack_with"] = inst.stack_with
    special = special_armor_from_nodes(display_nodes, rating)
    if special:
        row["special_armor"] = special
    limits = limit_modifiers_from_nodes(display_nodes, rating)
    if limits:
        row["limit_modifiers"] = limits
    return row


def _stack_value(item: dict[str, Any]) -> int:
    """What a Custom Fit (Stack) piece adds on top of the armor it was
    tailored to: its `+N` `<armoroverride>`, 0 when it has none."""
    value, additive = parse_armor_value(str(item.get("armoroverride") or ""), int(item.get("rating") or 1))
    return value if additive else 0


def armor_encumbrance(load: int, strength: int) -> int:
    """SR5 p.169: −1 AGI and REA for every 2 full points of stacked armor
    past Strength — Chummer's `ArmorEncumbrance`, 0 up to STR + 1."""
    if load <= strength + 1:
        return 0
    return -((load - strength) // 2)


def _recompute_worn_armor(
    armor_items: list[dict[str, Any]], strength: int | None = None
) -> tuple[int, str, list[Notice], int]:
    """Only the best piece counts, plus every `+N` accessory (SR5 p.169).

    Custom Fit (Stack) (RG p.59) is the exception: a piece tailored to another
    worn piece adds its `+N` override to that one instead of competing with it
    — Chummer's `ArmorRating` stacking pass.

    What stacks on top — accessories and tailored pieces together — counts up
    to the wearer's Strength (SR5 p.169), as Chummer caps it; `strength=None`
    leaves it uncapped, as does `<uncappedarmoraccessorybonuses>`.

    The fourth value is the AGI/REA encumbrance from that same stack, taken
    before the cap (see `armor_encumbrance`).
    """
    warnings: list[Notice] = []
    worn = [item for item in armor_items if item.get("equipped")]
    accessories = [item for item in worn if item.get("additive")]
    add_total = sum(int(item.get("armor_value") or 0) for item in accessories)
    bases = [item for item in worn if not item.get("additive")]
    # base piece id -> the pieces stacked onto it
    stacked_on: dict[str, list[dict[str, Any]]] = {}
    for item in bases:
        target = str(item.get("stack_with") or "")
        if not target or not _stack_value(item):
            continue
        host = next((other for other in bases if other is not item and other.get("name") == target), None)
        if host is not None:
            stacked_on.setdefault(str(host["id"]), []).append(item)

    rules = current_rules()

    def capped(stack: int) -> int:
        if strength is None or rules.uncapped_armor_accessory_bonuses:
            return stack
        return min(stack, max(0, strength))

    best: dict[str, Any] | None = None
    best_value = 0
    for item in bases:
        stack = add_total + sum(_stack_value(p) for p in stacked_on.get(str(item["id"]), []))
        value = int(item.get("armor_value") or 0) + capped(stack)
        if best is None or value > best_value:
            best, best_value = item, value
    riders = stacked_on.get(str(best["id"]), []) if best is not None else []
    stack_total = add_total + sum(_stack_value(p) for p in riders)
    if best is None:
        best_value = capped(add_total)
    if capped(stack_total) < stack_total:
        warnings.append(notice("engine.gear.armorAccessoryCapped", bonus=stack_total, strength=int(strength or 0)))
    if len(bases) > 1 + len(riders):
        warnings.append(notice("engine.gear.armorHighestOnly"))
    # what each stacking piece still adds once the cap has taken its share,
    # in the order they are listed
    room = capped(stack_total)
    for item in armor_items:
        if not item.get("equipped"):
            item["contributes"] = 0
        elif item is best:
            item["contributes"] = int(item.get("armor_value") or 0)
        elif item.get("additive") or any(item is rider for rider in riders):
            full = int(item.get("armor_value") or 0) if item.get("additive") else _stack_value(item)
            item["contributes"] = min(full, room)
            room -= item["contributes"]
        else:
            item["contributes"] = 0
    worn_name = str(best.get("name") or "") if best is not None else ""
    penalty = armor_encumbrance(stack_total, strength) if strength is not None and not rules.no_armor_encumbrance else 0
    if penalty:
        warnings.append(
            notice("engine.gear.armorEncumbrance", load=stack_total, strength=int(strength or 0), penalty=penalty)
        )
    return best_value, worn_name, warnings, penalty


def apply_armor_gear(
    armor_items: list[dict[str, Any]], carried_by_bucket: dict[str, list[dict[str, Any]]], errors: list[Notice]
) -> None:
    """Gear carried in a piece of armor takes its `<armorcapacity>` from the
    armor's capacity — once per item of its quantity — as the mods do
    (Chummer's `Armor.CapacityRemaining`), and is listed on the armor it
    sits in. What came with the armor takes none."""
    for item in armor_items:
        carried = []
        for bucket, rows in carried_by_bucket.items():
            for row in rows:
                if row.get("parent_id") == item["id"]:
                    # which list the row lives in, for the front end to edit it
                    row["bucket"] = bucket
                    carried.append(row)
        item["gear"] = carried
        if not carried:
            continue
        before = float(item.get("capacity_used") or 0)
        used = round(
            before + sum(float(row.get("armor_capacity") or 0) * int(row.get("qty") or 1) for row in carried), 4
        )
        cap_max = float(item.get("capacity_max") or 0)
        item["capacity_used"] = int(used) if used == int(used) else used
        # armor without capacity (a Hat) is not checked, as in Chummer; when
        # the mods alone went over, that error is already in the list
        if current_rules().enforce_capacity and cap_max > 0 and used > cap_max + 1e-9 and before <= cap_max + 1e-9:
            errors.append(
                notice(
                    "engine.gear.capacityOver",
                    name=term(str(item["name"])),
                    used=f"{used:g}",
                    max=f"{cap_max:g}",
                )
            )
