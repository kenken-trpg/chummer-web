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
    # baseline with an empty overlay so the committed data.json can't skew counts
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setattr(data_loader, "OVERRIDE_DIR", empty)
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
    # every untouched vendored entry survives, plus the one brand-new key
    assert len(merged) == len(base) + 1


def test_load_ui_strings_merges_overlay_over_vendored(tmp_path, monkeypatch) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.setattr(data_loader, "OVERRIDE_DIR", empty)
    base = load_ui_strings()
    assert base.get("String_Karma") == "カルマ", "sanity: vendored entry present"

    monkeypatch.setattr(data_loader, "OVERRIDE_DIR", tmp_path)
    _write(tmp_path, "ui.json", {"String_Karma": "上書きカルマ"})
    merged = load_ui_strings()

    assert merged["String_Karma"] == "上書きカルマ"
    assert len(merged) == len(base)


def test_catalog_translations_reflect_overlay(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(data_loader, "OVERRIDE_DIR", tmp_path)
    _write(tmp_path, "data.json", {"Clothing": "キャタログ上書き"})
    data_loader.reset_catalog()
    try:
        assert data_loader.catalog()["translations"]["Clothing"] == "キャタログ上書き"
    finally:
        data_loader.reset_catalog()


# --- Phase 2: the committed data.json seed --------------------------------------

JP_RE = __import__("re").compile(r"[぀-ヿ㐀-鿿]")


def _committed_data_overlay() -> dict[str, str]:
    return json.loads((OVERRIDE_DIR / "data.json").read_text(encoding="utf-8"))


def test_committed_data_overlay_values_are_japanese() -> None:
    for key, val in _committed_data_overlay().items():
        assert isinstance(val, str) and JP_RE.search(val), f"{key!r} -> {val!r}"


def test_committed_data_overlay_keys_are_used_by_catalog() -> None:
    """Every seeded key should be an entity name or category the app exposes,
    otherwise it is dead weight (or a typo) and should be pruned."""
    overlay = _committed_data_overlay()
    if not overlay:
        return
    cat = data_loader.catalog()
    known: set[str] = set()

    def walk(obj: object) -> None:
        if isinstance(obj, dict):
            for field in ("name", "category"):
                v = obj.get(field)
                if isinstance(v, str) and v.strip():
                    known.add(v.strip())
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)

    for k, v in cat.items():
        if k not in {"translations", "ui_strings"}:
            walk(v)
    # skill groups are a plain list of strings, not dict rows
    known.update(
        g for g in (cat.get("skills") or {}).get("groups") or [] if isinstance(g, str)
    )

    orphans = sorted(k for k in overlay if k not in known)
    assert not orphans, f"overlay keys not present in catalog: {orphans}"


def test_committed_data_overlay_anchors() -> None:
    tr = data_loader.load_translations()
    # curated, glossary-checked
    assert tr["Human"] == "ヒューマン"
    assert tr["Troll"] == "トロール"
    assert tr["Metahuman"] == "メタヒューマン"
    assert tr["Body"] == "強靱力"  # 靭 -> 靱
    # imported from chumJA SR4 exact-name match
    assert tr["Alter Memory"] == "記憶改変"
    # Phase 2b hand translations
    assert tr["Close Combat"] == "近接戦闘"  # skill group
    assert tr["Biotech"] == "医療"  # group sense wins over the gear-category collision
    assert tr["Hobgoblin"] == "ホブゴブリン"  # metavariant
