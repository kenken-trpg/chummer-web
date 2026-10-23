"""Hostile expressions at the bounded evaluators.

Formulas come from Chummer XML and from custom data a visitor uploads, and
every caller catches `UnsafeExpression` and nothing else. So the property
worth holding is: whatever the text, `evaluate_arithmetic` returns a number
within `MAX_ABS_NUMBER` (or a comparison's bool) or raises `UnsafeExpression`;
`evaluate_boolean` returns a bool or raises the same.
"""

from __future__ import annotations

import ast
import warnings

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from app.safe_eval import MAX_ABS_NUMBER, UnsafeExpression, evaluate_arithmetic, evaluate_boolean

_LEAVES = st.sampled_from(["1", "0", "9" * 400, "1e308", "1e99", "1e-320", "True", "x", "int(3.9)", '"\\,"'])

_EXPRESSIONS = st.recursive(
    _LEAVES,
    lambda inner: st.one_of(
        st.builds(lambda a, op, b: f"({a}{op}{b})", inner, st.sampled_from("+-*/%"), inner),
        st.builds(lambda sign, a: sign + a, st.sampled_from(["-", "+", "-" * 300]), inner),
        st.builds(lambda a: f"int({a})", inner),
        st.builds(lambda parts: "<".join(parts), st.lists(inner, min_size=2, max_size=6)),
        st.builds(lambda n, a: "(" * n + a + ")" * n, st.integers(1, 300), inner),
    ),
    max_leaves=60,
)

_OPTIONS = st.sampled_from(
    [
        {},
        {"allow_comparisons": True, "allow_int": True},
        {"allowed_ops": {ast.Add, ast.Sub, ast.Mult, ast.Div}},
        {"allowed_ops": {ast.Pow, ast.FloorDiv, ast.LShift}},
    ]
)


@settings(max_examples=300, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(st.one_of(_EXPRESSIONS, st.text(max_size=600)), _OPTIONS)
def test_arithmetic_returns_a_bounded_number_or_refuses(expression, options):
    try:
        result = evaluate_arithmetic(expression, **options)
    except UnsafeExpression:
        return
    assert isinstance(result, bool) or abs(result) <= MAX_ABS_NUMBER


@settings(max_examples=200, deadline=None)
@given(st.text(alphabet="TrueFalsandor() 1", max_size=600))
def test_boolean_returns_a_bool_or_refuses(expression):
    try:
        assert isinstance(evaluate_boolean(expression), bool)
    except UnsafeExpression:
        pass  # refusing is the other allowed outcome; what must not happen is anything else


@pytest.mark.parametrize("expression", ["2**3", "7//2", "1<<4"])
def test_an_operator_outside_the_table_is_refused_even_when_allowed(expression):
    """It used to fall through to `%`: `2**3` came out as 2."""
    with pytest.raises(UnsafeExpression):
        evaluate_arithmetic(expression, allowed_ops={ast.Pow, ast.FloorDiv, ast.LShift})


def test_parsing_writes_no_warning():
    """An invalid escape in a string literal makes the parser warn; uploaded
    data must not be able to write to the server log."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with pytest.raises(UnsafeExpression):
            evaluate_arithmetic('"\\,"')
    assert caught == []
