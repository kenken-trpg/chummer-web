"""Regressions from the Japanese EXE import report: choices, names and arts."""

from __future__ import annotations

import pytest

from app.characters import apply_patch
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.engine import compute
from app.engine.constants import quality_attribute_extra_key
from app.models import CharacterPatch, CharacterState, InitiationChoice, Priorities, SettingsState
from app.settings_file import parse_settings_xml
from tests.notice_asserts import has
from tests.test_initiation import _initiate

VAMPIRE = "4024b100-c762-4354-95e4-db5cb0694a9a"


def _vampire(extras: dict[str, str]) -> CharacterState:
    return CharacterState(
        id="vampire",
        name="Vampire",
        metatype="Ork",
        priorities=Priorities(),
        quality_ids=[VAMPIRE],
        quality_extras=extras,
        attributes={"BOD": 3, "REA": 3, "WIL": 3, "CHA": 3},
    )


def test_all_four_infected_choices_affect_ratings_and_survive_recompute() -> None:
    picks = ["BOD", "REA", "WIL", "CHA"]
    extras = {quality_attribute_extra_key(VAMPIRE, i): a for i, a in enumerate(picks)}
    baseline = compute(_vampire({}))
    out = compute(_vampire(extras))
    for attr in picks:
        assert out.derived["totals"][attr] == baseline.derived["totals"][attr] + 1
        assert (
            out.derived["metatype_info"]["attributes"][attr]["max"]
            == baseline.derived["metatype_info"]["attributes"][attr]["max"]
        )
    assert not has(out.derived["warnings"], "engine.attrs.pickAttribute")
    assert out.quality_extras == extras
    again = apply_patch(out, CharacterPatch(name="Renamed"))
    assert again.quality_extras == extras
    assert again.derived["totals"] == out.derived["totals"]


def test_infected_slots_reject_the_wrong_attribute_group() -> None:
    out = compute(_vampire({VAMPIRE: "WIL", f"{VAMPIRE}:attribute:2": "BOD"}))
    assert has(out.derived["warnings"], "engine.attrs.attributeNotAllowed")
    assert has(out.derived["warnings"], "engine.attrs.pickAttribute")


@pytest.mark.parametrize("extra", ["BOD (1), REA (1), WIL (1), CHA (1)", "BOD, REA, WIL, CHA"])
def test_import_restores_infected_choices_from_extra(extra: str) -> None:
    st, _ = chum5_to_state(
        f"<character><qualities><quality><id>{VAMPIRE}</id><extra>{extra}</extra></quality></qualities></character>".encode()
    )
    assert [st["quality_extras"][quality_attribute_extra_key(VAMPIRE, i)] for i in range(4)] == [
        "BOD",
        "REA",
        "WIL",
        "CHA",
    ]


def test_import_restores_choices_from_quality_improvements() -> None:
    imps = "".join(
        f"<improvement><improvedname>{a}</improvedname><sourcename>quality-instance</sourcename><improvementttype>Attribute</improvementttype><improvementsource>Quality</improvementsource></improvement>"
        for a in ["BOD", "BOD", "WIL", "CHA"]
    )
    st, _ = chum5_to_state(
        f"<character><qualities><quality><id>{VAMPIRE}</id><guid>quality-instance</guid><extra /></quality></qualities><improvements>{imps}</improvements></character>".encode()
    )
    assert [st["quality_extras"][quality_attribute_extra_key(VAMPIRE, i)] for i in range(4)] == [
        "BOD",
        "BOD",
        "WIL",
        "CHA",
    ]


def test_infected_choices_survive_chummer_export_and_import() -> None:
    extras = {quality_attribute_extra_key(VAMPIRE, i): a for i, a in enumerate(["BOD", "BOD", "WIL", "CHA"])}
    st, _ = chum5_to_state(state_to_chum5(_vampire(extras)))
    assert st["quality_extras"] == extras


@pytest.mark.parametrize("grade", ["Betaware", "ベータウェア"])
def test_import_keeps_beta_grade_and_uses_beta_cost_and_essence(grade: str) -> None:
    xml = f"<character><cyberwares><cyberware><name>Datajack</name><grade>{grade}</grade></cyberware><cyberware><name>Muscle Toner</name><improvementsource>Bioware</improvementsource><grade>{grade}</grade></cyberware></cyberwares></character>"
    st, _ = chum5_to_state(xml.encode())
    out = compute(CharacterState.model_validate(st))
    for kind in ("cyberware", "bioware"):
        assert getattr(out, kind)[0].grade == "Betaware"
        assert out.derived[kind][0]["grade"] == "Betaware"
    assert out.derived["cyberware"][0]["nuyen"] == 1500
    assert out.derived["cyberware"][0]["essence"] == 0.07
    restored = apply_patch(out, CharacterPatch(name="Renamed"))
    assert restored.cyberware[0].grade == restored.bioware[0].grade == "Betaware"


@pytest.mark.parametrize("en,ja", [("Adrenaline Boost", "アドレナリン・ブースト"), ("Improved Sense", "感覚強化")])
def test_saved_power_id_matches_even_with_localized_or_custom_name(en: str, ja: str) -> None:
    pid = next(p["id"] for p in catalog()["powers"] if p["name"] == en)
    st, warnings = chum5_to_state(
        f"<character><powers><power><id>{pid}</id><guid>instance-guid</guid><name>{ja}</name><rating>2</rating><extra>Low-Light Vision</extra></power></powers></character>".encode()
    )
    assert not warnings
    assert st["adept_powers"][0]["power_id"] == pid
    assert st["adept_powers"][0]["extra"] == "Low-Light Vision"


def test_import_resolves_japanese_power_name_when_saved_id_is_unknown() -> None:
    st, warnings = chum5_to_state(
        "<character><powers><power><id>legacy-or-custom-id</id><name>アドレナリン・ブースト</name><rating>1</rating></power></powers></character>".encode()
    )
    assert not warnings
    assert st["adept_powers"][0]["power_id"] == next(
        p["id"] for p in catalog()["powers"] if p["name"] == "Adrenaline Boost"
    )


def test_import_resolves_localized_power_name_with_parenthetical_extra() -> None:
    st, warnings = chum5_to_state(
        "<character><powers><power><id>custom-id</id><name>感覚強化 (暗視強化)</name><rating>1</rating><extra>Low-Light Vision</extra></power></powers></character>".encode()
    )
    assert not warnings
    assert st["adept_powers"][0]["power_id"] == next(
        p["id"] for p in catalog()["powers"] if p["name"] == "Improved Sense"
    )


@pytest.mark.parametrize("name", ["Centering", "Masking"])
def test_core_only_and_ignoreart_settings_do_not_require_sg_art(name: str) -> None:
    pid = next(m["id"] for m in catalog()["metamagics"] if m["name"] == name)
    for settings in [
        SettingsState(books=["SR5"]),
        parse_settings_xml(b"<settings><ignoreart>True</ignoreart><books><book>SG</book></books></settings>"),
    ]:
        out = compute(_initiate("Magician", "art-gates", [InitiationChoice(grade=1, option_id=pid)], settings=settings))
        assert not any("requires" in w["key"] for w in out.derived["warnings"])
        assert out.initiations[0].option_id == pid
    assert settings.ignore_art is True
    assert "ignoreart" not in settings.unsupported


def test_masking_warning_includes_the_art_alternative_with_sg_enabled() -> None:
    pid = next(m["id"] for m in catalog()["metamagics"] if m["name"] == "Masking")
    out = compute(
        _initiate(
            "Magician",
            "masking-art",
            [InitiationChoice(grade=1, option_id=pid)],
            settings=SettingsState(books=["SR5", "SG"]),
        )
    )
    assert has(out.derived["warnings"], "engine.initiation.requiresArtOrQuality", name="Masking")
    warning = next(w for w in out.derived["warnings"] if w["key"] == "engine.initiation.requiresArtOrQuality")
    assert warning["params"]["arts"] == [{"tr": "Masking"}]


@pytest.mark.parametrize("name", ["Centering", "Masking"])
def test_same_grade_art_and_metamagic_import_and_round_trip(name: str) -> None:
    pid = next(m["id"] for m in catalog()["metamagics"] if m["name"] == name)
    aid = next(a["id"] for a in catalog()["magic_arts"] if a["name"] == name)
    state = _initiate(
        "Magician",
        "art-with-meta",
        [InitiationChoice(grade=1, option_id=pid, art_ids=[aid])],
        settings=SettingsState(books=["SR5", "SG"]),
    )
    out = compute(state)
    assert not any("requires" in w["key"] for w in out.derived["warnings"])
    assert out.derived["initiation"]["karma"] == 13
    assert out.derived["initiation"]["arts"][0]["name"] == name
    assert out.initiations[0].art_ids == [aid]
    saved, _ = chum5_to_state(state_to_chum5(out))
    assert saved["initiations"][0]["option_id"] == pid
    assert saved["initiations"][0]["art_ids"] == [aid]
    imported = compute(CharacterState.model_validate(saved))
    assert not any("requires" in w["key"] for w in imported.derived["warnings"])


def test_core_only_setting_can_explicitly_enforce_arts() -> None:
    pid = next(m["id"] for m in catalog()["metamagics"] if m["name"] == "Centering")
    out = compute(
        _initiate(
            "Magician",
            "explicit-art",
            [InitiationChoice(grade=1, option_id=pid)],
            settings=SettingsState(books=["SR5"], ignore_art=False),
        )
    )
    assert has(out.derived["warnings"], "engine.initiation.requiresArt", name="Centering")
