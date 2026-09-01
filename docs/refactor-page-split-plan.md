# Plan: split `app/page.tsx`

Working doc. The last oversized frontend file — 620 lines, all in one
`Page()`: ~10 state hooks, ~18 handlers, 2 effects, one giant `return`
(header / toolbar / tab bar / sheet-desc editor / tab panels / sidebar).
Now guarded by the vitest suite (74 tests).

## Target shape

```
app/page.tsx                          # ~45 L — hooks + the outer <div> layout
lib/character/
  useCharacterEditor.ts               # catalog/ch/error/roster/history + all CRUD /
                                      #   patch / undo-redo / import / export / copy
  useSheetLayout.ts                   # localStorage-backed "standard|compact|text"
  useKeyboardShortcuts.ts             # Ctrl/⌘+Z / +Y (or +Shift+Z) -> undo/redo,
                                      #   ignoring INPUT/TEXTAREA focus
components/character/
  Toolbar.tsx                         # the <div class="toolbar"> — roster select,
                                      #   複製/削除, undo/redo, name, JSON/.chum5/読込,
                                      #   ココフォリア/チャットパレット/精霊コマ, キャリア,
                                      #   sheet-layout select + 印刷, hidden file input
  TabBar.tsx                          # the <div class="tabs"> (enabled-tab aware)
  TabPanels.tsx                       # the `{tab === "x" && <XTab {...panel}/>}` switch
                                      #   + <CharacterSheet> for tab==="sheet"
  SheetDescEditor.tsx                 # the tab==="sheet" portrait + age/…/notes editor
```

`useCharacterEditor` returns
`{ catalog, ch, error, roster, history, tr, t, copied, setCh, setError,
patch, openCharacter, newCharacter, deleteCurrent, duplicateCurrent, undo,
redo, restoreSnapshot, onImport, onPortraitFile, download, downloadChum5,
copyText, refreshRoster }` and takes `{ onCharacterOpened?: () => void }`
so `Page` can `setTab("priority")` on open/new/dup/import.

The mount-only bootstrap `useEffect` (and its
`// eslint-disable-next-line react-hooks/exhaustive-deps`) moves into
`useCharacterEditor` unchanged.

## Commits

1. **`useSheetLayout` + `useKeyboardShortcuts`** — extract the two small
   hooks; `Page` uses them. + tests.
2. **`useCharacterEditor`** — move every state field + handler into the
   hook; `Page`'s JSX now reads `ed.*`. No behaviour change.
3. **`Toolbar` + `SheetDescEditor`** — extract the two JSX chunks.
4. **`TabBar` + `TabPanels`** — extract; `Page` collapses to the shell.
5. **tests** — `useCharacterEditor` (mock `@/lib/api`: bootstrap opens a
   character, `patch` records history + swaps `ch`, `undo` restores),
   `useSheetLayout` (reads/writes localStorage, bad value → "standard"),
   `useKeyboardShortcuts` (⌘Z → undo, ⌘⇧Z → redo, ignores when an input is
   focused), `Toolbar` render (buttons present; カリア toggle payload).
6. **docs** — architecture.md Frontend section + this doc's Done section.

## Verification per commit

```
cd frontend && npm run typecheck && npm run lint && npm run format:check && npm run test && npm run build
```
