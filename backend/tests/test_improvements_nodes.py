"""Guard for the improvements/nodes/ domain split: every tag the pipeline
claims to implement must be handled by some domain module, even the ones no
character-level test exercises.
"""

import re
from pathlib import Path

import pytest

from app.improvements import EffectsDict, apply_bonus_nodes, empty_effects, substitute_rating
from app.improvements._common import IMPLEMENTED, _eval_int


def test_eval_int_does_bare_arithmetic_but_refuses_exponentiation() -> None:
    assert _eval_int("3*2") == 6
    assert _eval_int("(4+2)/3") == 2
    assert _eval_int("Rating*2", 0) == 0  # names never eval
    # "9**9**9" clears the digit/operator char class but would hang eval;
    # the "**" guard sends it to the plain-int path, which falls back.
    assert _eval_int("9**9**9", 7) == 7


def test_every_implemented_tag_has_a_handler() -> None:
    effects = empty_effects()
    nodes = [{"tag": tag} for tag in sorted(IMPLEMENTED)]
    apply_bonus_nodes(nodes, effects, "guard")
    unhandled = sorted({row["tag"] for row in effects["unimplemented"]})
    assert unhandled == [], f"IMPLEMENTED tags with no domain handler: {unhandled}"


def test_weaponcategorydice_accepts_both_upstream_shapes() -> None:
    # legacy: <weaponcategorydice><category><name>Bows</name><value>1</value></category>
    legacy = empty_effects()
    apply_bonus_nodes([{"tag": "weaponcategorydice", "nested": {"category": ["Bows", "1"]}}], legacy, "legacy")
    assert legacy["weapon_category_dice"] == [{"category": "Bows", "dice": 1, "source": "legacy"}]

    # current: <weaponcategorydice><name>Bows</name><bonus>1</bonus></weaponcategorydice>
    current = empty_effects()
    apply_bonus_nodes([{"tag": "weaponcategorydice", "fields": {"name": "Bows", "bonus": "1"}}], current, "current")
    assert current["weapon_category_dice"] == [{"category": "Bows", "dice": 1, "source": "current"}]


def test_bonus_int_evaluates_the_arithmetic_substitute_rating_leaves_behind() -> None:
    """Five vendored items carry an expression rather than a number.

    ``substitute_rating`` turns ``Rating*0.5`` into ``6*0.5``, which the old
    per-site ``_as_int`` could not parse and silently scored 0. Values are the
    ones in ``vendor/chummer/data`` as of Chummer 5.225.
    """

    def fold(tag: str, value: str, rating: int) -> EffectsDict:
        effects = empty_effects()
        apply_bonus_nodes(substitute_rating([{"tag": tag, "value": value}], rating), effects, "arith")
        return effects

    # Move-by-Wire System / Stirrup Interface (cyberware.xml)
    assert fold("skillwire", "Rating * 2", 3)["skillwires"] == 6
    # Bone Density Augmentation (bioware.xml)
    assert fold("unarmeddv", "Rating-1", 4)["unarmed_dv"] == 3
    # Striking Callus (bioware.xml)
    assert fold("unarmeddv", "Rating*0.5", 6)["unarmed_dv"] == 3
    # Grey Mana Tattoos (gear.xml) — t100 means hundredths of an Essence point
    assert fold("essencepenaltyt100", "-10*Rating", 2)["essence_penalty"] == pytest.approx(0.2)


def test_no_domain_module_reimplements_the_bonus_value_fallback() -> None:
    """``_bonus_int`` is the single way a bonus magnitude is read.

    The chain used to be pasted inline at 43 sites, which is how three of the
    five items above drifted onto the non-arithmetic ``_as_int``. Keep new
    handlers from starting a sixth copy.
    """
    magnitude_chain = re.compile(r'node\.get\("value"\)\s*or\s*fields\.get\("(?:val|bonus)"\)')
    offenders = [
        path.name
        for path in sorted((Path(__file__).resolve().parents[1] / "app/improvements/nodes").glob("*.py"))
        if magnitude_chain.search(path.read_text())
    ]
    assert offenders == [], f"inline fallback chain is back in: {offenders}"
