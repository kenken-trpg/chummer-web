# Changelog

Notable changes. Format follows [Keep a Changelog](https://keepachangelog.com/);
self-hosters can pin to a tag instead of tracking `main`.

## [Unreleased]

### Added

- Accessibility pass: every control has a name, the tab bar is a named `<nav>`
  with `aria-current`, there is a skip link ahead of the toolbar, and focus is
  visible. `eslint-plugin-jsx-a11y` is enforced.
- Catalog pickers say why a list stops where it does — how many rows were cut
  off, and that an empty search box lists core-rulebook entries only.
- `X-Request-ID` on every response, and `LOG_FORMAT=json` for one structured
  log line per request (`LOG_LEVEL` to go with it).
- End-to-end tests (Playwright) and coverage reporting for both halves.

### Changed

- `GET /api/catalog` is served with an ETag, so a reload revalidates into a 304
  instead of re-transferring ~2.9 MB.
- Addon dropdowns (armor mods, commlink accessories, vehicle mods, lifestyle
  qualities) no longer widen when the unrelated catalog search box below them
  has text in it; the narrowing is unconditional.
- A `v*` tag now publishes a GitHub Release from this file, and the image gets
  a `{major}.{minor}` tag to pin against.

### Fixed

- The knowledge-skill picker cut its list to 40 rows **before** removing the
  skills you already had, so a character with many knowledge skills was shown
  an empty list.

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

[Unreleased]: https://github.com/kenken-trpg/chummer-web/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/kenken-trpg/chummer-web/releases/tag/v0.1.0
