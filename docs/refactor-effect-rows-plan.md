# Plan: type the `EffectsDict` row lists

Working doc for a dedicated session. Follow-on to
`docs/refactor-effects-typeddict-plan.md`: that made `effects` an
`EffectsDict` but left the ~45 `list[dict[str, Any]]` values (the
`*_mods` / `*_slots` / `grant_*` / `add_*` / cost-rule rows) as `Any`
row dicts — `row.get("nam")` (typo) still passes. Same playbook:
incremental, every commit green, snapshot gate byte-identical, `mypy` clean.

## Scope

**In:** the `EffectsDict` row-list values only — the internal contract
between `improvements/nodes/**` (producers) and ~20 engine consumers.

**Out:** the `Ctx` bundle row lists (`bundle_types.py`) — every `.public`
list, the `GearBundle` gear-category lists, `InitiationBundle.choices` etc.,
and `BonusSource = tuple[str, list[dict[str, Any]]]`. Those are
serialisation DTOs (30-plus free-form keys each, fed straight into
`state.derived`), low bug-risk, high churn. A genuinely separate job; note
it in `refactor-ctx-bundles-plan.md` as stage 5 if we ever want it.

## Survey (measured, not guessed)

| fact | value |
| --- | --- |
| `list[dict[str, Any]]` values in `EffectsDict` | **45** |
| distinct row shapes | **~24** (many keys share one shape — see groups) |
| producers | one `nodes/<domain>.py` branch each; **3** rows also produced/replaced by a `bind_*` in `engine/` |
| consumers | `for row in effects.get("<key>") or []:` + `row.get("<literal>")` — **no dynamic row-key access anywhere** |
| rows mutated after creation | `spell_category_drain` / `spell_category_damage` (`row["category"] = picked`), `action_dice_pools` (whole list replaced by `bind_action_dice_pools`, drops `needs_action`) |
| `{**slot}` spread into a stored row | **1** — `select_power_slots` (`nodes/magic.py:173`, `{"source": source, **slot}` where `slot = parse_select_power_slot(node)`) |
| rows replaced wholesale (`effects["k"] = <new list>`) | `action_dice_pools`, `weapon_category_dv`, `weapon_skill_accuracy`, `limit_spell_categories` / `limit_spirit_categories` (already `list[str]`), `extra_spirits` (already `list[str]`) |

## Target

Row `TypedDict`s in a new `app/improvements/effect_rows.py` (imports only
`typing`; `effects.py` imports it, nothing imports back — keeps the
`improvements` DAG). `EffectsDict` values change from
`list[dict[str, Any]]` to `list[<Row>]`. Producers' `.append({...})` and
consumers' `row.get("x")` are then checked.

Post-creation mutation / shape-narrowing keys → `typing.NotRequired`
(PEP 655, py3.11 native) so a `total`-ish row still accepts the reduced
form. Everything else stays `total=True`.

### Row groups

**G1 — karma-cost rules (7 keys, 2 shapes)**
- `KarmaCostRow` `{name: str, val: int, min: int, max: int | None, condition: str}` — `active_skill_karma_cost`, `knowledge_skill_karma_cost`, `knowledge_skill_karma_cost_min`, `skill_category_karma_cost`
- `KarmaMultRow` `{name: str, val: int, condition: str}` — `skill_category_karma_cost_mult`, `skill_category_spec_karma_cost_mult`, `skill_group_category_karma_cost_mult`

**G2 — dice mods (5 keys, 2 shapes)**
- `SkillModRow` `{name: str, bonus: int, exclude: str, condition: str, source: str}` — `skill_group_mods`, `skill_category_mods`
- `NamedBonusRow` `{name: str, bonus: int, condition: str, source: str}` — `skill_specific_mods`, `skill_attribute_mods`, `spell_category_mods`

**G3 — grants (5 keys, 5 shapes)**
- `grant_echoes` `{source, name}` · `free_martial_arts` `{name, source}`
- `grant_spells` `{source, name, alchemical: bool, extended: bool, limited: bool}`
- `grant_powers` `{source, name, rating: int, extra: str}`
- `free_metamagics` `{name, source, forced: bool}`

**G4 — slots / selects (9 keys)**
- `attribute_selects` `{exclude: list[str], max: int, source: str}`
- `select_quality_slots` `{source: str, options: list[str]}`
- `expertise_slots` `{source: str, skills: list[str], limit_to_specialization: str}`
- `limit_spell_category_slots` `{source: str, value: str, exclude: str}`
- `limit_spirit_category_slots` `{source: str, spirits: list[str]}`
- `add_spirit_slots` `{source: str, skill: str, rating_divisor: int, add_to_selected: bool, allowed: list[str]}`
- `select_power_slots` = `SelectPowerSlot` (`parse_select_power_slot` return: `options: list[str], rating: int, rating_expr: str, limit_expr: str, points_per_level: float, ignore_rating: bool, open_select: bool, needs_select: bool`) + `source: str`
- `weapon_category_dv_slots` `{source, skills: list[str], name: str, bonus: int, needs_select: bool}`
- `weapon_skill_accuracy_slots` `{source, name: str, bonus: int, select_attrs: dict[str, str], needs_select: bool}`

**G5 — misc effect rows (~14 keys)**
- `restricted_gear` `{availability: int, amount: int, source: str}`
- `limit_modifiers` `{limit: str, value: int, condition: str, condition_label: str, source: str}`
- `action_dice_pools` `{category: str, name: str, bonus: int, source: str, needs_action: NotRequired[bool]}`
- `focus_binding` `{name: str, val: int, extracontains: str, source: str}`
- `spell_dice_pool` `{name: str, id: str, bonus: int, source: str}`
- `SpellCategoryValueRow` `{source: str, category: str, value: int}` — `spell_category_drain`, `spell_category_damage`
- `SpellDescriptorValueRow` `{source: str, descriptor: str, value: int}` — `spell_descriptor_drain`, `spell_descriptor_damage`
- `fading_value_specific` `{specific: str, value: int}`
- `free_spells_skill` `{skill: str, limit: str, source: str}`
- `free_spells_attribute` `{attribute: str, limit: str, source: str}`
- `new_spell_karma_cost` `{type: str, value: int, condition: str, source: str}`
- `add_contacts` `{source: str, connection: int, loyalty: int, forced_loyalty: int | None, free: bool, group: bool, force_group: bool}`
- `unimplemented` `{source: str, tag: str}`

**G6 — resolved / output rows (produced by `bind_*` in `engine/`, not nodes)**
- `weapon_category_dv` / `weapon_skill_accuracy` — resolved rows from
  `gear/weapons.py`; shapes from `bind_weapon_category_dv` /
  `bind_weapon_skill_accuracy`. Seeded `[]`, replaced wholesale.
- `add_spirit_picks` — `{quality_id, quality_name, index, key, value, options, skill}` from `magic/spirits.py::bind_extra_spirits`.

## Commits

1. **plan** — this doc.
2. **G1 + G2** — `effect_rows.py` with `KarmaCostRow` / `KarmaMultRow` /
   `SkillModRow` / `NamedBonusRow`; retype the 12 `EffectsDict` values;
   fix producers (`nodes/skills.py`, `nodes/magic.py`) + consumers
   (`engine/karma.py`, `engine/skills.py`, `compute/_career.py`,
   `compute/economy.py`, `engine/magic/spells.py`).
3. **G3 + G5** — the grant + misc rows. Friction: the `row["category"] =`
   fill-in on `spell_category_*` (key already present, `total=True` OK);
   `action_dice_pools` `needs_action` → `NotRequired`, and
   `bind_action_dice_pools` return type.
4. **G4** — slots / selects. Friction: `select_power_slots`
   `{"source": source, **slot}` — give `parse_select_power_slot` a
   `SelectPowerSlot` return (in `data_loader`, or re-declared), then the
   stored row is `SelectPowerSlotRow(SelectPowerSlot): source: str` and the
   spread becomes `SelectPowerSlotRow(source=source, **slot)` or a `cast`.
5. **G6** — the three `bind_*`-produced rows; annotate the binders'
   returns + the `effects["k"] = resolved` sites.
6. **docs** — `architecture.md`, this doc's Done section,
   `refactor-effects-typeddict-plan.md` cross-link.

Split any commit 3a/3b if the diff is unwieldy. Keep each green.

## Known friction

1. **`{**slot}` spread** (`select_power_slots`) — see commit 4.
2. **whole-list replacement with a narrower shape** (`action_dice_pools`)
   — `NotRequired[bool]` on `needs_action`; `bind_action_dice_pools`
   returns `list[ActionDicePoolRow]`.
3. **`parse_select_power_slot` lives in `data_loader`** — either move its
   return `TypedDict` there and import it into `effect_rows.py`
   (`improvements` already imports `data_loader`), or re-declare a
   structurally-identical one. Prefer the former.
4. **`compute/` is a strict-override package** — `warn_return_any` /
   `disallow_untyped_defs` already hold there; typed rows may turn a
   `row.get("x")` that fed a `-> int` into an `int | None` needing
   `int(... or 0)`. Expect a handful, same as the `EffectsDict` sweep.
5. **`app.improvements.*` is now a strict-override package too** — the new
   `effect_rows.py` and every touched `nodes/*.py` line is checked at that
   bar (fully annotated already).

## Risks / notes

- **No behaviour change** — `tests/snapshots/*.json` must not move.
  `TypedDict` is a plain `dict` at runtime; edits are annotations plus the
  `NotRequired` markers and the one `select_power_slots` spread fix.
- Do **not** reach for `total=False` wholesale — use `NotRequired` on the
  specific keys that need it, so the rest of each row still catches typos.
- If a genuine bug surfaces (a real key typo, a wrong-typed default), fix
  it in its own commit with a note, don't fold it into the sweep.

## Verification per commit

```
cd backend && ./.venv/bin/python -m pytest -q && ./.venv/bin/ruff check . \
  && ./.venv/bin/ruff format --check . && ./.venv/bin/mypy
```

`tests/test_snapshot.py` first (byte-identical gate);
`tests/test_improvements_nodes.py` guards producer completeness;
`tests/test_compute_phases.py` guards the phase seams.
