# Plan: split `engine/gear/` (weapons → vehicles → orchestrator), then `engine/magic/`

Working doc for a dedicated session. Companion to `docs/architecture.md` §"Planned
refactors" item 1.

## Where we are

`app/engine/__init__.py` is **4,878 lines** (from ~10,475 at the start of the
split). Extracted:

- `engine/lookups.py`, `constants.py`, `priority.py`, `formulas.py`, `karma.py`,
  `pricing.py`, `selects.py`, `requirements.py`, `dice.py`
- `engine/gear/`: `_common.py`, `drugs.py`, `matrix.py`, `armor.py`, `optics.py`,
  `sensors.py`, `programs.py`, `apps.py`, `ammo.py`, `weapons.py`, `vehicles.py`,
  `misc.py`
- `engine/magic/`: `_common.py`, `powers.py`, `mentor.py`, `foci.py`,
  `spirits.py`, `spells.py`, `initiation.py`, `submersion.py`

`resolve_gear()` and `compute()` stay in `__init__.py` as orchestrators.
Steps 1–4 (gear) and Step 5 (magic) are **done**; Step 6 (mid-file import
cleanup) is not.

## Ground rules (unchanged)

- Every commit individually green: `make check` (ruff check + ruff format --check
  + pytest `468 passed` + frontend tsc/eslint/prettier/build).
- Submodules import only `catalog` / engine `constants` / already-extracted
  engine modules / models. **Never** import back into `app.engine` — keeps the
  import graph a DAG. Import breakage surfaces 100 % at pytest collection.
- `compute()` and `resolve_gear()` stay in `__init__.py`. `_ensure_*` mutators
  (`_ensure_weapon_accessories`, `_ensure_drone_equipment`, `_ensure_misc_gear`)
  move **with** their cluster.
- `__init__.py` keeps re-exporting every name `store.py` / `chummer_export.py` /
  tests import — via `gear/__init__.py`'s `__all__` and the mid-file
  `from .gear import (...)  # noqa: E402` block.
- **Snapshot gate:** run `tests/test_snapshot.py` before and after each move;
  require byte-identical output. This is the code-motion safety net the leaf
  extractions didn't have. `UPDATE_SNAPSHOTS=1` only when a change is
  intentional (it won't be here).
- Commit trailers:
  `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>` and
  `Claude-Session: https://claude.ai/code/session_01VPrtYHJPX12Bqw8danc3hX`.
- Terminology enforced by `backend/tests/test_terminology.py`.

## Extraction mechanics (established pattern)

1. `sed -n 'A,Bp' app/engine/__init__.py > /tmp/x.txt` for each cluster range.
2. Python heredoc writes `app/engine/gear/<name>.py` = module docstring + correct
   relative imports + bodies.
3. `ruff check --fix && ruff format` the new file.
4. Python heredoc deletes each cluster from `__init__.py`: locate `def NAME(` →
   next top-level `def `/`class `, assert the two preceding lines are blank,
   delete, splice back exactly two blank lines.
5. Wire `gear/__init__.py` (import + sorted `__all__`) and the `__init__.py`
   re-import block.
6. Manually remove now-unused imports from `__init__.py` (ruff does **not**
   auto-fix F401 inside `__init__.py`; grep-confirm one remaining occurrence =
   the import line).
7. `ruff check --fix && ruff format && ruff check && ruff format --check &&
   python -m pytest -q` → `468 passed`.
8. Snapshot check, then commit.

Shell: chain `source .venv/bin/activate && <cmd>` in one Bash call — state does
not persist between calls.

---

## Step 1 — `gear/weapons.py`

Bigger and more entangled than the leaf clusters. Recommend **3 sub-commits**.

### Shared-helper triage first

The weapon range references these non-local helpers (all already extracted or
trivially movable):

| helper | home | action |
| --- | --- | --- |
| `catalog`, `eval_formula` | `data_loader` | import in new module |
| `_item_by_id` | `engine/lookups.py` | import |
| `substitute_rating` | `engine/improvements.py` | import |
| `parse_capacity` | `data_loader` | import |
| `_clamp_rating`, `_device_rating_of`, `_capacity_value`, `_program_label` | `gear/_common.py` | import |
| `ammo_fits_weapon` | `gear/ammo.py` | import |
| `gear_extra_options` | `engine/selects.py` | import |
| `_leading_int` | `engine/formulas.py` | import |
| `_add_signed_stat`, `_set_damage_type` | `engine/formulas.py` | import if referenced (they were removed from `__init__` imports earlier — re-check) |

`_pick_accessory_mount` / `_find_mount_part` / `_default_mount_parts` are shared
between **weapons and vehicles** → put them in `gear/_common.py` in sub-commit 1a,
imported by both `weapons.py` and (Step 2) `vehicles.py`.

### 1a — constraint + accessory-fit + mount primitives → `_common.py`

Move to `gear/_common.py`:

- `_has_weapon_constraints`      (`__init__.py:987`)
- `_weapon_matches_or`          (`993`)
- `accessory_fits_weapon`       (`1015`)
- `_pick_accessory_mount`       (`1032`)
- `_find_mount_part`            (`1509`)
- `_default_mount_parts`        (`1521`)

Check each for deps; `_find_mount_part` / `_default_mount_parts` use `catalog` +
`_item_by_id` only. `vehicle_matches` (`1428`) / `mod_fits_vehicle` (`1453`) are
the same constraint family but vehicle-only — leave them for Step 2 unless a
weapon helper turns out to need them. Commit: `refactor(engine): move weapon/vehicle constraint &
mount primitives to gear/_common`.

### 1b — `gear/weapons.py` core

Move (ranges from current `__init__.py`):

- `_public_weapon`                (`513–560`)
- `_append_gear_weapons`          (`561–587`)
- `_drone_mod_limb_attrs`         (`588–642`) — used by ware-weapon attrs
- `_ware_weapon_attr_values`      (`643–677`)
- `_apply_ware_weapon_attrs`      (`678–693`)
- `_append_ware_weapons`          (`694–724`)
- `apply_reach_bonus`             (`1110–1118`)
- `_is_unarmed_weapon`            (`1119–1124`)
- `apply_weapon_category_dv`      (`1141–1160`)
- `weapon_skill_dictionary_key`   (`1161–1193`)
- `apply_weapon_skill_accuracy`   (`1194–1211`)
- `_ensure_weapon_accessories`    (`1212–1252`)
- `_apply_modify_ammo_capacity`   (`1253–1269`)
- `_apply_recoil_totals`          (`1270–1288`)
- `_resolve_weapon_accessories`   (`1289–1397`)
- `_commlink_accessory_parent_spec` (`502–512`) — check caller; may belong here

Watch: `_public_weapon` and `_append_ware_weapons` take `state` / `attr_totals`
args — no `app.engine` import needed, they receive everything. `bind_*` binders
stay for 1c.

Commit: `refactor(engine): extract weapon resolution to gear/weapons.py`.

### 1c — DV / skill-accuracy binders

- `bind_weapon_category_dv`   (`__init__.py:2758`)
- `bind_weapon_skill_accuracy` (`2792`)

Small, sit far from the cluster (line ~2758), called from `compute()`. Move to
`gear/weapons.py`, re-export. Commit: `refactor(engine): move weapon DV/accuracy
binders to gear/weapons.py`.

---

## Step 2 — `gear/vehicles.py` (largest cluster)

After Step 1, mount primitives already live in `_common.py`. Move:

- `_vehicle_interior_parent_spec`  (`494–501`)
- `_leading_vehicle_stat`          (`1398–1404`)
- `_format_vehicle_stat`           (`1405–1412`)
- `_vehicle_extras`                (`1413–1427`)
- `_apply_vehicle_bonus`           (`1469–1497`)
- `_clamp_vehicle_rating`          (`1498–1508`)
- `_host_is_drone`                 (`1580–1583`)
- `_add_vehicle_slot_use`          (`1584–1596`)
- `_finalize_vehicle_slots`        (`1597–1633`)
- `_iter_vehicle_hosts`            (`1634–1648`)
- `_ensure_drone_equipment`        (`1649–1744`)
- `_resolve_vehicle_mods`          (`1745–1812`)
- `_resolve_weapon_mounts`         (`1813–1903`) — takes `weapons` list arg; fine
- `_resolve_drones`                (`1904–1964`)
- `_publish_drone_stats`           (`1965–1991`)

Leave in `__init__.py` (they touch `state` broadly / run in the ware pipeline,
not gear): `_vehicle_mod_hosts` (`4134`), `_ware_fits_vehicle_mod` (`4149`),
`_drop_invalid_vehicle_ware` (`4161`), `_vehicle_hosted_ware_ids` (`4183`),
`_zero_vehicle_hosted_essence` (`4208`), `_attach_ware_to_vehicle_mods` (`4216`).
Re-check their deps before deciding — if they only need vehicle helpers, they can
come too, but the ware pipeline is a separate future `engine/ware/` split.

Possible sub-commits: (2a) stat-format + bonus + slot helpers; (2b)
`_ensure_drone_equipment` + the three `_resolve_*` + `_publish_drone_stats`.

Commit(s): `refactor(engine): extract vehicle/drone resolution to
gear/vehicles.py`.

---

## Step 3 — `gear/misc.py`

- `_misc_external_hosts`   (`725–750`)
- `_misc_child_fits`       (`751–766`)
- `_misc_slot_stats`       (`767–777`)
- `_ensure_misc_gear`      (`778–841`)
- `_resolve_misc_gear`     (`842–986`)

`resolve_gear()` (`2135–2482`) **stays** in `__init__.py` and imports
`_resolve_misc_gear` from `.gear`. This is the last gear cluster; after it,
`__init__.py`'s gear surface is just the `resolve_gear` orchestrator +
`_finalize_avail_tree` / avail & device-rating limit checks (those are chargen
validation, leave them).

Commit: `refactor(engine): extract misc-gear resolution to gear/misc.py`.

---

## Step 4 — docs + cleanup

- Update `docs/architecture.md` §"Planned refactors" item 1: mark
  weapons/vehicles/misc done, note new `__init__.py` line count.
- If the lifestyle-quality helper (`apply_lifestyle_cost_mod`, `__init__.py`
  ~1071) has by now moved to a module, drop the mid-file `# noqa: E402` blocks
  and the `["B023", "E402"]` per-file ignore in `pyproject.toml` and hoist the
  `from .gear import ...` / `from .selects import ...` imports to the top. (Only
  if `find_metatype` no longer sits above them — recheck.)

---

## Step 5 — `magic/` — **done**

`app/engine/__init__.py`: 7,060 → 4,878 lines. Thirteen green commits:

1. `quality_*_extra_key` → `engine/constants.py`
2. `_metamagic_by_*` / `_magic_art_by_id` / `_echo_by_*` → `engine/lookups.py`
3. `requirement_tree_met` (+ `_requirement_item_met` / `_pool_rating`) →
   new `engine/requirements.py` (shared with qualities + martial arts)
4. `_skill_spec` / `skill_dice_pool` / `magic_opposed_test` → new
   `engine/dice.py` (shared with the technomancer test-attachers)
5. `engine/magic/_common.py` — `spell_drain_value`, `tradition_resist`,
   `_active_skill_rating_from_state`, `spell_cast_info` (+ its
   `_spell_category`/`_spell_descriptor` mod helpers), `_magic_grade_discount`
6. `magic/powers.py` — `resolve_adept_powers` + `power_*` + Way discounts
7. `magic/mentor.py` — `resolve_mentor` + `_choice_allowed`
8. `magic/foci.py` — `resolve_foci` / `resolve_qi_foci` /
   `attach_weapon_focus_dice` (landed here — mutates the weapon rows compute()
   passes, pulls in nothing weapon-specific) / `apply_focus_limits` /
   `attach_focus_tests`
9. `magic/spirits.py` — `resolve_spirits` / `bind_extra_spirits` /
   `attach_spirit_tests` / `spirit_attributes` (`sprite_attributes` stays —
   technomancer)
10. `magic/spells.py` — `resolve_spells` + the `bind_spell_*` /
    `apply_granted_spells` / `apply_tradition_bonuses` / `spell_defense_pools` /
    `free_spell_bonus_points` / `spell_karma_cost` cluster
11. `magic/initiation.py` — `resolve_initiation` / `apply_free_metamagics` +
    grade-karma helpers
12. `magic/submersion.py` — `resolve_submersion` + grade-karma helpers

Snapshot (`tests/test_snapshot.py`, 6 fixtures incl. hermetic mage / adept /
technomancer) byte-identical before and after every move; `468 passed`
throughout.

Still in `__init__.py` for a future `engine/resonance/` split: `sprite_attributes`,
`resolve_complex_forms`, `resolve_sprites`, `attach_complex_form_tests`,
`attach_sprite_tests`, `living_persona`, `_echo_by_name`, `apply_granted_echoes`,
`_cyberadept_res_penalty_reduction`.

## Step 6 — mid-file import cleanup (not done)

`apply_lifestyle_cost_mod` (a loop-local closure → the `B023` ignore) and
`find_metatype` still sit above the mid-file `from .xxx import (...)` blocks, so
the `["B023", "E402"]` per-file ignore in `pyproject.toml` and the `# noqa: E402`
blocks stay. To finish: move `apply_lifestyle_cost_mod` (lifestyle/quality
helper) to its own module and hoist `find_metatype` (or accept it below the
imports), then delete the ignore and lift every `from .xxx import` to the top.

---

## Quick verification checklist per commit

```
source .venv/bin/activate && \
  ruff check app/ && ruff format --check app/ && \
  python -m pytest -q && \
  python -m pytest -q tests/test_snapshot.py
# expect: 468 passed; snapshot 6 passed, no diff
git --no-pager diff --stat
```

Frontend is untouched by this work but `make check` still runs it — no-op there.
