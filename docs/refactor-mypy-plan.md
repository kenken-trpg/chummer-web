# Plan: mypy to zero, then make it blocking

Working doc. Sixth in the refactor series. Companion to the eslint-to-zero
work (`docs/architecture.md` item 6) — same shape, backend side.

## Where we are

`cd backend && ./.venv/bin/mypy app` → **30 errors in 10 files**. CI runs it
`(non-blocking)` (`.github/workflows/ci.yml`). `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.11"
files = ["app"]
exclude = ["vendor", "saves"]
ignore_missing_imports = true
check_untyped_defs = false
warn_unused_ignores = true
warn_redundant_casts = true
```

### The 30 errors, by root cause

| cause | sites | count | fix |
| --- | --- | --- | --- |
| **loop-variable type reuse** — `for inst in state.armor:` then `for inst in state.weapons:` in one function; mypy pins `inst` to the first element type | `engine/__init__.py` `resolve_gear` (547/602/632), `engine/gear/misc.py` `_misc_external_hosts` (59/65), `chummer_export.py` `state_to_chum5` (`a` / `mrow` / `g` / `v` reused across `state.armor` / `armor_mods` / gear rows / vehicles) | ~19 | rename each loop's variable (`armor_inst`, `weapon_inst`, `mrow` → `arow`/`vrow`, …). Pure rename, no behaviour change. |
| **`dict[str, int]` where `dict[str, int \| float] \| None` expected** (dict invariance) | `eval_formula` / `ware_rating_bounds` calls: `ware/rating.py:48`, `ware/resolve.py:81/90/96`, `magic/_common.py:49`, `magic/spirits.py:29`, `resonance.py:30` | 7 | widen the two callee params to `Mapping[str, float] \| None` (covariant read-only) in `data_loader/formulas.py` + `data_loader/bonus.py`? no — `ware_rating_bounds` is in `engine/ware/rating.py`. Two one-line signature changes. |
| **`str \| None` assigned to `str`** | `chummer_import.py:270`, `engine/qualities.py:333` | 2 | `or ""` narrow at the assignment. |
| **misc** — `_apply_recoil_totals(weapons, attr_totals)` gets `dict[str,int] \| None` for a non-optional param (`engine/__init__.py:626`); `total["ESS"] = ess` puts a `float` in a `dict[str,int]` (`engine/__init__.py:1072`) | | 2 | `attr_totals or {}`; annotate `total: dict[str, float]`. |

All are real (mostly latent, duck-typing saves them at runtime) — no
behaviour changes, so no snapshot risk. `make check` (`469 passed` +
frontend) stays green throughout.

## Commits

1. **`engine/__init__.py` resolve_gear loop renames** + the `total` / recoil
   fixes (same function region).
2. **`chummer_export.py` loop renames.**
3. **`engine/gear/misc.py` loop renames.**
4. **`eval_formula` / `ware_rating_bounds` signature widen** → the 7
   `arg-type` errors.
5. **`str | None` narrows** (`chummer_import.py`, `engine/qualities.py`)
   + mop up any stragglers `mypy` still reports.
6. **make it blocking** — drop `(non-blocking)` / `|| true` from the CI
   step, add `mypy` to the `check-backend` Make target, note it in
   `pyproject.toml` / `docs/architecture.md`.

Each of 1–5: `./.venv/bin/mypy app` error count strictly down, `make check`
green.

## Verification per commit

```
cd backend && source .venv/bin/activate && \
  mypy app && ruff check app/ && python -m pytest -q
# 1-5: mypy error count decreasing; 6: mypy clean
```
