"""Logging that can be read by a machine, and a request id to correlate on.

The default is plain text, because that is what you want tailing `make dev`.
Set ``LOG_FORMAT=json`` for a deploy: one JSON object per line, which is what
Cloud Logging / Loki / CloudWatch want, and what makes "show me every 429 from
this caller" a query rather than a grep.

Every line carries a ``request_id``. It comes from the edge when the proxy set
one (Cloudflare, Cloud Run and a `header_up` in Caddy all can), so a trace that
starts in the browser's network tab reaches the engine traceback; otherwise
this process invents one. It goes back out on ``X-Request-ID`` so the caller
can quote it in a bug report.

Deliberately not logged: request bodies, query strings, and anything derived
from a `CharacterState`. Characters are the user's, they never touch disk here
(see docs/architecture.md), and a log line is disk. The path, the status and
the duration are enough to find a problem; reproducing it is the user's call.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from contextvars import ContextVar
from typing import Any

#: Set per request by the middleware in `main`; empty outside a request
#: (startup, a script, a test calling the engine directly).
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def new_request_id() -> str:
    """Short enough to paste into a bug report, wide enough not to collide."""
    return uuid.uuid4().hex[:12]


class _RequestIdFilter(logging.Filter):
    """Make `request_id` available to every formatter, always defined."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


# Everything `logging` puts on a record by itself. Anything else was passed as
# `extra=` by us and belongs in the JSON output.
_STANDARD = frozenset(logging.LogRecord("", 0, "", 0, "", None, None).__dict__) | {
    "asctime",
    "message",
    "taskName",
    "request_id",
}


class JsonFormatter(logging.Formatter):
    """One JSON object per line. `extra=` fields are merged in at the top level."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if rid := getattr(record, "request_id", ""):
            payload["request_id"] = rid
        for key, value in record.__dict__.items():
            if key not in _STANDARD and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        # `default=str` so an unexpected object in `extra=` degrades to its repr
        # instead of taking down the handler that was reporting the problem.
        return json.dumps(payload, ensure_ascii=False, default=str)


_TEXT_FORMAT = "%(asctime)s %(levelname)-7s %(name)s [%(request_id)s] %(message)s"


def configure_logging() -> None:
    """Install one stderr handler on the root logger, and give uvicorn's
    loggers the same treatment so access lines and ours look alike.

    Idempotent: importing `app.main` twice (a test client, then a reload) must
    not double every line.
    """
    level = (os.environ.get("LOG_LEVEL") or "INFO").upper()
    as_json = (os.environ.get("LOG_FORMAT") or "text").lower() == "json"

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter() if as_json else logging.Formatter(_TEXT_FORMAT))
    handler.addFilter(_RequestIdFilter())
    handler.set_name("chummer_web")

    root = logging.getLogger()
    for existing in [h for h in root.handlers if h.get_name() == "chummer_web"]:
        root.removeHandler(existing)
    root.addHandler(handler)
    root.setLevel(level)

    # uvicorn installs its own handlers at import; drop them so its lines go
    # through ours (same format, same request id) instead of being emitted twice.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
    # `uvicorn.access` would now be a second, worse copy of the line the request
    # middleware writes — no request id, no duration. Keep its warnings.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
