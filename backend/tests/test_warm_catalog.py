"""Startup builds the catalog payload before the first request asks for it."""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

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
