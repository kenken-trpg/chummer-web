"""The ruleset a new character starts under: 日本語環境.

Every book with a Japanese edition — the SR5 core book and Run & Gun — plus
the Shadowrun Codex, the Japanese compendium that reprints parts of the
untranslated supplements (see data_loader/codex.py). That is what a table
playing from Japanese books can actually open.

It is this app's preset, not one of Chummer's: it is offered beside them in the
settings pulldown, but kept out of `load_settings_presets`, which is also how a
.chum5 import and export find Chummer's own preset ids.
"""

from __future__ import annotations

from typing import Any

from .models.settings import SettingsState

NAME = "日本語環境"
BOOKS = ("SR5", "RG", "SRCX")

PRESET: dict[str, Any] = {
    "id": "chummer-web-ja",
    "name": NAME,
    "build_method": "Priority",
    "books": list(BOOKS),
    "sum_to_ten": 10,
    "quality_karma_limit": 25,
    "priority_table": "Standard",
    "nuyen_max_bp": 10,
}


def settings() -> SettingsState:
    return SettingsState(name=NAME, books=list(BOOKS))
