"""Startup builds the catalog payload before the first request asks for it."""

from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from app import data_loader, main
from app.api import catalog
from app.data_loader._xml import data_root
from app.main import app


def test_startup_warms_the_catalog():
    if data_root("skills.xml") is None:
        pytest.skip("vendored Chummer data not fetched")
    catalog._serialise_vendored.cache_clear()
    with TestClient(app):
        deadline = time.monotonic() + 30
        while catalog._serialise_vendored.cache_info().currsize == 0 and time.monotonic() < deadline:
            time.sleep(0.05)
        assert catalog._serialise_vendored.cache_info().currsize == 1


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


class TestOneBuildBetweenConcurrentCallers:
    """`lru_cache` has no "wait for whoever is already computing this".

    It reruns the function for every caller that arrives before the first one
    returns, so N requests on a cold cache paid for N full builds of the same
    data. The warm-up and `/api/ready` closed the case where the racer was the
    startup thread; this closes the general one, which custom data can still
    reach — a table that uploads a pack and whose five players all load the
    sheet at once arrive together on a key nothing holds yet.
    """

    @staticmethod
    def _run_together(work, threads: int = 4) -> list:
        """Call `work` on `threads` threads that all start at the same moment."""
        barrier = threading.Barrier(threads, timeout=30)

        def once():
            barrier.wait()
            return work()

        with ThreadPoolExecutor(max_workers=threads) as pool:
            return [future.result(timeout=120) for future in [pool.submit(once) for _ in range(threads)]]

    def test_four_cold_callers_build_the_catalog_once(self, monkeypatch):
        if data_root("skills.xml") is None:
            pytest.skip("vendored Chummer data not fetched")
        builds = []
        real = data_loader.load_metatypes

        def counted():
            builds.append(1)
            return real()

        monkeypatch.setattr(data_loader, "load_metatypes", counted)
        data_loader._catalog_for.cache_clear()
        try:
            results = self._run_together(data_loader.catalog)
            assert len(builds) == 1
            # and they all got the same object, not four equal ones
            assert all(result is results[0] for result in results)
        finally:
            data_loader._catalog_for.cache_clear()

    def test_a_build_that_raises_leaves_the_lock_free_for_the_next_caller(self, monkeypatch):
        """`lru_cache` does not memoise exceptions, and the lock must not
        outlive the failure either — otherwise a missing data directory would
        wedge the process instead of erroring per request."""
        calls = []
        real = data_loader.load_metatypes

        def boom():
            calls.append(1)
            raise FileNotFoundError("no data")

        monkeypatch.setattr(data_loader, "load_metatypes", boom)
        data_loader._catalog_for.cache_clear()
        try:
            for _ in range(2):
                with pytest.raises(FileNotFoundError):
                    data_loader.catalog()
            assert len(calls) == 2
            monkeypatch.setattr(data_loader, "load_metatypes", real)
            assert data_loader.catalog()["skills"]
        finally:
            data_loader._catalog_for.cache_clear()

    def test_the_lock_registry_cannot_grow_without_bound(self):
        """An overlay key is a hash of an uploaded set, so a long-lived process
        sees arbitrarily many. Evicting a lock is safe — whoever holds it keeps
        its reference — so the registry is simply capped."""
        for index in range(data_loader.MAX_BUILD_LOCKS * 2):
            data_loader._build_lock(f"key-{index}")
        assert len(data_loader._build_locks) == data_loader.MAX_BUILD_LOCKS
        # the vendored key is gone from the registry, which costs nothing: the
        # catalog itself is still cached
        data_loader._build_locks.clear()

    def test_four_cold_callers_serialise_the_payload_once(self, monkeypatch):
        if data_root("skills.xml") is None:
            pytest.skip("vendored Chummer data not fetched")
        runs = []
        real = catalog._serialise_catalog

        def counted():
            runs.append(1)
            return real()

        monkeypatch.setattr(catalog, "_serialise_catalog", counted)
        catalog._serialise_vendored.cache_clear()
        try:
            bodies = self._run_together(catalog._cached_catalog)
            assert len(runs) == 1
            assert {body.etag for body in bodies} == {bodies[0].etag}
        finally:
            catalog._serialise_vendored.cache_clear()
