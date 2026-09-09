"""The server's cache of merged custom-data sets.

The browser holds the `customdata/` files; the server holds what they merge
into. A request carries only the content hash, and the server answers 409 when
it does not have that hash yet — the client then uploads the files once and
retries. So the usual request costs 32 bytes rather than 100 KB, and the
server keeps no user data beyond a bounded in-memory cache it can lose at any
time without anything breaking.

Nothing here is durable on purpose. A restart empties it and the next request
re-uploads; the character, which is what matters, lives in the browser.
"""

from __future__ import annotations

import threading
from collections import OrderedDict

from .customdata import MergeReport, build_overlay
from .data_loader import Overlay

#: How many merged sets to keep. Each is a handful of parsed XML trees — a few
#: MB — so this bounds the cache at "a few tables", not "everyone who ever
#: visited".
MAX_SETS = 8

#: Cap on one upload. The published custom-data packs are ~200 KB; this leaves
#: room for a large one without letting the endpoint be used as storage.
MAX_UPLOAD_BYTES = 16 * 1024 * 1024


class _Store:
    def __init__(self) -> None:
        self._sets: OrderedDict[str, tuple[Overlay, MergeReport]] = OrderedDict()
        # `compute()` runs in a threadpool, so two requests can race here.
        self._lock = threading.Lock()

    def get(self, key: str) -> tuple[Overlay, MergeReport] | None:
        with self._lock:
            found = self._sets.get(key)
            if found is not None:
                self._sets.move_to_end(key)
            return found

    def put(self, key: str, overlay: Overlay, report: MergeReport) -> None:
        with self._lock:
            self._sets[key] = (overlay, report)
            self._sets.move_to_end(key)
            while len(self._sets) > MAX_SETS:
                self._sets.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._sets.clear()


_store = _Store()


def overlay_key(dataset: str, customdata: list[str]) -> str:
    """What one merge is identified by.

    Both halves matter: the same files with a different set of directories
    enabled is a different result, and the order they are listed in decides
    who wins when two of them edit the same entry.
    """
    return dataset + "|" + "|".join(customdata)


def lookup(dataset: str, customdata: list[str]) -> tuple[Overlay, MergeReport] | None:
    if not dataset or not customdata:
        return None
    return _store.get(overlay_key(dataset, customdata))


def remember(
    dataset: str,
    customdata: list[str],
    files: dict[str, bytes],
) -> tuple[Overlay, MergeReport]:
    """Merge one upload and keep it under its content hash."""
    key = overlay_key(dataset, customdata)
    trees, report = build_overlay(files, customdata)
    overlay = Overlay(key=key, trees=trees)
    _store.put(key, overlay, report)
    return overlay, report


def reset() -> None:
    """Empty the cache. For tests; nothing in the app needs it."""
    _store.clear()
