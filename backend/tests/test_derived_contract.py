"""Parity guards for the two payload contracts the frontend mirrors by hand.

``compute()`` builds ``ctx.state.derived`` from a ``DerivedDict`` literal in
``app/engine/compute/assemble.py`` — ``mypy`` checks the literal against
``DerivedDict``, so ``DerivedDict.__annotations__`` is the authoritative
server-side key set. The frontend mirrors it by hand as
``Derived`` in ``frontend/lib/types/derived.ts``; nothing
forces the two to agree, and they had drifted (``essence_lost`` / ``talent``
/ ``translations`` / ``unarmed_physical`` were server-only).

``/api/catalog`` has the same shape of problem and is the larger of the two —
46 collections against ``derived``'s payload, fetched on every cold load — but
``public_catalog()`` returns a plain ``dict``, so there is no annotation to
read. It gets checked against the *actual* response instead, which is the
stronger guard of the two: it compares what the frontend will really receive
rather than what a type says it should.

Both pin the **top-level key set**. ``derived`` is also held one level down
wherever the server types a value as a ``TypedDict`` — ``points``,
``karma_chargen`` and the like. The "public row" lists are plain dicts on the
server and stay hand-maintained: there is nothing to compare them against.
"""

from __future__ import annotations

import re
import typing
from pathlib import Path

import pytest

from app.engine.compute.derived_types import DerivedDict

_DERIVED_TS = Path(__file__).resolve().parents[2] / "frontend" / "lib" / "types" / "derived.ts"


def _ts_derived_keys() -> set[str]:
    text = _DERIVED_TS.read_text(encoding="utf-8")
    start = text.index("export interface Derived {")
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
    # Direct children only: exactly two leading spaces (nested props are 4+).
    return set(re.findall(r"^ {2}([A-Za-z_][A-Za-z0-9_]*)\??:", block, re.MULTILINE))


@pytest.mark.skipif(not _DERIVED_TS.exists(), reason="frontend/ not checked out")
def test_derived_top_level_keys_match_the_frontend_type() -> None:
    py = set(DerivedDict.__annotations__)
    ts = _ts_derived_keys()
    assert py == ts, (
        "derived payload drifted from frontend/lib/types/derived.ts.\n"
        f"  server-only (add to derived.ts): {sorted(py - ts)}\n"
        f"  frontend-only (stale in derived.ts): {sorted(ts - py)}"
    )


def _typed_dict_of(annotation: object) -> type | None:
    """The `TypedDict` an annotation names — directly, in a union with `None`,
    or as the element of a list — or `None` when it names none."""
    if typing.is_typeddict(annotation):
        return annotation  # type: ignore[return-value]
    for arg in typing.get_args(annotation):
        found = _typed_dict_of(arg)
        if found is not None:
            return found
    return None


def _ts_inline_members(block: str, key: str) -> set[str] | None:
    """Members of the object literal `Derived` declares inline for `key`
    (`key: {...}`, `key?: {...} | null`, `key?: {...}[]`), or `None` when the
    type is written some other way."""
    found = re.search(rf"^ {{2}}{key}\??: \{{", block, re.MULTILINE)
    if found is None:
        return None
    text = re.sub(r"/\*.*?\*/", "", block[found.end() :], flags=re.S)
    # Split the literal's body into members at depth 0 on `;` and newlines —
    # both spellings occur, `{ a: number; b: number }` and one per line.
    members: set[str] = set()
    depth, token = 0, ""
    for char in text:
        if depth == 0 and char == "}":
            break
        if char in "{[(<":
            depth += 1
        elif char in "}])>":
            depth -= 1
        if depth == 0 and char in ";\n":
            name = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\??\s*:", token)
            if name:
                members.add(name.group(1))
            token = ""
        else:
            token += char
    name = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\??\s*:", token)
    if name:
        members.add(name.group(1))
    return members


#: Typed on the server but declared on the frontend by name, from a module that
#: owns the shape — nothing to compare member by member.
_NAMED_ON_THE_FRONTEND = {"Notice"}


@pytest.mark.skipif(not _DERIVED_TS.exists(), reason="frontend/ not checked out")
def test_derived_nested_objects_match_the_frontend_type() -> None:
    """One level down from the key set: the sub-objects the server types.

    The "public row" lists are plain dicts on the server and stay unchecked,
    as the module docstring says. But about thirty of `DerivedDict`'s values
    are `TypedDict`s — `points`, `karma_chargen`, `metatype_info` — and those
    have an authoritative member list that the frontend's inline object
    literal can be held to. They had drifted: `movement.sprint_bonus`,
    `metatype_info.parent` / `.source` and `action_dice_pools[].needs_action`
    were sent and undeclared.
    """
    text = _DERIVED_TS.read_text(encoding="utf-8")
    block = text[text.index("export interface Derived {") :]
    drift: list[str] = []
    for key, annotation in typing.get_type_hints(DerivedDict).items():
        shape = _typed_dict_of(annotation)
        if shape is None or shape.__name__ in _NAMED_ON_THE_FRONTEND:
            continue
        ts = _ts_inline_members(block, key)
        if ts is None:
            drift.append(f"{key}: typed as {shape.__name__} on the server, not an inline object in derived.ts")
            continue
        py = set(typing.get_type_hints(shape))
        if py != ts:
            drift.append(f"{key} ({shape.__name__}): server-only {sorted(py - ts)}, frontend-only {sorted(ts - py)}")
    assert not drift, "derived sub-objects drifted from frontend/lib/types/derived.ts:\n  " + "\n  ".join(drift)


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


_GENERATED_TS = Path(__file__).resolve().parents[2] / "frontend" / "lib" / "types" / "generated.ts"


@pytest.mark.skipif(not _GENERATED_TS.exists(), reason="frontend/ not checked out")
def test_the_generated_state_types_are_not_stale() -> None:
    """The third contract, and the only one that needs no guessing: the state
    models are Pydantic, so `frontend/lib/types/generated.ts` is written from
    them rather than mirrored by hand. This fails when someone edits a model
    and forgets to re-run the script."""
    import subprocess
    import sys

    script = Path(__file__).resolve().parents[1] / "scripts" / "gen_frontend_types.py"
    done = subprocess.run([sys.executable, str(script), "--check"], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr.strip()
