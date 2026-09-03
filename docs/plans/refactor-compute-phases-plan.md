# Plan: split `compute()` into phases

Working doc. `app/engine/__init__.py` is **1,955 lines**; `compute()` alone is
**~1,200** (lines 758–1955) — the last monolith. It is a straight-line
pipeline whose only real difficulty is its working set: ~200 interdependent
locals threaded top-to-bottom.

## Current shape of `compute()`

| # | lines | phase | key outputs |
|---|-------|-------|-------------|
| 1 | 758–800 | **bootstrap** | `build_method`, `career`, reward totals, skill caps, `errors` seed, `meta`, `attrs_spec`, ware sanity (side conflicts, required warnings) |
| 2 | 800–830 | **qualities** | `talent`, `qualities`, `free_quality_ids`, grade-effect ware clamps, `mentor`, `sources` |
| 3 | 830–870 | **ware** | `cyber_installed`, `bio_installed`, quality sides, `installed`, `hosted_ids`, `ware_attr_bonus` (+ chargen cap) |
| 4 | 870–900 | **effects** | `effects = collect_effects(sources)`, excon ban, every `bind_*`, granted spells/powers, `attr_max_bonus`, cyberseeker → `limb_quality` |
| 5 | 900–930 | **essence** | `ess_start`, `ess_lost_{cyber,bio}`, `ess`, `mag_penalty`, cyberadept RES reduction, `initiate_grade` / `submersion_grade` |
| 6 | 930–970 | **attributes** | the `ratings` dict (racial min/max, MAG/RES caps, ESS) |
| 7 | 970–1010 | **initiation/submersion** | `initiation`, `submersion`, free metamagics / granted echoes, their bonus nodes |
| 8 | 1010–1070 | **foci/adept** | `qi`, `foci`, `focus_limits`, tradition bonuses, `adept`, `state.mystic_pp`, `enhancements`, `attr_totals` |
| 9 | 1070–1130 | **gear** | `gear = resolve_gear(...)`, lifestyle/erased/reach/DV, Black-Market-Pipeline resolve, purchase discounts, overclocker, trust-fund, active drugs, weapon-focus dice |
| 10 | 1130–1160 | **totals** | power-pool check, `total` (ratings + attribute_bonus), `limb_replace` |
| 11 | 1160–1210 | **magic/resonance** | `magic` (spells), `spirits`, `resonance` (complex forms), `techno_sprites`, adept spell-select force, tab enables |
| 12 | 1210–1290 | **priority points** | `attr_row`…`her_row`, `special_from_meta`, `spent_physical/special`, `nuyen_karma_max`, is-karma branch, `nuyen_pool`, `nuyen_spent`, `nuyen` |
| 13 | 1290–1400 | **skills** | groups, `skill_picks`, per-skill cost, `exotic`, `knowledge`, `skill_mods`, `skillsofts`, `expertises`, `specs`, `effective_skills/knowledge` |
| 14 | 1400–1470 | **karma totals** | `karma_from_q`, `mystic_karma`, `spell_karma`, is-karma branch (attr/skill/knowledge karma), career baseline + `career_raise_karma` |
| 15 | 1470–1560 | **social** | `contacts`, `martial_ctx`, `martial`, unarmed bonuses, `karma_left`, `karma_spend_lines`, `nuyen_spend_lines`, notoriety / public awareness |
| 16 | 1560–1620 | **derived stats** | `physical/mental/social_limit`, `cm_phys/stun`, `initiative`, spirit/focus/complex-form/sprite test attachment |
| 17 | 1620–1660 | **quality rules** | `movement`, `apply_quality_rules` → `negative_quality_karma`, `quality_report` |
| 18 | 1660–1760 | **validate** | rating-6 / natural-max, point-overspend (Priority), karma/nuyen negative, chargen leftover, essence≤0, capacity, heritage-metatype, avail / device-rating limits |
| 19 | 1760–1955 | **assemble** | `state.derived = { … }` — ~195-line dict literal reading ~80 locals |

Private helpers only `compute()` uses, also in `__init__.py`:
`resolve_gear` (228 L), `resolve_movement`, `resolve_attribute_selects`,
`default_attributes`, `_effective_attr_spec`. Plus the career-layer
`snapshot_career_baseline` / `career_raise_karma` / `nuyen_spend_breakdown` /
`sync_reward_totals` (compute-only, but `store.py` + `test_engine.py` also
import `snapshot_career_baseline` and `default_attributes` by name).

## Target

```
app/engine/compute/
  __init__.py     # compute(state) orchestrator; re-exports resolve_gear etc.
  context.py      # @dataclass Ctx — state + data + every intermediate (typed)
  bootstrap.py    # phase 1
  qualities.py    # phases 2 + 4  (quality gather + effects + binders)
  ware.py         # phase 3
  essence.py      # phases 5 + 6  (essence penalty + the ratings loop)
  magic.py        # phases 7 + 8 + 11  (initiation/submersion/foci/adept + spells/spirits/resonance)
  gear.py         # phase 9  (hosts the moved resolve_gear + post-gear application)
  economy.py      # phases 12 + 13 + 14 + 15  (points / skills / karma / social)
  finalize.py     # phases 10 + 16 + 17 + 18  (totals check, limits/CM/init, quality rules, validation)
  assemble.py     # phase 19
```

`compute()` becomes:

```python
def compute(state: CharacterState) -> CharacterState:
    ctx = Ctx(state=state, data=catalog())
    for phase in (bootstrap, qualities, ware, effects_and_binders, essence,
                  attributes, magic, gear, totals, economy, finalize):
        phase(ctx)
    assemble(ctx)
    return ctx.state
```

Each `phase(ctx: Ctx) -> None` reads and writes `ctx.*`. `Ctx` is large
(~150 fields) but that is the honest working set; every field gets a type
and a `field(default_factory=…)` so `Ctx(state=…, data=…)` constructs.

`engine/__init__.py` keeps its re-export barrel — adds
`from .compute import compute, resolve_gear, resolve_movement,
default_attributes, resolve_attribute_selects` (with the existing
`# noqa: F401 (re-exported for store.py)` style). `from app.engine import
compute` and every current name stay importable.

## Commits

1. **relocate, no logic change** — move `compute`, `resolve_gear`,
   `resolve_movement`, `resolve_attribute_selects`, `default_attributes`,
   `_effective_attr_spec` verbatim into `engine/compute/__init__.py`; barrel
   re-exports. `engine/__init__.py` ~1,955 → ~760. Snapshot byte-identical.
2. **`Ctx` dataclass** — add `context.py`; rewrite the *one* `compute()` body
   to fill `ctx = Ctx(...)` and read `ctx.foo` instead of bare locals. Still
   one function, still in `compute/__init__.py`. This is the invasive rename;
   `test_snapshot.py` + 477 tests guard it.
3. **peel bootstrap + ware + essence** → `bootstrap.py` / `ware.py` /
   `essence.py`; `compute()` calls them.
4. **peel qualities + magic** → `qualities.py` / `magic.py`.
5. **peel gear** → `gear.py` (carries `resolve_gear` in with it).
6. **peel economy** → `economy.py` (points / skills / karma / social).
7. **peel finalize + assemble** → `finalize.py` / `assemble.py`;
   `compute/__init__.py` is now just the `Ctx` build + the phase loop.
8. **docs** — `architecture.md` "Planned refactors" item + a Backend section
   note; this doc's Done section.

Commits 3–7 may split further if a phase's `ctx` slice is still unwieldy;
the career-layer helpers can move to `compute/_career.py` in commit 6 or stay
put — decide when economy lands.

## Risks / notes

- **`Ctx` + mypy** — every field typed; the one existing
  `total["ESS"] = ess  # type: ignore[assignment]` moves with the code. Watch
  the loop-variable-reuse trap (`bonus` is rebound inside phase 11) that bit
  the earlier engine split — rename per scope.
- **No behaviour change** is the whole point: `backend/tests/snapshots/*.json`
  must not move. If a diff appears, it's a bug in the split, not the golden.
- `resolve_gear` already returns a bundle dict — it stays a plain function
  taking explicit args, called from the `gear` phase, not a `Ctx` mutator.
- Order is load-bearing (e.g. `effects` binders run before the `ratings`
  loop; `attr_totals` before `resolve_gear`). The phase list encodes it;
  don't reorder.

## Verification per commit

```
cd backend && ./.venv/bin/python -m pytest -q && ./.venv/bin/ruff check . \
  && ./.venv/bin/ruff format --check . && ./.venv/bin/mypy
```

`tests/test_snapshot.py` is the byte-identical gate; run it first.

## Done

All 8 commits landed on `refactor/gear-weapons-vehicles`; 477 backend tests
pass, snapshots byte-identical, ruff + mypy clean throughout.

| commit | what |
|--------|------|
| 1 | relocate `compute` + `resolve_gear` / `resolve_movement` / `resolve_attribute_selects` / `default_attributes` / `_effective_attr_spec` verbatim into `engine/compute/__init__.py`; `engine/__init__.py` → pure re-export barrel (~250 L) |
| 2 | `context.py` — `@dataclass Ctx`; `compute()` body rewritten to fill / read `ctx.*` |
| 3 | peel `bootstrap.py` (+ `sync_reward_totals`) / `ware.py` / `essence.py` |
| 4 | peel `qualities.py` (gather + effects + binders, + `resolve_attribute_selects`) / `magic.py` (awakened + spells) |
| 5 | peel `gear.py` (carries `resolve_gear`) |
| 6 | peel `economy.py` (points / skills / karma / social); career helpers → `_career.py` |
| 7 | peel `finalize.py` (totals + limits/CM/init + quality rules + validation, carries `resolve_movement`) / `assemble.py` (`state.derived`, carries `_effective_attr_spec`); `compute/__init__.py` → ~60 L (`Ctx` build + phase loop) |
| 8 | docs — this section + `architecture.md` |

Deviations from the sketch above: phase functions kept explicit calls rather
than a literal tuple loop, and split finer than the 11-name list — `gather` /
`effects_and_binders` (phase 2 + 4), `awakened` / `spells` (7+8 / 11),
`gear_phase`, `totals` / `finalize` (10 / 16+17+18). `Ctx` landed at ~150
fields as predicted. `bonus` stayed a plain local in `totals()` (rebound to
an int inside the spell-focus loop in `spells()`).
