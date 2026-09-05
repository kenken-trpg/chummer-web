"""Parity guards for the two payload contracts the frontend mirrors by hand.

``compute()`` builds ``ctx.state.derived`` from a ``DerivedDict`` literal in
``app/engine/compute/assemble.py`` — ``mypy`` checks the literal against
``DerivedDict``, so ``DerivedDict.__annotations__`` is the authoritative
server-side key set. The frontend mirrors it by hand as
``Character["derived"]`` in ``frontend/lib/types/character.ts``; nothing
forces the two to agree, and they had drifted (``essence_lost`` / ``talent``
/ ``translations`` / ``unarmed_physical`` were server-only).

``/api/catalog`` has the same shape of problem and is the larger of the two —
46 collections against ``derived``'s payload, fetched on every cold load — but
``public_catalog()`` returns a plain ``dict``, so there is no annotation to
read. It gets checked against the *actual* response instead, which is the
stronger guard of the two: it compares what the frontend will really receive
rather than what a type says it should.

Both pin the **top-level key set** only. Nested row shapes stay
hand-maintained; pinning those by hand as well would cost more to keep honest
than it protects, and a wrong nested field is usually visible on screen where
a missing top-level key is just ``undefined``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.engine.compute.derived_types import DerivedDict

_CHARACTER_TS = Path(__file__).resolve().parents[2] / "frontend" / "lib" / "types" / "character.ts"


def _ts_derived_keys() -> set[str]:
    text = _CHARACTER_TS.read_text(encoding="utf-8")
    start = text.index("derived: {")
    depth = 0
    end = start
    for i in range(text.index("{", start), len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    block = text[start:end]
    # Direct children only: exactly four leading spaces (nested props are 6+).
    return set(re.findall(r"^ {4}([A-Za-z_][A-Za-z0-9_]*)\??:", block, re.MULTILINE))


@pytest.mark.skipif(not _CHARACTER_TS.exists(), reason="frontend/ not checked out")
def test_derived_top_level_keys_match_the_frontend_type() -> None:
    py = set(DerivedDict.__annotations__)
    ts = _ts_derived_keys()
    assert py == ts, (
        "derived payload drifted from frontend/lib/types/character.ts.\n"
        f"  server-only (add to character.ts): {sorted(py - ts)}\n"
        f"  frontend-only (stale in character.ts): {sorted(ts - py)}"
    )


_CATALOG_TS = Path(__file__).resolve().parents[2] / "frontend" / "lib" / "types" / "catalog.ts"


def _ts_interface_keys(text: str, declaration: str) -> set[str]:
    """Members of a TS interface/type body, ignoring anything nested inside it.

    Brace/bracket depth rather than indentation: `Catalog` nests object and
    array literals several levels deep, so counting leading spaces the way
    `_ts_derived_keys` does would pick up inner properties too.
    """
    start = text.index(declaration)
    open_at = text.index("{", start)
    depth = 0
    for i in range(open_at, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                body = text[open_at + 1 : i]
                break
    else:  # pragma: no cover - unbalanced braces would be a syntax error
        raise AssertionError(f"unbalanced braces after {declaration!r}")

    keys: set[str] = set()
    depth = 0
    for line in body.split("\n"):
        if depth == 0:
            match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\??\s*:", line.strip())
            if match:
                keys.add(match.group(1))
        depth += line.count("{") + line.count("[") - line.count("}") - line.count("]")
    return keys


@pytest.mark.skipif(not _CATALOG_TS.exists(), reason="frontend/ not checked out")
def test_catalog_top_level_keys_match_the_frontend_type() -> None:
    from app.catalog_view import public_catalog

    payload = set(public_catalog())
    assert payload, "empty catalog — is backend/vendor/chummer populated?"

    ts = _ts_interface_keys(_CATALOG_TS.read_text(encoding="utf-8"), "export interface Catalog {")
    assert payload == ts, (
        "/api/catalog drifted from frontend/lib/types/catalog.ts.\n"
        f"  served but undeclared (add to catalog.ts): {sorted(payload - ts)}\n"
        f"  declared but never served (stale in catalog.ts): {sorted(ts - payload)}"
    )
