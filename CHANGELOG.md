# Changelog

Notable changes. Format follows [Keep a Changelog](https://keepachangelog.com/);
self-hosters can pin to a tag instead of tracking `main`.

## [Unreleased]

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
