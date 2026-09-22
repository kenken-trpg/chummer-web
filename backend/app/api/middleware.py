"""The ASGI layers every request passes through: the body-size guard, and the
outermost one that gives a request its id, logs it and sets the security
headers. `main.py` decides the order they are stacked in."""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from ..logging_config import new_request_id, request_id_var
from . import deploy

_log = logging.getLogger("chummer_web")

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


async def _request_context(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """Give the request an id, log one line when it finishes, hand the id back.

    An id from the edge wins so a trace spans the whole hop chain — but only
    from a header a proxy we trust would have written, on the same footing as
    the forwarded-IP rule in `deploy._client_ip`.
    """
    incoming = request.headers.get("x-request-id", "").strip() if deploy._TRUSTED_PROXY_HOPS > 0 else ""
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
                "client": deploy._client_ip(request),
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
