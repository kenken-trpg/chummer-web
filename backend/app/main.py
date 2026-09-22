from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .api import catalog, characters, csp
from .api.deploy import _ALLOWED_ORIGINS, _MAX_REQUEST_BYTES, limiter
from .api.middleware import _LimitBodySize, _request_context
from .logging_config import configure_logging
from .notices import NoticeError

configure_logging()

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


async def _validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """FastAPI's own 422 echoes each offending value back as `input`. That
    sends a large bad body straight back out, and a deeply nested one makes
    the encoder recurse until the 422 turns into a 500. Nothing reads `input`,
    so it is dropped; `loc` still says where the problem is."""
    assert isinstance(exc, RequestValidationError)
    detail = [{k: v for k, v in err.items() if k not in ("input", "ctx", "url")} for err in exc.errors()]
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
    return {"ok": True}


app.include_router(csp.router)
app.include_router(catalog.router)
app.include_router(characters.router)
