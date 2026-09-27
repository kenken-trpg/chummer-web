"""What a character loses on the way through the キャラシテンプレート .xlsx.

The template is lossier than a .chum5 by a wide margin, and for reasons worth
saying out loud rather than listing as rules:

* **It is a fixed grid.** Ten qualities, twenty spells, twenty adept powers,
  thirty implants, seven devices, twenty contacts, twenty-five knowledge skills.
* **Several of its dropdowns are shorter than the book.** Five metatypes, six
  kinds of magic user, five implant grades, two build methods.
* **All the equipment shares one free-text column.** A name that two of the
  book's lists both hold comes back under whichever the import tries first, so a
  grenade kept as gear can come back as a weapon.

Rather than a rule per case, this writes the file, reads it back and compares —
so the report is right by construction, and stays right as the sheets change.
"""

from __future__ import annotations

from ..characters import import_character
from ..export_check import differences
from ..models import CharacterState
from ..notices import Notice
from ..xlsx_import import xlsx_to_state
from . import state_to_xlsx, xlsx_limits

__all__ = ["roundtrip_differences"]


def roundtrip_differences(state: CharacterState) -> list[Notice]:
    """What the character would look like after being written to the template's
    .xlsx and read back, as notices. Empty when it comes back the same.

    The equipment rows the re-import could not match are counted among the
    losses rather than offered for confirmation: this is asked before the
    download, and what it answers is "how much of this character does the file
    carry", not "what should it have been".
    """
    first = import_character(state.model_dump())
    again = import_character(xlsx_to_state(state_to_xlsx(first))[0])
    return xlsx_limits(first) + differences(first, again)
