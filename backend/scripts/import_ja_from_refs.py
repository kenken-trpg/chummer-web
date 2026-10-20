#!/usr/bin/env python3
"""Phase 2 of docs/plans/translation-plan.md — seed backend/data/ja_overrides/data.json.

Sources, newest-wins (see docs/plans/translation-plan.md):
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
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# external reference material — set JA_REF_DIR (default ~/Downloads) or pass --chumja
_REF_DIR = Path(os.environ.get("JA_REF_DIR") or (Path.home() / "Downloads"))
DEFAULT_CHUMJA = _REF_DIR / "chumJA_20130129/lang/ja_data.xml"
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
    # Metavariants are deliberately absent. Every one of them is Run Faster's,
    # and the project shows Run Faster entries under their English names —
    # the katakana forms here were transliterations, not an established
    # Japanese rendering anyone could look up. The five core metatypes above
    # stay translated; they are SR5 core and the glossary carries them.
    # 収束具, settling the "needs a manual pass" note this category carried:
    # chumJA's SR4 集束具 and the loanword フォーカス were both in use.
    "Foci": "収束具",
    "Living Focus": "生体収束具",  # chumJA gives 生体集束具
    "Power Point": "パワー・ポイント",  # the metamagic, core rulebook p.332; upstream has パワーポイント
    # vehicle modification, core rulebook p.467 (Japanese edition; Chummer's
    # p.461 is the English one); upstream has リガーインターフェイス
    "Rigger Interface": "リガー・コマンド・インターフェース",
    # active-skill categories, as the core rulebook heads them (chumJA has
    # 戦闘能動 and the like); the sheet's headings say the same
    "Combat Active": "戦闘系能動技能",
    "Physical Active": "身体系能動技能",
    "Social Active": "社交系能動技能",
    "Magical Active": "魔法系能動技能",
    "Resonance Active": "共振力系能動技能",
    "Technical Active": "技術系能動技能",
    "Vehicle Active": "ヴィークル系能動技能",
    # spell categories (glossary lang.*Spells minus the 呪文 suffix used elsewhere)
    "Combat": "戦闘",
    "Detection": "探知",
    "Health": "身体",
    "Illusion": "幻影",
    "Manipulation": "操作",
    # skill groups / common category corrections vs glossary
    "Body": "強靱力",  # attribute category kanji fix (靭 -> 靱)
    # the Social limit, as an armor's wireless bonus names it; core rulebook
    # term (社交リミット). It sat in the Run & Gun table while the worksheet
    # counted that reference as one of RG's items.
    "Social": "社交",
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
    # The overlay's one hand-added entry, from before these modules existed.
    # Curated here so `regen_ja.sh` (which resets data.json) keeps it: the
    # vendored file leaves "BTLs" untranslated, and it is a gear/drug category
    # as well as a knowledge skill.
    "BTLs": "BTLチップ",
    # --- rulebook titles (the settings picker's "ルールブックを選ぶ" list) -------
    # Only books with a published Japanese edition, titled as that edition is.
    # The other 61 stay on English fallback for the same reason supplement gear
    # does: a transliterated title is a guess, and the code in brackets beside
    # it already identifies the book for anyone who owns the English one.
    "Shadowrun 5th Edition": "シャドウラン 第5版",
    "Run and Gun": "ラン＆ガン",
    # --- one reading for a name the catalog uses in two senses ---------------
    # "Mundane" is both the priority table's talent (a character with no magic
    # at all) and the category of non-magical critter powers, and the table is
    # keyed by English name alone, so one reading has to serve both. The
    # glossary's マンディン wins because it is the only one anybody sees: a
    # critter power reaches the client as name/type/action/range/duration and
    # its category is never served (`CritterPower` in
    # frontend/lib/types/rows/magic.ts has no `category` field), while the
    # talent is a cell every player picks from at creation. chumJA's 通常生物
    # would have put "ordinary creature" in that cell. If a picker grouped by
    # critter-power category is ever added, マンディン reads acceptably there
    # as an adjective — but that is the moment to look at this again.
    "Mundane": "マンディン",
}

# bulk hand translations live in their own modules to keep this file lean.
try:
    from scripts.ja_books import BOOKS as _BOOKS
    from scripts.ja_curated_entities import ENTITIES as _ENTITIES
    from scripts.ja_curated_spells import SPELLS as _SPELLS
except ImportError:  # when run as `python backend/scripts/import_ja_from_refs.py`
    # same modules by their other name; mypy only ever sees the branch above
    from ja_books import BOOKS as _BOOKS  # type: ignore[no-redef]
    from ja_curated_entities import ENTITIES as _ENTITIES  # type: ignore[no-redef]
    from ja_curated_spells import SPELLS as _SPELLS  # type: ignore[no-redef]
#: Which hand-kept table each CURATED entry came from, for the report. Kept in
#: step with CURATED: the later table wins both the value and the origin.
ORIGIN: dict[str, str] = dict.fromkeys(CURATED, "import_ja_from_refs.CURATED")
CURATED.update(_SPELLS)
ORIGIN.update(dict.fromkeys(_SPELLS, "ja_curated_spells.SPELLS"))
CURATED.update(_ENTITIES)
ORIGIN.update(dict.fromkeys(_ENTITIES, "ja_curated_entities.ENTITIES"))


def _book_terms() -> dict[str, tuple[str, str]]:
    """Every book pass's verified table, merged in registry order.

    Last, because these are the only entries somebody has read in print: they
    outrank the community translation upstream shipped for the same names. A
    book whose pass has not started has no module yet, which is not an error.
    """
    import importlib

    out: dict[str, tuple[str, str]] = {}
    for book in _BOOKS.values():
        for candidate in (f"scripts.{book.module}", book.module):
            try:
                module = importlib.import_module(candidate)
            except ImportError:
                continue
            origin = f"{book.module}.{book.table}"
            out.update({k: (v, origin) for k, v in getattr(module, book.table, {}).items()})
            break
    return out


for _key, (_val, _origin) in _book_terms().items():
    CURATED[_key] = _val
    ORIGIN[_key] = _origin

# chumJA category english -> skip when the SR4 term is stale / wrong for SR5.
CATEGORY_SKIP = {
    "Armor",  # keep vendored 防具 (category sense), not glossary 装甲 (the value)
    # chumJA gives 通常生物, which reads right for the critter-power category
    # (non-magical powers) and wrong for the other "Mundane" in the catalog:
    # the priority table's talent, where it means a character with no magic at
    # all and the glossary says マンディン. The translation table is keyed by
    # English name alone and cannot tell the two apart, so the reading is
    # decided once, below, in favour of the priority table — see CURATED.
    # The skip stays so the decision is only in one place.
    "Mundane",
}

# chumJA <name> matches to skip (wrong sense in SR4 -> SR5).
NAME_SKIP = {
    "Sioux",  # chumJA gives "スー語" (the language); here it is a nation/tradition
    "Centaur",  # untranslated Run Faster; retain the upstream English name
    "Medic",  # chumJA's 修復 is an SR4 item; here a Data Trails A.I. program, kept English
    "Miracle Shooter",  # chumJA's is an SR4 item; here a life module of the same name
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


#: Report section order: the tables a human checked against print first.
_SECTION_ORDER = ("ja_curated_", "import_ja_from_refs.", "chumJA")


def _section_rank(src: str) -> tuple[int, str]:
    if src.startswith("ja_curated_") and not src.startswith(("ja_curated_spells", "ja_curated_entities")):
        return (0, src)  # a book pass
    return (1 + next((i for i, p in enumerate(_SECTION_ORDER) if src.startswith(p)), len(_SECTION_ORDER)), src)


def _report(ordered: dict[str, str], by_src: dict[str, list[tuple[str, str]]], vendored: dict[str, str]) -> str:
    """docs/translation-import-report.md: every overlay entry by origin, with
    the kinds and books its name lands on, then the per-book picture."""
    from app.catalog_view import public_catalog
    from app.data_loader import reset_catalog

    try:
        from scripts import ja_provenance as prov
    except ImportError:  # run as `python backend/scripts/import_ja_from_refs.py`
        import ja_provenance as prov  # type: ignore[no-redef]

    # The catalog was loaded before data.json was written — under regen_ja.sh,
    # from an emptied one — so read it again: the report describes the result.
    # Book titles are translations too (Run and Gun's ラン＆ガン is an overlay
    # entry), and the Japanese-edition test reads them.
    reset_catalog()
    public = public_catalog()
    books = public.get("books") or []
    printed = prov.ja_books(books)
    found = prov.carriers(public, printed)
    shown = public.get("translations") or {}
    titles = {b["code"]: b["name"] for b in books}

    def where(name: str) -> str:
        c = found.get(name)
        return c.render() if c else "—"

    lines = [
        "# 翻訳インポートレポート",
        "",
        "**自動生成** — `backend/scripts/regen_ja.sh` (= `import_ja_from_refs.py --write`)。",
        "画面の日本語名は 3 つの層から来る。上流 Chummer の `ja-jp_data.xml`、その上に重ねる",
        "`data.json`、最後にまだ英語の名前にだけ当てるシャドウラン・コデックスの名前",
        "（`app/data_loader/codex.py`）。ここに載るのは `data.json` の全エントリで、出どころの表ごとに分けてある。",
        "訳の表は英語名だけで引くので、「品目」の列には、その名前を持つ品目の種類と本をすべて並べる。",
        "",
        f"- オーバーレイ合計: **{len(ordered)} 件**",
        f"- 日本語版のある本: {', '.join(sorted(printed))}（コデックスが再録した品目も日本語版ありと数える）",
        "",
    ]

    orphans = sorted(
        (k, v, src)
        for src, rows in by_src.items()
        if not src.startswith("chumJA")
        for k, v in rows
        if k in found and not found[k].printed_ja and found[k].books()
    )
    lines += [
        f"## 日本語版の無い品目にだけ当たる自前の訳 ({len(orphans)})",
        "",
        "サプリの用語は英語のままにする方針（本に無い片仮名を作らない）と食い違う候補。",
        "chumJA（SR4 の訳）は別に数える。",
        "",
        "| English | 日本語 | 出どころ | 品目 |",
        "|---|---|---|---|",
        *(f"| {k} | {v} | {src} | {where(k)} |" for k, v, src in orphans),
        "",
    ]

    for src in sorted(by_src, key=_section_rank):
        rows = by_src[src]
        lines += [f"## {src} ({len(rows)})", "", "| English | 日本語 | 品目 |", "|---|---|---|"]
        lines += [f"| {k} | {v} | {where(k)} |" for k, v in sorted(rows)]
        lines.append("")

    counts = prov.per_book(found, ordered, vendored, shown)
    lines += [
        "## 本ごとの訳の出どころ",
        "",
        "名前の数。1 つの名前が複数の本に載っていれば、それぞれの本で数える。",
        "",
        "| 本 | 書名 | 日本語版 | 上流 | data.json | コデックス | 英語のまま |",
        "|---|---|---|---|---|---|---|",
    ]
    for code in sorted(counts, key=lambda c: (-sum(counts[c].values()), c)):
        n = counts[code]
        lines.append(
            f"| {code} | {titles.get(code, '')} | {'あり' if code in printed else ''} "
            f"| {n['upstream']} | {n['overlay']} | {n['codex']} | {n['english']} |"
        )
    lines.append("")
    return "\n".join(lines) + "\n"


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
    cj_names: dict[str, str] = {}
    cj_cats: dict[str, str] = {}
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
                    prov[key] = ORIGIN[key]

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
    # Remove the old SR4 rendering even on an additive --no-reset run.
    merged_overlay.pop("Centaur", None)
    merged_overlay.update(additions)
    ordered = {k: merged_overlay[k] for k in sorted(merged_overlay)}

    # provenance for the *whole* overlay (not just this run's additions), so the
    # report is meaningful even on an additive --no-reset run.
    def provenance_of(key: str) -> str:
        if key in prov:
            return prov[key]
        if key in CURATED:
            return ORIGIN[key]
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
        OVERLAY.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        args.report.write_text(_report(ordered, by_src, vendored), encoding="utf-8")
        print(f"wrote {OVERLAY.relative_to(ROOT.parent)}")
        print(f"wrote {args.report.relative_to(ROOT.parent)}")
    else:
        for k, v in sorted(additions.items()):
            print(f"  + {k}  =>  {v}   [{prov[k]}]")
        print("\n(dry run — pass --write to apply)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
