"""The routes that take a file from the visitor.

Five character formats (JSON, .chum5, キャラシテンプレート .xlsx, that same
template fetched from its Google Sheets URL, and a Foundry VTT actor) plus the
two uploads that are not a character: a Chummer `settings/*.xml` and a
`customdata/` tree.

They have one shape in common. Every one of them is a stranger's file, so each
turns its own failure into a 400 carrying a notice the user can act on, and
`NoticeError` — raised by the importers when they know what is wrong — is let
through so its reason survives. What none of them does is keep anything: the
answer goes back to the browser, which owns the character.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Body, HTTPException, Query, Request
from limits import parse

from .. import ja_default
from ..characters import import_character
from ..chummer_import import chum5_to_state
from ..customdata import dataset_hash
from ..data_loader import catalog, using_customdata
from ..dataset_store import MAX_UPLOAD_BYTES, lookup, remember
from ..fvtt_import import fvtt_to_state
from ..models import CustomDataUpload, SettingsState, SheetUrlRequest
from ..notices import NoticeError, notice
from ..settings_file import parse_settings_upload
from ..sheets_url import fetch_sheet
from ..xlsx_import import xlsx_to_state
from .characters import require_dataset
from .deploy import _IMPORT_RATE_LIMIT, _SHEET_URL_RATE_LIMIT, _SHEET_URL_TOTAL_RATE_LIMIT, limiter

_log = logging.getLogger("chummer_web")

router = APIRouter()

#: The ceiling every caller shares on the sheet-URL import, checked alongside
#: the per-caller one on the route. Parsed once, as `catalog` does with its own.
_SHEET_URL_TOTAL_LIMIT = parse(_SHEET_URL_TOTAL_RATE_LIMIT)


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


@router.post("/api/characters/import")
@limiter.limit(_IMPORT_RATE_LIMIT)
def import_json(request: Request, payload: dict) -> dict:
    """A character's own JSON (a backup, a share link, a pasted state). It
    carries its settings, custom data included, so it waits for that data
    the way `patch` does — otherwise the items it added are dropped as
    unknown."""
    settings = payload.get("settings")
    if isinstance(settings, dict):
        try:
            wanted = SettingsState.model_validate(settings)
        except ValueError:
            wanted = None  # import_character reports a malformed state itself
        if wanted is not None:
            require_dataset(wanted)
    try:
        return import_character(payload).model_dump()
    except NoticeError:
        raise
    except Exception as exc:
        _log.exception("JSON import failed")
        raise HTTPException(status_code=400, detail=notice("api.importJsonFailed")) from exc


@router.post("/api/characters/import-chummer")
@limiter.limit(_IMPORT_RATE_LIMIT)
def import_chummer(
    request: Request,
    body: bytes = Body(..., media_type="application/octet-stream"),
    dataset: str = "",
    customdata: Annotated[list[str], Query()] = [],  # noqa: B006  (FastAPI reads the default)
) -> dict:
    """Import a Chummer5a .chum5 / .chum5lz save. Returns the character plus a
    list of things that could not be mapped.

    A save does not say which custom data it was built with — Chummer keeps
    that in the settings file it names — so an item the custom data added is
    unknown here and skipped. The browser, which may hold that settings file
    and its folder, can send the set as `dataset` + `customdata` (the same
    pair `/api/catalog` takes) and import again: the save is then read under
    it, and the character keeps it. Without one, a skip on a save that names
    a settings file of its own gets a line saying what to load."""
    overlay = None
    if dataset and customdata:
        found = lookup(dataset, list(customdata))
        if found is None:
            raise HTTPException(status_code=409, detail=notice("api.customDataMissing", dataset=dataset))
        overlay = found[0]
    try:
        with using_customdata(overlay):
            state, warnings = chum5_to_state(body)
        state.pop("_warnings", None)
        if overlay is not None:
            state.setdefault("settings", {}).update(customdata=list(customdata), dataset=dataset)
        elif _skipped_under_own_settings(state, warnings):
            warnings.append(notice("engine.import.customDataHint", name=state["settings"]["name"]))
        char = import_character(state)
        return {"character": char.model_dump(), "warnings": warnings}
    except NoticeError as exc:
        # chummer_import raises this with an actionable, user-facing notice.
        raise HTTPException(status_code=400, detail=exc.notice) from exc
    except Exception as exc:  # noqa: BLE001
        _log.exception("chum5 import failed")
        raise HTTPException(status_code=400, detail=notice("api.importChummerFailed")) from exc


def _skipped_under_own_settings(state: dict[str, Any], warnings: list[Any]) -> bool:
    """Something was skipped as unknown, and the save names a settings file
    that is not one Chummer ships — the case where the missing items most
    likely came from that file's custom data."""
    if not any(isinstance(w, dict) and w.get("key") == "engine.import.skippedUnknown" for w in warnings):
        return False
    name = str((state.get("settings") or {}).get("name") or "")
    shipped = {ja_default.PRESET["name"], *(str(p.get("name")) for p in catalog().get("settings_presets") or [])}
    return bool(name) and name not in shipped


@router.post("/api/characters/import-xlsx")
@limiter.limit(_IMPORT_RATE_LIMIT)
def import_xlsx(request: Request, body: bytes = Body(..., media_type="application/octet-stream")) -> dict:
    """Import a filled-in シャドウラン_キャラシテンプレート (.xlsx).

    Returns the character, the warnings, and `pending_gear`: the rows of the
    装備 sheet that could not be matched, each with a shortlist of what it looks
    like for the client to offer.
    """
    try:
        state, warnings, pending = xlsx_to_state(body)
        char = import_character(state)
        return {"character": char.model_dump(), "warnings": warnings, "pending_gear": pending}
    except NoticeError as exc:
        raise HTTPException(status_code=400, detail=exc.notice) from exc
    except Exception as exc:  # noqa: BLE001
        _log.exception("xlsx import failed")
        raise HTTPException(status_code=400, detail=notice("api.importXlsxFailed")) from exc


@router.post("/api/characters/import-sheet-url")
@limiter.limit(_SHEET_URL_RATE_LIMIT)
def import_sheet_url(request: Request, req: SheetUrlRequest) -> dict:
    """Import a キャラシテンプレート from its Google Sheets address.

    The same import as the uploaded .xlsx — only where the bytes come from
    differs, so the answer has the same shape, `pending_gear` included. Only a
    sheet shared with 「リンクを知っている全員」 can be read: see `sheets_url`,
    which is also the only outbound request this backend makes.
    """
    # Counted twice: the decorator above per caller, and this across all of them
    # together. An IP-keyed bucket alone is no ceiling on what this host is made
    # to fetch, because a caller with many addresses has a bucket per address.
    if not limiter.limiter.hit(_SHEET_URL_TOTAL_LIMIT, "sheet-url"):
        raise HTTPException(status_code=429, detail=notice("api.sheetUrlBusy"))
    # Outside the try below: what went wrong fetching is worth saying precisely
    # (「共有されていません」 asks something different of the player than a bad
    # URL does), and `NoticeError` already leaves here as a 400 carrying its own
    # reason — see the handler in `main`.
    body = fetch_sheet(req.url)
    try:
        state, warnings, pending = xlsx_to_state(body)
        char = import_character(state)
        return {"character": char.model_dump(), "warnings": warnings, "pending_gear": pending}
    except NoticeError as exc:
        raise HTTPException(status_code=400, detail=exc.notice) from exc
    except Exception as exc:  # noqa: BLE001
        _log.exception("sheet url import failed")
        raise HTTPException(status_code=400, detail=notice("api.importXlsxFailed")) from exc


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
