"""An A.I.'s programs (DT p.158), priced as Chummer's CharacterCreate does.

Each program the A.I. bought costs `<karmanewaiprogram>` (5), or
`<karmanewaiadvancedprogram>` (8) for one in the Advanced Programs category.
The talent hands out no free ones (`<ainormalprogramlimit>` and
`<aiadvancedprogramlimit>` appear on no talent), so every bought program is
paid for. A career raise is billed the same price, so one sum serves both.

`Inherent Program` (DT p.148) adds one common or hacking program that cannot
be deleted and costs nothing (`selectinherentaiprogram`, `blnCanDelete =
false`). The pick is the quality's extra, as a sprite is Sprite Affinity's.
"""

from __future__ import annotations

from typing import Any, TypedDict

from ..data_loader import INHERENT_CATEGORIES, catalog
from ..models import CharacterState
from ..notices import Notice, notice, term, terms
from ..rules import current_rules

#: The tab an A.I.'s metatype enables (`<enabletab>advanced programs`).
AI_PROGRAMS_TAB = "advanced programs"


class AIProgramsBundle(TypedDict):
    public: list[dict[str, Any]]
    karma: int
    warnings: list[Notice]
    errors: list[Notice]


def empty_ai_programs() -> AIProgramsBundle:
    return {"public": [], "karma": 0, "warnings": [], "errors": []}


def _programs() -> dict[str, dict[str, Any]]:
    return {str(p["id"]): p for p in catalog().get("ai_programs") or []}


def _row(spec: dict[str, Any], *, row_id: str, extra: str, free: bool, granted_by: str) -> dict[str, Any]:
    rules = current_rules()
    price = rules.karma_ai_advanced_program if spec.get("advanced") else rules.karma_ai_program
    return {
        "id": row_id,
        "program_id": spec["id"],
        "name": spec["name"],
        "category": spec.get("category") or "",
        "advanced": bool(spec.get("advanced")),
        "required": list(spec.get("required") or []),
        "needs_extra": bool(spec.get("needs_extra")),
        "extra": extra,
        "free": free,
        "granted_by": granted_by,
        "karma": 0 if free else price,
        "source": spec.get("source"),
        "page": spec.get("page"),
    }


def resolve_ai_programs(
    state: CharacterState,
    enabled_tabs: set[str],
    qualities: list[dict[str, Any]],
    *,
    career: bool,
) -> AIProgramsBundle:
    """The A.I.'s programs, what they cost, and what is wrong with them.

    A character whose metatype has no program tab keeps none — the way a
    non-technomancer's complex forms are dropped — so leaving the A.I. behind
    does not leave a karma bill behind with it.
    """
    out = empty_ai_programs()
    if AI_PROGRAMS_TAB not in enabled_tabs:
        state.ai_programs = []
        return out
    by_id = _programs()
    by_name = {str(p["name"]): p for p in by_id.values()}
    extras = state.quality_extras or {}
    for quality in qualities:
        if not any(node.get("tag") == "selectinherentaiprogram" for node in quality.get("bonus") or []):
            continue
        picked = str(extras.get(quality["id"]) or "").strip()
        spec = by_name.get(picked)
        if spec is None or spec.get("category") not in INHERENT_CATEGORIES:
            # unpicked, or not one it may pick: the quality's own check says so
            continue
        out["public"].append(
            _row(spec, row_id=f"inherent:{quality['id']}", extra="", free=True, granted_by=str(quality["name"]))
        )
    kept = []
    for inst in state.ai_programs:
        spec = by_id.get(inst.program_id)
        if spec is None:
            continue
        kept.append(inst)
        extra = (inst.extra or "").strip()
        if spec.get("needs_extra") and not extra:
            out["warnings"].append(notice("engine.aiPrograms.pickExtra", name=term(str(spec["name"]))))
        out["public"].append(_row(spec, row_id=inst.id, extra=extra, free=False, granted_by=""))
    state.ai_programs = kept
    owned = {row["name"] for row in out["public"]}
    if not career:
        # `<required>` is a purchase-time gate in Chummer (SelectAIProgram
        # asks `RequirementsMetAsync` when the program is added); in creation
        # the engine is the only gate there is, as for qualities.
        for row in out["public"]:
            needed = row["required"]
            if needed and not owned & set(needed):
                out["errors"].append(notice("engine.aiPrograms.prereq", name=term(row["name"]), needed=terms(needed)))
    out["karma"] = sum(int(row["karma"]) for row in out["public"])
    return out
