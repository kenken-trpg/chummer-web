# Plan: a `.chum5` Chummer itself can open

Working doc. A tester built a character in this app, exported it, and opened
the file in Chummer.exe. Two things went wrong:

- the settings file failed to load, "although a file by that name is there"
- attributes and special attribute points came out negative; redoing the
  priorities in Chummer recovered most of it

Both reproduce against Chummer's own test saves, without the tester's file.

## Where we are

`scripts/chum5_reconcile.py --fidelity` compares each of Chummer's 34 test
saves with what this app writes back out, field by field, over the
character's own header. Today **0 of 34** come back saying everything Chummer
said: 98 fields are dropped, and `<settings>` is written with different text.

`--roundtrip` cannot see any of this. It reads the export back with *this
app's own* importer, so a field neither side reads comes back unchanged
because neither side looked, and the round trip calls that a pass.

## What Chummer actually reads

From `Chummer/Backend/Characters/Character.cs` and
`Chummer/Backend/Attributes/Attribute.Core.cs` at the pinned ref
(`vendor/chummer/.chummer-ref`). "Reads" means `Load` pulls it out of the
save; the rest are written for other readers and recomputed on load.

| Field | Read by `Load`? | Note |
| --- | --- | --- |
| `special`, `totalspecial` | **yes** | the special attribute points, stored, not recomputed |
| `totalattributes` | **yes** | likewise for attribute points |
| `maxkarma`, `maxnuyen` | **yes** | legacy budget, used to score which settings to substitute |
| `startingnuyen`, `contactpoints`, `spelllimit`, `metatypebp` | **yes** | |
| `magenabled`, `resenabled`, `depenabled` | **yes** | without them the character has no Magic/Resonance at all |
| `adept`, `magician`, `technomancer`, `critter` | **yes** | an adept whose `<adept>` is missing loads mundane |
| `tradition`, `stream`, `initiategrade`, `submersiongrade` | **yes** | |
| `createdversion`, `gameedition`, `metatypecategory`, `primaryarm`, `playername`, `essenceatspecialstart`, `prototypetranshuman`, `cfplimit`, `publicawareness`, `mainmugshotindex`, `walk`/`run`/`sprint` | **yes** | |
| `settingshashcode` | **yes** | fallback when the settings key does not match |
| `sumtoten`, `buildkarma`, `gameplayoption`, `gameplayoptionqualitylimit`, `nuyenmaxbp`, `contactmultiplier`, `totaless`, `traditiondrain`, `streamdrain`, `contactpointsused`, `walkalt`/`runalt`/`sprintalt` | no | output only |
| attribute `metatypemin`, `metatypemax`, `metatypeaugmax`, `base`, `karma` | **yes** | what an attribute is made of |
| attribute `value` | yes, as a shim | pre-split saves only; folded into `karma` |
| attribute `totalvalue`, `metatypecategory` | no | recomputed; the category comes from the abbreviation |

So the earlier guess that `sumtoten` was behind the negative attributes was
wrong — Chummer does not read it back. The budget comes from the settings.

## Why the settings fail to load

`Character.Load` reads `<settings>` into the *settings key* and looks it up in
`SettingsManager.LoadedCharacterSettings`. That dictionary is keyed by
`CharacterSettings.DictionaryKey`, which is

```
BuiltInOption ? SourceIdString : FileName
```

— a GUID for a built-in preset (`223a11ff-…` for Standard, listed in
`settings.xml`, which this app already vendors), and the **file name with its
extension** for a custom one. This app writes the preset's display name
(`Standard`, `Prime Runner`), which is neither, so the lookup always misses.
The dialog that follows prints `Path.GetFileNameWithoutExtension` of that key,
which is why it names something the tester can see in their settings folder.

## Why that also explains the attributes

An attribute's `<base>` is kept only when `BaseUnlocked`, which is
`EffectiveBuildMethodUsesPriorityTables` — a property of the **settings
Chummer ended up loading**, not of the save's own `<buildmethod>`. When the
settings lookup misses and Chummer substitutes a Karma-method setting, every
attribute's `<base>` is zeroed on load. Combine that with `special` /
`totalspecial` missing (they are stored, not recomputed) and the character
arrives with points spent and no pool to spend them from.

That matches the tester's account: the settings failed first, the numbers were
wrong after, and redoing the priorities recomputed part of it.

## Steps

1. ~~`--fidelity`, so the gap is measured rather than argued~~ (done)
2. ~~Read `Character.Load`; settle which fields are required~~ (this doc)
3. Write the stored budget and pools: `special`, `totalspecial`,
   `totalattributes`, `maxkarma`, `maxnuyen`, `startingnuyen`, `contactpoints`,
   `metatypebp`, `spelllimit`. The engine already computes all of these.
4. Write the flags that decide what the character *is*: `magenabled`,
   `resenabled`, `depenabled`, `adept`, `magician`, `technomancer`, `critter`,
   `tradition`, `stream`, `initiategrade`, `submersiongrade`, plus the header
   fields (`createdversion`, `gameedition`, `metatypecategory`, `primaryarm`,
   `essenceatspecialstart`, `prototypetranshuman`, `cfplimit`,
   `publicawareness`, `walk`/`run`/`sprint`).
5. Write `<settings>` as the key Chummer looks up: the preset's `<id>` from
   `settings.xml` for a built-in, the file name for a custom settings file.
   Also write `<sources><source>` and
   `<customdatadirectorynames><directoryname>`, which is what Chummer scores a
   replacement against when the key is not on that machine.
6. Wire `--fidelity` into `make reconcile` once it is green, so the next field
   Chummer adds is a test failure rather than a bug report.

## Out of scope

Attribute `totalvalue` / `metatypecategory` and the other output-only fields.
Chummer recomputes them, and writing figures nobody reads is how the two sides
drift apart quietly.

Confirming the fix needs Windows and Chummer.exe; this app can only show that
its export states what Chummer's own saves state. The tester's Chummer version
is worth having before step 5: the key above is what the pinned ref does, and
the 5.202-era test saves all write a plain `default.xml` there, so that era
evidently spelled it differently. Which of the two a given exe wants has to be
read off that exe's own source.
