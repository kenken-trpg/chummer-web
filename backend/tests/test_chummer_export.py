"""Chummer .chum5 export + round-trip (backend/app/chummer_export.py)."""

from __future__ import annotations

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
from app.store import import_character


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


def test_round_tripped_state_still_validates() -> None:
    st, _ = chum5_to_state(state_to_chum5(_rich_state()))
    ch = import_character({k: v for k, v in st.items() if k != "_warnings"})
    assert ch.id and isinstance(ch.derived, dict)
