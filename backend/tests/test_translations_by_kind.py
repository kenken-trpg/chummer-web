"""`ja_overrides/by_kind.json`: readings for names another kind of thing shares."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET

import pytest

from app.data_loader import OVERRIDE_DIR
from app.data_loader._xml import LANG_DIR, data_root
from app.data_loader.loaders.translations import TRANSLATION_KINDS, load_translations_by_kind

#: kind -> (data file, element) its names come from
SOURCES = {
    "armor": ("armor.xml", "armor"),
    "critter_power": ("critterpowers.xml", "power"),
    "cyberware": ("cyberware.xml", "cyberware"),
    "gear": ("gear.xml", "gear"),
    "knowledge_skill": ("skills.xml", "knowledgeskills/skill"),
    "power": ("powers.xml", "power"),
    "skill": ("skills.xml", "skills/skill"),
}

#: (file, name) pairs whose flat-table reading is not the file's own, as of
#: 2026-09-22, after by_kind.json. Nearly all are a borrowed reading that is
#: right (the critter power Fear showing the spirit power's 恐怖) or spelling
#: drift (手裏剣 / シュリケン) — see the PR that added this file. The ceiling
#: is here so a new collision from an upstream update gets looked at.
KNOWN_MISMATCHES = 75


def test_every_kind_has_a_source():
    assert set(SOURCES) == set(TRANSLATION_KINDS)


def test_the_overlay_is_read():
    assert json.loads((OVERRIDE_DIR / "by_kind.json").read_text(encoding="utf-8")) == load_translations_by_kind()


@pytest.mark.parametrize("kind", sorted(SOURCES))
def test_every_name_exists_in_its_kind(kind):
    names = load_translations_by_kind().get(kind, {})
    filename, element = SOURCES[kind]
    root = data_root(filename)
    if root is None:
        pytest.skip("vendored Chummer data not fetched")
    present = {(el.findtext("name") or "").strip() for el in root.findall(f".//{element}")}
    assert set(names) <= present


def _mismatches() -> int:
    from app.data_loader.loaders.translations import load_translations

    flat = load_translations()
    overlay = json.loads((OVERRIDE_DIR / "data.json").read_text(encoding="utf-8"))
    covered = {name for names in load_translations_by_kind().values() for name in names}
    root = ET.parse(LANG_DIR / "ja-jp_data.xml").getroot()  # noqa: S314 -- vendored lang file
    found = set()
    for section in root:
        file = section.get("file") or section.tag
        for node in section.iter():
            name = (node.findtext("name") or "").strip()
            trans = (node.findtext("translate") or "").strip()
            if not name or not trans or name in overlay or name in covered or file == "books.xml":
                continue
            shown = flat.get(name)
            if shown != trans and not (trans == name and shown == name):
                found.add((file, name))
    return len(found)


def test_no_new_cross_kind_collisions():
    if not (LANG_DIR / "ja-jp_data.xml").exists():
        pytest.skip("vendored lang file not fetched")
    assert _mismatches() <= KNOWN_MISMATCHES
