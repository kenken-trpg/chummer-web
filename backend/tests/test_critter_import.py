"""A critter save is refused by name, not mistaken for missing custom data.

Chummer builds critters from `critters.xml`, which this app does not load. The
import used to reach `find_metatype`, which said the metatype "is not in this
app's data (it may come from custom data)" — true of the lookup, wrong about
the cause, and it sent the reader off to find a custom-data pack that would not
have helped.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from app.chummer_import import chum5_to_state
from app.engine import compute
from app.models import CharacterState
from app.notices import NoticeError
from tests.chum5_fixtures import build_chum5


def _as_critter(raw: bytes) -> bytes:
    """The same save with Chummer's `<critter>` flag set."""
    root = ET.fromstring(raw)
    ET.SubElement(root, "critter").text = "True"
    return ET.tostring(root, encoding="utf-8")


def test_a_critter_says_it_is_a_critter() -> None:
    raw = _as_critter(build_chum5(name="Mittens", metatype="Hellhound"))
    with pytest.raises(NoticeError) as caught:
        chum5_to_state(raw)
    notice = caught.value.notice
    assert notice["key"] == "api.critterNotSupported"
    assert notice["params"]["name"] == "Hellhound"


def test_a_shapeshifter_still_imports() -> None:
    # Chummer saves a Shapeshifter with `<critter>True</critter>` and it is an
    # ordinary playable metatype (`Mittens Chargen.chum5` in Chummer's own test
    # files is one), so the flag alone must not refuse a character that works
    state, _ = chum5_to_state(_as_critter(build_chum5(metatype="Shapeshifter: Vulpine")))
    assert state["metatype"] == "Shapeshifter: Vulpine"


def test_an_unknown_metatype_without_the_flag_is_unchanged() -> None:
    # Not a critter: the import is best-effort and lets the name through, and
    # the custom-data message it always had comes from `compute` later. The
    # refusal above is deliberately narrower than "metatype not found".
    state, _ = chum5_to_state(build_chum5(metatype="Neo-Tokyo Houserule Elf"))
    assert state["metatype"] == "Neo-Tokyo Houserule Elf"
    with pytest.raises(NoticeError) as caught:
        compute(CharacterState(**state))
    assert caught.value.notice["key"] == "api.unknownMetatype"
