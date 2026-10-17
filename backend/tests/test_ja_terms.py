"""The Japanese UI strings do not use a term the glossary already rejected.

`scripts/check_ja_terms.py` says why this cannot be a full glossary comparison.
Running it from the suite rather than wiring a new CI job keeps it in the job
that already runs, next to the other contract tests that read `frontend/`.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LOCALE = ROOT / "frontend/lib/i18n/locales/ja"
BANNED = ROOT / "docs/translation-banned-terms.md"


def _checker():
    spec = importlib.util.spec_from_file_location("check_ja_terms", ROOT / "scripts/check_ja_terms.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.skipif(not LOCALE.is_dir(), reason="frontend/ not checked out")
def test_no_banned_term_reached_the_japanese_ui() -> None:
    assert _checker().check(LOCALE, BANNED) == []


def test_every_rule_is_backed_by_a_glossary_line() -> None:
    # A rule whose canon is not in the glossary would enforce someone's taste.
    glossary = (ROOT / "docs/translation-glossary.md").read_text(encoding="utf-8").split("\n")
    for rule in _checker().rules(BANNED.read_text(encoding="utf-8")):
        line = int(rule.source.rsplit("(", 1)[1].rstrip(")"))
        row = glossary[line - 1]
        assert rule.right in row, f"{rule.wrong}: line {line} is {row!r}"


@pytest.mark.parametrize(
    ("text", "flagged"),
    [
        ('"a": "ライフスタイル品質",', True),
        ('"a": "ライフスタイル資質",', False),
        ('"a": "ウェアのグレード",', True),
        ('"a": "システム・アップグレード",', False),  # the allowed word, not the term
        ('"a": "マトリクス",', True),
        ('"a": "マトリックス",', False),  # the long vowel is the correct form
        ('"a": "物理ダメージ",', True),  # damage goes on the 身体 track
        ('"a": "物理呪文",', False),  # the spell type really is 物理
    ],
)
def test_rules_fire_on_the_wrong_word_and_not_the_right_one(tmp_path: Path, text: str, flagged: bool) -> None:
    locale = tmp_path / "ja"
    locale.mkdir()
    (locale / "probe.ts").write_text(text, encoding="utf-8")
    assert bool(_checker().check(locale, BANNED)) is flagged


def test_no_banned_term_reached_the_docs() -> None:
    assert _checker().check_docs(ROOT, BANNED) == []


def test_every_docs_term_is_a_rule() -> None:
    checker = _checker()
    text = BANNED.read_text(encoding="utf-8")
    words = checker.doc_terms(text)
    assert "車両" in words
    assert words <= {rule.wrong for rule in checker.rules(text)}


@pytest.mark.parametrize(
    ("text", "flagged"),
    [
        ("A.I.のホームノードが車両なら", True),
        ("リポジトリ全体が `物理リミット` と書いていた", False),  # a code span quotes the old word
        ("値を判定する", False),  # 判定 is banned in the UI, ordinary prose in the docs
        ("イニシアチブ・ダイスの上限", True),
    ],
)
def test_the_docs_are_held_to_their_own_list(tmp_path: Path, text: str, flagged: bool) -> None:
    (tmp_path / "probe.md").write_text(text, encoding="utf-8")
    assert bool(_checker().check_docs(tmp_path, BANNED)) is flagged


EN_LOCALE = ROOT / "frontend/lib/i18n/locales/en"


@pytest.mark.skipif(not EN_LOCALE.is_dir(), reason="frontend/ not checked out")
def test_no_banned_term_reached_the_english_ui() -> None:
    assert _checker().check_en(EN_LOCALE, BANNED) == []


def test_every_english_rule_is_backed_by_a_glossary_line() -> None:
    glossary = (ROOT / "docs/translation-glossary.md").read_text(encoding="utf-8").split("\n")
    found = _checker().en_rules(BANNED.read_text(encoding="utf-8"))
    assert found
    for rule in found:
        line = int(rule.source.rsplit("(", 1)[1].rstrip(")"))
        assert glossary[line - 1].startswith(f"| {rule.right} |"), f"{rule.wrong}: line {line}"


@pytest.mark.parametrize(
    ("text", "flagged"),
    [
        ('"a": "Stun monitor = 8 + WIL",', True),
        ('"a": "the stun monitor",', True),  # case does not save it
        ('"a": "Stun track = 8 + WIL",', False),
        ('"a": "Matrix condition monitor",', False),
        ('"a": " · fade {fade}",', True),
        ('"a": "Fade is the hits ×2",', True),
        ('"res.fadeResist": " · fading resistance {fade}",', False),  # the key and the placeholder are code
        ('"a": "what it holds fades over time",', False),  # an ordinary verb
    ],
)
def test_english_rules_fire_on_the_other_name(tmp_path: Path, text: str, flagged: bool) -> None:
    locale = tmp_path / "en"
    locale.mkdir()
    (locale / "probe.ts").write_text(text, encoding="utf-8")
    assert bool(_checker().check_en(locale, BANNED)) is flagged
