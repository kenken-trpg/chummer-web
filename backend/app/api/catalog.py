"""`GET /api/catalog`: the options catalog, cached as bytes with an ETag."""

from __future__ import annotations

import hashlib
import json
import logging
import threading
from collections import OrderedDict
from functools import lru_cache
from pathlib import PurePosixPath
from typing import Annotated, NamedTuple

from fastapi import APIRouter, HTTPException, Query, Request, Response
from limits import parse

from ..catalog_view import public_catalog
from ..data_loader import Overlay, using_customdata
from ..dataset_store import lookup
from ..notices import notice
from . import deploy
from .deploy import _IMPORT_RATE_LIMIT, limiter

_log = logging.getLogger("chummer_web")

router = APIRouter()


class _CachedCatalog(NamedTuple):
    body: bytes
    etag: str


def _serialise_catalog() -> _CachedCatalog:
    """The catalog as bytes, plus an ETag over them.

    Separators and `ensure_ascii` match Starlette's `JSONResponse` so the body
    is byte-identical to what the plain `-> dict` route used to send.
    """
    body = json.dumps(public_catalog(), ensure_ascii=False, separators=(",", ":")).encode()
    return _CachedCatalog(body, f'"{hashlib.blake2b(body, digest_size=16).hexdigest()}"')


@lru_cache(maxsize=1)
def _cached_catalog() -> _CachedCatalog:
    """Serialise the vendored catalog once per process.

    The vendored Chummer data is fixed at image-build time, so the payload
    cannot change while the process lives — `data_loader.catalog()` is already
    `lru_cache`d, but `public_catalog()` rebuilt its ~2.9 MB projection on every
    request. Caching the *bytes* also gives us a stable ETag for free.

    `lru_cache` does not memoise exceptions, so a request that arrives before
    `make data` still raises `FileNotFoundError` and a later one can succeed.
    """
    return _serialise_catalog()


#: Serialised catalogs for custom-data sets, by overlay key. Fewer than
#: `dataset_store.MAX_SETS` on purpose: each is ~3 MB of bytes held on top of
#: the parsed trees the overlay already costs, and re-serialising a set that
#: falls out is ~25 ms, not a rebuild.
MAX_CACHED_CUSTOM_CATALOGS = 4

_custom_catalogs: OrderedDict[str, _CachedCatalog] = OrderedDict()
_custom_catalogs_lock = threading.Lock()


#: What a cache miss below costs a caller. A miss reparses and re-serialises
#: the catalog (~0.4 s of CPU), and cycling through more sets than are cached
#: makes every ask a miss — at the route's default 120/minute that is most of
#: a core per client. So a rebuild is counted like an import, and a hit is
#: not counted at all.
_REBUILD_LIMIT = parse(_IMPORT_RATE_LIMIT)


def _cached_catalog_for(overlay: Overlay, caller: str) -> _CachedCatalog:
    """The catalog as this custom-data set sees it.

    Built under `using_customdata`, so every loader in `catalog()` reads the
    merged trees — which is what makes a house-ruled martial art appear in the
    pick lists rather than only in the sheet of a character that already had
    one.
    """
    with _custom_catalogs_lock:
        found = _custom_catalogs.get(overlay.key)
        if found is not None:
            _custom_catalogs.move_to_end(overlay.key)
            return found
    if not limiter.limiter.hit(_REBUILD_LIMIT, "catalog-rebuild", caller):
        raise HTTPException(status_code=429, detail=notice("api.catalogRebuildLimited"))
    # Built outside the lock: the first build under a new overlay reparses the
    # catalog (~0.4 s) and holding the lock would queue every other dataset
    # behind it. Two racing builds produce equal bytes, so the loser is simply
    # discarded.
    with using_customdata(overlay):
        built = _serialise_catalog()
    with _custom_catalogs_lock:
        _custom_catalogs[overlay.key] = built
        _custom_catalogs.move_to_end(overlay.key)
        while len(_custom_catalogs) > MAX_CACHED_CUSTOM_CATALOGS:
            _custom_catalogs.popitem(last=False)
    return built


def _matches_etag(header: str, etag: str) -> bool:
    """RFC 9110 If-None-Match: `*`, or a comma-separated list where a `W/`
    prefix is ignored (weak comparison is the right one for GET)."""
    candidates = [t.strip() for t in header.split(",") if t.strip()]
    return "*" in candidates or any(c.removeprefix("W/") == etag for c in candidates)


@router.get("/api/catalog")
def catalog_endpoint(
    request: Request,
    dataset: str = "",
    customdata: Annotated[list[str], Query()] = [],  # noqa: B006  (FastAPI reads the default)
) -> Response:
    """The whole options catalog. ~2.9 MB, and the same bytes for the life of
    the process, so it is served with an ETag: a reload costs one 304 instead
    of a re-transfer. Deliberately *not* `immutable` — the URL has no version
    in it, so a container update has to be able to invalidate it.

    With `dataset` (and the `customdata` directory list that goes with it) the
    catalog is the one that custom-data set sees. It used to be the vendored
    data whatever the character's settings said, which meant a merged pack
    reached `compute()` and the sheet but never the pick lists: a house-ruled
    martial art was computable and printable, and unbuyable.

    A set this process does not hold answers 409 with the hash it wants, the
    same handshake the character routes use, so the client's existing retry
    uploads it and asks again.

    No gzip here on purpose. In the bundled container Caddy encodes (zstd/gzip)
    and in dev the Next proxy is on localhost; compressing at this layer would
    only take zstd off the table.
    """
    overlay = None
    if dataset and customdata:
        found = lookup(dataset, list(customdata))
        if found is None:
            raise HTTPException(
                status_code=409,
                detail=notice("api.customDataMissing", dataset=dataset),
            )
        overlay = found[0]
    try:
        cached = _cached_catalog_for(overlay, deploy._client_ip(request)) if overlay else _cached_catalog()
    except FileNotFoundError as exc:
        # The name of the file, not the path to it. `str(exc)` reads
        # "[Errno 2] No such file or directory: '/app/backend/vendor/…'", and
        # this response goes to anyone who can reach the port — it would hand
        # out the server's directory layout to ask for a missing data file.
        # The operator who has to act on it gets the whole thing in the log.
        _log.error("catalog unavailable: %s", exc)
        missing = PurePosixPath(str(getattr(exc, "filename", "") or "")).name
        raise HTTPException(
            status_code=503,
            detail=notice("api.catalogMissing", file=missing or "?"),
        ) from exc
    headers = {"ETag": cached.etag, "Cache-Control": "no-cache"}
    if _matches_etag(request.headers.get("if-none-match", ""), cached.etag):
        return Response(status_code=304, headers=headers)
    return Response(cached.body, media_type="application/json", headers=headers)
