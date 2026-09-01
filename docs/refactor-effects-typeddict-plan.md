# Plan: type the `effects` dict as `EffectsDict`

Working doc for a dedicated session. Stage 4 (and last) of
`docs/refactor-ctx-bundles-plan.md` — the one bundle left over because it is
the biggest. Same playbook: incremental, every commit green, snapshot gate
byte-identical, `mypy` clean.

## Where we are

`effects` is the engine's central accumulator: `improvements/effects.py::
empty_effects()` seeds it, `improvements/nodes/{stats,skills,magic,social}.py`
mutate it via `apply_bonus_nodes`, and ~25 engine modules read it. Every key
is `Any`, so `effects.get("initiave_dice")` (typo) silently returns `None`.
The other 16 `Ctx` bundles are now `TypedDict`s; this is the hold-out.

### Survey (measured, not guessed)

| fact | value |
| --- | --- |
| keys seeded by `empty_effects()` | **133** |
| keys written by `improvements/nodes/**` not in the schema | **0** — every write is a string literal already in `empty_effects()` |
| keys written by engine code outside `improvements/` | **1** — `add_spirit_picks` (`engine/magic/spirits.py`, set by `bind_extra_spirits`) |
| keys read in `engine/**` not in the schema | same 1 (`add_spirit_picks`) |
| `effects: dict[str, Any]` param declarations | **~54**, across **23 files**, all under `app/engine/` + `app/improvements/` |
| uses outside `app/engine` + `app/improvements` | **none** (`store.py`, API, `data_loader`, tests don't type it; `test_improvements_nodes.py` gets it via `empty_effects()`) |
| dynamic `effects[<var>]` access | **1** — `nodes/skills.py:23`, `key = "skill_group_mods" if tag=="skillgroup" else "skill_category_mods"` |
| `effects: dict[str, Any] \| None` + `(effects or {}).get(...)` idiom | **~10 sites** (`magic/spells.py`, `magic/_common.py`, `resonance.py`, `gear/weapons.py`, `compute/_career.py`) |

So the schema is **134 keys** (`empty_effects()` + `add_spirit_picks`), the
write side already conforms to `total=True`, and the blast radius is bounded
to two packages with no API/store/test churn.

## Target

New `EffectsDict(TypedDict)` in `app/improvements/effects.py`, next to
`empty_effects()` (which produces it). `improvements` imports nothing from
`engine`, so `engine` importing `EffectsDict` from `improvements` keeps the
DAG. Value types: scalars (`int` / `bool` / `float`) and the obvious nested
dicts typed precisely —

- `attribute_bonus`, `attribute_max_mods`, `test_mods`,
  `spell_defense_resist`, `special_armor`, `walk_multiplier`,
  `run_multiplier`, `sprint_bonus` → `dict[str, int]`
- `immunities` → `dict[str, bool]`
- `movement_replace` → `dict[tuple[str, str], int]`
- `living_persona` → `dict[str, int]`
- `enabled_tabs` → `set[str]`

— and the ~40 `*_mods` / `*_slots` / `grant_*` / `add_*` lists stay
`list[dict[str, Any]]` (their row shapes are out of scope, exactly as with
the other bundles). `Ctx.effects: EffectsDict = field(default_factory=empty_effects)`.

`empty_effects() -> EffectsDict`; `apply_bonus_nodes` and the four
`nodes/*.py` `apply(...)` handlers take `EffectsDict`;
`special_armor_totals` / `compact_limit_modifiers` too. Then the ~54
`effects: dict[str, Any]` params across `engine/` flip to `EffectsDict`
(mechanical), with the friction points below fixed as they surface.

### Known friction

1. **`nodes/skills.py:23`** — `effects[key].append(...)` with
   `key: str`. Fix: inline the two-way branch
   (`effects["skill_group_mods"].append(...)` /
   `effects["skill_category_mods"].append(...)`), or a one-line `cast`.
2. **`(effects or {}).get(...)`** — `{}` is not an `EffectsDict`. Fix: for
   the ~10 read-only helpers, either take a non-optional `EffectsDict` and
   pass `empty_effects()` at the (few) `None` call sites, or replace
   `effects or {}` with an `empty_effects()` fallback. Prefer the former
   where the call sites are internal.
3. **`add_spirit_picks`** — add it to the schema; `bind_extra_spirits`
   already writes it, `assemble.py` already reads it. TypedDict makes the
   contract explicit (no behaviour change).
4. **`warn_return_any` in `compute/`** (from the mypy override) — helpers
   that `return effects.get("x")` from a `-> int` function now need
   `int(... or 0)`. Expect a handful.
5. **`collect_effects`** (`improvements/__init__.py`) builds a fresh
   `empty_effects()`, folds nodes, then does
   `effects["enabled_tabs"] = sorted(effects["enabled_tabs"])` — turning the
   `set[str]` into a `list[str]`. Later `compute/qualities.py` /
   `magic.py` / `gear.py` re-`set(...)` it. So `enabled_tabs` legitimately
   holds **`set[str]` early, `list[str]` after `collect_effects`, `set`
   again in `compute`**. Type it `set[str] | list[str]` and accept the
   union at the ~4 touch points, or (cleaner) stop the in-place type-swap:
   have `collect_effects` keep `enabled_tabs` a set and let its callers
   sort at the point they actually need an ordered list. Decide in commit 1.

## Commits

1. **`EffectsDict` + the write side** — define the `TypedDict`; annotate
   `empty_effects()`, `collect_effects`, `apply_bonus_nodes`, the four
   `nodes/*.py` `apply()` handlers, `special_armor_totals`,
   `compact_limit_modifiers`. Fix friction #1, #3. `improvements/` only.
2. **`Ctx.effects` + the `compute/` phases** — field annotation +
   `compute/{qualities,magic,gear,finalize,assemble,_career}.py`. This is
   the strict-override package, so friction #4 lands here.
3. **the engine read side** — the remaining `effects: dict[str, Any]`
   params: `magic/{spells,_common,spirits,initiation}.py`,
   `resonance.py`, `skills.py`, `gear/{weapons,drugs}.py`, `limits.py`,
   `pricing.py`, `qualities.py`, `contacts.py`, `martial_arts.py`. Fix
   friction #2. Split 3a/3b if the diff is unwieldy.
4. **docs** — `architecture.md` (the effects-dict section + the
   "Planned refactors" note), `refactor-ctx-bundles-plan.md` stage 4 →
   done, and this doc's Done section.

## Risks / notes

- **No behaviour change** is the whole point — `tests/snapshots/*.json`
  must not move. `TypedDict` is a plain `dict` at runtime; the only code
  edits are annotations plus the handful of friction fixes, none of which
  change values.
- `total=True` is safe (survey confirms no out-of-schema writes). Do **not**
  reach for `total=False` — it would silence the very typos this exists to
  catch.
- If a genuine bug surfaces (a real key typo, a wrong-typed default), fix it
  in its own commit with a note, don't fold it into the mechanical sweep.
- Consider adding `app.improvements.*` to the strict `mypy` override once
  this lands and the package is clean to that bar.

## Verification per commit

```
cd backend && ./.venv/bin/python -m pytest -q && ./.venv/bin/ruff check . \
  && ./.venv/bin/ruff format --check . && ./.venv/bin/mypy
```

`tests/test_snapshot.py` first (byte-identical gate);
`tests/test_compute_phases.py` guards the phase seams.
