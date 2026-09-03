"""HTTP-level guards on backend/app/main.py: body-size cap and rate limiting.

These are the only tests that go through the ASGI app (TestClient); the rest of
the suite calls the store / engine directly.
"""

from __future__ import annotations

import re

import pytest
from starlette.testclient import TestClient

from app.main import _MAX_REQUEST_BYTES, _client_ip, _content_disposition, app

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


def test_oversized_collection_is_rejected() -> None:
    ip = {"cf-connecting-ip": "203.0.113.55"}
    base = client.post("/api/characters/new", json={"name": "X"}, headers=ip).json()
    base["spells"] = [{"spell_id": "x"} for _ in range(2001)]
    r = client.post("/api/characters/patch", json={"state": base}, headers=ip)
    assert r.status_code == 422


def test_content_disposition_is_latin1_safe_for_a_japanese_name() -> None:
    header = _content_disposition("サムライ・ドッグ")
    # latin-1 is what Starlette/uvicorn encode header values as; a bare
    # filename="..." with kana used to raise UnicodeEncodeError -> 500.
    header.encode("latin-1")
    assert re.fullmatch(
        r'attachment; filename="[A-Za-z0-9._ -]+\.chum5"; filename\*=UTF-8\'\'%.+\.chum5',
        header,
    )
    assert "%E3%82%B5" in header  # percent-encoded "サ"


def test_chummer_export_succeeds_with_a_non_ascii_name() -> None:
    ip = {"cf-connecting-ip": "203.0.113.56"}
    state = client.post("/api/characters/new", json={"name": "夜叉"}, headers=ip).json()
    r = client.post("/api/characters/chummer", json={"state": state}, headers=ip)
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/xml")
    assert "filename*=UTF-8''%E5%A4%9C%E5%8F%89.chum5" in r.headers["content-disposition"]
    assert r.text.lstrip().startswith("<")


def test_catalog_is_served_with_an_etag_and_revalidates_to_304() -> None:
    first = client.get("/api/catalog")
    assert first.status_code == 200
    assert first.headers["content-type"].startswith("application/json")
    etag = first.headers["etag"]
    assert etag.startswith('"') and etag.endswith('"')
    assert first.headers["cache-control"] == "no-cache"
    # the body still parses as the catalog the UI expects
    assert "metatypes" in first.json()

    again = client.get("/api/catalog", headers={"If-None-Match": etag})
    assert again.status_code == 304
    assert again.content == b""
    assert again.headers["etag"] == etag

    # a weak validator is still a match for GET, a stale one is not
    assert client.get("/api/catalog", headers={"If-None-Match": f"W/{etag}"}).status_code == 304
    assert client.get("/api/catalog", headers={"If-None-Match": '"stale"'}).status_code == 200
