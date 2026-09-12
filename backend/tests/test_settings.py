"""The settings file, as far as it is ported: the books/preset loaders, the
`SettingsState` container and its `.chum5` round-trip.

Chummer's `<settings>` holds ~150 house-rule knobs; what lands here is the
book list and the build method. See docs/plans/settings-plan.md.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from app.catalog_view.chargen import section as catalog_section
from app.characters import apply_patch, new_character
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.data_loader.loaders.books import load_books, load_settings_presets
from app.engine.priority import priority_value
from app.models import CharacterPatch, CharacterState, SettingsState
from app.rules import _DIRECT, DEFAULT_RULES, RULE_FIELDS, rules_for, using_rules
from app.settings_file import parse_settings_upload, parse_settings_xml
from tests.notice_asserts import has


def test_books_carry_every_code_the_catalog_cites() -> None:
    """A `<source>` the settings screen cannot list is a book the user can
    never enable — the item would be unbuyable under any preset."""
    codes = {b["code"] for b in load_books()}
    assert {"SR5", "RG"} <= codes
    cited = {
        str(row.get("source"))
        for bucket in ("qualities", "spells", "weapons", "armor", "gear")
        for row in catalog()[bucket]  # type: ignore[literal-required]
        if row.get("source")
    }
    assert cited <= codes, f"cited but not in books.xml: {sorted(cited - codes)}"


def test_presets_only_offer_build_methods_the_engine_has() -> None:
    presets = load_settings_presets()
    assert presets, "settings.xml should ship presets"
    assert {p["build_method"] for p in presets} <= {"Priority", "SumToTen", "Karma"}
    standard = next(p for p in presets if p["name"] == "Standard")
    assert standard["books"] == ["SR5"]


def test_a_new_character_is_unrestricted() -> None:
    """Empty books means the whole catalog, not an empty one — a character
    built before settings existed must not lose its gear."""
    state = new_character(None)
    assert state.settings.name == ""
    assert state.settings.books == []


def test_patching_settings_merges_rather_than_replaces() -> None:
    """The name and the book list are edited from two different controls."""
    state = new_character(None)
    state = apply_patch(state, CharacterPatch(settings={"name": "Standard", "books": ["SR5"]}))
    assert state.settings.name == "Standard"

    state = apply_patch(state, CharacterPatch(settings={"books": ["SR5", "RG"]}))
    assert state.settings.books == ["SR5", "RG"]
    assert state.settings.name == "Standard"


def _export(state: CharacterState) -> ET.Element:
    return ET.fromstring(state_to_chum5(state))


def test_an_untouched_character_writes_no_settings_tag() -> None:
    assert _export(new_character(None)).find("settings") is None


def test_a_shipped_preset_round_trips_its_books() -> None:
    """Only the name survives a `.chum5` — Chummer keeps the books in the
    settings file, not in the character — so import recovers them by name."""
    state = apply_patch(
        new_character(None),
        CharacterPatch(settings={"name": "Sum-to-Ten", "books": ["SR5", "RF"]}),
    )
    assert _export(state).findtext("settings") == "Sum-to-Ten"

    back = chum5_to_state(state_to_chum5(state))[0]
    assert back["settings"] == {"name": "Sum-to-Ten", "books": ["SR5", "RF"]}


def test_an_unknown_settings_file_comes_back_unrestricted() -> None:
    """A GM's own settings file names books this app has never seen; guessing
    a restriction would hide gear the character legitimately owns."""
    xml = "<character><alias>X</alias><settings>日本_2021_SumTo10.xml</settings></character>"
    state = chum5_to_state(xml)[0]
    assert state["settings"] == {"name": "日本_2021_SumTo10", "books": []}


def test_a_settings_element_holding_house_rules_is_not_read_as_a_name() -> None:
    """Some builds write `<settings>` as a container, not a file name."""
    xml = "<character><alias>X</alias><settings><karmaattribute>5</karmaattribute></settings></character>"
    assert chum5_to_state(xml)[0]["settings"] == {}


# --- the settings file itself ------------------------------------------- #


def _settings_xml(**tags: object) -> str:
    body = "".join(f"<{k}>{v}</{k}>" for k, v in tags.items())
    return f"<settings><name>House</name>{body}</settings>"


def test_a_file_that_changes_nothing_reports_nothing_unsupported() -> None:
    """The ignored-knob list is measured against Chummer's Standard preset, so
    a default-valued knob is not "a house rule we dropped"."""
    parsed = parse_settings_xml(_settings_xml(armordegredation="False"))
    assert parsed.unsupported == []


def test_a_knob_this_app_has_no_implementation_for_is_named() -> None:
    parsed = parse_settings_xml(_settings_xml(armordegredation="True", dronemods="True"))
    assert parsed.unsupported == ["armordegredation", "dronemods"]


def test_the_karma_price_list_is_read() -> None:
    xml = "<settings><name>H</name><karmacost><karmaattribute>7</karmaattribute></karmacost></settings>"
    parsed = parse_settings_xml(xml)
    assert parsed.karma_attribute == 7
    assert parsed.karma_spell is None, "a knob the file left alone stays unset, not zeroed"
    assert "karmaattribute" not in parsed.unsupported


def test_the_karma_to_nuyen_expression_wins_over_the_plain_rate() -> None:
    """Chummer evaluates the expression, so a file that disagrees with itself
    is honoured the way Chummer honours it."""
    parsed = parse_settings_xml(
        _settings_xml(
            nuyenperbpwftm="2000",
            chargenkarmatonuyenexpression="{Karma} * 3000 + {PriorityNuyen}",
        )
    )
    assert parsed.karma_to_nuyen == 3000
    assert parsed.unsupported == []


def test_an_expression_this_app_cannot_evaluate_is_reported_not_guessed() -> None:
    parsed = parse_settings_xml(
        _settings_xml(nuyenperbpwftm="2000", chargenkarmatonuyenexpression="{Karma} * {BOD} * 500")
    )
    assert parsed.karma_to_nuyen == 2000
    assert "chargenkarmatonuyenexpression" in parsed.unsupported


def test_a_preset_library_file_is_accepted_as_well_as_a_single_setting() -> None:
    """Chummer's own `settings.xml` nests many; a saved one is a bare tag."""
    library = "<chummer><settings><setting><name>Lib</name><sumtoten>13</sumtoten></setting></settings></chummer>"
    assert parse_settings_xml(library).sum_to_ten == 13


def test_a_non_settings_document_is_rejected() -> None:
    """So the endpoint can answer 400 rather than an all-defaults object that
    looks like a successful import."""
    with pytest.raises(ValueError):
        parse_settings_xml("<character><alias>X</alias></character>")
    with pytest.raises(ValueError):
        parse_settings_xml("not xml at all")


# --- what the numbers do once they are in ------------------------------- #


def test_rules_default_to_the_printed_sr5_values() -> None:
    assert rules_for(None) is DEFAULT_RULES
    assert rules_for(SettingsState()) == DEFAULT_RULES


def test_every_direct_override_names_a_real_rules_field() -> None:
    """Guards the two hand-written tables against a rename on either side."""
    assert set(_DIRECT.values()) <= RULE_FIELDS


def test_one_quality_limit_caps_both_directions() -> None:
    rules = rules_for(SettingsState(quality_karma_limit=30))
    assert (rules.quality_karma_cap_positive, rules.quality_karma_cap_negative) == (30, 30)


def test_the_karma_to_nuyen_rate_reaches_the_sheet() -> None:
    state = apply_patch(new_character(None), CharacterPatch(settings={"karma_to_nuyen": 3000}))
    assert state.derived["karma_chargen"]["nuyen_per_karma"] == 3000


def test_a_banned_ware_grade_is_pushed_back_to_an_allowed_one() -> None:
    """`<bannedwaregrades>` stacks with the grades a quality disables."""
    cat = catalog()
    ware = next(w for w in cat["cyberware"]["items"] if w.get("name") == "Wired Reflexes")
    state = apply_patch(
        new_character(None),
        CharacterPatch(
            cyberware=[{"ware_id": ware["id"], "rating": 1, "grade": "Deltaware"}],
            settings={"banned_ware_grades": ["Deltaware"]},
        ),
    )
    assert state.cyberware[0].grade != "Deltaware"
    assert has(state.derived["warnings"], "engine.ware.gradeBanned")


def test_unsupported_knobs_are_surfaced_as_a_warning() -> None:
    """A house rule silently dropped is worse than one the sheet says it
    ignored — the GM can then decide what to do about it."""
    state = apply_patch(
        new_character(None),
        CharacterPatch(settings={"name": "House", "unsupported": ["ignoreart"]}),
    )
    assert has(state.derived["warnings"], "engine.settings.unsupported", tags="ignoreart")


def test_the_priority_table_a_settings_file_names_is_the_one_used() -> None:
    """`priorities.xml` carries three tables and this app used to hard-code
    Standard, so a Prime Runner table silently paid Standard nuyen."""
    xml = "<settings><name>PR</name><prioritytable>Prime Runner</prioritytable></settings>"
    settings = parse_settings_xml(xml)
    assert settings.priority_table == "Prime Runner"
    with using_rules(rules_for(settings)):
        prime = priority_value("Resources", "A")["nuyen"]
    with using_rules(DEFAULT_RULES):
        standard = priority_value("Resources", "A")["nuyen"]
    assert prime != standard
    assert prime == 500000


def test_a_table_the_data_does_not_have_falls_back_rather_than_emptying() -> None:
    """A settings file may name a table that lives in custom data the user did
    not load. Building against Standard beats offering no options at all."""
    with using_rules(rules_for(SettingsState(priority_table="Nonexistent"))):
        assert priority_value("Resources", "A")["nuyen"] == 450000


def test_the_catalog_carries_only_what_another_table_replaces() -> None:
    """The catalog is shared by every character, so it ships the Standard
    table plus the differences — not three copies of the metatype lists."""
    overrides = catalog_section(catalog())["priority_table_overrides"]
    assert set(overrides) == {"Prime Runner", "Street Level"}
    assert set(overrides["Prime Runner"]) == {"Resources"}, "only Resources differs in SR5"
    assert overrides["Prime Runner"]["Resources"]["A"]["nuyen"] == 500000


def test_the_contact_points_expression_sets_the_free_multiplier() -> None:
    """Prime Runner writes `{CHAUnaug} * 6`; Standard's `* 3` changes nothing."""
    assert parse_settings_xml(_settings_xml(contactpointsexpression="{CHAUnaug} * 6")).contact_free_mult == 6
    standard = parse_settings_xml(_settings_xml(contactpointsexpression="{CHAUnaug} * 3"))
    assert standard.contact_free_mult == 3
    assert standard.unsupported == []
    assert rules_for(standard) == DEFAULT_RULES


def test_a_contact_expression_this_app_cannot_evaluate_is_reported() -> None:
    parsed = parse_settings_xml(_settings_xml(contactpointsexpression="({CHAUnaug} + {INTUnaug}) * 2"))
    assert parsed.contact_free_mult is None
    assert "contactpointsexpression" in parsed.unsupported


def test_the_spirit_and_sprite_limits_read_a_single_attribute() -> None:
    """Standard writes `{CHA}` for both; the German presets `{LOG}` for sprites."""
    parsed = parse_settings_xml(_settings_xml(boundspiritexpression="{CHA}", registeredspriteexpression="{LOG}"))
    assert parsed.bound_spirit_attr == "CHA"
    assert parsed.registered_sprite_attr == "LOG"
    assert parsed.unsupported == []
    rules = rules_for(parsed)
    assert (rules.bound_spirit_attr, rules.registered_sprite_attr) == ("CHA", "LOG")


def test_a_limit_expression_this_app_cannot_evaluate_is_reported() -> None:
    parsed = parse_settings_xml(_settings_xml(boundspiritexpression="{CHA} + 1"))
    assert parsed.bound_spirit_attr is None
    assert "boundspiritexpression" in parsed.unsupported


def test_the_negative_quality_house_rules_are_read() -> None:
    parsed = parse_settings_xml(_settings_xml(exceednegativequalities="True", exceednegativequalitiesnobonus="True"))
    assert parsed.exceed_negative_qualities is True
    assert parsed.exceed_negative_qualities_no_bonus is True
    assert parsed.unsupported == []
    rules = rules_for(parsed)
    assert rules.quality_exceed_negative and rules.quality_exceed_negative_no_bonus
    standard = parse_settings_xml(_settings_xml(exceednegativequalities="False"))
    assert rules_for(standard) == DEFAULT_RULES


def test_the_astral_initiative_dice_are_read() -> None:
    """The German presets roll 2D6 astral initiative instead of 3."""
    parsed = parse_settings_xml(_settings_xml(minastralinitiativedice="2", maxastralinitiativedice="5"))
    assert parsed.min_astral_initiative_dice == 2
    assert "minastralinitiativedice" not in parsed.unsupported
    assert rules_for(parsed).min_astral_initiative_dice == 2


def test_the_cyberleg_movement_rule_is_read() -> None:
    parsed = parse_settings_xml(_settings_xml(cyberlegmovement="True"))
    assert parsed.cyberleg_movement is True
    assert "cyberlegmovement" not in parsed.unsupported
    assert rules_for(parsed).cyberleg_movement is True


def test_the_limb_count_and_excluded_slot_are_read() -> None:
    """Neon Anarchy: five limbs, the skull left out of the average."""
    parsed = parse_settings_xml(_settings_xml(limbcount="5", excludelimbslot="skull"))
    assert (parsed.limb_count, parsed.exclude_limb_slot) == (5, "skull")
    assert not {"limbcount", "excludelimbslot"} & set(parsed.unsupported)
    rules = rules_for(parsed)
    assert (rules.limb_count, rules.exclude_limb_slot) == (5, "skull")


def test_the_knowledge_specialization_price_is_read() -> None:
    xml = (
        "<settings><name>NA</name><karmacost><karmaknospecialization>3</karmaknospecialization></karmacost></settings>"
    )
    parsed = parse_settings_xml(xml)
    assert parsed.karma_knowledge_specialization == 3
    assert "karmaknospecialization" not in parsed.unsupported
    assert rules_for(parsed).karma_knowledge_specialization == 3


def test_a_settings_file_with_entities_is_refused() -> None:
    """Parsed with defusedxml, like every other uploaded XML: no DTD entity is
    expanded, however small."""
    with pytest.raises(ValueError, match="not valid XML"):
        parse_settings_xml('<!DOCTYPE s [<!ENTITY n "House">]><settings><name>&n;</name></settings>')


def test_the_upload_reads_the_settings_and_build_method_from_one_parse() -> None:
    settings, build_method = parse_settings_upload(_settings_xml(buildmethod="SumtoTen", sumtoten=13).encode())
    assert settings.sum_to_ten == 13
    assert build_method == "SumToTen"
    _, none = parse_settings_upload(_settings_xml(sumtoten=13))
    assert none is None
