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
    main.py             HTTP routes (thin; delegates to characters/catalog_view)
    models.py           Pydantic models: CharacterState, CharacterPatch, installs
    characters.py       pure new / patch / compute / import (no storage)
    catalog_view.py     public_catalog(): the catalog projected for the UI
    data_loader/        parse vendored Chummer XML -> cached catalog() dict
    engine/             compute(state) -> state.derived  (the rules live here)
    improvements/       the <bonus> node vocabulary (apply_bonus_nodes)
    chummer_import.py   .chum5 / .chum5lz  ->  CharacterState
    chummer_export.py   CharacterState     ->  .chum5 XML
  scripts/fetch_chummer_data.py   downloads Chummer/data + lang files
  tests/                          pytest
  data/ja_overrides/              git-tracked JP translation overlay
frontend/               Next.js 15 (App Router) + React 19 + TypeScript
  app/page.tsx          top-level editor shell + state/patch plumbing
  app/share/            read-only share view (state rides in the URL fragment)
  components/character/  sidebar, shared pickers, tabs/ (one file per tab)
    CatalogPicker.tsx    chips + search + truncated list; PickerList/Footnote
    AddonSelect.tsx      the per-row "pick a mod, press 装着" pair
  lib/                   api client, types, i18n, cocofolia export, helpers
  lib/character/         editor hook, IndexedDB store, sheet + share codecs
docs/                   architecture, data pipeline, "how to add a rule"
docs/plans/             working docs for refactors that already shipped
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

- **`tests/test_chummer_roundtrip*.py`** — `.chum5` import ⇄ export must be a
  fixed point: a character that has been through Chummer once must not change
  if it goes through again. The four hand-built scenarios name maybe eighty
  catalog entries between them; the `_property` file draws the character from
  the live catalog with Hypothesis instead, so a field only one weapon category
  sets is still reachable. Both share the XML builder in
  `tests/chum5_fixtures.py` (deliberately not named `test_*`, so pytest does
  not collect it). Hypothesis remembers failing examples in `backend/.hypothesis/`
  (gitignored) and replays them first, so a fix is verified against the case
  that actually broke.

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

### End-to-end

```bash
make e2e          # or: cd frontend && npm run test:e2e  (--ui to watch it)
```

Playwright, one Chromium, `frontend/e2e/*.spec.ts`. It builds the frontend and
starts `uvicorn` on 8100 / `next start` on 3100 itself — off the `make dev`
ports so it never drives a server you already had running. It needs
`backend/vendor` (`make data`); without it `/api/catalog` 503s.

Keep it to flows the unit suite **cannot** reach. In vitest, `lib/api` is
mocked, the local store is a `Map`, and jsdom has no IndexedDB — so anything
crossing browser storage or the Python engine for real belongs here, and
anything else belongs in a fast unit test. Two specs today: create → edit →
reload → `.chum5` export, and share-link → fragment → read-only view.

CI runs it on pushes to `main` and on tags, not on every PR push; the report is
uploaded as an artifact when it fails.

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

The per-row pickers (slot / ammo / extra) name themselves after the row they
belong to — `Ares Predator V: アクセサリを追加` — which is what
`<AddonSelect>` is for. Where a panel still writes its own `<select>`, give it
the same `aria-label={`${tr(row.name)}: …`}` shape.

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

## Releasing

1. Write the section in `CHANGELOG.md` (rename `[Unreleased]` to the version).
2. Bump the version in `backend/pyproject.toml` and `backend/app/main.py` —
   the latter is what the API reports at `/docs`.
3. `make release-check VERSION=0.2.0` — fails if either of the above is missing.
4. `git tag -a v0.2.0 -m v0.2.0 && git push origin v0.2.0`.

CI then builds and pushes `ghcr.io/…/chummer-web:0.2.0`, `:0.2` and `:latest`,
and publishes a GitHub Release whose notes are that CHANGELOG section. The tag
build is exempt from `cancel-in-progress`, so a release image is never
cancelled out from under you. `frontend/package.json` stays at whatever it is —
it is `"private": true` and never published.

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
