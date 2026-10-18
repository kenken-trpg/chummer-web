"""The Critter Powers tab: powers an Infected or a drake buys with karma.

An Infected quality (RF p.126, the DTR powers) or a Dracoform quality (HS)
opens the tab (`<enabletab>critter`) and names the category it sells from
(`<limitcritterpowercategory>` Infected / Drake). Chummer's SelectCritterPower
lists the powers in those categories whose `<required>` / `<forbidden>` the
character meets; CharacterCreate takes each bought power's `<karma>` off the
karma total, and CritterPower.Create runs its `<bonus>` at the rating picked.

The powers a quality or the metatype grants are not here: those are derived
from the quality (`critter_power_effects`) and the metatype (`power_grants`).
"""

from __future__ import annotations

from typing import Any, TypedDict

from ..data_loader import catalog
from ..improvements._common import substitute_rating
from ..models import CharacterState
from ..notices import Notice, notice, term
from .qualities import bought_source, without_source
from .requirements import requirement_tree_met

#: The tab a quality enables (`<enabletab>critter`).
CRITTER_TAB = "critter"


class CritterPowersBundle(TypedDict):
    public: list[dict[str, Any]]
    #: ids of the powers the tab offers now: in an open category, and with
    #: their `<required>` / `<forbidden>` met
    offer: list[str]
    categories: list[str]
    karma: int
    warnings: list[Notice]
    errors: list[Notice]


def empty_critter_powers() -> CritterPowersBundle:
    return {"public": [], "offer": [], "categories": [], "karma": 0, "warnings": [], "errors": []}


def _stock() -> dict[str, dict[str, Any]]:
    return {str(row["id"]): row for row in catalog().get("buyable_critter_powers") or []}


def _needs_extra(spec: dict[str, Any]) -> bool:
    return any(node.get("tag") == "selecttext" for node in spec.get("bonus") or [])


def _label(spec: dict[str, Any], extra: str) -> str:
    return f"{spec['name']} ({extra})" if extra else str(spec["name"])


def bought_power_sources(state: CharacterState, enabled_tabs: set[str]) -> list[tuple[str, list[dict[str, Any]]]]:
    """What the bought powers do, for the effects pass — and the purchases
    themselves dropped when nothing opens the tab any more, the way an A.I.'s
    programs go with the A.I., so a karma bill does not outlive the quality."""
    if CRITTER_TAB not in enabled_tabs:
        state.critter_powers = []
        return []
    stock = _stock()
    state.critter_powers = [inst for inst in state.critter_powers if inst.power_id in stock]
    out = []
    for inst in state.critter_powers:
        spec = stock[inst.power_id]
        rating = int(inst.rating or 0) if spec.get("has_rating") else 0
        out.append((_label(spec, (inst.extra or "").strip()), substitute_rating(list(spec.get("bonus") or []), rating)))
    return out


def resolve_critter_powers(
    state: CharacterState,
    enabled_tabs: set[str],
    categories: set[str],
    req_ctx: dict[str, Any],
    *,
    career: bool,
) -> CritterPowersBundle:
    """The bought powers as the sheet lists them, their karma, and what the tab
    offers. `<required>` / `<forbidden>` and the category are purchase-time
    gates in Chummer, so they are errors in creation only — as for qualities
    and an A.I.'s programs."""
    out = empty_critter_powers()
    if CRITTER_TAB not in enabled_tabs:
        return out
    stock = _stock()
    out["categories"] = sorted(categories)
    out["offer"] = [
        power_id
        for power_id, spec in stock.items()
        if spec.get("category") in categories
        and requirement_tree_met(spec.get("required_tree"), req_ctx)
        and not (spec.get("forbidden_tree") and requirement_tree_met(spec.get("forbidden_tree"), req_ctx))
    ]
    for inst in state.critter_powers:
        spec = stock[inst.power_id]
        extra = (inst.extra or "").strip()
        rating = int(inst.rating or 0) if spec.get("has_rating") else None
        out["public"].append(
            {
                "id": inst.id,
                "power_id": spec["id"],
                "name": spec["name"],
                "label": _label(spec, extra),
                "category": spec.get("category") or "",
                "type": spec.get("type") or "",
                "action": spec.get("action") or "",
                "range": spec.get("range") or "",
                "duration": spec.get("duration") or "",
                "karma": int(spec.get("karma") or 0),
                "has_rating": bool(spec.get("has_rating")),
                "rating": rating,
                "needs_extra": _needs_extra(spec),
                "extra": extra,
                "source": spec.get("source"),
                "page": spec.get("page"),
            }
        )
        name = term(str(spec["name"]))
        if _needs_extra(spec) and not extra:
            out["warnings"].append(notice("engine.critterPowers.pickExtra", name=name))
        if spec.get("has_rating") and not rating:
            out["warnings"].append(notice("engine.critterPowers.pickRating", name=name))
        if career:
            continue
        if spec.get("category") not in categories:
            out["errors"].append(
                notice("engine.critterPowers.category", name=name, category=term(str(spec.get("category") or "")))
            )
            continue
        own = without_source(req_ctx, bought_source(inst.id))
        if not requirement_tree_met(spec.get("required_tree"), own):
            out["errors"].append(notice("engine.critterPowers.prereq", name=name))
        elif spec.get("forbidden_tree") and requirement_tree_met(spec.get("forbidden_tree"), own):
            out["errors"].append(notice("engine.critterPowers.forbidden", name=name))
    out["karma"] = sum(int(row["karma"]) for row in out["public"])
    return out
