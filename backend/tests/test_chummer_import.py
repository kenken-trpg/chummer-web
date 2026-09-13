"""Chummer5a .chum5 / .chum5lz import (see backend/app/chummer_import/)."""

from __future__ import annotations

import lzma

import pytest

from app.characters import import_character
from app.chummer_import import chum5_to_state, decompress_chum5lz
from app.data_loader import catalog
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
