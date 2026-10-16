"""A shapeshifter's other body: the metahuman form beside the animal one.

The animal is the metatype and what the character is built in (Chummer's
`Character.Create`). The two forms share the points bought, `base` and
`karma`, and differ only in each attribute's range: Chummer's `CopyAttribute`
carries both over and takes the minimum and maximums from the metavariant. A
rating in the metahuman form is therefore the animal rating moved by the
difference of the two minimums, held inside the form's own range.

Movement in that form is the metavariant's `alt` rates, with the form's AGI.
"""

from __future__ import annotations

from typing import Any

from ..lookups import find_metatype
from .context import Ctx
from .finalize import resolve_movement

#: The attributes whose range the forms can differ in. MAG, RES and ESS are
#: the same in every form in the data, and a form's essence is the body's.
FORM_ATTRIBUTES = ("BOD", "AGI", "REA", "STR", "CHA", "INT", "LOG", "WIL", "EDG")


def _metahuman_ranges(ctx: Ctx) -> tuple[dict[str, Any], dict[str, Any]] | None:
    animal = find_metatype(ctx.state.metatype, None)
    if animal.get("category") != "Shapeshifter" or not ctx.state.metavariant:
        return None
    form = next((mv for mv in animal.get("metavariants") or [] if mv["name"] == ctx.state.metavariant), None)
    return (animal, form) if form else None


def metahuman_form(ctx: Ctx) -> dict[str, Any] | None:
    """``derived["metatype_info"]["metahuman_form"]``, or None for anyone
    who is not a shapeshifter."""
    found = _metahuman_ranges(ctx)
    if found is None:
        return None
    _animal, form = found
    attributes: dict[str, dict[str, int]] = {}
    for key in FORM_ATTRIBUTES:
        own = form["attributes"].get(key)
        built = ctx.attrs_spec.get(key)
        if not own or not built:
            continue
        shift = int(own["min"]) - int(built["min"])
        bonus = int(ctx.attr_max_bonus.get(key) or 0)
        low, high, aug = int(own["min"]), int(own["max"]) + bonus, int(own["aug"]) + bonus
        rating = min(max(int(ctx.ratings.get(key) or 0) + shift, low), high)
        total = min(max(int(ctx.total.get(key) or 0) + shift, low), aug)
        attributes[key] = {"rating": rating, "total": total, "min": low, "max": high, "aug": aug}
    rates = {kind: form.get(f"{kind}_alt") or "" for kind in ("walk", "run", "sprint")}
    movement = None
    if all(rates.values()):
        # as the body's own: meat AGI on the ground, totals in the water
        meat_agi = attributes["AGI"]["rating"] + ctx.attr_bonus("AGI") if "AGI" in attributes else 0
        movement = resolve_movement(
            rates,
            ctx.effects,
            meat_agi,
            swim_agi=attributes.get("AGI", {}).get("total", 0),
            swim_str=attributes.get("STR", {}).get("total", 0),
        )
    return {"name": form["name"], "attributes": attributes, "movement": movement}
