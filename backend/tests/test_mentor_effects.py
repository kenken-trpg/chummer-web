"""mentor_effects — a mentor's fixed advantage as short lines, in place of
the rulebook's text the app does not reproduce."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.data_loader import load_mentors, load_paragons
from app.engine.magic.mentor import mentor_effects

JA_ENGINE = Path(__file__).resolve().parents[2] / "frontend" / "lib" / "i18n" / "locales" / "ja" / "engine.ts"


def _by_name(name: str) -> list[dict]:
    row = next(m for m in load_mentors() + load_paragons() if m["name"] == name)
    return mentor_effects(row.get("bonus") or [])


def test_every_mentor_and_paragon_effect_has_a_line_of_its_own() -> None:
    # "other" is the fallback for a tag nothing here knows; data that grows a
    # new one should get a line, not a shrug.
    keys = set(re.findall(r'"(engine\.mentorEffect\.[A-Za-z]+)"', JA_ENGINE.read_text(encoding="utf-8")))
    problems = []
    for row in load_mentors() + load_paragons():
        for effect in mentor_effects(row.get("bonus") or []):
            if effect["key"] == "engine.mentorEffect.other" or effect["key"] not in keys:
                problems.append(f"{row['name']}: {effect['key']}")
    assert not problems, problems


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Dog", [{"key": "engine.mentorEffect.skill", "params": {"value": "+2", "names": [{"tr": "Tracking"}]}}]),
        ("Bear", [{"key": "engine.mentorEffect.damageResistance", "params": {"value": "+2"}}]),
        (
            "Dragonslayer",
            [{"key": "engine.mentorEffect.pickSkill", "params": {"options": [{"tr": "Social Active"}], "value": "+2"}}],
        ),
        (
            "Disease",
            [
                {"key": "engine.mentorEffect.toxinResist", "params": {"value": "+2"}},
                {"key": "engine.mentorEffect.pathogenResist", "params": {"value": "+2"}},
            ],
        ),
    ],
)
def test_a_mentor_reads_as_what_the_engine_applies(name: str, expected: list[dict]) -> None:
    assert _by_name(name) == expected


def test_eagle_names_the_allergy_it_grants_with_its_pick() -> None:
    assert _by_name("Eagle")[0] == {
        "key": "engine.mentorEffect.qualityPick",
        "params": {"name": {"tr": "Allergy (Common, Mild)"}, "pick": {"tr": "Pollutants"}},
    }


def test_nodes_that_differ_only_by_name_share_a_line() -> None:
    # Shooter gives +1 accuracy to twelve weapon skills; Squirrel repeats Gymnastics.
    accuracy = [e for e in _by_name("Shooter (The Soldier)") if e["key"] == "engine.mentorEffect.accuracy"]
    assert len(accuracy) == 1
    assert len(accuracy[0]["params"]["names"]) == 12
    assert _by_name("Squirrel")[0]["params"]["names"] == [{"tr": "Gymnastics"}]
