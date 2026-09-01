# Plan: frontend tab-component tests

Working doc. `components/character/tabs/` has **18** tab components; only
`QualitiesTab` has a test. The behaviour-heavy ones (`SkillsTab` 491 L,
`AdeptTab` 396 L, `gear/VehicleDroneGear` 631 L, `gear/WeaponGear`,
`gear/MiscDrugsGear`) are uncovered.

## Approach

- One `*.test.tsx` next to each tab, driven by `tests/fixtures.ts`
  (`makeCharacter` / `makeCatalog` / `identityTr`). `makeCatalog()` now
  ships every catalog collection empty, so a tab renders against a bare
  fixture; each test passes the slice it exercises via `overrides`.
- Each test: (1) a render smoke over an empty character — the info line /
  key controls appear, no throw; (2) one or two behaviour assertions —
  the `patch()` / `setCharacter()` payload for the primary interaction
  (pick a metatype, bump an attribute slider, toggle a technique, add a
  spell, …).
- No snapshot files. `fireEvent` from `@testing-library/dom`, `vi.fn()`
  spies for `patch` / `setCharacter`.

## Commits (one tab per commit)

1. `AttrsTab` — slider `onMouseUp` → `patch({ attributes: { … } })`; MAG/RES
   rows hidden unless the tab is enabled.
2. `MetaTab` — Priority vs Karma metatype list; click → `patch({ metatype,
   metavariant: null })`; metavariant `<select>` when the metatype has them.
3. `PriorityTab` — build-method buttons → `patch({ build_method })`; letter
   assignment; Sum-to-Ten cost readout.
4. `ContactsTab` — add-contact form → `setCharacter` with the new row; free
   / paid point line.
5. `MartialTab` — technique checkbox → `patch({ martial_arts })`; cap line.
6. `SkillsTab` — active-skill rating input → `patch`; specialisation picker;
   custom knowledge-skill add.
7. `CyberTab` + `BioTab` — catalog filter (search / category), add-ware →
   `patch({ cyberware })` / `patch({ bioware })`, grade `<select>`.
8. `AdeptTab` — power-point readout; add power → `patch`; mentor picker.
9. `SpellsTab` — kind filter; add spell → `patch({ spell_ids })`; free-slot
   line.
10. `SpiritsTab` — tradition `<select>` → `patch({ tradition_id })`.
11. `FociTab` / `ComplexFormsTab` / `SpritesTab` — search + add → `patch`.
12. `InitiationTab` / `SubmersionTab` — grade input → `patch({ initiate_grade
    / submersion_grade })`; metamagic pick.
13. `gear/WeaponGear` — add weapon, accessory rows.
14. `gear/VehicleDroneGear` — add vehicle / drone, mod slots.
15. `gear/MiscDrugsGear` — misc gear + drug rows.
16. docs — architecture.md test-count note + this doc's Done section.

Commits may be merged where two tabs are near-identical in shape
(Foci/ComplexForms/Sprites, Initiation/Submersion).

## Verification per commit

```
cd frontend && npm run typecheck && npm run lint && npm run format:check && npm run test && npm run build
```
