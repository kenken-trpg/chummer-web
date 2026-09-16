"""Hostile input at the three doors a visitor's file comes through.

`.chum5` imports, JSON imports and settings uploads all take a stranger's file.
The endpoints wrap every failure in a 400, so nothing here can reach a 500 —
but that wrapper is also what hides a crash: a save with one odd field is
refused whole, with a message that says nothing, and the exception only shows
up in the server log. The property worth holding is narrower than "no 500":

* `chum5_to_state` either reads the file or raises `NoticeError` — the error
  that carries a reason the user can act on — and a state it hands back
  computes without raising;
* `import_character` on JSON accepts it or rejects it through validation;
* `parse_settings_upload` accepts it or raises `ValueError`.

The seeds are real-shaped files, not noise: noise is refused at the first
byte and explores nothing. Each example takes one seed and damages it the way
a hand edit, a truncated download or a hostile author would — one element
dropped, duplicated, renamed or given a value no field expects.
"""

from __future__ import annotations

import lzma
import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from app.characters import import_character, new_character
from app.chummer_import import chum5_to_state
from app.notices import NoticeError
from app.settings_file import parse_settings_upload
from tests.chum5_fixtures import build_chum5
from tests.test_chummer_import import SAMPLE

#: 120 per property keeps CI quick. `FUZZ_EXAMPLES=5000` for a real hunt.
_FUZZ = settings(
    max_examples=int(os.environ.get("FUZZ_EXAMPLES") or 120),
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

#: Values no field expects: signs and sizes an int() will take and a rating
#: should not, spellings float() takes and int() does not, digits that are
#: not ASCII, and text where a number belongs.
_HOSTILE = st.sampled_from(
    [
        "",
        " ",
        "-1",
        "-2147483649",
        "99999999999999999999999999",
        "1e309",
        "NaN",
        "inf",
        "-0",
        "0x10",
        "１２",
        "٣",
        "3.5",
        "True",
        "maybe",
        "00000000-0000-0000-0000-000000000000",
        "x" * 5000,
        "‮evil",
        "<",
        "&amp;",
    ]
)


def _seeds() -> list[bytes]:
    rich = build_chum5(
        name="Fuzz",
        skills={"Pistols": 4, "Sneaking": 3},
        skill_specs={"Pistols": "Semi-Automatics"},
        groups={"Athletics": 2},
        knowledge=[{"name": "Alcohol", "rating": 3, "category": "Interest"}],
        qualities=["Ambidextrous"],
        karma=5,
        nuyen=1000,
    )
    seeds = [SAMPLE, rich]
    # Chummer's own test characters, when `make reconcile` has fetched them:
    # a real save reaches sections the two above never name. Absent in CI.
    vendored = Path(__file__).resolve().parents[1] / "vendor" / "chummer-tests"
    seeds += [p.read_bytes() for p in sorted(vendored.rglob("*.chum5"))[:8]]
    return seeds


_SEEDS = _seeds()


@st.composite
def _damaged_chum5(draw: st.DrawFn) -> bytes:
    root = ET.fromstring(draw(st.sampled_from(_SEEDS)))
    for _ in range(draw(st.integers(min_value=1, max_value=4))):
        nodes = list(root.iter())
        target = draw(st.sampled_from(nodes))
        parents = {child: parent for parent in root.iter() for child in parent}
        action = draw(st.sampled_from(["text", "drop", "dup", "rename", "empty", "nest"]))
        if action == "text":
            target.text = draw(_HOSTILE)
        elif action == "drop" and target in parents:
            parents[target].remove(target)
        elif action == "dup" and target in parents:
            parents[target].append(ET.fromstring(ET.tostring(target)))
        elif action == "rename" and target is not root:
            target.tag = draw(st.sampled_from([t.tag for t in nodes]))
        elif action == "empty":
            for child in list(target):
                target.remove(child)
            target.text = None
        elif action == "nest":
            ET.SubElement(target, draw(st.sampled_from([t.tag for t in nodes]))).text = draw(_HOSTILE)
    raw = ET.tostring(root, encoding="utf-8")
    shape = draw(st.sampled_from(["plain", "truncated", "lzma", "bom"]))
    if shape == "truncated":
        return raw[: draw(st.integers(min_value=0, max_value=len(raw)))]
    if shape == "lzma":
        return lzma.compress(raw, format=lzma.FORMAT_ALONE)
    if shape == "bom":
        return b"\xef\xbb\xbf" + raw
    return raw


def _read_or_refuse(raw: bytes) -> None:
    """What the import endpoint does, minus the catch-all that would hide a
    crash: read the file, compute it, and let only a `NoticeError` stop that."""
    try:
        state, _warnings = chum5_to_state(raw)
        state.pop("_warnings", None)
        import_character(state)
    except NoticeError:
        pass


@_FUZZ
@given(_damaged_chum5())
def test_a_damaged_save_is_read_or_refused_with_a_reason(raw: bytes) -> None:
    _read_or_refuse(raw)


def _state_seed() -> dict[str, Any]:
    state = new_character(None).model_dump()
    state.pop("derived", None)
    return state


_STATE = _state_seed()

#: Values of the wrong type or an absurd size, for any field.
_JUNK = st.one_of(
    _HOSTILE,
    st.integers(min_value=-(10**12), max_value=10**12),
    st.floats(allow_nan=True, allow_infinity=True),
    st.booleans(),
    st.none(),
    st.lists(_HOSTILE, max_size=3),
    st.dictionaries(_HOSTILE, st.integers(min_value=-(10**9), max_value=10**9), max_size=3),
)


@st.composite
def _damaged_state(draw: st.DrawFn) -> dict[str, Any]:
    state = dict(_STATE)
    keys = sorted(state)
    for _ in range(draw(st.integers(min_value=1, max_value=4))):
        key = draw(st.sampled_from(keys))
        current = state[key]
        if isinstance(current, dict) and current and draw(st.booleans()):
            inner = dict(current)
            inner[draw(st.sampled_from(sorted(inner)))] = draw(_JUNK)
            state[key] = inner
        else:
            state[key] = draw(_JUNK)
    return state


@_FUZZ
@given(_damaged_state())
def test_a_damaged_json_character_is_accepted_or_fails_validation(payload: dict[str, Any]) -> None:
    try:
        import_character(payload)
    except (ValidationError, NoticeError):
        pass


_SETTINGS_SEED = (
    b"<settings><name>House</name><buildmethod>Priority</buildmethod>"
    b"<qualitykarmalimit>25</qualitykarmalimit><maxskillratingcreate>6</maxskillratingcreate>"
    b"<karmacost><karmaattribute>5</karmaattribute><karmaspecialization>7</karmaspecialization></karmacost>"
    b"<cyberlegmovement>False</cyberlegmovement>"
    b"<bannedwaregrades><grade>Betaware</grade></bannedwaregrades>"
    b"<customdatadirectorynames><directoryname>x</directoryname></customdatadirectorynames>"
    b"</settings>"
)


@st.composite
def _damaged_settings(draw: st.DrawFn) -> bytes:
    root = ET.fromstring(_SETTINGS_SEED)
    for _ in range(draw(st.integers(min_value=1, max_value=4))):
        target = draw(st.sampled_from(list(root.iter())))
        if draw(st.booleans()):
            target.text = draw(_HOSTILE)
        else:
            ET.SubElement(target, draw(st.sampled_from([t.tag for t in root.iter()]))).text = draw(_HOSTILE)
    raw = ET.tostring(root, encoding="utf-8")
    if draw(st.booleans()):
        raw = raw[: draw(st.integers(min_value=0, max_value=len(raw)))]
    return raw


@_FUZZ
@given(_damaged_settings())
def test_a_damaged_settings_file_is_read_or_refused(raw: bytes) -> None:
    try:
        parse_settings_upload(raw)
    except ValueError:
        pass


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"<character/>",
        b"<character><metatype/></character>",
        b"\xff\xfe" + "<character/>".encode("utf-16-le"),
        b"<?xml version='1.0' encoding='latin-1'?><character><name>\xe9</name></character>",
        b"<character>" + b"<qualities>" * 2000 + b"</qualities>" * 2000 + b"</character>",
        # found by the properties above: int(float("1e309")) is an OverflowError
        b"<character><metatype>Human</metatype><attributes><attribute><name>BOD</name>"
        b"<metatypemin>1e309</metatypemin><base>NaN</base></attribute></attributes></character>",
        # and an unknown metatype was a KeyError from deep inside the engine
        b"<character><metatype>Dracoform</metatype></character>",
    ],
    # Short names, not the bytes: pytest puts the test id in an environment
    # variable, and Windows refuses one past 32,767 characters — the deep
    # nesting case alone is 26 KB.
    ids=["empty", "bare", "no-metatype", "utf-16", "latin-1", "deep", "non-finite", "unknown-metatype"],
)
def test_odd_but_plausible_files_are_read_or_refused(raw: bytes) -> None:
    _read_or_refuse(raw)


@pytest.mark.parametrize("value", ["1e309", "-1e309", "NaN", "inf"])
def test_a_settings_number_that_is_not_finite_is_ignored(value: str) -> None:
    settings_state, _ = parse_settings_upload(
        f"<settings><name>H</name><maxskillratingcreate>{value}</maxskillratingcreate></settings>".encode()
    )
    assert settings_state.chargen_skill_max is None
