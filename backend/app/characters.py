"""Character mutations: create, patch, import.

The backend is stateless — characters live in the browser (IndexedDB). Every
function here is pure: a client-supplied `CharacterState` in, a computed
`CharacterState` out. Nothing is stored, so nothing here has an id to look up.

`apply_patch` is the one with real rules in it; the rest are thin.
"""

from __future__ import annotations

import uuid

from .engine import (
    ADEPT_TALENTS,
    BUILD_METHOD_KARMA,
    COMPLEX_FORM_TALENTS,
    FOCUS_TALENTS,
    MAG_TALENTS,
    RES_TALENTS,
    SPELL_TALENTS,
    SPIRIT_TALENTS,
    SPRITE_TALENTS,
    compute,
    default_attributes,
    find_metatype,
    normalize_build_method,
    resolve_talent_for_method,
    sanitize_quality_ids,
    snapshot_career_baseline,
    talent_special,
)
from .models import CharacterCreate, CharacterPatch, CharacterState, Priorities


def _new_state(payload: CharacterCreate) -> CharacterState:
    meta = find_metatype(payload.metatype, None)
    method = normalize_build_method(payload.build_method)
    state = CharacterState(
        id=str(uuid.uuid4()),
        name=payload.name,
        build_method=method,
        priorities=payload.priorities or Priorities(),
        metatype=payload.metatype,
        attributes=default_attributes(meta),
    )
    return compute(state)


def new_character(payload: CharacterCreate | None = None) -> CharacterState:
    """A fresh, computed character. Persisting it is the client's job."""
    return _new_state(payload or CharacterCreate())


def compute_state(state: CharacterState) -> CharacterState:
    """Recompute `derived` for a client-supplied state (no merge)."""
    return compute(state)


def _apply_talent_ratings(data: dict) -> None:
    talent = resolve_talent_for_method(data["priorities"]["Talent"], data.get("talent"), data.get("build_method"))
    data["talent"] = talent["name"]
    key, start = talent_special(talent)
    if normalize_build_method(data.get("build_method")) == BUILD_METHOD_KARMA and key:
        start = 1
    attrs = dict(data.get("attributes") or {})
    attrs["MAG"] = start if key == "MAG" else 0
    attrs["RES"] = start if key == "RES" else 0
    data["attributes"] = attrs


def apply_patch(state: CharacterState, patch: CharacterPatch) -> CharacterState:
    """Merge a `CharacterPatch` onto a client-supplied state, run the talent /
    priority / career normalisation, and return the recomputed state."""
    data = state.model_dump()
    old_letter = state.priorities.Talent
    old_talent = state.talent
    old_method = normalize_build_method(state.build_method)
    was_career = bool(state.career)
    updates = patch.model_dump(exclude_unset=True)
    if "priorities" in updates and updates["priorities"] is not None:
        data["priorities"] = updates.pop("priorities")
    if "options" in updates and updates["options"] is not None:
        current = dict(data.get("options") or {})
        current.update(updates.pop("options"))
        data["options"] = current
    data.update({k: v for k, v in updates.items() if v is not None})
    if "career" in updates:
        now_career = bool(updates["career"])
        data["career"] = now_career
        if now_career and not was_career:
            data["career_baseline"] = snapshot_career_baseline(state).model_dump()
            # Seed reward ledger from existing earned totals so history stays coherent.
            if not (data.get("reward_log") or []) and (
                int(data.get("karma_earned") or 0) or int(data.get("nuyen_earned") or 0)
            ):
                data["reward_log"] = [
                    {
                        "id": str(uuid.uuid4()),
                        "label": "キャリア開始時の報酬合計",
                        "karma": max(0, int(data.get("karma_earned") or 0)),
                        "nuyen": max(0, int(data.get("nuyen_earned") or 0)),
                    }
                ]
        elif not now_career:
            data["career_baseline"] = None
    if "reward_log" in updates and updates["reward_log"] is not None:
        log = list(updates["reward_log"] or [])
        data["reward_log"] = log
        data["karma_earned"] = sum(max(0, int(row.get("karma") or 0)) for row in log if isinstance(row, dict))
        data["nuyen_earned"] = sum(max(0, int(row.get("nuyen") or 0)) for row in log if isinstance(row, dict))
    if "tradition_id" in updates:
        data["tradition_id"] = updates.pop("tradition_id") or None
    if "stream_id" in updates:
        data["stream_id"] = updates.pop("stream_id") or None
    if "quality_ids" in updates:
        data["quality_ids"], _ = sanitize_quality_ids(list(data.get("quality_ids") or []))
    if patch.metatype or patch.metavariant is not None:
        meta = find_metatype(data["metatype"], data.get("metavariant"))
        data["attributes"] = default_attributes(meta)
    data["build_method"] = normalize_build_method(data.get("build_method"))
    talent = resolve_talent_for_method(data["priorities"]["Talent"], data.get("talent"), data.get("build_method"))
    data["talent"] = talent["name"]
    method_changed = old_method != data["build_method"]
    if old_letter != data["priorities"]["Talent"] or old_talent != data["talent"] or patch.metatype or method_changed:
        _apply_talent_ratings(data)
        if data["talent"] not in ADEPT_TALENTS:
            data["adept_powers"] = []
            data["mystic_pp"] = 0
            data["qi_foci"] = []
            data["adept_enhancements"] = []
        if data["talent"] not in MAG_TALENTS:
            data["mentor_id"] = None
            data["mentor_choices"] = []
            data["mentor_extras"] = {}
            data["initiate_grade"] = 0
            data["initiations"] = []
        if data["talent"] not in SPELL_TALENTS:
            data["spells"] = []
            data["tradition_id"] = None
        if data["talent"] not in SPIRIT_TALENTS:
            data["spirits"] = []
        if data["talent"] not in FOCUS_TALENTS:
            data["foci"] = []
        if data["talent"] not in COMPLEX_FORM_TALENTS and data["talent"] not in RES_TALENTS:
            data["complex_forms"] = []
            data["stream_id"] = None
        if data["talent"] not in RES_TALENTS:
            data["submersion_grade"] = 0
            data["submersions"] = []
        if data["talent"] not in SPRITE_TALENTS:
            data["sprites"] = []
    return compute(CharacterState.model_validate(data))


def import_character(payload: dict) -> CharacterState:
    """Take a raw state dict (our JSON export, or a Chummer-derived dict),
    stamp a fresh id, and return it computed."""
    payload = dict(payload)
    payload["id"] = str(uuid.uuid4())
    return compute(CharacterState.model_validate(payload))
