# Security policy

Chummer Web is an unofficial, fan-made Shadowrun 5e character builder run by a
single maintainer. There is no account system and the backend keeps no state —
characters live in the visitor's browser (IndexedDB). Please still report
anything that looks exploitable.

## Reporting a vulnerability

Use GitHub's **private vulnerability reporting**: the *Security* tab →
*Report a vulnerability*. That opens a private thread with the maintainer.

If that is unavailable, open a public issue that only says "security issue,
please enable private reporting" — no details in the clear — and wait to be
contacted.

Please include: affected route or file, a minimal reproduction, and the impact
you think it has. A fix or mitigation is welcome but not required.

Expect a first response within about a week. This is a hobby project, so there
is no formal SLA and no bounty.

## Scope

In scope:

- The FastAPI backend (`backend/app/`) — the import path (`.chum5` / `.chum5lz`
  parsing, decompression), request-size and rate-limit handling, the stateless
  compute/transform endpoints.
- The Docker image and `deploy/` config (Caddy, supervisord).
- The Next.js frontend (`frontend/`) — XSS via imported character data, the
  portrait `data:` URI handling.

Out of scope:

- Anything in the upstream [chummer5a](https://github.com/chummer5a/chummer5a)
  game data or its translations — report those upstream.
- Denial of service from a single client hammering a self-hosted instance you
  control; tune `RATE_LIMIT` / `MAX_REQUEST_BYTES` (see `docs/deploy.md`).
- Missing hardening headers on a deployment that bypasses the bundled Caddy.

## Supported versions

Only the latest `main` and the most recent tagged release get fixes. There are
no backports.
