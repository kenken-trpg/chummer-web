"""HTTP-level guards on backend/app/main.py: body-size cap and rate limiting.

These are the only tests that go through the ASGI app (TestClient); the rest of
the suite calls the store / engine directly.
"""

from __future__ import annotations

from starlette.testclient import TestClient

from app.main import _MAX_REQUEST_BYTES, app

client = TestClient(app)


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
