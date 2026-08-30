#!/usr/bin/env python3
"""Phase 1 of docs/translation-plan.md.

Extract the canonical SR5 terminology glossary from the 2021 character-sheet
localization (``xz.language.xslt`` / "52160対応") and diff it against the
vendored ``ja-jp.xml`` / ``ja-jp_data.xml`` so the mismatches can be reviewed
by hand before Phase 2.

The 2021 sheet glossary is the authority (newest of the ~/Downloads sources).
The 2020 file is strictly superseded and is only used to report which terms it
still left untranslated.

Outputs (regenerated, safe to commit):
  docs/translation-glossary.md
  docs/translation-glossary-mismatches.md

Usage:
  python scripts/build_ja_glossary.py \
      [--xslt PATH] [--xslt-old PATH] [--lang-dir PATH] [--docs-dir PATH]
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_XSLT = Path.home() / "Downloads/chummer5th_シート日本語化_52160対応/xz.language.xslt"
DEFAULT_XSLT_OLD = Path.home() / "Downloads/chummer5th_シート日本語化/xz.language.xslt"
DEFAULT_LANG = ROOT / "vendor" / "chummer" / "lang"
DEFAULT_DOCS = ROOT.parent / "docs"

JP_RE = re.compile(r"[぀-ヿ㐀-鿿]")
VAR_RE = re.compile(
    r'name="lang\.([^"]+)"\s+select="(?:string\()?\'((?:[^\']|\\\')*)\'\)?"'
)

# var name -> English term where de-camelCasing the var name is wrong / ambiguous.
ENGLISH_OVERRIDES = {
    "AGI": "AGI", "BOD": "BOD", "REA": "REA", "STR": "STR", "WIL": "WIL",
    "LOG": "LOG", "INT": "INT", "CHA": "CHA", "EDG": "EDG", "MAG": "MAG",
    "RES": "RES", "DEP": "DEP", "ESS": "ESS", "ASDF": "A/S/D/F",
    "Mugshot": "Portrait", "Data": "Date (data label)", "OVR": "OVR",
    "AIandAdvanced": "AI Programs and Advanced Programs",
    "Nothing2Show4Devices": "No Devices to list",
    "Nothing2Show4Notes": "No Notes to list",
    "Nothing2Show4SpiritsSprites": "No Spirits/Sprites to list",
    "Nothing2Show4Vehicles": "No Vehicles to list",
    "tstDamage1": "P", "tstDamage2": "S",
    "tstDuration1": "I", "tstDuration2": "P", "tstDuration3": "S",
    "NuyenSymbol": "¥ (nuyen symbol)", "marks": ". , (decimal / grouping)",
}

# Core rules terms mapped explicitly to ja-jp.xml string keys for a precise diff.
CORE_KEY_MAP: dict[str, list[str]] = {
    "Body": ["String_AttributeBODLong"],
    "BOD": ["String_AttributeBODShort"],
    "Agility": ["String_AttributeAGILong"],
    "AGI": ["String_AttributeAGIShort"],
    "Reaction": ["String_AttributeREALong"],
    "REA": ["String_AttributeREAShort"],
    "Strength": ["String_AttributeSTRLong"],
    "STR": ["String_AttributeSTRShort"],
    "Willpower": ["String_AttributeWILLong"],
    "WIL": ["String_AttributeWILShort"],
    "Logic": ["String_AttributeLOGLong"],
    "LOG": ["String_AttributeLOGShort"],
    "Intuition": ["String_AttributeINTLong"],
    "INT": ["String_AttributeINTShort"],
    "Charisma": ["String_AttributeCHALong"],
    "CHA": ["String_AttributeCHAShort"],
    "Edge": ["String_AttributeEDGLong"],
    "EDG": ["String_AttributeEDGShort"],
    "Magic": ["String_AttributeMAGLong"],
    "MAG": ["String_AttributeMAGShort"],
    "Resonance": ["String_AttributeRESLong"],
    "RES": ["String_AttributeRESShort"],
    "Depth": ["String_AttributeDEPLong"],
    "DEP": ["String_AttributeDEPShort"],
    "Essence": ["String_AttributeESSLong", "String_AttributeESSShort"],
}

# Glossary vars whose value is a sheet-local range/test abbreviation, not a
# reusable term — excluded from the fuzzy en-text matching in sections B/C.
NON_TERM_VARS = {
    "L", "M", "E", "S", "W", "H", "ASDF",
    "tstDamage1", "tstDamage2", "tstDuration1", "tstDuration2", "tstDuration3",
    "tstRange1", "tstRange2", "tstRange3", "tstRange4", "tstRange5",
    "tstRange6", "tstRange7", "tstRange8", "tstRange9", "tstRange10",
    "NuyenSymbol", "marks", "OVR",
}


def de_camel(name: str) -> str:
    parts = re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+", name)
    return " ".join(parts) if parts else name


def parse_xslt(path: Path) -> list[tuple[str, str]]:
    txt = path.read_text(encoding="utf-8")
    return [(m.group(1), m.group(2)) for m in VAR_RE.finditer(txt)]


def english_for(var: str, value: str) -> str:
    if var in ENGLISH_OVERRIDES:
        return ENGLISH_OVERRIDES[var]
    if not JP_RE.search(value):
        return value.strip()
    return de_camel(var)


def load_lang_strings(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    root = ET.parse(path).getroot()
    for s in root.findall(".//string"):
        key = s.get("key") or (s.findtext("key") or "")
        text = s.findtext("text") or ""
        if key:
            out[key] = text
    return out


def load_data_translations(path: Path) -> tuple[dict[str, str], dict[str, str]]:
    """(name -> translate, category-english -> translate)."""
    names: dict[str, str] = {}
    cats: dict[str, str] = {}
    if not path.exists():
        return names, cats
    root = ET.parse(path).getroot()
    for node in root.iter():
        nm = node.findtext("name")
        tr = node.findtext("translate")
        if nm and tr and nm.strip() and tr.strip():
            names.setdefault(nm.strip(), tr.strip())
    for cat in root.iter("category"):
        eng = (cat.text or "").strip()
        tr = (cat.get("translate") or "").strip()
        if eng and tr:
            cats.setdefault(eng, tr)
    return names, cats


def build_glossary_doc(rows: list[tuple[str, str]], old_rows: list[tuple[str, str]]) -> str:
    old_map = {v: val for v, val in old_rows}
    jp_rows, code_rows = [], []
    for var, value in rows:
        eng = english_for(var, value)
        if JP_RE.search(value):
            jp_rows.append((eng, value, var))
        else:
            code_rows.append((eng, value, var))
    jp_rows.sort(key=lambda r: r[0].lower())
    code_rows.sort(key=lambda r: r[0].lower())

    was_en_in_2020 = sum(
        1
        for _, _value, var in jp_rows
        if old_map.get(var) is not None and not JP_RE.search(old_map[var])
    )

    lines = [
        "# SR5 用語集 (確定版)",
        "",
        "**自動生成** — `backend/scripts/build_ja_glossary.py` が再生成する。手で編集しない。",
        "",
        "## 出典と優先順位",
        "",
        "- 典拠: `~/Downloads/chummer5th_シート日本語化_52160対応/xz.language.xslt` "
        "(2021-11, Chummer build 5.216.0 対応)。",
        "- `~/Downloads/` 内で競合したら新しい方が真 → **2021 版 > 2020 版 > chumJA (2013)**。",
        "- 2020 版 (`chummer5th_シート日本語化/xz.language.xslt`) は本表で完全に上位互換のため参照不要。",
        f"  - 2020 版では英語のままだったが 2021 版で和訳された語: **{was_en_in_2020} 件**。",
        "- 2021 版でも英語/略号のままの語 (下表2) は原文維持が正 (AP・DV・ESS 等のゲーム用語コード)。",
        "",
        f"- 和訳あり: **{len(jp_rows)} 件** / コード・略号 (latin のまま): **{len(code_rows)} 件**。",
        "",
        "## 表1: 和訳あり (確定用語)",
        "",
        "| English | 日本語 | xslt var | 備考 |",
        "|---|---|---|---|",
    ]
    for eng, value, var in jp_rows:
        note = ""
        prev = old_map.get(var)
        if prev is not None and prev != value:
            note = f"2020版: `{prev}`"
        lines.append(f"| {eng} | {value} | `lang.{var}` | {note} |")

    lines += [
        "",
        "## 表2: コード・略号 (原文維持)",
        "",
        "| English | 表示 | xslt var |",
        "|---|---|---|",
    ]
    for eng, value, var in code_rows:
        lines.append(f"| {eng} | {value} | `lang.{var}` |")
    lines.append("")
    return "\n".join(lines)


def build_mismatch_doc(
    rows: list[tuple[str, str]],
    ui_en: dict[str, str],
    ui_ja: dict[str, str],
    data_names: dict[str, str],
    data_cats: dict[str, str],
) -> str:
    gloss: dict[str, tuple[str, str]] = {}  # english(lower) -> (english, jp)
    for var, value in rows:
        if not JP_RE.search(value) or var in NON_TERM_VARS:
            continue
        eng = english_for(var, value)
        if len(eng) <= 1:
            continue
        gloss.setdefault(eng.lower(), (eng, value))

    # Section A: explicit core-term key map against ja-jp.xml
    core_lines = [
        "## A. コア用語 (ja-jp.xml キー明示マッピング)",
        "",
        "| English | 用語集 (2021) | ja-jp.xml キー | 現在値 | 一致 |",
        "|---|---|---|---|---|",
    ]
    core_hits = 0
    for eng, keys in CORE_KEY_MAP.items():
        g = gloss.get(eng.lower())
        if not g:
            continue
        want = g[1]
        for key in keys:
            cur = ui_ja.get(key)
            if cur is None:
                continue
            ok = "✅" if cur == want else "❌"
            if cur != want:
                core_hits += 1
            core_lines.append(f"| {eng} | {want} | `{key}` | {cur or '(なし)'} | {ok} |")
    core_lines.append("")
    core_lines.insert(1, f"\n不一致: **{core_hits} 件**\n")

    # Section B: ja-jp.xml text values whose en-us text equals a glossary term
    ui_lines = [
        "## B. ja-jp.xml — 英語原文が用語集の見出しと一致するもの",
        "",
        "en-us.xml の `<text>` が用語集の English と一致するキーについて、"
        "現在の日本語訳が用語集と違うものだけを挙げる。",
        "",
        "| English | 用語集 | ja-jp.xml キー | 現在値 |",
        "|---|---|---|---|",
    ]
    seen = set()
    for key, en_text in sorted(ui_en.items()):
        norm = (en_text or "").strip()
        g = gloss.get(norm.lower())
        if not g:
            continue
        cur = ui_ja.get(key, "")
        if cur == g[1] or not norm:
            continue
        row = (g[0], g[1], key, cur)
        if row in seen:
            continue
        seen.add(row)
        ui_lines.append(f"| {g[0]} | {g[1]} | `{key}` | {cur or '(未訳)'} |")
    ui_lines.append("")

    # Section C: ja-jp_data.xml names / categories vs glossary
    data_lines = [
        "## C. ja-jp_data.xml — エンティティ名・カテゴリが用語集見出しと一致するもの",
        "",
        "| English | 用語集 | 種別 | 現在値 |",
        "|---|---|---|---|",
    ]
    for src_label, mapping in (("name", data_names), ("category", data_cats)):
        for eng, cur in sorted(mapping.items()):
            g = gloss.get(eng.strip().lower())
            if not g or cur == g[1]:
                continue
            data_lines.append(f"| {g[0]} | {g[1]} | {src_label} | {cur} |")
    data_lines.append("")

    header = [
        "# 用語集 vs 既存訳 — 不一致レポート",
        "",
        "**自動生成** — `backend/scripts/build_ja_glossary.py`。",
        "Phase 2 で採用形を決める際の作業リスト。用語集 (2021) を正とするが、",
        "固有名・文脈依存の差は個別判断すること。",
        "",
    ]
    return "\n".join(header + core_lines + ui_lines + data_lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--xslt", type=Path, default=DEFAULT_XSLT)
    ap.add_argument("--xslt-old", type=Path, default=DEFAULT_XSLT_OLD)
    ap.add_argument("--lang-dir", type=Path, default=DEFAULT_LANG)
    ap.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS)
    args = ap.parse_args(argv)

    if not args.xslt.exists():
        print(f"error: xslt not found: {args.xslt}", file=sys.stderr)
        return 2

    rows = parse_xslt(args.xslt)
    old_rows = parse_xslt(args.xslt_old) if args.xslt_old.exists() else []
    ui_en = load_lang_strings(args.lang_dir / "en-us.xml")
    ui_ja = load_lang_strings(args.lang_dir / "ja-jp.xml")
    data_names, data_cats = load_data_translations(args.lang_dir / "ja-jp_data.xml")

    args.docs_dir.mkdir(parents=True, exist_ok=True)
    gloss_path = args.docs_dir / "translation-glossary.md"
    mism_path = args.docs_dir / "translation-glossary-mismatches.md"
    gloss_path.write_text(build_glossary_doc(rows, old_rows) + "\n", encoding="utf-8")
    mism_path.write_text(
        build_mismatch_doc(rows, ui_en, ui_ja, data_names, data_cats) + "\n",
        encoding="utf-8",
    )

    print(f"parsed {len(rows)} glossary vars from {args.xslt.name}")
    print(f"wrote {gloss_path.relative_to(ROOT.parent)}")
    print(f"wrote {mism_path.relative_to(ROOT.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
