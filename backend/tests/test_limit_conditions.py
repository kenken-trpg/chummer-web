"""Every limit condition the data names must have wording behind it.

A `<limitmodifier>` carries its condition as one of Chummer's own tokens
(`LimitCondition_Visible`). `limit_condition_label` maps it to a dictionary key,
and an unmapped token falls through as itself — all the way onto the screen,
since the front end renders a key it does not know as the key. That is how
"社交リミット +2（LimitCondition_Visible）" reached the sidebar of anyone wearing
one of the Social-limit suits, in Japanese *and* in English.

So the mapping is checked against the data rather than maintained by eye:
`test_notice_keys.py` already makes sure each key it points at has a sentence
in `locales/ja/`, and the `Record<MsgKey, string>` type makes `en` keep up.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.improvements._common import LIMIT_CONDITION_KEYS, limit_condition_label

DATA = Path(__file__).resolve().parents[1] / "vendor" / "chummer" / "data"
CONDITION_RE = re.compile(r"<condition>\s*(LimitCondition_[A-Za-z0-9_]+)\s*</condition>")


def _tokens_in_data() -> set[str]:
    found: set[str] = set()
    for path in sorted(DATA.glob("*.xml")):
        found |= set(CONDITION_RE.findall(path.read_text(encoding="utf-8", errors="replace")))
    return found


pytestmark = pytest.mark.skipif(not DATA.is_dir(), reason="vendored Chummer data not fetched")


def test_every_condition_token_in_the_data_is_mapped() -> None:
    missing = sorted(_tokens_in_data() - set(LIMIT_CONDITION_KEYS))
    assert not missing, f"would render as the raw token: {missing}"


def test_the_map_carries_nothing_the_data_dropped() -> None:
    # One exception: `SkillsActiveSneaking` is not in the data today. It was
    # mapped to the *thermal* sneaking wording, which is a different condition,
    # so it is kept with its own wording rather than left to come back wrong.
    extra = sorted(set(LIMIT_CONDITION_KEYS) - _tokens_in_data())
    assert extra == ["LimitCondition_SkillsActiveSneaking"]


def test_a_mapped_token_becomes_a_key_and_an_unmapped_one_is_still_visible() -> None:
    assert limit_condition_label("LimitCondition_Visible") == {
        "key": "engine.limitCond.visible",
        "params": {},
    }
    # the fallback stays as it was: visible in the UI, not a crash
    assert limit_condition_label("LimitCondition_Invented") == {
        "key": "LimitCondition_Invented",
        "params": {},
    }
    assert limit_condition_label("") is None
