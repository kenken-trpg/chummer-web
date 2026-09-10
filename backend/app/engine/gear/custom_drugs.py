"""Drugs the character mixed instead of buying (CF p.190).

A custom drug is one Foundation plus any number of Blocks and Enhancers.
There is no catalog entry for the result — the components *are* the drug — so
everything a bought drug reads off its gear spec is summed here instead: cost,
availability, addiction rating and threshold, onset, duration, crash damage,
and the effects themselves.

The effects stay in the ``drugcomponents.xml`` ``<bonus>`` vocabulary the
premade drugs already speak, so ``gear/drugs.py`` folds an active custom drug
into ``effects`` through exactly the same translation — Narco's lift and the
granted-quality expansion included.

Imports only ``catalog`` / the avail helpers (``..data_loader``), models and
notices — never back into ``app.engine``.
"""

from __future__ import annotations

from typing import Any

from ...data_loader import catalog, drug_effect_summary, eval_formula, format_avail, parse_avail, sum_avail
from ...models import CharacterState, CustomDrugInstall
from ...notices import Notice, ParamValue, notice, term, ui

FOUNDATION = "Foundation"
# CF p.190: a drug takes effect in 9 seconds unless a component says otherwise.
BASE_SPEED_SECONDS = 9
# CF p.191: a Block above level 2 may not raise an attribute its Foundation
# lowers. Chummer applies the check from `Level + 1 > 2`, i.e. the third row.
_BLOCK_LEVEL_CHECKED = 2


def _effect_at(spec: dict[str, Any], level: int) -> dict[str, Any] | None:
    """The component's effect for the level it was added at.

    Chummer's ``ActiveDrugEffect``: no matching level means the component
    contributes nothing at all, not that it falls back to level 0.
    """
    for effect in spec.get("effects") or []:
        if int(effect.get("level") or 0) == level:
            return dict(effect)
    return None


def _attribute_totals(nodes: list[dict[str, Any]]) -> dict[str, int]:
    out: dict[str, int] = {}
    for node in nodes:
        if node.get("tag") != "attribute":
            continue
        fields = node.get("fields") or {}
        name = str(fields.get("name") or "").upper()
        raw = str(fields.get("value") or "").strip()
        try:
            value = int(raw)
        except ValueError:
            continue
        if name:
            out[name] = out.get(name, 0) + value
    return out


def _blocked_by_foundation(
    foundation: dict[str, Any] | None,
    spec: dict[str, Any],
    level: int,
) -> str:
    """The attribute a high Block level fights its Foundation over, if any.

    A Foundation that lowers an attribute caps what a Block may do to it: past
    level 2 the Block may not push that same attribute back up (CF p.191).
    """
    if not foundation or level < _BLOCK_LEVEL_CHECKED:
        return ""
    base = _effect_at(foundation, 0)
    effect = _effect_at(spec, level)
    if not base or not effect:
        return ""
    lowered = {name for name, value in _attribute_totals(base["nodes"]).items() if value < 0}
    raised = {name for name, value in _attribute_totals(effect["nodes"]).items() if value > 0}
    return next(iter(sorted(lowered & raised)), "")


def _grade_by_name(name: str) -> dict[str, Any]:
    grades = catalog().get("drug_component_grades") or []
    for grade in grades:
        if str(grade.get("name") or "") == name:
            return grade
    return grades[0] if grades else {"name": name, "cost_multiplier": 1.0, "addiction_threshold": 0}


def _component_cost(spec: dict[str, Any], level: int) -> int:
    """``<cost>`` with the component's level substituted, as Chummer does."""
    raw = str(spec.get("cost") or "0").strip().lstrip("+")
    return int(eval_formula(raw.replace("{Level}", str(level)).replace("Level", str(level)), 1, 0))


def _resolve_one(
    inst: CustomDrugInstall,
    specs: dict[str, dict[str, Any]],
    warnings: list[Notice],
    errors: list[Notice],
) -> tuple[dict[str, Any], int]:
    """One mixed drug → (public row, nuyen for the quantity held).

    Mutates ``inst``: parts pointing at components that are gone are dropped,
    and the quantity is clamped, the same way the gear resolvers do it.
    """
    name = str(inst.name or "").strip()
    label: ParamValue = term(name) if name else ui("engine.customDrug.unnamed")
    qty = max(1, int(inst.qty or 1))
    inst.qty = qty

    kept: list[Any] = []
    parts: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    foundation: dict[str, Any] | None = None
    for part in inst.parts or []:
        spec = specs.get(str(part.component_id or ""))
        if not spec:
            continue
        level = max(0, int(part.level or 0))
        effect = _effect_at(spec, level)
        if not effect:
            warnings.append(notice("engine.customDrug.noSuchLevel", name=term(str(spec["name"])), level=str(level + 1)))
            continue
        if spec["category"] == FOUNDATION and foundation is not None:
            errors.append(notice("engine.customDrug.oneFoundation", drug=label))
            continue
        limit = int(spec.get("limit") or 0)
        counts[spec["id"]] = counts.get(spec["id"], 0) + 1
        if limit and counts[spec["id"]] > limit:
            errors.append(
                notice("engine.customDrug.tooMany", drug=label, name=term(str(spec["name"])), limit=str(limit))
            )
            continue
        if spec["category"] == FOUNDATION:
            foundation = spec
        kept.append(part)
        parts.append({"spec": spec, "level": level, "effect": effect})
    inst.parts = kept

    # The Foundation may be added after a Block, so the CF p.191 check runs
    # once the whole mix is known rather than as each part is read.
    for mixed in parts:
        if mixed["spec"]["category"] == FOUNDATION:
            continue
        clash = _blocked_by_foundation(foundation, mixed["spec"], mixed["level"])
        if clash:
            errors.append(
                notice(
                    "engine.customDrug.blockFightsFoundation",
                    drug=label,
                    name=term(str(mixed["spec"]["name"])),
                    foundation=term(str((foundation or {}).get("name") or "")),
                    attribute=clash,
                )
            )
    if parts and foundation is None:
        errors.append(notice("engine.customDrug.missingFoundation", drug=label))

    grade = _grade_by_name(str(inst.grade or "Standard"))
    nodes = [node for part in parts for node in part["effect"]["nodes"]]
    parts_cost = sum(_component_cost(part["spec"], part["level"]) for part in parts)
    # Half up, like every other price in the engine — `round()` would send
    # Street Cooked's 72.5¥ down to 72 and 73.5¥ down to 73.
    unit_cost = int(parts_cost * grade["cost_multiplier"] + 0.5)
    avail_value, avail_suffix = sum_avail(
        [(value, suffix) for value, suffix, _add in (parse_avail(str(p["spec"].get("avail") or "")) for p in parts)]
    )
    threshold = sum(int(part["spec"].get("addiction_threshold") or 0) for part in parts)
    row = {
        "id": inst.id,
        "name": name,
        "grade": grade["name"],
        "qty": qty,
        "active": bool(inst.active),
        "nuyen": unit_cost * qty,
        "avail": format_avail(avail_value, avail_suffix),
        # The pair the chargen availability check reads (`engine/limits.py`);
        # a mixed drug is bought like anything else, so it is subject to it.
        "avail_value": avail_value,
        "avail_suffix": avail_suffix,
        "addiction_rating": sum(int(part["spec"].get("addiction_rating") or 0) for part in parts),
        # A negative total would read as "cannot get hooked", which is not what
        # Pharmaceutical's -1 means; the floor keeps it at the lowest step.
        "addiction_threshold": max(0, threshold + int(grade.get("addiction_threshold") or 0)) if parts else 0,
        "crash_damage": sum(int(part["effect"]["crash_damage"] or 0) for part in parts),
        "speed": (BASE_SPEED_SECONDS + sum(int(part["effect"]["speed"] or 0) for part in parts)) if parts else 0,
        "duration": sum(int(part["effect"]["duration"] or 0) for part in parts),
        "infos": [part["effect"]["info"] for part in parts if part["effect"]["info"]],
        "components": [
            {
                "component_id": part["spec"]["id"],
                "name": part["spec"]["name"],
                "category": part["spec"]["category"],
                "level": part["level"],
            }
            for part in parts
        ],
        "bonus": nodes,
        "effect": drug_effect_summary(nodes),
        "source": "CF",
        "page": "190",
    }
    return row, row["nuyen"]


def resolve_custom_drugs(state: CharacterState) -> tuple[list[dict[str, Any]], int, list[Notice], list[Notice]]:
    """Every mixed drug the character holds → (rows, nuyen, warnings, errors)."""
    specs = {str(item["id"]): item for item in catalog().get("drug_components") or []}
    rows: list[dict[str, Any]] = []
    warnings: list[Notice] = []
    errors: list[Notice] = []
    nuyen = 0
    for inst in state.custom_drugs or []:
        row, cost = _resolve_one(inst, specs, warnings, errors)
        rows.append(row)
        nuyen += cost
    return rows, nuyen, warnings, errors
