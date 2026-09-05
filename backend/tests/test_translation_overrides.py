"""Phase 0: Git-tracked Japanese translation overlay merged on top of the
vendored chummer5a lang files (see docs/plans/translation-plan.md)."""

from __future__ import annotations

import json
from pathlib import Path

from app import data_loader
from app.data_loader import (
    OVERRIDE_DIR,
    _load_ja_overrides,
    load_skill_group_names,
    load_skills,
    load_translations,
    load_ui_strings,
)
from app.data_loader.loaders import translations as _translations_mod


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
    monkeypatch.setattr(_translations_mod, "OVERRIDE_DIR", tmp_path)
    assert _load_ja_overrides("data.json") == {}


def test_load_ja_overrides_malformed_json_is_ignored(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(_translations_mod, "OVERRIDE_DIR", tmp_path)
    _write(tmp_path, "data.json", "{ not valid json ")
    assert _load_ja_overrides("data.json") == {}


def test_load_ja_overrides_non_object_is_ignored(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(_translations_mod, "OVERRIDE_DIR", tmp_path)
    _write(tmp_path, "data.json", ["not", "a", "dict"])
    assert _load_ja_overrides("data.json") == {}


def test_load_ja_overrides_skips_blank_and_non_string_values(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(_translations_mod, "OVERRIDE_DIR", tmp_path)
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
    monkeypatch.setattr(_translations_mod, "OVERRIDE_DIR", empty)
    base = load_translations()
    assert base.get("Clothing") == "衣服", "sanity: vendored entry present"

    monkeypatch.setattr(_translations_mod, "OVERRIDE_DIR", tmp_path)
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
    monkeypatch.setattr(_translations_mod, "OVERRIDE_DIR", empty)
    base = load_ui_strings()
    assert base.get("String_Karma") == "カルマ", "sanity: vendored entry present"

    monkeypatch.setattr(_translations_mod, "OVERRIDE_DIR", tmp_path)
    _write(tmp_path, "ui.json", {"String_Karma": "上書きカルマ"})
    merged = load_ui_strings()

    assert merged["String_Karma"] == "上書きカルマ"
    assert len(merged) == len(base)


def test_catalog_translations_reflect_overlay(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(_translations_mod, "OVERRIDE_DIR", tmp_path)
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
    known.update(g for g in (cat.get("skills") or {}).get("groups") or [] if isinstance(g, str))

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
    assert tr["Fire Elemental"] == "火のエレメンタル"  # spirit
    assert tr["Necromancy"] == "死霊術"  # magic art
    assert tr["Buddhism"] == "仏教"  # tradition
    # spells — 漢語/カタカナ dual format (batch 3, confident subset only)
    assert tr["Ice Spear"] == "氷槍/アイス・スピア"
    assert tr["Mindnet Extended"] == "広域精神網/エクステンデッド・マインドネット"
    # obscure supplement coinages were rolled back to English fallback
    assert not JP_RE.search(tr.get("Krigama Carpet", "") or "")
    assert not JP_RE.search(tr.get("Pyrohemetics", "") or "")
    # small-bucket batch (mentors / lifestyles / martial arts / powers / echoes / CF)
    assert tr["Bolt Hole"] == "隠れ家"
    assert tr["German Jujitsu"] == "ジャーマン柔術"
    assert tr["Indomitable Will"] == "不屈の意志"
    assert tr["Redundancy"] == "冗長化"
    # parenthetical mentor variants stay on English fallback (upstream convention)
    assert not JP_RE.search(tr.get("Wolf (Alt)", "") or "")
    # SR5 core gear translated; supplement gear stays English by policy
    assert tr["Fire Resistance"] == "耐火"
    assert tr["Liner - Insulation (3)"] == "ライナー - 断熱 (3)"


# --- Phase 3: ui_strings wired through public_catalog + ui.json seed -----------


def _committed_ui_overlay() -> dict[str, str]:
    return json.loads((OVERRIDE_DIR / "ui.json").read_text(encoding="utf-8"))


def test_public_catalog_exposes_ui_strings() -> None:
    from app.catalog_view import public_catalog

    pc = public_catalog()
    strings = pc.get("ui_strings")
    assert isinstance(strings, dict) and set(strings) == {"ja", "en"}
    # ui.json override is reflected in ja...
    assert strings["ja"]["String_AttributeBODLong"] == "強靱力"
    # ...and the same key is the English original, straight from en-us.xml
    assert strings["en"]["String_AttributeBODLong"] == "Body"


def test_shipped_ui_strings_are_the_same_keys_in_both_locales() -> None:
    """A key present in one locale but not the other renders as a raw
    `String_Foo` on one side of the language switch and not the other."""
    from app.catalog_view import public_catalog

    strings = public_catalog()["ui_strings"]
    assert set(strings["ja"]) == set(strings["en"])


def test_shipped_ui_strings_cover_what_the_app_reads() -> None:
    """`attrShort` / `attrName` build `String_Attribute<KEY>Short|Long`, so the
    projection must keep every attribute the sheet can show."""
    from app.catalog_view import public_catalog

    strings = public_catalog()["ui_strings"]
    wanted = {
        f"String_Attribute{key}{suffix}"
        for key in ("BOD", "AGI", "REA", "STR", "CHA", "INT", "LOG", "WIL", "EDG", "MAG", "RES")
        for suffix in ("Short", "Long")
    }
    for locale, table in strings.items():
        assert wanted <= set(table), f"{locale} missing {sorted(wanted - set(table))}"


def test_the_curated_overlay_keys_all_ship() -> None:
    """ui.json is hand-written; a key that never reaches the browser is work
    thrown away, so the projection carries the whole overlay."""
    from app.catalog_view import public_catalog
    from app.data_loader.loaders.translations import shipped_ui_keys

    shipped = set(public_catalog()["ui_strings"]["ja"])
    assert shipped_ui_keys() <= shipped


def test_english_ui_strings_do_not_take_the_japanese_overlay() -> None:
    """`ja_overrides/ui.json` corrects the vendored Japanese. Applying it to
    `en` would overwrite the English original with a Japanese term."""
    from app.data_loader.loaders.translations import load_ui_strings

    assert load_ui_strings("en")["String_AttributeBODLong"] == "Body"


def test_an_unknown_locale_loads_nothing_rather_than_raising() -> None:
    from app.data_loader.loaders.translations import load_ui_strings

    assert load_ui_strings("fr") == {}


def test_committed_ui_overlay_keys_exist_in_lang() -> None:
    """Every ui.json key must be a real ja-jp.xml / en-us.xml string key."""
    overlay = _committed_ui_overlay()
    if not overlay:
        return
    en = data_loader.load_ui_strings()  # merged, but keys come from vendored
    import xml.etree.ElementTree as ET

    root = ET.parse(data_loader.LANG_DIR / "en-us.xml").getroot()
    en_keys = {s.get("key") or (s.findtext("key") or "") for s in root.findall(".//string")}
    orphans = sorted(k for k in overlay if k not in en_keys)
    assert not orphans, f"ui.json keys not in en-us.xml: {orphans}"
    assert all(k in en for k in overlay)


def test_committed_ui_overlay_values_are_japanese() -> None:
    for key, val in _committed_ui_overlay().items():
        assert isinstance(val, str) and JP_RE.search(val), f"{key!r} -> {val!r}"


def test_every_skill_group_has_a_japanese_name() -> None:
    """The skills tab renders `catalog.skills.groups` through this map, so a
    gap shows the player a bare English group name."""
    groups = load_skills()["groups"]
    names = load_skill_group_names()
    assert groups, "no skill groups loaded"
    assert [g for g in groups if not names.get(g)] == []


def test_skill_group_names_do_not_borrow_from_the_flat_table() -> None:
    """`translations` is keyed by English name alone, and these four names
    belong to other entities there: Influence and Stealth are spells, Firearms
    and Engineering are knowledge skills. Reading groups out of that table gave
    the Influence group the spell's 感化. Keep the two apart."""
    names = load_skill_group_names()
    flat = load_translations()
    assert names["Influence"] == "対人"
    assert names["Stealth"] == "隠密"
    assert names["Firearms"] == "小火器"
    assert names["Engineering"] == "機器整備"
    assert flat["Influence"] != names["Influence"]


def test_ja_overrides_win_over_the_upstream_group_name() -> None:
    """Same precedence as `load_translations`: the curated overlay is the
    project's own wording and outranks the vendored file."""
    overrides = _load_ja_overrides("data.json")
    names = load_skill_group_names()
    assert overrides["Conjuring"] == "召喚"  # upstream says 召霊術
    assert names["Conjuring"] == overrides["Conjuring"]
