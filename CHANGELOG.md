# Changelog

Notable changes. Format follows [Keep a Changelog](https://keepachangelog.com/);
self-hosters can pin to a tag instead of tracking `main`.

## [Unreleased]

## [0.2.1] — 2026-09-05

### Security

Dependency-only release. `0.2.0` ships a frontend build with five known
advisories in it; the image published for that tag is not rebuilt, so
self-hosters on `:0.2.0` should move to `:0.2.1` (or `:0.2`, which now points
here). Nothing else changed — no rules, no API, no UI.

- `sharp` 0.34.5 → 0.35.4, for four libvips CVEs (GHSA-f88m-g3jw-g9cj).
- `postcss` 8.4.31 → 8.5.28, for arbitrary `.map` file disclosure via an
  attacker-controlled `sourceMappingURL` (CVE-2026-45623, CVE-2026-73646) and
  two lesser issues (CVE-2026-41305, CVE-2026-69153). Pinned through an
  `overrides` entry so Next stays on 15.x: the automated fix wanted Next 16,
  which is a migration rather than a patch.
- `next` 15.5.23 → 15.5.25.

Neither package is reachable from a request — `postcss` reads this project's
own CSS at build time and `sharp` backs Next's image optimisation, which this
app does not use on user input — so the practical exposure was low. `npm audit`
now reports zero.

## [0.2.0] — 2026-09-05

### Added

- **Read-only share links.** A character is encoded into the URL fragment and
  opened at `/share#c=…`. The fragment never reaches the server, so nothing is
  uploaded and nothing is stored; the view is `noindex`. Long links and dropped
  portraits are reported as a notice on a link that worked, not as an error.
- **English UI.** Every string is in `lib/i18n` behind a language switch, and
  the SR5 vocabulary tables, the formatters, the text sheet and the error copy
  all follow the locale. A locale that is missing a key fails the build.
- **Build-check panel** — the chargen errors and warnings in one place.
- Accessibility pass: every control has a name, the tab bar is a named `<nav>`
  with `aria-current`, there is a skip link ahead of the toolbar, and focus is
  visible. `eslint-plugin-jsx-a11y` is enforced.
- Catalog pickers say why a list stops where it does — how many rows were cut
  off, and that an empty search box lists core-rulebook entries only.
- `X-Request-ID` on every response, and `LOG_FORMAT=json` for one structured
  log line per request (`LOG_LEVEL` to go with it).
- End-to-end tests (Playwright) and coverage reporting for both halves.

### Changed

- **Japanese Run & Gun entry names.** 31 names that had no Japanese at all are
  now translated, and four existing ones were corrected (`コーティング`, not
  `コーディング`). Three entries stay in Latin script because the book prints
  them that way. Bracket and colon conventions in the overlay are now linted.
- `GET /api/catalog` is served with an ETag, so a reload revalidates into a 304
  instead of re-transferring ~2.9 MB.
- Addon dropdowns (armor mods, commlink accessories, vehicle mods, lifestyle
  qualities) no longer widen when the unrelated catalog search box below them
  has text in it; the narrowing is unconditional.
- Docker base images are pinned by digest and the image ships a baseline CSP.
- Collections sent by a client are size-capped in the models.
- A `v*` tag now publishes a GitHub Release from this file, and the image gets
  a `{major}.{minor}` tag to pin against.

### Fixed

- The knowledge-skill picker cut its list to 40 rows **before** removing the
  skills you already had, so a character with many knowledge skills was shown
  an empty list.
- A truncated catalog list now says it is truncated instead of looking complete.
- The per-IP rate limiter no longer trusts a client-supplied
  `X-Forwarded-For`, which let one caller present as many.
- Two `specialArmorBits` implementations had drifted; the sheet now uses one.

### Internal

No behaviour change, but this is most of the diff: `store.py`, the catalog
projection, the `.chum5` reader and writer, the weapons engine and the magic
loader were each split along their own seams, and the seven copies of the
catalog picker became one component. Test coverage went from ~49% to ~76% on
the frontend and ~91% to ~92% on the backend, with the panels that patch a
character — gear, weapons, vehicles, skills, qualities, lifestyles — and the
editor hook that owns the only copy of it covered for the first time.

## [0.1.0] — 2026-09-02

First tagged release.

### Character builder

- Build methods: Priority / Sum-to-Ten / Life Modules.
- Metatype + metavariants, attributes, active / knowledge / exotic skills and
  skill groups, positive & negative qualities.
- Augmentations (cyber- and bioware, grades, nested), armor + mods, weapons +
  accessories + ranges + recoil, commlinks / cyberdecks / RCCs / programs,
  drones & vehicles + mods + weapon mounts, lifestyles, contacts, martial arts.
- Magic: spells, spirits, foci, adept powers, mentor spirits, traditions,
  initiation + metamagics. Resonance: complex forms, sprites, submersion + echoes.
- Career mode: karma / nuyen reward ledger, chargen baseline diff, street cred.
- Derived-stat engine (`compute()`), chargen validation with errors / warnings.

### Import / export

- Chummer5a `.chum5` / `.chum5lz` import (best-effort; unresolved items become
  warnings) and `.chum5` export.
- JSON save / load.
- Cocofolia コマ + BCDice chat-palette export; conjured spirits / sprites as
  separate コマ.
- Character sheet: standard / compact / text / print (A4) layouts.

### Platform

- Japanese-first UI; terminology overlay on top of the Chummer JA translations.
- **Stateless backend** — characters live in the browser (IndexedDB); the
  server only computes and transforms.
- Import path hardened: `defusedxml`, request-size cap, `.chum5lz`
  decompression-bomb cap, per-IP rate limiting.
- chummer5a game data pinned to a commit and fetched at build time.
- One-container Docker image (Caddy + uvicorn + Next standalone) published to
  GHCR; `make up` / `compose.yaml` for local self-hosting.

[Unreleased]: https://github.com/kenken-trpg/chummer-web/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/kenken-trpg/chummer-web/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/kenken-trpg/chummer-web/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/kenken-trpg/chummer-web/releases/tag/v0.1.0
