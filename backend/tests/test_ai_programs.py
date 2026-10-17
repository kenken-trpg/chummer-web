"""An A.I.'s programs (DT p.158), as the pinned Chummer source prices them.

CharacterCreate bills every bought program at `<karmanewaiprogram>` (5), one
in the Advanced Programs category at `<karmanewaiadvancedprogram>` (8);
Inherent Program adds one common or hacking program that cannot be deleted
and costs nothing; SelectAIProgram asks that a program's `<required>` one is
already among the A.I.'s programs. See `docs/ai-chargen.md`.
"""

import xml.etree.ElementTree as ET

import pytest

from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.data_loader import catalog
from app.engine import compute, default_attributes, find_metatype
from app.models import AIProgramInstall, CharacterState, Priorities, SettingsState
from tests.notice_asserts import has

AI = "A.I."


def _program(name: str) -> dict:
    return next(p for p in catalog()["ai_programs"] if p["name"] == name)


def _quality_id(name: str) -> str:
    return next(q["id"] for q in catalog()["qualities"] if q["name"] == name)


def _ai(metavariant: str | None = "E-Ghost", *programs: str, **kwargs: object) -> CharacterState:
    # An E-Ghost: the bare A.I.'s Codeslinger wants a Matrix action picked.
    return CharacterState(
        id="ai",
        name="Ghost",
        metatype=AI,
        metavariant=metavariant,
        talent=AI,
        priorities=Priorities(Heritage="A", Attributes="B", Talent="C", Skills="D", Resources="E"),
        attributes=default_attributes(find_metatype(AI, metavariant)),
        ai_programs=[AIProgramInstall(program_id=_program(name)["id"]) for name in programs],
        **kwargs,  # type: ignore[arg-type]
    )


def _spent(out: CharacterState) -> int:
    lines = {row["notice"]["key"]: row["amount"] for row in out.derived["karma_spend_breakdown"]}
    return lines.get("engine.spend.aiPrograms", 0)


# --- the data -----------------------------------------------------------------


def test_the_catalog_holds_the_programs_file() -> None:
    programs = catalog()["ai_programs"]
    assert len(programs) == 71
    advanced = [p["name"] for p in programs if p["advanced"]]
    assert len(advanced) == 16
    assert "Authority" in advanced
    assert _program("Authority")["required"] == ["Exploit"]
    assert _program("Skill Autosoft")["needs_extra"] is True
    assert _program("Browse")["needs_extra"] is False


def test_inherent_program_offers_the_common_and_hacking_programs() -> None:
    inherent = next(q for q in catalog()["qualities"] if q["name"] == "Inherent Program")
    options = set(inherent["select_options"])
    assert {"Browse", "Exploit", "Stealth"} <= options
    assert "Authority" not in options  # advanced
    assert "Clearsight Autosoft" not in options  # an autosoft
    assert inherent["extra_kind"] == "text"


# --- the price ----------------------------------------------------------------


def test_a_program_costs_five_and_an_advanced_one_eight() -> None:
    out = compute(_ai("E-Ghost", "Browse", "Exploit", "Authority"))
    rows = {row["name"]: row for row in out.derived["ai_programs"]}
    assert [rows[name]["karma"] for name in ("Browse", "Exploit", "Authority")] == [5, 5, 8]
    assert rows["Authority"]["advanced"] is True
    assert _spent(out) == 18
    assert not out.derived["errors"]


def test_the_settings_set_the_price() -> None:
    settings = SettingsState(karma_ai_program=6, karma_ai_advanced_program=10)
    out = compute(_ai("E-Ghost", "Exploit", "Authority", settings=settings))
    assert _spent(out) == 16


def test_a_karma_build_pays_the_same() -> None:
    out = compute(_ai("E-Ghost", "Browse", build_method="Karma"))
    assert _spent(out) == 5


# --- what a program needs -----------------------------------------------------


def test_an_advanced_program_needs_its_base_program() -> None:
    out = compute(_ai("E-Ghost", "Authority"))
    assert has(out.derived["errors"], "engine.aiPrograms.prereq")


def test_the_need_is_a_creation_gate_only() -> None:
    # Chummer asks when a program is added, never again: a career A.I. that
    # had Exploit when it took Authority keeps Authority.
    out = compute(_ai("E-Ghost", "Authority", career=True))
    assert not has(out.derived["errors"], "engine.aiPrograms.prereq")


def test_an_autosoft_asks_what_it_is_for() -> None:
    out = compute(_ai("E-Ghost", "Skill Autosoft"))
    assert has(out.derived["warnings"], "engine.aiPrograms.pickExtra")
    state = _ai("E-Ghost")
    state.ai_programs = [AIProgramInstall(program_id=_program("Skill Autosoft")["id"], extra="Pistols")]
    out = compute(state)
    assert not has(out.derived["warnings"], "engine.aiPrograms.pickExtra")
    assert out.derived["ai_programs"][0]["extra"] == "Pistols"


# --- Inherent Program ---------------------------------------------------------


def test_a_protosapient_picks_its_inherent_program_for_free() -> None:
    inherent = _quality_id("Inherent Program")
    unpicked = compute(_ai("Protosapient"))
    assert has(unpicked.derived["errors"], "engine.qualities.pickExtra")
    assert unpicked.derived["ai_programs"] == []

    out = compute(_ai("Protosapient", "Authority", quality_extras={inherent: "Exploit"}))
    rows = {row["name"]: row for row in out.derived["ai_programs"]}
    assert rows["Exploit"]["free"] is True
    assert rows["Exploit"]["karma"] == 0
    assert rows["Exploit"]["granted_by"] == "Inherent Program"
    # the free one satisfies Authority's need
    assert not has(out.derived["errors"], "engine.aiPrograms.prereq")
    assert _spent(out) == 8


def test_an_inherent_program_is_not_an_advanced_one() -> None:
    out = compute(_ai("Protosapient", quality_extras={_quality_id("Inherent Program"): "Authority"}))
    assert has(out.derived["errors"], "engine.qualities.extraInvalid")
    assert out.derived["ai_programs"] == []


# --- who has them -------------------------------------------------------------


def test_a_metahuman_keeps_no_programs() -> None:
    state = CharacterState(
        id="human",
        name="Joe",
        metatype="Human",
        priorities=Priorities(Heritage="E", Attributes="B", Talent="C", Skills="A", Resources="D"),
        attributes=default_attributes(find_metatype("Human", None)),
        ai_programs=[AIProgramInstall(program_id=_program("Browse")["id"])],
    )
    out = compute(state)
    assert out.ai_programs == []
    assert _spent(out) == 0


# --- .chum5 -------------------------------------------------------------------


def _round_trip(state: CharacterState) -> tuple[CharacterState, CharacterState, ET.Element]:
    first = compute(state)
    xml = state_to_chum5(first)
    again, _ = chum5_to_state(xml)
    return first, compute(CharacterState(**again)), ET.fromstring(xml)


def test_the_export_writes_the_programs_chummer_reads() -> None:
    inherent = _quality_id("Inherent Program")
    _, _, root = _round_trip(_ai("Protosapient", "Authority", quality_extras={inherent: "Exploit"}))
    rows = {p.findtext("name"): p for p in root.iter("aiprogram")}
    assert set(rows) == {"Exploit", "Authority"}
    assert rows["Exploit"].findtext("candelete") == "False"
    assert rows["Authority"].findtext("candelete") == "True"
    assert rows["Authority"].findtext("isadvancedprogram") == "True"
    assert rows["Authority"].findtext("sourceid") == _program("Authority")["id"]


@pytest.mark.parametrize("metavariant", ["Protosapient", "E-Ghost"])
def test_programs_and_the_inherent_pick_survive_a_round_trip(metavariant: str) -> None:
    extras = {_quality_id("Inherent Program"): "Exploit"} if metavariant == "Protosapient" else {}
    state = _ai(metavariant, "Authority", "Browse", quality_extras=extras)
    if metavariant == "E-Ghost":
        state.ai_programs.append(AIProgramInstall(program_id=_program("Exploit")["id"]))
    first, second, _ = _round_trip(state)

    def summary(out: CharacterState) -> list[tuple]:
        return sorted((r["name"], r["free"], r["karma"]) for r in out.derived["ai_programs"])

    assert summary(second) == summary(first)
    assert _spent(second) == _spent(first)


def test_a_metatype_qualitys_pick_survives_a_round_trip() -> None:
    # The bare A.I.'s Codeslinger: a pick on a quality the metatype grants,
    # which the export used to write without and the import to throw away.
    codeslinger = _quality_id("Codeslinger")
    first, second, _ = _round_trip(_ai(None, quality_extras={codeslinger: "Brute Force"}))
    assert not first.derived["errors"]
    assert second.quality_extras.get(codeslinger) == "Brute Force"
    assert not second.derived["errors"]


@pytest.mark.parametrize(("metavariant", "bought"), [("Protosapient", False), ("E-Ghost", True)])
def test_the_inherent_program_is_tied_to_its_quality(metavariant: str, bought: bool) -> None:
    # Chummer's selectinherentaiprogram makes an AIProgram improvement from
    # the quality's guid to the program's; removing the quality removes it.
    inherent = _quality_id("Inherent Program")
    state = _ai(metavariant, quality_extras={inherent: "Exploit"})
    if bought:
        state.quality_ids = [inherent]
    _, second, root = _round_trip(state)
    program = next(p for p in root.iter("aiprogram") if p.findtext("name") == "Exploit")
    quality = next(
        q
        for q in root.iter("quality")
        if q.findtext("name") == "Inherent Program" and (q.findtext("qualitysource") == "Selected") == bought
    )
    links = [i for i in root.iter("improvement") if i.findtext("improvementttype") == "AIProgram"]
    assert len(links) == 1
    assert links[0].findtext("improvedname") == program.findtext("guid")
    assert links[0].findtext("sourcename") == quality.findtext("guid")
    assert links[0].findtext("improvementsource") == "Quality"
    # and reading it back still bills nothing for it
    assert [(r["name"], r["free"]) for r in second.derived["ai_programs"]] == [("Exploit", True)]


def test_the_foundry_check_names_the_programs_it_leaves_out() -> None:
    # Foundry's Chummer import reads no `aiprograms`, so the export writes
    # none and says so before the file is written.
    from app.fvtt_export.check import export_omissions

    notices = export_omissions(_ai("E-Ghost", "Browse", "Exploit"))
    names = [n["params"]["name"]["tr"] for n in notices if n["key"] == "engine.export.fvttAIProgram"]
    assert names == ["Browse", "Exploit"]
