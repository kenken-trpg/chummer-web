"""Phase 4 of docs/plans/translation-plan.md — lock in the unified UI terminology.

Every Japanese label below was deliberately standardised across the app. This
test fails if a banned form reappears anywhere in the frontend sources, the
engine's user-facing messages, or the committed ja_overrides files, so future
edits don't silently drift back.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FRONTEND = REPO / "frontend"
OVERLAY = REPO / "backend" / "data" / "ja_overrides"
GLOSSARY = REPO / "docs" / "translation-glossary.md"

# banned Japanese label -> the form to use instead
BANNED: dict[str, str] = {
    "属性": "能力値",
    "クオリティ": "資質",
    "コネクト": "コンタクト",
    "メタタイプ": "メタ",
    "強靭": "強靱",  # kanji-variant of 靱
    "レゾナンス": "共振力",
}
# "スキル" is banned as a standalone label but kept in these proper gear names.
SKILL_RE = re.compile(r"スキル(?!ソフト|ワイヤ|ジャック)")


def _scan(text: str) -> list[str]:
    hits: list[str] = []
    for bad, good in BANNED.items():
        for m in re.finditer(re.escape(bad), text):
            line = text.count("\n", 0, m.start()) + 1
            hits.append(f"L{line}: {bad} → {good}")
    for m in SKILL_RE.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        hits.append(f"L{line}: スキル → 技能")
    return sorted(hits, key=lambda s: int(s.split(":", 1)[0][1:]))


def _frontend_sources() -> list[Path]:
    out: list[Path] = []
    for sub in ("app", "components", "lib"):
        d = FRONTEND / sub
        if d.is_dir():
            out += [p for p in d.rglob("*.ts*") if "node_modules" not in p.parts and ".next" not in p.parts]
    return sorted(out)


def _fmt(problems: dict[str, list[str]]) -> str:
    return "\n" + "\n".join(f"  {f}\n    " + "\n    ".join(hits) for f, hits in sorted(problems.items()))


def test_frontend_uses_unified_terminology() -> None:
    files = _frontend_sources()
    assert files, "no frontend sources found"
    problems = {}
    for p in files:
        hits = _scan(p.read_text(encoding="utf-8"))
        if hits:
            problems[str(p.relative_to(REPO))] = hits
    assert not problems, _fmt(problems)


def test_engine_messages_use_unified_terminology() -> None:
    problems = {}
    for p in sorted((REPO / "backend" / "app").glob("*.py")):
        hits = _scan(p.read_text(encoding="utf-8"))
        if hits:
            problems[str(p.relative_to(REPO))] = hits
    assert not problems, _fmt(problems)


def test_overlay_values_use_unified_terminology() -> None:
    problems = {}
    for name in ("data.json", "ui.json"):
        data = json.loads((OVERLAY / name).read_text(encoding="utf-8"))
        hits = [f"{k}: {h}" for k, v in data.items() for h in _scan(v)]
        if hits:
            problems[f"ja_overrides/{name}"] = hits
    assert not problems, _fmt(problems)


def test_curated_module_values_use_unified_terminology() -> None:
    from scripts.ja_curated_entities import ENTITIES
    from scripts.ja_curated_spells import SPELLS

    hits = [
        f"{name}/{k}: {h}"
        for name, table in (("SPELLS", SPELLS), ("ENTITIES", ENTITIES))
        for k, v in table.items()
        for h in _scan(v)
    ]
    assert not hits, "\n  " + "\n  ".join(hits)


# --- glossary consistency: data.json must not contradict the 2021 glossary ----

# entity-name / category keys that intentionally diverge from the sheet glossary
GLOSSARY_EXCEPTIONS = {
    "Armor": "防具",  # category sense; glossary 装甲 is the armor *value*
}


def _load_glossary() -> dict[str, str]:
    mapping: dict[str, str] = {}
    if not GLOSSARY.exists():
        return mapping
    jp = re.compile(r"[぀-ヿ㐀-鿿]")
    for line in GLOSSARY.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 4 or cells[1] in ("English", "---") or not cells[1]:
            continue
        eng, ja = cells[1], cells[2]
        if jp.search(ja):
            mapping.setdefault(eng.lower(), ja)
    return mapping


def test_overlay_data_matches_glossary_terms() -> None:
    glossary = _load_glossary()
    assert glossary, "glossary failed to parse"
    overlay = json.loads((OVERLAY / "data.json").read_text(encoding="utf-8"))
    mismatches = []
    for key, value in overlay.items():
        want = glossary.get(key.lower())
        if want and value != want and GLOSSARY_EXCEPTIONS.get(key) != value:
            mismatches.append(f"{key!r}: overlay {value!r} vs glossary {want!r}")
    assert not mismatches, "\n  " + "\n  ".join(mismatches)
