"""Hostile input at the four doors a visitor's file comes through.

`.chum5` imports, JSON imports, settings uploads and custom-data trees all take
a stranger's file. The endpoints wrap every failure in a 400, so nothing here can reach a 500 —
but that wrapper is also what hides a crash: a save with one odd field is
refused whole, with a message that says nothing, and the exception only shows
up in the server log. The property worth holding is narrower than "no 500":

* `chum5_to_state` either reads the file or raises `NoticeError` — the error
  that carries a reason the user can act on — and a state it hands back
  computes without raising;
* `fvtt_to_state` does the same for a Foundry VTT actor;
* `import_character` on JSON accepts it or rejects it through validation;
* `parse_settings_upload` accepts it or raises `ValueError`;
* `decompress_chum5lz` unwraps within its size ceiling or raises `NoticeError`;
* `build_overlay` returns — every problem there is a row in its report, not an
  exception — and never edits the base tree it copied.

A last property goes through the endpoints instead of around them, for the other
half of the claim: whatever gets past all of the above, the caller sees a 4xx
with a notice and never a 5xx.

The seeds are real-shaped files, not noise: noise is refused at the first
byte and explores nothing. Each example takes one seed and damages it the way
a hand edit, a truncated download or a hostile author would — one element
dropped, duplicated, renamed or given a value no field expects.
"""

from __future__ import annotations

import copy
import gzip
import lzma
import os
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from app.characters import import_character, new_character
from app.chummer_import import chum5_to_state, decompress_chum5lz
from app.chummer_import.container import _MAX_DECOMPRESSED_BYTES
from app.customdata import build_overlay
from app.data_loader._xml import MAX_UNTRUSTED_DEPTH, MAX_UNTRUSTED_ELEMENTS, parse_untrusted
from app.fvtt_import import fvtt_to_state
from app.notices import NoticeError
from app.settings_file import parse_settings_upload
from tests.chum5_fixtures import build_chum5
from tests.test_chummer_import import SAMPLE
from tests.test_fvtt_import import _geared

#: 120 per property keeps CI quick, and 30 on a laptop (no `CI` in the
#: environment) keeps `pytest -q` a matter of seconds; CI is where the full run
#: happens. `.github/workflows/audit.yml` raises it: 500 on a pull request,
#: 5,000 on the weekly run, which is the real hunt.
_FUZZ = settings(
    max_examples=int(os.environ.get("FUZZ_EXAMPLES") or (120 if os.environ.get("CI") else 30)),
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


# --- Foundry VTT actors -------------------------------------------------------
#
# The same door as `.chum5`, a different shape: nested JSON whose every field a
# stranger chose. `fvtt_to_state` owes the same answer — a state that computes,
# or a `NoticeError`.


def _paths(node: Any, here: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    found = [here]
    if isinstance(node, dict):
        for key, value in node.items():
            found += _paths(value, (*here, key))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            found += _paths(value, (*here, i))
    return found


@st.composite
def _damaged_fvtt(draw: st.DrawFn) -> Any:
    actor = copy.deepcopy(_FVTT_SEED)
    for _ in range(draw(st.integers(min_value=1, max_value=4))):
        path = draw(st.sampled_from(_paths(actor)))
        if not path:
            return draw(_JUNK)
        parent = actor
        for step in path[:-1]:
            parent = parent[step]
        if draw(st.booleans()):
            parent[path[-1]] = draw(_JUNK)
        elif isinstance(parent, dict):
            del parent[path[-1]]
        else:
            parent.append(copy.deepcopy(parent[path[-1]]))
    return actor


_FVTT_SEED = _geared()


@_FUZZ
@given(_damaged_fvtt())
def test_a_damaged_fvtt_actor_is_read_or_refused_with_a_reason(actor: Any) -> None:
    try:
        state, _warnings = fvtt_to_state(actor)
        import_character(state)
    except NoticeError:
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


# --- the container, on its own ------------------------------------------------
#
# `_damaged_chum5` compresses a *valid* save with the one format Chummer writes.
# The container has five more branches than that, tries each in turn, and is the
# only part of the import that allocates on the strength of a number the file
# supplies — so it gets its own property.


@st.composite
def _damaged_container(draw: st.DrawFn) -> bytes:
    inner = draw(st.sampled_from(_SEEDS))
    how = draw(
        st.sampled_from(
            [
                "lzma-alone",
                "xz",
                "zlib",
                "raw-deflate",
                "gzip",
                "double",
                "header-lies",
                "tail-cut",
                "head-cut",
                "spliced",
            ]
        )
    )
    if how == "lzma-alone":
        raw = lzma.compress(inner, format=lzma.FORMAT_ALONE)
    elif how == "xz":
        raw = lzma.compress(inner, format=lzma.FORMAT_XZ)
    elif how == "zlib":
        raw = zlib.compress(inner)
    elif how == "raw-deflate":
        deflate = zlib.compressobj(wbits=-zlib.MAX_WBITS)
        raw = deflate.compress(inner) + deflate.flush()
    elif how == "gzip":
        raw = gzip.compress(inner)
    elif how == "double":
        # compressed twice: the first layer decompresses to something that is
        # not XML, which must be a refusal rather than another round
        raw = lzma.compress(lzma.compress(inner, format=lzma.FORMAT_ALONE), format=lzma.FORMAT_ALONE)
    elif how == "header-lies":
        # the `.lzma` header's 8-byte size field, rewritten to a huge number.
        # Nothing may allocate on the strength of it.
        raw = bytearray(lzma.compress(inner, format=lzma.FORMAT_ALONE))
        raw[5:13] = draw(st.sampled_from([b"\xff" * 8, (2**62).to_bytes(8, "little"), b"\x00" * 8]))
        raw = bytes(raw)
    elif how == "spliced":
        first = lzma.compress(inner, format=lzma.FORMAT_ALONE)
        raw = first + lzma.compress(inner, format=lzma.FORMAT_ALONE)
    else:
        whole = lzma.compress(inner, format=lzma.FORMAT_ALONE)
        cut = draw(st.integers(min_value=0, max_value=len(whole)))
        raw = whole[cut:] if how == "head-cut" else whole[:cut]
    return raw


@_FUZZ
@given(_damaged_container())
def test_a_damaged_container_unwraps_within_its_ceiling_or_refuses(raw: bytes) -> None:
    """Either bytes come out, bounded, or a `NoticeError` says why — and what
    comes out is something the import as a whole reads or refuses.

    The ceiling is the point of the header-lying cases: a decompressor handed
    `2**62` as the uncompressed size must not try to hold it.

    Deliberately *not* asserted: that the output starts with `<?xml` or
    `<character`. The container sniffs a leading `<` and returns anything that
    has one as-is — a front-truncated LZMA stream that happens to begin with
    `0x3c` goes straight through, which the first version of this test called a
    failure. It is not the container's job: validation is `parse_untrusted`'s,
    one layer up, and the line below is what actually matters about such a file.
    """
    try:
        out = decompress_chum5lz(raw)
    except NoticeError:
        return
    assert len(out) <= _MAX_DECOMPRESSED_BYTES
    _read_or_refuse(out)


# --- the custom-data merge ---------------------------------------------------
#
# The fourth door, and the odd one out: the tree is a stranger's *and* it edits
# our own data files in place. A merge that raises takes the request with it;
# one that corrupts the base tree takes every later request too, since
# `build_overlay` hands out copies of a cached root.

_AMEND_FILES = ("amend_qualities.xml", "amend_martialarts.xml", "amend_weapons.xml")

#: A plausible amend rule, with the fields the merge dispatches on.
_AMEND_SEED = b"""<chummer>
  <qualities>
    <quality>
      <name>Ambidextrous</name>
      <karma>4</karma>
      <bonus><ambidextrous /></bonus>
    </quality>
  </qualities>
</chummer>"""


@st.composite
def _damaged_customdata(draw: st.DrawFn) -> tuple[dict[str, bytes], list[str]]:
    root = ET.fromstring(_AMEND_SEED)
    for _ in range(draw(st.integers(min_value=1, max_value=3))):
        nodes = list(root.iter())
        target = draw(st.sampled_from(nodes))
        action = draw(st.sampled_from(["text", "attr", "nest", "rename", "dup"]))
        parents = {child: parent for parent in root.iter() for child in parent}
        if action == "text":
            target.text = draw(_HOSTILE)
        elif action == "attr":
            # `amendoperation` / `addifnotfound` are what the merge branches on
            target.set(
                draw(st.sampled_from(["amendoperation", "addifnotfound", "isidnode", "xxx"])),
                draw(st.sampled_from(["append", "remove", "replace", "recurse", "True", "", "0"])),
            )
        elif action == "nest":
            ET.SubElement(target, draw(st.sampled_from([t.tag for t in nodes]))).text = draw(_HOSTILE)
        elif action == "rename" and target is not root:
            target.tag = draw(st.sampled_from([t.tag for t in nodes] + ["name", "id", "karma"]))
        elif action == "dup" and target in parents:
            parents[target].append(ET.fromstring(ET.tostring(target)))
    path = f"{draw(st.sampled_from(['NTS4C08', 'x', 'a/b']))}/{draw(st.sampled_from(_AMEND_FILES))}"
    files = {path: ET.tostring(root, encoding="utf-8")}
    enabled = draw(st.sampled_from([[path.split("/")[0]], ["missing"], [], ["NTS4C08", "NTS4C08"]]))
    return files, enabled


@_FUZZ
@given(_damaged_customdata())
def test_a_damaged_customdata_tree_merges_or_reports(payload: tuple[dict[str, bytes], list[str]]) -> None:
    """`build_overlay` has no refusal to raise — every problem is a row in the
    report — so the property is simply that it returns."""
    files, enabled = payload
    _trees, report = build_overlay(files, enabled)
    assert isinstance(report.applied, int)


def test_the_merge_never_edits_the_base_tree_it_copied() -> None:
    """The base roots are cached per process and handed to every request. A
    merge that edited one in place would leak a stranger's custom data into the
    next visitor's catalog — the one bug in this door that no status code shows.
    """
    from app.data_loader._xml import data_root

    before = ET.tostring(data_root("qualities.xml"))
    build_overlay(
        {
            "NTS4C08/amend_qualities.xml": _AMEND_SEED.replace(b"<karma>4</karma>", b"<karma>999</karma>"),
            "NTS4C08/amend_weapons.xml": b'<chummer><weapons><weapon amendoperation="remove"><name>Ares Predator V</name></weapon></weapons></chummer>',
        },
        ["NTS4C08"],
    )
    assert ET.tostring(data_root("qualities.xml")) == before


# --- the endpoints, as the browser reaches them -------------------------------


@pytest.mark.parametrize(
    ("route", "content_type"),
    [
        ("/api/characters/import-chummer", "application/octet-stream"),
        ("/api/settings/parse", "application/octet-stream"),
    ],
)
@pytest.mark.parametrize(
    "body",
    [
        b"",
        b"\x00" * 64,
        b"<character>",
        b"<?xml version='1.0'?><character><metatype>\xff\xfe</metatype></character>",
        lzma.compress(b"not xml at all", format=lzma.FORMAT_ALONE),
        b"%PDF-1.4\n",
    ],
    ids=["empty", "nuls", "unclosed", "bad-bytes", "lzma-not-xml", "wrong-file"],
)
def test_an_upload_route_answers_with_a_status_not_a_stack_trace(route: str, content_type: str, body: bytes) -> None:
    """The properties above bypass the endpoints to see the exceptions the
    catch-all hides. This is the other half: whatever gets through, the caller
    sees a 4xx with a notice, never a 5xx.

    A distinct source IP per case, so the shared rate limiter does not turn a
    later case into a 429.
    """
    from starlette.testclient import TestClient

    from app.main import app

    ip = f"198.51.100.{abs(hash((route, body))) % 200 + 1}"
    response = TestClient(app).post(
        route,
        content=body,
        headers={"content-type": content_type, "cf-connecting-ip": ip},
    )
    assert 400 <= response.status_code < 500, response.text
    assert response.status_code != 429, "rate limiter got in the way of the test"


# --- size ceilings ------------------------------------------------------------


@pytest.mark.parametrize(
    "xml",
    [
        pytest.param("<r>" + "<a/>" * (MAX_UNTRUSTED_ELEMENTS + 1) + "</r>", id="too-many-elements"),
        pytest.param("<a>" * (MAX_UNTRUSTED_DEPTH + 1) + "</a>" * (MAX_UNTRUSTED_DEPTH + 1), id="too-deep"),
    ],
)
def test_an_oversized_tree_is_refused_as_unparsable(xml: str) -> None:
    with pytest.raises(ET.ParseError, match="refused"):
        parse_untrusted(xml)


def test_a_tree_at_the_ceilings_still_parses() -> None:
    deep = "<a>" * MAX_UNTRUSTED_DEPTH + "</a>" * MAX_UNTRUSTED_DEPTH
    assert parse_untrusted(deep).tag == "a"
    wide = "<r>" + "<a/>" * (MAX_UNTRUSTED_ELEMENTS - 1) + "</r>"
    assert len(parse_untrusted(wide)) == MAX_UNTRUSTED_ELEMENTS - 1
