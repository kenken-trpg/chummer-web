from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import threading
import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from functools import lru_cache
from pathlib import PurePosixPath
from typing import Annotated, NamedTuple
from urllib.parse import quote

from fastapi import Body, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from .catalog_view import public_catalog
from .characters import apply_patch, compute_state, import_character, new_character
from .chummer_export import state_to_chum5
from .chummer_import import chum5_to_state
from .customdata import dataset_hash
from .data_loader import Overlay, using_customdata
from .dataset_store import MAX_UPLOAD_BYTES, lookup, remember
from .logging_config import configure_logging, new_request_id, request_id_var
from .models import CharacterCreate, CharacterState, CustomDataUpload, PatchRequest, StateRequest
from .notices import NoticeError, notice
from .settings_file import parse_settings_upload

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
# A page can legitimately fire one report per violation per load, so this is
# looser than the import limit and tighter than the default.
_CSP_REPORT_RATE_LIMIT = os.environ.get("CSP_REPORT_RATE_LIMIT") or "60/minute"
#: Reporting API batches; a browser sends a handful, never hundreds.
_CSP_REPORTS_PER_REQUEST = 20
# How many entries to count in from the *right* of `x-forwarded-for` to find the
# real client. 0 (default) = don't trust `x-forwarded-for` at all — a direct
# client can put anything in it, and taking the leftmost hop lets it forge a
# fresh IP per request and walk straight past every rate limit. Behind a
# platform LB (Cloud Run / Fly) set 2; behind a single self-managed reverse
# proxy that appends the peer, set 1.
_TRUSTED_PROXY_HOPS = int(os.environ.get("TRUSTED_PROXY_HOPS") or 0)
#: `cf-connecting-ip` is only meaningful behind Cloudflare, which overwrites
#: it on the way in. Anywhere else the caller writes it, and a fresh value per
#: request walks past every rate limit — so it is read only when the deploy
#: says it is behind Cloudflare.
_TRUST_CLOUDFLARE_IP = (os.environ.get("TRUST_CLOUDFLARE_IP") or "").strip().lower() in {"1", "true", "yes", "on"}


def _client_ip(request: Request) -> str:
    """Best-effort caller identity for rate limiting. Only reads forwarded
    headers that infrastructure we trust is known to have written."""
    cf = (request.headers.get("cf-connecting-ip") or "").strip() if _TRUST_CLOUDFLARE_IP else ""
    if cf:
        return cf
    if _TRUSTED_PROXY_HOPS > 0:
        hops = [p.strip() for p in request.headers.get("x-forwarded-for", "").split(",") if p.strip()]
        if len(hops) >= _TRUSTED_PROXY_HOPS:
            return hops[-_TRUSTED_PROXY_HOPS]
    return request.client.host if request.client else "anon"


#: Set on every response, unless something in front already did. JSON and a
#: .chum5 download, never a page: the policy says "no page here at all".
#: Every powerful browser feature this app never uses, switched off. The app
#: has no camera, microphone, geolocation, payment or sensor code at all, so
#: the list is "off" rather than "same-origin": a page that starts needing one
#: has to say so here.
_PERMISSIONS_POLICY = ", ".join(
    f"{feature}=()"
    for feature in (
        "accelerometer",
        "camera",
        "display-capture",
        "encrypted-media",
        "geolocation",
        "gyroscope",
        "magnetometer",
        "microphone",
        "midi",
        "payment",
        "usb",
        "xr-spatial-tracking",
    )
)

#: The API's half of the set `tests/test_security_headers.py` holds the three
#: senders to. `Referrer-Policy` is stricter here than on a page on purpose —
#: a JSON body is never a document, so it has no links to leak a referrer
#: through — and the CSP is the strict one an answer that renders nothing can
#: afford. Everything else is the shared set.
_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-site",
    "Permissions-Policy": _PERMISSIONS_POLICY,
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
}

_log = logging.getLogger("chummer_web")

limiter = Limiter(key_func=_client_ip, default_limits=[_RATE_LIMIT])

app = FastAPI(
    title="Chummer Web",
    description="Unofficial Shadowrun 5e character creator. Not affiliated with Catalyst Game Labs.",
    version="0.2.1",
)

app.state.limiter = limiter
# slowapi's handler is typed for its own exception; Starlette wants (Request, Exception)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_middleware(SlowAPIMiddleware)


async def _notice_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """A `NoticeError` is a refusal with a reason the user can act on. Wherever
    it is raised — the engine included — it goes out as a 400 carrying that
    reason, not as a 500 or a catch-all "that failed"."""
    assert isinstance(exc, NoticeError)
    return JSONResponse(status_code=400, content={"detail": exc.notice})


app.add_exception_handler(NoticeError, _notice_error_handler)

# Only what `frontend/lib/api.ts` sends: GET for the catalog, POST for
# everything else, and a Content-Type (JSON or octet-stream). A split deploy
# whose frontend starts sending something new has to be listed here first.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class _LimitBodySize:
    """Reject over-large request bodies.

    A declared Content-Length is refused before anything is read. A body sent
    without one (chunked transfer) is counted as it streams in: the read that
    crosses the cap reports a client disconnect instead, so nothing past it is
    buffered, and whatever the app answers to that is swapped for the 413.
    The .chum5lz path is independently bounded in chummer_import.

    Plain ASGI rather than `@app.middleware("http")`: counting needs to wrap
    `receive`, which a `BaseHTTPMiddleware` does not hand to its dispatch. It
    does not raise out of `receive` either — the `BaseHTTPMiddleware`s inside
    (slowapi) wrap that in an ExceptionGroup and FastAPI answers it with 400.
    """

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        cl = Headers(scope=scope).get("content-length")
        if cl and cl.isdigit() and int(cl) > self.max_bytes:
            _log.warning("request body too large", extra={"content_length": int(cl)})
            await _TOO_LARGE(scope, receive, send)
            return

        seen = 0
        too_large = False
        rejected = False

        async def counting_receive() -> Message:
            nonlocal seen, too_large
            if too_large:
                return {"type": "http.disconnect"}
            message = await receive()
            if message["type"] == "http.request":
                seen += len(message.get("body", b""))
                if seen > self.max_bytes:
                    too_large = True
                    _log.warning("request body too large", extra={"content_length": seen})
                    return {"type": "http.disconnect"}
            return message

        async def guarded_send(message: Message) -> None:
            nonlocal rejected
            if not too_large:
                await send(message)
            elif not rejected:
                rejected = True
                await _TOO_LARGE(scope, receive, send)

        await self.app(scope, counting_receive, guarded_send)
        if too_large and not rejected:
            await _TOO_LARGE(scope, receive, send)


_TOO_LARGE = JSONResponse({"detail": "request body too large"}, status_code=413)


app.add_middleware(_LimitBodySize, max_bytes=_MAX_REQUEST_BYTES)


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
        # The bundled deploy has Caddy in front and the browser talks to Next,
        # both of which set these. A split deploy exposes this app directly,
        # where nothing else would: an API answer is never a document, so it
        # is marked as one nobody may sniff, frame or embed.
        for header, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response
    finally:
        request_id_var.reset(token)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


#: The report fields worth a log line, and how much of each is kept. A report
#: body is written by the browser but *names* come from the page, and a page can
#: be made to fetch an attacker-chosen URL — so every value is truncated and
#: anything not listed here is dropped rather than logged.
_CSP_REPORT_FIELDS = {
    "document-uri": 200,
    "blocked-uri": 200,
    "effective-directive": 60,
    "violated-directive": 60,
    "disposition": 20,
    "status-code": 8,
}


def _csp_report_fields(report: object) -> dict[str, str]:
    """`{field: value}` for the listed fields, truncated, newlines stripped.

    A newline in a logged value would let a report forge a second log line,
    which matters more here than anywhere else in the app: this is the only
    endpoint whose body is written by something other than our own client.
    """
    if not isinstance(report, dict):
        return {}
    return {
        field: str(report[field]).replace("\r", " ").replace("\n", " ")[:limit]
        for field, limit in _CSP_REPORT_FIELDS.items()
        if report.get(field) not in (None, "")
    }


@app.post("/api/csp-report", status_code=204)
@limiter.limit(_CSP_REPORT_RATE_LIMIT)
async def csp_report(request: Request) -> Response:
    """Where the browser sends a Content-Security-Policy violation.

    Without this the policy is enforced and nobody finds out: a directive that
    is too tight breaks a feature silently, and one that is too loose is only
    discovered by whoever exploits it. `frontend/lib/csp.ts` names this URL in
    `report-uri` and `report-to`, which is why both report shapes are accepted:

    * `report-uri` sends `application/csp-report` — one `{"csp-report": {...}}`
    * the Reporting API sends `application/reports+json` — a *list* of
      `{"type": "csp-violation", "body": {...}}`

    Answers 204 to everything, malformed bodies included. There is no caller to
    tell anything to — the browser sends this and ignores the response — and a
    400 would only invite somebody to probe the parser.

    Extensions and injected scripts generate a steady trickle of reports on any
    public deployment, so these are `info`, not `warning`, and the rate limit is
    its own: a page can fire one report per violation per load.
    """
    try:
        payload = json.loads(await request.body() or b"")
    except ValueError:
        return Response(status_code=204)
    reports = payload if isinstance(payload, list) else [payload]
    for entry in reports[:_CSP_REPORTS_PER_REQUEST]:
        if isinstance(entry, dict):
            fields = _csp_report_fields(entry.get("csp-report") or entry.get("body") or entry)
            if fields:
                _log.info(
                    "csp violation: %s blocked %s",
                    fields.get("effective-directive") or fields.get("violated-directive") or "?",
                    fields.get("blocked-uri") or "?",
                    extra={"csp_report": fields, "client": _client_ip(request)},
                )
    return Response(status_code=204)


class _CachedCatalog(NamedTuple):
    body: bytes
    etag: str


def _serialise_catalog() -> _CachedCatalog:
    """The catalog as bytes, plus an ETag over them.

    Separators and `ensure_ascii` match Starlette's `JSONResponse` so the body
    is byte-identical to what the plain `-> dict` route used to send.
    """
    body = json.dumps(public_catalog(), ensure_ascii=False, separators=(",", ":")).encode()
    return _CachedCatalog(body, f'"{hashlib.blake2b(body, digest_size=16).hexdigest()}"')


@lru_cache(maxsize=1)
def _cached_catalog() -> _CachedCatalog:
    """Serialise the vendored catalog once per process.

    The vendored Chummer data is fixed at image-build time, so the payload
    cannot change while the process lives — `data_loader.catalog()` is already
    `lru_cache`d, but `public_catalog()` rebuilt its ~2.9 MB projection on every
    request. Caching the *bytes* also gives us a stable ETag for free.

    `lru_cache` does not memoise exceptions, so a request that arrives before
    `make data` still raises `FileNotFoundError` and a later one can succeed.
    """
    return _serialise_catalog()


#: Serialised catalogs for custom-data sets, by overlay key. Fewer than
#: `dataset_store.MAX_SETS` on purpose: each is ~3 MB of bytes held on top of
#: the parsed trees the overlay already costs, and re-serialising a set that
#: falls out is ~25 ms, not a rebuild.
MAX_CACHED_CUSTOM_CATALOGS = 4

_custom_catalogs: OrderedDict[str, _CachedCatalog] = OrderedDict()
_custom_catalogs_lock = threading.Lock()


def _cached_catalog_for(overlay: Overlay) -> _CachedCatalog:
    """The catalog as this custom-data set sees it.

    Built under `using_customdata`, so every loader in `catalog()` reads the
    merged trees — which is what makes a house-ruled martial art appear in the
    pick lists rather than only in the sheet of a character that already had
    one.
    """
    with _custom_catalogs_lock:
        found = _custom_catalogs.get(overlay.key)
        if found is not None:
            _custom_catalogs.move_to_end(overlay.key)
            return found
    # Built outside the lock: the first build under a new overlay reparses the
    # catalog (~0.4 s) and holding the lock would queue every other dataset
    # behind it. Two racing builds produce equal bytes, so the loser is simply
    # discarded.
    with using_customdata(overlay):
        built = _serialise_catalog()
    with _custom_catalogs_lock:
        _custom_catalogs[overlay.key] = built
        _custom_catalogs.move_to_end(overlay.key)
        while len(_custom_catalogs) > MAX_CACHED_CUSTOM_CATALOGS:
            _custom_catalogs.popitem(last=False)
    return built


def _matches_etag(header: str, etag: str) -> bool:
    """RFC 9110 If-None-Match: `*`, or a comma-separated list where a `W/`
    prefix is ignored (weak comparison is the right one for GET)."""
    candidates = [t.strip() for t in header.split(",") if t.strip()]
    return "*" in candidates or any(c.removeprefix("W/") == etag for c in candidates)


@app.get("/api/catalog")
def catalog_endpoint(
    request: Request,
    dataset: str = "",
    customdata: Annotated[list[str], Query()] = [],  # noqa: B006  (FastAPI reads the default)
) -> Response:
    """The whole options catalog. ~2.9 MB, and the same bytes for the life of
    the process, so it is served with an ETag: a reload costs one 304 instead
    of a re-transfer. Deliberately *not* `immutable` — the URL has no version
    in it, so a container update has to be able to invalidate it.

    With `dataset` (and the `customdata` directory list that goes with it) the
    catalog is the one that custom-data set sees. It used to be the vendored
    data whatever the character's settings said, which meant a merged pack
    reached `compute()` and the sheet but never the pick lists: a house-ruled
    martial art was computable and printable, and unbuyable.

    A set this process does not hold answers 409 with the hash it wants, the
    same handshake the character routes use, so the client's existing retry
    uploads it and asks again.

    No gzip here on purpose. In the bundled container Caddy encodes (zstd/gzip)
    and in dev the Next proxy is on localhost; compressing at this layer would
    only take zstd off the table.
    """
    overlay = None
    if dataset and customdata:
        found = lookup(dataset, list(customdata))
        if found is None:
            raise HTTPException(
                status_code=409,
                detail=notice("api.customDataMissing", dataset=dataset),
            )
        overlay = found[0]
    try:
        cached = _cached_catalog_for(overlay) if overlay else _cached_catalog()
    except FileNotFoundError as exc:
        # The name of the file, not the path to it. `str(exc)` reads
        # "[Errno 2] No such file or directory: '/app/backend/vendor/…'", and
        # this response goes to anyone who can reach the port — it would hand
        # out the server's directory layout to ask for a missing data file.
        # The operator who has to act on it gets the whole thing in the log.
        _log.error("catalog unavailable: %s", exc)
        missing = PurePosixPath(str(getattr(exc, "filename", "") or "")).name
        raise HTTPException(
            status_code=503,
            detail=notice("api.catalogMissing", file=missing or "?"),
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


@app.post("/api/customdata")
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


@app.post("/api/settings/parse")
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
    except NoticeError:
        raise
    except Exception as exc:
        _log.exception("JSON import failed")
        raise HTTPException(status_code=400, detail=notice("api.importJsonFailed")) from exc


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
    except NoticeError as exc:
        # chummer_import raises this with an actionable, user-facing notice.
        raise HTTPException(status_code=400, detail=exc.notice) from exc
    except Exception as exc:  # noqa: BLE001
        _log.exception("chum5 import failed")
        raise HTTPException(status_code=400, detail=notice("api.importChummerFailed")) from exc
