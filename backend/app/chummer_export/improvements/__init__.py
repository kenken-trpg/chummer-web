"""The improvements a `<bonus>` makes, as Chummer's `AddImprovementCollection`
makes them, for the export to write beside the row that owns the bonus.

Chummer never runs a bonus again when it opens a file: it keeps the saved
improvements as they are. So a quality, an implant or a power exported
without them does nothing there. Each tag this knows is read by the
function `AddImprovementCollection` would run for it, from the bonus, the
owner's rating and its pick; a tag it does not know makes nothing.
"""

from ._imp import _Imp, _text
from .bonus import _bonus_improvements
from .write import _with_rows, _write_improvements

__all__ = ["_Imp", "_bonus_improvements", "_text", "_with_rows", "_write_improvements"]
