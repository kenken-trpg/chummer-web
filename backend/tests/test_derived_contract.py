"""Parity guard for the ``derived`` payload contract.

``compute()`` builds ``ctx.state.derived`` as one ~175-key dict literal in
``app/engine/compute/assemble.py`` (it is a plain ``dict[str, Any]`` — the one
place the strict-``mypy`` sweep can't see). The frontend mirrors it by hand as
``Character["derived"]`` in ``frontend/lib/types/character.ts``. Nothing forced
them to agree, and they had drifted (``essence_lost`` / ``talent`` /
``translations`` / ``unarmed_physical`` were server-only).

This test pins the **top-level key set** on both sides. It is intentionally
shallow — nested row shapes are still hand-maintained — but a renamed or
added top-level ``derived`` key now fails here instead of silently reaching a
component as ``undefined``.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

_ASSEMBLE = Path(__file__).resolve().parents[1] / "app" / "engine" / "compute" / "assemble.py"
_CHARACTER_TS = Path(__file__).resolve().parents[2] / "frontend" / "lib" / "types" / "character.ts"


def _python_derived_keys() -> set[str]:
    tree = ast.parse(_ASSEMBLE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Attribute) and t.attr == "derived" for t in node.targets)
            and isinstance(node.value, ast.Dict)
        ):
            return {k.value for k in node.value.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)}
    raise AssertionError("could not find `ctx.state.derived = {...}` in assemble.py")


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
    py = _python_derived_keys()
    ts = _ts_derived_keys()
    assert py == ts, (
        "derived payload drifted from frontend/lib/types/character.ts.\n"
        f"  server-only (add to character.ts): {sorted(py - ts)}\n"
        f"  frontend-only (stale in character.ts): {sorted(ts - py)}"
    )
