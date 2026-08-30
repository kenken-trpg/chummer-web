"""Phase 0: Git-tracked Japanese translation overlay merged on top of the
vendored chummer5a lang files (see docs/translation-plan.md)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app import data_loader
from app.data_loader import (
    OVERRIDE_DIR,
    _load_ja_overrides,
    load_translations,
    load_ui_strings,
)


def _write(dirpath: Path, name: str, payload: object) -> None:
    (dirpath / name).write_text(
        payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )


def test_override_dir_ships_empty_json_files() -> None:
    for name in ("data.json", "ui.json"):
        path = OVERRIDE_DIR / name
        assert path.exists(), f"{name} should be committed"
        assert isinstance(json.loads(path.read_text(encoding="utf-8")), dict)


def test_load_ja_overrides_missing_file_returns_empty(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(data_loader, "OVERRIDE_DIR", tmp_path)
    assert _load_ja_overrides("data.json") == {}


def test_load_ja_overrides_malformed_json_is_ignored(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(data_loader, "OVERRIDE_DIR", tmp_path)
    _write(tmp_path, "data.json", "{ not valid json ")
    assert _load_ja_overrides("data.json") == {}


def test_load_ja_overrides_non_object_is_ignored(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(data_loader, "OVERRIDE_DIR", tmp_path)
    _write(tmp_path, "data.json", ["not", "a", "dict"])
    assert _load_ja_overrides("data.json") == {}


def test_load_ja_overrides_skips_blank_and_non_string_values(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(data_loader, "OVERRIDE_DIR", tmp_path)
    _write(
        tmp_path,
        "data.json",
        {"Keep": "残す", "Blank": "", "Spaces": "   ", "Number": 5},
    )
    assert _load_ja_overrides("data.json") == {"Keep": "残す"}


def test_load_translations_merges_overlay_over_vendored(tmp_path, monkeypatch) -> None:
    base = load_translations()
    assert base.get("Clothing") == "衣服", "sanity: vendored entry present"

    monkeypatch.setattr(data_loader, "OVERRIDE_DIR", tmp_path)
    _write(
        tmp_path,
        "data.json",
        {"Clothing": "オーバーライド衣服", "Totally New Item": "新規アイテム"},
    )
    merged = load_translations()

    assert merged["Clothing"] == "オーバーライド衣服"
    assert merged["Totally New Item"] == "新規アイテム"
    # untouched vendored entries survive
    assert len(merged) >= len(base)


def test_load_ui_strings_merges_overlay_over_vendored(tmp_path, monkeypatch) -> None:
    base = load_ui_strings()
    assert base.get("String_Karma") == "カルマ", "sanity: vendored entry present"

    monkeypatch.setattr(data_loader, "OVERRIDE_DIR", tmp_path)
    _write(tmp_path, "ui.json", {"String_Karma": "上書きカルマ"})
    merged = load_ui_strings()

    assert merged["String_Karma"] == "上書きカルマ"
    assert len(merged) >= len(base)


def test_catalog_translations_reflect_overlay(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(data_loader, "OVERRIDE_DIR", tmp_path)
    _write(tmp_path, "data.json", {"Clothing": "キャタログ上書き"})
    data_loader.reset_catalog()
    try:
        assert data_loader.catalog()["translations"]["Clothing"] == "キャタログ上書き"
    finally:
        data_loader.reset_catalog()
