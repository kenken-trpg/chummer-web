"""Per-phase contract tests for :mod:`app.engine.compute`.

``compute()`` is a straight-line pipeline of ``phase(ctx: Ctx) -> None``
calls (see ``docs/refactor-compute-phases-plan.md``).  ``test_snapshot.py``
freezes the *end* of that pipeline byte-for-byte; this module pins the
*seams*.  It drives the identical phase sequence by hand and, after each
phase, asserts the ``ctx`` slice that phase is responsible for is filled
in — so a phase that stops writing one of its outputs (or a ``Ctx`` field
that goes dead) fails here with the phase named, instead of showing up as
an opaque multi-key snapshot diff.

If you add / rename / reorder a phase in ``compute/__init__.py`` you must
mirror it in :data:`PHASES`; ``test_phase_sequence_matches_compute`` and
``test_manual_pipeline_matches_compute`` hold the two in lock-step.
"""

from __future__ import annotations

import copy
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from app.data_loader import catalog
from app.engine.compute import (
    Ctx,
    assemble,
    awakened,
    bootstrap,
    compute,
    economy,
    effects_and_binders,
    essence,
    finalize,
    gather,
    gear_phase,
    spells,
    totals,
    ware,
)
from tests.test_snapshot import CHARACTERS, _normalize, _scrub_ids

# The canonical phase order — mirrors ``compute()`` in
# ``app/engine/compute/__init__.py``.  Keep the two in sync.
PHASES: tuple[tuple[str, Callable[[Ctx], None]], ...] = (
    ("bootstrap", bootstrap),
    ("gather", gather),
    ("ware", ware),
    ("effects_and_binders", effects_and_binders),
    ("essence", essence),
    ("awakened", awakened),
    ("gear_phase", gear_phase),
    ("totals", totals),
    ("spells", spells),
    ("economy", economy),
    ("finalize", finalize),
    ("assemble", assemble),
)

CHAR_NAMES = sorted(CHARACTERS)
_PKG_DIR = Path(__file__).parents[1] / "app" / "engine" / "compute"
_PKG_SRC = "\n".join(p.read_text(encoding="utf-8") for p in sorted(_PKG_DIR.glob("*.py")))

_CHECKPOINTS: dict[str, dict[str, Ctx]] = {}


def _checkpoints(char: str) -> dict[str, Ctx]:
    """Run the phase pipeline for ``char`` once; return a deep copy of
    ``ctx`` captured immediately after each phase, keyed by phase name."""
    if char not in _CHECKPOINTS:
        ctx = Ctx(state=CHARACTERS[char](), data=catalog())
        snaps: dict[str, Ctx] = {}
        for name, fn in PHASES:
            fn(ctx)
            catalog_ref = ctx.data
            ctx.data = {}  # keep the huge, shared catalog out of the deepcopy
            try:
                snaps[name] = copy.deepcopy(ctx)
            finally:
                ctx.data = catalog_ref
        _CHECKPOINTS[char] = snaps
    return _CHECKPOINTS[char]


@pytest.fixture(params=CHAR_NAMES)
def cp(request: pytest.FixtureRequest) -> dict[str, Ctx]:
    """Phase-name -> post-phase ``ctx`` snapshot, one parametrization per fixture character."""
    return _checkpoints(str(request.param))


# --------------------------------------------------------------------------
# phase 1 — bootstrap
# --------------------------------------------------------------------------
def test_bootstrap_sets_meta_caps_and_flags(cp: dict[str, Ctx]) -> None:
    ctx = cp["bootstrap"]
    assert ctx.meta["name"] == "Human"
    assert {"BOD", "AGI", "REA", "STR", "WIL", "LOG", "INT", "CHA", "MAG", "RES", "ESS"} <= set(ctx.attrs_spec)
    assert ctx.skill_rating_cap == 6
    assert ctx.skill_group_cap == 6
    assert ctx.is_karma is False
    assert ctx.career is False
    assert isinstance(ctx.errors, list)
    assert isinstance(ctx.warnings, list)


# --------------------------------------------------------------------------
# phase 2 — gather (talent / qualities / mentor / sources seed)
# --------------------------------------------------------------------------
def test_gather_resolves_talent_and_quality_lists(cp: dict[str, Ctx]) -> None:
    ctx = cp["gather"]
    assert ctx.talent.get("name")
    assert isinstance(ctx.qualities, list)
    assert isinstance(ctx.free_quality_ids, list)
    assert isinstance(ctx.mentor, dict)
    # ``sources`` is seeded with the metatype bonus row, then one per quality.
    assert ctx.sources and ctx.sources[0][0] == ctx.meta["name"]
    assert len(ctx.sources) >= 1 + len(ctx.qualities)


# --------------------------------------------------------------------------
# phase 3 — ware
# --------------------------------------------------------------------------
def test_ware_resolves_installs(cp: dict[str, Ctx]) -> None:
    ctx = cp["ware"]
    assert isinstance(ctx.cyber_installed, list)
    assert isinstance(ctx.bio_installed, list)
    assert ctx.installed == ctx.cyber_installed + ctx.bio_installed
    assert isinstance(ctx.ware_attr_bonus, dict)


# --------------------------------------------------------------------------
# phase 4 — effects_and_binders
# --------------------------------------------------------------------------
def test_effects_and_binders_builds_effects_and_special_key(cp: dict[str, Ctx]) -> None:
    ctx = cp["effects_and_binders"]
    assert isinstance(ctx.effects, dict)
    assert isinstance(ctx.effects.get("attribute_bonus"), dict)
    assert "enabled_tabs" in ctx.effects
    assert isinstance(ctx.attr_max_bonus, dict)
    assert ctx.special_key in (None, "MAG", "RES")
    assert isinstance(ctx.talent_start, int) and ctx.talent_start >= 0
    assert isinstance(ctx.enabled, set)
    if ctx.special_key:
        assert ctx.special_key in ctx.enabled


# --------------------------------------------------------------------------
# phase 5 + 6 — essence (penalty) + the ratings loop
# --------------------------------------------------------------------------
def test_essence_and_ratings(cp: dict[str, Ctx]) -> None:
    ctx = cp["essence"]
    assert isinstance(ctx.ess, float)
    assert 0.0 < ctx.ess <= 6.0
    assert ctx.ess_lost == pytest.approx(round(ctx.ess_lost_cyber + ctx.ess_lost_bio, 4))
    assert {"BOD", "AGI", "REA", "STR", "WIL", "LOG", "INT", "CHA"} <= set(ctx.ratings)
    assert all(isinstance(v, int) for v in ctx.ratings.values())


# --------------------------------------------------------------------------
# phase 7 + 8 — awakened (initiation / submersion / foci / adept)
# --------------------------------------------------------------------------
def test_awakened_bundles(cp: dict[str, Ctx]) -> None:
    ctx = cp["awakened"]
    for bundle in (ctx.initiation, ctx.submersion, ctx.qi, ctx.foci, ctx.focus_limits, ctx.adept, ctx.enhancements):
        assert isinstance(bundle, dict)
    assert "spent" in ctx.adept  # totals() reads ctx.adept["spent"]
    assert isinstance(ctx.attr_totals, dict)
    assert ctx.quality_names == {q["name"] for q in ctx.qualities}


# --------------------------------------------------------------------------
# phase 9 — gear
# --------------------------------------------------------------------------
def test_gear_phase_bundle(cp: dict[str, Ctx]) -> None:
    ctx = cp["gear_phase"]
    assert isinstance(ctx.gear, dict)
    assert {"weapons", "armor_items", "recoil", "gear", "lifestyles"} <= set(ctx.gear)
    assert isinstance(ctx.active_drugs, list)
    assert isinstance(ctx.bmp_active, bool)


# --------------------------------------------------------------------------
# phase 10 — totals
# --------------------------------------------------------------------------
def test_totals_folds_attribute_bonus(cp: dict[str, Ctx]) -> None:
    ctx = cp["totals"]
    bonus = ctx.effects["attribute_bonus"]
    # STR / AGI are overwritten by the cyberlimb replace; ESS by ctx.ess.
    skip = {"ESS"} | ({"STR", "AGI"} if ctx.limb_replace else set())
    for key, base in ctx.ratings.items():
        if key in skip:
            continue
        assert ctx.total[key] == base + int(bonus.get(key, 0))
    assert ctx.total["ESS"] == ctx.ess
    assert isinstance(ctx.power_pool, float)
    assert isinstance(ctx.power_spent, float)
    assert ctx.power_spent <= ctx.power_pool + 1e-9


# --------------------------------------------------------------------------
# phase 11 — spells / spirits / resonance
# --------------------------------------------------------------------------
def test_spells_bundles(cp: dict[str, Ctx]) -> None:
    ctx = cp["spells"]
    for bundle in (ctx.magic, ctx.spirits, ctx.resonance, ctx.techno_sprites):
        assert isinstance(bundle, dict)


# --------------------------------------------------------------------------
# phases 12–15 — economy (points / skills / karma / social)
# --------------------------------------------------------------------------
def test_economy_points_skills_karma_social(cp: dict[str, Ctx]) -> None:
    ctx = cp["economy"]
    assert isinstance(ctx.nuyen, int)
    assert isinstance(ctx.nuyen_pool, int)
    assert isinstance(ctx.skill_totals, dict)
    assert isinstance(ctx.effective_skills, dict)
    assert "public" in ctx.knowledge
    assert "skill_bonus" in ctx.skill_mods
    assert isinstance(ctx.contacts, dict)
    assert isinstance(ctx.martial, dict)
    assert isinstance(ctx.karma_pool, int)
    assert isinstance(ctx.karma_left, int)


# --------------------------------------------------------------------------
# phases 16–18 — finalize (limits / CM / init / quality rules / validate)
# --------------------------------------------------------------------------
def test_finalize_derives_limits_cm_initiative_movement(cp: dict[str, Ctx]) -> None:
    ctx = cp["finalize"]
    assert ctx.physical_limit > 0
    assert ctx.mental_limit > 0
    assert ctx.social_limit > 0
    assert ctx.cm_phys >= 8
    assert ctx.cm_stun >= 8
    assert ctx.initiative > 0
    assert ctx.initiative_dice >= 1
    assert {"walk", "run", "sprint"} <= set(ctx.movement)
    assert isinstance(ctx.quality_report, dict)
    assert isinstance(ctx.negative_quality_karma, int)
    assert ctx.negative_quality_karma >= 0


# --------------------------------------------------------------------------
# phase 19 — assemble
# --------------------------------------------------------------------------
def test_assemble_writes_attributes_and_derived(cp: dict[str, Ctx]) -> None:
    ctx = cp["assemble"]
    assert ctx.state.attributes == ctx.ratings
    derived = ctx.state.derived
    assert isinstance(derived, dict)
    assert len(derived) > 100
    assert {"errors", "warnings", "totals", "limits", "initiative", "movement", "essence"} <= set(derived)
    assert derived["errors"] == []  # the fixture characters are legal builds


# --------------------------------------------------------------------------
# character-specific spot checks — a phase output that should differ by build
# --------------------------------------------------------------------------
def test_street_samurai_ware_eats_essence() -> None:
    cps = _checkpoints("street_samurai")
    assert {w["name"] for w in cps["ware"].cyber_installed}  # Wired Reflexes + Datajack
    assert cps["essence"].ess < 6.0
    assert cps["economy"].skill_totals["Automatics"] == 6


def test_hermetic_mage_has_magic_and_spells() -> None:
    cps = _checkpoints("hermetic_mage")
    assert cps["effects_and_binders"].special_key == "MAG"
    assert cps["essence"].ratings["MAG"] > 0
    assert len(cps["spells"].magic["public"]) == 2  # Manabolt + Heal


def test_adept_has_power_pool() -> None:
    cps = _checkpoints("adept")
    assert cps["effects_and_binders"].special_key == "MAG"
    assert cps["totals"].power_pool > 0
    assert cps["awakened"].adept["public"]


def test_technomancer_has_resonance_and_complex_forms() -> None:
    cps = _checkpoints("technomancer")
    assert cps["effects_and_binders"].special_key == "RES"
    assert cps["essence"].ratings["RES"] > 0
    assert len(cps["spells"].resonance["public"]) == 2  # Cleaner + Editor


# --------------------------------------------------------------------------
# consistency guards — keep PHASES and compute() in lock-step
# --------------------------------------------------------------------------
def test_phase_sequence_matches_compute() -> None:
    """The ``name(ctx)`` calls in ``compute()``'s body, in order, are exactly :data:`PHASES`."""
    src = (_PKG_DIR / "__init__.py").read_text(encoding="utf-8")
    body = src.split("def compute(", 1)[1]
    calls = re.findall(r"^ {4}(\w+)\(ctx\)$", body, re.MULTILINE)
    assert calls == [name for name, _ in PHASES]


@pytest.mark.parametrize("char", CHAR_NAMES)
def test_manual_pipeline_matches_compute(char: str) -> None:
    """Running the phases by hand produces the same ``derived`` as ``compute()`` —
    proves the sequence these tests assert against is the real one."""
    state = CHARACTERS[char]()
    reference = compute(copy.deepcopy(state)).derived

    ctx = Ctx(state=state, data=catalog())
    for _, fn in PHASES:
        fn(ctx)

    # The gear / accessory resolvers mint fresh uuids for generated rows on
    # every run, so scrub instance ids the way test_snapshot does before
    # comparing structure + values.
    got = _scrub_ids(_normalize(ctx.state.derived), {})
    want = _scrub_ids(_normalize(reference), {})
    assert got == want


def test_no_orphan_ctx_fields() -> None:
    """Every ``Ctx`` field is read or written by some phase module."""
    missing = [
        name for name in Ctx.__dataclass_fields__ if name not in ("state", "data") and f"ctx.{name}" not in _PKG_SRC
    ]
    assert not missing, f"Ctx fields defined but never used by any phase: {missing}"


def test_phase_functions_mutate_ctx_and_return_none() -> None:
    ctx = Ctx(state=CHARACTERS[CHAR_NAMES[0]](), data=catalog())
    for name, fn in PHASES:
        result: Any = fn(ctx)
        assert result is None, f"{name}(ctx) should mutate ctx in place and return None, got {result!r}"
