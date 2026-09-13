"""Technomancers: complex forms, streams, sprites, submersion and echoes."""

from app.data_loader import catalog
from app.engine import (
    compute,
    default_attributes,
    find_metatype,
    spell_drain_value,
)
from app.models import (
    CharacterState,
    ComplexFormInstall,
    CyberwareInstall,
    Priorities,
    SettingsState,
    SpriteInstall,
    SubmersionChoice,
)
from tests.engine_support import (
    CLEANER,
    COURIER_SPRITE,
    DATAJACK,
    EDITOR,
    _career_quality,
    _techno,
)
from tests.notice_asserts import has


def test_technomancer_does_not_charge_resonance_baseline() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    state = CharacterState(
        id="techno",
        name="Techno",
        priorities=Priorities(Heritage="C", Attributes="B", Talent="C", Skills="A", Resources="E"),
        metatype="Human",
        talent="Technomancer",
        attributes=attrs,
    )
    out = compute(state)
    assert out.derived["totals"]["RES"] == 3
    assert out.derived["totals"]["MAG"] == 0
    assert out.derived["points"]["special"]["used"] == 0
    assert "RES" in out.derived["enabled_tabs"]
    assert "complexforms" in out.derived["enabled_tabs"]
    assert "sprites" in out.derived["enabled_tabs"]
    assert out.derived["complex_form_points"]["free"] == 3
    assert out.derived["living_persona"]["device_rating"] == 3
    assert out.derived["fade_resist"]["attrs"] == "WIL+RES"


DIFFUSION = "33e75cd6-cad7-43dd-87ac-9838c83eccb5"
OVERDRIVE = "60b3f99f-f903-426a-ae13-ea604e77a956"
PULSE_STORM = "d8b11a80-eb95-409e-a53b-18c48e09342e"
STATIC_VEIL = "dbb1d719-c829-4c45-9a53-9ff538865c14"
RESONANCE_SPIKE = "704abd70-c0e6-4f06-b186-53a7cb856584"
RESONANT_STREAM_MACHINIST = "e3d04705-b90a-4d94-90d0-4ad2c7adfa79"
RESONANT_STREAM_SOURCEROR = "11d6c3b6-47c4-4765-a625-7a5907ba1b4a"
RESONANT_STREAM_CYBERADEPT = "d2873478-d265-45bb-8a9f-320b8d0d33d3"
SOURCERER_DAEMON = "08848a07-a013-4c45-b103-f5600f1e7171"
OTAKU_TO_TECHNOMANCER = "d62880dd-3e28-4b0c-8c71-dc0e4b72397b"


PARAGON = "c5311ee0-8a9b-41b9-857f-28541090968a"  # the quality, KC p.102
DELPHI = "c45c123c-06c7-42b3-a2ee-01e37f2f7bf8"
SHOOTER = "de755412-5cae-4859-880f-75a7bd68d5a4"


def test_a_paragon_is_the_technomancers_mentor_spirit() -> None:
    """Delphi trades initiative for Threading (KC p.103). It reaches the
    character through the mentor machinery, off `paragons.xml`."""
    base = compute(_techno("no-paragon"))
    out = compute(_techno("delphi", quality_ids=[PARAGON], mentor_id=DELPHI))

    assert out.derived["needs_paragon"] is True
    assert out.derived["needs_mentor"] is False
    assert out.derived["mentor"]["name"] == "Delphi (The Oracle)"
    assert out.derived["initiative"]["value"] == base.derived["initiative"]["value"] - 2
    threading = [row for row in out.derived["action_dice_pools"] if row["name"] == "Threading"]
    assert [row["bonus"] for row in threading] == [1]


def test_delphi_gives_up_matrix_initiative_as_well() -> None:
    """`<matrixinitiative>` moves the VR score itself, not the dice — the one
    tag in the file that the initiative-dice handler does not cover."""
    base = compute(_techno("no-paragon"))
    out = compute(_techno("delphi-vr", quality_ids=[PARAGON], mentor_id=DELPHI))

    assert out.derived["matrix_initiative"]["value"] == base.derived["matrix_initiative"]["value"] - 2
    assert out.derived["matrix_initiative"]["cold_dice"] == base.derived["matrix_initiative"]["cold_dice"]


def test_a_paragon_gives_and_takes_dice() -> None:
    """Shooter is +1 Cybercombat and -2 Compiling (KC p.104)."""
    out = compute(
        _techno("shooter", quality_ids=[PARAGON], mentor_id=SHOOTER, skills={"Cybercombat": 3, "Compiling": 3})
    )
    assert out.derived["skill_bonus"]["Cybercombat"] == 1
    assert out.derived["skill_bonus"]["Compiling"] == -2


def test_the_paragon_quality_asks_for_a_pick() -> None:
    out = compute(_techno("unpicked", quality_ids=[PARAGON]))
    assert out.derived["needs_paragon"] is True
    assert out.derived["mentor"] is None
    assert has(out.derived["warnings"], "engine.qualities.paragonMissing")


def test_no_paragon_bonus_is_left_unimplemented() -> None:
    """All nine, so a data bump that adds a tag we do not read shows up here."""
    for spec in catalog()["paragons"]:
        out = compute(_techno(f"p-{spec['id'][:8]}", quality_ids=[PARAGON], mentor_id=spec["id"]))
        assert out.derived["unimplemented_bonuses"] == [], spec["name"]


def test_complex_form_fade_formula() -> None:
    assert spell_drain_value("L-2", 3) == 2
    assert spell_drain_value("L+1", 3) == 4
    assert spell_drain_value("L-3", 3) == 2


def test_technomancer_a_gets_seven_free_complex_forms() -> None:
    out = compute(
        _techno(
            "cf-free",
            "A",
            complex_forms=[
                ComplexFormInstall(form_id=CLEANER),
                ComplexFormInstall(form_id=EDITOR),
                ComplexFormInstall(form_id=STATIC_VEIL),
            ],
        )
    )
    assert out.derived["complex_form_points"]["free"] == 7
    assert out.derived["complex_form_points"]["used"] == 3
    assert out.derived["complex_form_points"]["paid"] == 0
    assert all(row["karma"] == 0 for row in out.derived["complex_forms"])
    assert out.derived["karma"]["remaining"] == 25
    cleaner = next(row for row in out.derived["complex_forms"] if row["name"] == "Cleaner")
    assert cleaner["level"] == 6
    assert cleaner["fade"] == 4
    assert cleaner["fade_code"] == "S"


def test_eighth_complex_form_costs_karma() -> None:
    ids = [
        CLEANER,
        EDITOR,
        STATIC_VEIL,
        PULSE_STORM,
        RESONANCE_SPIKE,
        DIFFUSION,
        "cfebf27d-707e-4ea2-a376-394738a11b3c",
        "42cc98b0-2b3f-42a0-bbe7-fb7d2633d11a",
    ]
    forms = [ComplexFormInstall(form_id=fid, extra="Attack" if fid == DIFFUSION else None) for fid in ids]
    out = compute(_techno("cf-paid", "A", complex_forms=forms))
    assert out.derived["complex_form_points"]["used"] == 8
    assert out.derived["complex_form_points"]["paid"] == 1
    assert out.derived["complex_forms"][-1]["karma"] == 4
    assert out.derived["karma"]["spent"] == 4


def test_duplicate_complex_form_is_dropped() -> None:
    out = compute(
        _techno(
            "cf-dup",
            complex_forms=[ComplexFormInstall(form_id=CLEANER), ComplexFormInstall(form_id=CLEANER)],
        )
    )
    assert len(out.derived["complex_forms"]) == 1
    assert has(out.derived["warnings"], "engine.complexforms.duplicateDropped")


def test_diffusion_needs_matrix_attribute() -> None:
    out = compute(_techno("diff-none", complex_forms=[ComplexFormInstall(form_id=DIFFUSION)]))
    row = out.derived["complex_forms"][0]
    assert row["needs_extra"] is True
    assert has(out.derived["warnings"], "engine.complexforms.pickMatrixAttribute")
    out = compute(_techno("diff-atk", complex_forms=[ComplexFormInstall(form_id=DIFFUSION, extra="Attack")]))
    assert out.derived["complex_forms"][0]["extra"] == "Attack"
    assert out.derived["complex_forms"][0]["label"] == "Diffusion of Attack"
    assert not has(out.derived["warnings"], "engine.complexforms.pickMatrixAttribute")


def test_overdrive_requires_stream_quality() -> None:
    out = compute(_techno("overdrive", complex_forms=[ComplexFormInstall(form_id=OVERDRIVE)]))
    assert out.derived["complex_forms"] == []
    assert has(out.derived["warnings"], "engine.complexforms.requires", needed=["Resonant Stream: Cyberadept"])


def test_resonant_stream_machinist_reduces_specific_complex_form_fade() -> None:
    base = compute(
        _techno(
            "mach-base",
            complex_forms=[ComplexFormInstall(form_id=DIFFUSION, extra="Attack")],
        )
    )
    out = compute(
        _techno(
            "mach",
            quality_ids=[RESONANT_STREAM_MACHINIST],
            complex_forms=[ComplexFormInstall(form_id=DIFFUSION, extra="Attack")],
        )
    )
    assert base.derived["complex_forms"][0]["fade"] == 4
    row = out.derived["complex_forms"][0]
    assert row["fade_mod"] == -2
    assert row["fade"] == 2
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "fadingvalue" not in tags


def test_resonant_stream_sourceror_reduces_all_complex_form_fade() -> None:
    base = compute(_techno("sour-base", complex_forms=[ComplexFormInstall(form_id=CLEANER)]))
    out = compute(
        _techno(
            "sour",
            quality_ids=[RESONANT_STREAM_SOURCEROR],
            complex_forms=[ComplexFormInstall(form_id=CLEANER)],
        )
    )
    assert base.derived["complex_forms"][0]["fade"] == 4
    row = out.derived["complex_forms"][0]
    assert row["fade_mod"] == -2
    assert row["fade"] == 2


def test_otaku_to_technomancer_fading_resist() -> None:
    base = compute(_techno("otaku-base"))
    out = compute(_techno("otaku", quality_ids=[OTAKU_TO_TECHNOMANCER]))
    assert base.derived["fade_resist"]["pool"] == 7
    assert out.derived["fade_resist"]["pool"] == 9
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "fadingresist" not in tags


def test_sourceror_grants_sourcerer_daemon_echo() -> None:
    out = compute(_techno("sour-daemon", quality_ids=[RESONANT_STREAM_SOURCEROR]))
    echo = next(row for row in out.derived["submersion"]["echoes"] if row["name"] == "Sourcerer Daemon")
    assert echo["echo_id"] == SOURCERER_DAEMON
    assert echo["granted"] is True
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "addecho" not in tags


def test_cyberadept_daemon_reduces_res_essence_penalty() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    attrs["RES"] = 6
    common = {
        "attributes": attrs,
        "cyberware": [CyberwareInstall(ware_id=DATAJACK)],
        "submersion_grade": 2,
        "submersions": [
            SubmersionChoice(grade=1, echo_id=OVERCLOCKING),
            SubmersionChoice(grade=2, echo_id=OVERCLOCKING),
        ],
    }
    base = compute(_techno("ca-base", "A", **common))
    out = compute(_techno("ca", "A", quality_ids=[RESONANT_STREAM_CYBERADEPT], **common))
    assert base.attributes["RES"] == 5
    assert out.attributes["RES"] == 6
    tags = [item["tag"] for item in out.derived["unimplemented_bonuses"]]
    assert "cyberadeptdaemon" not in tags


def test_courier_sprite_matrix_stats() -> None:
    out = compute(
        _techno(
            "courier",
            "A",
            sprites=[SpriteInstall(sprite_id=COURIER_SPRITE, level=3, services=2, registered=True)],
        )
    )
    row = out.derived["sprites"][0]
    assert row["name"] == "Courier Sprite"
    assert row["level"] == 3
    assert row["services"] == 2
    assert row["registered"] is True
    assert row["matrix"]["attack"] == 3
    assert row["matrix"]["sleaze"] == 6
    assert row["matrix"]["dataprocessing"] == 4
    assert row["matrix"]["firewall"] == 5
    assert row["matrix"]["initiative"] == 7
    assert [p["name"] for p in row["powers"] if p["name"] == "Cookie"] == ["Cookie"]
    assert out.derived["errors"] == []


def test_registered_sprite_clamps_to_resonance() -> None:
    out = compute(_techno("sprite-cap", "C", sprites=[SpriteInstall(sprite_id=COURIER_SPRITE, level=12, services=9)]))
    row = out.derived["sprites"][0]
    assert row["level"] == 3
    assert row["services"] == 3


def test_compiled_sprite_can_exceed_resonance() -> None:
    out = compute(
        _techno(
            "compile-over",
            "C",
            sprites=[SpriteInstall(sprite_id=COURIER_SPRITE, level=6, registered=False, hits=4, opposed_hits=1)],
        )
    )
    row = out.derived["sprites"][0]
    assert row["level"] == 6
    assert row["services"] == 3
    assert row["registered"] is False
    assert row["test"]["physical"] is True


def test_too_many_registered_sprites() -> None:
    sprites = [SpriteInstall(sprite_id=COURIER_SPRITE, level=1, registered=True) for _ in range(4)]
    out = compute(_techno("too-many", "C", sprites=sprites))
    assert has(out.derived["errors"], "engine.sprites.registeredOverLimit", attr="CHA", count=4, max=1)


def test_registered_sprites_are_capped_by_charisma_not_resonance() -> None:
    """Chummer's Standard `<registeredspriteexpression>` is `{CHA}`."""

    def run(cid: str, cha: int, settings: SettingsState | None = None) -> list:
        state = _techno(
            cid, "A", sprites=[SpriteInstall(sprite_id=COURIER_SPRITE, level=1, registered=True) for _ in range(2)]
        )
        state.attributes["CHA"] = cha
        state.attributes["LOG"] = 2
        if settings is not None:
            state.settings = settings
        out = compute(state)
        assert out.derived["totals"]["RES"] >= 2
        return out.derived["errors"]

    assert has(run("cha1", 1), "engine.sprites.registeredOverLimit", max=1)
    assert not has(run("cha2", 2), "engine.sprites.registeredOverLimit")
    # the German presets cap them by LOG instead
    assert not has(run("log", 1, SettingsState(registered_sprite_attr="LOG")), "engine.sprites.registeredOverLimit")


def test_mage_has_no_technomancer_tabs() -> None:
    out = compute(
        CharacterState(
            id="mage-no-techno",
            name="mage",
            priorities=Priorities(Heritage="C", Attributes="B", Talent="A", Skills="D", Resources="E"),
            metatype="Human",
            talent="Magician",
            attributes=default_attributes(find_metatype("Human", None)),
        )
    )
    assert "complexforms" not in out.derived["enabled_tabs"]
    assert "sprites" not in out.derived["enabled_tabs"]
    assert out.derived["living_persona"] is None


ATTACK_UPGRADE = "36aa9af4-5c04-40d9-ba09-31b401cc1ff0"
OVERCLOCKING = "61055141-71f5-400e-9e67-cef650ce4801"
RESONANCE_PROGRAM = "d5dbe3f7-8a44-466b-8d5d-db9f0c68ee6b"


def test_submersion_grade_one_costs_thirteen_karma() -> None:
    out = compute(
        _techno(
            "sub1",
            "A",
            submersion_grade=1,
            submersions=[SubmersionChoice(grade=1, echo_id=OVERCLOCKING)],
        )
    )
    assert "submersion" in out.derived["enabled_tabs"]
    assert out.derived["submersion"]["grade"] == 1
    assert out.derived["submersion"]["karma"] == 13
    assert out.derived["submersion"]["echoes"][0]["name"] == "Overclocking"
    assert out.derived["karma"]["spent"] == 13
    assert out.derived["living_persona"]["matrix_initiative_dice"] == 1


def test_submersion_raises_res_max_and_attack_upgrade() -> None:
    attrs = default_attributes(find_metatype("Human", None))
    attrs["RES"] = 7
    attrs["CHA"] = 3
    base = compute(_techno("sub-base", "A", attributes=dict(attrs)))
    out = compute(
        _techno(
            "sub-res",
            "A",
            attributes=attrs,
            submersion_grade=1,
            submersions=[SubmersionChoice(grade=1, echo_id=ATTACK_UPGRADE)],
        )
    )
    assert out.derived["metatype_info"]["attributes"]["RES"]["max"] == 7
    assert out.attributes["RES"] == 7
    assert out.derived["living_persona"]["attack"] == int(base.derived["living_persona"]["attack"]) + 1


def test_submersion_grade_above_res_errors() -> None:
    out = compute(_techno("sub-over", "C", submersion_grade=5))
    assert has(out.derived["errors"], "engine.submersion.gradeOverResonance")


def test_echo_max_takes_blocks_third_attack_upgrade() -> None:
    out = compute(
        _techno(
            "sub-dup",
            "A",
            submersion_grade=3,
            submersions=[
                SubmersionChoice(grade=1, echo_id=ATTACK_UPGRADE),
                SubmersionChoice(grade=2, echo_id=ATTACK_UPGRADE),
                SubmersionChoice(grade=3, echo_id=ATTACK_UPGRADE),
            ],
        )
    )
    assert len(out.derived["submersion"]["echoes"]) == 2
    assert has(out.derived["warnings"], "engine.submersion.maxTakes", max=2)


def test_resonance_program_echo_needs_extra() -> None:
    out = compute(
        _techno(
            "sub-prog",
            "A",
            submersion_grade=1,
            submersions=[SubmersionChoice(grade=1, echo_id=RESONANCE_PROGRAM)],
        )
    )
    assert has(out.derived["warnings"], "engine.submersion.pickEchoExtra")
    out2 = compute(
        _techno(
            "sub-prog2",
            "A",
            submersion_grade=1,
            submersions=[SubmersionChoice(grade=1, echo_id=RESONANCE_PROGRAM, extra="Browse")],
        )
    )
    assert out2.derived["submersion"]["echoes"][0]["extra"] == "Browse"
    assert not has(out2.derived["warnings"], "engine.select.target")


def test_sprite_affinity_picks_one_sprite_from_the_catalog() -> None:
    """`<selectsprite>` (KC p.97): Sprite Affinity names one sprite type — a
    required pick, offered from the sprites the character can compile."""
    spec = _career_quality("Sprite Affinity")
    sprites = [s["name"] for s in catalog()["sprites"]]
    assert (spec["needs_extra"], spec["extra_kind"], spec["select_options"]) == (True, "text", sprites)

    missing = compute(_techno("sa-none", quality_ids=[spec["id"]])).derived
    assert has(missing["errors"], "engine.qualities.pickExtra")
    picked = compute(_techno("sa-data", quality_ids=[spec["id"]], quality_extras={spec["id"]: "Data Sprite"})).derived
    assert not has(picked["errors"], "engine.qualities.pickExtra")
    assert not has(picked["errors"], "engine.qualities.extraInvalid")
    bogus = compute(_techno("sa-bogus", quality_ids=[spec["id"]], quality_extras={spec["id"]: "Fire Spirit"})).derived
    assert has(bogus["errors"], "engine.qualities.extraInvalid")
