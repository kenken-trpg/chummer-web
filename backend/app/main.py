from __future__ import annotations

import logging
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .api import catalog, characters, csp, export_routes, import_routes
from .api.deploy import _ALLOWED_ORIGINS, _MAX_REQUEST_BYTES, limiter
from .api.middleware import _LimitBodySize, _request_context
from .logging_config import configure_logging
from .notices import NoticeError

configure_logging()


#: Set once the warm-up below has finished, however it finished. `/api/ready`
#: waits on this; see there for why a failure still counts as finished.
_warmed = threading.Event()


def _warm_catalog() -> None:
    """Build the catalog payload before anyone asks for it.

    Parsing the vendored data and serialising the ~3 MB projection takes about
    0.5 s on a developer machine and ~3.3 s on one Cloud Run vCPU, and without
    this the first visitor after a restart waits for it. It runs on a thread so
    startup does not wait, and a missing `make data` is left for the request to
    report, exactly as before.
    """
    try:
        catalog._cached_catalog()
    except Exception:  # noqa: BLE001 -- the request path reports it properly
        logging.getLogger("chummer_web").warning("catalog warm-up failed", exc_info=True)
    finally:
        _warmed.set()


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
    threading.Thread(target=_warm_catalog, name="warm-catalog", daemon=True).start()
    yield


app = FastAPI(
    lifespan=_lifespan,
    title="Chummer Web",
    description="Unofficial Shadowrun 5e character creator. Not affiliated with Catalyst Game Labs.",
    version="0.3.0",
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


#: Enough to fix a hand-made body by; the client never shows these.
_MAX_VALIDATION_ERRORS = 20


async def _validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """FastAPI's own 422 echoes each offending value back as `input`. That
    sends a large bad body straight back out, and a deeply nested one makes
    the encoder recurse until the 422 turns into a 500. Nothing reads `input`,
    so it is dropped; `loc` still says where the problem is. Only the first
    `_MAX_VALIDATION_ERRORS` are listed: one per bad row of a large body made
    the 422 many times the size of the request."""
    assert isinstance(exc, RequestValidationError)
    errors = exc.errors()
    detail = [
        {k: v for k, v in err.items() if k not in ("input", "ctx", "url")} for err in errors[:_MAX_VALIDATION_ERRORS]
    ]
    return JSONResponse(status_code=422, content={"detail": detail})


app.add_exception_handler(RequestValidationError, _validation_error_handler)

# Only what `frontend/lib/api.ts` sends: GET for the catalog, POST for
# everything else, and a Content-Type (JSON or octet-stream). A split deploy
# whose frontend starts sending something new has to be listed here first.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.add_middleware(_LimitBodySize, max_bytes=_MAX_REQUEST_BYTES)

# Added last, so it is the *outermost* middleware: the id has to exist before
# anything else can log, and the access line has to see the status the body-size
# guard and the rate limiter actually returned.
app.middleware("http")(_request_context)


@app.get("/api/health")
def health() -> dict:
    """Liveness: the process is up and answering. Says nothing about the
    catalog — `/api/ready` is the one that waits for it."""
    return {"ok": True}


@app.get("/api/version")
def version() -> dict:
    """What is actually running.

    The container exposes `/api/*` and nothing else — `deploy/Caddyfile` sends
    only that prefix to uvicorn — so FastAPI's own `/docs` and
    `/openapi.json`, where the version is otherwise written, are unreachable
    in a deployment. Without this, confirming a release had landed meant
    comparing image digests from the outside.

    Reads `app.version`, so it cannot drift from the value
    `scripts/release_notes.py` checks against the tag.
    """
    return {"version": app.version}


@app.get("/api/ready")
def ready(response: Response) -> dict:
    """Readiness: the catalog is built, so the first real request will not pay
    for it.

    This is what a platform's *startup* probe should ask for. `/api/health`
    answers 200 the moment uvicorn binds, which on Cloud Run let traffic in
    while the warm-up thread was still parsing: the request then built the
    catalog a second time (`lru_cache` does not join concurrent callers) and
    the two competed for the single vCPU. Measured on `--cpu-boost`, the first
    `/api/catalog` after an idle period took 4.75 s that way against 0.2 s when
    the warm-up had finished first.

    A warm-up that *failed* still reports ready. The catalog is broken either
    way, and the request path says so with a proper error; holding the probe
    open would instead loop the container forever on a platform that restarts
    what never becomes ready.
    """
    if _warmed.is_set():
        return {"ok": True, "ready": True}
    response.status_code = 503
    return {"ok": False, "ready": False}


app.include_router(csp.router)
app.include_router(catalog.router)
app.include_router(characters.router)
app.include_router(import_routes.router)
app.include_router(export_routes.router)
