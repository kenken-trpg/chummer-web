#!/usr/bin/env python3
"""Phase 2 of docs/translation-plan.md — seed backend/data/ja_overrides/data.json.

Sources, newest-wins (see docs/translation-plan.md):
  1. curated map below (SR5, glossary-checked) — highest priority
  2. chumJA SR4 ``ja_data.xml`` — only exact ``<name>`` / category matches, JP only

Only names/categories that the running catalog() actually exposes and that are
NOT already Japanese (vendored or existing overlay) are added, so the diff stays
small and reviewable. Re-runnable: existing overlay entries are preserved unless
a higher-priority source changes them.

Usage:
  python scripts/import_ja_from_refs.py [--chumja PATH] [--write] [--report PATH]

Without --write it only prints what would change.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_CHUMJA = Path.home() / "Downloads/chumJA_20130129/lang/ja_data.xml"
OVERLAY = ROOT / "data" / "ja_overrides" / "data.json"
DEFAULT_REPORT = ROOT.parent / "docs" / "translation-import-report.md"

JP_RE = re.compile(r"[぀-ヿ㐀-鿿]")

# --- curated SR5 entries (glossary-checked). Highest priority. -----------------
CURATED: dict[str, str] = {
    # playable metatypes
    "Human": "ヒューマン",
    "Elf": "エルフ",
    "Dwarf": "ドワーフ",
    "Ork": "オーク",
    "Troll": "トロール",
    # core metavariants (Run Faster)
    "Nartaki": "ナルタキ",
    "Gnome": "ノーム",
    "Hanuman": "ハヌマーン",
    "Koborokuru": "コボロクル",
    "Menehune": "メネフネ",
    "Oni": "オニ",
    "Satyr": "サテュロス",
    "Nocturna": "ノクターナ",
    "Dryad": "ドリアード",
    "Wakyambi": "ワキャンビ",
    "Xapiri Thëpë": "シャピリ・テペ",
    "Fomori": "フォモール",
    "Giant": "ジャイアント",
    "Minotaur": "ミノタウロス",
    "Cyclops": "キュクロプス",
    "Formori": "フォモール",
    "Ghoul": "グール",
    # spell categories (glossary lang.*Spells minus the 呪文 suffix used elsewhere)
    "Combat": "戦闘",
    "Detection": "探知",
    "Health": "身体",
    "Illusion": "幻影",
    "Manipulation": "操作",
    # skill groups / common category corrections vs glossary
    "Body": "強靱力",          # attribute category kanji fix (靭 -> 靱)
    "Attributes": "能力値",
    "Resonance": "共振力",
    # metatype categories — chumJA's SR4 "ヒト" is wrong for SR5
    "Metahuman": "メタヒューマン",
    "Metavariant": "メタバリアント",
    # knowledge-skill categories — match frontend KNOW_CAT_JA (constants.ts)
    "Academic": "学術",
    "Interest": "趣味",
    "Language": "言語",
    "Professional": "職業",
    "Street": "街",
    # --- Phase 2b: hand translations, glossary-checked -----------------------
    # skill groups still on English fallback (SR5 official JP).
    # "Biotech" collides with a gear category; the skill-group sense wins.
    "Acting": "演技",
    "Athletics": "運動",
    "Biotech": "医療",
    "Close Combat": "近接戦闘",
    "Conjuring": "召喚",
    "Cracking": "クラッキング",
    "Electronics": "エレクトロニクス",
    "Enchanting": "付術",
    "Outdoors": "野外",
    "Sorcery": "魔術",
    "Tasking": "タスキング",
    # remaining playable metavariants
    "Hobgoblin": "ホブゴブリン",
    "Ogre": "オーガ",
    "Fomorian": "フォモリアン",
    # derived-value pseudo-entity + a category shown via tr() (glossary lang.*)
    "Acceleration": "加速値",
    "Services": "助力",
    # --- Phase 2b batch 2: high-visibility sheet entities ------------------
    # Only entries with an established / unambiguous JP form. Spells are left
    # for a rulebook pass (they use a 漢字/カタカナ dual format).
    #
    # sprites (house style: "X・スプライト", cf. Courier/Data Sprite)
    "Companion Sprite": "コンパニオン・スプライト",
    "Generalist Sprite": "ジェネラリスト・スプライト",
    # elemental spirits — hermetic aliases of the already-translated Spirit of X
    "Air Elemental": "大気のエレメンタル",
    "Earth Elemental": "大地のエレメンタル",
    "Fire Elemental": "火のエレメンタル",
    "Water Elemental": "水のエレメンタル",
    # magic arts (house style: technique arts take a 術 suffix, cf. 浄化術/擬態術)
    "Necromancy": "死霊術",
    "Divination": "占術",
    "Exorcism": "祓魔術",
    "Advanced Alchemy": "上級錬金術",
    "Advanced Spellcasting": "上級呪文行使",
    "Advanced Ritual Casting": "上級儀式行使",
    "Blood Magic": "血の魔術",
    # traditions — plain religion/culture names (bracketed variants left as-is)
    "Buddhism": "仏教",
    "Hinduism": "ヒンドゥー教",
    "Islam": "イスラム教",
    "Zoroastrianism": "ゾロアスター教",
    "Druid": "ドルイド",
    "Vodou": "ヴォドゥン",
    # mentor spirits — plain animals (kanji, cf. 熊/狼/蛇) and archetypes
    "Monkey": "猿",
    "Whale": "鯨",
    "Dove": "鳩",
    "Stag": "牡鹿",
    "Squirrel": "リス",
    "Badger": "アナグマ",
    "Groundhog": "ウッドチャック",
    "Eurasian Jay": "カケス",
    "Death": "死",
    "War": "戦争",
    "Moon": "月",
    "Tide": "潮",
    "Green Man": "グリーンマン",
    "Wild Hunt": "ワイルドハント",
    "Berserker": "バーサーカー",
    "Peacemaker": "ピースメーカー",
    "Oracle": "オラクル",
    "Artist": "芸術家",
    "Smith": "鍛冶師",
    "Gambler": "賭博師",
    "Goddess": "女神",
    "Architect": "建築家",
    "Treasure Hunter": "トレジャーハンター",
    "Brother in Arms": "戦友",
    "Little Red Riding Hood": "赤ずきん",
    "Guanyin": "観音",
    "German Shepherd": "ジャーマン・シェパード",
    "Doberman": "ドーベルマン",
    "Weimaraner": "ワイマラナー",
}

# bulk hand translations live in their own modules to keep this file lean.
try:
    from scripts.ja_curated_spells import SPELLS as _SPELLS
    from scripts.ja_curated_entities import ENTITIES as _ENTITIES
except ImportError:  # when run as `python backend/scripts/import_ja_from_refs.py`
    from ja_curated_spells import SPELLS as _SPELLS
    from ja_curated_entities import ENTITIES as _ENTITIES
CURATED.update(_SPELLS)
CURATED.update(_ENTITIES)

# chumJA category english -> skip when the SR4 term is stale / wrong for SR5.
CATEGORY_SKIP = {
    "Armor",  # keep vendored 防具 (category sense), not glossary 装甲 (the value)
    "Foci",   # SR5 official is フォーカス, not chumJA's 集束具 — needs a manual pass
}

# chumJA <name> matches to skip (wrong sense in SR4 -> SR5).
NAME_SKIP = {
    "Sioux",  # chumJA gives "スー語" (the language); here it is a nation/tradition
}


def load_chumja(path: Path) -> tuple[dict[str, str], dict[str, str]]:
    names: dict[str, str] = {}
    cats: dict[str, str] = {}
    root = ET.parse(path).getroot()
    for node in root.iter():
        nm = node.findtext("name")
        tr = node.findtext("translate")
        if nm and tr and nm.strip() and tr.strip() and JP_RE.search(tr):
            names.setdefault(nm.strip(), tr.strip())
    for cat in root.iter("category"):
        eng = (cat.text or "").strip()
        tr = (cat.get("translate") or "").strip()
        if eng and tr and JP_RE.search(tr):
            cats.setdefault(eng, tr)
    return names, cats


def catalog_names_and_categories() -> tuple[set[str], set[str]]:
    from app.data_loader import catalog

    cat = catalog()
    names: set[str] = set()
    cats: set[str] = set()

    def walk(obj: object) -> None:
        if isinstance(obj, dict):
            n = obj.get("name")
            if isinstance(n, str) and n.strip():
                names.add(n.strip())
            c = obj.get("category")
            if isinstance(c, str) and c.strip():
                cats.add(c.strip())
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)

    for key, value in cat.items():
        if key in {"translations", "ui_strings"}:
            continue
        walk(value)
    # skill groups are a plain list of strings, not dict rows
    for grp in (cat.get("skills") or {}).get("groups") or []:
        if isinstance(grp, str) and grp.strip():
            names.add(grp.strip())
    return names, cats


def is_japanese(existing: dict[str, str], vendored: dict[str, str], key: str) -> bool:
    for src in (existing, vendored):
        val = src.get(key)
        if val and JP_RE.search(val):
            return True
    return False


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--chumja", type=Path, default=DEFAULT_CHUMJA)
    ap.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    ap.add_argument("--write", action="store_true", help="write data.json + report")
    args = ap.parse_args(argv)

    from app.data_loader import load_translations

    existing: dict[str, str] = json.loads(OVERLAY.read_text(encoding="utf-8"))
    # vendored-only view: load_translations() merges the overlay, so subtract it.
    merged = load_translations()
    vendored = {k: v for k, v in merged.items() if existing.get(k) != v}

    app_names, app_cats = catalog_names_and_categories()
    cj_names, cj_cats = ({}, {})
    if args.chumja.exists():
        cj_names, cj_cats = load_chumja(args.chumja)
    else:
        print(f"warning: chumJA not found at {args.chumja}; curated only", file=sys.stderr)

    additions: dict[str, str] = {}
    prov: dict[str, str] = {}

    # 1) curated (only where relevant to the app and not already JP)
    for key, val in CURATED.items():
        if key in app_names or key in app_cats:
            if not is_japanese(existing, vendored, key) or existing.get(key) != val:
                if existing.get(key) != val:
                    additions[key] = val
                    prov[key] = "curated"

    # 2) chumJA exact name matches, app-relevant, still untranslated
    for key, val in sorted(cj_names.items()):
        if key in additions or key in NAME_SKIP:
            continue
        if key in app_names and not is_japanese(existing, vendored, key):
            additions[key] = val
            prov[key] = "chumJA(SR4) name"

    # 3) chumJA category matches
    for key, val in sorted(cj_cats.items()):
        if key in additions or key in CATEGORY_SKIP:
            continue
        if key in app_cats and not is_japanese(existing, vendored, key):
            additions[key] = val
            prov[key] = "chumJA(SR4) category"

    merged_overlay = dict(existing)
    merged_overlay.update(additions)
    ordered = {k: merged_overlay[k] for k in sorted(merged_overlay)}

    # provenance for the *whole* overlay (not just this run's additions), so the
    # report is meaningful even on an additive --no-reset run.
    def provenance_of(key: str) -> str:
        if key in prov:
            return prov[key]
        if key in CURATED:
            return "curated"
        if key in cj_names:
            return "chumJA(SR4) name"
        if key in cj_cats:
            return "chumJA(SR4) category"
        return "manual / prior"

    by_src: dict[str, list[tuple[str, str]]] = {}
    for k, v in ordered.items():
        by_src.setdefault(provenance_of(k), []).append((k, v))

    print(f"app entity names: {len(app_names)}  categories: {len(app_cats)}")
    print(f"existing overlay entries: {len(existing)}")
    print(f"new additions: {len(additions)}  |  overlay total: {len(ordered)}")
    for src, rows in sorted(by_src.items()):
        print(f"  {src}: {len(rows)}")

    if args.write:
        OVERLAY.write_text(
            json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        lines = [
            "# 翻訳インポートレポート",
            "",
            "**自動生成** — `backend/scripts/regen_ja.sh` (= `import_ja_from_refs.py --write`)。",
            "`data.json` の全エントリを出典別に一覧。curated (SR5・用語集照合済) と",
            "chumJA SR4 の完全一致のみ。アプリの catalog() が使う名前／カテゴリに限定。",
            "",
            f"- オーバーレイ合計: **{len(ordered)} 件**",
            "",
        ]
        for src, rows in sorted(by_src.items()):
            lines.append(f"## {src} ({len(rows)})")
            lines.append("")
            lines.append("| English | 日本語 |")
            lines.append("|---|---|")
            lines += [f"| {k} | {v} |" for k, v in sorted(rows)]
            lines.append("")
        args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"wrote {OVERLAY.relative_to(ROOT.parent)}")
        print(f"wrote {args.report.relative_to(ROOT.parent)}")
    else:
        for k, v in sorted(additions.items()):
            print(f"  + {k}  =>  {v}   [{prov[k]}]")
        print("\n(dry run — pass --write to apply)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
