"""Chummer .chum5 export + round-trip (backend/app/chummer_export.py)."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from app.characters import import_character
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.models import (
    ArmorInstall,
    ArmorModInstall,
    CharacterState,
    CommlinkInstall,
    ContactInstall,
    CyberwareInstall,
    GearInstall,
    Priorities,
    SpellInstall,
    WeaponAccessoryInstall,
    WeaponInstall,
)


def _rich_state() -> CharacterState:
    c = catalog()

    def gid(bucket: str, name: str) -> str:
        return next(r["id"] for r in c[bucket] if r.get("name") == name)

    wire = next(r["id"] for r in c["cyberware"]["items"] if r["name"] == "Wired Reflexes")
    return CharacterState(
        id="rt",
        name="RoundTrip",
        notes="街の顔役に借り 2 件。義体は次のランで更新予定。",
        age="27",
        sex="女",
        eyes="サイバー（銀）",
        concept="元企業ウェットワーク",
        background="かつてはアレス社の内勤。今はフリー。",
        portrait=(
            "data:image/png;base64,"
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        ),
        priorities=Priorities(Heritage="C", Attributes="B", Talent="A", Skills="D", Resources="E"),
        metatype="Elf",
        talent="Magician",
        attributes={"BOD": 3, "AGI": 4, "REA": 3, "STR": 2, "CHA": 5, "INT": 4, "LOG": 4, "WIL": 4, "MAG": 5},
        skills={"Spellcasting": 5, "Pistols": 3},
        skill_specializations={"Spellcasting": "Combat"},
        knowledge_skills={"Magical Theory": 3},
        knowledge_categories={"Magical Theory": "Academic"},
        native_languages=["Sperethiel"],
        cyberware=[CyberwareInstall(ware_id=wire, rating=2, grade="Alpha")],
        spells=[SpellInstall(spell_id=gid("spells", "Acid Stream"))],
        weapons=[WeaponInstall(id="w1", weapon_id=gid("weapons", "Ares Predator V"))],
        weapon_accessories=[
            WeaponAccessoryInstall(
                accessory_id=gid("weapon_accessories", "Silencer/Suppressor"), parent_id="w1", mount="Barrel"
            )
        ],
        armor=[ArmorInstall(id="a1", armor_id=gid("armor", "Armor Jacket"))],
        armor_mods=[ArmorModInstall(mod_id=gid("armor_mods", "Fire Resistance"), parent_id="a1", rating=3)],
        gear=[GearInstall(gear_id=gid("gear", "Medkit"), rating=6)],
        commlinks=[CommlinkInstall(gear_id=c["commlinks"][0]["id"])],
        contacts=[ContactInstall(name="Sam", role="Fixer", connection=3, loyalty=2)],
    )


def test_export_is_wellformed_chummer_xml() -> None:
    xml = state_to_chum5(_rich_state())
    assert xml.lstrip().startswith(b"<?xml")
    text = xml.decode("utf-8")
    assert "<character>" in text and "<metatype>Elf</metatype>" in text
    assert "<prioritytalent>Magician</prioritytalent>" in text


def test_round_trip_preserves_the_core() -> None:
    src = _rich_state()
    st, warnings = chum5_to_state(state_to_chum5(src))

    assert warnings == []
    assert st["name"] == "RoundTrip"
    assert st["metatype"] == "Elf"
    assert st["talent"] == "Magician"
    assert st["priorities"] == {
        "Heritage": "C",
        "Attributes": "B",
        "Talent": "A",
        "Skills": "D",
        "Resources": "E",
    }
    assert st["attributes"]["AGI"] == 4  # survives min/base encoding
    assert st["attributes"]["MAG"] == 5
    assert st["skills"] == {"Spellcasting": 5, "Pistols": 3}
    assert st["skill_specializations"]["Spellcasting"] == "Combat"
    assert st["knowledge_skills"] == {"Magical Theory": 3}
    assert st["native_languages"] == ["Sperethiel"]

    assert [w["ware_id"] for w in st["cyberware"]] == [src.cyberware[0].ware_id]
    assert st["cyberware"][0]["grade"] == "Alpha" and st["cyberware"][0]["rating"] == 2
    assert [s["spell_id"] for s in st["spells"]] == [src.spells[0].spell_id]
    assert [w["weapon_id"] for w in st["weapons"]] == [src.weapons[0].weapon_id]
    assert st["weapon_accessories"][0]["mount"] == "Barrel"
    assert [a["armor_id"] for a in st["armor"]] == [src.armor[0].armor_id]
    assert st["armor_mods"][0]["rating"] == 3
    assert [g["gear_id"] for g in st["gear"]] == [src.gear[0].gear_id]
    assert st["commlinks"] and st["commlinks"][0]["gear_id"] == src.commlinks[0].gear_id
    assert st["contacts"][0]["name"] == "Sam"
    assert st["notes"] == src.notes
    assert st["age"] == "27" and st["sex"] == "女" and st["concept"] == "元企業ウェットワーク"
    assert st["background"] == src.background
    assert st["portrait"] == src.portrait


def test_priorities_are_written_where_and_how_chummer_reads_them() -> None:
    """`Character.Load` reads the priorities straight off `<character>`; a
    `<priorities>` wrapper was invisible to it and the file opened on defaults."""
    root = ET.fromstring(state_to_chum5(_rich_state()))
    assert root.find("priorities") is None
    assert [root.findtext(t) for t in ("prioritymetatype", "priorityattributes", "priorityspecial")] == [
        "C,2",
        "B,3",
        "A,4",
    ]
    assert (root.findtext("priorityskills"), root.findtext("priorityresources")) == ("D,1", "E,0")
    assert root.findtext("prioritytalent") == "Magician"


def test_round_tripped_state_still_validates() -> None:
    st, _ = chum5_to_state(state_to_chum5(_rich_state()))
    ch = import_character({k: v for k, v in st.items() if k != "_warnings"})
    assert ch.id and isinstance(ch.derived, dict)


def test_custom_fit_stack_target_survives_export() -> None:
    """Chummer keeps the armor a Custom Fit (Stack) was tailored to in the
    mod's `<extra>`; so do we."""
    c = catalog()
    coat = next(r["id"] for r in c["armor"] if r["name"] == "Mortimer of London: Greatcoat Coat")
    fit = next(r["id"] for r in c["armor_mods"] if r["name"] == "Custom Fit (Stack)")
    src = CharacterState(
        id="cf",
        name="cf",
        metatype="Human",
        attributes={},
        priorities=Priorities(),
        armor=[ArmorInstall(id="a1", armor_id=coat)],
        armor_mods=[ArmorModInstall(mod_id=fit, parent_id="a1", included=True, stack_with="Armor Jacket")],
    )
    st, _ = chum5_to_state(state_to_chum5(src))
    assert [m["stack_with"] for m in st["armor_mods"] if m["mod_id"] == fit] == ["Armor Jacket"]


def _infected(name: str, picked: str) -> tuple[CharacterState, str]:
    qid = next(q["id"] for q in catalog()["qualities"] if q["name"] == name)
    state = CharacterState(
        id="inf",
        name="Infected",
        priorities=Priorities(),
        metatype="Elf",
        attributes={},
        quality_ids=[qid],
        quality_extras={f"{qid}:optionalpower": picked} if picked else {},
    )
    return state, qid


def _with_quality(name: str, extras: dict[str, str]) -> tuple[CharacterState, str]:
    qid = next(q["id"] for q in catalog()["qualities"] if q["name"] == name)
    state = CharacterState(
        id="q",
        name="Quality",
        priorities=Priorities(),
        metatype="Human",
        attributes={},
        quality_ids=[qid],
        quality_extras={key.replace("{id}", qid): value for key, value in extras.items()},
    )
    return state, qid


def _powers(xml: bytes) -> list[tuple[str, str]]:
    root = ET.fromstring(xml)
    return [(p.findtext("name") or "", p.findtext("extra") or "") for p in root.findall("./critterpowers/critterpower")]


def test_an_infected_optional_power_survives_the_round_trip() -> None:
    """Chummer's `optionalpowers` improvement adds the pick to
    `<critterpowers>` next to the fixed ones; that is the only place a
    `.chum5` has for it, so export writes it there and import reads it back."""
    state, qid = _infected("Infected: Banshee", "Immunity (Toxins)")
    xml = state_to_chum5(state)
    powers = _powers(xml)
    assert ("Immunity", "Toxins") in powers
    assert ("Dual Natured", "") in powers
    assert all(p.findtext("grade") == "-1" for p in ET.fromstring(xml).findall("./critterpowers/critterpower"))

    back, _ = chum5_to_state(xml)
    assert back["quality_extras"][f"{qid}:optionalpower"] == "Immunity (Toxins)"


def test_a_pick_that_repeats_a_granted_power_is_told_apart_by_count() -> None:
    """Grendel is granted Immunity (Toxins) and may pick it again: the file
    then lists it twice, and only the second copy is the pick."""
    state, qid = _infected("Infected: Grendel", "Immunity (Toxins)")
    xml = state_to_chum5(state)
    assert _powers(xml).count(("Immunity", "Toxins")) == 2
    assert chum5_to_state(xml)[0]["quality_extras"][f"{qid}:optionalpower"] == "Immunity (Toxins)"

    unpicked, _ = _infected("Infected: Grendel", "")
    back = chum5_to_state(state_to_chum5(unpicked))[0]
    assert f"{qid}:optionalpower" not in back["quality_extras"]


def test_no_critter_powers_are_written_for_a_character_without_them() -> None:
    assert (
        ET.fromstring(
            state_to_chum5(_infected("Infected: Banshee", "")[0].model_copy(update={"quality_ids": []}))
        ).find("critterpowers")
        is None
    )


def _quality_el(xml: bytes) -> ET.Element:
    el = ET.fromstring(xml).find("./qualities/quality")
    assert el is not None
    return el


def test_chain_breakers_spirits_ride_the_quality_extra() -> None:
    """Chummer's `AddSpiritOrSprite` appends each `<addspirit>` pick to the
    quality's selected value, `, `-joined — that is Chain Breaker's `<extra>`."""
    state, qid = _with_quality(
        "Chain Breaker", {"{id}:addspirit:0": "Guardian Spirit", "{id}:addspirit:1": "Plant Spirit"}
    )
    xml = state_to_chum5(state)
    assert _quality_el(xml).findtext("extra") == "Guardian Spirit, Plant Spirit"

    back = chum5_to_state(xml)[0]["quality_extras"]
    assert back == {f"{qid}:addspirit:0": "Guardian Spirit", f"{qid}:addspirit:1": "Plant Spirit"}


def test_apprentices_spirit_is_the_extra_and_its_spell_category_an_improvement() -> None:
    """Apprentice: `<limitspiritcategory />` adds the spirit to the selected
    value, `<limitspellcategory />` does not — Chummer keeps that pick on the
    improvement, tied to the quality's guid."""
    state, qid = _with_quality("Apprentice", {"{id}": "Combat", "{id}:spiritcategory": "Spirit of Fire"})
    xml = state_to_chum5(state)
    quality = _quality_el(xml)
    assert quality.findtext("extra") == "Spirit of Fire"
    imp = ET.fromstring(xml).find("./improvements/improvement")
    assert imp is not None
    assert imp.findtext("improvementttype") == "LimitSpellCategory"
    assert imp.findtext("improvedname") == "Combat"
    assert imp.findtext("sourcename") == quality.findtext("guid")

    back = chum5_to_state(xml)[0]["quality_extras"]
    assert back == {qid: "Combat", f"{qid}:spiritcategory": "Spirit of Fire"}


def test_an_apprentice_file_from_before_keeps_its_spell_category() -> None:
    """This app used to write the spell category into `<extra>` with no
    improvement; a spell category is not a spirit, so it goes back where it was."""
    state, qid = _with_quality("Apprentice", {})
    root = ET.fromstring(state_to_chum5(state))
    quality = root.find("./qualities/quality")
    assert quality is not None
    quality.find("extra").text = "Health"  # type: ignore[union-attr]
    back = chum5_to_state(ET.tostring(root))[0]["quality_extras"]
    assert back == {qid: "Health"}


def test_black_market_pipelines_contact_survives_the_round_trip() -> None:
    """`<blackmarketdiscount />` then `<selectcontact />`: Chummer's `<extra>`
    is the category and the contact's name, `, `-joined. Import points the
    name back at the contact, which keeps its `<guid>`."""
    state, qid = _with_quality("Black Market Pipeline", {"{id}": "Weapons"})
    fixer = ContactInstall(name="Mr. Johnson", role="Fixer", connection=3, loyalty=2)
    state = state.model_copy(
        update={"contacts": [fixer], "quality_extras": {qid: "Weapons", f"{qid}:contact": fixer.id}}
    )
    xml = state_to_chum5(state)
    assert _quality_el(xml).findtext("extra") == "Weapons, Mr. Johnson"

    back = chum5_to_state(xml)[0]
    assert back["contacts"][0]["id"] == fixer.id
    assert back["quality_extras"] == {qid: "Weapons", f"{qid}:contact": fixer.id}


def test_a_chummer_pipeline_names_its_contact_without_our_guid() -> None:
    """A file Chummer saved has its own contact guids; the name still finds
    the row, and a name no contact carries is dropped rather than kept dangling."""
    state, qid = _with_quality("Black Market Pipeline", {"{id}": "Drugs"})
    root = ET.fromstring(state_to_chum5(state))
    quality = root.find("./qualities/quality")
    assert quality is not None
    quality.find("extra").text = "Drugs, Ghost"  # type: ignore[union-attr]
    contacts = root.find("contacts")
    assert contacts is not None
    ghost = ET.SubElement(contacts, "contact")
    ET.SubElement(ghost, "name").text = "Ghost"
    back = chum5_to_state(ET.tostring(root))[0]
    assert back["quality_extras"] == {qid: "Drugs", f"{qid}:contact": back["contacts"][0]["id"]}

    quality.find("extra").text = "Drugs, Nobody"  # type: ignore[union-attr]
    assert chum5_to_state(ET.tostring(root))[0]["quality_extras"] == {qid: "Drugs"}


def _career_with_rewards() -> CharacterState:
    from app.models import RewardEntry

    state, _ = _with_quality("Black Market Pipeline", {})
    log = [
        RewardEntry(label="Run: Renraku job", karma=6, nuyen=12000),
        RewardEntry(label="GM bonus", karma=2),
    ]
    return state.model_copy(
        update={"quality_ids": [], "career": True, "reward_log": log, "karma_earned": 8, "nuyen_earned": 12000}
    )


def test_the_reward_ledger_rides_chummers_expense_log() -> None:
    """Chummer logs karma and nuyen apart, so the run that paid both is two
    `<expense>` rows; `<rewardid>` joins them again on the way back."""
    state = _career_with_rewards()
    xml = state_to_chum5(state)
    rows = ET.fromstring(xml).findall("./expenses/expense")
    assert [(r.findtext("type"), r.findtext("amount"), r.findtext("reason")) for r in rows] == [
        ("Karma", "6", "Run: Renraku job"),
        ("Nuyen", "12000", "Run: Renraku job"),
        ("Karma", "2", "GM bonus"),
    ]

    back = chum5_to_state(xml)[0]
    assert back["reward_log"] == [row.model_dump() for row in state.reward_log]


def test_an_expense_log_that_does_not_add_up_is_left_out() -> None:
    """Chummer's `<karma>` is what is left, not what was earned — when the
    earnings in the log do not come to it, the rows would change the totals,
    so the import keeps the totals and says it skipped the rows."""
    root = ET.fromstring(state_to_chum5(_career_with_rewards()))
    root.find("karma").text = "3"  # type: ignore[union-attr]
    back, warnings = chum5_to_state(ET.tostring(root))
    assert "reward_log" not in back
    assert back["karma_earned"] == 3
    assert any(w["key"] == "engine.import.expensesSkipped" for w in warnings)
