"""The routes that write a character out to a file, and the checks that go with
them.

Every format here has to be read back out of the file by something else —
Chummer, the キャラシテンプレート, Foundry VTT — so each download has a sibling
`.../check` that says what the round trip would change. They share
`_content_disposition`, which is the one thing a download needs that a plain
JSON answer does not.
"""

from __future__ import annotations

import json
import re
from urllib.parse import quote

from fastapi import APIRouter, Request, Response

from ..chummer_export import state_to_chum5
from ..chummer_export.check import roundtrip_differences
from ..fvtt_export import state_to_fvtt
from ..fvtt_export.check import export_omissions
from ..models import FvttExportRequest, StateRequest
from ..xlsx_export import state_to_xlsx
from ..xlsx_export.check import roundtrip_differences as xlsx_differences
from .deploy import _IMPORT_RATE_LIMIT, limiter

router = APIRouter()


def _content_disposition(name: str, ext: str = "chum5") -> str:
    """RFC 6266 attachment header. Starlette encodes header values as latin-1,
    so a Japanese character name in a bare `filename="..."` raises at send time
    (500). Emit an ASCII-safe `filename=` fallback plus a percent-encoded
    `filename*=UTF-8''` that carries the real name."""
    stem = (name or "").strip() or "character"
    ascii_stem = re.sub(r"[^A-Za-z0-9._ -]", "_", stem) or "character"
    encoded = quote(f"{stem}.{ext}", safe="")
    return f"attachment; filename=\"{ascii_stem}.{ext}\"; filename*=UTF-8''{encoded}"


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


@router.post("/api/characters/fvtt")
@limiter.limit(_IMPORT_RATE_LIMIT)
def export_fvtt(request: Request, req: FvttExportRequest) -> Response:
    """Download JSON for Foundry VTT shadowrun5e's Chummer importer (0.34.5).

    Limited like the .chum5 download: it computes the character when the
    state arrives without `derived`."""
    body = json.dumps(state_to_fvtt(req.state, req.locale), ensure_ascii=False, indent=2)
    return Response(
        content=body.encode("utf-8"),
        media_type="application/json",
        headers={"Content-Disposition": _content_disposition(req.state.name, "json")},
    )


@router.post("/api/characters/fvtt/check")
@limiter.limit(_IMPORT_RATE_LIMIT)
def check_fvtt_export(request: Request, req: StateRequest) -> dict:
    """Known export omissions; does not simulate Foundry's importer."""
    return {"differences": export_omissions(req.state)}


@router.post("/api/characters/xlsx")
@limiter.limit(_IMPORT_RATE_LIMIT)
def export_xlsx(request: Request, req: StateRequest) -> Response:
    """Download the character as a シャドウラン_キャラシテンプレート-shaped .xlsx.

    Not the template itself — that is 音の兔 様's work, and the .xlsx it downloads
    as has dead Google Sheets formulas throughout — but a workbook with its sheet
    names and its input cells, which this app reads back.
    """
    body = state_to_xlsx(req.state)
    return Response(
        content=body,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": _content_disposition(req.state.name, "xlsx")},
    )


@router.post("/api/characters/xlsx/check")
@limiter.limit(_IMPORT_RATE_LIMIT)
def check_xlsx_export(request: Request, req: StateRequest) -> dict:
    """What the character would lose on a template round trip.

    Asked alongside the download, like the .chum5 check, and limited the same
    way: one call writes the file, reads it back and computes the character
    twice over.
    """
    return {"differences": xlsx_differences(req.state)}


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
