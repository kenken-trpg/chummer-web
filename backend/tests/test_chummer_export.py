"""Chummer .chum5 export + round-trip (backend/app/chummer_export.py)."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from app.characters import compute_state, import_character
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.engine.priority import heritage_cost
from app.models import (
    ArmorInstall,
    ArmorModInstall,
    CharacterState,
    CommlinkInstall,
    ComplexFormInstall,
    ContactInstall,
    CyberwareInstall,
    GearInstall,
    LifestyleInstall,
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


def test_prototype_transhumans_pick_is_a_quality_of_its_own() -> None:
    """`<selectquality>`: Chummer adds the picked quality with
    `<qualitysource>Improvement</qualitysource>` and the granting quality's
    name as `<sourcename>`, ties the two with a SpecificQuality improvement,
    and leaves the granting quality's `<extra>` empty."""
    allergy = next(q["id"] for q in catalog()["qualities"] if q["name"] == "Allergy (Common, Mild)")
    state, qid = _with_quality("Prototype Transhuman", {"{id}": "Allergy (Common, Mild)", allergy: "Soy"})
    xml = state_to_chum5(state)
    root = ET.fromstring(xml)
    parent, child = root.findall("./qualities/quality")
    assert parent.findtext("extra") == ""
    assert (child.findtext("name"), child.findtext("extra")) == ("Allergy (Common, Mild)", "Soy")
    assert child.findtext("qualitysource") == "Improvement"
    assert child.findtext("sourcename") == "Prototype Transhuman"
    imp = root.find("./improvements/improvement")
    assert imp is not None
    assert imp.findtext("improvementttype") == "SpecificQuality"
    assert imp.findtext("improvedname") == child.findtext("guid")
    assert imp.findtext("sourcename") == parent.findtext("guid")

    back = chum5_to_state(xml)[0]
    assert back["quality_ids"] == [qid]  # the pick is granted, not bought
    assert back["quality_extras"] == {qid: "Allergy (Common, Mild)", allergy: "Soy"}


def test_a_prototype_transhuman_file_from_before_keeps_its_pick() -> None:
    """This app used to write the pick into the granting quality's `<extra>`."""
    state, qid = _with_quality("Prototype Transhuman", {})
    root = ET.fromstring(state_to_chum5(state))
    quality = root.find("./qualities/quality")
    assert quality is not None
    quality.find("extra").text = "Astral Beacon"  # type: ignore[union-attr]
    assert chum5_to_state(ET.tostring(root))[0]["quality_extras"] == {qid: "Astral Beacon"}


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


def test_a_career_balance_is_what_is_left_not_what_was_earned() -> None:
    """Chummer's `<karma>` / `<nuyen>` are what is left to spend. The log's
    earnings stay the rewards (Street Cred counts them); whatever else sets
    the saved balance apart — rent, purchases — is kept as an adjustment, so
    the balance comes back as saved."""
    root = ET.fromstring(state_to_chum5(_career_with_rewards()))
    saved_karma = int(root.findtext("karma") or 0)
    back, warnings = chum5_to_state(ET.tostring(root))
    assert (back["karma_adjust"], back["nuyen_adjust"]) == (0, 0)  # a fixed point

    root.find("karma").text = str(saved_karma - 3)  # type: ignore[union-attr]
    back, warnings = chum5_to_state(ET.tostring(root))
    assert warnings == []
    assert back["karma_adjust"] == -3
    derived = import_character(back).derived
    assert derived["karma"]["remaining"] == saved_karma - 3
    assert derived["karma_earned"] == sum(row.karma for row in _career_with_rewards().reward_log)


def test_skills_are_written_the_way_chummer_reads_them() -> None:
    """`<newskills>`, an active skill by its skills.xml id: Chummer drops a
    skill with no `<suid>`, and without `<newskills>` looks for a pre-5 layout."""
    c = catalog()
    state = CharacterState(
        id="sk",
        name="Skills",
        priorities=Priorities(),
        metatype="Human",
        attributes={},
        skills={"Pistols": 4},
        skill_specializations={"Pistols": "Revolvers", "Seattle Gangs": "Halloweeners"},
        skill_groups={"Stealth": 2},
        knowledge_skills={"Seattle Gangs": 2, "Arcana Lore": 1},
        knowledge_categories={"Seattle Gangs": "Street", "Arcana Lore": "Academic"},
        native_languages=["Japanese"],
    )
    root = ET.fromstring(state_to_chum5(state))
    assert root.find("skills") is None
    pistols_id = next(row["id"] for row in c["skills"]["skills"] if row["name"] == "Pistols")
    (active,) = root.findall("./newskills/skills/skill")
    assert (active.findtext("suid"), active.findtext("base"), active.findtext("karma")) == (pistols_id, "4", "0")
    assert active.findtext("./specs/spec/name") == "Revolvers"
    know = {s.findtext("name"): s for s in root.findall("./newskills/knoskills/skill")}
    assert know["Japanese"].findtext("isnativelanguage") == "True"
    assert know["Seattle Gangs"].findtext("suid") == "00000000-0000-0000-0000-000000000000"  # custom
    assert know["Seattle Gangs"].findtext("./specs/spec/name") == "Halloweeners"
    assert root.findtext("./newskills/groups/group/name") == "Stealth"

    back, warnings = chum5_to_state(ET.tostring(root))
    assert warnings == []
    assert back["skills"] == {"Pistols": 4}
    assert back["skill_groups"] == {"Stealth": 2}
    assert back["knowledge_skills"] == {"Seattle Gangs": 2, "Arcana Lore": 1}
    assert back["native_languages"] == ["Japanese"]
    assert back["skill_specializations"] == {"Pistols": "Revolvers", "Seattle Gangs": "Halloweeners"}


def test_ammo_counts_rounds_in_chummer_and_boxes_here() -> None:
    """Chummer's `<qty>` is single rounds; this app's `qty` is lots of
    `costfor` (a box of 10). Read straight across, 100 rounds of APDS were
    billed as a hundred boxes."""
    apds = next(row for row in catalog()["gear"] if row["name"] == "Ammo: APDS")
    assert apds["costfor"] == 10
    xml = b"""<character><metatype>Human</metatype><buildmethod>Priority</buildmethod>
      <gears><gear><name>Ammo: APDS</name><category>Ammunition</category><qty>100</qty></gear></gears>
    </character>"""
    st, _ = chum5_to_state(xml)
    assert [row["qty"] for row in st["gear"]] == [10]
    derived = import_character(st).derived
    assert derived["gear"][0]["nuyen"] == 10 * int(apds["cost"])

    back = ET.fromstring(state_to_chum5(import_character(st)))
    assert back.findtext("./gears/gear/qty") == "100"


def test_raised_lifestyle_points_round_trip() -> None:
    low = next(row["id"] for row in catalog()["lifestyles"] if row["name"] == "Low")
    state = CharacterState(
        id="ls",
        name="ls",
        priorities=Priorities(),
        metatype="Human",
        attributes={},
        lifestyles=[LifestyleInstall(lifestyle_id=low, comforts=1, area=1)],
    )
    back = chum5_to_state(state_to_chum5(state))[0]["lifestyles"][0]
    assert (back["comforts"], back["area"], back["security"]) == (1, 1, 0)


def test_a_picked_price_and_a_custom_name_round_trip() -> None:
    custom = "0025f1c7-45a4-4ec5-a692-e18aab2f97a9"
    state = CharacterState(
        id="pc",
        name="pc",
        priorities=Priorities(),
        metatype="Human",
        attributes={},
        gear=[GearInstall(gear_id=custom, cost=250, name="Rosary")],
    )
    back = chum5_to_state(state_to_chum5(import_character(state.model_dump())))[0]["gear"][0]
    assert (back["gear_id"], back["cost"], back["name"]) == (custom, 250, "Rosary")


def test_a_listed_knowledge_skill_keeps_its_type() -> None:
    """The engine stores a listed skill's type only when it was changed, and
    the export filled the gap with Academic: Area Knowledge: Seattle came back
    a LOG skill in 20 of Chummer's 34 test saves."""
    state = compute_state(
        CharacterState(
            id="k",
            name="K",
            priorities=Priorities(),
            metatype="Human",
            attributes={},
            knowledge_skills={"Area Knowledge: Seattle": 3, "Homebrew Lore": 2},
        )
    )
    know = {
        s.findtext("name"): s.findtext("skillcategory")
        for s in ET.fromstring(state_to_chum5(state)).findall("./newskills/knoskills/skill")
    }
    assert know["Area Knowledge: Seattle"] == "Street"
    assert know["Homebrew Lore"] == "Street"


def test_ratings_extras_and_alchemy_survive_the_round_trip() -> None:
    """Armor and accessory ratings, a complex form's attribute and a spell's
    alchemical form were read on import but never written."""
    state = CharacterState(
        id="rt",
        name="Round trip",
        priorities=Priorities(),
        metatype="Human",
        attributes={},
        armor=[ArmorInstall(id="a1", armor_id="fc4074b5-b48a-43d4-8d9c-25a11da2a6a8", rating=6)],
        weapons=[WeaponInstall(id="w1", weapon_id="971c711b-db32-4339-9203-865ef38f350e")],
        weapon_accessories=[
            WeaponAccessoryInstall(accessory_id="d40d2fc6-3aad-4793-843d-20e3597b2365", parent_id="w1", rating=2)
        ],
        complex_forms=[ComplexFormInstall(form_id="2abb9759-30b1-490f-9b42-0d6b7d282526", level=1, extra="Firewall")],
        spells=[SpellInstall(spell_id="c78d91cc-fa02-48c3-a243-28823a2038ef", alchemical=True)],
    )
    back, _ = chum5_to_state(state_to_chum5(state))
    assert [row["rating"] for row in back["armor"]] == [6]
    assert [row["rating"] for row in back["weapon_accessories"]] == [2]
    assert [row["extra"] for row in back["complex_forms"]] == ["Firewall"]
    assert [row["alchemical"] for row in back["spells"]] == [True]


MADE_MAN = "45be40cc-a21a-4771-b47d-a532ea60b205"


def test_a_contact_a_quality_added_is_not_added_twice() -> None:
    """Made Man adds a contact. Exported without the AddContact improvement
    that ties it to the quality, it came back as a contact of its own, and the
    quality added a second one (Ushi Resub: 3 contacts became 4)."""
    state = compute_state(
        CharacterState(
            id="mm",
            name="Made",
            priorities=Priorities(),
            metatype="Human",
            attributes={},
            quality_ids=[MADE_MAN],
            contacts=[ContactInstall(name="Fixer", connection=3, loyalty=2)],
        )
    )
    granted = [c for c in state.contacts if c.source_quality_id == MADE_MAN]
    assert len(granted) == 1
    back = import_character(chum5_to_state(state_to_chum5(state))[0])
    assert sorted(c.name for c in back.contacts) == sorted(c.name for c in state.contacts)
    assert [c.source_quality_id for c in back.contacts if c.name == granted[0].name] == [MADE_MAN]


def test_chummers_addcontact_improvement_marks_the_granted_contact() -> None:
    """Chummer names the quality by its `<id>`, not by the catalog guid."""
    xml = f"""<character><metatype>Human</metatype><buildmethod>Priority</buildmethod>
      <qualities><quality><guid>{MADE_MAN}</guid><name>Made Man</name>
        <id>0b1e7a3c-0000-4000-8000-000000000001</id></quality></qualities>
      <contacts><contact><name>Made Man</name><connection>1</connection><loyalty>3</loyalty>
        <guid>0b1e7a3c-0000-4000-8000-000000000002</guid></contact></contacts>
      <improvements><improvement>
        <improvedname>0b1e7a3c-0000-4000-8000-000000000002</improvedname>
        <sourcename>0b1e7a3c-0000-4000-8000-000000000001</sourcename>
        <improvementttype>AddContact</improvementttype><improvementsource>Quality</improvementsource>
      </improvement></improvements>
    </character>""".encode()
    st, _ = chum5_to_state(xml)
    assert [c["source_quality_id"] for c in st["contacts"]] == [MADE_MAN]
    assert len(import_character(st).contacts) == 1


def test_the_build_pools_are_written_as_figures() -> None:
    """Chummer stores these rather than recomputing them from the priority
    table (`Character.Load` reads every one back), so a save that leaves them
    out opens as a character with points spent and no pool they came from —
    negative attributes and negative special attribute points, which is how
    this was found.
    """
    src = _rich_state()
    root = ET.fromstring(state_to_chum5(import_character(src.model_dump())))
    derived = import_character(src.model_dump()).derived
    assert root.findtext("totalspecial") == str(derived["points"]["special"]["max"])
    # Chummer tracks what was spent in the attributes themselves and never
    # decrements this, so the two are the same number.
    assert root.findtext("special") == root.findtext("totalspecial")
    assert root.findtext("totalattributes") == str(derived["points"]["attributes"]["max"])
    assert root.findtext("contactpoints") == str(derived["contact_points"]["free"])
    assert root.findtext("spelllimit") == str(derived["spell_points"]["free"])
    # Resources E, from the priority table — not the pool, which also holds
    # the nuyen bought with leftover karma.
    assert root.findtext("startingnuyen") == "6000"
    assert (root.findtext("maxkarma"), root.findtext("maxnuyen")) == ("25", "10")


def test_a_metavariant_is_charged_for_its_heritage_once() -> None:
    """A metavariant's priority row replaces the metatype's rather than adding
    to it: `Shapeshifter: Vulpine` costs 5 karma at priority C, and its Human
    variant costs that same 5. Adding the two charged the character twice, and
    wrote the doubled figure out as `<metatypebp>` (Chummer's own
    `Mittens Chargen` says 5 where this said 10)."""
    assert heritage_cost("C", "Shapeshifter: Vulpine", "Human") == (4, 5)
    assert heritage_cost("C", "Shapeshifter: Vulpine", None) == (4, 5)
    # a metatype whose variants really do cost extra still reads its own row
    assert heritage_cost("C", "Elf", "Wakyambi") == (3, 12)
    assert heritage_cost("C", "Elf", None) == (3, 0)


def test_what_the_character_is_is_written_for_chummer_to_read() -> None:
    """`Character.Load` reads each of these back, and a missing one is read as
    its default: an adept whose `<adept>` is absent opens in Chummer mundane,
    with the Magic they paid for disallowed. They follow `enabled_tabs`, the
    same answer this app draws its own tabs from."""
    src = _rich_state()  # a Magician
    root = ET.fromstring(state_to_chum5(import_character(src.model_dump())))
    assert (root.findtext("magenabled"), root.findtext("magician")) == ("True", "True")
    assert [root.findtext(t) for t in ("adept", "technomancer", "resenabled", "depenabled")] == [
        "False",
        "False",
        "False",
        "False",
    ]
    # the moment the special attribute was granted: this app cannot start a
    # character below 6
    assert root.findtext("essenceatspecialstart") == "6"
    assert root.findtext("gameedition") == "SR5"
    assert root.findtext("metatypecategory") == "Metahuman"
    assert (root.findtext("walk"), root.findtext("run")) == ("2/1/0", "4/0/0")


def test_a_mundane_character_claims_no_special_attribute() -> None:
    """The flags are written for every character, not only the awakened: left
    out, they are the *previous* character's in a Chummer already holding
    one. A mundane has no moment a special attribute was granted, which
    Chummer's own loader fills in for itself."""
    base = _rich_state()
    src = base.model_copy(
        update={
            # the talent is the *priority*, not the label: leaving Talent on A
            # keeps Magic switched on whatever the name says
            "priorities": base.priorities.model_copy(update={"Talent": "E", "Resources": "A"}),
            "talent": "Mundane",
            "spells": [],
            "mystic_pp": 0,
        }
    )
    root = ET.fromstring(state_to_chum5(import_character(src.model_dump())))
    assert [root.findtext(t) for t in ("magenabled", "magician", "adept")] == ["False", "False", "False"]
    assert root.find("essenceatspecialstart") is None


def test_a_portrait_free_character_says_it_has_no_main_portrait() -> None:
    """-1 is Chummer's "none". Without it the save is read as having a
    portrait at index 0 that is not there."""
    root = ET.fromstring(state_to_chum5(import_character(_rich_state().model_copy(update={"portrait": ""}))))
    assert root.findtext("mainmugshotindex") == "-1"
    assert root.find("mugshots") is None
