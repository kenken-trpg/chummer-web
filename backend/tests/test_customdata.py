"""`customdata/` directories, merged into the vendored XML.

The merge happens on the XML tree, upstream of every loader, so an added
martial art is indistinguishable from one that shipped. These pin the four
amend shapes real custom data uses, the two matching rules that are easy to
get wrong (guid case, Unicode normalisation), and the upload handshake.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest
from starlette.testclient import TestClient

from app import dataset_store
from app.customdata import (
    MergeReport,
    apply_amend,
    apply_custom,
    build_overlay,
    dataset_hash,
    manifest_key,
)
from app.data_loader import Overlay, catalog, reset_catalog, using_customdata
from app.main import app


def _root(xml: str) -> ET.Element:
    return ET.fromstring(xml)


BASE = """
<chummer><martialarts>
  <martialart><id>a1</id><name>Aikido</name><source>RG</source>
    <techniques><technique><name>Throw</name></technique></techniques>
  </martialart>
  <martialart><id>a2</id><name>Boxing</name><source>RG</source><category>Sport</category>
    <bannedgrades><grade>Used</grade></bannedgrades>
  </martialart>
</martialarts></chummer>
"""


def test_an_amend_replaces_the_fields_it_names_and_leaves_the_rest() -> None:
    base = _root(BASE)
    report = MergeReport()
    apply_amend(
        base,
        _root(
            "<chummer><martialarts><martialart><id>a1</id><source>JCD</source><page>7</page></martialart></martialarts></chummer>"
        ),
        "f",
        report,
    )
    art = base.find("./martialarts/martialart")
    assert (art.findtext("source"), art.findtext("page")) == ("JCD", "7")
    assert art.findtext("name") == "Aikido", "the selector must not be treated as an edit"
    assert report.skipped == []


def test_addnode_appends_into_a_list_rather_than_replacing_it() -> None:
    base = _root(BASE)
    apply_amend(
        base,
        _root(
            '<chummer><martialarts><martialart><id>a1</id><techniques><technique amendoperation="addnode"><name>Kick</name></technique></techniques></martialart></martialarts></chummer>'
        ),
        "f",
        MergeReport(),
    )
    names = [t.findtext("name") for t in base.findall("./martialarts/martialart/techniques/technique")]
    assert names == ["Throw", "Kick"], "the existing technique must survive"


def test_remove_deletes_the_child_it_names() -> None:
    base = _root(BASE)
    apply_amend(
        base,
        _root(
            '<chummer><martialarts><martialart><id>a2</id><bannedgrades amendoperation="remove"/></martialart></martialarts></chummer>'
        ),
        "f",
        MergeReport(),
    )
    assert base.find("./martialarts/martialart[2]/bannedgrades") is None


def test_pathfilter_selects_by_a_field_instead_of_an_id() -> None:
    """One rule touching a whole category — how "no banned grades on cultured
    bioware" is written."""
    base = _root(BASE)
    apply_amend(
        base,
        _root(
            '<chummer><martialarts><martialart pathfilter="category=\'Sport\'"><bannedgrades amendoperation="remove"/></martialart></martialarts></chummer>'
        ),
        "f",
        MergeReport(),
    )
    assert base.find("./martialarts/martialart[2]/bannedgrades") is None


def test_a_rule_that_matches_nothing_is_reported_not_swallowed() -> None:
    """Custom data that half-applied is worse than custom data that refused:
    the sheet still looks right."""
    report = MergeReport()
    apply_amend(
        _root(BASE),
        _root("<chummer><martialarts><martialart><id>nope</id><source>X</source></martialart></martialarts></chummer>"),
        "f.xml",
        report,
    )
    assert report.applied == 0
    assert report.skipped == [("f.xml", "no <martialart> matches 'nope'")]


def test_custom_appends_new_entries() -> None:
    base = _root(BASE)
    report = MergeReport()
    apply_custom(
        base,
        _root("<chummer><martialarts><martialart><id>a3</id><name>New</name></martialart></martialarts></chummer>"),
        "f",
        report,
    )
    assert [a.findtext("name") for a in base.findall("./martialarts/martialart")] == ["Aikido", "Boxing", "New"]
    assert report.applied == 1


# --- matching the directory a settings file names ----------------------- #

MANIFEST = "<manifest><guid>5682BC90-4C83-11EF-A3FE-319D7CB90725</guid><version>0.1</version></manifest>"


def test_a_guid_matches_regardless_of_case() -> None:
    """Manifests write it upper-case and settings files lower-case."""
    assert manifest_key(MANIFEST.encode()) == "5682bc90-4c83-11ef-a3fe-319d7cb90725>0.1"


def test_a_japanese_directory_matches_across_unicode_normalisation() -> None:
    """A macOS filesystem hands over NFD; the XML naming it is NFC. Same
    directory, different bytes."""
    nfd = "NTS3A04_中古等級の培養バイオウェア"
    nfc = "NTS3A04_中古等級の培養バイオウェア"
    files = {
        f"{nfd}/manifest.xml": b"<manifest><guid>x</guid><version>1</version></manifest>",
        f"{nfd}/custom_martialarts.xml": b"<chummer><martialarts><martialart><id>z</id><name>Z</name></martialart></martialarts></chummer>",
    }
    _, report = build_overlay(files, [nfc])
    assert report.skipped == []
    assert report.applied == 1


def test_a_directory_the_settings_asked_for_but_nobody_supplied_is_named() -> None:
    _, report = build_overlay({}, ["some-guid>1.0"])
    assert report.skipped == [("some-guid>1.0", "the custom data for this entry was not supplied")]


def test_a_placeholder_file_with_no_root_element_is_not_an_error() -> None:
    """Published packs ship licence-header-only files; there is no rule in one
    to drop, so it is not something to report."""
    files = {
        "d/manifest.xml": b"<manifest><guid>g</guid><version>1</version></manifest>",
        "d/custom_martialarts.xml": b"<!-- just a licence header -->\n",
    }
    _, report = build_overlay(files, ["g>1"])
    assert report.skipped == []


def test_the_hash_changes_when_a_file_moves() -> None:
    """Path feeds the digest as well as content: renaming changes load order,
    which changes the result."""
    a = {"d/custom_x.xml": b"<chummer/>"}
    b = {"e/custom_x.xml": b"<chummer/>"}
    assert dataset_hash(a) != dataset_hash(b)
    assert dataset_hash(a) == dataset_hash(dict(a))


# --- through the loaders ------------------------------------------------ #


def test_the_overlay_reaches_the_catalog_and_leaves_no_trace_after() -> None:
    files = {
        "d/manifest.xml": b"<manifest><guid>g</guid><version>1</version></manifest>",
        "d/custom_martialarts.xml": "<chummer><martialarts><martialart><id>zz</id><name>新東京テスト</name><source>NTR</source></martialart></martialarts></chummer>".encode(),
    }
    before = len(catalog()["martial_arts"])
    trees, _ = build_overlay(files, ["g>1"])
    reset_catalog()
    try:
        with using_customdata(Overlay(key=dataset_hash(files), trees=trees)):
            arts = catalog()["martial_arts"]
            assert len(arts) == before + 1
            assert any(a["name"] == "新東京テスト" for a in arts)
        assert len(catalog()["martial_arts"]) == before, "the overlay must not leak out of the block"
    finally:
        reset_catalog()


# --- the upload handshake ----------------------------------------------- #


@pytest.fixture
def client() -> TestClient:
    dataset_store.reset()
    return TestClient(app)


_FILES = {
    "d/manifest.xml": "<manifest><guid>g</guid><version>1</version></manifest>",
    "d/custom_martialarts.xml": "<chummer><martialarts><martialart><id>zz</id><name>Z</name></martialart></martialarts></chummer>",
}


def test_a_character_whose_custom_data_the_server_lacks_gets_409(client: TestClient) -> None:
    """The browser holds the files and sends only their hash, so a cold server
    has to ask for them; the client uploads once and retries."""
    state = client.post("/api/characters/new").json()
    state["settings"] = {"name": "H", "books": [], "customdata": ["g>1"], "dataset": "nope"}
    res = client.post("/api/characters/patch", json={"state": state})
    assert res.status_code == 409
    assert res.json()["detail"]["key"] == "api.customDataMissing"


def test_uploading_the_files_lets_the_same_request_through(client: TestClient) -> None:
    up = client.post("/api/customdata", json={"files": _FILES, "customdata": ["g>1"]}).json()
    assert up["applied"] == 1
    state = client.post("/api/characters/new").json()
    state["settings"] = {"name": "H", "books": [], "customdata": ["g>1"], "dataset": up["dataset"]}
    assert client.post("/api/characters/patch", json={"state": state}).status_code == 200


def test_a_character_that_never_loaded_its_custom_data_still_computes(client: TestClient) -> None:
    """A settings file can name custom data the user has not supplied yet.
    Refusing would leave the character uncomputable rather than merely missing
    the entries those directories add — the editor says so on its own."""
    state = client.post("/api/characters/new").json()
    state["settings"] = {"name": "H", "books": [], "customdata": ["g>1"], "dataset": ""}
    assert client.post("/api/characters/patch", json={"state": state}).status_code == 200


def test_a_character_with_no_custom_data_never_needs_the_handshake(client: TestClient) -> None:
    state = client.post("/api/characters/new").json()
    assert client.post("/api/characters/patch", json={"state": state}).status_code == 200


def test_an_empty_upload_is_refused(client: TestClient) -> None:
    res = client.post("/api/customdata", json={"files": {}, "customdata": []})
    assert res.status_code == 400
    assert res.json()["detail"]["key"] == "api.customDataEmpty"


def test_the_same_files_with_different_directories_enabled_are_different_sets(client: TestClient) -> None:
    """Which directories are on, and in what order, changes the merge — so it
    is part of what the cache is keyed by."""
    up = client.post("/api/customdata", json={"files": _FILES, "customdata": ["g>1"]}).json()
    state = client.post("/api/characters/new").json()
    state["settings"] = {"name": "H", "books": [], "customdata": [], "dataset": up["dataset"]}
    # no directories enabled: nothing to merge, so nothing to ask for
    assert client.post("/api/characters/patch", json={"state": state}).status_code == 200
    state["settings"]["customdata"] = ["other>1"]
    assert client.post("/api/characters/patch", json={"state": state}).status_code == 409
