"""Request ids, and the JSON the deploy reads.

The point of these is that an operator can answer "what happened to the request
this user is quoting" — which needs the id to reach the caller, the log line to
carry it, and the line to be machine-readable when asked.
"""

from __future__ import annotations

import json
import logging

import pytest
from starlette.testclient import TestClient

from app.logging_config import JsonFormatter, configure_logging, request_id_var
from app.main import app

client = TestClient(app)


def _record(**extra: object) -> logging.LogRecord:
    record = logging.LogRecord("chummer_web", logging.INFO, __file__, 1, "hello %s", ("world",), None)
    record.__dict__.update(extra)
    return record


def test_every_response_carries_a_request_id() -> None:
    first = client.get("/api/health")
    second = client.get("/api/health")
    assert first.headers["x-request-id"]
    assert first.headers["x-request-id"] != second.headers["x-request-id"]


def test_a_forwarded_request_id_is_ignored_without_a_trusted_proxy() -> None:
    # same rule as the forwarded-IP handling: with TRUSTED_PROXY_HOPS at its
    # default 0 the header is attacker-controlled, so it does not win
    forged = "a" * 200
    got = client.get("/api/health", headers={"X-Request-ID": forged}).headers["x-request-id"]
    assert got != forged
    assert len(got) == 12


def test_a_forwarded_request_id_is_taken_and_bounded_behind_a_proxy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.main._TRUSTED_PROXY_HOPS", 1)
    assert client.get("/api/health", headers={"X-Request-ID": "edge-123"}).headers["x-request-id"] == "edge-123"
    # an essay in the header must not become an essay on every log line
    long = client.get("/api/health", headers={"X-Request-ID": "z" * 500}).headers["x-request-id"]
    assert len(long) == 64


def test_the_access_line_names_the_route_and_its_timing(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="chummer_web"):
        client.get("/api/health")
    line = next(r for r in caplog.records if r.name == "chummer_web")
    assert line.getMessage().startswith("GET /api/health -> 200 in")
    assert line.status == 200  # type: ignore[attr-defined]
    assert isinstance(line.duration_ms, float)  # type: ignore[attr-defined]


def test_the_body_size_rejection_is_logged(caplog: pytest.LogCaptureFixture) -> None:
    from app.main import _MAX_REQUEST_BYTES

    with caplog.at_level(logging.WARNING, logger="chummer_web"):
        response = client.post("/api/characters/patch", content=b"x" * (_MAX_REQUEST_BYTES + 1))
    assert response.status_code == 413
    assert any("too large" in r.getMessage() for r in caplog.records)


class TestJsonFormatter:
    def test_extra_fields_land_at_the_top_level(self) -> None:
        token = request_id_var.set("abc123")
        try:
            record = _record(request_id="abc123", status=503, path="/api/catalog")
            payload = json.loads(JsonFormatter().format(record))
        finally:
            request_id_var.reset(token)
        assert payload["message"] == "hello world"
        assert payload["level"] == "INFO"
        assert payload["request_id"] == "abc123"
        assert payload["status"] == 503
        assert payload["path"] == "/api/catalog"

    def test_internal_logging_machinery_is_not_leaked_into_the_payload(self) -> None:
        payload = json.loads(JsonFormatter().format(_record()))
        for noise in ("args", "msg", "levelno", "pathname", "created", "stack_info"):
            assert noise not in payload

    def test_an_unserialisable_extra_degrades_instead_of_exploding(self) -> None:
        # a formatter that raises takes down the log line reporting the problem
        payload = json.loads(JsonFormatter().format(_record(thing=object())))
        assert payload["thing"].startswith("<object object")

    def test_an_exception_is_carried_as_text(self) -> None:
        try:
            raise ValueError("boom")
        except ValueError:
            import sys

            record = _record()
            record.exc_info = sys.exc_info()
        payload = json.loads(JsonFormatter().format(record))
        assert "ValueError: boom" in payload["exception"]


def test_configure_logging_does_not_stack_handlers() -> None:
    root = logging.getLogger()
    configure_logging()
    before = [h for h in root.handlers if h.get_name() == "chummer_web"]
    configure_logging()
    after = [h for h in root.handlers if h.get_name() == "chummer_web"]
    assert len(before) == len(after) == 1
