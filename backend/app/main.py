from __future__ import annotations

import logging
import os
from collections.abc import Awaitable, Callable

from fastapi import Body, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .chummer_export import state_to_chum5
from .chummer_import import chum5_to_state
from .models import CharacterCreate, PatchRequest, StateRequest
from .store import (
    apply_patch,
    compute_state,
    import_character,
    new_character,
    public_catalog,
)

# --- deploy-time knobs (env-overridable) --------------------------------------
_ALLOWED_ORIGINS = [
    o.strip()
    for o in (os.environ.get("ALLOWED_ORIGINS") or "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if o.strip()
]
# 12 MiB: a CharacterState carrying a base64 portrait (≤3 MB image) is POSTed whole
_MAX_REQUEST_BYTES = int(os.environ.get("MAX_REQUEST_BYTES") or 12 * 1024 * 1024)
_RATE_LIMIT = os.environ.get("RATE_LIMIT") or "120/minute"
_IMPORT_RATE_LIMIT = os.environ.get("IMPORT_RATE_LIMIT") or "20/minute"
# How many entries to count in from the *right* of `x-forwarded-for` to find the
# real client. 0 (default) = don't trust `x-forwarded-for` at all — a direct
# client can put anything in it, and taking the leftmost hop lets it forge a
# fresh IP per request and walk straight past every rate limit. `cf-connecting-ip`
# is always honoured (Cloudflare overwrites it). Behind a platform LB
# (Cloud Run / Fly) set 2; behind a single self-managed reverse proxy that
# appends the peer, set 1.
_TRUSTED_PROXY_HOPS = int(os.environ.get("TRUSTED_PROXY_HOPS") or 0)


def _client_ip(request: Request) -> str:
    """Best-effort caller identity for rate limiting. Only reads forwarded
    headers that infrastructure we trust is known to have written."""
    cf = (request.headers.get("cf-connecting-ip") or "").strip()
    if cf:
        return cf
    if _TRUSTED_PROXY_HOPS > 0:
        hops = [p.strip() for p in request.headers.get("x-forwarded-for", "").split(",") if p.strip()]
        if len(hops) >= _TRUSTED_PROXY_HOPS:
            return hops[-_TRUSTED_PROXY_HOPS]
    return request.client.host if request.client else "anon"


_log = logging.getLogger("chummer_web")

limiter = Limiter(key_func=_client_ip, default_limits=[_RATE_LIMIT])

app = FastAPI(
    title="Chummer Web",
    description="Unofficial Shadowrun 5e character creator. Not affiliated with Catalyst Game Labs.",
    version="0.1.0",
)

app.state.limiter = limiter
# slowapi's handler is typed for its own exception; Starlette wants (Request, Exception)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def _limit_body_size(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Reject over-large request bodies up front. Covers the normal case where a
    client sends Content-Length (browsers, httpx, curl); the .chum5lz path is
    independently bounded in chummer_import."""
    cl = request.headers.get("content-length")
    if cl and cl.isdigit() and int(cl) > _MAX_REQUEST_BYTES:
        return JSONResponse({"detail": "request body too large"}, status_code=413)
    return await call_next(request)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/catalog")
def catalog_endpoint() -> dict:
    try:
        return public_catalog()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Chummer ゲームデータが見つかりません。`make data`"
                "（または backend/scripts/fetch_chummer_data.py）を実行してください。"
                "Docker で起動している場合はイメージに同梱されているはずです。"
                f"（{exc}）"
            ),
        ) from exc


# --- stateless character ops (the client owns the CharacterState) ------------


@app.post("/api/characters/new")
def create(payload: CharacterCreate | None = None) -> dict:
    return new_character(payload).model_dump()


@app.post("/api/characters/patch")
def patch(req: PatchRequest) -> dict:
    """Merge `patch` onto `state` (talent / priority / career normalisation) and
    recompute. With no `patch` it's a bare recompute of the given state."""
    try:
        if req.patch is None:
            return compute_state(req.state).model_dump()
        return apply_patch(req.state, req.patch).model_dump()
    except Exception as exc:
        _log.exception("patch failed")
        raise HTTPException(status_code=400, detail="この変更を適用できませんでした。") from exc


@app.post("/api/characters/chummer")
def export_chummer(req: StateRequest) -> Response:
    """Download a Chummer5a-compatible .chum5 (plain XML) for the given state."""
    xml = state_to_chum5(req.state)
    fname = (req.state.name or "character").replace('"', "") + ".chum5"
    return Response(
        content=xml,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@app.post("/api/characters/import")
@limiter.limit(_IMPORT_RATE_LIMIT)
def import_json(request: Request, payload: dict) -> dict:
    try:
        return import_character(payload).model_dump()
    except Exception as exc:
        _log.exception("JSON import failed")
        raise HTTPException(status_code=400, detail="この JSON を取り込めませんでした。") from exc


@app.post("/api/characters/import-chummer")
@limiter.limit(_IMPORT_RATE_LIMIT)
def import_chummer(request: Request, body: bytes = Body(..., media_type="application/octet-stream")) -> dict:
    """Import a Chummer5a .chum5 / .chum5lz save. Returns the character plus a
    list of things that could not be mapped."""
    try:
        state, warnings = chum5_to_state(body)
        state.pop("_warnings", None)
        char = import_character(state)
        return {"character": char.model_dump(), "warnings": warnings}
    except ValueError as exc:
        # chummer_import raises ValueError with an actionable, user-facing message.
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        _log.exception("chum5 import failed")
        raise HTTPException(status_code=400, detail="この .chum5 / .chum5lz を取り込めませんでした。") from exc
