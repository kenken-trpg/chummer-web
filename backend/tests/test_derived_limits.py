from app.engine.compute.finalize import _inherent_limits


def test_inherent_limits_match_sr5_formulas() -> None:
    total = {
        "BOD": 4,
        "AGI": 3,
        "REA": 3,
        "STR": 2,
        "LOG": 3,
        "INT": 3,
        "WIL": 3,
        "CHA": 3,
    }

    # Physical = ceil((STR*2 + BOD + REA) / 3) = ceil(11 / 3) = 4.
    # The deliberately different AGI value must not affect that limit.
    assert _inherent_limits(total, 6.0) == (4, 4, 5)


def test_social_limit_rounds_essence_up_before_the_formula() -> None:
    total = {"BOD": 2, "REA": 2, "STR": 2, "LOG": 2, "INT": 2, "WIL": 2, "CHA": 2}

    # ceil((CHA*2 + WIL + ceil(ESS)) / 3) = ceil((4 + 2 + 4) / 3) = 4.
    assert _inherent_limits(total, 3.1) == (3, 3, 4)


def test_inherent_limit_rounding_and_agi_independence() -> None:
    total = {"BOD": 1, "AGI": 6, "REA": 1, "STR": 1, "LOG": 1, "INT": 1, "WIL": 1, "CHA": 1}

    # Each unmodified result rounds up after division by three.
    assert _inherent_limits(total, 1.0) == (2, 2, 2)
