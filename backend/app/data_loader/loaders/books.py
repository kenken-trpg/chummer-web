"""Rulebook + settings-preset loaders.

`books.xml` is the list of source books Chummer knows; every catalog row's
`<source>` is one of these `<code>`s. `settings.xml` is Chummer's own shipped
settings presets — the pulldown the user picks a ruleset from.

Only the parts a web chargen can act on are read: which books a preset
enables, and how it builds a character. The remaining ~150 house-rule knobs
in a `<setting>` are left on the floor until the engine can honour them.
"""

from __future__ import annotations

from typing import Any

from .._xml import _int, _text, data_root

#: `<buildmethod>` as `settings.xml` spells it -> as `CharacterState.build_method`
#: does. Deliberately not `chummer_import._BUILD_METHODS`: that one is lenient
#: because it has a character to place somewhere, and folds `LifeModule` into
#: Priority. A preset has no character, so an unbuildable one is dropped.
_BUILD_METHODS = {"priority": "Priority", "sumtoten": "SumToTen", "karma": "Karma"}


def load_books() -> list[dict[str, Any]]:
    """`[{code, name}]`, in `books.xml` order.

    Returns `[]` when the file is missing or unreadable so an un-fetched
    vendor tree still imports (see docs/adding-rules.md).
    """
    root = data_root("books.xml")
    if root is None:
        return []
    books = []
    for el in root.findall("./books/book"):
        code = _text(el.find("code"))
        if not code:
            continue
        books.append({"code": code, "name": _text(el.find("name")) or code})
    return books


def load_settings_presets() -> list[dict[str, Any]]:
    """Chummer's shipped `<setting>` presets, projected to what the web app
    can apply today: the enabled books and the build method.

    A preset whose `<buildmethod>` this app has no engine for is dropped
    rather than silently rewritten to Priority — offering "Life Modules" in
    the pulldown and then building a Priority character would be a lie.
    """
    root = data_root("settings.xml")
    if root is None:
        return []
    presets = []
    for el in root.findall("./settings/setting"):
        name = _text(el.find("name"))
        method = _BUILD_METHODS.get(_text(el.find("buildmethod")).lower())
        if not name or not method:
            continue
        books = [code for code in (_text(b) for b in el.findall("./books/book")) if code]
        presets.append(
            {
                "id": _text(el.find("id")) or name,
                "name": name,
                "build_method": method,
                "books": books,
                "sum_to_ten": _int(el.find("sumtoten"), 10),
            }
        )
    return presets
