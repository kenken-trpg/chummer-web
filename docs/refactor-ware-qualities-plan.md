# Plan: split `engine/ware/` then `engine/qualities.py`

Working doc for a dedicated session. Companion to `docs/architecture.md`
§"Planned refactors" item 1 and `docs/refactor-gear-weapons-plan.md` (which
covered `engine/gear/`, `engine/magic/`, `engine/resonance.py`,
`martial_arts` / `contacts` / `skills` / `limits`).

## Where we are

`app/engine/__init__.py` is **3,323 lines** (from ~10,475 at the start of the
split). Extracted so far:

- `engine/lookups.py`, `constants.py`, `priority.py`, `formulas.py`, `karma.py`,
  `pricing.py`, `selects.py`, `requirements.py`, `dice.py`
- `engine/gear/` (13 modules), `engine/magic/` (8 modules),
  `engine/resonance.py`, `engine/martial_arts.py`, `engine/contacts.py`,
  `engine/skills.py`, `engine/limits.py`

What's left in `__init__.py`:

| block | contents | disposition |
| --- | --- | --- |
| orchestrators | `compute()`, `resolve_gear()` | **stay** |
| **'ware pipeline** | `resolve_ware` + rating/formula, cyberlimb attrs, redliner / Cyberseeker, limb sides, grades, subsystems, vehicle-hosted ware, required-ware warnings | **→ `engine/ware/` (Step 1)** |
| **qualities** | `gather_qualities`, `apply_quality_rules`, `sanitize_quality_ids`, the `bind_*` binders, `quality_requirement_context`, `quality_needs_extra` + `_quality_needs_*` inspectors, `free_powers_from_grants` | **→ `engine/qualities.py` (Step 2)** |
| adept enhancements | `resolve_enhancements` (sits inside the 'ware block by line number only) | **→ `engine/magic/powers.py`** (Step 1 prep) |
| header helpers | `find_metatype`, `default_attributes`, `_effective_attr_spec`, `resolve_attribute_selects`, `resolve_movement`, `apply_lifestyle_cost_mod`, `snapshot_career_baseline`, `career_raise_karma`, `nuyen_spend_breakdown`, `sync_reward_totals` | **stay** (Step 3 note re: `find_metatype` / `apply_lifestyle_cost_mod` and the `pyproject` E402/B023 ignore) |

After Steps 1–2, `__init__.py` is `compute()` + `resolve_gear()` + ~10 attribute
/ reward / movement / lifestyle helpers — target **~1.7–1.9k lines**.

## Ground rules (unchanged)

- Every commit individually green: `make check` (ruff check + ruff format --check
  + pytest `468 passed` + frontend). Plus the **snapshot gate**:
  `python -m pytest -q tests/test_snapshot.py` → `6 passed`, byte-identical,
  before and after every code move. `UPDATE_SNAPSHOTS=1` is never needed here.
- Submodules import only `catalog` / `eval_formula` (`..data_loader`),
  `..improvements`, `..models`, `.constants`, and **already-extracted** engine
  modules. **Never** import back into `app.engine` — the graph stays a DAG.
  Breakage surfaces 100 % at pytest collection.
- `compute()` and `resolve_gear()` stay in `__init__.py`. `_ensure_*` mutators
  move **with** their cluster.
- `__init__.py` keeps re-exporting every name `store.py` / `chummer_export.py` /
  tests import, via each new package's `__all__` and a mid-file
  `from .ware import (...)  # noqa: E402` / `from .qualities import (...)`
  block. Externally-imported names in these two clusters are only
  **`is_way_quality`** and **`sanitize_quality_ids`** (both `store.py`); every
  other moved name is `compute()`-only and satisfied by the re-import block.
- F401 **is** enforced on `__init__.py` (only `B023` / `E402` are per-file
  ignored). After each `carve` delete, manually strip now-unused
  `..data_loader` / `..models` / `.constants` / `.lookups` imports; grep
  `tests/ app/` first to confirm a name isn't an external re-export (those get
  `# noqa: F401  (re-exported for tests|store.py)` instead of deletion).
- Commit trailers (this session):
  `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>` and
  `Claude-Session: https://claude.ai/code/session_014XsGWooKn7vH58HZzP3nMJ`.
  (The `session_01VPrtYHJPX12Bqw8danc3hX` in the older plan doc is stale.)
- Terminology enforced by `backend/tests/test_terminology.py`.

## Extraction mechanics (established pattern)

1. `sed -n 'A,Bp' app/engine/__init__.py > /tmp/x.txt` per cluster range.
2. Heredoc writes `app/engine/ware/<name>.py` = docstring + relative imports +
   bodies.
3. `ruff check --fix && ruff format` the new file.
4. Heredoc deletes each cluster from `__init__.py`: locate `def NAME(` → next
   top-level `def `/`class `, assert the two preceding lines are blank, delete,
   splice back exactly two blank lines. Module-level constants (`LIMB_BODY_SLOTS`
   …) move by explicit line set.
5. Wire `ware/__init__.py` (imports + sorted `__all__`) and the `__init__.py`
   re-import block; `ruff check --fix` fixes I001 ordering.
6. Manually remove now-unused imports from `__init__.py`.
7. `ruff check && ruff format --check && python -m pytest -q` → `468 passed`;
   then `pytest -q tests/test_snapshot.py` → `6 passed`.
8. `python -c "import app.main, app.store, app.chummer_export, app.engine"`
   sanity, then commit.

Shell: chain `cd backend && source
.venv/bin/activate && <cmd>` in one Bash call — cwd resets to repo root after a
`git commit`, and shell state doesn't persist between calls.

---

## Step 1 — `engine/ware/`

~770 lines across ~40 functions. A **package**, not a single file (skills.py at
593 is already the ceiling; this is bigger and cleanly separable). Recommend
**5 commits** + 1 prep.

### 1a — prep: relocate two shared helpers, one bystander

Neither `ware/` nor `qualities.py` should import the other. Break the two
cross-cluster helpers out first, into neutral homes:

| name | `__init__.py` | → home | why |
| --- | --- | --- | --- |
| `_normalize_side` (+ `SIDES`, `_SLOT_JA`, `_SIDE_JA`) | 1382 / 1334-1338 | `engine/constants.py` (end, next to the `quality_*_extra_key` one-liners already living there) | pure Left/Right string maths; used by ware side logic **and** `apply_quality_rules` + the compute() `quality_extras` publisher |
| `_enhancement_by_id` | 1263 | `engine/lookups.py` (with the other `_*_by_id`) | catalog accessor, no other deps |
| `resolve_enhancements` | 2000 | `engine/magic/powers.py` | it's adept-power machinery (`state.adept_enhancements`, `ADEPT_TALENTS`, `ENHANCEMENT_KARMA`); only inside the 'ware line-range by accident. `compute()` re-imports it from `.magic`. |

`_quality_has_selectside` / `_quality_limb_slot` / `resolve_quality_sides` stay
put for now and go to **`qualities.py`** in Step 2 (they inspect `spec["bonus"]`
and validate quality picks; `resolve_quality_sides` takes the resolved
cyber/bio dicts as args, imports nothing ware-specific). This keeps
`ware → constants` as the only edge; `qualities → constants` too; no
`ware ↔ qualities`.

Commit: `refactor(engine): relocate _normalize_side / _enhancement_by_id ahead of ware split`
(or split enhancements into its own commit if the diff is noisy).

### 1b — `ware/rating.py`

- `racial_formula_extras`   (1270)
- `ware_rating_bounds`      (1278)
- `_clamp_ware_rating`      (1290)
- `ware_ranges`            (1666)

Deps: `catalog`, `eval_formula` (`..data_loader`) only. `ware_ranges` +
`_clamp_ware_rating` also feed `ware/resolve.py` and `ware/sides.py` → this
module is the leaf of the package. Re-export `ware_ranges` (compute() line
~3298).

### 1c — `ware/limbs.py` (cyberlimb attrs + redliner + Cyberseeker)

Move, with the limb module-constants block (`LIMB_BODY_SLOTS`,
`LIMB_BODY_PARTS`, `CYBERLIMB_BASE_ATTR`, `REDLINER_BASE_SLOTS`,
`_PARTIAL_LIMB`, `_MUSCLE_WARE`):

- `_apply_limb_attributes`      (1295)  — uses `_limb_attr_effect` from `.gear`
- `redliner_slot_caps`          (1341)
- `_is_full_limb` / `_is_body_limb` / `_is_redliner_limb` / `_limb_slot_count` (1352-1379)
- `limb_attribute_replace`      (1534)
- `count_redliner_limbs`        (1581)
- `apply_cyberseeker`           (1604)
- `redliner_incompat_warnings`  (1647)

Deps: `_limb_attr_effect` (`.gear`), `_normalize_side` (`.constants` after 1a),
`CharacterOptions` (`..models`). All take primitives / resolved dicts as args —
no `find_metatype`.

### 1d — `ware/sides.py`

- `_occupied_sides`   (1394)
- `_next_free_side`   (1410)
- `ensure_sides`      (1420)
- `_side_conflicts`   (1438)

Deps: `_ware_by_id` (`.lookups`), `_normalize_side` + `_SLOT_JA` / `_SIDE_JA`
(`.constants`), `CyberwareInstall` (`..models`).

### 1e — `ware/vehicles.py` (vehicle-hosted 'ware)

- `_vehicle_mod_hosts`          (1689)
- `_ware_fits_vehicle_mod`      (1704)
- `_drop_invalid_vehicle_ware`  (1716)
- `_vehicle_hosted_ware_ids`    (1738)
- `_zero_vehicle_hosted_essence` (1763)
- `_attach_ware_to_vehicle_mods` (1771)

Deps: `catalog` (`..data_loader`), `_iter_vehicle_hosts` + `mod_fits_vehicle`
(`.gear` — already mid-file-imported at `__init__.py:114`/`137`),
`_ware_by_id` (`.lookups`), `_cascade_orphans` + `_public_installed`
(`.ware.resolve`, see 1f — so land 1f first or fold these two commits).
`compute()` re-imports `_drop_invalid_vehicle_ware`,
`_zero_vehicle_hosted_essence`, `_attach_ware_to_vehicle_mods`,
`_vehicle_mod_hosts`.

### 1f — `ware/resolve.py` (core) + `ware/__init__.py`

- `_cascade_orphans`        (1678)
- `ensure_subsystems`       (1794)
- `_ensure_kind_subsystems` (1801)
- `resolve_ware`            (1833)
- `resolve_cyberware`       (1913)  — **dead code** (no callers anywhere in
  `app/` or `tests/`; `compute()` calls `resolve_ware("cyberware", …)`
  directly). Drop it in this commit rather than move it — it's the only thing
  in the cluster that would need `find_metatype`. Note the deletion in the
  commit body.
- `_public_installed`       (1918)
- `_first_allowed_grade`    (2050)  — grades
- `_clamp_ware_grades`      (2068)
- `_installed_ware_names`   (2092)  — warnings
- `_required_warnings`      (2101)

Deps: `catalog`, `eval_formula` (`..data_loader`); `substitute_rating`
(`..improvements`); `CyberwareInstall` (`..models`); `_ware_by_id` /
`_ware_by_name` / `_grade_by_name` (`.lookups`); `_capacity_value` /
`_device_rating_of` (`.gear`); `ware_rating_bounds` / `_clamp_ware_rating`
(`.ware.rating`); `_apply_limb_attributes` (`.ware.limbs`); `ensure_sides`
(`.ware.sides`). `compute()` re-imports `resolve_ware`, `ensure_subsystems`,
`_public_installed`, `_clamp_ware_grades`, `_installed_ware_names`,
`_required_warnings`.

`ware/__init__.py` re-exports the union with a sorted `__all__` (mirrors
`gear/__init__.py`).

Grades + warnings are only ~40 lines total — fold them into `resolve.py`
rather than spawn `ware/grades.py` / `ware/warnings.py`. Split them out later
only if `resolve.py` gets unwieldy.

---

## Step 2 — `engine/qualities.py`

~360 lines, one **single file** (in line with `contacts.py` / `martial_arts.py`;
no package needed). Recommend **2 commits**.

### 2a — inspectors + binders + context

- `_quality_extra_key_owned`      (441)  — only caller is `apply_quality_rules`
- `is_way_quality`                (916)  — re-export for `store.py`
- `sanitize_quality_ids`          (920)  — re-export for `store.py`
- `quality_needs_extra`           (956)
- `_quality_has_actiondicepool`   (983)
- `_quality_needs_spell_category` (987)
- `_quality_needs_spirit_category` (994)
- `_quality_has_selectside`       (1463) — moved here from the 'ware region
- `_quality_limb_slot`            (1467)
- `bind_action_dice_pools`        (1006)
- `bind_select_powers`            (1032)
- `free_powers_from_grants`       (1086)
- `quality_requirement_context`   (1110)
- `resolve_quality_sides`         (1483) — validates quality selectside extras
  against installed limbs; called from `compute()` right after `resolve_ware`

Deps: `re`; `_quality_by_id` / `_quality_by_name` / `_item_by_id` /
`_power_by_name` (`.lookups`); `_normalize_side` + `_SLOT_JA` / `_SIDE_JA`
(`.constants`); `talent_special` (`.priority`);
`QUALITY_*_EXTRA_SUFFIX` / `QUALITY_ADDSPIRIT_EXTRA_MARKER` (`.constants`);
`CharacterState` (`..models`). `compute()` re-imports the binders +
`quality_requirement_context` + `resolve_quality_sides` +
`_quality_has_selectside` + `_normalize_side` usage stays via `.constants`.

### 2b — `gather_qualities` + `apply_quality_rules`

- `gather_qualities`   (1948)
- `apply_quality_rules` (1151)

Deps: everything in 2a, plus `requirement_tree_met` (`.requirements`),
`_as_int` (`..improvements`), `quality_addspirit_extra_key` /
`quality_spirit_category_extra_key` (`.constants`),
`NEGATIVE_QUALITY_KARMA_CAP` / `POSITIVE_QUALITY_KARMA_CAP` (`.constants`).
`compute()` re-imports both.

Split into two commits so the snapshot gate brackets the two heaviest
functions (`apply_quality_rules` is ~110 lines of validation branches)
independently.

---

## Step 3 — docs + the E402/B023 cleanup

- Update `docs/architecture.md` §"Planned refactors" item 1: move `engine/ware/`
  + `engine/qualities.py` from "Next" to "Done", refresh the `__init__.py` line
  count, and note that "Next" is now just `compute()` / `resolve_gear()` +
  the attribute / reward helpers (i.e. the engine split is effectively done).
- Append a "Step 1 / Step 2 — done" section to this doc with the commit log
  (mirrors the older plan doc's Step 5/5b/5c sections).
- **Optional, if appetite remains — the `pyproject` ignore:**
  `"app/engine/__init__.py" = ["B023", "E402"]` exists because
  (a) `apply_lifestyle_cost_mod` (`__init__.py:529`) is a loop-local closure
  (`B023`), and (b) `find_metatype` (`__init__.py:77`) sits *above* the mid-file
  `from .X import (...)` blocks so those are `E402`. To retire it:
  1. Move `apply_lifestyle_cost_mod` to a module (it's a lifestyle/gear helper —
     `engine/gear/misc.py` or a new `engine/lifestyle.py`), which removes the
     `B023` site.
  2. Move `find_metatype` to `engine/lookups.py` (it needs only `catalog`) —
     re-export for `store.py` / `chummer_export.py` / tests — then every
     `from .X import` can hoist to the top of `__init__.py`.
  3. Delete the per-file-ignore and all `# noqa: E402` markers.
  This is independent of Steps 1–2 and can be its own session.

---

## Quick verification checklist per commit

```
cd backend && source .venv/bin/activate && \
  ruff check app/ && ruff format --check app/ && \
  python -m pytest -q && \
  python -m pytest -q tests/test_snapshot.py && \
  python -c "import app.main, app.store, app.chummer_export, app.engine"
# expect: 468 passed; snapshot 6 passed, no diff
git --no-pager diff --stat
```

Frontend is untouched but `make check` still runs it — no-op there.

---

## Step 1 / Step 2 — done

Executed in session `session_014XsGWooKn7vH58HZzP3nMJ`. `__init__.py`:
**3,323 → 2,111 lines**. Every commit `make check` green (468 passed) +
snapshot gate 6 passed, byte-identical.

| commit | what |
| --- | --- |
| `de39a33` | 1a prep — `_normalize_side` (+ `SIDES` / `_SLOT_JA` / `_SIDE_JA`) → `constants.py`; `_enhancement_by_id` → `lookups.py`; `resolve_enhancements` → `magic/powers.py` |
| `e1156b1` | 1b — `ware/rating.py`: `racial_formula_extras`, `ware_rating_bounds`, `_clamp_ware_rating`, `ware_ranges` |
| `36561f8` | 1c — `ware/limbs.py`: `_apply_limb_attributes`, `limb_attribute_replace`, `redliner_slot_caps`, `count_redliner_limbs`, `apply_cyberseeker`, `redliner_incompat_warnings`, `_is_*_limb` / `_limb_slot_count` + the `LIMB_*` constant block |
| `edb6beb` | 1d — `ware/sides.py`: `_occupied_sides`, `_next_free_side`, `ensure_sides`, `_side_conflicts` |
| `7c569dd` | 1e — `ware/vehicles.py`: `_vehicle_mod_hosts`, `_ware_fits_vehicle_mod`, `_drop_invalid_vehicle_ware`, `_vehicle_hosted_ware_ids`, `_zero_vehicle_hosted_essence`, `_attach_ware_to_vehicle_mods`; plus `ware/_common.py` (`_cascade_orphans`, `_public_installed`) to keep `resolve ↔ vehicles` a DAG |
| `d78a88c` | 1f — `ware/resolve.py`: `ensure_subsystems`, `_ensure_kind_subsystems`, `resolve_ware`, `_first_allowed_grade`, `_clamp_ware_grades`, `_installed_ware_names`, `_required_warnings`. `resolve_cyberware` **dropped** (dead code). |
| `71f7f95` | 2a — `qualities.py`: `is_way_quality`, `sanitize_quality_ids`, `quality_needs_extra`, the `_quality_*` inspectors, `_quality_has_selectside` / `_quality_limb_slot` (moved from the 'ware region), `_quality_extra_key_owned`, `bind_action_dice_pools`, `bind_select_powers`, `free_powers_from_grants`, `quality_requirement_context`, `resolve_quality_sides` |
| `0d4d6eb` | 2b — `qualities.py`: `gather_qualities`, `apply_quality_rules` |

Deviations from the plan above:

- 1a folded all three relocations into one commit (diff stayed small).
- 1e/1f: rather than land 1f first (which would make `ware → app.engine`
  during `ensure_subsystems`'s `_vehicle_mod_hosts` call), added
  `ware/_common.py` for the two leaf helpers both `resolve.py` and
  `vehicles.py` need — mirrors `gear/_common.py`.
- With `resolve_ware` gone, `__init__.py` also shed `CyberwareInstall`,
  `_capacity_value` / `_device_rating_of`, `_grade_by_name` / `_ware_by_id`
  / `_ware_by_name`, `_iter_vehicle_hosts` / `mod_fits_vehicle`, `_as_int`,
  `requirement_tree_met`, `re`, `_SLOT_JA` / `_SIDE_JA`, the `QUALITY_*`
  suffix constants and `POSITIVE_QUALITY_KARMA_CAP` — none were external
  re-exports. `quality_addspirit_extra_key` kept its re-export (an
  `# noqa: F401`) for `tests/test_engine.py`.

## Step 3 — remaining

The `["B023", "E402"]` `pyproject` cleanup (§Step 3 above) is still open and
independent — its own session.
