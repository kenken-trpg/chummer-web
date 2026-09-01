# Plan: split `app/data_loader.py` into a `data_loader/` package

Working doc for a dedicated session. Fourth in the series
(`docs/refactor-{gear-weapons,ware-qualities,engine-e402-b023,improvements}-plan.md`).
Same playbook: incremental, every commit green, snapshot gate byte-identical.

## Where we are

`app/data_loader.py` is **2,864 lines** — now the largest backend file.
Shape:

| layer | lines | contents |
| --- | --- | --- |
| paths + XML primitives | 13–61 | `VENDOR` / `DATA_DIR` / `LANG_DIR` / `OVERRIDE_DIR`, `ATTR_KEYS` / `PHYSICAL_ATTRS` / `SPECIAL_ATTRS`, `_text` / `_int` / `_float` / `_child` / `_int_text` |
| formula / avail / capacity | 63–196 | `eval_formula`, `parse_avail` / `format_avail` / `sum_avail`, `parse_capacity` / `split_capacity`, `CHARGEN_*` |
| bonus / requirement / select parsing | 297–520, 593–679, 972–1049 | `parse_bonus` / `_bonus_fields`, `parse_required` / `_parent_name_requirements`, `parse_requirement_tree` / `_parse_requirement_node`, `parse_select_power_slot` / `_specific_powers`, `quality_needs_extra` / `quality_extra_meta`, the `_limit_*_needs_select` / `_weapon*_select*` / `_filter_active_skill_names` / `selecttext_catalog_options` helpers + `MATRIX_ACTION_OPTIONS` / `SPELL_SELECT_CATEGORIES` / `STANDARD_SPIRIT_NAMES` |
| **52 `load_*` domain loaders** | scattered | ware, metatypes, skills, qualities, magic (powers/spells/spirits/foci/…), weapons, armor, gear, vehicles, lifestyle, drugs, martial arts, priorities, translations |
| `catalog()` | 2718–2860 | `@lru_cache` assembler — calls every `load_*`, does the cross-wiring (weapon↔gear ids, drug effects onto gear, quality `select_options`), returns the mega-dict. `reset_catalog()` clears the cache. |

Domain loaders are near-independent: each parses one vendored XML file →
`list[dict]`. Cross-entity wiring all happens in `catalog()`. Helpers
(`_load_grades`, `_load_ware_items`, `_parse_metatype`, `_skill_specs`,
`_load_gear_categories`, `_load_vehicle_entries`) are each used only within
their own domain — verified by grep.

### External API surface (must stay `from app.data_loader import …`)

Grep of `app/ tests/`:

| kind | names |
| --- | --- |
| constants | `PHYSICAL_ATTRS`, `MATRIX_ATTRIBUTES`, `PROGRAM_HOSTS`, `SPELL_CAST_CATEGORIES`, `SPELL_CATEGORIES`, `CHARGEN_AVAIL_MAX`, `CHARGEN_DEVICE_RATING_MAX`, `CHARGEN_WARE_ATTR_BONUS_MAX`, `OVERRIDE_DIR`, `LANG_DIR` |
| functions | `catalog`, `reset_catalog`, `eval_formula`, `parse_avail`, `format_avail`, `sum_avail`, `parse_capacity`, `parse_select_power_slot`, `selecttext_catalog_options`, `drug_effect_summary`, `drug_node_value`, `load_translations`, `load_ui_strings`, `_load_ja_overrides` |

`data_loader/__init__.py` re-exports every one of these via `__all__` — **no
importer changes**. (Engine modules use `..data_loader` / `...data_loader`;
those keep resolving to the package.)

## Target layout

```
app/data_loader/
  __init__.py       # barrel: re-export the API above + catalog() + reset_catalog()
  _xml.py           # paths, ATTR_KEYS/PHYSICAL_ATTRS/SPECIAL_ATTRS, _text/_int/_float/_child/_int_text, log
  formulas.py       # eval_formula, parse_avail/format_avail/sum_avail, parse_capacity/split_capacity, CHARGEN_*
  bonus.py          # parse_bonus, parse_required, parse_requirement_tree, parse_select_power_slot,
                    #   quality_needs_extra/quality_extra_meta, the *_needs_select / select helpers,
                    #   selecttext_catalog_options, MATRIX_ACTION_OPTIONS / SPELL_SELECT_CATEGORIES / STANDARD_SPIRIT_NAMES
  loaders/
    __init__.py     # re-export every load_* the barrel + catalog() need
    ware.py         # CORE_GRADES, _load_grades, _load_ware_items, load_cyberware, load_bioware
    metatypes.py    # _parse_metatype, load_metatypes
    skills.py       # _skill_specs, load_skills
    qualities.py    # load_qualities
    magic.py        # powers, enhancements, mentors, spells, traditions, spirits, complex_forms,
                    #   streams, sprites, foci, focus_formulae, metamagics, magic_arts, echoes, qi_focus
                    #   + SPELL_CAST_CATEGORIES / SPELL_CATEGORIES / CATEGORY_SKILL / SPIRIT_* / MATRIX_ATTRIBUTES
    weapons.py      # load_weapons, load_weapon_ranges, load_weapon_accessories, load_weapon_mounts
                    #   + SKIP_WEAPON_CATEGORIES / _RANGE_BANDS
    armor.py        # load_armor, load_armor_mods
    gear.py         # _load_gear_categories, load_commlinks/cyberdecks/rccs/optics/gear/programs/apps/sensors
                    #   + PROGRAM_HOSTS / GEAR_* / _extra_kind
    vehicles.py     # load_vehicle_names, load_vehicle_mods, load_weapon_mounts?, _load_vehicle_entries,
                    #   load_drones, load_vehicles  (weapon_mounts can live here or in weapons — decide at cut time)
    lifestyle.py    # load_lifestyles, load_lifestyle_qualities
    drugs.py        # drug_node_value, drug_effect_summary, load_drug_components, load_drug_grades, _DRUG_LIMIT_LABEL
    martial_arts.py # load_martial_art_techniques, load_martial_arts
    priorities.py   # load_priorities
    translations.py # _load_ja_overrides, load_translations, load_ui_strings
```

Import direction: `loaders/*` → `bonus` / `formulas` / `_xml` (+ each
other never — cross-wiring stays in `catalog()`). `bonus` → `_xml`.
`formulas` → (stdlib only). `__init__` → everything. A DAG; a cycle
surfaces at pytest collection.

## Ground rules (unchanged)

- Every commit green: `make check` (ruff + `pytest 469 passed` + frontend).
  Plus the snapshot gate: `python -m pytest -q tests/test_snapshot.py` →
  `6 passed`, byte-identical, before/after every move.
- No behaviour change — pure relocation. `catalog()` output identical.
- `data_loader/` submodules import only stdlib + each other per the DAG
  above, never `app.engine` / `app.improvements` / `app.models`.
- `__init__.py` re-exports every externally-imported name via `__all__` +
  explicit imports; F401 markers as needed.
- Commit trailers: `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`
  + `Claude-Session: <this session URL>`.

Shell: chain `cd .../backend && source .venv/bin/activate && <cmd>` per call.

---

## Commits

1. **package skeleton + `_xml.py`** — `mkdir`, `git mv data_loader.py
   __init__.py`, cut paths + `_text`/`_int`/`_float`/`_child`/`_int_text` +
   the three attr tuples + `log` → `_xml.py`. `__init__` imports `*` back.
2. **`formulas.py`** — `eval_formula`, `parse_avail` family,
   `parse_capacity` family, `CHARGEN_*`. Re-export for `engine/limits.py`,
   `engine/__init__.py`, gear/magic modules.
3. **`bonus.py`** — the requirement / bonus / select-slot parsers +
   `quality_*` inspectors + `selecttext_catalog_options` + the three
   option-list constants. Re-export `parse_select_power_slot` (imported by
   `improvements/nodes/*` and `improvements/__init__`) and
   `selecttext_catalog_options` (`engine/selects.py` — check).
4. **`loaders/` skeleton + `ware.py` + `metatypes.py` + `skills.py`**
5. **`loaders/qualities.py` + `magic.py`** (magic is the big one — powers …
   qi_focus, ~15 loaders)
6. **`loaders/weapons.py` + `armor.py`**
7. **`loaders/gear.py` + `vehicles.py`**
8. **`loaders/lifestyle.py` + `drugs.py` + `martial_arts.py` + `priorities.py`**
9. **`loaders/translations.py`** — leaves `__init__.py` = imports + `catalog()`
   + `reset_catalog()` only (~160 lines).
10. **docs** — `architecture.md` new "data_loader split — done" bullet;
    append the Done section here.

Each of 4–9: `git`-move the loaders + their private helpers + module-level
constants, wire `loaders/__init__.py` and the barrel, `ruff --fix` for I001,
strip now-unused imports from `__init__.py`, run 469 + snapshot 6.

---

## Quick verification per commit

```
cd backend && source .venv/bin/activate && \
  ruff check app/ && ruff format --check app/ && \
  python -m pytest -q && \
  python -m pytest -q tests/test_snapshot.py && \
  python -c "import app.main, app.store, app.engine, app.improvements, app.data_loader"
# expect: 469 passed; snapshot 6 passed, no diff
```

---

## Done

Executed in session `session_014XsGWooKn7vH58HZzP3nMJ`. `app/data_loader.py`
(2,864 lines, one file) → `app/data_loader/` package; `__init__.py` down to
**240 lines** (barrel + `@lru_cache catalog()` + `reset_catalog()`). Every
commit `make check` green + snapshot gate 6 passed, byte-identical.

| commit | what |
| --- | --- |
| `5d804ec` | 1 — `git mv` to `__init__.py`; `_xml.py` (paths anchored on `parents[2]`, attr tuples, `_text`/`_int`/`_float`/`_child`, `log`) |
| `432b07b` | 2 — `formulas.py` (`eval_formula`, avail + capacity parsers, `CHARGEN_*`) |
| `df4671f` | 3 — `bonus.py` (requirement / bonus / select-slot parsers, quality inspectors, `selecttext_catalog_options`; `MATRIX_ATTRIBUTES` up to `_xml.py`) |
| `b8b0ec2` | 4 — `loaders/` package + `ware` / `metatypes` / `skills` / `qualities`; `_is_variable_cost` up to `formulas.py` |
| `2e24e30` | 5 — `loaders/magic.py` (~465 lines: powers … foci) |
| `494270d` | 6 — `loaders/{armor,weapons,gear,vehicles}`; `_parse_weaponbonus` down to `bonus.py` |
| `411a600` | 7 — `loaders/{lifestyle,drugs,martial_arts,priorities,translations}` + metamagics/echoes/qi-focus appended to `magic.py` |
| _this_ | docs |

Deviations from the plan:

- Commits 8–9 folded into 6–7 (armor/weapons/gear/vehicles in one, the
  small loaders + translations in one).
- Three helpers found to be shared across domains got hoisted rather than
  duplicated: `_is_variable_cost` → `formulas.py`, `_parse_weaponbonus` and
  `MATRIX_ATTRIBUTES` → `bonus.py` / `_xml.py`.
- `tests/test_translation_overrides.py` had to repoint its `OVERRIDE_DIR`
  monkeypatch from the `data_loader` barrel to
  `app.data_loader.loaders.translations` — `_load_ja_overrides` reads the
  constant from its own module now, so patching the re-export no longer
  reached it. No production behaviour changed (snapshot byte-identical).

Every external `from app.data_loader import …` (constants
`PHYSICAL_ATTRS` / `MATRIX_ATTRIBUTES` / `PROGRAM_HOSTS` /
`SPELL_CAST_CATEGORIES` / `SPELL_CATEGORIES` / `CHARGEN_*` / `OVERRIDE_DIR` /
`LANG_DIR`, functions `catalog` / `reset_catalog` / `eval_formula` /
`parse_avail` / `format_avail` / `sum_avail` / `parse_capacity` /
`parse_select_power_slot` / `selecttext_catalog_options` /
`drug_effect_summary` / `drug_node_value` / `load_translations` /
`load_ui_strings` / `_load_ja_overrides`) still resolves via `__init__.py`'s
re-exports.
