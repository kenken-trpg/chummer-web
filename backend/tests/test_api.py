"""HTTP-level guards on backend/app/main.py: body-size cap and rate limiting.

These are the only tests that go through the ASGI app (TestClient); the rest of
the suite calls the store / engine directly.
"""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from app.main import _MAX_REQUEST_BYTES, _client_ip, app

client = TestClient(app)


class _StubClient:
    def __init__(self, host: str) -> None:
        self.host = host


class _StubRequest:
    """Just enough of starlette.Request for `_client_ip`."""

    def __init__(self, headers: dict[str, str], peer: str = "10.0.0.1") -> None:
        self.headers = headers
        self.client = _StubClient(peer)


def test_health_ok() -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_oversize_body_is_rejected_413() -> None:
    big = b"x" * (_MAX_REQUEST_BYTES + 1)
    r = client.post(
        "/api/characters/import-chummer",
        content=big,
        headers={"content-type": "application/octet-stream", "cf-connecting-ip": "203.0.113.7"},
    )
    assert r.status_code == 413


def test_rate_limit_returns_429_after_the_burst() -> None:
    # default limit is "120/minute" per client key; a distinct CF IP keeps this
    # test's budget separate from the other tests in this file.
    ip = {"cf-connecting-ip": "203.0.113.99"}
    seen_429 = False
    for _ in range(160):
        if client.get("/api/health", headers=ip).status_code == 429:
            seen_429 = True
            break
    assert seen_429


def test_client_ip_ignores_x_forwarded_for_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    # With no trusted hops configured, a client-supplied XFF is worthless — fall
    # back to the socket peer so it can't forge a fresh key per request.
    monkeypatch.setattr("app.main._TRUSTED_PROXY_HOPS", 0)
    req = _StubRequest({"x-forwarded-for": "1.2.3.4, 5.6.7.8"}, peer="10.0.0.1")
    assert _client_ip(req) == "10.0.0.1"  # type: ignore[arg-type]


def test_client_ip_reads_nth_hop_from_the_right(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.main._TRUSTED_PROXY_HOPS", 2)
    req = _StubRequest({"x-forwarded-for": "spoofed, 203.0.113.5, 70.0.0.1"})
    assert _client_ip(req) == "203.0.113.5"  # type: ignore[arg-type]
    # spoofer truncates the list -> not enough hops -> socket peer
    short = _StubRequest({"x-forwarded-for": "203.0.113.5"}, peer="10.0.0.2")
    assert _client_ip(short) == "10.0.0.2"  # type: ignore[arg-type]


def test_client_ip_prefers_cf_connecting_ip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.main._TRUSTED_PROXY_HOPS", 2)
    req = _StubRequest({"cf-connecting-ip": "198.51.100.9", "x-forwarded-for": "spoofed, a, b"})
    assert _client_ip(req) == "198.51.100.9"  # type: ignore[arg-type]
