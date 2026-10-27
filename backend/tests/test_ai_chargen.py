"""An A.I. in creation (DT p.135), as the pinned Chummer source builds one.

No test save of Chummer's has an A.I. player character, so each rule here is
pinned against the source instead (`docs/ai-chargen.md`):
SelectMetatypePriority halves the attribute points and starts Depth at the
talent's `<depth>`, `Character.IsAI` caps Edge at Depth, the talents'
`<forbidden>` / `<required>` keep the A.I. and everyone else apart, and
SelectQuality offers an A.I. only its `<qualityrestriction>`.
"""

import xml.etree.ElementTree as ET

import pytest

from app.catalog_view import public_catalog
from app.characters import apply_patch
from app.chummer_export import state_to_chum5
from app.chummer_import import chum5_to_state
from app.engine import compute, default_attributes, find_metatype, talent_allowed, talent_options
from app.models import CharacterPatch, CharacterState, Priorities
from tests.notice_asserts import has

AI = "A.I."
VARIANTS = ("E-Ghost", "Xenosapient", "Protosapient")


def _ai(
    metavariant: str | None = None,
    method: str = "Priority",
    *,
    attributes: str = "B",
    talent_letter: str = "C",
    **kwargs: object,
) -> CharacterState:
    # Heritage A or C (B is the A.I.'s too); the letters left go to the rest.
    heritage = "C" if "A" in {attributes, talent_letter} else "A"
    rest = [letter for letter in "ABCDE" if letter not in {heritage, attributes, talent_letter}]
    kwargs.setdefault("talent", AI)
    return CharacterState(
        id="ai",
        name="Ghost",
        metatype=AI,
        metavariant=metavariant,
        build_method=method,
        priorities=Priorities(
            Heritage=heritage, Attributes=attributes, Talent=talent_letter, Skills=rest[0], Resources=rest[1]
        ),
        attributes=default_attributes(find_metatype(AI, metavariant)),
        **kwargs,  # type: ignore[arg-type]
    )


def _human(**kwargs: object) -> CharacterState:
    return CharacterState(
        id="human",
        name="Joe",
        metatype="Human",
        priorities=Priorities(Heritage="E", Attributes="B", Talent="C", Skills="A", Resources="D"),
        attributes=default_attributes(find_metatype("Human", None)),
        **kwargs,  # type: ignore[arg-type]
    )


def _quality_id(name: str) -> str:
    from app.data_loader import catalog

    return next(q["id"] for q in catalog()["qualities"] if q["name"] == name)


# --- the data -----------------------------------------------------------------


@pytest.mark.parametrize("metavariant", [None, *VARIANTS])
def test_an_ai_has_depth_and_no_body(metavariant: str | None) -> None:
    meta = find_metatype(AI, metavariant)
    attrs = meta["attributes"]
    assert (attrs["DEP"]["min"], attrs["DEP"]["max"]) == (1, 6)
    for key in ("BOD", "AGI", "REA", "STR"):
        assert (attrs[key]["min"], attrs[key]["max"]) == (0, 0)
    assert meta["halve_attribute_points"] is True
    restriction = meta["quality_restriction"]
    assert len(restriction["Positive"]) == 63
    assert len(restriction["Negative"]) == 43


def test_a_metavariant_keeps_its_own_ranges() -> None:
    # Unlike a shapeshifter's, an A.I.'s metavariant is a different mind.
    assert find_metatype(AI, "Xenosapient")["attributes"]["LOG"]["max"] == 8
    assert find_metatype(AI, None)["attributes"]["LOG"]["max"] == 7


def test_a_metahuman_has_no_depth_and_no_restriction() -> None:
    human = find_metatype("Human", None)
    assert human["attributes"]["DEP"] == {"min": 0, "max": 0, "aug": 0}
    assert human["halve_attribute_points"] is False
    assert human["quality_restriction"] is None


# --- the talent ---------------------------------------------------------------


@pytest.mark.parametrize(("letter", "depth"), [("A", 6), ("B", 4), ("C", 3), ("D", 2), ("E", 1)])
def test_every_talent_row_offers_the_ai_its_depth(letter: str, depth: int) -> None:
    talent = next(t for t in talent_options(letter) if t["name"] == AI)
    assert talent["depth"] == depth
    assert talent_allowed(talent, AI)
    assert not talent_allowed(talent, "Human")
    # An A.I. may take nothing else, not even Mundane.
    others = [t for t in talent_options(letter) if t["name"] != AI]
    assert others
    assert not any(talent_allowed(t, AI) for t in others)


def test_a_technomancer_must_be_a_metahuman() -> None:
    techno = next(t for t in talent_options("A") if t["name"] == "Technomancer")
    assert talent_allowed(techno, "Human")
    # The base metatype's category: a Nocturna is a Metahuman Elf.
    assert talent_allowed(techno, "Elf")
    assert not talent_allowed(techno, "Centaur")
    assert not talent_allowed(techno, "Shapeshifter: Vulpine")


# --- creation -----------------------------------------------------------------


@pytest.mark.parametrize(("letter", "depth"), [("A", 6), ("B", 4), ("C", 3), ("D", 2), ("E", 1)])
def test_depth_starts_at_the_talent(letter: str, depth: int) -> None:
    # An E-Ghost: the bare A.I.'s Codeslinger wants a Matrix action picked.
    out = compute(_ai("E-Ghost", talent_letter=letter, attributes="B" if letter != "B" else "C"))
    assert out.talent == AI
    assert out.attributes["DEP"] == depth
    assert out.derived["metatype_info"]["attributes"]["DEP"]["min"] == depth
    assert {"DEP", "advanced programs"} <= set(out.derived["enabled_tabs"])
    assert not out.derived["errors"]


@pytest.mark.parametrize(
    ("method", "letter", "points"), [("Priority", "B", 10), ("SumToTen", "B", 10), ("Priority", "D", 7)]
)
def test_the_attribute_points_are_halved(method: str, letter: str, points: int) -> None:
    out = compute(_ai(method=method, attributes=letter))
    assert out.derived["points"]["attributes"]["max"] == points


def test_the_body_stays_at_zero() -> None:
    state = _ai()
    state.attributes = {**state.attributes, "BOD": 4, "AGI": 3}
    out = compute(state)
    assert all(out.derived["totals"][key] == 0 for key in ("BOD", "AGI", "REA", "STR"))
    assert out.derived["points"]["attributes"]["used"] == 0


def test_depth_above_the_talent_spends_special_points() -> None:
    state = _ai()
    state.attributes = {**state.attributes, "DEP": 5}
    out = compute(state)
    assert out.derived["totals"]["DEP"] == 5
    assert out.derived["points"]["special"] == {"used": 2, "max": 4}


def test_edge_is_capped_by_depth() -> None:
    state = _ai(talent_letter="D")
    state.attributes = {**state.attributes, "EDG": 6}
    out = compute(state)
    assert out.derived["metatype_info"]["attributes"]["EDG"]["max"] == 2
    assert out.derived["totals"]["EDG"] == 2


def test_an_e_ghosts_luck_raises_the_edge_cap_above_depth() -> None:
    out = compute(_ai("E-Ghost", talent_letter="D"))
    assert out.derived["metatype_info"]["attributes"]["EDG"]["max"] == 3


def test_a_karma_ai_starts_depth_at_one() -> None:
    out = compute(_ai(method="Karma"))
    assert out.attributes["DEP"] == 1
    breakdown = {row["notice"]["key"]: row["amount"] for row in out.derived["karma_spend_breakdown"]}
    assert breakdown["engine.spend.metatype"] == 180


def test_a_karma_ai_may_buy_no_talent() -> None:
    # A Karma build has no Talent priority: Mundane only means none was
    # bought, and the metatype still enables Depth.
    out = compute(_ai(method="Karma", talent="Mundane"))
    assert out.talent == "Mundane"
    assert out.attributes["DEP"] == 1
    assert not has(out.derived["errors"], "engine.priority.talentNotAllowed")


def test_a_new_karma_ai_takes_its_talent_rather_than_mundane() -> None:
    human = compute(_human(build_method="Karma"))
    ai = apply_patch(human, CharacterPatch(metatype=AI, metavariant=None))
    assert ai.talent == AI


def test_an_e_ghost_is_born_saying_hello_three_times() -> None:
    out = compute(_ai("E-Ghost"))
    names = [q["name"] for q in out.derived["qualities"] if q.get("origin") == "Metatype"]
    assert names.count("Hello World!") == 3
    assert not out.derived["errors"]


def test_a_gnome_is_born_with_arcane_arrester_twice() -> None:
    # The same rule as Hello World!: one quality per `<quality>` line.
    state = CharacterState(
        id="gnome",
        name="Gnome",
        metatype="Dwarf",
        metavariant="Gnome",
        priorities=Priorities(Heritage="A", Attributes="B", Talent="C", Skills="D", Resources="E"),
        attributes=default_attributes(find_metatype("Dwarf", "Gnome")),
    )
    out = compute(state)
    names = [q["name"] for q in out.derived["qualities"]]
    assert names.count("Arcane Arrester") == 2
    assert out.derived["spell_resistance"] == 4


# --- what an A.I. may not take ------------------------------------------------


def test_an_ai_may_not_take_a_magic_talent() -> None:
    out = compute(_ai(talent="Adept"))
    assert out.talent == "Adept"
    assert has(out.derived["errors"], "engine.priority.talentNotAllowed")


def test_a_human_may_not_take_the_ai_talent() -> None:
    out = compute(_human(talent=AI))
    assert has(out.derived["errors"], "engine.priority.talentNotAllowed")


def test_becoming_an_ai_switches_to_its_talent_and_back() -> None:
    human = compute(_human(talent="Adept"))
    ai = apply_patch(human, CharacterPatch(metatype=AI, metavariant=None))
    assert ai.talent == AI
    assert ai.attributes["DEP"] == 3
    assert not has(ai.derived["errors"], "engine.priority.talentNotAllowed")
    back = apply_patch(ai, CharacterPatch(metatype="Human", metavariant=None))
    assert back.talent != AI
    assert not has(back.derived["errors"], "engine.priority.talentNotAllowed")


def test_an_ai_may_take_only_the_qualities_on_its_list() -> None:
    allowed = compute(_ai(quality_ids=[_quality_id("Guts")]))
    assert not has(allowed.derived["errors"], "engine.qualities.forbidden")
    refused = compute(_ai(quality_ids=[_quality_id("Ambidextrous")]))
    assert has(refused.derived["errors"], "engine.qualities.forbidden")


def test_the_list_does_not_bind_a_metahuman() -> None:
    out = compute(_human(quality_ids=[_quality_id("Ambidextrous")]))
    assert not has(out.derived["errors"], "engine.qualities.forbidden")


def test_creation_offers_the_ai_and_its_talent() -> None:
    cat = public_catalog()
    offered = {m["name"]: m for m in cat["metatypes"]}
    assert {v["name"] for v in offered[AI]["metavariants"]} == set(VARIANTS)
    assert offered[AI]["quality_restriction"]["Positive"]
    heritage = cat["priority_table"]["Heritage"]
    for letter, cell in heritage.items():
        assert (AI in {m["name"] for m in cell["metatypes"]}) == (letter in "ABC")
    for cell in cat["priority_table"]["Talent"].values():
        rows = {t["name"]: t for t in cell["talents"]}
        assert rows[AI]["required"] == [{"kind": "metatype", "name": AI}]
    karma = {t["name"]: t for t in cat["karma_talents"]}
    assert AI in karma


# --- essence -----------------------------------------------------------------


def _ware_id(name: str) -> str:
    from tests.engine_support import _ware_id as ware_id

    return ware_id("cyberware", name)


def _wired(*names: str, **kwargs: object) -> CharacterState:
    from app.models import CyberwareInstall

    state = _ai("E-Ghost", talent_letter="A", attributes="B", **kwargs)
    state.cyberware = [CyberwareInstall(ware_id=_ware_id(name)) for name in names]
    return state


def test_essence_loss_takes_depth_as_it_takes_magic() -> None:
    # Chummer does not stop an A.I. buying ware; its Depth then falls with
    # essence the way MAG and RES do (`GetAllAttributeSpecificEssence`).
    # 1.1 essence gone costs two points: Depth 6 is 4, and so is Edge's cap.
    out = compute(_wired("Obvious Full Arm", "Datajack"))
    assert out.derived["essence"] == pytest.approx(4.9)
    assert out.attributes["DEP"] == 6
    assert out.derived["totals"]["DEP"] == 4
    assert out.derived["metatype_info"]["attributes"]["EDG"]["max"] == 4 + 1  # Lucky


def test_without_ware_depth_is_untouched() -> None:
    out = compute(_wired())
    assert out.derived["totals"]["DEP"] == 6


def test_the_maximum_only_rule_keeps_a_depth_under_the_new_maximum() -> None:
    from app.models import SettingsState

    state = _wired("Obvious Full Arm", settings=SettingsState(ess_loss_reduces_maximum_only=True))
    state.attributes = {**state.attributes, "DEP": 6}
    assert compute(state).derived["totals"]["DEP"] == 5


# --- .chum5 -------------------------------------------------------------------


def test_the_export_says_depth_is_enabled_and_where_it_starts() -> None:
    state = _ai("E-Ghost")
    state.attributes = {**state.attributes, "DEP": 5}
    root = ET.fromstring(state_to_chum5(compute(state)))
    assert root.findtext("metatypecategory") == "Metasapient"
    assert root.findtext("depenabled") == "True"
    dep = next(a for a in root.iter("attribute") if a.findtext("name") == "DEP")
    # The talent's Depth is Chummer's minimum; only the two above it are bought.
    assert (dep.findtext("metatypemin"), dep.findtext("base")) == ("3", "2")


def test_an_ai_is_a_fixed_point_of_export_and_import() -> None:
    state = _ai("Xenosapient")
    state.attributes = {**state.attributes, "DEP": 4, "LOG": 6}
    first = compute(state)
    again, _ = chum5_to_state(state_to_chum5(first))
    second = compute(CharacterState(**again))
    assert second.metatype == AI
    assert second.metavariant == "Xenosapient"
    assert second.talent == AI
    assert second.attributes["DEP"] == 4
    assert second.attributes["LOG"] == 6
    assert second.derived["points"] == first.derived["points"]


# --- monitors and initiative (no home node) -----------------------------------


def test_an_ai_has_a_core_track_and_no_stun_track() -> None:
    # Chummer `PhysicalCM`: 8 + DEP / 2, rounded up; `StunCM`: none at all
    out = compute(_ai("E-Ghost"))
    assert out.derived["totals"]["DEP"] == 3
    assert out.derived["condition_monitor"]["physical"] == 8 + 2
    assert out.derived["condition_monitor"]["stun"] == 0
    assert out.derived["condition_monitor"]["core"] is True


def test_a_metahuman_keeps_both_tracks() -> None:
    cm = compute(_human()).derived["condition_monitor"]
    assert cm["core"] is False
    assert cm["stun"] > 0


def test_an_ai_outside_a_vehicle_has_no_physical_limit() -> None:
    assert compute(_ai("E-Ghost")).derived["limits"]["physical"] == 0


def test_an_ai_rolls_four_matrix_initiative_dice_cold_or_hot() -> None:
    # Chummer `MatrixInitiativeValue` / `MatrixInitiativeDice` for an A.I.:
    # INT, and the hot-sim minimum whether it runs cold or hot
    out = compute(_ai("E-Ghost"))
    mi = out.derived["matrix_initiative"]
    assert mi["device"] == "ai"
    assert mi["value"] == out.derived["totals"]["INT"]
    assert (mi["cold_dice"], mi["hot_dice"]) == (4, 4)


def test_an_ais_matrix_dice_stop_at_the_initiative_maximum() -> None:
    from app.engine.gear import ai_matrix_initiative

    assert ai_matrix_initiative(3, extra_dice=3)["hot_dice"] == 5


# --- home node ------------------------------------------------------------------


def _deck(name: str = "Shiawase Cyber-5", state: CharacterState | None = None) -> CharacterState:
    from app.data_loader import catalog
    from app.models import GearInstall

    state = state or _ai("E-Ghost")
    spec = next(x for x in catalog()["cyberdecks"] if x["name"] == name)
    state.cyberdecks = [GearInstall(gear_id=spec["id"])]
    state.home_node = state.cyberdecks[0].id
    return state


def test_a_home_node_adds_its_data_processing_to_the_matrix_initiative() -> None:
    out = compute(_deck())
    mi = out.derived["matrix_initiative"]
    assert mi["dataprocessing"] == 6
    assert mi["value"] == out.derived["totals"]["INT"] + 6
    assert mi["hot_dice"] == 4


def test_a_home_node_sets_the_mental_and_social_limits() -> None:
    # Chummer `LimitMental`: the higher of the usual one and Data Processing;
    # `LimitSocial`: (CHA + DP + WIL + ESS) / 3 where a metahuman doubles CHA
    out = compute(_deck())
    totals = out.derived["totals"]
    assert out.derived["limits"]["mental"] == 6
    assert out.derived["limits"]["social"] == -(-(totals["CHA"] + 6 + totals["WIL"] + 6) // 3)


def test_a_home_nodes_matrix_monitor_stands_in_for_the_stun_one() -> None:
    cm = compute(_deck()).derived["condition_monitor"]
    assert cm["core"] is True
    assert cm["stun"] == 8 + 3  # Device Rating 5


def test_a_metahuman_drops_the_mark() -> None:
    state = _deck(state=_human())
    out = compute(state)
    assert out.home_node == ""
    assert out.derived["home_node"] is None


def test_a_sold_device_takes_the_mark_with_it() -> None:
    state = _deck()
    state.cyberdecks = []
    out = compute(state)
    assert out.home_node == ""
    assert out.derived["matrix_initiative"]["dataprocessing"] == 0


def test_a_node_below_the_program_limit_is_warned_of() -> None:
    # Chummer greys out the box unless Program Limit >= 2 when DEP is above
    # the Device Rating; Scratch-Built Junk (DR 1, one program) at DEP 3
    from app.data_loader import catalog
    from app.models import GearInstall

    state = _ai("E-Ghost")
    junk = next(x for x in catalog()["rccs"] if x["name"] == "Scratch-Built Junk")
    state.rccs = [GearInstall(gear_id=junk["id"])]
    state.home_node = state.rccs[0].id
    assert has(compute(state).derived["warnings"], "engine.homeNode.programLimit")
    assert not has(compute(_deck()).derived["warnings"], "engine.homeNode.programLimit")


def test_the_home_node_survives_a_round_trip() -> None:
    first = compute(_deck())
    xml = state_to_chum5(first)
    marked = [g.findtext("name") for g in ET.fromstring(xml).iter("gear") if g.findtext("homenode") == "True"]
    assert marked == ["Shiawase Cyber-5"]
    again, _ = chum5_to_state(xml)
    second = compute(CharacterState(**again))
    assert second.derived["home_node"]["name"] == "Shiawase Cyber-5"
    assert second.derived["limits"] == first.derived["limits"]


def test_the_patch_sets_and_clears_the_home_node() -> None:
    state = _deck()
    node = state.home_node
    cleared = apply_patch(state, CharacterPatch(home_node=""))
    assert cleared.home_node == ""
    again = apply_patch(cleared, CharacterPatch(home_node=node))
    assert again.home_node == node


# --- a vehicle or drone as home node -------------------------------------------


def _vehicle(bucket: str = "vehicles", name: str = "Dodge Scoot (Scooter)") -> CharacterState:
    from app.data_loader import catalog
    from app.models import GearInstall

    state = _ai("E-Ghost")
    spec = next(x for x in catalog()[bucket] if x["name"] == name)
    setattr(state, bucket, [GearInstall(gear_id=spec["id"])])
    state.home_node = getattr(state, bucket)[0].id
    return state


@pytest.mark.parametrize(
    ("bucket", "name", "boxes"),
    [
        ("vehicles", "Dodge Scoot (Scooter)", 12 + 2),  # Body 4
        ("drones", "Aztechnology Hedgehog (Minidrone)", 6 + 1),  # Body 1
    ],
)
def test_every_vehicle_row_has_its_damage_track(bucket: str, name: str, boxes: int) -> None:
    # Chummer `Vehicle.PhysicalCM`: 12, or 6 for a drone, + Body / 2 + mods
    out = compute(_vehicle(bucket, name))
    assert out.derived[bucket][0]["condition_monitor"] == boxes


def test_in_a_vehicle_the_ai_takes_its_track_handling_and_pilot() -> None:
    # Scooter: Body 4, Handling 4/3, Pilot 1, Sensor 1
    out = compute(_vehicle())
    d = out.derived
    assert d["condition_monitor"]["physical"] == 14
    assert d["condition_monitor"]["vehicle"] is True
    assert d["condition_monitor"]["stun"] == 8 + 1  # Device Rating = Pilot 1
    assert d["limits"]["physical"] == 4
    assert d["matrix_initiative"]["value"] == d["totals"]["INT"] + 1


def test_a_vehicles_sensor_joins_the_mental_limit() -> None:
    # Hedgehog: Pilot 4, Sensor 3 — the higher of the two and the usual one
    out = compute(_vehicle("drones", "Aztechnology Hedgehog (Minidrone)"))
    assert out.derived["limits"]["mental"] == 4


def test_a_vehicle_node_warns_of_the_persona_firmware() -> None:
    assert has(compute(_vehicle()).derived["warnings"], "engine.homeNode.personaFirmware")
    assert not has(compute(_deck()).derived["warnings"], "engine.homeNode.personaFirmware")


def test_a_vehicle_home_node_survives_a_round_trip() -> None:
    first = compute(_vehicle())
    xml = state_to_chum5(first)
    marked = [v.findtext("name") for v in ET.fromstring(xml).iter("vehicle") if v.findtext("homenode") == "True"]
    assert marked == ["Dodge Scoot (Scooter)"]
    again, _ = chum5_to_state(xml)
    second = compute(CharacterState(**again))
    assert second.derived["condition_monitor"] == first.derived["condition_monitor"]


# --- damage resistance ----------------------------------------------------------


def test_a_metahuman_soaks_with_body_and_armor() -> None:
    out = compute(_human())
    soak = out.derived["damage_resist"]
    assert soak["body"] == out.derived["totals"]["BOD"]
    assert soak["armor"] == out.derived["armor"]
    assert soak["pool"] == soak["body"] + soak["armor"] + soak["bonus"]


@pytest.mark.parametrize("state", ["bare", "deck"])
def test_an_ai_out_of_a_vehicle_soaks_with_no_body(state: str) -> None:
    # Chummer `DamageResistancePool`: an A.I.'s body is its vehicle node's or 0
    out = compute(_ai("E-Ghost") if state == "bare" else _deck())
    assert out.derived["damage_resist"]["body"] == 0


def test_an_ai_in_a_vehicle_soaks_with_its_body() -> None:
    out = compute(_vehicle())  # Dodge Scoot: Body 4
    soak = out.derived["damage_resist"]
    assert soak["body"] == 4
    assert soak["pool"] == 4 + soak["armor"] + soak["bonus"]


# --- spell defense ----------------------------------------------------------------


def test_a_metahumans_spell_defense_pools_are_chummers() -> None:
    out = compute(_human())
    t = out.derived["totals"]
    pools = out.derived["spell_defense_pools"]
    assert pools["direct_mana"] == t["WIL"]
    assert pools["direct_physical"] == t["BOD"]
    assert pools["detection"] == t["LOG"] + t["WIL"]
    assert pools["decrease"]["STR"] == t["STR"] + t["WIL"]
    assert pools["physical_illusion"] == t["LOG"] + t["INT"]
    assert pools["physical_manipulation"] == t["BOD"] + t["STR"]
    assert pools["indirect_soak"] == out.derived["damage_resist"]["pool"]


def test_an_ai_in_a_vehicle_defends_with_its_body_where_chummer_reads_bod_or_str() -> None:
    out = compute(_vehicle())  # Dodge Scoot: Body 4
    wil = out.derived["totals"]["WIL"]
    pools = out.derived["spell_defense_pools"]
    assert pools["direct_physical"] == 4
    assert pools["decrease"]["BOD"] == 4 + wil
    assert pools["decrease"]["STR"] == 4 + wil
    assert pools["physical_manipulation"] == 8  # TotalBody × 2
    assert pools["indirect_soak"] == out.derived["damage_resist"]["pool"]


def test_an_ai_without_a_vehicle_has_no_body_to_defend_with() -> None:
    pools = compute(_deck()).derived["spell_defense_pools"]
    assert pools["direct_physical"] == 0
    assert pools["physical_manipulation"] == 0


# --- career -------------------------------------------------------------------
#
# Chummer's CharacterCareer has nothing of its own for an A.I. beyond buying a
# program (`cmdAddAIProgram_Click`, at the same 5 / 8 as creation) and the home
# node box. Depth is raised like MAG and RES (`UpgradeKarmaCost`, from the value
# essence loss left), so the career rules every character has already cover it.


def _career_ai_dep_5() -> CharacterState:
    from app.engine import snapshot_career_baseline

    # Talent B: Depth starts at 4, and one raise takes it to 5
    state = compute(_ai("E-Ghost", talent_letter="B", attributes="C"))
    state.career = True
    state.career_baseline = snapshot_career_baseline(state)
    state.karma_earned = 100
    return compute(state)


def test_a_career_depth_raise_costs_its_new_rating_times_five() -> None:
    state = _career_ai_dep_5()
    assert state.attributes["DEP"] == 4
    state.attributes = {**state.attributes, "DEP": 5}
    out = compute(state)
    assert out.derived["totals"]["DEP"] == 5
    assert out.derived["career_advancement_karma"] == 25
    # and Edge's cap follows the raised Depth
    assert out.derived["metatype_info"]["attributes"]["EDG"]["max"] == 5 + 1  # Lucky


def test_a_career_depth_raise_is_priced_from_the_value_after_essence_loss() -> None:
    from app.models import CyberwareInstall

    state = _career_ai_dep_5()
    state.cyberware = [CyberwareInstall(ware_id=_ware_id("Datajack"))]
    state = compute(state)
    assert state.derived["totals"]["DEP"] == 3
    state.attributes = {**state.attributes, "DEP": 5}
    out = compute(state)
    # Depth 4 -> 5 stands at 3 -> 4: 4 x 5, not 5 x 5
    assert out.derived["totals"]["DEP"] == 4
    assert out.derived["career_advancement_karma"] == 20


def test_a_program_bought_in_career_costs_what_it_costs_in_creation() -> None:
    from app.data_loader import catalog
    from app.models import AIProgramInstall

    def program(name: str) -> AIProgramInstall:
        return AIProgramInstall(program_id=next(p["id"] for p in catalog()["ai_programs"] if p["name"] == name))

    state = _career_ai_dep_5()
    left = state.derived["karma"]["remaining"]
    state.ai_programs = [program("Exploit"), program("Authority")]
    out = compute(state)
    assert left - out.derived["karma"]["remaining"] == 5 + 8
    assert not has(out.derived["errors"], "engine.aiPrograms.prereq")


def test_a_career_ai_keeps_its_balance_through_the_chum5() -> None:
    state = _career_ai_dep_5()
    state.attributes = {**state.attributes, "DEP": 5}
    first = compute(state)
    again, _ = chum5_to_state(state_to_chum5(first))
    second = compute(CharacterState(**again))
    assert second.career is True
    assert second.attributes["DEP"] == 5
    assert second.derived["karma"]["remaining"] == first.derived["karma"]["remaining"]
