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
state.derived  (plain dict)   →  every /api/characters* response
```

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

## Frontend

- `app/page.tsx` owns `catalog`, the current `Character`, the active tab, and
  the `patch()` / undo-redo plumbing. It passes a `TabPanelProps` bag
  (`catalog`, `character`, `d = character.derived`, `tr`, `patch`,
  `setCharacter`) to each tab.
- `components/character/tabs/*` — one file per tab; gear sub-tabs under
  `tabs/gear/`. Tabs are presentational: they read `d.*` and call `patch({...})`.
- `components/CharacterSheet.tsx` — the printable sheet (standard / compact /
  plain-text layouts).
- `lib/types.ts` — hand-maintained mirror of the backend payloads. When you add
  a field to `derived` or a catalog entry, add it here too.
- `lib/api.ts` — fetch wrappers. `lib/cocofolia.ts` — VTT/chat-palette export.

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
     `_resolve_misc_gear`), and the `engine/magic/` package: `magic/_common.py`
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
     `resolve_quality_sides`). `resolve_gear()` and `compute()` stay in
     `__init__.py` as orchestrators. `__init__.py` is ~2.1k lines, down from
     ~10.5k — the engine split is effectively done.
   - The mid-file `from .priority import (...)` / `from .lookups import (...)`
     blocks and the `["B023", "E402"]` ignore in `pyproject.toml` go away once
     the lifestyle-quality helper lands in a module and imports move to the top.
   - *Next (own session):* only the `["B023", "E402"]` cleanup above — move
     `apply_lifestyle_cost_mod` to a module and `find_metatype` to
     `engine/lookups.py` so every mid-file `from .X import` can hoist to the
     top. What's left in `__init__.py` is `compute()` / `resolve_gear()` + a
     handful of attribute / reward / movement / lifestyle helpers.
2. **Split `CharacterSheet.tsx`** (~1.2k lines) into per-section components.
   - *Done:* plain-text sheet → `lib/character/text-sheet.ts`; shared
     `Section` / `GradeList` / `VehicleBlock` → `components/character/sheet/
     blocks.tsx`; range-band + special-armor formatting →
     `lib/character/sheet-format.ts`; formatters consolidated in
     `lib/character/format.ts`.
   - *Next:* pull each `<Section>` in the big `return (…)` into its own
     component under `components/character/sheet/`, passing `d` / `tr` / `t`.
3. **Split `lib/types.ts`** — *done:* `lib/types/{installs,catalog,derived,
   character}.ts` + an `index.ts` barrel; `@/lib/types` still resolves.
4. Drive the demoted eslint warnings to zero (see `eslint.config.mjs`): the
   remaining 4 are one custom-font `<link>`, one `useEffect` dep, one
   internal `location.href`, and one `any` in a sheet helper.
