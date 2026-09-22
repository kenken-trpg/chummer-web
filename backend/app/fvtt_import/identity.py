"""What the actor is rather than what it has: the kind of magic user, and the
biography turned from HTML into text."""

from __future__ import annotations

from html.parser import HTMLParser
from typing import Any


class _Text(HTMLParser):
    """The text of an HTML fragment, a line break for <br> and </p>."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "br":
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag == "p":
            self.parts.append("\n")


def _plain(text: str) -> str:
    """HTML description -> plain text, a paragraph per line. A parser, not a
    regex: the text comes from an uploaded file (ReDoS)."""
    parser = _Text()
    parser.feed(text)
    parser.close()
    return "".join(parser.parts).strip()


def _talent(system: dict[str, Any], items: list[dict[str, Any]]) -> str:
    """Foundry keeps only mundane / magic / resonance: the kind of magic user
    is read off what they have."""
    special = str(system.get("special") or "")
    if special == "resonance":
        return "Technomancer"
    if special != "magic":
        return "Mundane"
    types = {str(i.get("type") or "") for i in items}
    casts = bool(types & {"spell", "ritual"})
    if "adept_power" in types:
        return "Mystic Adept" if casts else "Adept"
    return "Magician"
