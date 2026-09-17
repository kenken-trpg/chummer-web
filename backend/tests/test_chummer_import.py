"""Chummer5a .chum5 / .chum5lz import (see backend/app/chummer_import/)."""

from __future__ import annotations

import lzma
import xml.etree.ElementTree as ET

import pytest

from app.characters import import_character
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state, decompress_chum5lz
from app.data_loader import catalog
from app.data_loader._xml import _text
from app.models import CharacterState
from app.notices import NoticeError
from tests.notice_asserts import has

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
    assert has(warnings, "engine.import.skippedUnknown", kind="engine.kind.quality", name="Totally Made Up Quality")
    assert has(warnings, "engine.import.skippedUnknown", kind="engine.kind.spell", name="Nonexistent Spell")


def test_by_name_resolution_for_tradition_lifestyle_contact() -> None:
    st, _ = chum5_to_state(SAMPLE)
    assert st.get("tradition_id")
    assert st["lifestyles"] and st["lifestyles"][0]["months"] == 2
    assert st["contacts"][0]["name"] == "Fixer Sam"


def test_names_chummer_has_since_corrected_still_resolve() -> None:
    """Older saves carry no sourceid on these, only the name the data dropped."""
    xml = b"""<character><metatype>Human</metatype><buildmethod>Priority</buildmethod>
      <qualities>
        <quality><name>Biocompatability (Cyberware)</name><qualitysource>Selected</qualitysource></quality>
        <quality><name>Dishevelled</name><qualitysource>Selected</qualitysource></quality>
      </qualities>
      <gears><gear><name>Rapelling Gloves</name><category>Climbing Gear</category><qty>1</qty></gear></gears>
    </character>"""
    st, warnings = chum5_to_state(xml)
    names = {row["id"]: row["name"] for row in catalog()["qualities"]}
    assert sorted(names[q] for q in st["quality_ids"]) == ["Biocompatibility (Cyberware)", "Disheveled"]
    assert not has(warnings, "engine.import.skippedUnknown", name="Rapelling Gloves")


def test_a_quality_resolves_by_the_id_chummer_saved_before_its_name() -> None:
    """Chummer writes the data id to `<id>` (`<guid>` is the instance). "College
    Education" is two qualities — SASS's changes a limit, Run Faster's halves
    Academic point costs — and matching by name took the SASS one, so every
    save with the Run Faster one lost the discount."""
    run_faster = "604aea10-3f13-4f28-a87b-25b8bf677276"
    xml = f"""<character><metatype>Human</metatype><buildmethod>Priority</buildmethod>
      <qualities><quality>
        <guid>6f8fdf12-a624-44a6-a1b1-f188cd287a96</guid><id>{run_faster}</id>
        <name>College Education</name><qualitysource>Selected</qualitysource>
      </quality></qualities>
    </character>""".encode()
    st, _ = chum5_to_state(xml)
    assert st["quality_ids"] == [run_faster]


def test_a_stream_saved_as_a_res_tradition_is_read_as_the_stream() -> None:
    """Current Chummer writes the stream as `<tradition>` of type RES; the
    `<stream>` element is its legacy form."""
    stream = next(s for s in catalog()["streams"] if s["name"] == "Default")
    xml = f"""<character><metatype>Human</metatype><buildmethod>Priority</buildmethod>
      <tradition><traditiontype>RES</traditiontype><id>{stream["id"]}</id><name>Default</name></tradition>
    </character>""".encode()
    st, warnings = chum5_to_state(xml)
    assert st["stream_id"] == stream["id"]
    assert "tradition_id" not in st
    assert not warnings


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
    with pytest.raises(NoticeError) as caught:
        decompress_chum5lz(b"\x00\x01\x02not-compressed-not-xml\xff\xfe")
    assert caught.value.notice["key"] == "api.chum5lzUndecompressible"


def test_decompress_rejects_bomb_over_the_size_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.chummer_import.container as ci

    monkeypatch.setattr(ci, "_MAX_DECOMPRESSED_BYTES", 64 * 1024)
    # ~4 MB of a repeating byte -> a tiny FORMAT_ALONE payload
    bomb = lzma.compress(b"<character>" + b" " * (4 * 1024 * 1024) + b"</character>", format=lzma.FORMAT_ALONE)
    assert len(bomb) < 64 * 1024
    with pytest.raises(NoticeError) as caught:
        ci.decompress_chum5lz(bomb)
    assert caught.value.notice["key"] == "api.chum5lzUndecompressible"


def test_non_character_xml_rejected() -> None:
    with pytest.raises(NoticeError) as caught:
        chum5_to_state(b"<notacharacter><foo/></notacharacter>")
    assert caught.value.notice["key"] == "api.notACharacterFile"


def test_xml_entity_expansion_is_blocked() -> None:
    # a "billion laughs" style payload — defusedxml must refuse it, not expand it
    evil = (
        b'<?xml version="1.0"?>'
        b'<!DOCTYPE lolz [<!ENTITY lol "lol">'
        b'<!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">'
        b'<!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">]>'
        b"<character>&lol3;</character>"
    )
    with pytest.raises(NoticeError) as caught:
        chum5_to_state(evil)
    assert caught.value.notice["key"] == "api.xmlUnparsable"


_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="


def _with_mugshot(mugshot: str) -> bytes:
    return SAMPLE.replace(b"</character>", f"<mugshot>{mugshot}</mugshot></character>".encode())


@pytest.mark.parametrize(
    ("mugshot", "expected"),
    [
        # Chummer's own form: bare base64, the type guessed from the header
        (_PNG_B64, f"data:image/png;base64,{_PNG_B64}"),
        # wrapped across lines by an editor — still the same picture
        (f"{_PNG_B64[:40]}\n  {_PNG_B64[40:]}", f"data:image/png;base64,{_PNG_B64}"),
        (f"data:image/png;base64,{_PNG_B64}", f"data:image/png;base64,{_PNG_B64}"),
        # anything that is not an inline raster image goes into <img src> nowhere
        ("data:image/svg+xml;base64,PHN2Zz48L3N2Zz4=", ""),
        ("data:text/html;base64,PGgxPmhpPC9oMT4=", ""),
        ("data:image/png,not-base64", ""),
    ],
)
def test_mugshot_is_kept_only_as_a_raster_data_uri(mugshot: str, expected: str) -> None:
    st, _ = chum5_to_state(_with_mugshot(mugshot))
    assert st.get("portrait", "") == expected


def test_priorities_in_chummers_own_form_are_read() -> None:
    """Chummer saves `<prioritymetatype>E,0</prioritymetatype>` straight under
    `<character>` — letter, then the sum-to-ten value. Only a bare letter used
    to be accepted, so every real save came in as C across the board."""
    legacy = b"""<priorities>
    <prioritymetatype>D</prioritymetatype><priorityattributes>B</priorityattributes>
    <priorityspecial>A</priorityspecial><priorityskills>C</priorityskills>
    <priorityresources>E</priorityresources><prioritytalent>Magician</prioritytalent>
  </priorities>"""
    chummer = (
        b"<prioritymetatype>E,0</prioritymetatype><priorityattributes>A,4</priorityattributes>"
        b"<priorityspecial>B,3</priorityspecial><priorityskills>C,2</priorityskills>"
        b"<priorityresources>D,1</priorityresources><prioritytalent>Adept</prioritytalent>"
    )
    assert legacy in SAMPLE
    st, _ = chum5_to_state(SAMPLE.replace(legacy, chummer))
    assert st["priorities"] == {"Heritage": "E", "Attributes": "A", "Talent": "B", "Skills": "C", "Resources": "D"}
    assert st["talent"] == "Adept"


_CHUMMER_ADDED = b"""
  <weapons><weapon><sourceid>63dcfdb6-bbd9-4a58-bbf4-cd35f7614fdc</sourceid><name>Unarmed Attack</name></weapon></weapons>
  <gears><gear><id>9f0d5d35-43f3-4877-b384-cf4188b5bca7</id><name>Lighter</name></gear></gears>
  <cyberwares><cyberware><sourceid>47c48542-48c3-417e-91f0-b5a456183f05</sourceid><name>Datajack</name>
    <gears><gear><name>Universal Connector Cord (Meter)</name></gear></gears></cyberware></cyberwares>
  <vehicles><vehicle><sourceid>c0d3e7fd-d5fd-48c4-b49d-0c7dea26895d</sourceid><name>Dodge Scoot (Scooter)</name>
    <gears><gear><id>2ca81a10-d0f7-4b39-ac93-a84f2f69f9d9</id><name>Sensor Array</name></gear></gears></vehicle></vehicles>
"""


def _import_keys(extra: bytes) -> list[str]:
    _, warnings = chum5_to_state(SAMPLE.replace(b"</character>", extra + b"</character>"))
    return [w["key"] for w in warnings]


def test_what_chummer_adds_itself_is_not_reported_as_lost() -> None:
    """`<hide />` entries (the Unarmed Attack, a Survival Kit's lighter) and the
    gear a ware or vehicle entry includes (a Datajack's cord, a vehicle's
    Sensor Array) are in every save though nobody picked them. Reporting each
    as "could not be imported" buried the entries that really were lost."""
    baseline = _import_keys(b"")
    assert _import_keys(_CHUMMER_ADDED) == baseline


def test_gear_nobody_included_is_still_reported() -> None:
    picked = (
        _CHUMMER_ADDED.replace(b"<name>Universal Connector Cord (Meter)</name>", b"<name>Sim Module, Hot</name>")
        .replace(b"<name>Lighter</name>", b"<name>Homebrew Gizmo</name>")
        .replace(b"<id>9f0d5d35-43f3-4877-b384-cf4188b5bca7</id>", b"")
    )
    keys = _import_keys(picked)
    assert keys.count("engine.import.skippedUnknown") == _import_keys(b"").count("engine.import.skippedUnknown") + 1
    assert "engine.import.nestedGearSkipped" in keys


_EAGLE_ADEPT = b"""
  <mentorspirits><mentorspirit><id>9e38a8c0-f11c-461d-a489-ba1432f4551f</id><name>Eagle</name></mentorspirit></mentorspirits>
  <powers><power><name>Combat Sense</name><rating>0</rating></power>
    <power><name>Critical Strike</name><rating>1</rating><extra>Unarmed Combat</extra></power></powers>
  <improvements>
    <improvement><improvedname>Perception</improvedname><improvementttype>Skill</improvementttype>
      <improvementsource>MentorSpirit</improvementsource></improvement>
    <improvement><improvedname>Combat Sense</improvedname><improvementttype>AdeptPowerFreeLevels</improvementttype>
      <improvementsource>MentorSpirit</improvementsource></improvement>
  </improvements>
"""


def test_a_mentor_choice_is_recovered_from_the_improvements_it_made() -> None:
    """Chummer saves without `<extrachoice1>` keep the pick only as what it
    did: Eagle's adept option is an `AdeptPowerFreeLevels` "Combat Sense"."""
    st, _ = chum5_to_state(SAMPLE.replace(b"</character>", _EAGLE_ADEPT + b"</character>"))
    assert st["mentor_choices"] == ["Adept: 1 free level of Combat Sense"]


def test_a_power_only_free_levels_hold_up_is_not_imported_as_bought() -> None:
    """Rating 0 is Chummer's row for a power the mentor's free level carries;
    as a paid level 1 it billed half a power point nobody spent."""
    st, _ = chum5_to_state(SAMPLE.replace(b"</character>", _EAGLE_ADEPT + b"</character>"))
    names = {p["name"]: p["id"] for p in catalog()["powers"]}
    assert [p["power_id"] for p in st["adept_powers"]] == [names["Critical Strike"]]


def test_an_explicit_mentor_choice_still_wins() -> None:
    explicit = _EAGLE_ADEPT.replace(
        b"<name>Eagle</name>",
        b"<name>Eagle</name><extrachoice1>Magician: +2 dice summoning spirits of air</extrachoice1>",
    )
    st, _ = chum5_to_state(SAMPLE.replace(b"</character>", explicit + b"</character>"))
    assert st["mentor_choices"] == ["Magician: +2 dice summoning spirits of air"]


def test_ware_nested_three_deep_keeps_each_parent() -> None:
    """A modular connector holds the arm, the arm holds its enhancements: the
    enhancements belong to the arm, not to the connector at the top."""
    xml = b"""<character><metatype>Human</metatype><buildmethod>Priority</buildmethod>
      <cyberwares><cyberware><name>Modular Connector, Shoulder</name><grade>Used</grade>
        <children><cyberware><name>Obvious Full Arm, Modular</name><grade>Used</grade>
          <children><cyberware><name>Customized Agility</name><rating>6</rating><grade>Used</grade></cyberware></children>
        </cyberware></children>
      </cyberware></cyberwares>
    </character>"""
    st, _ = chum5_to_state(xml)
    ware = {row["id"]: row for row in catalog()["cyberware"]["items"]}
    by_name = {ware[row["ware_id"]]["name"]: row for row in st["cyberware"]}
    connector = by_name["Modular Connector, Shoulder"]
    arm = by_name["Obvious Full Arm, Modular"]
    assert "parent_id" not in connector
    assert arm["parent_id"] == connector["id"]
    assert by_name["Customized Agility"]["parent_id"] == arm["id"]

    # the enhancement's `+` availability rolls into the arm, not the connector
    rows = {row["name"]: row for row in import_character(st).derived["cyberware"]}
    assert rows["Modular Connector, Shoulder"]["avail"] == "8"  # 12, Used -4


NEWSKILLS = b"""<character><metatype>Human</metatype><buildmethod>Priority</buildmethod>
  <newskills>
    <skills>
      <skill><suid>adf31a50-b228-4e09-a09c-46ab9f5e59a1</suid><isknowledge>False</isknowledge>
        <karma>1</karma><base>4</base>
        <specs><spec><name>Revolvers</name><free>False</free></spec></specs></skill>
      <skill><suid>9cff9aa7-d092-4f89-8b7b-3ab835818874</suid><karma>0</karma><base>0</base></skill>
      <skill><suid>a1366ec2-772d-4f08-8c65-5f79464d975b</suid><karma>0</karma><base>3</base>
        <specific>Horns</specific></skill>
      <skill><suid>00000000-1111-2222-3333-444444444444</suid><karma>0</karma><base>2</base></skill>
    </skills>
    <knoskills>
      <skill><suid>a72084f6-3a4c-4c23-82aa-4697e543ee0b</suid><isknowledge>True</isknowledge>
        <karma>0</karma><base>0</base><name>German</name><type>Language</type></skill>
      <skill><isknowledge>True</isknowledge><karma>0</karma><base>2</base>
        <name>Runner Hangouts</name><type>Street</type></skill>
    </knoskills>
    <groups><group><karma>0</karma><base>2</base><name>Stealth</name></group></groups>
  </newskills>
</character>"""


def test_skills_in_chummers_newskills_layout() -> None:
    """Chummer writes `<newskills>` and names an active skill only by its
    skills.xml id; this app's own export used `<skills>` with names."""
    st, warnings = chum5_to_state(NEWSKILLS)
    assert st["skills"] == {"Pistols": 5}  # base 4 + karma 1; Sneaking at 0 is no skill
    assert st["skill_specializations"] == {"Pistols": "Revolvers"}
    assert [(row["skill_name"], row["extra"], row["rating"]) for row in st["exotic_skills"]] == [
        ("Exotic Melee Weapon", "Horns", 3)
    ]
    assert st["skill_groups"] == {"Stealth": 2}
    assert st["knowledge_skills"] == {"Runner Hangouts": 2}
    assert st["knowledge_categories"] == {"Runner Hangouts": "Street"}
    # a pre-5.212.72 save has no <isnativelanguage>: a language with no points is the native one
    assert st["native_languages"] == ["German"]
    assert has(warnings, "engine.import.skippedUnknown", name="00000000-1111-2222-3333-444444444444")


def test_ware_a_player_put_in_is_bought_and_what_came_with_it_is_not() -> None:
    """Chummer's `<parentid>` is the parent's guid on what the parent's data
    added and empty on what was bought for it — which is paid for."""
    xml = b"""<character><metatype>Human</metatype><buildmethod>Priority</buildmethod>
      <cyberwares><cyberware><guid>11111111-0000-0000-0000-000000000000</guid>
        <name>Obvious Full Arm</name><grade>Standard</grade><parentid />
        <children>
          <cyberware><name>Customized Agility</name><rating>4</rating><grade>Standard</grade><parentid /></cyberware>
          <cyberware><name>Biomonitor</name><grade>Standard</grade>
            <parentid>11111111-0000-0000-0000-000000000000</parentid></cyberware>
        </children>
      </cyberware></cyberwares>
    </character>"""
    st, _ = chum5_to_state(xml)
    ware = {row["id"]: row["name"] for row in catalog()["cyberware"]["items"]}
    included = {ware[row["ware_id"]]: row.get("included") for row in st["cyberware"]}
    assert included == {"Obvious Full Arm": False, "Customized Agility": False, "Biomonitor": True}
    rows = {row["name"]: row for row in import_character(st).derived["cyberware"]}
    assert rows["Customized Agility"]["nuyen"] > 0  # bought, so it costs
    assert rows["Biomonitor"]["nuyen"] == 0


def test_bioware_chummer_keeps_among_the_cyberware_is_read_as_bioware() -> None:
    """Chummer writes bioware as `<cyberware>` rows in `<cyberwares>`, marked
    only by `<improvementsource>Bioware</improvementsource>`; filed with the
    cyberware they were priced nowhere and dropped."""
    xml = b"""<character><metatype>Human</metatype><buildmethod>Priority</buildmethod>
      <cyberwares>
        <cyberware><name>Datajack</name><grade>Standard</grade><improvementsource>Cyberware</improvementsource></cyberware>
        <cyberware><name>Muscle Toner</name><rating>2</rating><grade>Standard</grade>
          <improvementsource>Bioware</improvementsource></cyberware>
      </cyberwares>
    </character>"""
    st, _ = chum5_to_state(xml)
    derived = import_character(st).derived
    assert [row["name"] for row in derived["cyberware"]] == ["Datajack"]
    assert [(row["name"], row["rating"]) for row in derived["bioware"]] == [("Muscle Toner", 2)]
    assert derived["bioware"][0]["nuyen"] > 0


def test_lifestyle_qualities_come_in_but_not_the_built_in_ones() -> None:
    """A `Selected` quality is the player's pick; a `BuiltIn` one comes with
    the lifestyle and is derived again. Chummer's `<extra>` holding display
    text is kept only where the quality asks for a pick."""
    xml = b"""<character><metatype>Human</metatype><buildmethod>Priority</buildmethod>
      <lifestyles><lifestyle><baselifestyle>Low</baselifestyle><months>2</months>
        <lifestylequalities>
          <lifestylequality><id>ff0cb981-4459-46e7-ab75-d8c5bcb0c486</id><name>Cramped</name>
            <extra>Cramped [-10%]</extra><lifestylequalitysource>Selected</lifestylequalitysource></lifestylequality>
          <lifestylequality><id>adaf6b3d-874a-42e5-b08b-37adf1222f23</id><name>Grid Subscription</name>
            <extra>Public Grid</extra><lifestylequalitysource>BuiltIn</lifestylequalitysource></lifestylequality>
        </lifestylequalities>
      </lifestyle></lifestyles>
    </character>"""
    st, warnings = chum5_to_state(xml)
    (row,) = st["lifestyles"]
    assert row["months"] == 2
    assert row["quality_ids"] == ["ff0cb981-4459-46e7-ab75-d8c5bcb0c486"]
    assert row["quality_extras"] == {}
    assert warnings == []


def test_an_accessory_a_save_puts_on_no_mount_takes_no_slot() -> None:
    """Chummer's "None" mount takes no slot. A save from before Chummer
    tracked mounts has every accessory on it — two Stock accessories on one
    Savalette Guardian included — and Chummer does not re-check them."""
    xml = b"""<character><metatype>Human</metatype><buildmethod>Priority</buildmethod>
      <weapons><weapon><name>Savalette Guardian</name><accessories>
        <accessory><name>Folding Stock</name><mount>None</mount></accessory>
        <accessory><name>Gecko Grip</name><mount>None</mount></accessory>
        <accessory><name>Silencer</name><mount>None</mount></accessory>
      </accessories></weapon></weapons>
    </character>"""
    st, warnings = chum5_to_state(xml)
    assert warnings == []  # "Silencer" is the old name of Silencer/Suppressor
    derived = import_character(st).derived
    mounts = {acc["name"]: acc["mount"] for acc in derived["weapons"][0]["accessories"] if not acc["included"]}
    assert mounts == {"Folding Stock": "None", "Gecko Grip": "None", "Silencer/Suppressor": "None"}
    assert not has(derived["errors"], "engine.gear.noFreeMount")


def test_what_chummer_made_up_rather_than_took_from_data_is_not_reported() -> None:
    """A Shapeshifter's Bite is built from its critter powers and saved with
    an empty id; there is nothing to import and nobody to warn."""
    xml = b"""<character><metatype>Human</metatype><buildmethod>Priority</buildmethod>
      <weapons><weapon><sourceid>00000000-0000-0000-0000-000000000000</sourceid>
        <name>Bite (Vulpine Form)</name><category>Critter Powers</category></weapon></weapons>
    </character>"""
    st, warnings = chum5_to_state(xml)
    assert st["weapons"] == []
    assert warnings == []


def test_items_the_player_prices_keep_their_price_and_name() -> None:
    """`Variable(lo-hi)` in Chummer's data: the save's `<cost>` is the price
    picked, and a Custom Item's `<name>` is the player's (its `<id>` says
    which entry it is)."""
    xml = b"""<character><metatype>Human</metatype><buildmethod>Priority</buildmethod>
      <armors><armor><sourceid>31c68476-6328-476a-ae8a-94f65d505a04</sourceid><name>Clothing</name>
        <cost>1000</cost></armor></armors>
      <gears>
        <gear><id>0025f1c7-45a4-4ec5-a692-e18aab2f97a9</id><name>Golden Lotus Flower</name>
          <category>Custom</category><cost>100</cost><qty>1</qty></gear>
        <gear><name>Hermes Ikon</name><category>Commlinks</category><children>
          <gear><id>f1d72c1e-32f6-48d1-88c9-f916119cbaf8</id><name>Theme Music</name>
            <category>Commlink Apps</category><cost>40</cost></gear></children></gear>
      </gears>
    </character>"""
    st, warnings = chum5_to_state(xml)
    assert warnings == []
    derived = import_character(st).derived
    assert [(row["name"], row["nuyen"]) for row in derived["armor_items"]] == [("Clothing", 1000)]
    (lotus,) = derived["gear"]
    assert (lotus["label"], lotus["nuyen"]) == ("Golden Lotus Flower", 100)
    assert [(row["name"], row["nuyen"]) for row in derived["apps"]] == [("Theme Music", 40)]


def test_a_picked_price_is_held_to_its_range() -> None:
    from app.engine import compute
    from app.models import ArmorInstall, CharacterState, GearInstall, Priorities

    custom = "0025f1c7-45a4-4ec5-a692-e18aab2f97a9"
    clothing = "31c68476-6328-476a-ae8a-94f65d505a04"
    out = compute(
        CharacterState(
            id="p",
            name="p",
            priorities=Priorities(),
            metatype="Human",
            attributes={},
            armor=[ArmorInstall(armor_id=clothing, cost=5)],  # Clothing starts at 20
            gear=[GearInstall(gear_id=custom, cost=2500, name="Rosary")],
        )
    )
    assert out.armor[0].cost == 20
    assert out.derived["armor_items"][0]["nuyen"] == 20
    assert (out.derived["gear"][0]["label"], out.derived["gear"][0]["nuyen"]) == ("Rosary", 2500)


def test_gear_carried_in_armor_comes_in_on_the_armor_and_goes_back_out_there() -> None:
    """Chummer keeps a Holster or a Medkit in the armor's own `<gears>`; a
    Personal Drone Rack older saves list with the mods is gear too, and a
    helmet's sensor and vision enhancements sit there as well."""
    xml = b"""<character><metatype>Human</metatype><buildmethod>Priority</buildmethod>
      <armors><armor><name>Armor Jacket</name>
        <armormods><armormod><name>Personal Drone Rack</name></armormod></armormods>
        <gears>
          <gear><name>Holster</name><qty>1</qty></gear>
          <gear><name>Medkit</name><rating>3</rating><qty>1</qty></gear>
        </gears>
      </armor>
      <armor><name>Helmet</name>
        <gears>
          <gear><name>Single Sensor</name><qty>1</qty></gear>
          <gear><name>Vision Magnification</name><qty>1</qty></gear>
          <gear><name>Vision Enhancement</name><rating>2</rating><qty>1</qty></gear>
        </gears>
      </armor></armors>
    </character>"""
    st, warnings = chum5_to_state(xml)
    assert warnings == []
    jacket, helmet = st["armor"]
    assert st["armor_mods"] == []
    assert {g["parent_id"] for g in st["gear"]} == {jacket["id"]}
    assert len(st["gear"]) == 3
    # Vision Magnification is an optic here, not a sensor function
    assert {g["parent_id"] for g in st["optics"] + st["sensors"]} == {helmet["id"]}
    assert (len(st["optics"]), len(st["sensors"])) == (2, 1)
    derived = import_character(st).derived
    jacket_row, helmet_row = derived["armor_items"]
    assert jacket_row["capacity_used"] == 1 + 3 + 5
    assert helmet_row["capacity_used"] == 1 + 1 + 2
    assert {row["bucket"] for row in helmet_row["gear"]} == {"optics", "sensors"}
    assert not has(derived["warnings"], "engine.gear.doesNotFit")

    root = ET.fromstring(state_to_chum5(CharacterState.model_validate(st)))
    armors = root.findall("./armors/armor")
    assert sorted(_text(g.find("name")) for g in armors[0].findall("./gears/gear")) == [
        "Holster",
        "Medkit",
        "Personal Drone Rack",
    ]
    assert len(armors[1].findall("./gears/gear")) == 3
    assert root.findall("./gears/gear") == []


def test_a_stack_of_commlinks_keeps_its_count() -> None:
    """Chummer's `<qty>` on a commlink (two burner Meta Links) is paid for
    and written back, not read as one."""
    xml = b"""<character><metatype>Human</metatype><buildmethod>Priority</buildmethod>
      <gears><gear><name>Meta Link</name><qty>2</qty></gear></gears>
    </character>"""
    st, warnings = chum5_to_state(xml)
    assert warnings == []
    (link,) = st["commlinks"]
    assert link["qty"] == 2
    derived = import_character(st).derived
    assert derived["commlinks"][0]["nuyen"] == 200
    root = ET.fromstring(state_to_chum5(CharacterState.model_validate(st)))
    assert root.findtext("./gears/gear/qty") == "2"


def test_what_a_commlink_comes_with_is_not_bought_again() -> None:
    """A Nixdorf Sekretar's entry includes a rating-3 Agent. Older saves do
    not mark it, but it came with the commlink: free, and not an item over
    the Availability limit on its own."""
    xml = b"""<character><metatype>Human</metatype><buildmethod>Priority</buildmethod>
      <gears><gear><name>Nixdorf Sekretar w/ Liebesekretar</name><children>
        <gear><name>Agent</name><category>Software</category><rating>3</rating><cost>0</cost></gear>
      </children></gear></gears>
    </character>"""
    st, warnings = chum5_to_state(xml)
    assert warnings == []
    (agent,) = st["apps"]
    assert agent["included"] is True
    derived = import_character(st).derived
    assert derived["apps"][0]["nuyen"] == 0
    assert derived["nuyen_spent"] == 6000


def test_the_black_market_discount_is_kept_per_item() -> None:
    """Chummer marks the one item the buyer took the Black Market Pipeline's
    10% off with `<discountedcost>`, rather than discounting everything of
    that category."""
    xml = b"""<character><metatype>Human</metatype><buildmethod>Priority</buildmethod>
      <weapons>
        <weapon><name>Ares Predator V</name><discountedcost>True</discountedcost></weapon>
        <weapon><name>Ares Predator V</name><discountedcost>False</discountedcost></weapon>
      </weapons>
    </character>"""
    st, warnings = chum5_to_state(xml)
    assert warnings == []
    assert [row["discounted"] for row in st["weapons"]] == [True, False]
    root = ET.fromstring(state_to_chum5(CharacterState.model_validate(st)))
    assert [_text(w.find("discountedcost")) for w in root.findall("./weapons/weapon")] == ["True", "False"]


def test_what_is_stowed_in_a_vehicle_comes_in_on_it() -> None:
    """A vehicle carries gear in its own `<gears>`. Its Sensor Array is not
    one: Chummer builds that from the vehicle's sensor rating and saves it,
    while this app keeps the rating."""
    xml = b"""<character><metatype>Human</metatype><buildmethod>Priority</buildmethod>
      <vehicles><vehicle><name>Ford Americar (Sedan)</name><gears>
        <gear><name>Sensor Array</name><rating>2</rating><cost>0</cost></gear>
        <gear><name>Medkit</name><rating>3</rating><qty>1</qty></gear>
      </gears></vehicle></vehicles>
    </character>"""
    st, warnings = chum5_to_state(xml)
    assert warnings == []
    (vehicle,) = st["vehicles"]
    assert [(row["gear_id"], row["parent_id"]) for row in st["gear"]] == [
        (next(g["id"] for g in catalog()["gear"] if g["name"] == "Medkit"), vehicle["id"])
    ]
    derived = import_character(st).derived
    assert not has(derived["warnings"], "engine.gear.doesNotFit")
    assert [row["name"] for row in derived["vehicles"][0]["gear"]] == ["Medkit"]
    root = ET.fromstring(state_to_chum5(CharacterState.model_validate(st)))
    assert [_text(g.find("name")) for g in root.findall("./vehicles/vehicle/gears/gear")] == ["Medkit"]
    assert root.findall("./gears/gear") == []


def test_a_career_saves_spending_is_kept_as_history() -> None:
    """The expense log's negative rows say where the balance went. They are
    history only — what they bought is priced from the character itself — so
    they are shown and written back, never counted again."""
    xml = b"""<character><metatype>Human</metatype><buildmethod>Priority</buildmethod><created>True</created>
      <karma>5</karma><nuyen>1000</nuyen>
      <expenses>
        <expense><type>Karma</type><amount>10</amount><reason>Run payout</reason><refund>False</refund></expense>
        <expense><type>Karma</type><amount>-6</amount><reason>Gained Positive Quality Toughness</reason>
          <refund>False</refund></expense>
        <expense><type>Nuyen</type><amount>-240</amount><reason>Purchased Gear Ammo</reason><refund>False</refund></expense>
      </expenses>
    </character>"""
    st, warnings = chum5_to_state(xml)
    assert warnings == []
    assert [(row["label"], row["karma"], row["nuyen"]) for row in st["expense_log"]] == [
        ("Gained Positive Quality Toughness", -6, 0),
        ("Purchased Gear Ammo", 0, -240),
    ]
    assert [row["karma"] for row in st["reward_log"]] == [10]
    derived = import_character(st).derived
    assert derived["karma"]["remaining"] == 5  # the adjustment still meets the balance
    assert derived["karma_earned"] == 10  # spending is not earning
    root = ET.fromstring(state_to_chum5(CharacterState.model_validate(st)))
    amounts = sorted(int(e.findtext("amount") or 0) for e in root.findall("./expenses/expense"))
    assert amounts == [-240, -6, 10]


def test_an_electronic_modification_comes_in_with_the_deck_it_is_soldered_into() -> None:
    """DT p.66 modifications sit in a device's `<children>`. They used to be
    left out of the catalog entirely, so three of Chummer's own test saves
    imported with an unknown piece of gear."""
    xml = b"""<character><metatype>Human</metatype><buildmethod>Priority</buildmethod>
      <gears>
        <gear><name>Hermes Ikon</name><category>Commlinks</category><children>
          <gear><name>Increase Data Processing Modification</name>
            <category>Electronic Modification</category><qty>1</qty></gear></children></gear>
      </gears>
    </character>"""
    st, warnings = chum5_to_state(xml)
    assert warnings == []
    derived = import_character(st).derived
    (mod,) = derived["gear"]
    assert (mod["name"], mod["nuyen"]) == ("Increase Data Processing Modification", 0)
    assert mod["parent_id"] == derived["commlinks"][0]["id"]
    assert derived["commlinks"][0]["dataprocessing"] == 6  # a Hermes Ikon's 5, plus the point


def test_gear_dragged_where_it_cannot_go_is_carried_on_its_own() -> None:
    """Chummer lets a player drag ammo into a Spare Clip. Kept there, the
    engine drops the ammo — and anything inside it, which then went missing
    on the next export. Carried on its own, both stay, and the move is said."""
    from tests.chum5_fixtures import build_chum5

    xml = build_chum5(
        gear=[
            {
                "name": "Spare Clip",
                "children": [
                    {"name": "Ammo: Injection Darts", "qty": 10, "children": [{"name": "Narcoject"}]},
                ],
            }
        ],
    )
    state, warnings = chum5_to_state(xml)
    assert [w["params"]["name"] for w in warnings if w["key"] == "engine.import.gearMovedOut"] == [
        "Ammo: Injection Darts"
    ]
    names = {str(g["id"]): g["name"] for g in catalog()["gear"]}
    ch = import_character(state)
    by_id = {row.id: row for row in ch.gear}
    held = {names[row.gear_id]: names[by_id[row.parent_id].gear_id] if row.parent_id else None for row in ch.gear}
    assert held == {"Spare Clip": None, "Ammo: Injection Darts": None, "Narcoject": "Ammo: Injection Darts"}
    assert not has(ch.derived["warnings"], "engine.gear.doesNotFit")

    back = import_character(chum5_to_state(state_to_chum5(ch))[0])
    assert sorted(names[row.gear_id] for row in back.gear) == sorted(held)
