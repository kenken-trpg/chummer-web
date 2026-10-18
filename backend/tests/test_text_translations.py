"""ja_overrides/texts.json — sentences keyed by row id (a mentor's advantage)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from app.catalog_view import public_catalog
from app.data_loader.loaders import translations as loader
from app.data_loader.loaders.translations import TEXT_FIELDS, load_text_translations, text_key
from scripts.ja_provenance import ja_books

JP_RE = re.compile(r"[぀-ヿ㐀-鿿]")
TEXTS = Path(__file__).resolve().parents[1] / "data" / "ja_overrides" / "texts.json"


def test_a_key_names_a_known_kind_and_field_and_its_id_is_lower_cased(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "texts.json").write_text(
        json.dumps(
            {
                "mentor/136A3DC5-D9C4/advantage": "全員：ダメージ抵抗テストにダイス+2",
                "mentor/136a3dc5-d9c4/notes": "読まれない欄",
                "quality/abc/advantage": "読まれない種類",
                "mentor//advantage": "id が無い",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(loader, "OVERRIDE_DIR", tmp_path)
    assert load_text_translations() == {"mentor/136a3dc5-d9c4/advantage": "全員：ダメージ抵抗テストにダイス+2"}


def test_the_catalog_carries_the_table() -> None:
    assert public_catalog()["text_translations"] == load_text_translations()


def test_every_entry_is_japanese_text_for_a_row_the_japanese_books_print() -> None:
    """Supplement content stays in English (CONTRIBUTING.md, Translations), so
    a sentence may only be translated for a row from a book with a Japanese
    edition — a Street Grimoire mentor's advantage is not ours to write."""
    raw: dict[str, str] = json.loads(TEXTS.read_text(encoding="utf-8"))
    pub = public_catalog()
    printed = ja_books(pub["books"])
    rows = {"mentor": {m["id"].lower(): m for m in pub["mentors"]}}
    problems = []
    for key, value in raw.items():
        kind, row_id, field = (key.split("/") + ["", ""])[:3]
        row = rows.get(kind, {}).get(row_id.lower())
        if field not in TEXT_FIELDS.get(kind, ()) or row is None:
            problems.append(f"{key}: no such {kind or 'kind'} row or field")
        elif row["source"] not in printed:
            problems.append(f"{key}: {row['name']} is from {row['source']}, which has no Japanese edition")
        elif key != text_key(kind, row_id, field):
            problems.append(f"{key}: write the id in lower case")
        elif not JP_RE.search(value):
            problems.append(f"{key}: not Japanese")
    assert not problems, "\n  " + "\n  ".join(problems)
