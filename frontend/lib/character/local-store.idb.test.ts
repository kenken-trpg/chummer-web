import "fake-indexeddb/auto";

import { makeCharacter } from "@/tests/fixtures";
import {
  deleteCharacter,
  getCharacter,
  getCharacterSnapshots,
  getBackupStatus,
  recordBackup,
  listCharacters,
  putCharacter,
  type StoredCharacter,
} from "@/lib/character/local-store";

/**
 * The backend stores nothing, so IndexedDB is the *only* copy of a character.
 * Its sibling `local-store.test.ts` covers the degraded path (jsdom ships no
 * IndexedDB, so every accessor there hits a catch); this file drives a real
 * store, which is where the round trip that users actually depend on lives.
 *
 * `fake-indexeddb/auto` installs the global before `local-store` is imported —
 * that module caches its open request, so the import order matters.
 */

/** Reach past the module's API to plant a record the current code would never
 *  write — an old schema, a shape from a previous release. */
function writeRaw(rec: Record<string, unknown>): Promise<void> {
  return new Promise((resolve, reject) => {
    const open = indexedDB.open("chummer-web", 1);
    open.onsuccess = () => {
      const tx = open.result.transaction("characters", "readwrite");
      tx.objectStore("characters").put(rec);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    };
    open.onerror = () => reject(open.error);
  });
}

beforeEach(async () => {
  for (const row of await listCharacters()) await deleteCharacter(row.id);
});

describe("local-store round trip", () => {
  it("reads back what it wrote", async () => {
    const character = makeCharacter({ id: "a", name: "Jazz" });

    expect(await putCharacter(character)).toBe(true);

    expect(await getCharacter("a")).toEqual(character);
  });

  it("returns null for an id it does not hold", async () => {
    expect(await getCharacter("never-written")).toBeNull();
  });

  it("overwrites in place rather than accumulating revisions", async () => {
    await putCharacter(makeCharacter({ id: "a", name: "Jazz" }));
    await putCharacter(makeCharacter({ id: "a", name: "Jazz the Second" }));

    expect((await getCharacter("a"))?.name).toBe("Jazz the Second");
    expect(await listCharacters()).toHaveLength(1);
  });

  it("forgets a deleted character", async () => {
    await putCharacter(makeCharacter({ id: "a" }));
    await deleteCharacter("a");

    expect(await getCharacter("a")).toBeNull();
    expect(await listCharacters()).toEqual([]);
  });

  it("deleting something absent is not an error", async () => {
    await expect(deleteCharacter("never-written")).resolves.toBeUndefined();
  });
});

describe("listCharacters", () => {
  it("projects the roster summary, most recently saved first", async () => {
    // savedAt is Date.now() at write time and two writes can land in the same
    // millisecond, so pin the clock. Only Date.now, not vi.useFakeTimers():
    // fake-indexeddb delivers its events on real timers and freezing those
    // deadlocks every request made after this test.
    // ids ascend while savedAt does too, so the store's own key order is the
    // *opposite* of the wanted one. Name them the other way round and getAll()
    // happens to return the right answer with no sort at all.
    const now = vi.spyOn(Date, "now").mockReturnValue(1_000);
    await putCharacter(makeCharacter({ id: "a-older", name: "First" }));
    now.mockReturnValue(2_000);
    await putCharacter(
      makeCharacter({ id: "b-newer", name: "Second", metatype: "Elf", talent: "Magician" }),
    );
    now.mockRestore();

    const roster = await listCharacters();

    expect(roster.map((r) => r.id)).toEqual(["b-newer", "a-older"]);
    expect(roster[0]).toEqual({
      id: "b-newer",
      name: "Second",
      metatype: "Elf",
      metavariant: "",
      talent: "Magician",
      career: false,
      updated: 2_000,
      buildMethod: "Priority",
      changesSinceBackup: 0,
    });
  });

  it("carries no `derived` — the roster is a list, not a payload", async () => {
    await putCharacter(makeCharacter({ id: "a" }));

    expect(Object.keys((await listCharacters())[0]).sort()).toEqual([
      "buildMethod",
      "career",
      "changesSinceBackup",
      "id",
      "metatype",
      "metavariant",
      "name",
      "talent",
      "updated",
    ]);
  });
});

describe("reading records written by an older build", () => {
  it("accepts a v0 record, which predates the schemaVersion field", async () => {
    const character = makeCharacter({ id: "v0", name: "Grandfathered" });
    await writeRaw({ id: "v0", savedAt: 1, character });

    expect(await getCharacter("v0")).toEqual(character);
  });

  it("stamps the current schema version on everything it writes", async () => {
    await putCharacter(makeCharacter({ id: "a" }));

    const rec = await new Promise<StoredCharacter>((resolve) => {
      const open = indexedDB.open("chummer-web", 1);
      open.onsuccess = () => {
        const req = open.result.transaction("characters").objectStore("characters").get("a");
        req.onsuccess = () => resolve(req.result as StoredCharacter);
      };
    });

    // v2 normalization needs the live catalog and runs in the server engine.
    expect(rec.schemaVersion).toBe(2);
  });
});

it("keeps explicit stopped programs and construction records after persistence", async () => {
  const ch = makeCharacter({
    id: "ledger",
    programs: [{ id: "p", gear_id: "browse", running: false, parent_id: "deck" }],
    electronic_parts_supplies: [{ id: "salvage", units: 3, kind: "salvaged" }],
    electronic_modification_records: [
      {
        id: "r",
        modification_id: "m",
        gear_id: "mod",
        host_id: "deck",
        status: "pending",
        required_units: 16,
        allocations: [{ source_id: "salvage", units: 3 }],
      },
    ],
  });
  expect(await putCharacter(ch)).toBe(true);
  expect(await getCharacter("ledger")).toEqual(ch);
});

describe("persistent editing history", () => {
  it("retains the last ten prior states per character and survives reads", async () => {
    for (let i = 0; i <= 12; i++) {
      await putCharacter(makeCharacter({ id: "history", name: `Version ${i}` }));
    }
    await putCharacter(makeCharacter({ id: "other", name: "Other" }));
    const snapshots = await getCharacterSnapshots("history");
    expect(snapshots).toHaveLength(10);
    expect(snapshots[0].character.name).toBe("Version 11");
    expect(snapshots[9].character.name).toBe("Version 2");
    expect(await getCharacterSnapshots("other")).toEqual([]);
    expect(await getCharacterSnapshots("history")).toEqual(snapshots);
    await putCharacter(snapshots[0].character);
    expect((await getCharacterSnapshots("history"))[0].character.name).toBe("Version 12");
    await deleteCharacter("history");
    expect(await getCharacterSnapshots("history")).toEqual([]);
  });

  it("does not make a snapshot when only derived calculations change", async () => {
    const character = makeCharacter({ id: "derived" });
    await putCharacter(character);
    await putCharacter({
      ...character,
      derived: { ...character.derived, test: true },
    } as typeof character);
    expect(await getCharacterSnapshots("derived")).toEqual([]);
  });
});

describe("backup metadata", () => {
  it("tracks edits separately per character and preserves history when recording an export", async () => {
    const base = makeCharacter({ id: "backup" });
    await putCharacter(base);
    await putCharacter(makeCharacter({ id: "other" }));
    expect(await getBackupStatus(base.id)).toEqual({ lastExportedAt: null, changesSinceBackup: 0 });
    const edited = { ...base, name: "Edited" };
    await putCharacter(edited);
    const history = await getCharacterSnapshots(base.id);
    expect((await getBackupStatus(base.id))?.changesSinceBackup).toBe(1);
    expect(await recordBackup(edited)).toBe(true);
    expect(await getBackupStatus(base.id)).toEqual({
      lastExportedAt: expect.any(Number),
      changesSinceBackup: 0,
    });
    expect(await getCharacterSnapshots(base.id)).toEqual(history);
    expect(await getCharacter(base.id)).toEqual(edited);
    await putCharacter({ ...edited, name: "Again" });
    expect((await getBackupStatus(base.id))?.changesSinceBackup).toBe(1);
    expect((await getBackupStatus("other"))?.lastExportedAt).toBeNull();
  });

  it("does not count derived recomputations or reset newer edits for a stale export", async () => {
    const base = makeCharacter({ id: "stale" });
    await putCharacter(base);
    await putCharacter({ ...base, derived: { ...base.derived, test: true } } as typeof base);
    expect((await getBackupStatus(base.id))?.changesSinceBackup).toBe(0);
    const edited = { ...base, name: "Newer" };
    await putCharacter(edited);
    await recordBackup(base);
    expect((await getBackupStatus(base.id))?.changesSinceBackup).toBe(1);
    expect(await getCharacter(base.id)).toEqual(edited);
    await deleteCharacter(base.id);
    expect(await recordBackup(edited)).toBe(false);
    expect(await getBackupStatus(base.id)).toBeNull();
  });

  it("retains counts past the ten-snapshot limit and reads older records", async () => {
    await writeRaw({
      id: "old-backup",
      savedAt: 1,
      character: makeCharacter({ id: "old-backup" }),
    });
    expect(await getBackupStatus("old-backup")).toEqual({
      lastExportedAt: null,
      changesSinceBackup: 0,
    });
    for (let i = 0; i < 15; i++)
      await putCharacter(makeCharacter({ id: "old-backup", name: `Edit ${i}` }));
    expect((await getBackupStatus("old-backup"))?.changesSinceBackup).toBe(15);
  });
});

it("projects roster metadata and keeps the edit date when only recomputing or exporting", async () => {
  const character = makeCharacter({ id: "roster", build_method: "Karma" });
  const clock = vi.spyOn(Date, "now").mockReturnValue(1000);
  try {
    await putCharacter(character);
    clock.mockReturnValue(2000);
    await putCharacter({
      ...character,
      derived: { ...character.derived, test: true },
    } as typeof character);
    expect((await listCharacters())[0].updated).toBe(1000);
    const edited = { ...character, name: "Edited" };
    await putCharacter(edited);
    expect((await listCharacters())[0]).toMatchObject({
      buildMethod: "Karma",
      changesSinceBackup: 1,
      updated: 2000,
    });
    clock.mockReturnValue(3000);
    await recordBackup(edited);
    expect((await listCharacters())[0]).toMatchObject({ changesSinceBackup: 0, updated: 2000 });
  } finally {
    clock.mockRestore();
  }
});
