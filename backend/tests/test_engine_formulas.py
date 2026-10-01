"""The string arithmetic behind armor values, damage codes and Accuracy.

`app.engine.formulas` is where a stat that arrives as text gets a number
added to it. Its callers are the parts of the engine a player watches most
closely: `gear/armor.py` reads `<armor>` and `<armoroverride>` through
`parse_armor_value`, `gear/ammo.py` moves a round's AP and DV with
`_add_signed_stat` / `_set_damage_type`, `gear/weapons/bonuses.py` moves a
weapon's with `_add_weapon_dv` / `_add_accuracy`, and
`compute/_econ_skills.py` turns the settings file's knowledge-point
expression into a number with `eval_attribute_expression`.

Every one of them takes text Chummer's XML (or an uploaded settings file)
chose the spelling of, so what matters is not the happy `6P` but the shapes
that are not a leading integer at all: `Physical-1`, a bare `—`, `Special`,
`Rating * 2`, a division by zero. Those are tested here directly rather than
through `compute`, because each is one function of one string and routing a
character through the engine to reach it would hide which one answered.
"""

from __future__ import annotations

import pytest

from app.engine.formulas import (
    _add_accuracy,
    _add_leading_int,
    _add_signed_stat,
    _add_weapon_dv,
    _eval_attr_stat,
    _leading_int,
    _replace_leading_int,
    _set_damage_type,
    eval_attribute_expression,
    parse_armor_value,
)


class TestParseArmorValue:
    def test_the_word_rating_means_the_item_s_rating(self) -> None:
        assert parse_armor_value("Rating", 4) == (4, False)

    def test_a_formula_is_evaluated_against_the_rating(self) -> None:
        """`int(float(...))` raises on `Rating * 2`, so it falls through to
        `eval_formula` — the branch an Armor Jacket never takes."""
        assert parse_armor_value("Rating * 2", 3) == (6, False)

    def test_a_signed_number_is_additive_and_an_unsigned_one_is_not(self) -> None:
        assert parse_armor_value("+2") == (2, True)
        assert parse_armor_value("-1") == (-1, True)
        assert parse_armor_value("12") == (12, False)

    def test_an_empty_value_is_zero(self) -> None:
        assert parse_armor_value("") == (0, False)


class TestSignedStat:
    def test_no_delta_leaves_the_text_alone(self) -> None:
        assert _add_signed_stat("-2", 0) == "-2"

    @pytest.mark.parametrize("empty", ["", "-", "—"])
    def test_a_blank_or_dash_becomes_the_delta_itself(self, empty: str) -> None:
        """An AP of `-` is zero written as a dash; adding -1 to it must read
        `-1`, not `-1-`."""
        assert _add_signed_stat(empty, -1) == "-1"

    def test_a_word_is_left_alone(self) -> None:
        assert _add_signed_stat("Special", 2) == "Special"

    def test_a_leading_integer_moves_and_the_rest_stays(self) -> None:
        assert _add_signed_stat("-2", 1) == "-1"
        assert _add_signed_stat("6P", 2) == "8P"


class TestDamageType:
    def test_the_type_replaces_the_old_one_after_the_number(self) -> None:
        assert _set_damage_type("+2S", "P") == "+2P"

    def test_damage_with_no_number_becomes_the_type_alone(self) -> None:
        assert _set_damage_type("Special", "P") == "P"


class TestLeadingInt:
    def test_a_stat_with_no_leading_integer_has_none(self) -> None:
        assert _leading_int("Special") is None
        assert _leading_int(None) is None

    def test_the_sign_is_part_of_the_number(self) -> None:
        assert _leading_int("-2") == -2
        assert _leading_int("+1 AP") == 1

    def test_adding_to_something_with_no_number_changes_nothing(self) -> None:
        assert _add_leading_int("Physical", 1) == "Physical"
        assert _add_leading_int("6P", 0) == "6P"

    def test_replacing_keeps_the_tail_and_drops_it_when_there_is_no_number(self) -> None:
        assert _replace_leading_int("6P", 8) == "8P"
        assert _replace_leading_int("Special", 4) == "4"


class TestWeaponDamage:
    def test_no_delta_leaves_the_code_alone(self) -> None:
        assert _add_weapon_dv("6P", 0) == "6P"

    def test_the_number_nearest_the_end_is_the_one_that_moves(self) -> None:
        """`2(f)` style codes exist; the DV is the last number, not the first."""
        assert _add_weapon_dv("6P", 2) == "8P"
        assert _add_weapon_dv("10S(e)", 1) == "11S(e)"

    def test_a_signed_bonus_stays_signed_while_it_is_still_a_bonus(self) -> None:
        assert _add_weapon_dv("+1P", 1) == "+2P"

    def test_a_signed_bonus_driven_negative_loses_the_plus(self) -> None:
        assert _add_weapon_dv("+1P", -3) == "-2P"

    def test_a_code_that_is_only_a_damage_type_gains_the_delta_in_front(self) -> None:
        """A Shock Glove's `(STR+half)S` arrives type-first; the number goes
        before the type, not after it."""
        assert _add_weapon_dv("P", 2) == "+2P"
        assert _add_weapon_dv("S", -1) == "-1S"

    def test_a_code_with_neither_number_nor_type_gets_the_delta_appended(self) -> None:
        assert _add_weapon_dv("Chemical", 2) == "Chemical+2"
        assert _add_weapon_dv("Chemical", -2) == "Chemical-2"


class TestAccuracy:
    def test_a_limit_based_accuracy_keeps_the_word_and_moves_the_offset(self) -> None:
        """A Raptor Foot is `Physical-1`: the limit is resolved nowhere, so the
        word has to survive while the offset moves."""
        assert _add_accuracy("Physical", 2) == "Physical+2"
        assert _add_accuracy("Physical+1", -1) == "Physical"
        assert _add_accuracy("Physical-1", 1) == "Physical"
        assert _add_accuracy("Physical - 1", -1) == "Physical-2"

    def test_a_numeric_accuracy_behaves_like_any_leading_integer(self) -> None:
        assert _add_accuracy("5", 1) == "6"
        assert _add_accuracy("Physical", 0) == "Physical"


class TestAttrStat:
    ATTRS = {"STR": 5, "AGI": 3, "MAG": 6}

    def test_text_with_no_token_is_returned_untouched(self) -> None:
        assert _eval_attr_stat("6P", self.ATTRS) == "6P"

    def test_a_token_becomes_the_attribute_and_the_arithmetic_is_folded(self) -> None:
        assert _eval_attr_stat("{STR}P", self.ATTRS) == "5P"
        assert _eval_attr_stat("({STR}/2)P", self.ATTRS) == "2P"

    def test_chummer_s_number_test_counts_each_threshold_met(self) -> None:
        """An Osmium Mace is `3+number({STR} >= 5)+number({STR} >= 7)`
        (TCT p.185): at STR 5 one test holds, so the DV is 4."""
        assert _eval_attr_stat("3+number({STR} >= 5)+number({STR} >= 7)", self.ATTRS) == "4"
        assert _eval_attr_stat("3+number({STR} >= 5)+number({STR} >= 7)", {"STR": 7}) == "5"

    def test_a_token_this_module_does_not_know_leaves_the_text_as_it_was(self) -> None:
        """Only STR / AGI / MAG are substituted. A `{BOD}` would otherwise be
        handed to the evaluator with the brace still in it."""
        assert _eval_attr_stat("{BOD}+2", self.ATTRS) == "{BOD}+2"

    def test_an_attribute_the_character_has_no_value_for_reads_as_zero(self) -> None:
        assert _eval_attr_stat("{MAG}", {}) == "0"

    def test_a_division_by_zero_comes_back_as_text_rather_than_raising(self) -> None:
        """This runs while a weapon row is being built, so a formula that
        cannot be folded has to survive as the string it already was."""
        assert _eval_attr_stat("({MAG}/0)P", self.ATTRS) == "(6/0)P"

    def test_a_sum_the_damage_type_is_glued_to_is_left_half_folded(self) -> None:
        """`{STR}+2P` has a sum at the top level but is not arithmetic — the
        trailing `P` is the damage type. The tokens are substituted and the sum
        is left as written rather than being mangled into a number."""
        assert _eval_attr_stat("{STR}+2P", self.ATTRS) == "5+2P"
        assert _eval_attr_stat("{STR}+{AGI}P", self.ATTRS) == "5+3P"

    def test_a_leftover_word_inside_brackets_stops_the_fold(self) -> None:
        assert _eval_attr_stat("({STR}+X)", self.ATTRS) == "(5+X)"


class TestSettingsExpression:
    def test_the_default_shape_of_a_knowledge_point_expression(self) -> None:
        assert eval_attribute_expression("({INTUnaug} + {LOGUnaug}) * 2", {"INTUnaug": 3.0, "LOGUnaug": 4.0}) == 14.0

    def test_xpath_s_div_is_accepted_as_division(self) -> None:
        assert eval_attribute_expression("{INT} div 2", {"INT": 5.0}) == 2.5

    def test_a_sign_in_front_of_a_term_is_honoured(self) -> None:
        assert eval_attribute_expression("-{INT} + +2", {"INT": 3.0}) == -1.0

    @pytest.mark.parametrize(
        "expr",
        ["{XYZ}", "{INT} +", "{INT} div 0", "{INT} ** 2", "__import__('os')", "True"],
        ids=[
            "unknown-attribute",
            "not-an-expression",
            "divides-by-zero",
            "operator-the-walker-refuses",
            "not-arithmetic-at-all",
            "a-bool-is-an-int-but-not-a-number",
        ],
    )
    def test_anything_else_is_none_rather_than_an_exception(self, expr: str) -> None:
        """The text comes from an uploaded settings file, so a refusal has to be
        a `None` the caller falls back from — never a 500, and never an `eval`."""
        assert eval_attribute_expression(expr, {"INT": 2.0}) is None
