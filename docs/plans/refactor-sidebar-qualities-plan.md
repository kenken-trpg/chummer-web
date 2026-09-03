# Plan: split CharacterSidebar.tsx + QualitiesTab.tsx

Working doc. The last two oversized frontend components. Now that the
`vitest` harness exists (`docs/plans/frontend-test-setup-plan.md`), each split
gets a render smoke test as a guard.

## Targets

| file | lines | shape |
| --- | --- | --- |
| `components/character/CharacterSidebar.tsx` | 760 | one giant `<aside>` — a flat run of `<div className="stat">` rows + small `{d.x ? … : null}` conditionals, **no section headers** (only one `<h3>能力値</h3>`). Local `useState` for the reward-log editor + `addReward` / `removeReward`. |
| `components/character/tabs/QualitiesTab.tsx` | 635 | `renderExtraEditor(q)` is a **~370-line** local function (the per-quality "extra pick" UI: add_spirit / attribute / side / skill / expertise / text / selectquality). Plus `filteredQualities` / `qualityCtx` / `catalogById` memos and the owned-list + picker `return`. |

## Approach

### QualitiesTab (biggest single win)

- Extract `renderExtraEditor` → `components/character/tabs/qualities/QualityExtraEditor.tsx`
  as `<QualityExtraEditor q={q} d={d} patch={patch} setCharacter={setCharacter}
  tr={tr} catalogById={catalogById} />` (grep shows it closes over exactly
  those). QualitiesTab drops to ~265 lines and just renders
  `<QualityExtraEditor q={q} … />` at the one call site.

### CharacterSidebar

Split the flat stat-dump into block components under
`components/character/sidebar/`, each `(p: SidebarBlockProps) => JSX` where
`SidebarBlockProps = { catalog, character, d, tr, t, career, patch }`
(`patch` optional, as today). Blocks, in source order:

| component | rows |
| --- | --- |
| `SidebarStatus` | name / meta / mode / build-method / errors / warnings |
| `SidebarDerived` | limits + limit_modifiers, CM, limb_quality, init, armor, special armor, reach, LS-cost, notoriety / fame, SC / PA summary |
| `SidebarCareerEdit` | the `career && patch` SC / notoriety-bonus edit panel |
| `SidebarMagicStats` | fatigue / spell resist, spell defense rows, test-mods, essence |
| `SidebarFlags` | ambidextrous / erased / excon / overclocker / special-mod-limit / friends-in-high-places / made-man / trustfund one-liners |
| `SidebarEconomy` | nuyen, avail / DR limits, skillwires / skilljack, ware-attr bonus, lifestyle, commlink / cyberdeck / rcc, karma |
| `SidebarCareerRewards` | the reward-log editor — **owns** `useState` + `addReward` / `removeReward` + the spend breakdown |
| `SidebarBudgets` | career-advancement / negative karma, attr / special / skill / knowledge points, contacts, martial arts |
| `SidebarAwakened` | initiation / submersion / adept / spells / spirits / foci / complex forms / sprites / living persona / tradition / mentor |
| `SidebarAttributes` | the `<h3>能力値</h3>` grid + the unimplemented-bonuses footer |

`CharacterSidebar.tsx` → the `<aside>` shell + `<Sidebar* {...p} />` list.

## Guard

Extend the vitest suite first:

- `components/character/CharacterSidebar.test.tsx` — empty fixture renders
  the name `<h2>` + 能力値 `<h3>` + "作成" mode; a `career` fixture shows
  "キャリア" + the reward panel; a fixture with `d.ambidextrous` /
  `d.tradition` etc. shows those labels.
- `components/character/tabs/QualitiesTab.test.tsx` — renders with an empty
  catalog (no crash, the 取得済み `<h3>`); an owned quality with
  `needs_extra` renders an `<input>` / `<select>` from `QualityExtraEditor`.

`makeCatalog` gains a `qualities: []` default.

## Commits

1. **smoke tests** — `CharacterSidebar.test.tsx`, `QualitiesTab.test.tsx`,
   `makeCatalog` `qualities` default.
2. **QualitiesTab** — extract `QualityExtraEditor.tsx`.
3. **CharacterSidebar** — the `sidebar/` block split (may be 2 commits if
   noisy: derived/magic/economy first, then career/awakened/attrs).
4. **docs** — architecture.md + this doc's Done section.

## Verification per commit

```
cd frontend && npm run typecheck && npm run lint && npm run format:check && npm run test && npm run build
```

---

## Done

Executed in session `session_014XsGWooKn7vH58HZzP3nMJ`.

| commit | what | lines |
| --- | --- | --- |
| `4721a3b` | `CharacterSidebar.test.tsx` + `QualitiesTab.test.tsx` smoke tests; `makeDerived` fills `points.*`, `makeCatalog` gets `qualities: []` | +34 vitest total |
| `47a5504` | `renderExtraEditor` → `tabs/qualities/QualityExtraEditor.tsx` | QualitiesTab 635 → 240; editor 424 |
| `c1e4733` | `CharacterSidebar` → nine `sidebar/*` blocks + `sidebar/types.ts` | Sidebar 760 → 48 |
| _this_ | docs |

Deviations:

- Sidebar landed as one commit (not the planned 2) — the blocks are
  verbatim JSX slices and the smoke test + typecheck/build cover them.
- The planned `SidebarStatus` / `SidebarDerived` split collapsed into one
  `SidebarStatus` (the auto-detected boundary put mode/build-method with
  the derived stats; a 2-line "status" block wasn't worth it) → **9**
  blocks, not 10.
- `QualityExtraEditor` also needed `catalog` (not just `catalogById`) — the
  body reads `catalog.spirits` / `catalog.skills` too.
