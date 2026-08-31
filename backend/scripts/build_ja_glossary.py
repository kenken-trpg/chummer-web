#!/usr/bin/env python3
"""Phases 1 / 4 of docs/translation-plan.md.

Merge the SR5 terminology from the two external references and diff the result
against the vendored lang files + our committed overlay.

Sources (``~/Downloads/``):
  1. ``xz.language.xslt`` / "52160対応"       — 2021 Chummer sheet localisation.
                                                Chummer-native conventions, so it
                                                stays authoritative for this app.
  2. ``shadowrun5eja/lang/ja.json``          — Foundry VTT SR5e i18n, maintained
                                                (github.com/MiyabiRouga/shadowrun5eja).
                                                Used *additively* — fills terms the
                                                2021 file lacks; never overrides it.
  3. ``xz.language.xslt`` (2020)             — superseded, only a delta count.

Precedence: ``ADOPTED_OVERRIDES`` (hand fixes) > 2021 xslt > sr5eja. Where the
two references simply disagree the row is flagged 差異 for a human to judge.

Outputs (regenerated, safe to commit):
  docs/translation-glossary.md
  docs/translation-glossary-mismatches.md

Usage:
  python scripts/build_ja_glossary.py \
      [--xslt PATH] [--xslt-old PATH] [--sr5eja PATH] [--lang-dir PATH] [--docs-dir PATH]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DL = Path.home() / "Downloads"
DEFAULT_XSLT = DL / "chummer5th_シート日本語化_52160対応/xz.language.xslt"
DEFAULT_XSLT_OLD = DL / "chummer5th_シート日本語化/xz.language.xslt"
DEFAULT_SR5EJA = DL / "shadowrun5eja_ja.json"
DEFAULT_LANG = ROOT / "vendor" / "chummer" / "lang"
DEFAULT_OVERLAY = ROOT / "data" / "ja_overrides"
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

# Hand-fixed adopted forms (win over both references). Keyed by English (lower).
# The user fixed the 靱/靭 kanji variant and prefers 直観 over 直感.
ADOPTED_OVERRIDES = {
    "body": "強靱力", "bod": "強靱",
    "intuition": "直観力", "int": "直観",
    "contact": "コンタクト",
}

# Core rules terms mapped explicitly to ja-jp.xml string keys for a precise diff.
CORE_KEY_MAP: dict[str, list[str]] = {
    "Body": ["String_AttributeBODLong"], "BOD": ["String_AttributeBODShort"],
    "Agility": ["String_AttributeAGILong"], "AGI": ["String_AttributeAGIShort"],
    "Reaction": ["String_AttributeREALong"], "REA": ["String_AttributeREAShort"],
    "Strength": ["String_AttributeSTRLong"], "STR": ["String_AttributeSTRShort"],
    "Willpower": ["String_AttributeWILLong"], "WIL": ["String_AttributeWILShort"],
    "Logic": ["String_AttributeLOGLong"], "LOG": ["String_AttributeLOGShort"],
    "Intuition": ["String_AttributeINTLong"], "INT": ["String_AttributeINTShort"],
    "Charisma": ["String_AttributeCHALong"], "CHA": ["String_AttributeCHAShort"],
    "Edge": ["String_AttributeEDGLong"], "EDG": ["String_AttributeEDGShort"],
    "Magic": ["String_AttributeMAGLong"], "MAG": ["String_AttributeMAGShort"],
    "Resonance": ["String_AttributeRESLong"], "RES": ["String_AttributeRESShort"],
    "Depth": ["String_AttributeDEPLong"], "DEP": ["String_AttributeDEPShort"],
    "Essence": ["String_AttributeESSLong", "String_AttributeESSShort"],
}

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
    return [(m.group(1), m.group(2)) for m in VAR_RE.finditer(path.read_text(encoding="utf-8"))]


def english_for(var: str, value: str) -> str:
    if var in ENGLISH_OVERRIDES:
        return ENGLISH_OVERRIDES[var]
    if not JP_RE.search(value):
        return value.strip()
    return de_camel(var)


def parse_sr5eja(path: Path) -> dict[str, tuple[str, str]]:
    """english(lower) -> (english, japanese) for term-like i18n leaves only."""
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    flat: dict[str, str] = {}

    def walk(obj: object, prefix: str = "") -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                walk(v, f"{prefix}.{k}" if prefix else k)
        elif isinstance(obj, str):
            flat[prefix] = obj

    walk(raw)
    out: dict[str, tuple[str, str]] = {}
    for key, value in flat.items():
        value = value.strip()
        if not value or not JP_RE.search(value) or any(c in value for c in "。、：（）\n"):
            continue
        parts = key.split(".")
        eng = None
        if parts[0] == "TYPES" and len(parts) == 3 and parts[1] in ("Item", "Actor"):
            eng = parts[2].replace("_", " ")
        elif (
            parts[0] == "SR5"
            and len(parts) == 2
            and re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", parts[1])
            and 1 <= len(value) <= 16
        ):
            eng = de_camel(parts[1])
        if eng:
            out.setdefault(eng.lower(), (eng, value))
    return out


def load_lang_strings(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for s in ET.parse(path).getroot().findall(".//string"):
        key = s.get("key") or (s.findtext("key") or "")
        if key:
            out[key] = s.findtext("text") or ""
    return out


def load_data_translations(path: Path) -> tuple[dict[str, str], dict[str, str]]:
    names: dict[str, str] = {}
    cats: dict[str, str] = {}
    if not path.exists():
        return names, cats
    root = ET.parse(path).getroot()
    for node in root.iter():
        nm, tr = node.findtext("name"), node.findtext("translate")
        if nm and tr and nm.strip() and tr.strip():
            names.setdefault(nm.strip(), tr.strip())
    for cat in root.iter("category"):
        eng = (cat.text or "").strip()
        tr = (cat.get("translate") or "").strip()
        if eng and tr:
            cats.setdefault(eng, tr)
    return names, cats


def adopted(english: str, xslt_ja: str | None, sr5eja_ja: str | None) -> str:
    """Hand fix > 2021 xslt > sr5eja (sr5eja only fills gaps)."""
    return (
        ADOPTED_OVERRIDES.get(english.lower())
        or xslt_ja
        or sr5eja_ja
        or ""
    )


def build_glossary_doc(
    rows: list[tuple[str, str]],
    old_rows: list[tuple[str, str]],
    sr5eja: dict[str, tuple[str, str]],
) -> str:
    old_map = dict(old_rows)
    xslt_jp: dict[str, tuple[str, str, str]] = {}  # eng_lower -> (eng, ja, var)
    code_rows = []
    for var, value in rows:
        eng = english_for(var, value)
        if JP_RE.search(value):
            xslt_jp.setdefault(eng.lower(), (eng, value, var))
        else:
            code_rows.append((eng, value, var))

    all_keys = sorted(set(xslt_jp) | set(sr5eja))
    merged = []
    conflicts = 0
    sr5eja_only = 0
    for k in all_keys:
        x = xslt_jp.get(k)
        s = sr5eja.get(k)
        eng = (x or s)[0]
        xja = x[1] if x else None
        sja = s[1] if s else None
        pick = adopted(eng, xja, sja)
        note = []
        if k in ADOPTED_OVERRIDES:
            note.append("手動確定")
        if xja and sja and xja != sja:
            conflicts += 1
            note.append("差異")
        if s and not x:
            sr5eja_only += 1
        merged.append((eng, pick, xja or "", sja or "", " / ".join(note)))

    was_en_in_2020 = sum(
        1
        for _, _v, var in xslt_jp.values()
        if old_map.get(var) is not None and not JP_RE.search(old_map[var])
    )

    lines = [
        "# SR5 用語集 (統合版)",
        "",
        "**自動生成** — `backend/scripts/build_ja_glossary.py`。手で編集しない。",
        "",
        "## 出典と優先順位",
        "",
        "1. `~/Downloads/chummer5th_シート日本語化_52160対応/xz.language.xslt` (2021) — "
        "Chummer 系の作法。本アプリの正典。",
        "2. `~/Downloads/shadowrun5eja_ja.json` — Foundry VTT SR5e 日本語化 (保守中, "
        "github.com/MiyabiRouga/shadowrun5eja)。**空欄補完のみ**で 2021 版を上書きしない。",
        "3. 2020 版 xslt — 上位互換のため参照不要 "
        f"(2020→2021 で和訳された語 {was_en_in_2020} 件)。",
        "",
        "- 採用順: `ADOPTED_OVERRIDES` (手動確定) > 2021 版 > sr5eja。",
        "- 2 資料が食い違う語は **採用=2021版** のまま `差異` を立てる (下表の備考)。人が判断する。",
        "",
        f"- 統合語数: **{len(merged)}** / うち sr5eja だけにある新規: **{sr5eja_only}** / "
        f"2 資料で表記が割れる語: **{conflicts}**。",
        "",
        "## 表1: 統合用語",
        "",
        "| English | 採用 | 2021版 | sr5eja | 備考 |",
        "|---|---|---|---|---|",
    ]
    for eng, pick, xja, sja, note in merged:
        lines.append(f"| {eng} | {pick} | {xja} | {sja} | {note} |")

    lines += [
        "",
        "## 表2: コード・略号 (原文維持, 2021版)",
        "",
        "| English | 表示 | xslt var |",
        "|---|---|---|",
    ]
    for eng, value, var in sorted(code_rows, key=lambda r: r[0].lower()):
        lines.append(f"| {eng} | {value} | `lang.{var}` |")
    lines.append("")
    return "\n".join(lines)


def build_mismatch_doc(
    rows: list[tuple[str, str]],
    sr5eja: dict[str, tuple[str, str]],
    ui_en: dict[str, str],
    ui_ja: dict[str, str],
    ui_overlay: dict[str, str],
    data_names: dict[str, str],
    data_cats: dict[str, str],
) -> str:
    gloss: dict[str, tuple[str, str]] = {}  # english(lower) -> (english, adopted jp)
    for var, value in rows:
        if not JP_RE.search(value) or var in NON_TERM_VARS:
            continue
        eng = english_for(var, value)
        if len(eng) > 1:
            gloss.setdefault(eng.lower(), (eng, value))
    for k, (eng, ja) in sr5eja.items():
        prev = gloss.get(k)
        gloss[k] = (eng, adopted(eng, prev[1] if prev else None, ja))
    for k in list(gloss):
        eng, ja = gloss[k]
        gloss[k] = (eng, adopted(eng, ja, None))

    # A: explicit core-term key map vs ja-jp.xml (+ ui.json overlay applied)
    def cur_ui(key: str) -> str | None:
        if key in ui_overlay:
            return ui_overlay[key]
        return ui_ja.get(key)

    core_lines = ["## A. コア用語 (ja-jp.xml + ui.json vs 用語集)", ""]
    core_hits = 0
    core_rows = ["| English | 用語集 | キー | 現在値 | 一致 |", "|---|---|---|---|---|"]
    for eng, keys in CORE_KEY_MAP.items():
        g = gloss.get(eng.lower())
        if not g:
            continue
        for key in keys:
            cur = cur_ui(key)
            if cur is None:
                continue
            ok = cur == g[1]
            core_hits += 0 if ok else 1
            core_rows.append(f"| {eng} | {g[1]} | `{key}` | {cur or '(なし)'} | {'✅' if ok else '❌'} |")
    core_lines += [f"不一致: **{core_hits} 件**", ""] + core_rows + [""]

    # B: ja-jp.xml English text == glossary term, but translation differs
    ui_lines = [
        "## B. ja-jp.xml — 英語原文が用語集見出しと一致し訳が違うもの",
        "",
        "| English | 用語集 | ja-jp.xml キー | 現在値 |",
        "|---|---|---|---|",
    ]
    seen = set()
    for key, en_text in sorted(ui_en.items()):
        norm = (en_text or "").strip()
        g = gloss.get(norm.lower())
        if not g or not norm:
            continue
        cur = cur_ui(key) or ""
        if cur == g[1] or (g[0], g[1], key) in seen:
            continue
        seen.add((g[0], g[1], key))
        ui_lines.append(f"| {g[0]} | {g[1]} | `{key}` | {cur or '(未訳)'} |")
    ui_lines.append("")

    # C: ja-jp_data.xml names/categories vs glossary
    data_lines = [
        "## C. ja-jp_data.xml — エンティティ名・カテゴリが用語集見出しと一致するもの",
        "",
        "| English | 用語集 | 種別 | 現在値 |",
        "|---|---|---|---|",
    ]
    for label, mapping in (("name", data_names), ("category", data_cats)):
        for eng, cur in sorted(mapping.items()):
            g = gloss.get(eng.strip().lower())
            if g and cur != g[1]:
                data_lines.append(f"| {g[0]} | {g[1]} | {label} | {cur} |")
    data_lines.append("")

    # D: sr5eja terms not yet in ui.json (candidates to seed)
    d_lines = [
        "## D. sr5eja 由来で ui.json 未収録の用語 (seed 候補)",
        "",
        "Foundry SR5e 日本語化にあり、当方の `ui.json` に無い用語。descriptor・ルール語の"
        "参照や `ui.json` 追加の材料。",
        "",
        "| English | sr5eja | 2021版 |",
        "|---|---|---|",
    ]
    xslt_by_eng = {}
    for var, value in rows:
        if JP_RE.search(value):
            xslt_by_eng.setdefault(english_for(var, value).lower(), value)
    overlay_vals = set(ui_overlay.values())
    for k, (eng, ja) in sorted(sr5eja.items()):
        if ja in overlay_vals or ja in ui_ja.values():
            continue
        d_lines.append(f"| {eng} | {ja} | {xslt_by_eng.get(k, '')} |")
    d_lines.append("")

    header = [
        "# 用語集 vs 既存訳 — 不一致レポート",
        "",
        "**自動生成** — `backend/scripts/build_ja_glossary.py`。",
        "採用形は sr5eja > 2021版 > 手動確定 override。文脈依存・固有名は個別判断。",
        "",
    ]
    return "\n".join(header + core_lines + ui_lines + data_lines + d_lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--xslt", type=Path, default=DEFAULT_XSLT)
    ap.add_argument("--xslt-old", type=Path, default=DEFAULT_XSLT_OLD)
    ap.add_argument("--sr5eja", type=Path, default=DEFAULT_SR5EJA)
    ap.add_argument("--lang-dir", type=Path, default=DEFAULT_LANG)
    ap.add_argument("--overlay-dir", type=Path, default=DEFAULT_OVERLAY)
    ap.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS)
    args = ap.parse_args(argv)

    if not args.xslt.exists():
        print(f"error: xslt not found: {args.xslt}", file=sys.stderr)
        return 2

    rows = parse_xslt(args.xslt)
    old_rows = parse_xslt(args.xslt_old) if args.xslt_old.exists() else []
    sr5eja = parse_sr5eja(args.sr5eja)
    ui_en = load_lang_strings(args.lang_dir / "en-us.xml")
    ui_ja = load_lang_strings(args.lang_dir / "ja-jp.xml")
    data_names, data_cats = load_data_translations(args.lang_dir / "ja-jp_data.xml")
    ui_overlay_path = args.overlay_dir / "ui.json"
    ui_overlay = (
        json.loads(ui_overlay_path.read_text(encoding="utf-8"))
        if ui_overlay_path.exists()
        else {}
    )

    args.docs_dir.mkdir(parents=True, exist_ok=True)
    gloss_path = args.docs_dir / "translation-glossary.md"
    mism_path = args.docs_dir / "translation-glossary-mismatches.md"
    gloss_path.write_text(
        build_glossary_doc(rows, old_rows, sr5eja) + "\n", encoding="utf-8"
    )
    mism_path.write_text(
        build_mismatch_doc(
            rows, sr5eja, ui_en, ui_ja, ui_overlay, data_names, data_cats
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"xslt terms: {len(rows)}  sr5eja terms: {len(sr5eja)}")
    print(f"wrote {gloss_path.relative_to(ROOT.parent)}")
    print(f"wrote {mism_path.relative_to(ROOT.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
