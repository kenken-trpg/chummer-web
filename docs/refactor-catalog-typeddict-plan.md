# Plan: type `catalog()` as `CatalogDict`

Working doc for a dedicated session. `data_loader.catalog()` returns a
`dict[str, Any]` of ~46 keys; every value is `Any`, so `catalog()["powres"]`
(typo) passes and `for row in catalog()["weapons"]` yields `Any`. The
loaders that fill it are **already annotated** (`load_weapons() ->
list[dict[str, Any]]`, …), so the return literal type-checks against a
`TypedDict` as-is. Same playbook as the `EffectsDict` work: incremental,
every commit green, snapshot gate byte-identical, `mypy` clean.

## Why

`catalog()` is the single `Any` fountain for the whole engine. Typing it:

- kills a class of `no-any-return` in the `*_by_id` / `*_by_name` lookups
  and everywhere a resolver iterates `catalog()["<kind>"]`;
- lets the engine holdouts (`ware/`, `gear/`, `magic/`, `resonance`,
  `qualities`, `pricing`) reach the strict `mypy` bar without hand-annotating
  every catalog row access;
- makes a mistyped catalog key a `mypy` error.

## Survey (measured)

| fact | value |
| --- | --- |
| keys in the `catalog()` return literal | **46** |
| value shapes | `list[dict[str, Any]]` ×38, `dict[str, Any]` (`skills` / `cyberware` / `bioware`), `dict[str, dict[str, Any]]` (`all_metatypes`), `dict[str, dict[str, str]]` (`weapon_ranges`), `dict[str, str]` (`translations` / `ui_strings`), `list[str]` (`vehicle_names`), `dict[str, Any] \| None` (`qi_focus`) |
| `catalog()` call sites | **82** (≈65 literal-key `catalog()["x"]` / `.get("x")`, rest whole-dict or dynamic) |
| **dynamic** `catalog()[<var>]` / `.get(<var>)` | `lookups._item_by_id` / `_ware_by_id` / `_ware_by_name` / `_grade_by_name`; `ware/rating.py:46`; `ware/resolve.py:151`; `chummer_import.py:450` (`{b: … for b in (…)}`) |
| indirect dynamic (the `kind` variable flows in from ~15 `ware/` + `gear/` call sites) | via the four lookups above — so `Literal` on their params would cascade; a cast helper does not |
| whole-dict consumers (`cat = catalog()` then literal keys) | `store.public_catalog`, `chummer_import.chum5_to_state`, `chummer_export.state_to_chum5`, `lookups.find_metatype` — all literal-key, fine |

## Target

`CatalogDict(TypedDict)` (`total=True`) in a new
`app/data_loader/catalog_types.py` (imports only `typing`).
`catalog() -> CatalogDict`; the return literal is unchanged.

Two escape hatches in `data_loader` for the computed-key sites (the
`CatalogDict` equivalent of the `EffectsDict` `cast`):

```python
def catalog_list(kind: str) -> list[dict[str, Any]]:
    return cast("list[dict[str, Any]]", catalog().get(kind) or [])

def catalog_ware(kind: str) -> dict[str, Any]:  # cyberware / bioware buckets
    return cast("dict[str, Any]", catalog().get(kind) or {})
```

- `lookups._item_by_id(kind, id)` → `_match_by(catalog_list(kind), "id", id)`
- `lookups._ware_by_id` / `_ware_by_name` / `_grade_by_name` →
  `catalog_ware(kind).get("items" / "grades")`
- `ware/rating.py:46`, `ware/resolve.py:151` → `catalog_ware(kind)`
- `chummer_import.py:450` → `_Resolver(catalog_list(b))`

`kind` params stay `str` — no `Literal` cascade.

## Commits

1. **plan** — this doc.
2. **`CatalogDict` + `catalog()` return + the escape hatches** — define the
   `TypedDict`, annotate `catalog()`, add `catalog_list` / `catalog_ware`,
   route the ~8 dynamic sites through them. `data_loader/` + the six engine
   dynamic call sites only. Green.
3. **engine literal-key consumers** — mostly a no-op (literal `.get("x")`
   already type-checks), but sweep any `warn_return_any` / default-mismatch
   fallout the strict modules surface. Split by package if noisy.
4. **grow the strict `mypy` override** — re-run the per-module strict probe
   (`--follow-imports=silent --disallow-untyped-defs …`) over `ware/*`,
   `gear/*`, `magic/*`, `resonance`, `qualities`, `pricing`; add whichever
   are now clean.
5. **docs** — `architecture.md` (data-pipeline + tightening notes),
   `refactor-mypy-plan.md`, this doc's Done section.

## Known friction

1. **Computed `kind`** — the `catalog_list` / `catalog_ware` casts above.
   Do **not** reach for `Literal` — `kind` originates in ~15 `ware/` /
   `gear/` call sites and the cascade is not worth it.
2. **`total=True` + `.get("x", <default>)`** — `catalog().get("weapons", [])`
   still type-checks (literal key, matching default). `.get("x") or []`
   becomes technically redundant but stays (harmless, and some call sites
   genuinely guard a missing test-catalog key).
3. **`data_loader` is lenient mypy** but `catalog()` is annotated, so its
   body is checked — the return literal must satisfy `CatalogDict` exactly
   (all 46 keys, right types). The loaders' existing annotations should
   carry it; a wrong one is a real find, fix it in its own commit.
4. **`selecttext_data`** inside `catalog()` is a *plain* `dict` (not the
   `CatalogDict`) — leave it untyped, it never escapes.

## Risks / notes

- **No behaviour change** — `TypedDict` is a plain `dict` at runtime;
  `tests/snapshots/*.json` byte-identical, backend suite green.
- The `cast`s are honest: the loaders really do return
  `list[dict[str, Any]]` — we just can't prove it through a computed key.

## Verification per commit

```
cd backend && ./.venv/bin/python -m pytest -q && ./.venv/bin/ruff check . \
  && ./.venv/bin/ruff format --check . && ./.venv/bin/mypy
```
