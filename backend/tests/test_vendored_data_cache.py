"""Vendored data files are parsed once and shared, so nobody may edit them."""

from __future__ import annotations

import os
import xml.etree.ElementTree as ET

import pytest

from app.data_loader import _xml
from tests.chum5_fixtures import _loop, build_chum5


def test_a_file_is_parsed_once_and_again_when_it_changes(tmp_path, monkeypatch):
    monkeypatch.setattr(_xml, "DATA_DIR", tmp_path)
    path = tmp_path / "things.xml"
    path.write_text("<chummer><thing>a</thing></chummer>")

    first = _xml.parse_data("things.xml")
    assert _xml.parse_data("things.xml") is first

    path.write_text("<chummer><thing>bb</thing></chummer>")
    os.utime(path, ns=(path.stat().st_atime_ns, path.stat().st_mtime_ns + 1_000_000))
    assert _xml.parse_data("things.xml").findtext("thing") == "bb"
    assert _xml.data_root("missing.xml") is None


def test_an_export_leaves_the_shared_data_as_it_found_it():
    """The cache is only safe while every writer copies first. A round trip
    through the exporter touches most of the files it reads, so compare them
    byte for byte before and after."""
    if _xml.data_root("qualities.xml") is None:
        pytest.skip("vendored Chummer data not fetched")
    xml = build_chum5(
        name="Cache",
        metatype="Troll",
        talent="Adept",
        priorities=("D", "B", "A", "C", "E"),
        attributes={"BOD": 5, "AGI": 4, "REA": 3, "STR": 5, "CHA": 2, "INT": 3, "LOG": 2, "WIL": 3},
        skills={"Pistols": 3},
        qualities=["Ambidextrous", "Toughness"],
        powers=[{"name": "Improved Reflexes"}, {"name": "Killing Hands"}],
        armor=[{"name": "Armor Jacket"}],
        weapons=[{"name": "Ares Predator V"}, {"name": "Combat Axe"}],
        gear=[{"name": "Commlink"}, {"name": "Medkit"}],
        vehicles=[{"name": "Dodge Scoot"}],
        lifestyles=[{"name": "Low", "months": 1}],
    )
    _loop(xml)  # fills the cache with every file an export reads
    cached = {key: ET.tostring(root) for key, root in _cached_roots()}
    assert len(cached) > 5
    _loop(xml)
    assert {key: ET.tostring(root) for key, root in _cached_roots()} == cached


def _cached_roots() -> list[tuple[str, ET.Element]]:
    """Every data file as the cache holds it (a file not read yet is parsed
    now, which is harmless: nothing has had the chance to change it)."""
    return [(path.name, _xml.parse_data(path.name)) for path in sorted(_xml.DATA_DIR.glob("*.xml"))]
