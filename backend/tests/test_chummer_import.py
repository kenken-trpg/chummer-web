"""Chummer5a .chum5 / .chum5lz import (see backend/app/chummer_import.py)."""

from __future__ import annotations

import lzma

import pytest

from app.characters import import_character
from app.chummer_import import chum5_to_state, decompress_chum5lz

SAMPLE = b"""<?xml version="1.0" encoding="utf-8"?>
<character>
  <name>Realname</name><alias>Jax</alias>
  <metatype>Elf</metatype><metavariant>None</metavariant>
  <buildmethod>Priority</buildmethod><created>False</created>
  <priorities>
    <prioritymetatype>D</prioritymetatype><priorityattributes>B</priorityattributes>
    <priorityspecial>A</priorityspecial><priorityskills>C</priorityskills>
    <priorityresources>E</priorityresources><prioritytalent>Magician</prioritytalent>
  </priorities>
  <attributes>
    <attribute><name>BOD</name><metatypemin>1</metatypemin><base>2</base><karma>0</karma></attribute>
    <attribute><name>LOG</name><metatypemin>1</metatypemin><base>4</base><karma>1</karma></attribute>
    <attribute><name>MAG</name><metatypemin>1</metatypemin><base>5</base><karma>0</karma></attribute>
    <attribute><name>ESS</name><base>6</base></attribute>
  </attributes>
  <skills>
    <skills>
      <skill><name>Spellcasting</name><base>5</base><karma>1</karma>
        <specializations><spec><name>Combat</name></spec></specializations></skill>
    </skills>
    <groups><group><name>Stealth</name><base>2</base><karma>0</karma></group></groups>
    <knoskills>
      <skill><name>Sperethiel</name><type>Language</type><isnativelanguage>True</isnativelanguage></skill>
      <skill><name>Magical Theory</name><type>Academic</type><base>3</base></skill>
    </knoskills>
  </skills>
  <qualities>
    <quality><name>Focused Concentration</name><qualitysource>Selected</qualitysource></quality>
    <quality><name>Elf</name><qualitysource>Metatype</qualitysource></quality>
    <quality><name>Totally Made Up Quality</name><qualitysource>Selected</qualitysource></quality>
  </qualities>
  <spells>
    <spell><name>Acid Stream</name><category>Combat</category></spell>
    <spell><name>Nonexistent Spell</name></spell>
  </spells>
  <tradition><name>Hermetic</name></tradition>
  <lifestyles><lifestyle><baselifestyle>Medium</baselifestyle><months>2</months></lifestyle></lifestyles>
  <contacts><contact><name>Fixer Sam</name><role>Fixer</role><connection>3</connection><loyalty>2</loyalty></contact></contacts>
</character>"""


def test_maps_core_identity_and_priorities() -> None:
    st, _ = chum5_to_state(SAMPLE)
    assert st["name"] == "Jax"  # alias beats name
    assert st["metatype"] == "Elf"
    assert st["metavariant"] is None  # "None" -> None
    assert st["talent"] == "Magician"
    assert st["build_method"] == "Priority"
    assert st["career"] is False
    assert st["priorities"] == {
        "Heritage": "D",
        "Attributes": "B",
        "Talent": "A",
        "Skills": "C",
        "Resources": "E",
    }


def test_attributes_fold_in_min_base_karma_and_drop_essence() -> None:
    st, _ = chum5_to_state(SAMPLE)
    # Chummer <base> is spend above the metatype minimum: min 1 + base 4 + karma 1
    assert st["attributes"]["LOG"] == 6
    assert st["attributes"]["MAG"] == 6  # min 1 + base 5
    assert st["attributes"]["BOD"] == 3  # min 1 + base 2
    assert "ESS" not in st["attributes"] and "ESSENCE" not in st["attributes"]


def test_skills_groups_knowledge_native() -> None:
    st, _ = chum5_to_state(SAMPLE)
    assert st["skills"]["Spellcasting"] == 6
    assert st["skill_specializations"]["Spellcasting"] == "Combat"
    assert st["skill_groups"]["Stealth"] == 2
    assert st["knowledge_skills"] == {"Magical Theory": 3}
    assert st["native_languages"] == ["Sperethiel"]


def test_unresolved_entries_become_warnings_not_errors() -> None:
    st, warnings = chum5_to_state(SAMPLE)
    assert len(st["quality_ids"]) == 1  # Selected only; Metatype grant skipped
    assert len(st["spells"]) == 1  # Acid Stream resolved, nonexistent dropped
    assert any("Totally Made Up Quality" in w for w in warnings)
    assert any("Nonexistent Spell" in w for w in warnings)


def test_by_name_resolution_for_tradition_lifestyle_contact() -> None:
    st, _ = chum5_to_state(SAMPLE)
    assert st.get("tradition_id")
    assert st["lifestyles"] and st["lifestyles"][0]["months"] == 2
    assert st["contacts"][0]["name"] == "Fixer Sam"


def test_imported_state_validates_and_computes() -> None:
    st, _ = chum5_to_state(SAMPLE)
    ch = import_character({k: v for k, v in st.items() if k != "_warnings"})
    assert ch.id
    assert isinstance(ch.derived, dict)  # compute() ran


def test_decompress_passes_plain_xml_through() -> None:
    assert decompress_chum5lz(b"<?xml ?><character/>").startswith(b"<?xml")
    assert decompress_chum5lz(b"\xef\xbb\xbf<character/>").startswith(b"\xef\xbb\xbf")


def test_decompress_reads_legacy_lzma() -> None:
    payload = lzma.compress(SAMPLE, format=lzma.FORMAT_ALONE)
    assert decompress_chum5lz(payload).lstrip().startswith(b"<?xml")


def test_decompress_reads_chummer_chum5lz_layout() -> None:
    """Chummer LzmaHelper writes 5-byte props + 8-byte size (0xFF*8 with the
    end marker it always uses) + raw LZMA1 — verify that exact byte layout."""
    alone = bytearray(lzma.compress(SAMPLE, format=lzma.FORMAT_ALONE))
    alone[5:13] = b"\xff" * 8  # size field as Chummer writes it (eos = true)
    assert decompress_chum5lz(bytes(alone)) == SAMPLE


def test_decompress_reads_xz() -> None:
    assert decompress_chum5lz(lzma.compress(SAMPLE)).lstrip().startswith(b"<?xml")


def test_decompress_rejects_garbage_with_hint() -> None:
    with pytest.raises(ValueError, match="非圧縮の .chum5"):
        decompress_chum5lz(b"\x00\x01\x02not-compressed-not-xml\xff\xfe")


def test_decompress_rejects_bomb_over_the_size_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.chummer_import as ci

    monkeypatch.setattr(ci, "_MAX_DECOMPRESSED_BYTES", 64 * 1024)
    # ~4 MB of a repeating byte -> a tiny FORMAT_ALONE payload
    bomb = lzma.compress(b"<character>" + b" " * (4 * 1024 * 1024) + b"</character>", format=lzma.FORMAT_ALONE)
    assert len(bomb) < 64 * 1024
    with pytest.raises(ValueError, match="非圧縮の .chum5"):
        ci.decompress_chum5lz(bomb)


def test_non_character_xml_rejected() -> None:
    with pytest.raises(ValueError, match="character"):
        chum5_to_state(b"<notacharacter><foo/></notacharacter>")


def test_xml_entity_expansion_is_blocked() -> None:
    # a "billion laughs" style payload — defusedxml must refuse it, not expand it
    evil = (
        b'<?xml version="1.0"?>'
        b'<!DOCTYPE lolz [<!ENTITY lol "lol">'
        b'<!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">'
        b'<!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">]>'
        b"<character>&lol3;</character>"
    )
    with pytest.raises(ValueError, match="解析できませんでした"):
        chum5_to_state(evil)
