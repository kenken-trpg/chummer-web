# Plan: frontend test harness (Vitest + RTL)

Working doc. The frontend has **no tests** — `tsc --noEmit` + `next build`
are the only guards, so a render regression (a section not wired, a bad
prop) ships silently. This sets up the harness + a first layer of tests so
the remaining frontend splits (`CharacterSidebar` 760, `QualitiesTab` 635,
`VehicleDroneGear` 631, `page.tsx` 610) have a safety net.

## Stack

- **Vitest** (`vitest`, `@vitejs/plugin-react`, `jsdom`) — fast, ESM-native,
  Jest-compatible API, first-class Vite/TS path-alias support.
- **@testing-library/react** (v16, React 19 compatible) + `@testing-library/dom`.
- `vitest.config.ts`: `environment: "jsdom"`, `plugins: [react()]`,
  `resolve.alias { "@": __dirname }` (mirror `tsconfig` `paths`),
  `globals: true` so `describe/it/expect` need no import.

## Files

```
frontend/
  vitest.config.ts
  tests/
    fixtures.ts            # makeCharacter() / makeCatalog() / identityTr — a
                           #   fully-typed minimal Character (complete `derived`,
                           #   empty arrays, zero scalars) + overrides merge
  lib/character/
    sheet-format.test.ts   # rangeRow, specialArmorBits, lifeIncrement, rangeNameFor
    format.test.ts         # matrixCM, vehicleCM, cfDuration/cfTarget, formatPoints,
                           #   leadInt, formatAccessoryCost, formatAmmoCost, mergeRatings
    sheet-data.test.ts     # buildSheetData: gear bucket split (misc / drugs / sins),
                           #   parent-id filter for cyber/bio, activeSkills filter+sort
  components/
    CharacterSheet.test.tsx  # smoke — see below
```

### `CharacterSheet.test.tsx`

- **empty fixture** (`makeCharacter()`): renders `layout="standard"` /
  `"compact"` / `"text"` without throwing; the `コア` section heading is
  present; sections with no data (`資質`, `戦闘`, `武道`, …) are absent
  (`<Section empty>` → null).
- **populated fixture** (`makeCharacter({ derived: { weapons: [w], qualities: [q], … } })`):
  the `戦闘` / `資質` headings now appear; `tr` is called with the item name.
- assert on `container.textContent` / `screen.getByRole("heading", …)` —
  **not** a full HTML snapshot (too brittle for a first test; a snapshot can
  come later once `toMatchSnapshot` is wired).

## Wiring

- `package.json`: `"test": "vitest run"`, and `check` becomes
  `npm run typecheck && npm run lint && npm run format:check && npm run test && npm run build`.
- `Makefile` `check-frontend`: add `&& npm run test` before `&& npm run build`.
- `eslint.config.mjs`: nothing special — test files lint like the rest
  (`vitest/globals` types via `vitest.config.ts` `types` or a
  `tests/vitest.d.ts` triple-slash). If `no-explicit-any` bites the fixture
  builder, a file-level disable there is fine (mirrors `blocks.tsx`).
- `tsconfig.json`: add `"vitest/globals"` to `compilerOptions.types` (or a
  `d.ts`), and make sure `tests/**` is covered by `include` (it already is
  via `**/*.ts`).
- `.gitignore` / prettier: `coverage/` ignored; test files are prettier-checked.
- `docs/architecture.md`: note the harness under a new item; CONTRIBUTING
  gets a `npm run test` line.

## Commits

1. **harness** — deps, `vitest.config.ts`, `tsconfig` types, `tests/fixtures.ts`,
   one trivial `sanity.test.ts` (`expect(1+1).toBe(2)`), wire `package.json` /
   `Makefile`. `make check` green with the empty suite.
2. **helper unit tests** — `sheet-format.test.ts`, `format.test.ts`,
   `sheet-data.test.ts`.
3. **`CharacterSheet.test.tsx`** smoke (empty + populated fixtures).
4. **docs** — architecture.md + CONTRIBUTING.

## Verification per commit

```
cd frontend && npm run typecheck && npm run lint && npm run format:check && npm run test && npm run build
```

---

## Done

Executed in session `session_014XsGWooKn7vH58HZzP3nMJ`. Frontend went from
**0 tests** to **5 files / 29 tests**, wired into `make check` + CI.

| commit | what |
| --- | --- |
| `ad12221` | harness — vitest / RTL / jsdom deps, `vitest.config.mts`, `tsconfig` `types`, `tests/fixtures.ts` (`makeCharacter` / `makeCatalog`, tsc-validated against the real types), `npm run test` in `check` / `Makefile` / CI |
| `04c7c7c` | unit tests — `sheet-format` (`rangeRow` / `specialArmorBits` / …), `format` (`matrixCM` / `cfDuration` / …), `sheet-data` (`buildSheetData` bucket + skill logic) |
| `4e2d0b5` | `CharacterSheet.test.tsx` smoke — empty / compact / text layouts, section-appears-with-data |
| _this_ | docs — `architecture.md` Frontend section, `CONTRIBUTING.md` |

Deviations from the plan:

- `vitest.config.ts` → `.mts` (the frontend `package.json` has no
  `"type": "module"`, so Vite's native config loader warned about ESM in a
  CJS file). eslint ignores `*.config.mts` alongside `*.config.mjs`.
- `npm run check` = typecheck + lint + format + **test** (no `build` — the
  Makefile's `check-frontend` adds it, matching the pre-existing split).
- The smoke test asserts on headings / roles / `container` queries, not a
  full HTML `toMatchSnapshot` — a snapshot is easy to add later now the
  harness exists, but is too brittle as the first test.
