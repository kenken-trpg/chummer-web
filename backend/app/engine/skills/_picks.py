"""`<selectskill>` / `<hardwires>` picks, and the ware accuracy bonuses that need one."""

from __future__ import annotations

from typing import Any

from ...improvements import EffectsDict, _as_int, substitute_rating
from ...models import CharacterState
from ...notices import Notice, notice, term
from ..bundle_types import SkillPicks
from ..lookups import _quality_by_id, _ware_by_id
from ..selects import (
    parse_hardwires_spec,
    parse_selectskill_spec,
    selectskill_options,
)

# Bonus tags that hand the user a skill to choose. `<hardwires>` is a
# `<selectskill>` whose value is a rating rather than a dice bonus, so it rides
# the same picker instead of growing a second one.
SKILL_PICK_TAGS = {"selectskill", "hardwires"}


def _ware_bonus_nodes(kind: str, inst: Any) -> tuple[str, list[dict[str, Any]]] | None:
    """The ware's name and the bonus nodes it applies as installed."""
    ware = _ware_by_id(kind, inst.ware_id)
    if not ware:
        return None
    nodes = list(ware.get("bonus") or [])
    if inst.wireless:
        nodes.extend(ware.get("wirelessbonus") or [])
    return str(ware["name"]), substitute_rating(nodes, int(inst.rating or 1))


def _needs_accuracy_pick(node: dict[str, Any]) -> bool:
    fields = node.get("fields") or {}
    return (
        node.get("tag") == "weaponskillaccuracy"
        and "selectskill" in fields
        and not str(fields.get("name") or "").strip()
    )


def ware_accuracy_picks(
    state: CharacterState, skip_ids: set[str] | frozenset[str] = frozenset()
) -> list[tuple[str, str, str, str, dict[str, Any]]]:
    """``<weaponskillaccuracy>`` on ware whose skill is the player's to name —
    Cyberlimb Optimization (CF p.87): +1 Accuracy with one chosen skill.

    Upstream spells it that way rather than as a `<selectskill>` so the bonus
    lands on the limit, not the pool; the pick itself is the same one. Returns
    ``(key, ware name, kind, install id, node)``. The key is numbered apart
    (``acc{n}``) so the plain `<selectskill>` picks on the same ware keep the
    keys they were saved under. Ware in a vehicle mod (`skip_ids`) is the
    vehicle's, not the character's, and gets no pick.
    """
    rows: list[tuple[str, str, str, str, dict[str, Any]]] = []
    for kind in ("cyberware", "bioware"):
        for inst in getattr(state, kind):
            if inst.id in skip_ids:
                continue
            resolved = _ware_bonus_nodes(kind, inst)
            if not resolved:
                continue
            name, nodes = resolved
            index = 0
            for node in nodes:
                if not _needs_accuracy_pick(node):
                    continue
                rows.append((f"ware:{inst.id}:acc{index}", name, kind, inst.id, node))
                index += 1
    return rows


def bind_ware_skill_accuracy(
    effects: EffectsDict,
    state: CharacterState,
    skills_data: dict[str, Any],
    skip_ids: set[str] | frozenset[str] = frozenset(),
) -> None:
    """Fold the picked skills of :func:`ware_accuracy_picks` into
    ``effects["weapon_skill_accuracy"]``. This runs before the weapons are
    priced, long before :func:`resolve_skill_picks`, so it reads the pick
    straight off the state; an out-of-range pick is left for that pass to
    report and simply does nothing here."""
    picks = state.skill_picks or {}
    rows = effects.setdefault("weapon_skill_accuracy", [])
    for key, source, _kind, _inst_id, node in ware_accuracy_picks(state, skip_ids):
        picked = str(picks.get(key) or "").strip()
        if not picked:
            continue
        spec = parse_selectskill_spec(_accuracy_select_node(node))
        if picked not in selectskill_options(spec, skills_data, {}):
            continue
        bonus = _as_int((node.get("fields") or {}).get("value"))
        if bonus:
            rows.append({"name": picked, "bonus": bonus, "source": source})


def _accuracy_select_node(node: dict[str, Any]) -> dict[str, Any]:
    """The `<selectskill>` inside a `<weaponskillaccuracy>`, shaped like a
    top-level one: its filters sit in ``field_attrs``, its value is the
    Accuracy, not dice."""
    attrs = dict((node.get("field_attrs") or {}).get("selectskill") or {})
    return {"tag": "selectskill", "attrs": attrs, "fields": {}}


def _extra_kind(spec: dict[str, Any]) -> str:
    return str(spec.get("extra_kind") or "")


#: The bioware whose pick `<reflexrecorderoptimization>` widens. Both printings
#: ("Reflex Recorder", "Reflex Recorder (2050)") carry the same skill pick.
REFLEX_RECORDER = "Reflex Recorder"


def _default_free_skills(picked: str, skills_data: dict[str, Any]) -> list[str]:
    """What a Reflex Recorder's pick covers once optimized (CF p.165).

    The recorded skill defaults without the −1, and so does the rest of its
    skill group — a skill outside any group covers only itself.
    """
    catalog_skills = skills_data.get("skills") or []
    spec = next((item for item in catalog_skills if item.get("name") == picked), None)
    group = str((spec or {}).get("skillgroup") or "").strip()
    if not group:
        return [picked] if spec else []
    return [str(item["name"]) for item in catalog_skills if str(item.get("skillgroup") or "") == group]


def resolve_skill_picks(
    state: CharacterState,
    skills_data: dict[str, Any],
    skill_totals: dict[str, int],
    *,
    reflex_optimized: bool = False,
    skip_ids: set[str] | frozenset[str] = frozenset(),
) -> SkillPicks:
    slots: list[dict[str, Any]] = []
    default_free: list[str] = []
    warnings: list[Notice] = []
    skill_max: dict[str, int] = {}
    pick_bonus: dict[str, int] = {}
    pick_notes: dict[str, list[str]] = {}
    hardwire_active: dict[str, int] = {}
    hardwire_knowledge: dict[str, int] = {}
    picks = state.skill_picks or {}

    def add_slot(
        key: str, source: str, source_kind: str, source_id: str, node: dict[str, Any], accuracy: int = 0
    ) -> None:
        hardwire = node.get("tag") == "hardwires"
        spec = parse_hardwires_spec(node) if hardwire else parse_selectskill_spec(node)
        options = selectskill_options(spec, skills_data, skill_totals)
        picked = picks.get(key) or ""
        if picked and picked not in options:
            warnings.append(notice("engine.skills.pickInvalid", source=term(source), picked=term(picked)))
            picked = ""
        if not picked:
            warnings.append(notice("engine.skills.pickSkill", source=term(source)))
        elif spec.get("bonus"):
            pick_bonus[picked] = int(pick_bonus.get(picked, 0)) + int(spec["bonus"])
            note = spec.get("condition") or ""
            if note:
                notes = pick_notes.setdefault(picked, [])
                if note not in notes:
                    notes.append(note)
        if picked and spec.get("max"):
            skill_max[picked] = int(skill_max.get(picked, 0)) + int(spec["max"])
        rating = int(spec.get("rating") or 0)
        if picked and rating:
            bucket = hardwire_knowledge if spec.get("knowledgeskills") else hardwire_active
            bucket[picked] = max(int(bucket.get(picked) or 0), rating)
        # Narrow: the geneware speaks of the recorder's skill, nobody else's.
        optimized = reflex_optimized and source_kind == "bioware" and source.startswith(REFLEX_RECORDER)
        covered = _default_free_skills(picked, skills_data) if optimized and picked else []
        for name in covered:
            if name not in default_free:
                default_free.append(name)
        slots.append(
            {
                "key": key,
                "source": source,
                "source_kind": source_kind,
                "source_id": source_id,
                "picked": picked,
                "bonus": int(spec.get("bonus") or 0),
                "max": int(spec.get("max") or 0),
                "rating": rating,
                "options": options,
                "knowledgeskills": bool(spec.get("knowledgeskills")),
                "default_free": bool(covered),
                "accuracy": accuracy,
            }
        )

    for qid in state.quality_ids:
        quality = _quality_by_id(qid)
        if not quality:
            continue
        index = 0
        for node in quality.get("bonus") or []:
            if node.get("tag") not in SKILL_PICK_TAGS:
                continue
            add_slot(f"quality:{qid}:{index}", quality["name"], "quality", qid, node)
            index += 1

    for kind in ("cyberware", "bioware"):
        for inst in getattr(state, kind):
            resolved = _ware_bonus_nodes(kind, inst)
            if not resolved:
                continue
            name, nodes = resolved
            index = 0
            for node in nodes:
                if node.get("tag") not in SKILL_PICK_TAGS:
                    continue
                add_slot(f"ware:{inst.id}:{index}", name, kind, inst.id, node)
                index += 1

    # The Accuracy picks: the same picker, but the value is Accuracy on the
    # chosen skill's weapons (bound earlier, in `bind_ware_skill_accuracy`),
    # so the slot carries it as `accuracy` and adds no dice.
    for key, name, kind, inst_id, node in ware_accuracy_picks(state, skip_ids):
        add_slot(
            key,
            name,
            kind,
            inst_id,
            _accuracy_select_node(node),
            accuracy=_as_int((node.get("fields") or {}).get("value")),
        )

    return {
        "slots": slots,
        "warnings": warnings,
        "skill_max_bonus": skill_max,
        "skill_bonus": pick_bonus,
        "skill_bonus_notes": pick_notes,
        "hardwires": {"active": hardwire_active, "knowledge": hardwire_knowledge},
        "no_default_penalty": sorted(default_free),
    }
