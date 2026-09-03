# Contributing

Thanks for helping out! This is an unofficial, fan-made Shadowrun 5e character
builder. Game data and translations come from
[chummer5a/chummer5a](https://github.com/chummer5a/chummer5a) (GPL-3.0); this
project is GPL-3.0 too.

## TL;DR

```bash
make setup     # venv + npm install
make data      # download Chummer game data into backend/vendor/ (gitignored)
make dev-backend    # API on :8000     (separate terminal)
make dev-frontend   # UI  on :3000     (separate terminal)
make check     # everything CI runs: ruff, pytest, tsc, eslint, prettier, build
```

No `make`? Every target is a one-liner you can read off the `Makefile`.

## Repository layout

```
backend/                FastAPI + the rules engine (Python 3.11+)
  app/
    main.py             HTTP routes (thin; delegates to store/engine)
    models.py           Pydantic models: CharacterState, CharacterPatch, installs
    data_loader.py      Parse vendored Chummer XML -> cached catalog() dict
    engine.py           compute(state) -> state.derived  (the rules live here)
    improvements.py     the <bonus> node vocabulary (apply_bonus_nodes)
    store.py            pure new/patch/compute helpers + public_catalog() shaping
    chummer_import.py   .chum5 / .chum5lz  ->  CharacterState
    chummer_export.py   CharacterState     ->  .chum5 XML
  scripts/fetch_chummer_data.py   downloads Chummer/data + lang files
  tests/                          pytest
  data/ja_overrides/              git-tracked JP translation overlay
frontend/               Next.js 15 (App Router) + React 19 + TypeScript
  app/page.tsx          top-level editor shell + state/patch plumbing
  components/character/  sidebar, shared pickers, tabs/ (one file per tab)
  lib/                   api client, types, cocofolia export, helpers
docs/                   architecture, data pipeline, "how to add a rule"
```

Read [`docs/architecture.md`](docs/architecture.md) before a first non-trivial
change, and [`docs/adding-rules.md`](docs/adding-rules.md) for step-by-step
recipes (new `<bonus>` tag, new gear category, new sheet section, …).

## Coding standards

**Backend** — `ruff` for lint + format (config in `backend/pyproject.toml`):

```bash
cd backend && ruff check . && ruff format . && python -m pytest -q
```

`mypy` is clean and **blocking** (CI + `make check`), and now strict across
the whole `app` package (`disallow_untyped_defs`, `warn_return_any`, …). New
code needs full annotations; see `docs/plans/refactor-mypy-plan.md` for how it
got there.

The backend tests come in two layers:

- **`tests/test_engine.py`** — hundreds of targeted assertions, one rule each.
  Copy the nearest existing test when you add or change a rule.
- **`tests/test_snapshot.py`** — golden snapshots of the whole `derived` blob
  for five representative characters (samurai / mage / adept / technomancer /
  rigger). They catch a refactor that silently drops, renames, or reorders part
  of the payload where no targeted test looks. Instance UUIDs are scrubbed to
  `#N` tokens so runs are deterministic. After an **intentional** change to the
  engine output, regenerate and eyeball the diff:

  ```bash
  cd backend && UPDATE_SNAPSHOTS=1 python -m pytest -q tests/test_snapshot.py
  ```

**Frontend** — `eslint` (flat config) + `prettier` + `tsc` + `vitest`:

```bash
cd frontend && npm run check   # typecheck + lint + format:check + test
npm run test                   # vitest (jsdom + React Testing Library)
```

Tests live next to the code (`*.test.ts` / `*.test.tsx`) with shared
fixtures in `frontend/tests/fixtures.ts` (`makeCharacter` / `makeCatalog`).
`eslint` is clean and blocking, including `no-explicit-any` (the source is
`any`-free; test files may still cast fixtures). `no-unused-vars` stays a
warning, with `_`-prefixed names exempt.

### Accessibility

`eslint-plugin-jsx-a11y`'s recommended set is on and blocking. The house rules:

- **A `<label>` wraps its control.** No `htmlFor`/`id` plumbing — the
  association is structural and cannot drift. When the text heads a *group*
  rather than one control, use `.field-label` on a heading instead; a `<label>`
  pointing at nothing is what the lint rule is there to catch.
- **A control with no visible label needs `aria-label`.** `placeholder` and
  `title` are not labels. Search boxes carry the placeholder text again as
  `aria-label`.
- Landmarks: one `<main id="main">` per page, a `<header>` for the chrome, the
  sidebar is an `<aside>`, the tab bar is a named `<nav>` with `aria-current`
  on the active tab. There is a skip link ahead of the toolbar.
- Focus is styled with `:focus-visible`; never `outline: none`.

Assert accessible names by **role + name** in tests (`getByRole("combobox",
{ name: … })`), not by class or DOM order — that way a dropped label fails a
test instead of passing silently.

Not done yet: the per-row `<select>` pickers in the gear and quality tabs
(slot / ammo / extra) still have no accessible name of their own — they read as
bare "combobox". They need a name built from the row they belong to.

### Coverage

```bash
make coverage            # both, or coverage-backend / coverage-frontend
```

**Nothing gates on the number** and there is no `fail_under` — the point is to
see *which* modules the suite never enters. At the time of writing the backend
is ~91% and the frontend ~49% of statements (the gap is components: the pure
`lib/` helpers are well covered, the tab UIs much less). HTML reports land in
`backend/htmlcov/` and `frontend/coverage/`, both gitignored. CI prints the
summary in the log — backend on 3.13 only, since the matrix would repeat it.

A PR that lowers coverage is fine if it is the right change; a PR that adds a
new module with no test at all is worth a second look.

## Commits & PRs

- One logical change per commit; keep formatting-only churn in its own commit
  (and add its hash to `.git-blame-ignore-revs`).
- Conventional-ish prefixes: `feat:`, `fix:`, `refactor:`, `chore:`, `docs:`,
  `style:`, `test:`. A scope is nice: `feat(engine): …`.
- Every PR must pass `make check` locally. Add or update tests for rule
  changes — `backend/tests/test_engine.py` has lots of patterns to copy.
- Rules changes should cite the SR5 (or supplement) page, and match what
  Chummer does when the books are ambiguous — Chummer is the reference
  implementation this project chases.

## Translations

Japanese is the primary UI language. Terminology is enforced by
`backend/tests/test_terminology.py`. Core-rulebook content is translated;
supplement content stays in English. See `docs/translation-*` and
`backend/data/ja_overrides/`.

## Scope / non-goals

- Not a play aid first — it's a **builder**. Play-time helpers (condition
  monitor tracking, expense ledger) are welcome but secondary.
- No account system, no server-side state. The backend only computes /
  transforms; characters live in the browser (IndexedDB), exported as
  `.json` / `.chum5` when you want a file.
- Data is never committed: `backend/vendor/` (Chummer data) is gitignored.
