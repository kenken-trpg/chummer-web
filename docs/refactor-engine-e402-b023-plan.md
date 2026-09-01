# Plan: retire the `app/engine/__init__.py` `["B023", "E402"]` ignore

Working doc for a dedicated session. Follow-on to
`docs/refactor-ware-qualities-plan.md` (Step 3, "remaining"). This is the
*last* item on `docs/architecture.md` §"Planned refactors" item 1 — after it
the engine split is fully done and the per-file ruff ignore is gone.

## Where we are

`app/engine/__init__.py` is **2,111 lines** (`compute()` + `resolve_gear()`
orchestrators + ~15 attribute / reward / movement / lifestyle / metatype
helpers). `pyproject.toml`:

```toml
[tool.ruff.lint.per-file-ignores]
"app/engine/__init__.py" = ["B023", "E402"]
```

Two independent reasons keep it alive:

| code | count | site | why it fires |
| --- | --- | --- | --- |
| **E402** | 15 blocks | `from .contacts import (...)` … `from .ware import (...)` + the `from .lookups import (...)` block, all at lines 86–499 | they sit **below** `def find_metatype` (line 69), the one definition still above them |
| **B023** | 9 spans | `_append_lifestyle_quality` closure, lines 761–807, inside `resolve_gear`'s `for inst in state.lifestyles:` loop | the nested fn closes over loop-body locals (`lifestyle_name`, `extras`, `seen_quality`, `kept_qualities`) + `nonlocal lp_used / quality_monthly / multiplier_pct` |

> Note: the current `pyproject` comment says B023 is about "the lifestyle
> **helper** `apply_lifestyle_cost_mod`". That's wrong — `apply_lifestyle_cost_mod`
> (line 529) is plain module scope. The real B023 site is the
> `_append_lifestyle_quality` **closure** inside the `resolve_gear` lifestyle
> loop. Fixing it means restructuring that loop, not moving the standalone
> helper (though the helper tags along for a tidy home).

Two tracks, fully independent — do in either order:

- **Track A — E402:** move `find_metatype` out, hoist the 15 import blocks to
  the top, drop `"E402"`.
- **Track B — B023:** extract the `resolve_gear` lifestyle cluster into
  `engine/gear/lifestyle.py` (the last gear category still inline), which
  turns the loop body into a function and kills the closure-over-loop-var,
  drop `"B023"`.

## Ground rules (unchanged from the prior sessions)

- Every commit individually green: `make check` (ruff check + ruff format
  --check + pytest **468 passed** + frontend). Plus the **snapshot gate**:
  `cd backend && python -m pytest -q tests/test_snapshot.py` → **6 passed**,
  byte-identical, before and after every code move. `UPDATE_SNAPSHOTS=1` is
  never needed here.
- Submodules import only `catalog` / `eval_formula` (`..data_loader`),
  `..improvements`, `..models`, `.constants`, and **already-extracted**
  engine modules. **Never** import back into `app.engine` — the graph stays
  a DAG. Breakage surfaces 100 % at pytest collection.
- `compute()` and `resolve_gear()` stay in `__init__.py`.
- F401 is enforced on `__init__.py`. Names re-exported for
  `store.py` / `chummer_export.py` / tests keep a
  `# noqa: F401  (re-exported for …)` marker; everything else that goes
  unused after a move is deleted. Grep `tests/ app/` before deleting.
- Commit trailers (this session):
  `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>` and
  `Claude-Session: <this session URL>`.
- Terminology enforced by `backend/tests/test_terminology.py`.

Shell: chain `cd backend &&
source .venv/bin/activate && <cmd>` in one Bash call — cwd resets after a
`git commit` and shell state doesn't persist between calls.

---

## Track A — retire E402 (1 commit)

### A1 — `find_metatype` → `engine/lookups.py`

`find_metatype(name, variant)` (lines 69–83) needs only `catalog()` — it's a
catalog accessor like the `_*_by_id` family already in `lookups.py`, just
public and metatype-shaped.

1. Move the body verbatim to the end of `engine/lookups.py` (after
   `_item_by_id`). `lookups.py` already imports `catalog` and `Any`.
2. In `__init__.py`, add `find_metatype` to the existing
   `from .lookups import (...)` block (the one currently at line 496) with
   `# noqa: F401  (re-exported for store.py / chummer_export.py / tests)`.
   External importers (`store.py:21`, `chummer_export.py:15`,
   `tests/test_engine.py:5` — ~90 call sites) keep importing it from
   `app.engine` unchanged.
3. `compute()` (line 930) uses it too, so it's a genuine import, not only a
   re-export — but keep the F401 marker anyway since the re-export is the
   contractual reason it's listed.

### A2 — hoist the 15 import blocks

With `find_metatype` gone, nothing sits between the top import group
(stdlib → `..data_loader` → `..improvements` → `..models` → `.constants`,
lines 3–66) and the first `def` (`resolve_attribute_selects`, was line 502).

- Move all of these, **in place / in order**, to sit directly after the
  `from .constants import (...)` block:

  ```
  .contacts .formulas .gear .karma .limits .magic .martial_arts
  .pricing .priority .qualities .resonance .selects .skills .ware
  ```
  then the `# Catalog single-row accessors live in engine/lookups.py.`
  comment + `from .lookups import (...)` block.

- Strip every block-level `# noqa: E402` from those 15 `from .X import (`
  lines. Keep the trailing prose in the same comment where it's useful
  (e.g. `# gear pipeline clusters; see engine/gear/`) — just the `noqa: E402`
  token goes.
- `.priority` line is `# noqa: E402, F401` → becomes `# noqa: F401`
  (whole block is re-exported for `store.py`).
- Keep every **per-line** `# noqa: F401` untouched (`spell_drain_value`,
  `tradition_resist`, `is_way_quality`, `sanitize_quality_ids`,
  `gear_extra_options`, `selectskill_options`,
  `quality_addspirit_extra_key`, …).
- `ruff check --fix` will re-sort the now-contiguous import section (I001).
  Let it. Confirm the diff is import-ordering only.

### A3 — `pyproject.toml`

`"app/engine/__init__.py" = ["B023", "E402"]` → `["B023"]` (Track B removes
the rest). Trim the E402 half of the explanatory comment.

Commit: `refactor(engine): move find_metatype to lookups.py, hoist engine
imports to top (retire E402 ignore)`

Risk: nil for the DAG — every `.X` module already imports only downward;
if any imported back into `app.engine` the current test collection would
already be red. The hoist just moves the same statements ~430 lines up.

---

## Track B — retire B023 (2 commits)

### B1 — `engine/gear/lifestyle.py`

The `resolve_gear` lifestyle block (lines ~746–868: the
`for inst in state.lifestyles:` loop + its `kept_lifestyles` /
`quality_specs` / `quality_by_name` setup) is the **only** gear category
still inline. Every sibling (`_resolve_optics`, `_resolve_sensors`,
`_resolve_programs`, …) is already its own `gear/*.py` with a `_resolve_*`
entry point that `resolve_gear` calls once.

New `app/engine/gear/lifestyle.py`:

```python
"""Lifestyle resolution: monthly cost, LP budget, lifestyle qualities
(freegrids + user picks + multipliers) and the post-resolve
lifestyle-cost-modifier bonus. The last gear category resolve_gear drives.

Imports only catalog (..data_loader), _item_by_id (..lookups), models —
never back into app.engine.
"""
```

Contents:

| name | from | shape |
| --- | --- | --- |
| `resolve_lifestyles(state) -> tuple[list[dict], int, list[str], list[tuple[str, list]]]` | new — wraps the loop | returns `(lifestyles_out, nuyen, warnings, bonus_sources)`, and sets `state.lifestyles = kept_lifestyles` internally (matches the in-place mutation `resolve_gear` does today) |
| `_resolve_one_lifestyle(inst, spec, quality_specs, quality_by_name, warnings, bonus_sources) -> dict` | the loop **body** | one lifestyle's resolved dict; `_append_lifestyle_quality` nests **here**, inside a function — no loop var to close over, so **B023 is gone** |
| `apply_lifestyle_cost_mod(gear, percent)` | `__init__.py:529`, verbatim | unchanged body |

Deps: `catalog` (`..data_loader`), `_item_by_id` (`..lookups`),
`LifestyleInstall` (`...models`). No `find_metatype`, no `eval_formula`.

Wire `gear/__init__.py`: add `apply_lifestyle_cost_mod`, `resolve_lifestyles`
to the imports + sorted `__all__` (mirrors the other `_resolve_*`).

Snapshot gate is the guard here — `tests/test_snapshot.py` exercises
lifestyle nuyen. Preserve **exactly**: freegrid derivation order,
`seen_quality.discard` for `allow_multiple` freegrids, the
`nonlocal lp_used / quality_monthly / multiplier_pct` accumulation, and the
`inst.quality_ids` / `inst.quality_extras` persistence (user picks only,
freegrids re-derived).

Commit: `refactor(engine): extract lifestyle resolution to engine/gear/lifestyle.py`

### B2 — wire `resolve_gear` + drop the ignore

- In `resolve_gear`, replace the inline block with one call, in the
  established style:
  ```python
  lifestyles, lifestyle_nuyen, lifestyle_warns, lifestyle_bonus = resolve_lifestyles(state)
  nuyen += lifestyle_nuyen
  warnings.extend(lifestyle_warns)
  bonus_sources.extend(lifestyle_bonus)
  ```
  Delete the now-dead `lifestyles: list[dict[str, Any]] = []` init (line 582)
  and the `kept_lifestyles` / `quality_specs` / `quality_by_name` locals.
- `compute()` re-imports `apply_lifestyle_cost_mod` from `.gear` (add to the
  `from .gear import (...)` block); delete the def from `__init__.py`.
- After the deletes, strip any now-unused `__init__.py` imports
  (`LifestyleInstall` from `..models` if nothing else uses it — grep first;
  it's likely still used by the `kept_lifestyles` type elsewhere → check).
- `pyproject.toml`: `"app/engine/__init__.py" = ["B023"]` →  the entry is now
  empty, so **delete the whole line** and its 5-line explanatory comment
  block (lines 31–37). `per-file-ignores` keeps only the `"tests/**"` row.

Commit: `refactor(engine): route resolve_gear lifestyles through the module, drop the B023/E402 ignore`

---

## Track C — docs (1 commit, fold into B2 if small)

- `docs/architecture.md` §"Planned refactors" item 1:
  - Add `gear/lifestyle.py` to the `engine/gear/` list.
  - Drop the "The mid-file `from .priority import (...)` … go away once …"
    bullet and the "*Next (own session)*" bullet — replace with a one-line
    "*Done:* the `["B023", "E402"]` ignore is retired; every engine import is
    top-of-file." The engine-split item is now fully **Done**.
- Append a "Done" section to this doc with the commit hashes.

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

After the final commit, confirm the ignore is truly gone:

```
cd backend && ./.venv/bin/ruff check --select B023,E402 app/engine/__init__.py
# expect: All checks passed!
grep -n "B023\|E402" pyproject.toml
# expect: no matches
```

Frontend is untouched but `make check` still runs it — no-op there.
