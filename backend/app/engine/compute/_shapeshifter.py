"""A shapeshifter's other body: the metahuman form beside the animal one.

The animal is the metatype and what the character is built in (Chummer's
`Character.Create`). The two forms share the points bought, `base` and
`karma`, and differ only in each attribute's range: Chummer's `CopyAttribute`
carries both over and takes the minimum and maximums from the metavariant. A
rating in the metahuman form is therefore the animal rating moved by the
difference of the two minimums, held inside the form's own range.

Movement in that form is the metavariant's `alt` rates, with the form's AGI.

At the table the character is in one form or the other
(`state.shapeshifter_form`). In the metahuman form `ctx.attr_totals` and
`ctx.total` are moved into it, so everything worked from them — pools,
limits, condition monitors, initiative, weapon damage — follows the body.
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


def in_metahuman_form(ctx: Ctx) -> bool:
    return ctx.state.shapeshifter_form == "metahuman" and _metahuman_ranges(ctx) is not None


def _form_total(ctx: Ctx, form: dict[str, Any], key: str, total: int) -> int:
    own = form["attributes"][key]
    shift = int(own["min"]) - int(ctx.attrs_spec[key]["min"])
    bonus = int(ctx.attr_max_bonus.get(key) or 0)
    return min(max(total + shift, int(own["min"])), int(own["aug"]) + bonus)


def into_metahuman_form(ctx: Ctx, totals: dict[str, int]) -> dict[str, int]:
    """`totals` (the animal's) as the metahuman form has them, when the
    character is in that form; otherwise unchanged."""
    found = _metahuman_ranges(ctx) if in_metahuman_form(ctx) else None
    if found is None:
        return totals
    _animal, form = found
    out = dict(totals)
    for key in FORM_ATTRIBUTES:
        if key in out and form["attributes"].get(key) and ctx.attrs_spec.get(key):
            out[key] = _form_total(ctx, form, key, int(out[key]))
    return out


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
        total = _form_total(ctx, form, key, int(ctx.animal_total.get(key) or 0))
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


def animal_form(ctx: Ctx, animal_movement: Any) -> dict[str, Any] | None:
    """``derived["metatype_info"]["animal_form"]``: the animal's totals and
    movement, which ``totals`` / ``movement`` stop being in the other form."""
    found = _metahuman_ranges(ctx)
    if found is None:
        return None
    animal, _form = found
    totals = {key: int(ctx.animal_total[key]) for key in FORM_ATTRIBUTES if key in ctx.animal_total}
    return {"name": animal["name"], "totals": totals, "movement": animal_movement}
