# Plan: type the `Ctx` bundle dicts

Working doc. After the `compute()` phase split (`docs/plans/refactor-compute-phases-plan.md`)
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

1. **done** — small, single-return resolvers: `skill_mods`
   (`resolve_skill_mods`), `skill_picks` (`resolve_skill_picks`), `contacts`
   (`resolve_contacts`), `martial` (`resolve_martial_arts`), `movement`
   (`resolve_movement`), `initiation` (`resolve_initiation`), `submersion`
   (`resolve_submersion`). Three consumers that took the bundle as
   `dict[str, Any]` — `_copy_exotic_skill_bonuses`, `apply_free_metamagics`,
   `apply_granted_echoes` — now take the `TypedDict`.
2. **done** — the awakened / emerged bundles: `adept` (`resolve_adept_powers`),
   `enhancements` (`resolve_enhancements`), `foci` (`resolve_foci`), `qi`
   (`resolve_qi_foci`), `focus_limits` (`apply_focus_limits`), `magic`
   (`resolve_spells`), `spirits` (`resolve_spirits`), `resonance`
   (`resolve_complex_forms`), `techno_sprites` (`resolve_sprites`). All had
   consistent early/late return shapes, so a `total=True` `TypedDict` fit
   without touching the write side.
3. **done** — `gear` (`resolve_gear`, single 29-key return). Consumers all
   use string-literal keys except `apply_purchase_discounts` /
   `apply_black_market_avail`, which iterate `gear[<category>]` over a tuple
   of names — those keep a `dict[str, Any]` param and take a `cast` at the
   call site. `apply_erased_lifestyle_cap`, `apply_overclocker`,
   `apply_lifestyle_cost_mod`, `nuyen_spend_breakdown` now take `GearBundle`.
4. **done** — the `effects` dict
   (`improvements/effects.py::empty_effects()`, 134 keys, consumed
   everywhere including outside `compute/`). Now `improvements.EffectsDict`
   (`total=True`), carried by `empty_effects()` / `collect_effects()` /
   `apply_bonus_nodes` / the four `nodes/*.py` handlers / `Ctx.effects` and
   the ~54 engine `effects:` params. `enabled_tabs` stopped being a
   set→list type-swap (it's a `set[str]` throughout; callers sort at use).
   See `docs/plans/refactor-effects-typeddict-plan.md`.

## Verification per commit

```
cd backend && ./.venv/bin/python -m pytest -q && ./.venv/bin/ruff check . \
  && ./.venv/bin/ruff format --check . && ./.venv/bin/mypy
```
