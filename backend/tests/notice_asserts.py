"""Assertion helpers for the structured messages the engine emits.

``derived["errors"]`` / ``["warnings"]`` are ``Notice`` dicts (``app.notices``):
a dictionary key plus its parameters, with the wording living in the front
end. Tests therefore match on the key — and, where the number or the name is
the point of the test, on the parameters — instead of on a Japanese substring.

``params`` are compared *unwrapped*: a catalog name marked with ``term()``
compares equal to the bare name, and a ``ui()`` phrase to its key, so a test
reads ``has(errs, "engine.gear.availOver", name="Ares Predator V")``.
"""

from __future__ import annotations

from typing import Any

from app.notices import Notice


def unwrap(value: Any) -> Any:
    """`{"tr": "Ares Predator V"}` -> `"Ares Predator V"`; `{"ui": k}` -> `k`.
    Lists unwrap element-wise; everything else passes through."""
    if isinstance(value, dict):
        if "tr" in value:
            return value["tr"]
        if "ui" in value:
            return value["ui"]
    if isinstance(value, list):
        return [unwrap(item) for item in value]
    return value


def find(notices: list[Notice], key: str, **params: Any) -> list[Notice]:
    """Every notice with `key` whose parameters include the given ones."""
    out = []
    for n in notices:
        if n["key"] != key:
            continue
        got = {k: unwrap(v) for k, v in n["params"].items()}
        if all(k in got and got[k] == v for k, v in params.items()):
            out.append(n)
    return out


def has(notices: list[Notice], key: str, **params: Any) -> bool:
    return bool(find(notices, key, **params))


def keys_of(notices: list[Notice]) -> list[str]:
    return [n["key"] for n in notices]
