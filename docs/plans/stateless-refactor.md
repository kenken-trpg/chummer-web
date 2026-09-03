# Stateless backend / client-owned state

Done. Deployment prep — the backend can now scale to zero / run many
instances, and no character data touches the server disk.

## Why

`store.py` kept every character in a process dict mirrored to
`backend/saves/*.json`, and `GET /api/characters` returned **everyone's**
roster with no auth. Fine for one local user, unfit for a public deploy
(data commingling, cross-deletion, single-instance, a volume to back up).
CONTRIBUTING already listed "no accounts, no server-side state" as a non-goal.

## What changed

- **`app/store.py`** is pure: `new_character(CharacterCreate)`,
  `apply_patch(state, patch)` (the talent / priority / career normalisation,
  unchanged — just takes the state as an argument now), `compute_state(state)`
  (bare recompute), `import_character(payload)` (id regenerated, no persist).
  `_MEMORY` / `_persist` / `SAVE_DIR` / `get_character` / `list_characters` /
  `delete_character` / `export_character` gone.
- **`app/main.py`**: `POST /api/characters/{new,patch,chummer,import}` +
  unchanged `import-chummer`. The id-addressed `GET/PATCH/DELETE` routes are
  gone. `models.py` gains `StateRequest` / `PatchRequest`.
- **`frontend/lib/character/local-store.ts`** (new, no dependency): an
  IndexedDB wrapper (`chummer-web` DB, `characters` store keyed on `id`).
  Every accessor degrades to an empty result on failure.
- **`frontend/lib/api.ts`**: `catalog` stays a GET; `list/get/remove` use the
  local store; `create/patch/import/importChummer` POST to the stateless
  endpoints and mirror the result into IndexedDB. `api.compute(state)` backs
  undo/redo; `api.exportChummer(state)` returns a `.chum5` blob.
- **`frontend/next.config.ts`**: rewrite target from `BACKEND_ORIGIN` (env) for
  split deploys.

## Tests

`backend/tests/test_roster.py` deleted; `test_stateless.py` covers the pure
functions + the HTTP surface. `frontend/lib/character/local-store.test.ts`
(graceful degradation); `useCharacterEditor.test.tsx` undo asserts the
`api.compute` path.

## Not done (future)

- Accounts / cloud sync / share links — would need a real datastore + auth,
  or signed read-only snapshot URLs.
- Migrating any old `backend/saves/*.json` — pre-launch, no real users.
