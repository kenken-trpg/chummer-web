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
from app.models import CharacterPatch, CharacterState, Priorities, SettingsState
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


def test_a_shipped_preset_is_named_by_the_key_chummer_looks_it_up_by() -> None:
    """`<settings>` is a key into Chummer's loaded settings, not the name on
    the pulldown: the `<id>` GUID for a shipped preset. Writing the display
    name missed every time, and Chummer answered "the settings file could not
    be loaded". The name goes in `<gameplayoption>`, which is where this app's
    own importer reads it from and where 5.202 kept it.

    The books ride along as `<sources>` so that a Chummer without this preset
    can still score which of its own settings to substitute; the import
    recovers them from the name, the way it always has."""
    state = apply_patch(
        new_character(None),
        CharacterPatch(settings={"name": "Sum-to-Ten", "books": ["SR5", "RF"]}),
    )
    root = _export(state)
    assert root.findtext("settings") == "3509a807-68ee-4c18-b7d5-b130313b4b77"
    assert root.findtext("gameplayoption") == "Sum-to-Ten"
    assert [el.text for el in root.findall("./sources/source")] == ["SR5", "RF"]

    back = chum5_to_state(state_to_chum5(state))[0]
    assert back["settings"] == {"name": "Sum-to-Ten", "books": ["SR5", "RF"]}


def test_a_players_own_settings_file_is_named_as_a_file() -> None:
    """A settings file of the player's own is keyed by its file name, which a
    `.chum5` never carried and this app therefore does not hold. The name it
    was saved under is the guess; the custom data directories are what let
    Chummer score its way to the right settings when the guess misses."""
    state = apply_patch(
        new_character(None),
        CharacterPatch(settings={"name": "コデックス", "books": ["SR5"], "customdata": ["Codex"]}),
    )
    root = _export(state)
    assert root.findtext("settings") == "コデックス.xml"
    assert [el.text for el in root.findall("./customdatadirectorynames/directoryname")] == ["Codex"]


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
    # `dronemods` is read (the Rigger 5.0 drone modification rules), so only
    # the armor degradation knob is reported
    assert parsed.unsupported == ["armordegredation"]


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


def _armor_from(source: str) -> dict:
    return next(a for a in catalog()["armor"] if a.get("source") == source)


def test_gear_outside_the_enabled_books_is_named_in_the_warnings() -> None:
    """The pick lists stop offering it, which on its own reads as "that item
    is gone". A character can arrive holding it — imported from Chummer, or
    built before the GM dropped the book — so the sheet says which pieces."""
    core, supplement = _armor_from("SR5"), _armor_from("RG")
    state = apply_patch(
        new_character(None),
        CharacterPatch(
            armor=[
                {"armor_id": core["id"], "rating": 1, "equipped": True},
                {"armor_id": supplement["id"], "rating": 1, "equipped": True},
            ],
            settings={"name": "SR5 only", "books": ["SR5"]},
        ),
    )
    assert has(
        state.derived["warnings"],
        "engine.settings.outOfBooks",
        names=[supplement["name"]],
        books="RG",
    )


def test_nothing_is_out_of_book_when_the_settings_name_no_books() -> None:
    """An empty book list means unrestricted, not "no books at all" — a
    character saved before the field existed must not light up in red."""
    state = apply_patch(
        new_character(None),
        CharacterPatch(
            armor=[{"armor_id": _armor_from("RG")["id"], "rating": 1, "equipped": True}],
            settings={"name": "unrestricted", "books": []},
        ),
    )
    assert not has(state.derived["warnings"], "engine.settings.outOfBooks")


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


def test_the_knowledge_points_expression_is_kept_when_it_is_arithmetic() -> None:
    standard = parse_settings_xml(_settings_xml(knowledgepointsexpression="({INTUnaug} + {LOGUnaug}) * 2"))
    assert standard.unsupported == []
    assert rules_for(standard) == DEFAULT_RULES
    house = parse_settings_xml(_settings_xml(knowledgepointsexpression="({INTUnaug} + {LOGUnaug}) * 3"))
    assert rules_for(house).knowledge_points_expression == "({INTUnaug} + {LOGUnaug}) * 3"


def test_a_knowledge_expression_this_app_cannot_evaluate_is_reported() -> None:
    parsed = parse_settings_xml(_settings_xml(knowledgepointsexpression="{Skill} * 2"))
    assert parsed.knowledge_points_expression is None
    assert "knowledgepointsexpression" in parsed.unsupported


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


def test_the_number_of_attributes_allowed_at_maximum_is_read() -> None:
    assert parse_settings_xml(_settings_xml(maxnumbermaxattributescreate=2)).chargen_attributes_at_max == 2


def test_the_career_knowledge_cap_is_not_read_as_the_group_cap() -> None:
    """`<maxknowledgeskillrating>` is the knowledge-skill cap after creation;
    it used to land on a skill-group cap Chummer does not have."""
    parsed = parse_settings_xml(_settings_xml(maxskillrating=13, maxknowledgeskillrating=9))
    assert (parsed.career_skill_max, parsed.career_knowledge_skill_max) == (13, 9)


def _save_with(max_avail: str) -> bytes:
    return (
        "<character><alias>Prime</alias><metatype>Human</metatype>"
        f"<settings>default.xml</settings><maxavail>{max_avail}</maxavail>"
        "</character>"
    ).encode()


def test_the_creation_availability_limit_comes_from_the_save() -> None:
    """`<maxavail>` is the one house rule a `.chum5` carries itself: the
    gameplay option sets it (Standard 12, Prime Runner 15) and a table can move
    it anywhere. It used to be ignored in favour of the preset's 12, which
    called seven pieces of equipment across four of Chummer's own test
    characters illegal when they were within the limit those characters were
    actually built to.
    """
    state, _ = chum5_to_state(_save_with("15"))
    assert state["settings"]["chargen_avail_max"] == 15


def test_a_save_with_no_availability_limit_leaves_it_unset() -> None:
    state, _ = chum5_to_state(_save_with(""))
    assert state["settings"].get("chargen_avail_max") is None
    state, _ = chum5_to_state(b"<character><metatype>Human</metatype></character>")
    assert state["settings"].get("chargen_avail_max") is None


def test_the_availability_limit_round_trips() -> None:
    state, _ = chum5_to_state(_save_with("20"))
    again, _ = chum5_to_state(state_to_chum5(CharacterState(**state)))
    assert again["settings"]["chargen_avail_max"] == 20


def test_a_raised_availability_limit_lets_the_equipment_through() -> None:
    """The limit is not just stored, it is the one the engine checks against.

    A Prime Runner is built to 15, so a piece of gear at 14 is theirs to buy;
    the same gear on a Standard character is not.
    """
    from app.engine import compute
    from app.models import GearInstall

    over = next(
        item
        for item in catalog()["gear"]
        if str(item.get("avail") or "").rstrip("RF").isdigit() and 12 < int(str(item["avail"]).rstrip("RF")) <= 15
    )
    state = CharacterState(
        id="prime",
        name="Prime",
        metatype="Human",
        attributes={"BOD": 3, "AGI": 3, "REA": 3, "STR": 3, "CHA": 3, "INT": 3, "LOG": 3, "WIL": 3, "EDG": 3},
        priorities=Priorities(),
        gear=[GearInstall(gear_id=over["id"])],
    )
    standard = compute(state.model_copy(deep=True))
    assert has(standard.derived["errors"], "engine.gear.availOver")

    state.settings = SettingsState(chargen_avail_max=15)
    prime = compute(state)
    assert not has(prime.derived["errors"], "engine.gear.availOver")


def test_a_prime_runner_is_judged_by_prime_runner_rules() -> None:
    """`<gameplayoption>` names the preset; `<settings>` names the *file*, which
    is `default.xml` even for a Prime Runner. Matching on the file found no
    preset, so two of Chummer's own saves were judged by Standard's 25-karma
    quality cap instead of Prime Runner's 35."""
    from app.data_loader import catalog

    presets = {row["name"]: row for row in catalog()["settings_presets"]}
    assert presets["Standard"]["quality_karma_limit"] == 25
    assert presets["Prime Runner"]["quality_karma_limit"] == 35

    raw = b"""<?xml version="1.0" encoding="utf-8"?><character>
      <settings>default.xml</settings>
      <gameplayoption>Prime Runner</gameplayoption>
      <metatype>Human</metatype>
    </character>"""
    settings = chum5_to_state(raw)[0]["settings"]
    assert settings["name"] == "Prime Runner"
    assert settings["quality_karma_limit"] == 35


def test_the_standard_preset_leaves_the_printed_cap_unset() -> None:
    """A settings state says what it changes. Standard does not move the cap,
    so it must not come back as "set to 25" — that is a different thing."""
    raw = b"""<?xml version="1.0" encoding="utf-8"?><character>
      <settings>default.xml</settings>
      <gameplayoption>Standard</gameplayoption>
      <metatype>Human</metatype>
    </character>"""
    assert "quality_karma_limit" not in chum5_to_state(raw)[0]["settings"]


def test_a_prime_runner_is_paid_from_the_prime_runner_resources_row() -> None:
    """Prime Runner builds from its own `<prioritytable>`: Resources E is
    100,000¥, not Standard's 6,000¥. Importing without the table left two of
    Chummer's own Prime Runner saves ~100,000¥ in debt."""
    from app.characters import import_character

    raw = b"""<?xml version="1.0" encoding="utf-8"?><character>
      <settings>default.xml</settings>
      <gameplayoption>Prime Runner</gameplayoption>
      <buildmethod>SumtoTen</buildmethod>
      <priorityresources>E,0</priorityresources>
      <metatype>Human</metatype>
    </character>"""
    state = chum5_to_state(raw)[0]
    assert state["settings"]["priority_table"] == "Prime Runner"
    assert import_character(state).derived["nuyen_pool"] == 100000

    standard = raw.replace(b"Prime Runner", b"Standard")
    assert "priority_table" not in chum5_to_state(standard)[0]["settings"]


def test_a_prime_runner_may_buy_25_points_of_nuyen_with_karma() -> None:
    """Prime Runner's `<nuyenmaxbp>` is 25, not Standard's 10. Import kept the
    cap at 10, so Chummer's own `prime` save lost 30,000¥ of the 50,000¥ its
    25 karma bought."""
    from app.characters import import_character

    raw = b"""<?xml version="1.0" encoding="utf-8"?><character>
      <settings>default.xml</settings>
      <gameplayoption>Prime Runner</gameplayoption>
      <buildmethod>SumtoTen</buildmethod>
      <nuyenbp>25</nuyenbp>
      <metatype>Human</metatype>
    </character>"""
    state = chum5_to_state(raw)[0]
    assert state["settings"]["priority_karma_nuyen_base"] == 25
    derived = import_character(state).derived
    assert derived["nuyen_karma_max"] == 25
    assert state["karma_nuyen"] == 25

    standard = raw.replace(b"Prime Runner", b"Standard")
    assert "priority_karma_nuyen_base" not in chum5_to_state(standard)[0]["settings"]


def test_the_focus_bonding_prices_are_read() -> None:
    """Chummer prices bonding a focus as Force x a multiplier for its kind
    (`Focus.BindingKarmaCost`), and every kind has its own settings tag."""
    xml = (
        "<settings><name>H</name><karmacost>"
        "<karmaweaponfocus>4</karmaweaponfocus><karmaqifocus>1</karmaqifocus>"
        "</karmacost></settings>"
    )
    parsed = parse_settings_xml(xml)
    assert (parsed.karma_weapon_focus, parsed.karma_qi_focus) == (4, 1)
    assert parsed.unsupported == []


def test_bonding_a_focus_costs_force_times_its_kinds_price() -> None:
    """The bug this fixes: bonding was charged at Force flat, a multiplier of
    1, which no kind of focus has. A Force 3 weapon focus is 9 karma."""
    from app.engine.magic import focus_bind_karma

    assert focus_bind_karma("Weapon Focus", 3, []) == 9
    # the kind is the name up to its first `(` or `,`, as Chummer cuts it
    assert focus_bind_karma("Weapon Focus (2050)", 3, []) == 9
    assert focus_bind_karma("Spellcasting Focus, Combat", 2, []) == 4
    # a name that is no kind Chummer prices binds at Force flat
    assert focus_bind_karma("Spell Lock, Combat (2050)", 3, []) == 3
    with using_rules(rules_for(SettingsState(karma_weapon_focus=1))):
        assert focus_bind_karma("Weapon Focus", 3, []) == 3


def test_the_first_level_of_a_skill_can_be_priced_apart() -> None:
    """`<karmanewactiveskill>` is what Chummer's `RangeCost` charges for the
    level bought from nothing. Standard sets it to one improve step, so it
    only shows under a house rule — here, 10 for the first level and the
    printed 2 a level above it."""
    from app.engine.karma import skill_karma_cost

    skills = {"skills": [{"name": "Pistols", "category": "Combat Active"}]}
    with using_rules(rules_for(SettingsState(karma_new_active_skill=10))):
        assert skill_karma_cost({}, {"Pistols": 1}, skills) == 10
        assert skill_karma_cost({}, {"Pistols": 3}, skills) == 10 + 4 + 6
    assert skill_karma_cost({}, {"Pistols": 3}, skills) == 2 + 4 + 6


def test_a_skill_group_pays_its_new_price_only_at_rating_one() -> None:
    """Chummer prices a group by the triangular number of levels and swaps
    the whole price for `<karmanewskillgroup>` only when that number is 1."""
    from app.engine.karma import skill_karma_cost

    skills = {"skills": []}
    with using_rules(rules_for(SettingsState(karma_new_skill_group=1))):
        assert skill_karma_cost({"Firearms": 1}, {}, skills) == 1
        # rating 2 is three levels' worth, so every level is the improve price
        assert skill_karma_cost({"Firearms": 2}, {}, skills) == 5 + 10


def _wired(rating: int, settings: SettingsState | None = None) -> CharacterState:
    from app.models import CyberwareInstall
    from tests.engine_support import _mundane

    wire = next(r["id"] for r in catalog()["cyberware"]["items"] if r["name"] == "Wired Reflexes")
    state = _mundane("init", cyberware=[CyberwareInstall(ware_id=wire, rating=rating)])
    if settings is not None:
        state.settings = settings
    return state


def test_initiative_dice_are_capped_at_the_settings_maximum() -> None:
    """Chummer's `InitiativeDice`: the minimum plus what augmentations add,
    never past `<maxinitiativedice>`. Nothing capped it here before."""
    from app.engine import compute

    assert compute(_wired(3)).derived["initiative"]["dice"] == 4
    capped = compute(_wired(3, SettingsState(max_initiative_dice=3)))
    assert capped.derived["initiative"]["dice"] == 3
    raised = compute(_wired(1, SettingsState(min_initiative_dice=2)))
    assert raised.derived["initiative"]["dice"] == 3


def test_vr_initiative_dice_come_from_the_settings() -> None:
    from app.engine.gear.matrix import matrix_initiative

    persona = [("commlink", {"dataprocessing": 3})]
    standard = matrix_initiative(persona, 4)
    assert standard is not None
    assert (standard["cold_dice"], standard["hot_dice"]) == (3, 4)
    with using_rules(rules_for(SettingsState(min_hotsim_initiative_dice=5, max_coldsim_initiative_dice=4))):
        house = matrix_initiative(persona, 4, extra_dice=2)
        assert house is not None
        assert (house["cold_dice"], house["hot_dice"]) == (4, 5)


def test_the_initiative_dice_settings_are_read() -> None:
    xml = _settings_xml(maxinitiativedice=4, minhotsiminitiativedice=5)
    parsed = parse_settings_xml(xml)
    assert (parsed.max_initiative_dice, parsed.min_hotsim_initiative_dice) == (4, 5)
    assert parsed.unsupported == []


def test_the_legacy_second_max_attribute_switch_allows_two() -> None:
    """`<allow2ndmaxattribute>` is read only when the file has no
    `<maxnumbermaxattributescreate>`, as Chummer's loader does."""
    assert parse_settings_xml(_settings_xml(allow2ndmaxattribute="True")).chargen_attributes_at_max == 2
    both = _settings_xml(allow2ndmaxattribute="True", maxnumbermaxattributescreate="1")
    assert parse_settings_xml(both).chargen_attributes_at_max == 1


def test_attribute_karma_switches_are_read_and_not_reported() -> None:
    parsed = parse_settings_xml(
        _settings_xml(
            alternatemetatypeattributekarma="True", unclampattributeminimum="True", allow2ndmaxattribute="True"
        )
    )
    assert parsed.alternate_metatype_attribute_karma is True


def test_doubling_the_excess_positive_qualities_is_not_reported() -> None:
    """Chummer doubles the excess only in the "X / 25" label; the karma spent
    and the over-limit error are the same either way."""
    parsed = parse_settings_xml(
        _settings_xml(exceedpositivequalities="True", exceedpositivequalitiescostdoubled="True")
    )
    assert parsed.unsupported == []


def test_the_redliner_exclusion_list_is_read() -> None:
    xml = "<settings><name>R</name><redlinerexclusion><limb>skull</limb></redlinerexclusion></settings>"
    parsed = parse_settings_xml(xml)
    assert parsed.redliner_exclusion == ["skull"]
    assert rules_for(parsed).redliner_excludes == ("skull",)
    assert parse_settings_xml("<settings><name>R</name></settings>").redliner_exclusion is None
    assert rules_for(SettingsState()).redliner_excludes == ("skull", "torso")


def test_technomancer_tags_are_read_or_known_dead() -> None:
    parsed = parse_settings_xml(
        _settings_xml(allowfreegrids="True", ignorecomplexformlimit="True", allowtechnomancerschooling="True")
    )
    assert parsed.allow_free_grids is True
    assert rules_for(parsed).allow_free_grids is True
    for tag in ("allowfreegrids", "ignorecomplexformlimit", "allowtechnomancerschooling"):
        assert tag not in parsed.unsupported
