"""The character routes. Stateless: the client owns the `CharacterState` and
sends it whole; nothing about a character is kept here."""

from __future__ import annotations

import logging
import re
from urllib.parse import quote

from fastapi import APIRouter, Body, HTTPException, Request, Response

from ..characters import apply_patch, compute_state, import_character, new_character
from ..chummer_export import state_to_chum5
from ..chummer_export.check import roundtrip_differences
from ..chummer_import import chum5_to_state
from ..customdata import dataset_hash
from ..dataset_store import MAX_UPLOAD_BYTES, lookup, remember
from ..fvtt_import import fvtt_to_state
from ..models import CharacterCreate, CharacterState, CustomDataUpload, PatchRequest, StateRequest
from ..notices import NoticeError, notice
from ..settings_file import parse_settings_upload
from .deploy import _IMPORT_RATE_LIMIT, limiter

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


@router.post("/api/customdata")
@limiter.limit(_IMPORT_RATE_LIMIT)
def upload_customdata(request: Request, body: CustomDataUpload) -> dict:
    """Take a `customdata/` tree and merge it, once, under its content hash.

    `files` is `{path relative to customdata/: XML text}` — the browser has
    the paths from a directory pick, and sends them verbatim so the merge sees
    the same layout Chummer would. JSON rather than multipart: the contents
    are text, the paths matter more than filenames do, and it costs no extra
    dependency.

    Nothing is written to disk. The merge is kept in a small in-memory cache
    that a restart empties; the client re-uploads when told to.
    """
    files = {path: text.encode("utf-8") for path, text in body.files.items()}
    if not files:
        raise HTTPException(status_code=400, detail=notice("api.customDataEmpty"))
    if sum(len(raw) for raw in files.values()) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=notice("api.customDataTooLarge"))
    dataset = dataset_hash(files)
    _, report = remember(dataset, body.customdata, files)
    return {
        "dataset": dataset,
        "applied": report.applied,
        "skipped": [{"source": source, "reason": reason} for source, reason in report.skipped],
        # itemised so the table can check a pack against what it claims to do:
        # 62 `source, page` edits is a different thing from 62 new weapons
        "changes": [
            {"file": c.file, "entry": c.entry, "action": c.action, "fields": list(c.fields)} for c in report.changes
        ],
        "truncated": report.truncated,
        "ignored": sorted(set(report.ignored)),
    }


@router.post("/api/settings/parse")
@limiter.limit(_IMPORT_RATE_LIMIT)
def parse_settings(request: Request, body: bytes = Body(..., media_type="application/octet-stream")) -> dict:
    """Read a Chummer `settings/*.xml` into a `SettingsState`.

    Parsing runs here rather than in the browser because every other piece of
    Chummer XML knowledge lives in Python, and the "which knobs did this file
    change that we cannot honour" answer needs the vendored `settings.xml` to
    compare against. The client stores the result and sends it back as part of
    the character; nothing about the upload is kept server-side.
    """
    try:
        settings, build_method = parse_settings_upload(body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=notice("api.settingsParseFailed")) from exc
    except Exception as exc:  # noqa: BLE001
        _log.exception("settings parse failed")
        raise HTTPException(status_code=400, detail=notice("api.settingsParseFailed")) from exc
    return {"settings": settings.model_dump(), "build_method": build_method}


def _content_disposition(name: str) -> str:
    """RFC 6266 attachment header. Starlette encodes header values as latin-1,
    so a Japanese character name in a bare `filename="..."` raises at send time
    (500). Emit an ASCII-safe `filename=` fallback plus a percent-encoded
    `filename*=UTF-8''` that carries the real name."""
    stem = (name or "").strip() or "character"
    ascii_stem = re.sub(r"[^A-Za-z0-9._ -]", "_", stem) or "character"
    encoded = quote(f"{stem}.chum5", safe="")
    return f"attachment; filename=\"{ascii_stem}.chum5\"; filename*=UTF-8''{encoded}"


@router.post("/api/characters/chummer")
@limiter.limit(_IMPORT_RATE_LIMIT)
def export_chummer(request: Request, req: StateRequest) -> Response:
    """Download a Chummer5a-compatible .chum5 (plain XML) for the given state."""
    xml = state_to_chum5(req.state)
    return Response(
        content=xml,
        media_type="application/xml",
        headers={"Content-Disposition": _content_disposition(req.state.name)},
    )


@router.post("/api/characters/chummer/check")
@limiter.limit(_IMPORT_RATE_LIMIT)
def check_chummer_export(request: Request, req: StateRequest) -> dict:
    """What the character would lose on a .chum5 round trip, as notices —
    asked for alongside the download so the player hears about it before
    they take the file to Chummer.

    Limited like the download itself: one call exports, re-imports and
    computes the character, the heaviest thing any route does, and the
    default 120/minute would let one client keep a core busy with it."""
    return {"differences": roundtrip_differences(req.state)}


@router.post("/api/characters/import")
@limiter.limit(_IMPORT_RATE_LIMIT)
def import_json(request: Request, payload: dict) -> dict:
    try:
        return import_character(payload).model_dump()
    except NoticeError:
        raise
    except Exception as exc:
        _log.exception("JSON import failed")
        raise HTTPException(status_code=400, detail=notice("api.importJsonFailed")) from exc


@router.post("/api/characters/import-chummer")
@limiter.limit(_IMPORT_RATE_LIMIT)
def import_chummer(request: Request, body: bytes = Body(..., media_type="application/octet-stream")) -> dict:
    """Import a Chummer5a .chum5 / .chum5lz save. Returns the character plus a
    list of things that could not be mapped."""
    try:
        state, warnings = chum5_to_state(body)
        state.pop("_warnings", None)
        char = import_character(state)
        return {"character": char.model_dump(), "warnings": warnings}
    except NoticeError as exc:
        # chummer_import raises this with an actionable, user-facing notice.
        raise HTTPException(status_code=400, detail=exc.notice) from exc
    except Exception as exc:  # noqa: BLE001
        _log.exception("chum5 import failed")
        raise HTTPException(status_code=400, detail=notice("api.importChummerFailed")) from exc


@router.post("/api/characters/import-fvtt")
@limiter.limit(_IMPORT_RATE_LIMIT)
def import_fvtt(request: Request, payload: dict) -> dict:
    """Import a Foundry VTT shadowrun5e character actor (its Export Data JSON).
    Returns the character plus a list of things that could not be mapped."""
    try:
        state, warnings = fvtt_to_state(payload)
        char = import_character(state)
        return {"character": char.model_dump(), "warnings": warnings}
    except NoticeError as exc:
        raise HTTPException(status_code=400, detail=exc.notice) from exc
    except Exception as exc:  # noqa: BLE001
        _log.exception("FVTT import failed")
        raise HTTPException(status_code=400, detail=notice("api.importFvttFailed")) from exc
