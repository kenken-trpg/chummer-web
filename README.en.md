_[日本語版はこちら / Japanese version](README.md)_

# Chummer Web

An unofficial Shadowrun 5th Edition character creator for the browser. Not affiliated with Catalyst Game Labs or The Topps Company.

Game data and the base translations come from [chummer5a/chummer5a](https://github.com/chummer5a/chummer5a) (GPL-3.0) — its `Chummer/data` and `Chummer/lang` trees. This project is GPL-3.0 as well. The Japanese terminology overlay in `backend/data/ja_overrides/` is mostly hand-translated against the SR5 glossary, with some proper nouns from chumJA (Chummer's SR4-era Japanese translation) and terms cross-checked against [shadowrun5eja](https://github.com/MiyabiRouga/shadowrun5eja) (a Japanese localisation for Foundry VTT's SR5e system). See [`NOTICE.txt`](NOTICE.txt) for the full attribution.

**Characters are stored in your browser (IndexedDB).** The server only computes derived values and converts `.chum5` files; it never stores a character. Export to JSON or `.chum5` to keep a backup.

## A note on language

The interface ships in Japanese and English, switchable in the top bar. Japanese is the reference locale — it is the one that is complete.

In English you get the app's own copy (tabs, buttons, panels, the character sheet including its print layout, and the creation-check messages) plus catalog entries under their original English names, since the Chummer data files are English and the Japanese translation is an overlay on top. The rules engine reports a key and its parameters rather than a sentence, so its wording lives in the frontend dictionary and follows the language switch.

**The Cocofolia export follows the UI language too**, but defaults to Japanese: Cocofolia is a Japanese VTT and the exported piece is pasted into a Japanese table's room. The dice commands themselves are BCDice syntax and read the same either way.

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

| Command       | What it does                             |
| ------------- | ---------------------------------------- |
| `make up`     | Start it (`http://localhost:8080`)       |
| `make down`   | Stop it                                  |
| `make logs`   | Follow the logs                          |
| `make update` | `git pull`, refresh the image, restart   |
| `make doctor` | Pre-flight check (Docker, free ports, …) |

The Chummer game data is fetched at image build time and bundled, pinned to a specific upstream commit — so running the container needs no network access.

## Putting it on the web (localhost + Cloudflare Tunnel)

How to publish an instance running on your own PC or server without opening any ports.
`cloudflared` connects out over 443 only, so there is nothing to configure on the router.

### 1. Run it on localhost

Start it as in "Running it (Docker)" above and check that http://localhost:8080 opens.
`compose.yaml` publishes the port on `127.0.0.1` only, so nothing on the LAN reaches it directly — only the tunnel does.

Before going public, put back the limits that are loosened for local use. In `.env`:

```bash
RATE_LIMIT=120/minute
IMPORT_RATE_LIMIT=20/minute
# leave TRUSTED_PROXY_HOPS at 0 (Cloudflare's cf-connecting-ip is used)
```

Run `make up` again to apply them.

### 2. Install cloudflared

```bash
brew install cloudflared            # macOS
# Linux / Windows: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
cloudflared --version
```

### 3a. Quick try: a temporary URL (no account needed)

```bash
cloudflared tunnel --url http://localhost:8080
```

The printed `https://<random>.trycloudflare.com` is the public URL. Ctrl-C stops it, and the
URL changes every run — good for sharing it for one session.

### 3b. Permanent: your own domain (needs a Cloudflare account and a domain)

This assumes the domain's DNS is on Cloudflare. Replace `chummer.example.com` with your hostname.

```bash
cloudflared tunnel login                                   # authenticate in the browser → ~/.cloudflared/cert.pem
cloudflared tunnel create chummer                          # prints the tunnel ID, writes ~/.cloudflared/<ID>.json
cloudflared tunnel route dns chummer chummer.example.com   # creates the DNS CNAME
```

Create `~/.cloudflared/config.yml` (replace `<ID>` and `<user>`):

```yaml
tunnel: <ID>
credentials-file: /Users/<user>/.cloudflared/<ID>.json   # /home/<user>/... on Linux
ingress:
  - hostname: chummer.example.com
    service: http://localhost:8080
  - service: http_status:404
```

```bash
cloudflared tunnel run chummer      # runs in the foreground → https://chummer.example.com
```

Once it works, have it start with the OS:

```bash
sudo cloudflared service install    # registers a service from config.yml (macOS: launchd / Linux: systemd)
```

The Linux systemd service reads `/etc/cloudflared/config.yml`, so copy `config.yml` and `<ID>.json` there
and fix the `credentials-file` path. The app itself is `restart: unless-stopped`, so it comes back with Docker.

### 4. Check and clean up

- `https://chummer.example.com/api/health` answering `{"ok":true}` means it is reachable.
- For a small group, put **Zero Trust → Access** (Cloudflare dashboard) in front of the hostname with a login (e.g. email one-time PIN). That removes anonymous access entirely.
- To stop: Ctrl-C `cloudflared` (or `sudo cloudflared service uninstall` if you installed the service), and `make down` for the app.
  To remove the tunnel for good, `cloudflared tunnel delete chummer` and delete the DNS CNAME.

Characters are stored in the browser, so publishing it does not leave any characters on the server.
See [`docs/deploy.md`](docs/deploy.md) for the environment variables and other deploy targets.

## Running it without Docker (for development)

Python 3.11+ and Node 22.12+ (CI and Docker run 24.x). On Windows, Docker is the easier path.

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
