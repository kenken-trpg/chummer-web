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

These are known and welcome as PRs:

1. **Split `engine.py`** (~10k lines) into an `app/engine/` package by concern
   (priority, attributes, gear/*, magic/*, karma, compute). `__init__.py`
   re-exports the current public names so imports don't churn. Doing this in
   small, individually-green commits is the whole trick. (This also removes the
   `B023` ruff ignore — the loop-local lifestyle-quality helper moves to module
   scope.)
2. **Split `CharacterSheet.tsx`** into per-section components.
3. **Split `lib/types.ts`** to mirror the backend module boundaries.
4. Drive the demoted eslint warnings to zero (see `eslint.config.mjs`).
