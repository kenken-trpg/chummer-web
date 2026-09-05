from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from collections.abc import Awaitable, Callable
from functools import lru_cache
from typing import NamedTuple
from urllib.parse import quote

from fastapi import Body, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .catalog_view import public_catalog
from .characters import apply_patch, compute_state, import_character, new_character
from .chummer_export import state_to_chum5
from .chummer_import import chum5_to_state
from .logging_config import configure_logging, new_request_id, request_id_var
from .models import CharacterCreate, PatchRequest, StateRequest

configure_logging()

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
    version="0.2.0",
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
        _log.warning("request body too large", extra={"content_length": int(cl)})
        return JSONResponse({"detail": "request body too large"}, status_code=413)
    return await call_next(request)


# Added last, so it is the *outermost* middleware: the id has to exist before
# anything else can log, and the access line has to see the status the body-size
# guard and the rate limiter actually returned.
@app.middleware("http")
async def _request_context(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Give the request an id, log one line when it finishes, hand the id back.

    An id from the edge wins so a trace spans the whole hop chain — but only
    from a header a proxy we trust would have written, on the same footing as
    the forwarded-IP rule above.
    """
    incoming = request.headers.get("x-request-id", "").strip() if _TRUSTED_PROXY_HOPS > 0 else ""
    # bound so a hostile client cannot write an essay into every log line
    rid = incoming[:64] if incoming else new_request_id()
    token = request_id_var.set(rid)
    started = time.perf_counter()
    try:
        try:
            response = await call_next(request)
        except Exception:
            # uvicorn logs the traceback itself; this is the line that carries
            # the id and the timing, so the 500 is findable from the caller's side
            _log.exception("request failed", extra={"method": request.method, "path": request.url.path})
            raise
        duration_ms = round((time.perf_counter() - started) * 1000, 1)
        # The message is readable on its own (text mode is what you tail in
        # dev); the same values repeat as fields so `LOG_FORMAT=json` is
        # queryable without parsing the sentence back apart.
        _log.info(
            "%s %s -> %s in %sms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            extra={
                "method": request.method,
                # path only — a query string is not ours to log
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
                "client": _client_ip(request),
            },
        )
        response.headers["X-Request-ID"] = rid
        return response
    finally:
        request_id_var.reset(token)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


class _CachedCatalog(NamedTuple):
    body: bytes
    etag: str


@lru_cache(maxsize=1)
def _cached_catalog() -> _CachedCatalog:
    """Serialise the catalog once per process.

    The vendored Chummer data is fixed at image-build time, so the payload
    cannot change while the process lives — `data_loader.catalog()` is already
    `lru_cache`d, but `public_catalog()` rebuilt its ~2.9 MB projection on every
    request. Caching the *bytes* also gives us a stable ETag for free.

    `lru_cache` does not memoise exceptions, so a request that arrives before
    `make data` still raises `FileNotFoundError` and a later one can succeed.

    Separators and `ensure_ascii` match Starlette's `JSONResponse` so the body
    is byte-identical to what the plain `-> dict` route used to send.
    """
    body = json.dumps(public_catalog(), ensure_ascii=False, separators=(",", ":")).encode()
    return _CachedCatalog(body, f'"{hashlib.blake2b(body, digest_size=16).hexdigest()}"')


def _matches_etag(header: str, etag: str) -> bool:
    """RFC 9110 If-None-Match: `*`, or a comma-separated list where a `W/`
    prefix is ignored (weak comparison is the right one for GET)."""
    candidates = [t.strip() for t in header.split(",") if t.strip()]
    return "*" in candidates or any(c.removeprefix("W/") == etag for c in candidates)


@app.get("/api/catalog")
def catalog_endpoint(request: Request) -> Response:
    """The whole options catalog. ~2.9 MB, and the same bytes for the life of
    the process, so it is served with an ETag: a reload costs one 304 instead
    of a re-transfer. Deliberately *not* `immutable` — the URL has no version
    in it, so a container update has to be able to invalidate it.

    No gzip here on purpose. In the bundled container Caddy encodes (zstd/gzip)
    and in dev the Next proxy is on localhost; compressing at this layer would
    only take zstd off the table.
    """
    try:
        cached = _cached_catalog()
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
    headers = {"ETag": cached.etag, "Cache-Control": "no-cache"}
    if _matches_etag(request.headers.get("if-none-match", ""), cached.etag):
        return Response(status_code=304, headers=headers)
    return Response(cached.body, media_type="application/json", headers=headers)


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


def _content_disposition(name: str) -> str:
    """RFC 6266 attachment header. Starlette encodes header values as latin-1,
    so a Japanese character name in a bare `filename="..."` raises at send time
    (500). Emit an ASCII-safe `filename=` fallback plus a percent-encoded
    `filename*=UTF-8''` that carries the real name."""
    stem = (name or "").strip() or "character"
    ascii_stem = re.sub(r"[^A-Za-z0-9._ -]", "_", stem) or "character"
    encoded = quote(f"{stem}.chum5", safe="")
    return f"attachment; filename=\"{ascii_stem}.chum5\"; filename*=UTF-8''{encoded}"


@app.post("/api/characters/chummer")
def export_chummer(req: StateRequest) -> Response:
    """Download a Chummer5a-compatible .chum5 (plain XML) for the given state."""
    xml = state_to_chum5(req.state)
    return Response(
        content=xml,
        media_type="application/xml",
        headers={"Content-Disposition": _content_disposition(req.state.name)},
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
