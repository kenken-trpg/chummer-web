# Plan: split `app/improvements.py` into an `improvements/` package

Working doc for a dedicated session. Same playbook as the engine split
(`docs/refactor-*-plan.md`): incremental, every commit green, snapshot gate
byte-identical.

## Where we are

`app/improvements.py` is **1,321 lines** — the last real monolith in the
backend. Breakdown:

| span | lines | contents |
| --- | --- | --- |
| 1–325 | ~325 | constant tables (`IMPLEMENTED`, `SILENT_TAGS`, `SPECIAL_ARMOR_TAGS`, `SPELL_DEFENSE_RESIST_TAGS`, `TEST_MOD_TAGS`, `ATTR_ALIASES`, `LIMIT_*` …) |
| 327–389 | ~63 | primitives: `_replace_rating`, `substitute_rating`, `_as_text`, `_limit_kind`, `limit_condition_label`, `_as_int`, `_bonus_int` |
| 391–526 | ~136 | `empty_effects()` — the 133-key effects dict |
| **529–1259** | **~731** | **`apply_bonus_nodes()` — one `for node` loop with a ~90-branch `if/elif tag == …` chain** |
| 1262–1321 | ~60 | `special_armor_totals`, `compact_special_armor`, `special_armor_from_nodes`, `compact_limit_modifiers`, `limit_modifiers_from_nodes`, `collect_effects` |

`apply_bonus_nodes` is 55 % of the file and the actual target.

### External API surface (must stay importable as `from app.improvements import …`)

Grep of `app/ tests/`:

| name | imported by |
| --- | --- |
| `apply_bonus_nodes` | `engine/gear/drugs.py`, `engine/magic/spells.py` |
| `substitute_rating` | 8 engine modules |
| `_as_int` | `engine/{limits,selects,skills,qualities}.py` |
| `ATTR_ALIASES` | `engine/limits.py` |
| `collect_effects` | `engine/__init__.py`, `tests/test_engine.py` |
| `compact_limit_modifiers`, `special_armor_totals` | `engine/__init__.py` |
| `limit_modifiers_from_nodes`, `special_armor_from_nodes` | `engine/gear/armor.py` |

`improvements/__init__.py` re-exports all of these (a barrel) so **no
importer changes**.

## Target layout

```
app/improvements/
  __init__.py        # barrel: re-export the public API above + collect_effects wrappers
  _common.py         # constant tables + primitives (_as_int, substitute_rating, _bonus_int, …)
  effects.py         # empty_effects, special_armor_totals, compact_special_armor,
                     #   compact_limit_modifiers  (need _common only)
  nodes/
    __init__.py      # apply_bonus_nodes: the `for node` loop + ordered domain dispatch;
                     #   IMPLEMENTED / SILENT_TAGS live here
    stats.py         # attributes, enable*, limits, armor/CM/initiative, special-armor,
                     #   spell-defense-resist, test-mods, movement, cm-recovery, reach, unarmed
    skills.py        # skillgroup/category/specific/attribute, unlock/disable, skillwire,
                     #   *karmacost* / *costmultiplier*, knowledge-skill tags
    magic.py         # adept powerpoints, spell/spirit category limits, drain/fading,
                     #   freespells, addspell/echo/metamagic/spirit, focus binding, selectpowers
    social.py        # economy (nuyen/lifestyle/fame/notoriety), contacts, black-market,
                     #   qualities (freequality/addqualities/selectquality), ware-ess multipliers,
                     #   erased/excon/martialart/prototype-transhuman + the `pass` no-op tags
```

### How the dispatch stays byte-identical

Each `nodes/<domain>.py` exposes:

```python
def apply(tag: str, node: dict, fields: dict, effects: dict, source: str) -> bool:
    if tag == "specificattribute":
        ...
        return True
    elif tag == "armor":
        ...
        return True
    ...
    return False   # not my tag
```

— i.e. its **slice of the original `if/elif` chain, verbatim**, ending in
`return False`.

`nodes/__init__.py`:

```python
_DOMAINS = (stats.apply, skills.apply, magic.apply, social.apply)

def apply_bonus_nodes(nodes, effects, source):
    for node in nodes:
        tag = node.get("tag", "")
        if tag not in IMPLEMENTED:
            if tag not in SILENT_TAGS:
                effects["unimplemented"].append({"source": source, "tag": tag})
            continue
        fields = node.get("fields") or {}
        for domain in _DOMAINS:
            if domain(tag, node, fields, effects, source):
                break
```

No tag is handled by two domains, so cross-domain order is irrelevant;
within a domain the branches keep their original order. Semantically
identical to the flat chain — the snapshot gate proves it.

**Completeness guard:** keep `IMPLEMENTED` as the current explicit set. Add
`tests/test_improvements_nodes.py::test_every_implemented_tag_has_a_handler`
— feeds a stub `{"tag": t}` node for every `t in IMPLEMENTED` through
`apply_bonus_nodes` with a fresh `empty_effects()` and asserts
`effects["unimplemented"] == []`. Catches a tag dropped during slicing even
if no character test exercises it.

## Ground rules (unchanged)

- Every commit green: `make check` (ruff + `pytest 468 passed` + frontend).
  Plus the snapshot gate: `python -m pytest -q tests/test_snapshot.py` →
  `6 passed`, byte-identical, before/after every move.
- `improvements/` submodules import only stdlib + `..data_loader`
  (`parse_select_power_slot`, used by the `selectpowers` branch) + each
  other, never back into `app.improvements` or `app.engine`. DAG.
- `__init__.py` keeps re-exporting every name in the API table via `__all__`
  + explicit imports. F401 on `__init__.py` is fine to mark re-exports.
- Commit trailers: `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`
  + `Claude-Session: <this session URL>`.

Shell: chain `cd .../backend && source .venv/bin/activate && <cmd>` per
Bash call.

---

## Commits

### 1 — `improvements/` package skeleton: `_common.py` + `effects.py`

- `mkdir app/improvements/`, `git mv app/improvements.py app/improvements/__init__.py`.
- Cut the constant tables + primitives (lines 1–389) → `_common.py`.
- Cut `empty_effects` + `special_armor_totals` + `compact_special_armor` +
  `compact_limit_modifiers` → `effects.py` (import tables from `._common`).
- `__init__.py` becomes: `from ._common import *`-style explicit re-exports
  + `from .effects import …` + the still-inline `apply_bonus_nodes` and the
  three `*_from_nodes` / `collect_effects` wrappers (temporarily importing
  `empty_effects` from `.effects`).
- Verify: import graph, 468, snapshot 6.

### 2 — `nodes/` package, flat move of `apply_bonus_nodes`

- New `nodes/__init__.py` = the dispatch loop + `IMPLEMENTED` + `SILENT_TAGS`
  + **one** temporary `nodes/_chain.py` holding the whole `if/elif` body as
  `apply(tag, node, fields, effects, source) -> bool`.
- `_DOMAINS = (_chain.apply,)` for now.
- `improvements/__init__.py` re-exports `apply_bonus_nodes` from `.nodes`.
- This commit is a pure relocation — snapshot must be byte-identical.

### 3–6 — carve `_chain.py` into `stats` / `skills` / `magic` / `social`

One commit per domain module. Each: move that domain's `if tag == …`
branches out of `_chain.py` into `nodes/<domain>.py`, add
`<domain>.apply` to `_DOMAINS` (before `_chain.apply`), shrink `_chain.py`.
Last commit deletes the now-empty `_chain.py` and drops it from `_DOMAINS`.

Snapshot gate + the new completeness test bracket every carve.

### 7 — completeness test + docs

- Add `tests/test_improvements_nodes.py` (the guard described above) if not
  already added in commit 2.
- `docs/architecture.md`: add an "improvements split" bullet under a new
  §item; note `app/improvements/` is a package.
- Append a "Done" section here with the commit log.

---

## Quick verification per commit

```
cd backend && source .venv/bin/activate && \
  ruff check app/ && ruff format --check app/ && \
  python -m pytest -q && \
  python -m pytest -q tests/test_snapshot.py && \
  python -c "import app.main, app.store, app.engine, app.improvements"
# expect: 469 passed; snapshot 6 passed, no diff
```

---

## Done

Executed in session `session_014XsGWooKn7vH58HZzP3nMJ`. `app/improvements.py`
(1,321 lines, one file) → `app/improvements/` package, largest module now
`nodes/magic.py` at 252. Every commit `make check` green + snapshot gate 6
passed, byte-identical.

| commit | what |
| --- | --- |
| `08994ab` | 1 — `git mv` to `__init__.py`; `_common.py` (tables + primitives) + `effects.py` (`empty_effects` + compactors) carved out; dead `logging` dropped |
| `bf4d891` | 2 — `apply_bonus_nodes` → `nodes/`: `__init__.py` = per-node loop + `_DOMAINS` dispatch, `_chain.py` = the whole chain wrapped in `for _once in (True,)` (keeps the 8 in-branch `continue`s exact); new `tests/test_improvements_nodes.py` completeness guard |
| `4918d8c` | 3 — `_chain.py`'s 127 branches carved into `nodes/{stats,skills,magic,social}.py` (36/21/31/39), `_chain.py` deleted; commits 3–6 of the plan folded into one |
| _this_ | docs |

Deviations:

- Commits 3–6 folded into one — each domain is a mechanical slice of the
  same chain and the snapshot gate + completeness guard prove equivalence,
  so per-domain commits were pure churn.
- The `for _once in (True,)` wrapper (not a dict registry) keeps every
  branch body **verbatim**, including the `continue` idiom, so the split is
  a pure relocation rather than a control-flow rewrite.

The `app/improvements/` package is the backend's last monolith cleared.
`from app.improvements import …` is unchanged — the package `__init__` is
the barrel (`__all__` covers `apply_bonus_nodes`, `collect_effects`,
`substitute_rating`, `_as_int`, `ATTR_ALIASES`, `special_armor_totals`,
`compact_limit_modifiers`, `empty_effects`, `special_armor_from_nodes`,
`limit_modifiers_from_nodes`, `compact_special_armor`).
