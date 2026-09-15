"""Attaching a player's picks onto the bonus rows `compute` collected.

A `<bonus>` can name a slot without filling it — a Matrix action to boost, an
adept power to grant — and the fill comes from `quality_extras` /
`mentor_extras` / a gear row's `extra`. These three run after the effects pass
has gathered the rows and before anything reads them.
"""

from __future__ import annotations

from typing import Any

from ...improvements import EffectsDict
from ...improvements.effect_rows import ActionDicePoolRow
from ...models import CharacterState
from ...notices import Notice, notice, term
from ..lookups import _item_by_id, _power_by_name


def bind_action_dice_pools(
    effects: EffectsDict,
    qualities: list[dict[str, Any]],
    state: CharacterState,
) -> list[ActionDicePoolRow]:
    """Attach chosen Matrix action names from quality_extras onto actiondicepool rows."""
    by_name = {q["name"]: q for q in qualities}
    extras = state.quality_extras or {}
    out: list[ActionDicePoolRow] = []
    for row in effects.get("action_dice_pools") or []:
        item: ActionDicePoolRow = {
            "category": str(row.get("category") or ""),
            "name": str(row.get("name") or "").strip(),
            "bonus": int(row.get("bonus") or 0),
            "source": str(row.get("source") or ""),
        }
        if not item["name"] and row.get("needs_action"):
            spec = by_name.get(item["source"])
            if spec:
                item["name"] = str(extras.get(spec["id"]) or "").strip()
        if item["bonus"] and item["name"]:
            out.append(item)
    effects["action_dice_pools"] = out
    return out


def bind_select_powers(
    effects: EffectsDict,
    qualities: list[dict[str, Any]],
    state: CharacterState,
    warnings: list[Notice],
    mentor_name: str = "",
) -> None:
    by_name = {q["name"]: q for q in qualities}
    mentor_extras = state.mentor_extras or {}
    quality_extras = state.quality_extras or {}
    mentor_prefix = f"{mentor_name}: " if mentor_name else ""

    for slot in effects.get("select_power_slots") or []:
        source = str(slot.get("source") or "").strip()
        options = list(slot.get("options") or [])
        rating = max(1, int(slot.get("rating") or 1))
        open_select = bool(slot.get("open_select"))
        if not options and not open_select:
            continue
        picked = ""
        if mentor_prefix and source.startswith(mentor_prefix):
            choice_name = source[len(mentor_prefix) :]
            picked = str(mentor_extras.get(choice_name) or "").strip()
        elif open_select:
            for inst in state.gear or []:
                spec = _item_by_id("gear", inst.gear_id)
                if not spec or str(spec.get("name") or "") != source:
                    continue
                picked = str(inst.extra or "").strip()
                rating = max(1, int(inst.rating or 1))
                break
        else:
            spec = by_name.get(source)
            if spec:
                picked = str(quality_extras.get(spec["id"]) or "").strip()
        if not picked:
            warnings.append(notice("engine.adept.powerPick", source=term(source)))
            continue
        if options and picked not in options:
            warnings.append(notice("engine.adept.powerNotAllowed", source=term(source), picked=term(picked)))
            continue
        if open_select and not _power_by_name(picked):
            warnings.append(notice("engine.adept.powerUnknown", source=term(source), power=term(picked)))
            continue
        effects["grant_powers"].append(
            {
                "source": source,
                "name": picked,
                "rating": rating,
                "extra": "",
            }
        )


def free_powers_from_grants(
    effects: EffectsDict,
    warnings: list[Notice],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in effects.get("grant_powers") or []:
        name = str(row.get("name") or "").strip()
        source = str(row.get("source") or "").strip()
        spec = _power_by_name(name)
        if not spec:
            warnings.append(notice("engine.adept.powerUnknown", source=term(source), power=term(name)))
            continue
        out.append(
            {
                "power_id": spec["id"],
                "name": spec["name"],
                "rating": max(1, int(row.get("rating") or 1)),
                "extra": str(row.get("extra") or "").strip(),
                "source": source,
            }
        )
    return out
