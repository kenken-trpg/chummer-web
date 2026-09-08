"""Drug / toxin / chemical effects used at play time.

``drugcomponents.xml`` expresses a drug's effect with its own small ``<bonus>``
vocabulary; :func:`_drug_effect_nodes` translates that into the tags
:func:`app.improvements.apply_bonus_nodes` understands, and
:func:`apply_active_drugs` folds every drug flagged ``active`` on the character
into the shared ``effects`` dict (plus a per-drug summary for the derived blob).
"""

from __future__ import annotations

from typing import Any

from ...data_loader import catalog, drug_effect_summary, drug_node_value, eval_formula
from ...improvements import EffectsDict, apply_bonus_nodes
from ...models import CharacterState
from ...notices import Notice, notice

_DRUG_CATEGORIES = {"Drugs", "Toxins", "Chemicals"}
_DRUG_LIMIT_TAG = {"physical": "physicallimit", "mental": "mentallimit", "social": "sociallimit"}


def _drug_effect_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Translate ``drugcomponents.xml`` <bonus> vocab into the tags that
    :func:`apply_bonus_nodes` understands."""
    out: list[dict[str, Any]] = []
    for node in nodes:
        tag = node.get("tag")
        fields = node.get("fields") or {}
        val = drug_node_value(node)
        if not val:
            continue
        if tag == "attribute":
            name = str(fields.get("name") or "").upper()
            if name:
                out.append({"tag": "specificattribute", "fields": {"name": name, "bonus": val}})
        elif tag == "limit":
            kind = _DRUG_LIMIT_TAG.get(str(fields.get("name") or node.get("value") or "").strip().lower())
            if kind:
                out.append({"tag": kind, "value": val})
        elif tag in ("initiativedice", "initiativepass"):
            out.append({"tag": "initiativepass", "value": val})
        elif tag == "initiative":
            out.append({"tag": "initiative", "value": val})
        elif tag == "specificskill":
            name = str(fields.get("name") or node.get("value") or "").strip()
            if name:
                out.append({"tag": "specificskill", "fields": {"name": name, "bonus": val}})
    return out


def _format_drug_duration(expr: str, bod: int) -> Notice | None:
    """The duration as a notice, or ``None`` when the catalog gives none.

    A formula with a die in it (``{D6}``) is rolled at its average, so those
    get the `Avg` variant of the key — the "（平均）" used to be glued on here.
    """
    if not expr:
        return None
    approx = "{D6}" in expr or "{d6}" in expr
    seconds = int(eval_formula(expr, 1, 0.0, {"BOD": max(1, int(bod)), "D6": 3.5}))
    if seconds <= 0:
        return None
    if seconds >= 3600:
        unit, value = "hours", f"{seconds / 3600:g}"
    elif seconds >= 60:
        unit, value = "minutes", str(seconds // 60)
    else:
        unit, value = "seconds", str(seconds)
    return notice(f"engine.drugDuration.{unit}{'Avg' if approx else ''}", value=value)


def apply_active_drugs(
    state: CharacterState,
    attr_totals: dict[str, int],
    effects: EffectsDict,
) -> list[dict[str, Any]]:
    """Fold the ``<bonus>`` of every drug/toxin flagged ``active`` into ``effects``
    and return a per-drug summary for the derived output."""
    specs = {item["id"]: item for item in catalog().get("gear") or []}
    bod = int(attr_totals.get("BOD") or 0)
    active: list[dict[str, Any]] = []
    for inst in state.gear or []:
        if not getattr(inst, "active", False):
            continue
        spec = specs.get(inst.gear_id)
        if not spec or (spec.get("category") or "") not in _DRUG_CATEGORIES:
            continue
        nodes = list(spec.get("drug_bonus") or [])
        if not nodes:
            continue
        # The name alone: bonus nodes are only folded in while the drug is
        # active, so there is nothing to tell it apart from.
        apply_bonus_nodes(_drug_effect_nodes(nodes), effects, str(spec["name"]))
        active.append(
            {
                "name": spec["name"],
                "category": spec.get("category") or "Drugs",
                "speed": spec.get("drug_speed") or "",
                "vectors": list(spec.get("drug_vectors") or []),
                "duration": _format_drug_duration(str(spec.get("drug_duration") or ""), bod),
                "effect": drug_effect_summary(nodes),
            }
        )
    return active
