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
    store.py            persistence + public_catalog() shaping for the UI
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

`mypy` runs in CI but is non-blocking; new modules are welcome to be strict.
The ruleset is deliberately modest — grow it in a focused PR rather than
turning everything on at once.

**Frontend** — `eslint` (flat config) + `prettier` + `tsc`:

```bash
cd frontend && npm run check   # typecheck + lint + format:check + build
```

Some pre-existing `no-unused-vars` / `exhaustive-deps` / `no-explicit-any`
findings are demoted to warnings so CI is green. **Turning a warning into a
clean fix is a great first contribution** — keep such PRs small and scoped to
one rule or one directory.

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
- No account system, no server-side multi-user state. One process, local JSON.
- Data is never committed: `backend/vendor/` (Chummer data) and
  `backend/saves/` (your characters) are gitignored.
