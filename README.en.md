*[日本語版はこちら / Japanese version](README.md)*

# Chummer Web

An unofficial Shadowrun 5th Edition character creator for the browser. Not affiliated with Catalyst Game Labs or The Topps Company.

Game data and the base translations come from [chummer5a/chummer5a](https://github.com/chummer5a/chummer5a) (GPL-3.0) — its `Chummer/data` and `Chummer/lang` trees. This project is GPL-3.0 as well. The Japanese terminology overlay in `backend/data/ja_overrides/` is mostly hand-translated against the SR5 glossary, with some proper nouns from chumJA (Chummer's SR4-era Japanese translation) and terms cross-checked against [shadowrun5eja](https://github.com/MiyabiRouga/shadowrun5eja) (a Japanese localisation for Foundry VTT's SR5e system). See [`NOTICE.txt`](NOTICE.txt) for the full attribution.

**Characters are stored in your browser (IndexedDB).** The server only computes derived values and converts `.chum5` files; it never stores a character. Export to JSON or `.chum5` to keep a backup.

## A note on language

The interface ships in Japanese and English, switchable in the top bar. Japanese is the reference locale — it is the one that is complete.

In English you get the app's own copy (tabs, buttons, panels, the character sheet including its print layout) plus catalog entries under their original English names, since the Chummer data files are English and the Japanese translation is an overlay on top. **Two things are still Japanese in English mode:**

- **The creation-check panel.** Its validation messages come from the rules engine, which emits Japanese. Translating the frontend labels alone would leave each label sitting next to a Japanese sentence, so they are deliberately left together until the backend messages move too.
- **The Cocofolia export**, on purpose — Cocofolia is a Japanese VTT and the exported piece is pasted into a Japanese table's room.

[`docs/i18n.md`](docs/i18n.md) explains the two string layers and how to add a locale.

## Running it (Docker)

Docker (Docker Desktop or equivalent) is the only requirement.

```bash
git clone https://github.com/kenken-trpg/chummer-web.git
cd chummer-web
cp .env.example .env      # optional — to change ports or limits
make up                   # → http://localhost:8080
```

`make up` pulls the published image (`ghcr.io/kenken-trpg/chummer-web`) if one is available and builds locally otherwise. Without `make`, `docker compose up` works too — the first build takes a few minutes.

| Command | What it does |
|---|---|
| `make up` | Start it (`http://localhost:8080`) |
| `make down` | Stop it |
| `make logs` | Follow the logs |
| `make update` | `git pull`, refresh the image, restart |
| `make doctor` | Pre-flight check (Docker, free ports, …) |

The Chummer game data is fetched at image build time and bundled, pinned to a specific upstream commit — so running the container needs no network access.

## Running it without Docker (for development)

Python 3.11+ and Node 20.12+. On Windows, Docker is the easier path.

```bash
make setup       # backend venv + npm install
make data        # fetch the Chummer game data into backend/vendor/ (gitignored)
make dev         # API on :8000 and the Next dev server on :3000; Ctrl-C stops both
```

Then open http://localhost:3000. Without `make`, each target is a one-line command in the `Makefile`.

## Importing `.chum5`

Chummer5a saves (`.chum5` and `.chum5lz`) can be imported. This is best-effort: anything the catalog cannot resolve is skipped and listed for you after the import. If a `.chum5lz` will not decompress, re-save it uncompressed as `.chum5` from Chummer.

## Tests and checks

```bash
make check       # the same as CI: ruff / pytest / mypy / tsc / eslint / prettier / build
```

## Layout and developer docs

```
backend/    FastAPI + the rules engine (compute() in app/engine/compute is the core). Stateless
frontend/   Next.js 15 App Router + React 19. Characters live in IndexedDB
deploy/     Caddyfile + supervisord.conf (the in-container process layout)
docs/       Architecture, data pipeline, deployment, how to add a rule
```

- [`CONTRIBUTING.md`](CONTRIBUTING.md) — setup, conventions, how to open a PR
- [`SECURITY.md`](SECURITY.md) — reporting a vulnerability (GitHub private vulnerability reporting)
- [`docs/architecture.md`](docs/architecture.md) — data flow, `<bonus>` nodes and `effects`, the API surface
- [`docs/deploy.md`](docs/deploy.md) — Docker, Cloud Run / Fly, or self-hosting behind a Cloudflare Tunnel
- [`docs/adding-rules.md`](docs/adding-rules.md) — recipes for a new modifier, item field, tab or validation
- [`docs/data-pipeline.md`](docs/data-pipeline.md) — fetch → vendor → translation overlay
- [`docs/i18n.md`](docs/i18n.md) — the two UI-string layers and how to add a locale (written in Japanese)
- [`docs/share-link.md`](docs/share-link.md) — the read-only share link (`/share#c=…`): format and validation
- [`docs/plans/`](docs/plans/) — working notes from refactors that have already landed (history, not current state)

Most of the documentation under `docs/` is written in Japanese; the code, comments and commit messages are in English.

Contributions are welcome. For a rules change, cite the SR5 page number (or the supplement), and where the book is ambiguous, match Chummer5a's behaviour.
