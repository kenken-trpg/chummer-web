from __future__ import annotations

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
from .models import CharacterCreate, CharacterPatch
from .store import (
    create_character,
    delete_character,
    export_character,
    get_character,
    import_character,
    list_characters,
    public_catalog,
    update_character,
)

# --- deploy-time knobs (env-overridable) --------------------------------------
_ALLOWED_ORIGINS = [
    o.strip()
    for o in (os.environ.get("ALLOWED_ORIGINS") or "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if o.strip()
]
_MAX_REQUEST_BYTES = int(os.environ.get("MAX_REQUEST_BYTES") or 8 * 1024 * 1024)
_RATE_LIMIT = os.environ.get("RATE_LIMIT") or "120/minute"
_IMPORT_RATE_LIMIT = os.environ.get("IMPORT_RATE_LIMIT") or "20/minute"


def _client_ip(request: Request) -> str:
    """Best-effort caller identity for rate limiting. Behind Cloudflare / a
    reverse proxy the socket peer is the proxy, so prefer the forwarded header."""
    fwd = request.headers.get("cf-connecting-ip") or request.headers.get("x-forwarded-for", "")
    return fwd.split(",")[0].strip() or (request.client.host if request.client else "anon")


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
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/characters")
def create(payload: CharacterCreate | None = None) -> dict:
    return create_character(payload).model_dump()


@app.get("/api/characters")
def roster() -> list[dict]:
    return list_characters()


@app.delete("/api/characters/{cid}")
def delete(cid: str) -> dict:
    delete_character(cid)
    return {"ok": True}


@app.get("/api/characters/{cid}")
def read(cid: str) -> dict:
    try:
        return get_character(cid).model_dump()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="character not found") from exc


@app.patch("/api/characters/{cid}")
def patch(cid: str, payload: CharacterPatch) -> dict:
    try:
        return update_character(cid, payload).model_dump()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="character not found") from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/characters/{cid}/export")
def export_json(cid: str) -> dict:
    try:
        return export_character(cid)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="character not found") from exc


@app.get("/api/characters/{cid}/chummer")
def export_chummer(cid: str) -> Response:
    """Download a Chummer5a-compatible .chum5 (plain XML)."""
    try:
        state = get_character(cid)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="character not found") from exc
    xml = state_to_chum5(state)
    fname = (state.name or "character").replace('"', "") + ".chum5"
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
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"取り込みに失敗しました: {exc}") from exc
