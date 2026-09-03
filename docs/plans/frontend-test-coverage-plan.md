# Plan: broaden the frontend test suite

Working doc. The harness (`docs/plans/frontend-test-setup-plan.md`) landed a thin
layer — 5 helper files + 3 smoke tests. This adds focused coverage for the
pure `lib/` predicates/builders and the two tabs that were just split.

## Targets

| area | why |
| --- | --- |
| `lib/character/gear.ts` (319 L) | ~13 pure predicates — `swapMatrixOrder`, `vehicleFits` / `vehicleForbidden`, `dropTree` / `dropDrone`, `miscFits`, `wareFitsVehicleMod`, `weaponDetailsMatch`, `ammoFits`, `weaponLine`, `accessoryFits`, `armorModFits`, `vehicleInteriorFits`. Zero deps, high branch density, drive every gear picker's "can I attach this" UI. |
| `lib/character/quality.ts` (85 L) | `reqNodeMet` (per-tag: quality / metatype / skill / ess / oneof / allof …), `qualityTreeMet`, `qualityBlockReason`, `dropSkillPicksForPrefix`, `dropRemovedWarePicks`. Gate the quality picker. |
| `lib/cocofolia.ts` (393 L) | `buildChatPalette` (BCDice palette) + `buildCocofolia` (ccfolia JSON) + `buildSpiritPieces` — deterministic string/JSON from `ch.derived`; regressions here are invisible until someone pastes into a VTT. |
| `components/character/tabs/QualitiesTab.tsx` | search filter, the category tabs, add / remove-quality `patch` payloads. |
| `components/character/sidebar/*` | a few behaviour asserts (Economy shows nuyen; Awakened shows イニシエーション only when `enabled_tabs` has it) — extend `CharacterSidebar.test.tsx`. |

## Commits

1. **`lib/character/gear.test.ts`** — the 13 predicates.
2. **`lib/character/quality.test.ts`** — `reqNodeMet` per tag + the tree /
   pick-drop helpers.
3. **`lib/cocofolia.test.ts`** — `buildChatPalette` lines (initiative,
   a skill roll, a spec roll, the fixed defense block), `buildCocofolia`
   (`JSON.parse` → `data.name` / `data.params` shape), `buildSpiritPieces`.
4. **tab behaviour** — extend `QualitiesTab.test.tsx` (filter / category /
   patch spies) and `CharacterSidebar.test.tsx` (Economy / Awakened rows).
5. **docs** — architecture.md testing note + this doc's Done section.

Fixtures: reuse `tests/fixtures.ts` (`makeCharacter` / `makeCatalog`),
extending `makeCatalog` / `makeDerived` only where a builder reads a field
the minimal fixture omits.

## Verification per commit

```
cd frontend && npm run typecheck && npm run lint && npm run format:check && npm run test
```

---

## Done

Executed in session `session_014XsGWooKn7vH58HZzP3nMJ`. Suite grew from
**34 → 74 tests** (10 files). Every commit `make check` green.

| commit | what | tests |
| --- | --- | --- |
| `c7bfaa4` | `lib/character/gear.test.ts` — the 13 picker predicates | +20 |
| `e1e4349` | `lib/character/quality.test.ts` — `reqNodeMet` per tag, tree / pick-drop helpers | +11 |
| `5d55ede` | `lib/cocofolia.test.ts` — `buildChatPalette` lines + `buildCocofolia` JSON shape | +5 |
| `58ba867` | `QualitiesTab.test.tsx` (filter / category / add-via-`patch`) + `CharacterSidebar.test.tsx` (Economy / Awakened rows) | +5 |
| _this_ | docs |

No deviations — `tests/fixtures.ts` was reused as-is (no field additions
needed this round).
