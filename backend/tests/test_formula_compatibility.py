"""Expression shapes used by Chummer's vendored data.

These are copied from the current Chummer XML rather than invented grammar
examples. A syntax change in the evaluator must keep these working or update
the matching data compatibility deliberately.
"""

from __future__ import annotations

import pytest

from app.data_loader import eval_formula, parse_avail
from app.engine.formulas import _eval_attr_stat
from app.engine.gear.ammo import _weapon_details_match


@pytest.mark.parametrize(
    ("expression", "rating", "extras", "expected"),
    [
        # vehicles.xml: <cost>Rating * 300</cost>
        pytest.param("Rating * 300", 3, {}, 900.0, id="rating-times-constant"),
        # vehicles.xml: Body == 0 and Body > 12, with a parenthesized term.
        pytest.param(
            "number(Body = 0) * 1500 + Body * 3000 + (Body * 1000)*number(Body > 12)",
            1,
            {"Body": 13},
            52000.0,
            id="number-comparisons-and-parentheses",
        ),
        # vehicles.xml: FixedValues containing number(), repeated variables,
        # multiplication and a rating-selected branch.
        pytest.param(
            "FixedValues(number(Body = 0) * 25 + Body * Body * 100,number(Body = 0) * 125 + Body * Body * 500)",
            2,
            {"Body": 2},
            2000.0,
            id="fixed-values-with-formulas",
        ),
        # lifestyles.xml: monthly DocWagon contract price.
        pytest.param("5000 div 12", 1, {}, 5000 / 12, id="xpath-div"),
    ],
)
def test_vendored_catalog_formula_shapes(
    expression: str,
    rating: int,
    extras: dict[str, int | float],
    expected: float,
) -> None:
    assert eval_formula(expression, rating, extras=extras) == pytest.approx(expected)


@pytest.mark.parametrize(
    "expression",
    [
        "9**9**9",
        "number(9**9**9 > 0)",
        "1e101",
        " + ".join(["1"] * 70),
        "1" * 513,
    ],
    ids=["power-operator", "power-inside-number", "number-out-of-range", "too-many-ast-nodes", "expression-too-long"],
)
def test_catalog_evaluator_refuses_unbounded_expression_shapes(expression: str) -> None:
    assert eval_formula(expression, default=7) == 7


def test_vendored_availability_suffix_and_rating_formula() -> None:
    # vehicles.xml uses both FixedValues(...R) and a Rating expression with an
    # availability suffix; availability parsing must keep the suffix separate.
    assert parse_avail("FixedValues(2,4,8,12R)", 4) == (12, "R", False)
    assert parse_avail("(Rating * 5)R", 2) == (10, "R", False)


def test_vendored_attribute_stat_shape() -> None:
    # critterpowers.xml and metatypes.xml carry damage such as `({STR}+1)P`;
    # weapons also use `number({STR} >= 5)` threshold terms.
    assert _eval_attr_stat("({STR}+1)P", {"STR": 5}) == "6P"
    assert _eval_attr_stat("3+number({STR} >= 5)+number({STR} >= 7)", {"STR": 7}) == "5"


def test_attribute_stat_does_not_evaluate_power_expressions() -> None:
    expression = "({STR}**1000000000)P"
    assert _eval_attr_stat(expression, {"STR": 5}) == "(5**1000000000)P"


@pytest.mark.parametrize(
    ("expression", "weapon", "expected"),
    [
        # gear.xml: `(contains(ammo, '(c)') or contains(ammo, '(d)')) and name != 'HK Urban Fighter'`
        pytest.param(
            "(contains(ammo, '(c)') or contains(ammo, '(d)')) and name != 'HK Urban Fighter'",
            {"ammo": "regular (c)", "name": "Ares Predator"},
            True,
            id="contains-and-name-not-equal",
        ),
        pytest.param(
            "(contains(ammo, '(c)') or contains(ammo, '(d)')) and name != 'HK Urban Fighter'",
            {"ammo": "regular (c)", "name": "HK Urban Fighter"},
            False,
            id="name-exclusion",
        ),
        # gear.xml also uses the simpler `contains(ammo, '(cy)')` form.
        pytest.param(
            "contains(ammo, '(cy)')",
            {"ammo": "regular (cy)", "name": "Test weapon"},
            True,
            id="contains-only",
        ),
        pytest.param(
            "__import__('os').system('false')",
            {"ammo": "regular (cy)", "name": "Test weapon"},
            False,
            id="unsupported-expression",
        ),
    ],
)
def test_vendored_weapon_details_shapes(expression: str, weapon: dict[str, str], expected: bool) -> None:
    assert _weapon_details_match(weapon, expression) is expected
