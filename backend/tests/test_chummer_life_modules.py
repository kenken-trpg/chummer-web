"""Life modules through a ``.chum5``.

Only this app's own files can be read back: Chummer saves what a module
granted and not which option was picked to grant it, so a file without this
app's ``<lifemodulechoices>`` is refused rather than silently stripped of its
modules. The export still writes Chummer's own shape, so Chummer can open it.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.notices import NoticeError
from tests.chum5_fixtures import _loop, build_chum5
from tests.notice_asserts import has

#: One module per stage, so the character has no missing-stage error. The
#: first four take no choices; `Decker` asks which Codeslinger action.
NATIONALITY = "604831d9-0fdc-4579-aa7e-bc5d99bcee5d"  # Elves/Humans
FORMATIVE = "111f66cd-be47-4e1e-8ee7-15cc67ed2cc8"  # Farm Living
TEEN = "737d188a-85b5-47d8-91f2-39863983b464"  # Factory Child Worker
EDUCATION = "5a2eee69-cedb-403e-9649-fdc9a1377374"  # Skipped Further Education
DECKER = "93c2318e-261e-48c6-ab79-72205ca94e00"  # Decker (Real Life)

_MODULES = [NATIONALITY, FORMATIVE, TEEN, EDUCATION, DECKER]
_ATTRIBUTES = {
    "BOD": 2,
    "AGI": 2,
    "REA": 2,
    "STR": 2,
    "CHA": 2,
    "INT": 3,
    "LOG": 3,
    "WIL": 2,
    "EDG": 2,
    "MAG": 0,
    "RES": 0,
}
#: The occurrence prefix is the module's index in the list above.
_CHOICES = {"4:q0": "Hack on the Fly"}

_XML = build_chum5(
    name="Lifer",
    metatype="Human",
    build_method="LifeModule",
    # The full set, as `default_attributes` gives a character made here and as
    # Chummer's own saves carry it. A life module character is computed on a
    # copy (see `engine.compute`), so nothing fills in a name left out.
    attributes=_ATTRIBUTES,
    life_modules=_MODULES,
    life_module_choices=_CHOICES,
)


def test_a_life_module_character_is_a_fixed_point() -> None:
    _, first, again = _loop(_XML)
    assert first.build_method == "LifeModule"
    assert first.life_modules == _MODULES
    assert first.life_module_choices == _CHOICES
    assert again.life_modules == first.life_modules
    assert again.life_module_choices == first.life_module_choices
    # the grants are re-derived, not read from the file, so they have to agree
    assert not first.derived["errors"]
    assert again.derived["totals"] == first.derived["totals"]


def test_the_export_writes_the_shape_chummer_reads() -> None:
    _, first, _ = _loop(_XML)
    root = ET.fromstring(state_to_chum5(first))
    assert root.findtext("buildmethod") == "LifeModule"
    modules = [q for q in root.findall("./qualities/quality") if q.findtext("qualitytype") == "LifeModule"]
    assert [q.findtext("sourceid") for q in modules] == _MODULES
    # `Quality.cs` writes `<stage>` only for this type, and reads it only for
    # this type; it is what orders the stages on Chummer's own screen.
    assert [q.findtext("stage") for q in modules] == [
        "Nationality",
        "Formative Years",
        "Teen Years",
        "Further Education",
        "Real Life",
    ]
    assert {q.findtext("qualitysource") for q in modules} == {"LifeModule"}
    assert modules[0].findtext("name") == "Elves/Humans"
    # the answers ride beside them, in the element Chummer ignores
    assert [(c.findtext("key"), c.findtext("value")) for c in root.findall("./lifemodulechoices/choice")] == [
        ("4:q0", "Hack on the Fly")
    ]


def test_the_modules_do_not_come_back_as_ordinary_qualities() -> None:
    """`qualitysource` is `LifeModule`, which the quality reader skips — a
    module read as a quality would be an unknown-quality warning and, worse,
    a quality the character never took."""
    state, warnings = chum5_to_state(_XML)
    assert not has(warnings, "engine.import.skippedUnknown")
    assert state["life_modules"] == _MODULES


def test_a_file_chummer_wrote_is_refused_rather_than_read_without_its_picks() -> None:
    root = ET.fromstring(_XML)
    picks = root.find("lifemodulechoices")
    assert picks is not None
    root.remove(picks)
    with pytest.raises(NoticeError) as caught:
        chum5_to_state(ET.tostring(root))
    assert caught.value.notice["key"] == "engine.life.chum5Unsupported"


def test_an_empty_picks_element_still_marks_the_file_as_this_app_s() -> None:
    """A character whose modules ask nothing has no answers to record, and the
    element is written empty. That is not a Chummer file."""
    xml = build_chum5(
        name="No picks",
        build_method="LifeModule",
        attributes=_ATTRIBUTES,
        life_modules=[NATIONALITY, FORMATIVE, TEEN, EDUCATION],
    )
    state, _ = chum5_to_state(xml)
    assert state["life_modules"] == [NATIONALITY, FORMATIVE, TEEN, EDUCATION]


def test_a_module_missing_from_the_data_stops_the_import() -> None:
    """Dropping one module would shift every later module's answers onto the
    wrong module, so there is no partial read."""
    root = ET.fromstring(_XML)
    first = next(q for q in root.findall("./qualities/quality") if q.findtext("qualitytype") == "LifeModule")
    sourceid = first.find("sourceid")
    assert sourceid is not None
    sourceid.text = "00000000-0000-0000-0000-000000000000"
    with pytest.raises(NoticeError) as caught:
        chum5_to_state(ET.tostring(root))
    assert caught.value.notice["key"] == "engine.life.chum5ModuleUnknown"
