"""Structured engine messages.

The engine used to append finished Japanese sentences to ``derived.errors`` /
``derived.warnings``. That made the creation-check panel the one part of the UI
that could not follow the locale switch: the wording was baked in here, and the
front end could only regex-match it to guess which tab fixes the problem
(``lib/character/checklist.ts``).

So the engine now emits a *key* plus its parameters and nothing else. All
wording — every locale of it — lives in ``frontend/lib/i18n/messages.ts`` with
the rest of the app's copy, where the ``Record<MsgKey, string>`` type stops a
locale from silently falling behind (docs/i18n.md).

Two consequences worth knowing at the call site:

* **Parameters carrying a catalog name go through :func:`term`.** The Chummer
  data files are English, so ``f"{spec['name']} の前提を満たしていません"`` put
  an English weapon name inside a Japanese sentence. Marking the value lets the
  front end run it through ``tr`` and render the name in the reader's locale —
  which fixes the Japanese side too, not just the English one.
* **Everything here has to survive JSON.** ``derived`` is stored in the
  browser's IndexedDB and posted back, so parameters stay primitives.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TypedDict


class Term(TypedDict):
    """A catalog name (weapon, quality, spell …) for the client to translate."""

    tr: str


class Phrase(TypedDict):
    """A parameter that is itself a dictionary key — for the fixed vocabulary
    the engine used to inline (limb slots, sides, the "ギア" fallback name)."""

    ui: str


ParamValue = str | int | float | bool | Term | Phrase | list[str] | list[Term]


class Notice(TypedDict):
    """One engine message: a key into the UI dictionary, plus its parameters."""

    key: str
    params: dict[str, ParamValue]


def notice(key: str, **params: ParamValue) -> Notice:
    return {"key": key, "params": params}


def term(name: str) -> Term:
    """Mark a catalog name so the client renders it with `tr`."""
    return {"tr": name}


def terms(names: Iterable[str]) -> list[Term]:
    return [{"tr": name} for name in names]


def ui(key: str) -> Phrase:
    """Mark a parameter that the client should look up rather than print."""
    return {"ui": key}


def has_key(notices: Iterable[Notice], key: str) -> bool:
    """Whether `key` was emitted. Mostly for tests and for engine code that
    checks whether it already complained about something."""
    return any(n["key"] == key for n in notices)
