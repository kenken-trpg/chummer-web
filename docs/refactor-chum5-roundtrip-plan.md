# Plan: `.chum5` round-trip coverage

Working doc. Lock the Chummer5a import ⇄ export loop against realistic,
catalog-driven fixtures.

## Where we are

- `app/chummer_import.py` (568 L) — `chum5_to_state(xml) -> (state, warnings)`.
  Resolves every section by `sourceid` / `guid`, falling back to name; unknown
  entries become warnings, never errors. Handles nested ware children, armor
  mods, weapon accessories, gear bucket routing
  (`commlinks/cyberdecks/rccs/sensors/optics/programs/apps/drones`), vehicles +
  mods, initiation / submersion grades + metamagics, martial arts + techniques,
  adept powers, complex forms, tradition, mentor, lifestyles, contacts,
  career mode (`created=True` → `karma_earned` / `nuyen_earned`).
- `app/chummer_export.py` (340 L) — `state_to_chum5(state) -> bytes`, pretty XML.
- `tests/test_chummer_import.py` (140 L) — one hand-written `SAMPLE`: identity /
  priorities / attributes (min+base+karma fold) / skills / groups / knowledge /
  native language / qualities / spells / tradition / lifestyle / contacts +
  the unresolved-→-warning path + all the `decompress_chum5lz` branches.
- `tests/test_chummer_export.py` (118 L) — a synthetic `_rich_state()`:
  well-formed-XML check, a **core** round-trip (`state → xml → state`), and a
  re-validate. Ware children, gear buckets, vehicles, initiation, submersion,
  martial arts, complex forms, adept powers, career mode, SumToTen /
  LifeModule build methods, mentor: **untested on the import side, and no
  `import → compute → export → re-import` fixed-point is asserted anywhere.**

No real `.chum5` files are vendored (GPL-3.0 data, large). The substitute:
Chummer-shaped XML generated from the live `catalog()` at test time, so the
fixtures can't rot when catalog ids shift.

## New file: `tests/test_chummer_roundtrip.py`

### Helper

```python
def build_chum5(**sections) -> bytes
```

Emits a `<character>` tree in Chummer's layout (the tags `chum5_to_state`
reads: `<cyberwares><cyberware>…<children>…`, `<armors><armor><armormods>`,
`<weapons><weapon><accessories><accessory><mount>`, `<gears><gear><children>`,
`<vehicles><vehicle><mods><mod>`, `<initiationgrades><initiationgrade>` +
`<metamagics><metamagic>`, `<martialarts><martialart><martialarttechniques>`,
`<spells>`, `<complexforms>`, `<powers>`, `<tradition>`, `<mentorspirit>`,
`<lifestyles>`, `<contacts>`). Item names come from `catalog()` lookups
(`_first("weapons")`, `_by_cat("cyberware", "Bodyware")`, …) so a fixture is
"the first N real rows of each bucket", not a frozen string list.

### The invariant each scenario asserts

```
s1              = chum5_to_state(xml)              # + assert the section mapped
ch1             = import_character(s1 - _warnings) # runs validate + compute
xml2            = state_to_chum5(ch1)              # export the computed state
assert xml2 == state_to_chum5(ch1)                # deterministic
s2              = chum5_to_state(xml2)
assert norm(s2) == norm(s1)                        # fixed point (ids stripped)
ch2             = import_character(s2 - _warnings)
assert stable(ch2.derived) == stable(ch1.derived) # compute is loop-invariant
```

- `norm()` drops every generated row `id` / `_warnings` and sorts list rows by
  their catalog id, so only real content is compared.
- `stable(derived)` = a curated dict: `errors`, `totals`, `essence`, `limits`,
  `condition_monitor`, `initiative`, `armor`, `nuyen`, `karma`,
  `enabled_tabs`, plus `len(derived[b])` for
  `b in {cyberware, bioware, weapons, armor_items, gear, drones, vehicles,
  spells, adept_powers, complex_forms}`.

## Commits

1. **helper + fixed-point + street samurai** — `build_chum5`, `norm`,
   `stable`, and scenario A: Priority build, nested cyberware (a `[…]` limb
   with a child), bioware, armor + mods, two weapons + a mounted accessory,
   gear routed to `commlinks` / `programs`, a drone, a vehicle + mod,
   a lifestyle, a group contact.
2. **full mage** — scenario B: `prioritytalent Magician`, MAG attribute,
   Spellcasting + spec, several spells, `<tradition>`, `<mentorspirit>`,
   two `<initiationgrade>` (one with `ordeal=True`) + two `<metamagic>`,
   a couple of `<power>` rows. Assert `initiate_grade`, `initiations[*].
   option_id`, `tradition_id`, `mentor_id`, warning-free.
3. **technomancer + career + SumToTen** — scenario C: `Technomancer`,
   `<complexforms>`, three `<initiationgrade res="True">` → `submersion_grade`
   / `submersions`. Scenario D: `buildmethod=SumToTen`, `created=True` with
   `<karma>` / `<nuyen>` → `career`, `karma_earned`, `nuyen_earned`; plus a
   `<martialart>` with two techniques.
4. **docs** — `architecture.md` (import/export bullet + test count) and this
   doc's Done section.

## Non-goals

- Vendoring real `.chum5` binaries.
- `.chum5lz` compression round-trip (already covered in
  `test_chummer_import.py`).
- Byte-stable XML across catalog changes — only the re-imported *state* and
  the recomputed *derived* are pinned, not the XML text.

## Verification per commit

```
cd backend && python3 -m pytest -q && ruff check . && ruff format --check . && mypy
```

## Done

`tests/test_chummer_roundtrip.py` — `build_chum5(**sections)` +
`_scrub` / `_stable` / `_loop`, 8 tests, 469 → 477. Four scenarios:
samurai (nested ware / armor+mod / weapon+accessory / gear→commlinks /
vehicle / group contact), mage (spells / Hermetic / Bear / two
initiation grades + Centering & Masking), technomancer (three complex
forms / three submersion grades), career (Ork, SumToTen, `created=True`
+ karma/nuyen, martial art + techniques).

Two real bugs the loop surfaced, both fixed:

- **`state_to_chum5` never emitted `<included>`** — a factory sub-item
  (armor / weapon / vehicle mod, ware / gear child) re-imported as
  user-added and got billed; nuyen drifted 7.5k on the second pass. It
  now writes `<included>` for ware/gear children and armor/weapon/vehicle
  mods.
- **ElementTree truthiness deprecation** in `chummer_import.py`
  (`root.find(...) or root.find(...)` on an `Element`) on the
  `mentorspirit` and nested-`character` paths — rewritten as
  `x = find(...); if x is None: …`.

`included` on `WeaponMountInstall` is not round-tripped (export emits no
`<weaponmounts>` section at all) — out of scope here, noted for later.
