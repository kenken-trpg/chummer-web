# Plan: type the `Ctx` bundle dicts

Working doc. After the `compute()` phase split (`docs/refactor-compute-phases-plan.md`)
`Ctx` (in `app/engine/compute/context.py`) has ~40 `dict[str, Any]` "bundle"
fields — `effects`, `gear`, `magic`, `adept`, `foci`, `skill_mods`,
`contacts`, `martial`, … — each produced by one resolver and read by two or
three phase modules. Before the split they were locals in one function; now
they are the **contract between phase modules**, and every one is `Any`, so a
mistyped key or wrong value type at a seam slips past `mypy` (phase bodies
*are* checked — they carry `-> None` annotations — the bundles just aren't).

## Approach

New module `app/engine/bundle_types.py` (imports only `typing`; no engine
imports, so no cycle from either direction). It holds one `TypedDict` per
bundle. Each resolver's return annotation changes from `dict[str, Any]` to
its `TypedDict`; the matching `Ctx` field is annotated with it. Deeply nested
"public" row lists stay `list[dict[str, Any]]` — typing those fully is a
separate job.

No behaviour change: `tests/snapshots/*.json` byte-identical, 549 backend
tests green, `mypy` clean.

## Stages

1. **small, single-return resolvers** — `skill_mods` (`resolve_skill_mods`),
   `skill_picks` (`resolve_skill_picks`), `contacts` (`resolve_contacts`),
   `martial` (`resolve_martial_arts`), `movement` (`resolve_movement`),
   `initiation` (`resolve_initiation`), `submersion` (`resolve_submersion`).
   Each has a fixed key set and every consumer uses string-literal keys.
2. **incrementally-built bundles** — `adept`, `magic`, `resonance`, `gear`.
   Built by a resolver then mutated by the phase; `TypedDict` still fits the
   read side. Split further per bundle if the write side fights back.
3. **stretch: `effects`** — `improvements/effects.py::empty_effects()`, ~150
   keys, consumed everywhere. Its own plan.

## Verification per commit

```
cd backend && ./.venv/bin/python -m pytest -q && ./.venv/bin/ruff check . \
  && ./.venv/bin/ruff format --check . && ./.venv/bin/mypy
```
