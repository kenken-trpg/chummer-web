# Plan: split `components/CharacterSheet.tsx` into per-section components

Working doc. Fifth in the refactor series, first on the frontend.
`docs/architecture.md` §"Planned refactors" item 3.

## Where we are

`components/CharacterSheet.tsx` was **1,155 lines**: ~55 lines of derived-data
massaging, a `layout === "text"` early return, then one `return (…)` with a
`<header>`, **18 `<Section>` blocks**, and a `<footer>`.

Every section closes over the same locals (`d`, `tr`, `t`, `totals`,
`enabled`, `activeSkills`, …) plus a few section-specific helpers imported
from `lib/character/*`.

**No frontend test suite.** The guard per commit is
`npm run check` (`tsc --noEmit` + `eslint` + `prettier --check`) **and**
`npm run build`. Extractions are pure JSX relocation — the risk is a typo,
which the typechecker + build catch.

## Approach

1. **`lib/character/sheet-data.ts`** (done, `e39e2ab`) — `buildSheetData()`
   returns a typed `SheetData` bundle (mirrors `textSheet(TextArgs)`).
2. **`components/character/sheet/sections/`** — one `*.tsx` per section,
   `export function XSection(s: SheetData)`, rendered as `<XSection {...s} />`.
   Section-specific helpers stay imported inside each section file.
3. **`components/character/sheet/SheetHeader.tsx`** — the `<header>` block.
4. `CharacterSheet.tsx` ends as: props, `buildSheetData`, the text branch,
   and `<article>` = `<SheetHeader {...s}/>` + the `<*Section {...s}/>` list
   + `<footer>`.

### Sections (source order)

| # | title | notes |
| --- | --- | --- |
| 1 | コア Core | attrs + limits + CM + init + movement |
| 2 | 技能 Skills | active + groups + exotic |
| 3 | 知識技能 Knowledge | |
| 4 | キャリア Career | conditional |
| 5 | 資質 Qualities | |
| 6 | アクションDP Action DP | conditional |
| 7 | 戦闘 Combat | ~175 lines — weapons + armor + ranges + recoil |
| 8 | ウェア Ware | cyber + bio |
| 9 | マトリクス Matrix | |
| 10 | 魔法 Magic | ~115 lines — adept / spells / spirits / foci |
| 11 | 共鳴 Resonance | complex forms / sprites / submersion |
| 12 | 武道 Martial | |
| 13 | コンタクト Contacts | |
| 14 | 車両・ドローン Vehicles | |
| 15 | ドラッグ／毒物 Drugs | |
| 16 | SIN／ライセンス SIN | |
| 17 | その他ギア Misc gear | |
| 18 | 記述 Description | IIFE |

### Commits

- **2** — Core, Skills, Knowledge, Career, Qualities, ActionDp
- **3** — Combat, Ware, Matrix
- **4** — Magic, Resonance, Martial, Contacts, Vehicles
- **5** — Drugs, Sin, MiscGear, Description + SheetHeader; CharacterSheet
  reduced to the shell
- **6** — docs

Each section commit: move the JSX verbatim into
`sections/<name>.tsx`, add `import type { SheetData }`, prefix the
section-local helper imports, wire it into `CharacterSheet.tsx`, run
`npm run check && npm run build`.

## Verification per commit

```
cd frontend && npm run typecheck && npm run lint && npm run format:check && npm run build
# expect: 0 errors; 3 pre-existing eslint warnings; build OK
```
