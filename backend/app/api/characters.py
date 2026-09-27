"""The character state routes: making one, and recomputing one.

Stateless: the client owns the `CharacterState` and sends it whole; nothing
about a character is kept here. The file formats live next door — `import_routes`
takes a visitor's file, `export_routes` writes one — and both of those end up
back at `compute_state` through `import_character`, which is why this is the
module the other two lean on rather than the other way round.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from ..characters import apply_patch, compute_state, new_character
from ..dataset_store import lookup
from ..models import CharacterCreate, CharacterState, PatchRequest
from ..notices import NoticeError, notice

_log = logging.getLogger("chummer_web")

router = APIRouter()


@router.post("/api/characters/new")
def create(payload: CharacterCreate | None = None) -> dict:
    return new_character(payload).model_dump()


@router.post("/api/characters/patch")
def patch(req: PatchRequest) -> dict:
    """Merge `patch` onto `state` (talent / priority / career normalisation) and
    recompute. With no `patch` it's a bare recompute of the given state."""
    _require_dataset(req.state)
    try:
        if req.patch is None:
            return compute_state(req.state).model_dump()
        return apply_patch(req.state, req.patch).model_dump()
    except NoticeError:
        raise
    except Exception as exc:
        _log.exception("patch failed")
        raise HTTPException(status_code=400, detail=notice("api.patchFailed")) from exc


def _require_dataset(state: CharacterState) -> None:
    """409 when the character's custom data is not merged here yet.

    The browser holds the files and sends only their hash, so a cold server —
    or one that has evicted the set — has to ask for them. `dataset` in the
    detail tells the client which set to upload; it retries the same request
    afterwards.
    """
    settings = state.settings
    # No `dataset` means the folder was never loaded — the settings name custom
    # data the user has not supplied. That is a state to compute in (with the
    # vendored data, and the editor saying the ruleset is incomplete), not one
    # to refuse: refusing would leave the character uncomputable rather than
    # merely missing its extra entries.
    if not settings.customdata or not settings.dataset:
        return
    if lookup(settings.dataset, settings.customdata):
        return
    raise HTTPException(
        status_code=409,
        detail=notice("api.customDataMissing", dataset=settings.dataset),
    )
