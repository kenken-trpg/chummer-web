"""Startup builds the catalog payload before the first request asks for it."""

from __future__ import annotations

import threading
import time

import pytest
from fastapi.testclient import TestClient

from app import main
from app.api import catalog
from app.data_loader._xml import data_root
from app.main import app


def test_startup_warms_the_catalog():
    if data_root("skills.xml") is None:
        pytest.skip("vendored Chummer data not fetched")
    catalog._cached_catalog.cache_clear()
    with TestClient(app):
        deadline = time.monotonic() + 30
        while catalog._cached_catalog.cache_info().currsize == 0 and time.monotonic() < deadline:
            time.sleep(0.05)
        assert catalog._cached_catalog.cache_info().currsize == 1


def test_a_failed_warm_up_does_not_stop_startup(monkeypatch):
    def boom():
        raise FileNotFoundError("no data")

    monkeypatch.setattr(catalog, "_cached_catalog", boom)
    with TestClient(app) as client:
        assert client.get("/api/health").json() == {"ok": True}


def test_ready_is_503_until_the_warm_up_finishes(monkeypatch):
    """The point of the endpoint: a platform's startup probe must not let
    traffic in while the catalog is still being built."""
    started = threading.Event()
    release = threading.Event()

    def slow():
        started.set()
        release.wait(10)

    monkeypatch.setattr(catalog, "_cached_catalog", slow)
    main._warmed.clear()
    with TestClient(main.app) as client:
        assert started.wait(10)
        r = client.get("/api/ready")
        assert r.status_code == 503
        assert r.json() == {"ok": False, "ready": False}
        # health is liveness and answers all along — the container is up, it
        # is only the catalog that is not there yet
        assert client.get("/api/health").status_code == 200
        release.set()
        deadline = time.monotonic() + 10
        while not main._warmed.is_set() and time.monotonic() < deadline:
            time.sleep(0.02)
        r = client.get("/api/ready")
        assert r.status_code == 200
        assert r.json() == {"ok": True, "ready": True}


def test_a_failed_warm_up_still_reports_ready(monkeypatch):
    """Otherwise the container never becomes ready and a platform that
    restarts what never starts would loop on it forever."""

    def boom():
        raise FileNotFoundError("no data")

    monkeypatch.setattr(catalog, "_cached_catalog", boom)
    main._warmed.clear()
    with TestClient(main.app) as client:
        deadline = time.monotonic() + 10
        while not main._warmed.is_set() and time.monotonic() < deadline:
            time.sleep(0.02)
        assert client.get("/api/ready").status_code == 200
