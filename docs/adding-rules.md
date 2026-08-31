# How to add a rule / feature

Concrete recipes. Each ends with "add a test" because rule changes without a
test don't get merged. Copy an existing test in `backend/tests/test_engine.py`.

---

## A new `<bonus>` modifier (attribute / limit / skill / …)

Chummer expresses a modifier you want to support, e.g.
`<bonus><dodge>2</dodge></bonus>` on some quality.

1. **Parse** — usually nothing to do: `data_loader.parse_bonus()` already turns
   any `<bonus>` child into `{"tag": "dodge", "value": "2"}`.
2. **Dispatch** — add a branch in `improvements.apply_bonus_nodes()`:
   ```python
   elif tag == "dodge":
       effects["dodge"] += _as_int(node.get("value") or fields.get("val"))
   ```
   and initialise the key in the `effects` factory (`collect_effects` / the
   dict literal near the top of `improvements.py`).
   - If the modifier should be *recognised but ignored*, add the tag to
     `SILENT_TAGS` instead (keeps it out of the "unimplemented" report).
3. **Consume** — read `effects["dodge"]` where the final number is built in
   `engine.compute()` (or the relevant `resolve_*` helper) and put it into
   `derived`.
4. **Surface** — add the field to `frontend/lib/types.ts` and render it in
   `CharacterSheet.tsx` / the relevant tab.
5. **Test** — pick a real catalog item that carries the bonus, build a
   `CharacterState` with it, assert on `out.derived[...]`.

---

## A new item field from the Chummer XML

Example: weapons gained a `<somestat>` you want.

1. `data_loader.load_weapons()` — add `"somestat": _text(el.find("somestat"))`
   to the dict it builds.
2. `store.public_catalog()` — add it to the weapons entry so the UI can see it.
3. `engine` — use `spec.get("somestat")` wherever weapons are resolved
   (`resolve_gear` / `_public_weapon`).
4. `frontend/lib/types.ts` — add to `WeaponCatalogItem` / `InstalledWeapon`.
5. Test in `test_engine.py` (+ `test_chummer_export.py` if it round-trips).

---

## A new data file from Chummer

Example: `drugcomponents.xml` (done — use it as the reference).

1. `backend/scripts/fetch_chummer_data.py` — add the path to `FILES`.
2. Re-run `make data` locally; the file lands in `backend/vendor/` (gitignored).
   CI caches `backend/vendor/` keyed on the fetch script, so bumping `FILES`
   busts the cache automatically.
3. `data_loader` — write a `load_*()` that parses it, and merge/expose it in
   `catalog()`. **Return `{}`/`[]` gracefully if the file is missing** so
   environments without the fetch step still import.
4. Surface via `store.public_catalog()` and `frontend/lib/types.ts` as needed.

---

## A new character field (age, portrait, …)

1. `models.py` — add to **both** `CharacterState` (with a default) and
   `CharacterPatch` (as `... | None = None`).
2. `chummer_import.py` / `chummer_export.py` — map it to/from the `.chum5` tag
   if Chummer has one.
3. Frontend — add to `Character` in `lib/types.ts`, add an input that calls
   `patch({ field: value })`, render it on the sheet.
4. `test_chummer_export.py` — add to `_rich_state()` and assert it round-trips.

---

## A new editor tab

1. Create `frontend/components/character/tabs/MyTab.tsx` taking `TabPanelProps`.
2. Register it in `app/page.tsx` (`tabs` list + the render switch). If it should
   only show for some builds, gate on `d.enabled_tabs` — the backend decides
   which tabs are enabled in `engine.compute()` (`effects["enabled_tabs"]`).

---

## A new chargen validation

Add the check in the relevant `engine` spot (many live in
`apply_quality_rules` or the final block of `compute()`), appending a Japanese
string to `errors` (hard block) or `warnings` (advisory). Gate career-mode
exemptions on `not career`. Test both the failing and passing case.
