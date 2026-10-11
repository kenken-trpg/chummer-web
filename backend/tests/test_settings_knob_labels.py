"""Every knob this app can report as unsupported must have a sentence.

`SettingsState.unsupported` carries raw Chummer tag names, and the front end
turns them into readable lines from the map in `frontend/lib/settings-knobs.ts`.
A tag with no entry there falls back to the tag itself — which is what the
report looked like before, and is unreadable for a GM comparing a house ruleset
against the sheet. The set of tags that can appear is knowable: it is every
leaf in the vendored `settings.xml` presets that `settings_file.py` does not
read. So it is checked here rather than discovered by a player.

A newer Chummer can of course write a tag this list predates; that is what the
fallback is for. This only stops the known ones going unnamed.
"""

from __future__ import annotations

from pathlib import Path

from app.data_loader._xml import DATA_DIR, parse_vendored
from app.settings_file import (
    _ATTR_FIELDS,
    _BOOL_FIELDS,
    _HANDLED_ELSEWHERE,
    _INT_FIELDS,
    _KARMA_FIELDS,
    _flatten,
)

REPO = Path(__file__).resolve().parents[2]
KNOBS = REPO / "frontend" / "lib" / "settings-knobs.ts"
JA = REPO / "frontend" / "lib" / "i18n" / "locales" / "ja" / "chargen.ts"


def _reportable() -> set[str]:
    """Tags the shipped presets can differ on that nothing here implements."""
    root = parse_vendored(DATA_DIR / "settings.xml")
    read = set(_INT_FIELDS) | set(_KARMA_FIELDS) | set(_BOOL_FIELDS) | _HANDLED_ELSEWHERE
    tags: set[str] = set()
    for setting in root.findall("./settings/setting"):
        tags |= set(_flatten(setting))
    # the expression knobs are read, but reported when their shape is one this
    # app cannot evaluate — so they reach the same list
    return (
        (tags - read)
        | set(_ATTR_FIELDS)
        | {
            "chargenkarmatonuyenexpression",
            "contactpointsexpression",
            "knowledgepointsexpression",
        }
    )


def test_every_reportable_knob_has_a_label() -> None:
    labels, wording = KNOBS.read_text(), JA.read_text()
    missing = sorted(tag for tag in _reportable() if f"settings.knob.{tag}" not in labels)
    assert not missing, f"no line in settings-knobs.ts for: {missing}"
    unworded = sorted(tag for tag in _reportable() if f'"settings.knob.{tag}"' not in wording)
    assert not unworded, f"no Japanese wording for: {unworded}"
