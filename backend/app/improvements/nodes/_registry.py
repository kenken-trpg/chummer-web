"""The tag → handler table the bonus-node chain dispatches through.

Every ``<bonus>`` tag the engine implements is claimed by exactly one handler,
with :func:`handles` as the only way to claim one. That makes the table the
single place the set of implemented tags is written down: ``IMPLEMENTED`` in
``nodes/__init__`` is read off these keys rather than maintained beside them,
so a handler cannot be added without the pipeline knowing about it, and a tag
cannot be listed as implemented with nothing behind it.

Claiming a tag twice raises at import. The domain modules used to be tried in
order with a comment promising that no tag belonged to two of them; the table
enforces that instead of asking.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from ..effects import EffectsDict

#: What a handler is handed: the tag it matched (handlers that claim several
#: need it), the raw node, its `fields` shortcut, the effects being built, and
#: the name of whatever carries the bonus.
Handler = Callable[[str, dict[str, Any], dict[str, Any], EffectsDict, str], None]

HANDLERS: dict[str, Handler] = {}

_F = TypeVar("_F", bound=Handler)


def handles(*tags: str) -> Callable[[_F], _F]:
    """Claim `tags` for the decorated handler."""

    def register(fn: _F) -> _F:
        for tag in tags:
            first = HANDLERS.setdefault(tag, fn)
            if first is not fn:
                raise RuntimeError(
                    f"bonus tag {tag!r} is claimed twice: "
                    f"{first.__module__}.{first.__name__} and {fn.__module__}.{fn.__name__}"
                )
        return fn

    return register
