# Architecture

## One sentence

The browser edits a `CharacterState`; every change is `PATCH`ed to a FastAPI
backend that runs `engine.compute(state)` and returns the state with a fat
`derived` blob the UI renders.

## Backend data flow

```
Chummer/data/*.xml  ──fetch_chummer_data.py──▶  backend/vendor/chummer/   (gitignored)
        │
        ▼
data_loader.catalog()        parse the subset we use into one big dict,
   (LRU-cached, process-wide) keyed by kind: metatypes, qualities, weapons,
        │                     cyberware, spells, gear, drugs, ranges, …
        ▼
store.public_catalog()        reshape + translate for the frontend  →  GET /api/catalog
        │
        ▼
engine.compute(CharacterState)          the rules engine
        │   • resolves priorities / talent / attributes / skills
        │   • resolves installs (ware, gear, armor, weapons, vehicles)
        │   • collects <bonus> nodes from every source into one `effects` dict
        │     via improvements.apply_bonus_nodes()
        │   • folds effects into totals, limits, initiative, condition monitor
        │   • runs chargen validation → errors[] / warnings[]
        ▼
state.derived  (DerivedDict)  →  every /api/characters* response
```

`engine.compute()` is the `engine/compute/` package: it builds one `Ctx`
dataclass (the working set) and runs it through ~19 ordered phases
(`bootstrap → qualities → ware → effects → essence → attributes → magic →
gear → totals → economy → finalize → assemble`), each a
`phase(ctx: Ctx) -> None`. Order is load-bearing. See
`docs/refactor-compute-phases-plan.md`.

`translation overlay`: `backend/data/ja_overrides/{data,ui}.json` is applied by
`data_loader` on top of the vendored `lang/ja-jp*.xml`. `data.json` is
generated (`regen_ja.sh`); `ui.json` is hand-written.

## The `effects` dict and `<bonus>` nodes

Almost every mechanical modifier in Shadowrun is expressed in Chummer's XML as a
`<bonus>` child with a tag like `<specificattribute>`, `<initiativepass>`,
`<limitmodifier>`, `<skillcategory>`. `data_loader.parse_bonus()` turns those
into `{"tag": ..., "value"/"fields": ...}` dicts.

`improvements.apply_bonus_nodes(nodes, effects, source)` is the single dispatch
point: it walks the nodes and accumulates into a mutable `effects` dict
(`attribute_bonus`, `initiative_dice`, `limit_physical`, `skill_specific_mods`,
…). `engine.compute()` calls it once per bonus source (qualities, ware, gear,
foci, tradition, metamagics, active drugs, …) and then reads `effects` when
computing finals.

That dict is typed: `improvements.EffectsDict` (a `total=True` `TypedDict`
next to `empty_effects()`, which produces it) fixes the ~134 keys and their
value types, so `effects["initiave_dice"]` (typo) is a `mypy` error rather
than a silent `None`. `collect_effects()` / `apply_bonus_nodes` / the four
`nodes/*.py` handlers and `Ctx.effects` all carry it. Scalars and nested
dicts are precise; the `*_mods` / `*_slots` / `grant_*` / cost-rule list
values carry row `TypedDict`s from `improvements/effect_rows.py` (one per
`nodes/*.py` producer branch), so `row.get("nam")` (typo) is caught too.
`enabled_tabs` is a `set[str]` throughout; callers `sorted(...)` it where
they need an ordered list.

Adding support for a new modifier = add a branch in `apply_bonus_nodes` (or a
tag to `SILENT_TAGS` if we intentionally ignore it) plus wherever `effects`
is consumed. See `docs/adding-rules.md`.

## HTTP API (all JSON unless noted)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | liveness |
| GET | `/api/catalog` | the whole options catalog for the UI |
| GET | `/api/characters` | roster summaries |
| POST | `/api/characters` | create |
| GET | `/api/characters/{id}` | full state + `derived` |
| PATCH | `/api/characters/{id}` | partial update (`CharacterPatch`) → recomputed state |
| DELETE | `/api/characters/{id}` | delete |
| GET | `/api/characters/{id}/export` | raw state JSON |
| GET | `/api/characters/{id}/chummer` | `.chum5` XML download |
| POST | `/api/characters/import` | import raw state JSON |
| POST | `/api/characters/import-chummer` | import `.chum5` / `.chum5lz` |

`store.py` keeps characters in an in-memory dict and mirrors them to
`backend/saves/*.json`. No database, no auth.

`chummer_import.py` (`chum5_to_state`) resolves a Chummer5a `.chum5` / `.chum5lz`
by `sourceid` then name; unknown entries become warnings, never errors.
`chummer_export.py` (`state_to_chum5`) writes it back. The pair is a fixed
point on a **computed** state — `tests/test_chummer_roundtrip.py` builds
Chummer-shaped XML from the live catalog and pins
`xml → state → compute → xml → state → compute`, asserting the second
computed state equals the first (row ids stripped) and `derived` is
loop-invariant, across a street samurai / mage / technomancer / career
(SumToTen) scenario.

## Frontend

- `app/page.tsx` is a ~90-line shell: it holds only view state (active tab,
  sheet layout, the hidden file-input ref), calls the editor hook, and lays
  out `<Toolbar> / <TabBar> / <TabPanels> / <CharacterSidebar>`. It passes a
  `TabPanelProps` bag (`catalog`, `character`, `d = character.derived`, `tr`,
  `patch`, `setCharacter`) to each tab via `<TabPanels>`.
- `lib/character/useCharacterEditor.ts` — owns `catalog` / `ch` / `error` /
  `roster` / `history` and every mutation (create / open / delete / duplicate
  / patch / undo-redo / import / export / clipboard / portrait). The
  mount-only bootstrap effect lives here. Returns a bag consumed by `Page`,
  `Toolbar` and the panels; takes `{ onCharacterOpened }` so `Page` resets the
  tab on open/new/dup/import.
- `lib/character/useSheetLayout.ts` (localStorage-backed `standard|compact|text`)
  and `lib/character/useKeyboardShortcuts.ts` (Ctrl/⌘+Z / +Y / +Shift+Z →
  undo/redo, inert while an INPUT/TEXTAREA is focused).
- `components/character/{Toolbar,TabBar,TabPanels,SheetDescEditor}.tsx` — the
  four presentational chunks of the old `Page` return: the `.toolbar` row, the
  `.tabs` row (enabled-tab aware), the `{tab === "x" && <XTab/>}` switch
  (+ `<CharacterSheet>` for `tab==="sheet"`), and the sheet portrait/bio editor.
- `components/character/tabs/*` — one file per tab; gear sub-tabs under
  `tabs/gear/`. Tabs are presentational: they read `d.*` and call `patch({...})`.
  `QualitiesTab` delegates the per-quality "extra pick" editor to
  `tabs/qualities/QualityExtraEditor.tsx`.
- `components/character/CharacterSidebar.tsx` — a shell over nine
  `sidebar/*` block components sharing a `SidebarBlockProps` bag
  (`sidebar/types.ts`); `SidebarCareerRewards` owns the reward-log state.
- `components/CharacterSheet.tsx` — the printable sheet (standard / compact /
  plain-text layouts); it's a thin shell over
  `lib/character/sheet-data.ts::buildSheetData` + one component per section
  under `components/character/sheet/sections/`.
- `lib/types.ts` — hand-maintained mirror of the backend payloads. When you add
  a field to `derived` or a catalog entry, add it here too.
- `lib/api.ts` — fetch wrappers. `lib/cocofolia.ts` — VTT/chat-palette export.
- **Tests** — `vitest` (jsdom + React Testing Library), `*.test.{ts,tsx}`
  next to the code, shared fixtures in `frontend/tests/fixtures.ts`
  (`makeCharacter` / `makeCatalog`). `npm run test` is part of `make check`
  and CI. Coverage (~157 tests): the `lib/character/*` pure helpers
  (`sheet-format`, `format`, `sheet-data`, `gear`, `quality`) + `cocofolia`
  builders; the `page.tsx` hooks (`useCharacterEditor` against a mocked
  `@/lib/api`, `useSheetLayout`, `useKeyboardShortcuts`); render smoke tests
  for `CharacterSheet` / `CharacterSidebar` / `Toolbar` (sections wired, all
  layouts render); and a render + primary-`patch()`-payload test beside every
  tab in `components/character/tabs/` (all 18, plus the `GearTab` container
  and the `gear/{WeaponGear,VehicleDroneGear,MiscDrugsGear}` sub-panels).

## Planned refactors

Welcome as PRs. Keep every commit individually green (`make check`).

1. **Split the engine** (`app/engine/__init__.py`) by concern.
   - *Done:* it's now a package. `engine/lookups.py` (catalog accessors),
     `engine/constants.py` (talent groupings, karma prices, lookup tables),
     `engine/priority.py` (priority table + talent + build-method validation),
     `engine/formulas.py` (stat-expression helpers), `engine/karma.py`
     (attribute / skill / knowledge cost maths + `<karmacost>` rule helpers),
     `engine/pricing.py` (post-resolve essence-multiplier / Black-Market /
     discount / Overclocker adjustments), `engine/selects.py` (enumerate the
     picks behind a `<select*>` / `*soft` bonus node), `engine/requirements.py`
     (`<required>` / `<forbidden>` tree evaluation), `engine/dice.py`
     (`skill_dice_pool` / `magic_opposed_test`), the `engine/gear/`
     package: `gear/_common.py` (`_clamp_rating` / `_device_rating_of` /
     `_capacity_value` / `_cascade_optics` / `_program_label`, plus the
     weapon/vehicle constraint & mount primitives and `_leading_vehicle_stat` /
     `_limb_attr_effect`), `gear/drugs.py`, `gear/matrix.py` (cyberdecks /
     RCCs), `gear/armor.py` (armor mods + worn-armor total), `gear/optics.py`,
     `gear/sensors.py`, `gear/programs.py`, `gear/apps.py`, `gear/ammo.py`,
     `gear/weapons.py` (public weapon row + gear/ware-weapons + ware-limb attrs
     + reach/unarmed/category-DV/skill-accuracy appliers + accessory & recoil
     pipeline + DV/accuracy binders), `gear/vehicles.py` (stat formatting +
     vehicle/mod constraints + R5 mod-slot accounting + drone/mod/mount
     resolvers), `gear/misc.py` (`_misc_external_hosts` + the catch-all
     `_resolve_misc_gear`), `gear/lifestyle.py` (monthly cost + LP budget +
     lifestyle qualities + `apply_lifestyle_cost_mod`), and the `engine/magic/`
     package: `magic/_common.py`
     (`spell_drain_value` / `tradition_resist` / `spell_cast_info` /
     `_magic_grade_discount` / `_active_skill_rating_from_state`),
     `magic/powers.py` (adept powers + `power_*` helpers + Way discounts),
     `magic/mentor.py`, `magic/foci.py` (bonded + Qi foci + weapon-focus
     bridge + Artificing/Arcana tests), `magic/spirits.py` (summonable types +
     services + summoning tests + addspirit), `magic/spells.py` (spell list +
     free-spell allowances + tradition/quality binders + drain summary),
     `magic/initiation.py` (metamagic / art grades + free metamagics),
     `magic/submersion.py` (echo grades); `engine/resonance.py` — the
     technomancer mirror (complex forms + fading, sprites, living persona,
     addecho grants); `engine/martial_arts.py` (styles + techniques),
     `engine/contacts.py` (contact network + Ex-Con / Erased caps),
     `engine/skills.py` (knowledge / specialization / exotic / skillsoft
     resolution + skill-bonus modifiers), `engine/limits.py` (chargen
     avail / device-rating / ware-attribute-bonus caps), the `engine/ware/`
     package: `ware/rating.py` (formula-driven rating bounds + `ware_ranges`),
     `ware/limbs.py` (cyberlimb attributes + Redliner / Cyberseeker),
     `ware/sides.py` (Left/Right assignment for paired 'ware), `ware/vehicles.py`
     (vehicle-hosted cyberware), `ware/_common.py` (`_cascade_orphans` /
     `_public_installed`) and `ware/resolve.py` (`resolve_ware` + subsystems +
     grade clamping + required-'ware warnings), and `engine/qualities.py`
     (`gather_qualities` / `apply_quality_rules` + the `bind_*` binders + the
     `_quality_*` extra-pick inspectors + `quality_requirement_context` /
     `resolve_quality_sides`). The
     `["B023", "E402"]` per-file ignore is retired: `find_metatype` moved to
     `engine/lookups.py`, every `from .X import` is top-of-file, and the
     lifestyle closure lives in `gear/lifestyle.py`. **The engine split is
     done** — `engine/__init__.py` is now a pure re-export barrel (~250 lines)
     and `compute()` is the `engine/compute/` package (see next item).
   - *Done:* `compute()` — the last ~1,200-line monolith — is split into
     `engine/compute/` by phase. `context.py` holds the `@dataclass Ctx` (the
     honest ~150-field working set threaded through the pipeline); each
     `phase(ctx: Ctx) -> None` reads/writes `ctx.*`. `bootstrap.py` (build
     method / caps / meta / ware sanity + `sync_reward_totals`), `qualities.py`
     (quality gather + effects + binders + `resolve_attribute_selects`),
     `ware.py`, `essence.py` (essence penalty + the ratings loop), `magic.py`
     (initiation / submersion / foci / adept + spells / spirits / resonance),
     `gear.py` (carries `resolve_gear` in with it + post-gear application),
     `economy.py` (priority points / skills / karma / social) with the
     career-layer helpers in `_career.py` (`snapshot_career_baseline` /
     `career_raise_karma` / `nuyen_spend_breakdown`), `finalize.py` (totals
     check + limits / CM / initiative + quality rules + chargen validation,
     carries `resolve_movement`), `assemble.py` (the ~175-key `state.derived`
     literal — typed `DerivedDict` (`derived_types.py`), key-parity with the
     frontend's `Character["derived"]` pinned by
     `tests/test_derived_contract.py` — carries `_effective_attr_spec`). `compute/__init__.py` is
     ~60 lines: build one `Ctx`, run the phases, return `ctx.state`. No
     behaviour change — `tests/test_snapshot.py` guards byte-identical output
     and `tests/test_compute_phases.py` pins the *seams*: it drives the same
     phase sequence by hand, asserts the `ctx` slice each phase owns after it
     runs, and holds `PHASES` in lock-step with `compute()` (order guard +
     manual-run-equals-`compute()` guard + no-orphan-`Ctx`-field guard).
     `store.py` / tests still `from app.engine import compute,
     snapshot_career_baseline, default_attributes` unchanged.
2. **Split `app/improvements.py`** (the `<bonus>` → `effects` pipeline) —
   *done:* now the `app/improvements/` package. `_common.py` (constant
   tables + `_as_int` / `substitute_rating` / `_bonus_int` primitives),
   `effects.py` (`empty_effects` + the special-armor / limit-modifier
   compactors), and `nodes/` — `apply_bonus_nodes` is a thin per-node loop
   that dispatches to `nodes/{stats,skills,magic,social}.py`, each owning a
   slice of the old ~90-branch `if/elif tag` chain as
   `apply(tag, node, fields, effects, source) -> bool`.
   `tests/test_improvements_nodes.py` guards that every `IMPLEMENTED` tag
   still has a handler. `from app.improvements import …` is unchanged (the
   package `__init__` is the barrel).
3. **Split `app/data_loader.py`** (vendored-XML → catalog dict) — *done:*
   now the `app/data_loader/` package. `_xml.py` (paths + `_text` / `_int`
   element accessors), `formulas.py` (`eval_formula` + avail / capacity
   parsers), `bonus.py` (the `<bonus>` / `<required>` sub-tree parsers +
   select-option inspectors), and `loaders/` — one module per domain
   (`ware`, `metatypes`, `skills`, `qualities`, `magic`, `weapons`, `armor`,
   `gear`, `vehicles`, `lifestyle`, `drugs`, `martial_arts`, `priorities`,
   `translations`). `__init__.py` is the barrel + the `@lru_cache`
   `catalog()` assembler that does the cross-entity wiring — 2,864 → 240
   lines. `from app.data_loader import …` is unchanged.
4. **Split `CharacterSheet.tsx`** (~1.2k lines) into per-section components.
   - *Done:* plain-text sheet → `lib/character/text-sheet.ts`; shared
     `Section` / `GradeList` / `VehicleBlock` → `components/character/sheet/
     blocks.tsx`; range-band + special-armor formatting →
     `lib/character/sheet-format.ts`; formatters consolidated in
     `lib/character/format.ts`. Then `lib/character/sheet-data.ts`
     (`buildSheetData()` → the typed `SheetData` bundle) and one component
     per section under `components/character/sheet/sections/` +
     `SheetHeader.tsx` — `CharacterSheet.tsx` is now props →
     `buildSheetData` → the text branch → `<article>` = `<SheetHeader/>` +
     18 `<*Section {...s}/>` + footer, **92 lines** down from ~1,155.
5. **Split `lib/types.ts`** — *done:* `lib/types/{installs,catalog,derived,
   character}.ts` + an `index.ts` barrel; `@/lib/types` still resolves.
6. **eslint warnings to zero** — *done:* the Google-fonts `<link>` moved to
   `next/font/google` (`--font-plex-sans-jp` CSS var), the `.chum5` export
   button downloads via a generated `<a>` instead of `window.location.href`,
   and the mount-only bootstrap effect carries an
   `// eslint-disable-next-line react-hooks/exhaustive-deps`. Those three
   rules + `react-hooks/refs` are promoted back to `error` in
   `eslint.config.mjs`; `no-explicit-any` / `no-unused-vars` stay `warn`
   (file-level disables fence off the remaining `any`).
7. **mypy to zero + blocking** — *done:* the 30 errors were loop-variable
   type reuse (`for inst in state.armor` then `state.weapons` in one
   function — renamed per loop in `resolve_gear` / `state_to_chum5` /
   `_misc_external_hosts`), `dict[str, int]` passed where the invariant
   `dict[str, int | float]` was expected (`eval_formula` /
   `ware_rating_bounds` `extras` widened to `Mapping[str, float] | None`),
   and a couple of `str | None` narrows. `mypy` is now clean and part of
   `make check` / CI (`ci.yml` dropped `continue-on-error`).
   - *Strict across the whole backend.* `[tool.mypy]` now runs
     `check_untyped_defs` / `disallow_untyped_defs` /
     `disallow_incomplete_defs` / `warn_return_any` over all of `app/` —
     no per-module `[[tool.mypy.overrides]]`. This was reached package by
     package: `app.engine.*` / `app.improvements.*` cleared once their two
     `Any` fountains were typed — the `Ctx` bundles / `effects`
     (`EffectsDict` + `effect_rows.py`) and `catalog()` (`CatalogDict`) —
     after which every module passed with at most a rename or a cast
     (`_match_by`, `catalog_list` / `catalog_ware`). The boundary modules
     (`store` / `main` / `chummer_import|export` / `data_loader`) turned out
     to already hold the bar, so the overrides collapsed into the base.
   - *Ctx bundles typed:* every `dict[str, Any]` "bundle" threaded between
     `compute()` phases is now a `TypedDict` — the small / awakened / gear
     bundles in `app/engine/bundle_types.py`, and the big one, the `effects`
     accumulator, as `improvements.EffectsDict` (next to `empty_effects()`).
     A mistyped key or wrong value type at a phase seam is a `mypy` error.
     `EffectsDict`'s ~45 row-list values are typed one level deeper too —
     row `TypedDict`s in `improvements/effect_rows.py`, one per `nodes/*.py`
     producer branch. Still `list[dict[str, Any]]`: the `Ctx` bundle
     `.public` / gear-category lists (serialisation DTOs, a separate job).
